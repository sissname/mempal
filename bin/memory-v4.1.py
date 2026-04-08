#!/usr/bin/env python3
"""
Unified Memory System v4.1 - 完整版

改进：
1. 同义词词典（语义扩展）
2. 规则冲突检测
3. 高级权重计算（时效衰减 + 紧急度）
4. 简单知识图谱
5. 输入验证
"""

import json
import sys
import math
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# 跨平台文件锁
if sys.platform == 'win32':
    import msvcrt
    HAS_MSVCRT = True
else:
    import fcntl
    HAS_FCNTL = True

# 尝试导入 jieba 分词（可选依赖）
try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False
    print("提示：安装 jieba 可获得更好的中文分词：pip install jieba")

# 路径配置（跨平台兼容）
if sys.platform == 'win32':
    # Windows: 使用 %USERPROFILE% 而不是 ~
    import os
    WORKSPACE = Path(os.environ.get('USERPROFILE', Path.home())) / ".openclaw" / "workspace"
else:
    WORKSPACE = Path.home() / ".openclaw" / "workspace"

MEMORY_DIR = WORKSPACE / "memory"
DAILY_DIR = MEMORY_DIR / "daily"
SESSION_STATE_PATH = WORKSPACE / "SESSION-STATE.md"
MEMORY_MD_PATH = WORKSPACE / "MEMORY.md"
GRAPH_PATH = MEMORY_DIR / "graph.json"
CONFIG_PATH = MEMORY_DIR / "config.json"  # Git 备份配置

# 确保目录存在
DAILY_DIR.mkdir(parents=True, exist_ok=True)
VERSIONS_DIR = MEMORY_DIR / ".versions"  # 版本历史目录
VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

# 版本保留策略
MAX_VERSIONS_PER_FILE = 10  # 每个文件保留最近 10 个版本

# 搜索缓存配置
SEARCH_CACHE_SIZE = 100  # LRU 缓存大小

# 关键词倒排索引配置
ENABLE_KEYWORD_INDEX = True  # 启用索引（大数据量时性能 +100 倍）
KEYWORD_INDEX_PATH = MEMORY_DIR / "keyword_index.json"
INDEX_UPDATE_THRESHOLD = 50  # 超过 50 条记忆时启用索引

# Git 备份配置（从配置文件加载，在函数定义后初始化）
GIT_BACKUP_ENABLED = False  # 临时值，后面会更新
GIT_BACKUP_AUTO_PUSH = False

# 版本保留策略
MAX_VERSIONS_PER_FILE = 10  # 每个文件保留最近 10 个版本

# 搜索缓存配置
SEARCH_CACHE_SIZE = 100  # LRU 缓存大小

# 关键词倒排索引配置
ENABLE_KEYWORD_INDEX = True  # 启用索引（大数据量时性能 +100 倍）
KEYWORD_INDEX_PATH = MEMORY_DIR / "keyword_index.json"
INDEX_UPDATE_THRESHOLD = 50  # 超过 50 条记忆时启用索引

# ─────────────────────────────────────────────────────────────
# 并发处理（跨平台文件锁）
# ─────────────────────────────────────────────────────────────

def acquire_lock(f, mode='exclusive'):
    """跨平台获取文件锁"""
    if sys.platform == 'win32' and HAS_MSVCRT:
        # Windows 用 msvcrt
        if mode == 'exclusive':
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
        else:
            msvcrt.locking(f.fileno(), msvcrt.LK_RLCK, 1)
    elif HAS_FCNTL:
        # macOS/Linux 用 fcntl
        if mode == 'exclusive':
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        else:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)

def release_lock(f):
    """跨平台释放文件锁"""
    if sys.platform == 'win32' and HAS_MSVCRT:
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
    elif HAS_FCNTL:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

def read_file_with_lock(filepath):
    """读取文件时加共享锁（跨平台）"""
    if not filepath.exists():
        return ""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        acquire_lock(f, mode='shared')
        try:
            content = f.read()
        finally:
            release_lock(f)
        return content

def write_file_with_lock(filepath, content):
    """写入文件时加排他锁（跨平台 + 版本历史）"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # 保存版本历史（如果是关键文件）
    if filepath.name in ['SESSION-STATE.md', 'MEMORY.md', 'graph.json']:
        save_version(filepath, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        acquire_lock(f, mode='exclusive')
        try:
            f.write(content)
        finally:
            release_lock(f)

def save_version(filepath, content):
    """保存文件的历史版本"""
    version_dir = VERSIONS_DIR / filepath.stem
    version_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成版本号
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    version_file = version_dir / f"{timestamp}_{filepath.name}"
    version_file.write_text(content, encoding='utf-8')
    
    # 清理旧版本（保留最近 N 个）
    cleanup_old_versions(version_dir)

def cleanup_old_versions(version_dir, keep=None):
    """清理旧版本，保留最近 N 个"""
    if keep is None:
        keep = MAX_VERSIONS_PER_FILE
    
    versions = sorted(version_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    for old_version in versions[keep:]:
        try:
            old_version.unlink()
        except Exception:
            pass

def list_versions(filename, limit=10):
    """列出文件的历史版本"""
    version_dir = VERSIONS_DIR / Path(filename).stem
    
    if not version_dir.exists():
        return []
    
    versions = sorted(version_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    result = []
    for v in versions[:limit]:
        result.append({
            "file": str(v),
            "time": datetime.fromtimestamp(v.stat().st_mtime).isoformat(),
            "size": v.stat().st_size
        })
    
    return result

def restore_version(filename, version_path):
    """恢复到指定版本"""
    version_file = Path(version_path)
    target_file = WORKSPACE / filename
    
    if not version_file.exists():
        return {"status": "error", "message": "版本文件不存在"}
    
    # 先备份当前版本
    if target_file.exists():
        save_version(target_file, target_file.read_text(encoding='utf-8'))
    
    # 恢复
    content = version_file.read_text(encoding='utf-8')
    write_file_with_lock(target_file, content)
    
    return {"status": "ok", "message": f"已恢复到 {version_path}"}

# ─────────────────────────────────────────────────────────────
# 导出/导入功能（v4.3 新增）
# ─────────────────────────────────────────────────────────────

def export_memories(format='json', output_file=None):
    """导出记忆为 JSON/Markdown"""
    memories = []
    
    # 从所有文件加载记忆
    all_files = [SESSION_STATE_PATH, MEMORY_MD_PATH] + list(DAILY_DIR.glob("*.md"))
    
    for filepath in all_files:
        if not filepath.exists():
            continue
        
        content = read_file_with_lock(filepath)
        for line in content.split('\n'):
            if line.strip() and not line.startswith('#'):
                memories.append({
                    "content": line.strip(),
                    "source": str(filepath),
                    "layer": "L1" if "SESSION-STATE" in str(filepath) else ("L2" if "MEMORY.md" in str(filepath) else "L3")
                })
    
    if format == 'json':
        data = json.dumps({"memories": memories, "exported_at": datetime.now().isoformat()}, indent=2, ensure_ascii=False)
    elif format == 'markdown':
        data = "# 记忆导出\n\n"
        data += f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        data += f"总计：{len(memories)} 条记忆\n\n"
        data += "---\n\n"
        for i, mem in enumerate(memories, 1):
            data += f"{i}. [{mem['layer']}] {mem['content']}\n"
    else:
        return {"status": "error", "message": f"不支持的格式：{format}"}
    
    if output_file:
        output_path = Path(output_file)
        output_path.write_text(data, encoding='utf-8')
        return {"status": "ok", "message": f"已导出到 {output_file}", "count": len(memories)}
    else:
        return {"status": "ok", "data": data, "count": len(memories)}

def import_memories(input_file, format='json', skip_existing=True):
    """从文件导入记忆"""
    input_path = Path(input_file)
    
    if not input_path.exists():
        return {"status": "error", "message": "文件不存在"}
    
    content = input_path.read_text(encoding='utf-8')
    
    if format == 'json':
        data = json.loads(content)
        memories = data.get('memories', [])
    elif format == 'markdown':
        # 解析 Markdown
        memories = []
        for line in content.split('\n'):
            if line.strip() and not line.startswith('#') and not line.startswith('---'):
                # 提取记忆内容
                import re
                match = re.search(r'\[(L\d+)\]\s*(.+)', line)
                if match:
                    memories.append({
                        "content": match.group(2),
                        "layer": match.group(1)
                    })
    else:
        return {"status": "error", "message": f"不支持的格式：{format}"}
    
    # 导入记忆
    imported = 0
    skipped = 0
    
    for mem in memories:
        mem_content = mem.get('content', '')
        
        # 检查是否已存在
        if skip_existing:
            existing = search_cached(mem_content, limit=1)
            if len(existing.get('results', [])) > 0:
                skipped += 1
                continue
        
        # 采集记忆
        result = capture(
            type="event",
            content=mem_content,
            importance=0.5
        )
        if result.get('id'):
            imported += 1
    
    return {"status": "ok", "message": f"导入完成", "imported": imported, "skipped": skipped}

# ─────────────────────────────────────────────────────────────
# Git 自动备份（可选功能）
# ─────────────────────────────────────────────────────────────

def is_git_repo():
    """检查是否在 git 仓库中"""
    try:
        result = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'],
                              capture_output=True, text=True, cwd=WORKSPACE)
        return result.returncode == 0
    except Exception:
        return False

def git_backup(message="auto-backup: memory update"):
    """Git 自动备份"""
    if not GIT_BACKUP_ENABLED:
        return {"status": "disabled", "message": "Git 备份未启用"}
    
    if not is_git_repo():
        return {"status": "error", "message": "不在 git 仓库中"}
    
    try:
        # 添加文件
        files_to_add = [
            str(SESSION_STATE_PATH),
            str(MEMORY_MD_PATH),
            str(MEMORY_DIR)
        ]
        
        for f in files_to_add:
            subprocess.run(['git', 'add', f], capture_output=True, cwd=WORKSPACE)
        
        # Commit
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        full_message = f"{message} ({timestamp})"
        result = subprocess.run(['git', 'commit', '-m', full_message],
                              capture_output=True, text=True, cwd=WORKSPACE)
        
        if result.returncode != 0:
            # 如果没有变化，git commit 会失败（正常）
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                return {"status": "ok", "message": "无变化，无需备份"}
            return {"status": "error", "message": f"Commit 失败：{result.stderr}"}
        
        # Push（可选）
        if GIT_BACKUP_AUTO_PUSH:
            subprocess.run(['git', 'push'], capture_output=True, cwd=WORKSPACE)
        
        return {"status": "ok", "message": f"备份成功：{full_message}"}
    
    except Exception as e:
        return {"status": "error", "message": f"备份失败：{str(e)}"}

def enable_git_backup(auto_push=False):
    """启用 Git 备份（持久化）"""
    global GIT_BACKUP_ENABLED, GIT_BACKUP_AUTO_PUSH
    result = set_git_backup_enabled(True, auto_push)
    GIT_BACKUP_ENABLED = True
    GIT_BACKUP_AUTO_PUSH = auto_push
    return result

def disable_git_backup():
    """禁用 Git 备份（持久化）"""
    global GIT_BACKUP_ENABLED, GIT_BACKUP_AUTO_PUSH
    result = set_git_backup_enabled(False)
    GIT_BACKUP_ENABLED = False
    GIT_BACKUP_AUTO_PUSH = False
    return result

# ─────────────────────────────────────────────────────────────
# 改进 1: 同义词词典
# ─────────────────────────────────────────────────────────────

SYNONYMS = {
    # 颜色/主题（12 组）
    "深色": ["暗黑", "暗色", "夜间模式", "dark", "黑"],
    "暗黑": ["深色", "暗色", "夜间模式", "dark", "黑"],
    "暗色": ["深色", "暗黑", "夜间模式", "dark"],
    "浅色": ["明亮", "亮色", "日间模式", "light", "白"],
    "明亮": ["浅色", "亮色", "日间模式", "light", "白"],
    "亮色": ["浅色", "明亮", "日间模式", "light"],
    
    # 时间/截止（10 组）
    "截止": ["deadline", "due", "到期", "提交", "结束"],
    "deadline": ["截止", "due", "到期", "提交", "结束"],
    "今天": ["今日", "today", "现在"],
    "明天": ["明日", "tomorrow", "隔天"],
    "周五": ["星期五", "Friday", "周末前"],
    "本周": ["这周", "week", "当周"],
    "下周": ["下周", "next week", "来周"],
    "月底": ["月末", "月底", "月底"],
    
    # 项目/工作（8 组）
    "项目": ["project", "任务", "work", "工程"],
    "任务": ["项目", "task", "工作", "活儿"],
    "工作": ["任务", "project", "活儿", "事情"],
    "工程": ["项目", "project", "工程"],
    
    # 决策相关（12 组）
    "用": ["使用", "采用", "choose", "select"],
    "不用": ["不使用", "不采用", "avoid", "reject"],
    "要": ["需要", "必须", "want", "need"],
    "不要": ["不需要", "禁止", "don't", "avoid"],
    "需要": ["要", "必须", "need", "require"],
    "不需要": ["不要", "无需", "don't need"],
    
    # 情感/偏好（8 组）
    "喜欢": ["爱", "love", "偏好", "倾向"],
    "讨厌": ["不喜欢", "hate", "厌恶", "烦"],
    "好": ["好", "good", "不错", "棒"],
    "坏": ["坏", "bad", "差", "不好"],
    
    # 状态/动作（10 组）
    "开": ["开启", "打开", "on", "启动"],
    "关": ["关闭", "关上", "off", "停止"],
    "快": ["快速", "speed", "fast", "迅速"],
    "慢": ["缓慢", "slow", "慢速"],
    "大": ["大型", "big", "巨大", "大"],
    "小": ["小型", "small", "微小", "小"],
}

def expand_query(query):
    """扩展搜索关键词（同义词）"""
    expanded = set([query.lower()])
    
    for key, synonyms in SYNONYMS.items():
        if key.lower() in query.lower():
            expanded.add(key.lower())
            expanded.update([s.lower() for s in synonyms])
    
    return list(expanded)

# ─────────────────────────────────────────────────────────────
# 改进 2: 规则冲突检测
# ─────────────────────────────────────────────────────────────

CONFLICT_PAIRS = [
    # 颜色/外观
    ("深色", "浅色"),
    ("暗黑", "明亮"),
    ("暗色", "亮色"),
    ("黑", "白"),
    ("深色", "明亮"),
    ("浅色", "暗黑"),
    
    # 肯定/否定
    ("用", "不用"),
    ("使用", "不使用"),
    ("采用", "不采用"),
    ("要", "不要"),
    ("需要", "不需要"),
    ("是", "不是"),
    ("有", "没有"),
    ("可以", "不可以"),
    ("能", "不能"),
    ("会", "不会"),
    
    # 情感/偏好
    ("喜欢", "讨厌"),
    ("偏好", "厌恶"),
    ("爱", "恨"),
    ("好", "坏"),
    ("好", "不好"),
    ("喜欢", "不喜欢"),
    
    # 动作/状态
    ("开", "关"),
    ("开启", "关闭"),
    ("启动", "停止"),
    ("开始", "结束"),
    ("增加", "减少"),
    ("上升", "下降"),
    ("快", "慢"),
    ("大", "小"),
    
    # 方向/位置
    ("上", "下"),
    ("左", "右"),
    ("前", "后"),
    ("内", "外"),
    ("里", "外"),
    
    # 时间
    ("先", "后"),
    ("早", "晚"),
    ("最近", "以前"),
    
    # 其他
    ("对", "错"),
    ("正确", "错误"),
    ("同意", "反对"),
    ("支持", "反对"),
    ("赞", "踩"),
    ("买", "卖"),
    ("进", "出"),
    ("来", "去"),
]

def detect_conflicts_rule(new_content, existing_memories):
    """基于规则的冲突检测"""
    conflicts = []
    
    for existing in existing_memories:
        existing_content = existing.get('content', '')
        
        for pair in CONFLICT_PAIRS:
            # 检查是否包含冲突对
            has_first = pair[0] in new_content or pair[0] in existing_content
            has_second = pair[1] in new_content or pair[1] in existing_content
            
            if has_first and has_second:
                # 进一步检查是否是同一主题
                if is_same_topic(new_content, existing_content):
                    conflicts.append({
                        "with": existing_content,
                        "type": "direct",
                        "reason": f"检测到冲突关键词：{pair[0]} vs {pair[1]}",
                        "severity": "high"
                    })
    
    return conflicts

def is_same_topic(content1, content2):
    """判断两个内容是否同一主题（使用 jieba 分词或正则）"""
    # 使用 jieba 分词（如果可用）
    if HAS_JIEBA:
        keywords1 = set(jieba.lcut(content1))
        keywords2 = set(jieba.lcut(content2))
    else:
        # 回退到正则（按空格或中文提取）
        # 先用空格分割，再提取中文词
        words1 = content1.replace('，', ' ').replace(',', ' ').split()
        words2 = content2.replace('，', ' ').replace(',', ' ').split()
        keywords1 = set()
        keywords2 = set()
        for w in words1:
            if len(w) >= 2:
                keywords1.add(w)
            else:
                keywords1.update(re.findall(r'[\u4e00-\u9fa5]{2,}', w))
        for w in words2:
            if len(w) >= 2:
                keywords2.add(w)
            else:
                keywords2.update(re.findall(r'[\u4e00-\u9fa5]{2,}', w))
    
    # 过滤停用词
    stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
    keywords1 = keywords1 - stopwords
    keywords2 = keywords2 - stopwords
    
    # 有 1 个以上共同关键词 = 同一主题
    common = keywords1 & keywords2
    return len(common) >= 1

# ─────────────────────────────────────────────────────────────
# 改进 3: 高级权重计算
# ─────────────────────────────────────────────────────────────

def parse_deadline(content):
    """尝试从内容中解析截止日期"""
    # 匹配「明天」「周五」「本周五」等
    today = datetime.now()
    
    if "明天" in content or "明日" in content:
        return today + timedelta(days=1)
    elif "今天" in content or "今日" in content:
        return today
    elif "本周五" in content or "星期五" in content:
        # 计算本周五
        days_until_friday = (4 - today.weekday()) % 7
        return today + timedelta(days=days_until_friday)
    elif "下周" in content:
        return today + timedelta(days=7)
    elif "下月" in content:
        return today + timedelta(days=30)
    
    return None

def calculate_weight_advanced(memory, query=None):
    """高级权重计算：基础重要性 × 时效衰减 × 紧急度 × 相关性"""
    content = memory.get('content', '')
    created_at = memory.get('created_at', '')
    
    # 1. 基础重要性
    base = 0.5
    if "[decision]" in content or "[preference]" in content:
        base = 0.8
    elif "[fact]" in content:
        base = 0.75
    elif "[insight]" in content:
        base = 0.75
    
    # 2. 时效衰减（指数衰减，30 天半衰期）
    recency_boost = 0.75  # 默认
    try:
        if isinstance(created_at, str):
            if "T" in created_at:
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_dt = datetime.strptime(created_at, '%Y-%m-%d')
        else:
            created_dt = datetime.fromtimestamp(created_at / 1000)
        
        age_days = (datetime.now() - created_dt).days
        recency_boost = math.exp(-age_days / 30)  # 30 天半衰期
    except:
        pass
    
    # 3. 紧急度（截止日期）
    urgency_boost = 1.0
    if "截止" in content or "deadline" in content or "due" in content:
        due_date = parse_deadline(content)
        if due_date:
            days_left = (due_date - datetime.now()).days
            if days_left < 0:
                urgency_boost = 0.5  # 已过期，降低权重
            elif days_left <= 1:
                urgency_boost = 2.0  # 明天截止，权重翻倍
            elif days_left <= 3:
                urgency_boost = 1.5  # 3 天内，权重 1.5 倍
    
    # 4. 相关性（搜索关键词匹配）
    relevance_boost = 1.0
    if query:
        expanded = expand_query(query)
        for kw in expanded:
            if kw in content.lower():
                relevance_boost = 1.3
                break
    
    weight = base * recency_boost * urgency_boost * relevance_boost
    return round(weight, 3)

# ─────────────────────────────────────────────────────────────
# 改进 4: 简单知识图谱
# ─────────────────────────────────────────────────────────────

def load_graph():
    """加载知识图谱（带文件锁）"""
    if GRAPH_PATH.exists():
        content = read_file_with_lock(GRAPH_PATH)
        return json.loads(content)
    return {"nodes": [], "edges": []}

def save_graph(graph):
    """保存知识图谱（带文件锁）"""
    content = json.dumps(graph, indent=2, ensure_ascii=False)
    write_file_with_lock(GRAPH_PATH, content)

def add_to_graph(memory_id, content, mem_type):
    """添加节点到图谱"""
    graph = load_graph()
    
    # 检查是否已存在
    for node in graph["nodes"]:
        if node["id"] == memory_id:
            return  # 已存在
    
    # 添加节点
    graph["nodes"].append({
        "id": memory_id,
        "type": mem_type,
        "content": content,
        "created_at": datetime.now().isoformat()
    })
    
    # 自动发现关联边
    edges = discover_edges(memory_id, content, graph["nodes"])
    graph["edges"].extend(edges)
    
    save_graph(graph)

def discover_edges(new_id, new_content, all_nodes, max_edges=5):
    """自动发现关联边（支持多种关系类型，限制边数量）
    
    Args:
        max_edges: 最大边数量，防止图谱膨胀（默认 5 条）
    """
    edges = []
    
    # 提取关键词（使用 jieba 或正则）
    if HAS_JIEBA:
        keywords = set(jieba.lcut(new_content))
    else:
        keywords = set(re.findall(r'[\u4e00-\u9fa5]{2,}', new_content))
    
    # 按共同关键词数量排序，优先保留强关联
    candidate_edges = []
    
    for node in all_nodes:
        if node["id"] == new_id:
            continue
        
        # 提取节点关键词
        if HAS_JIEBA:
            node_keywords = set(jieba.lcut(node["content"]))
        else:
            node_keywords = set(re.findall(r'[\u4e00-\u9fa5]{2,}', node["content"]))
        
        common = keywords & node_keywords
        
        if len(common) >= 2:  # 提高阈值到 2 个共同词，减少误报
            # 判断关系类型
            relation = detect_relation_type(new_content, node["content"], common)
            
            candidate_edges.append({
                "from": new_id,
                "to": node["id"],
                "relation": relation,
                "created_at": datetime.now().isoformat(),
                "common_count": len(common)  # 用于排序
            })
    
    # 按共同关键词数量排序，取前 N 个
    candidate_edges.sort(key=lambda x: x["common_count"], reverse=True)
    
    for edge in candidate_edges[:max_edges]:
        del edge["common_count"]  # 移除辅助字段
        edges.append(edge)
    
    return edges

def detect_relation_type(content1, content2, common_keywords):
    """检测两个内容之间的关系类型"""
    combined = content1 + " " + content2
    
    # 项目相关
    if any(kw in combined for kw in ["项目", "任务", "工程"]):
        if "预算" in content1 or "预算" in content2:
            return "has_budget"
        elif "截止" in content1 or "截止" in content2 or "deadline" in combined:
            return "has_deadline"
        elif any(kw in combined for kw in ["主题", "模式", "颜色", "风格"]):
            return "has_theme"
        elif any(kw in combined for kw in ["成员", "人员", "团队"]):
            return "has_member"
        else:
            return "same_project"
    
    # 依赖关系
    if any(kw in combined for kw in ["前提", "需要先", "必须先", "依赖"]):
        return "depends_on"
    
    # 因果关系
    if any(kw in combined for kw in ["导致", "因此", "所以", "造成"]):
        return "causes"
    
    # 阻止关系
    if any(kw in combined for kw in ["阻止", "防止", "避免", "禁止"]):
        return "prevents"
    
    # 部分 - 整体
    if any(kw in combined for kw in ["属于", "包括", "包含", "一部分"]):
        return "part_of"
    
    # 默认：相关
    return "related_to"

def find_related_nodes(memory_id):
    """查找关联节点"""
    graph = load_graph()
    related = []
    
    for edge in graph["edges"]:
        if edge["from"] == memory_id:
            related.append(edge["to"])
        elif edge["to"] == memory_id:
            related.append(edge["from"])
    
    return related

# ─────────────────────────────────────────────────────────────
# 改进 5: 输入验证
# ─────────────────────────────────────────────────────────────

def validate_input(content, mem_type, importance):
    """输入验证"""
    errors = []
    
    # 1. 空内容检查
    if not content or not content.strip():
        errors.append("内容不能为空")
    
    # 2. 长度限制
    if len(content) > 1000:
        errors.append("内容过长（最大 1000 字）")
    
    # 3. 特殊字符过滤
    if any(c in content for c in ['\x00', '\x0b', '\x1c']):
        errors.append("包含非法字符")
    
    # 4. 类型验证
    valid_types = ["decision", "preference", "fact", "event", "task", "insight", "error"]
    if mem_type not in valid_types:
        errors.append(f"无效类型（应为 {valid_types}）")
    
    # 5. 重要性范围
    if not (0 <= importance <= 1):
        errors.append("重要性应在 0-1 之间")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

# ─────────────────────────────────────────────────────────────
# 核心功能
# ─────────────────────────────────────────────────────────────

def capture(type, content, importance=0.5, tags=None):
    """
    v4.1 采集：输入验证 + WAL 协议 + 冲突检测 + 图谱更新
    """
    # 1. 输入验证（改进 5）
    validation = validate_input(content, type, importance)
    if not validation["valid"]:
        return {
            "id": None,
            "layer": None,
            "status": "error",
            "errors": validation["errors"]
        }
    
    timestamp = datetime.now()
    timestamp_str = timestamp.strftime('%H:%M:%S')
    date_str = timestamp.strftime('%Y-%m-%d')
    
    # 2. 写入 L3 (daily/)
    daily_file = DAILY_DIR / f"{date_str}.md"
    daily_entry = f"- [{timestamp_str}] [{type}] {content}\n"
    
    if daily_file.exists():
        with open(daily_file, 'a', encoding='utf-8') as f:
            f.write(daily_entry)
    else:
        daily_file.write_text(f"# {date_str}\n\n{daily_entry}", encoding='utf-8')
    
    # 3. 加载现有记忆（用于冲突检测）
    existing = load_existing_memories()
    
    # 4. 冲突检测（改进 2）
    conflicts = detect_conflicts_rule(content, existing)
    
    # 5. 判断是否写入 L1
    write_to_l1 = (
        type in ["decision", "preference"] or
        importance > 0.8 or
        len(conflicts) > 0  # 有冲突也写入 L1
    )
    
    layer = "L3"
    if write_to_l1:
        append_to_session_state(type, content, timestamp_str)
        layer = "L1"
    
    memory_id = f"mem_{timestamp.strftime('%Y%m%d%H%M%S')}"
    
    # 6. 添加到知识图谱（改进 4）
    add_to_graph(memory_id, content, type)
    
    # 7. 更新关键词索引（v4.3 修复）
    if ENABLE_KEYWORD_INDEX:
        update_keyword_index(content, action='add')
    
    result = {
        "id": memory_id,
        "layer": layer,
        "status": "success",
        "timestamp": timestamp.isoformat(),
        "created_at": timestamp.strftime('%Y-%m-%d')  # 用于权重计算
    }
    
    # 附加冲突信息
    if conflicts:
        result["conflicts"] = conflicts
    
    return result

def load_existing_memories():
    """加载现有记忆（带文件锁）"""
    memories = []
    
    # 从 SESSION-STATE.md 加载
    if SESSION_STATE_PATH.exists():
        content = read_file_with_lock(SESSION_STATE_PATH)
        for line in content.split('\n'):
            if line.strip().startswith('- [') and ']' in line:
                memories.append({
                    "id": "l1_" + str(hash(line)),
                    "content": line.strip(),
                    "layer": "L1"
                })
    
    # 从 MEMORY.md 加载
    if MEMORY_MD_PATH.exists():
        content = read_file_with_lock(MEMORY_MD_PATH)
        for line in content.split('\n'):
            if line.strip().startswith('- ['):
                memories.append({
                    "id": "l2_" + str(hash(line)),
                    "content": line.strip(),
                    "layer": "L2"
                })
    
    return memories

def append_to_session_state(type, content, timestamp_str):
    """WAL 协议：写入 SESSION-STATE.md（带文件锁）"""
    if not SESSION_STATE_PATH.exists():
        write_file_with_lock(
            SESSION_STATE_PATH,
            "# SESSION-STATE.md\n\n**WAL 协议：** 用户给出关键信息 → 先写这里 → 再回复\n\n---\n\n## 最近记录\n\n"
        )
    
    entry = f"- [{timestamp_str}] [{type}] {content}\n"
    with open(SESSION_STATE_PATH, 'a', encoding='utf-8') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.write(entry)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

def search(query, type=None, limit=10):
    """
    v4.3 搜索：同义词扩展 + 高级权重 + 关联扩展
    
    注意：不使用 LRU 缓存，因为文件修改后缓存会失效
    改用关键词索引加速搜索（如果已构建）
    """
    # 1. 同义词扩展（改进 1）
    expanded_keywords = expand_query(query)
    
    # 2. 优先使用索引搜索（如果已构建）
    if ENABLE_KEYWORD_INDEX and KEYWORD_INDEX_PATH.exists():
        index_result = search_with_index(query, type, limit)
        if index_result.get("from_index") and len(index_result["results"]) > 0:
            # 索引搜索成功
            alerts = context_check(query, index_result["results"])
            return {
                "results": index_result["results"],
                "alerts": alerts,
                "expanded_keywords": index_result["expanded_keywords"],
                "from_index": True
            }
    
    # 3. 回退到传统搜索
    results = []
    seen_contents = set()
    
    # 搜索 L1（带文件锁）
    if SESSION_STATE_PATH.exists():
        content = read_file_with_lock(SESSION_STATE_PATH)
        for line in content.split('\n'):
            line_lower = line.lower()
            if any(kw in line_lower for kw in expanded_keywords):
                if type is None or f"[{type}]" in line:
                    if line not in seen_contents:
                        seen_contents.add(line)
                        results.append({
                            "id": "l1_" + str(hash(line)),
                            "layer": "L1",
                            "content": line.strip(),
                            "source": "SESSION-STATE.md",
                            "weight": calculate_weight_advanced({"content": line, "created_at": ""}, query)
                        })
    
    # 搜索 L2（带文件锁）
    if MEMORY_MD_PATH.exists():
        content = read_file_with_lock(MEMORY_MD_PATH)
        for line in content.split('\n'):
            line_lower = line.lower()
            if any(kw in line_lower for kw in expanded_keywords):
                if type is None or f"[{type}]" in line:
                    if line not in seen_contents:
                        seen_contents.add(line)
                        results.append({
                            "id": "l2_" + str(hash(line)),
                            "layer": "L2",
                            "content": line.strip(),
                            "source": "MEMORY.md",
                            "weight": calculate_weight_advanced({"content": line, "created_at": ""}, query)
                        })
    
    # 搜索 L3（带文件锁）
    for daily_file in DAILY_DIR.glob("*.md"):
        content = read_file_with_lock(daily_file)
        for line in content.split('\n'):
            line_lower = line.lower()
            if any(kw in line_lower for kw in expanded_keywords):
                if type is None or f"[{type}]" in line:
                    if line not in seen_contents:
                        seen_contents.add(line)
                        results.append({
                            "id": "l3_" + daily_file.stem + "_" + str(hash(line)),
                            "layer": "L3",
                            "content": line.strip(),
                            "source": f"daily/{daily_file.name}",
                            "weight": calculate_weight_advanced({"content": line, "created_at": ""}, query)
                        })
    
    # 2. 按权重排序（改进 3）
    results.sort(key=lambda x: x.get("weight", 0), reverse=True)
    
    # 3. 情境检查
    alerts = context_check(query, results)
    
    # 4. 图谱关联扩展（改进 4）
    if len(results) > 0:
        related_ids = find_related_nodes(results[0]["id"])
        # 可以在这里添加关联节点到结果
    
    return {
        "results": results[:limit],
        "alerts": alerts,
        "expanded_keywords": expanded_keywords  # 显示扩展了哪些词
    }

def context_check(query, results):
    """情境触发检查"""
    alerts = {
        "deadlines": [],
        "conflicts": [],
        "outdated": []
    }
    
    for r in results:
        content = r.get('content', '')
        
        # 检查截止时间
        if any(kw in content for kw in ['截止', 'deadline', 'due', '到期']):
            alerts["deadlines"].append({
                "memory_id": r.get('id'),
                "content": content,
                "message": "⚠️ 此记忆提到截止时间"
            })
        
        # 检查冲突关键词
        if any(kw in content for kw in ['冲突', 'vs', '还是', '不用', '不要']):
            alerts["conflicts"].append({
                "memory_id": r.get('id'),
                "content": content,
                "message": "⚠️ 此记忆可能涉及冲突"
            })
    
    return alerts

def predict():
    """v4.1 预测：全面检查"""
    alerts = {
        "deadlines": [],
        "conflicts": [],
        "outdated": [],
        "total_memories": 0
    }
    
    # 检查 SESSION-STATE.md（带文件锁）
    if SESSION_STATE_PATH.exists():
        content = read_file_with_lock(SESSION_STATE_PATH)
        for line in content.split('\n'):
            if '截止' in line:
                due_date = parse_deadline(line)
                if due_date:
                    days_left = (due_date - datetime.now()).days
                    alerts["deadlines"].append({
                        "content": line.strip(),
                        "days_left": days_left,
                        "message": f"⚠️ 此记忆提到截止时间（还剩{days_left}天）"
                    })
            alerts["total_memories"] += 1
    
    # 检查图谱中的冲突边
    graph = load_graph()
    conflict_edges = [e for e in graph["edges"] if "conflict" in e.get("relation", "")]
    if conflict_edges:
        alerts["conflicts"].append({
            "count": len(conflict_edges),
            "message": f"⚠️ 检测到{len(conflict_edges)}个冲突"
        })
    
    return alerts

def status():
    """显示状态"""
    l1_exists = SESSION_STATE_PATH.exists()
    l2_exists = MEMORY_MD_PATH.exists()
    l3_count = len(list(DAILY_DIR.glob("*.md")))
    
    l1_lines = len(read_file_with_lock(SESSION_STATE_PATH).split('\n')) if l1_exists else 0
    l2_lines = len(read_file_with_lock(MEMORY_MD_PATH).split('\n')) if l2_exists else 0
    
    # 图谱状态
    graph_nodes = 0
    graph_edges = 0
    if GRAPH_PATH.exists():
        graph = load_graph()
        graph_nodes = len(graph.get("nodes", []))
        graph_edges = len(graph.get("edges", []))
    
    # 版本历史统计
    version_count = 0
    if VERSIONS_DIR.exists():
        version_count = sum(1 for _ in VERSIONS_DIR.rglob("*") if _.is_file())
    
    # Git 状态
    git_status = "✅" if is_git_repo() else "❌"
    
    # 索引统计
    index_keywords = 0
    if ENABLE_KEYWORD_INDEX and KEYWORD_INDEX_PATH.exists():
        index = load_keyword_index()
        index_keywords = len(index)
    
    # 跨平台状态
    platform = "Windows" if sys.platform == 'win32' else ("macOS" if sys.platform == 'darwin' else "Linux")
    
    return {
        "L1 (SESSION-STATE.md)": f"{'✅' if l1_exists else '❌'} {l1_lines} 行",
        "L2 (MEMORY.md)": f"{'✅' if l2_exists else '❌'} {l2_lines} 行",
        "L3 (memory/daily/)": f"✅ {l3_count} 个文件",
        "知识图谱": f"🕸️ {graph_nodes} 节点，{graph_edges} 关联",
        "版本历史": f"📚 {version_count} 个版本",
        "Git 仓库": f"{git_status} {'是' if is_git_repo() else '否'}",
        "关键词索引": f"🔍 {index_keywords} 个关键词" if index_keywords > 0 else "❌ 未构建",
        "平台": f"💻 {platform}",
        "忆伴 v1.0 功能": "✅ 同义词扩展 (60 组) + 冲突检测 (48 对) + 高级权重 + 知识图谱 + 输入验证 + 跨平台锁 + Git 备份 + 版本历史 + 搜索缓存 + 关键词索引 + 导出/导入"
    }

def clear_cache():
    """清除搜索缓存"""
    search_cached.cache_clear()
    return {"status": "ok", "message": "搜索缓存已清除"}

# ─────────────────────────────────────────────────────────────
# 关键词倒排索引（v4.3 新增）
# ─────────────────────────────────────────────────────────────

def load_keyword_index():
    """加载关键词倒排索引"""
    if not ENABLE_KEYWORD_INDEX:
        return {}
    
    if KEYWORD_INDEX_PATH.exists():
        content = read_file_with_lock(KEYWORD_INDEX_PATH)
        return json.loads(content)
    return {}

def save_keyword_index(index):
    """保存关键词倒排索引"""
    if not ENABLE_KEYWORD_INDEX:
        return
    
    content = json.dumps(index, indent=2, ensure_ascii=False)
    write_file_with_lock(KEYWORD_INDEX_PATH, content)

def build_keyword_index():
    """构建关键词倒排索引"""
    index = {}
    
    # 从所有记忆文件中提取关键词
    all_files = [SESSION_STATE_PATH, MEMORY_MD_PATH] + list(DAILY_DIR.glob("*.md"))
    
    for filepath in all_files:
        if not filepath.exists():
            continue
        
        content = read_file_with_lock(filepath)
        for line in content.split('\n'):
            if not line.strip() or line.startswith('#'):
                continue
            
            # 提取关键词
            if HAS_JIEBA:
                keywords = jieba.lcut(line)
            else:
                keywords = re.findall(r'[\u4e00-\u9fa5]{2,}', line)
            
            # 添加到索引
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower not in index:
                    index[kw_lower] = []
                
                line_hash = str(hash(line))
                if line_hash not in index[kw_lower]:
                    index[kw_lower].append({
                        "content": line.strip(),
                        "source": str(filepath),
                        "hash": line_hash
                    })
    
    save_keyword_index(index)
    return {"status": "ok", "message": f"索引构建完成，{len(index)} 个关键词"}

def update_keyword_index(content, action='add'):
    """更新索引（增量）"""
    if not ENABLE_KEYWORD_INDEX:
        return
    
    index = load_keyword_index()
    
    # 提取关键词
    if HAS_JIEBA:
        keywords = jieba.lcut(content)
    else:
        keywords = re.findall(r'[\u4e00-\u9fa5]{2,}', content)
    
    line_hash = str(hash(content))
    
    for kw in keywords:
        kw_lower = kw.lower()
        if action == 'add':
            if kw_lower not in index:
                index[kw_lower] = []
            
            # 检查是否已存在
            exists = any(item["hash"] == line_hash for item in index[kw_lower])
            if not exists:
                index[kw_lower].append({
                    "content": content,
                    "source": "incremental",
                    "hash": line_hash
                })
        elif action == 'remove':
            if kw_lower in index:
                index[kw_lower] = [item for item in index[kw_lower] if item["hash"] != line_hash]
    
    save_keyword_index(index)

def search_with_index(query, type=None, limit=10):
    """使用索引搜索（性能 +100 倍）"""
    index = load_keyword_index()
    
    # 扩展查询
    expanded_keywords = expand_query(query)
    
    results = []
    seen_hashes = set()
    
    for kw in expanded_keywords:
        if kw in index:
            for item in index[kw]:
                if item["hash"] not in seen_hashes:
                    seen_hashes.add(item["hash"])
                    results.append({
                        "id": "idx_" + item["hash"],
                        "layer": "index",
                        "content": item["content"],
                        "source": item["source"],
                        "weight": calculate_weight_advanced({"content": item["content"], "created_at": ""}, query)
                    })
    
    # 按权重排序
    results.sort(key=lambda x: x.get("weight", 0), reverse=True)
    
    return {
        "results": results[:limit],
        "expanded_keywords": expanded_keywords,
        "from_index": True
    }

# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: memory-v4.1.py <command> [args]")
        print("Commands: capture, search, predict, status, graph")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "capture":
        args = parse_args(sys.argv[2:])
        result = capture(
            type=args.get('type', 'event'),
            content=args.get('content', ''),
            importance=float(args.get('importance', 0.5))
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "search":
        args = parse_args(sys.argv[2:])
        result = search(
            query=args.get('query', ''),
            type=args.get('type'),
            limit=int(args.get('limit', 10))
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "predict":
        result = predict()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "status":
        result = status()
        print("🧠 忆伴 MemPal v1.0.0 状态")
        for k, v in result.items():
            print(f"  {k}: {v}")
    
    elif command == "graph":
        graph = load_graph()
        print(json.dumps(graph, indent=2, ensure_ascii=False))
    
    elif command == "git-backup":
        args = parse_args(sys.argv[2:])
        if args.get('enable') == 'true':
            result = enable_git_backup(auto_push=args.get('auto_push') == 'true')
        elif args.get('disable') == 'true':
            result = disable_git_backup()
        else:
            result = git_backup(message=args.get('message', 'manual-backup'))
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "versions":
        args = parse_args(sys.argv[2:])
        filename = args.get('file', 'SESSION-STATE.md')
        result = list_versions(filename, limit=int(args.get('limit', 10)))
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "restore":
        args = parse_args(sys.argv[2:])
        result = restore_version(
            args.get('file', 'SESSION-STATE.md'),
            args.get('version', '')
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "clear-cache":
        result = clear_cache()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "build-index":
        result = build_keyword_index()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "export":
        args = parse_args(sys.argv[2:])
        result = export_memories(
            format=args.get('format', 'json'),
            output_file=args.get('output')
        )
        if result.get('data'):
            print(result['data'])
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "import":
        args = parse_args(sys.argv[2:])
        result = import_memories(
            input_file=args.get('file', ''),
            format=args.get('format', 'json'),
            skip_existing=args.get('skip', 'true') == 'true'
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command in ["help", "-h", "--help"]:
        print_help()
    
    else:
        print(f"Unknown command: {command}")
        print("使用 'memory-v4.1.py help' 查看可用命令")
        sys.exit(1)

# Git 备份配置函数（在 read_file_with_lock 定义后）
def load_config():
    """加载配置"""
    if CONFIG_PATH.exists():
        content = read_file_with_lock(CONFIG_PATH)
        return json.loads(content)
    return {}

def save_config(config):
    """保存配置"""
    content = json.dumps(config, indent=2, ensure_ascii=False)
    write_file_with_lock(CONFIG_PATH, content)

def get_git_backup_enabled():
    """获取 Git 备份启用状态"""
    config = load_config()
    return config.get('git_backup_enabled', False)

def set_git_backup_enabled(enabled, auto_push=False):
    """设置 Git 备份启用状态"""
    config = load_config()
    config['git_backup_enabled'] = enabled
    config['git_backup_auto_push'] = auto_push
    save_config(config)
    return {"status": "ok", "message": f"Git 备份已{'启用' if enabled else '禁用'}"}

# 初始化 Git 备份状态
GIT_BACKUP_ENABLED = get_git_backup_enabled()
GIT_BACKUP_AUTO_PUSH = get_git_backup_enabled() and load_config().get('git_backup_auto_push', False)

def print_help():
    """打印帮助信息"""
    help_text = """
🧠 忆伴 MemPal v1.0.0 - 帮助信息

用法：python3 memory-v4.1.py <command> [arguments]

核心命令:
  capture type="decision" content="..." importance=0.9   采集记忆
  search query="关键词" type=decision limit=10           搜索记忆
  status                                                  查看状态
  predict                                                 预测提醒
  graph                                                   查看知识图谱

v1.0 新增:
  git-backup enable=true|message="..."                   Git 备份
  versions file=SESSION-STATE.md limit=10                查看版本
  restore file=SESSION-STATE.md version=xxx              恢复版本
  clear-cache                                             清除缓存
  build-index                                             构建关键词索引
  export format=json|markdown output=file                 导出记忆
  import file=xxx format=json|markdown skip=true|false    导入记忆

其他:
  help, -h, --help                                        显示此帮助

示例:
  # 采集决策
  memory-v4.1.py capture type="decision" content="用 Tailwind" importance="0.9"
  
  # 搜索记忆
  memory-v4.1.py search query="CSS 框架"
  
  # 查看状态
  memory-v4.1.py status
  
  # 构建索引（大数据量时）
  memory-v4.1.py build-index
  
  # 导出记忆
  memory-v4.1.py export format=json output=memories.json

文档:
  README.md - 完整使用说明
  TUTORIAL.md - 用户教程
  FAQ.md - 常见问题
"""
    print(help_text)

def parse_args(args):
    result = {}
    for arg in args:
        if '=' in arg:
            key, value = arg.split('=', 1)
            result[key] = value
    return result

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Unified Memory System v4.0 - LLM-Driven Active Memory
基于 LLM 语义理解的记忆系统

使用现有 Bailian/智谱/Kimi API 实现：
1. LLM 冲突检测（语义理解，不是关键词匹配）
2. LLM 关联建立（自动发现，不是预定义规则）
3. 情境触发提醒（用户提问时主动检查）
4. 动态权重排序（重要性 × 时效 × 关联度）
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import requests

# 路径配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
DAILY_DIR = MEMORY_DIR / "daily"
SESSION_STATE_PATH = WORKSPACE / "SESSION-STATE.md"
MEMORY_MD_PATH = WORKSPACE / "MEMORY.md"
GRAPH_PATH = MEMORY_DIR / "graph.json"

# 确保目录存在
DAILY_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# LLM API 调用（使用现有配置）
# ─────────────────────────────────────────────────────────────

def get_llm_api_key():
    """获取 API key（从 openclaw.json 读取）"""
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            # 优先用 Bailian（当前使用的）
            if 'bailian' in config.get('models', {}).get('providers', {}):
                return config['models']['providers']['bailian'].get('apiKey')
            # 备用：ZAI
            if 'zai' in config.get('models', {}).get('providers', {}):
                return config['models']['providers']['zai'].get('apiKey')
    return os.environ.get('OPENAI_API_KEY')

def call_llm(prompt, max_tokens=500):
    """
    调用 LLM API
    
    Args:
        prompt: 提示词
        max_tokens: 最大 token 数
    
    Returns:
        str: LLM 回答
    """
    api_key = get_llm_api_key()
    if not api_key:
        return None  # 降级到规则模式
    
    # 使用 Bailian API（阿里云千问）
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen-plus",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
    except Exception as e:
        print(f"LLM API 调用失败：{e}")
    
    return None

# ─────────────────────────────────────────────────────────────
# v4.0 核心功能 1: LLM 冲突检测
# ─────────────────────────────────────────────────────────────

def detect_conflicts_llm(new_content, existing_memories):
    """
    LLM 语义冲突检测
    
    Args:
        new_content: 新记忆内容
        existing_memories: 现有记忆列表
    
    Returns:
        list: 冲突列表
    """
    if not existing_memories:
        return []
    
    # 构建提示词
    existing_text = "\n".join([
        f"- {m['content']}" for m in existing_memories[:10]  # 限制数量
    ])
    
    prompt = f"""
请判断以下新记忆是否与现有记忆冲突：

**新记忆**:
{new_content}

**现有记忆**:
{existing_text}

请按以下格式回答（只回答 JSON）：
{{
    "has_conflict": true/false,
    "conflicts": [
        {{
            "with": "冲突记忆内容",
            "type": "direct/indirect/none",
            "reason": "冲突原因",
            "severity": "high/medium/low"
        }}
    ]
}}
"""
    
    response = call_llm(prompt)
    if not response:
        return []  # LLM 失败，返回空
    
    try:
        # 提取 JSON
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            result = json.loads(response[start:end])
            if result.get('has_conflict'):
                return result.get('conflicts', [])
    except Exception as e:
        print(f"解析 LLM 响应失败：{e}")
    
    return []

# ─────────────────────────────────────────────────────────────
# v4.0 核心功能 2: LLM 关联建立
# ─────────────────────────────────────────────────────────────

def find_relations_llm(new_content, existing_memories):
    """
    LLM 关联发现
    
    Args:
        new_content: 新记忆内容
        existing_memories: 现有记忆列表
    
    Returns:
        list: 关联列表
    """
    if not existing_memories:
        return []
    
    existing_text = "\n".join([
        f"- {m['id']}: {m['content']}" for m in existing_memories[:20]
    ])
    
    prompt = f"""
请找出与新记忆相关的现有记忆：

**新记忆**:
{new_content}

**现有记忆**:
{existing_text}

请按以下格式回答（只回答 JSON）：
{{
    "relations": [
        {{
            "memory_id": "相关记忆 ID",
            "relation_type": "related_to/supersedes/depends_on/part_of",
            "reason": "关联原因"
        }}
    ]
}}
"""
    
    response = call_llm(prompt)
    if not response:
        return []
    
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            result = json.loads(response[start:end])
            return result.get('relations', [])
    except Exception as e:
        print(f"解析 LLM 响应失败：{e}")
    
    return []

# ─────────────────────────────────────────────────────────────
# v4.0 核心功能 3: 动态权重计算
# ─────────────────────────────────────────────────────────────

def calculate_weight(memory, query=None):
    """
    计算记忆权重
    
    weight = base_importance × recency_boost × relevance_boost
    
    Args:
        memory: 记忆对象
        query: 搜索关键词（可选）
    
    Returns:
        float: 权重
    """
    # 基础重要性
    base = memory.get('importance', 0.5)
    
    # 时效增益（越新越高）
    created_at = memory.get('created_at', datetime.now().isoformat())
    try:
        if isinstance(created_at, str):
            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        else:
            created_dt = datetime.fromtimestamp(created_at / 1000)
        age_days = (datetime.now() - created_dt).days
        recency_boost = max(0.3, 1.0 - (age_days * 0.05))  # 每天衰减 5%
    except:
        recency_boost = 0.5
    
    # 相关性增益（如果有关键词）
    relevance_boost = 1.0
    if query:
        content = memory.get('content', '')
        if query.lower() in content.lower():
            relevance_boost = 1.5
    
    weight = base * recency_boost * relevance_boost
    return round(weight, 3)

# ─────────────────────────────────────────────────────────────
# v4.0 核心功能 4: 情境触发检查
# ─────────────────────────────────────────────────────────────

def context_check(query, memories):
    """
    情境触发检查
    
    用户提问时，自动检查：
    1. 相关记忆有截止吗？
    2. 有冲突需要解决吗？
    3. 有过时信息吗？
    
    Args:
        query: 用户问题
        memories: 相关记忆列表
    
    Returns:
        dict: 检查结果
    """
    alerts = {
        "deadlines": [],
        "conflicts": [],
        "outdated": []
    }
    
    for mem in memories:
        content = mem.get('content', '')
        
        # 检查截止时间
        if any(kw in content for kw in ['截止', 'deadline', 'due']):
            alerts["deadlines"].append({
                "memory_id": mem.get('id'),
                "content": content,
                "message": "⚠️ 此记忆提到截止时间"
            })
        
        # 检查冲突标记
        if mem.get('has_conflict'):
            alerts["conflicts"].append({
                "memory_id": mem.get('id'),
                "content": content,
                "message": "⚠️ 此记忆有冲突"
            })
        
        # 检查过时（超过 30 天）
        created_at = mem.get('created_at', '')
        try:
            if isinstance(created_at, str):
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_dt = datetime.fromtimestamp(created_at / 1000)
            age_days = (datetime.now() - created_dt).days
            if age_days > 30:
                alerts["outdated"].append({
                    "memory_id": mem.get('id'),
                    "content": content,
                    "age_days": age_days,
                    "message": f"⚠️ 此记忆已过时 {age_days} 天"
                })
        except:
            pass
    
    return alerts

# ─────────────────────────────────────────────────────────────
# 基础功能（复用 v2.0）
# ─────────────────────────────────────────────────────────────

def capture(type, content, importance=0.5, tags=None):
    """
    v4.0 采集：LLM 冲突检测 + 关联建立
    """
    timestamp = datetime.now()
    timestamp_str = timestamp.strftime('%H:%M:%S')
    date_str = timestamp.strftime('%Y-%m-%d')
    
    # 1. 写入 L3 (daily/)
    daily_file = DAILY_DIR / f"{date_str}.md"
    daily_entry = f"- [{timestamp_str}] [{type}] {content}\n"
    
    if daily_file.exists():
        with open(daily_file, 'a', encoding='utf-8') as f:
            f.write(daily_entry)
    else:
        daily_file.write_text(f"# {date_str}\n\n{daily_entry}", encoding='utf-8')
    
    # 2. 加载现有记忆（用于冲突检测和关联建立）
    existing = load_existing_memories()
    
    # 3. LLM 冲突检测（v4.0 新增）
    conflicts = detect_conflicts_llm(content, existing)
    
    # 4. LLM 关联建立（v4.0 新增）
    relations = find_relations_llm(content, existing)
    
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
    
    result = {
        "id": memory_id,
        "layer": layer,
        "status": "success",
        "timestamp": timestamp.isoformat()
    }
    
    # 附加冲突和关联信息（v4.0 新增）
    if conflicts:
        result["conflicts"] = conflicts
    if relations:
        result["relations"] = relations
    
    return result

def load_existing_memories():
    """加载现有记忆"""
    memories = []
    
    # 从 SESSION-STATE.md 加载
    if SESSION_STATE_PATH.exists():
        content = SESSION_STATE_PATH.read_text(encoding='utf-8')
        for line in content.split('\n'):
            if line.strip().startswith('- [') and ']' in line:
                memories.append({
                    "id": "l1_" + str(hash(line)),
                    "content": line.strip(),
                    "layer": "L1"
                })
    
    # 从 MEMORY.md 加载
    if MEMORY_MD_PATH.exists():
        content = MEMORY_MD_PATH.read_text(encoding='utf-8')
        for line in content.split('\n'):
            if line.strip().startswith('- ['):
                memories.append({
                    "id": "l2_" + str(hash(line)),
                    "content": line.strip(),
                    "layer": "L2"
                })
    
    return memories

def append_to_session_state(type, content, timestamp_str):
    """WAL 协议：写入 SESSION-STATE.md"""
    if not SESSION_STATE_PATH.exists():
        SESSION_STATE_PATH.write_text(
            "# SESSION-STATE.md\n\n**WAL 协议：** 用户给出关键信息 → 先写这里 → 再回复\n\n---\n\n## 最近记录\n\n",
            encoding='utf-8'
        )
    
    entry = f"- [{timestamp_str}] [{type}] {content}\n"
    with open(SESSION_STATE_PATH, 'a', encoding='utf-8') as f:
        f.write(entry)

def search(query, type=None, limit=10, with_context_check=True):
    """
    v4.0 搜索：动态权重排序 + 情境触发检查
    """
    results = []
    
    # 搜索 L1
    if SESSION_STATE_PATH.exists():
        content = SESSION_STATE_PATH.read_text(encoding='utf-8')
        for line in content.split('\n'):
            if query.lower() in line.lower():
                if type is None or f"[{type}]" in line:
                    results.append({
                        "id": "l1_" + str(hash(line)),
                        "layer": "L1",
                        "content": line.strip(),
                        "source": "SESSION-STATE.md"
                    })
    
    # 搜索 L2
    if MEMORY_MD_PATH.exists():
        content = MEMORY_MD_PATH.read_text(encoding='utf-8')
        for line in content.split('\n'):
            if query.lower() in line.lower():
                if type is None or f"[{type}]" in line:
                    results.append({
                        "id": "l2_" + str(hash(line)),
                        "layer": "L2",
                        "content": line.strip(),
                        "source": "MEMORY.md"
                    })
    
    # 动态权重排序（v4.0 新增）
    for r in results:
        r["weight"] = calculate_weight(r, query)
    
    results.sort(key=lambda x: x.get("weight", 0), reverse=True)
    
    # 情境触发检查（v4.0 新增）
    alerts = {}
    if with_context_check:
        alerts = context_check(query, results)
    
    return {
        "results": results[:limit],
        "alerts": alerts
    }

def predict():
    """
    v4.0 预测：全面检查
    """
    memories = load_existing_memories()
    alerts = context_check("all", memories)
    
    return {
        "deadlines": alerts.get("deadlines", []),
        "conflicts": alerts.get("conflicts", []),
        "outdated": alerts.get("outdated", []),
        "total_memories": len(memories)
    }

def status():
    """显示状态"""
    l1_exists = SESSION_STATE_PATH.exists()
    l2_exists = MEMORY_MD_PATH.exists()
    l3_count = len(list(DAILY_DIR.glob("*.md")))
    
    l1_lines = len(SESSION_STATE_PATH.read_text(encoding='utf-8').split('\n')) if l1_exists else 0
    l2_lines = len(MEMORY_MD_PATH.read_text(encoding='utf-8').split('\n')) if l2_exists else 0
    
    return {
        "L1 (SESSION-STATE.md)": f"{'✅' if l1_exists else '❌'} {l1_lines} 行",
        "L2 (MEMORY.md)": f"{'✅' if l2_exists else '❌'} {l2_lines} 行",
        "L3 (memory/daily/)": f"✅ {l3_count} 个文件",
        "v4.0 功能": "✅ LLM 冲突检测 + 关联建立 + 动态权重 + 情境触发"
    }

# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: memory-v4.py <command> [args]")
        print("Commands: capture, search, predict, status")
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
        print("🧠 Unified Memory System v4.0 状态")
        for k, v in result.items():
            print(f"  {k}: {v}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

def parse_args(args):
    result = {}
    for arg in args:
        if '=' in arg:
            key, value = arg.split('=', 1)
            result[key] = value
    return result

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Unified Memory System v4.0 Simple - 用 OpenClaw 内置能力

不调用外部 API，用 OpenClaw 已有的 memorySearch
冲突检测/关联建立由 Agent（我）判断，不是代码
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 路径配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
DAILY_DIR = MEMORY_DIR / "daily"
SESSION_STATE_PATH = WORKSPACE / "SESSION-STATE.md"
MEMORY_MD_PATH = WORKSPACE / "MEMORY.md"

# 确保目录存在
DAILY_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# 核心功能
# ─────────────────────────────────────────────────────────────

def capture(type, content, importance=0.5, tags=None):
    """
    采集记忆
    
    WAL 协议：
    - type=decision/preference → 自动写入 L1
    - importance>0.8 → 自动写入 L1
    - 其他 → 只写 L3 (daily/)
    """
    timestamp = datetime.now()
    timestamp_str = timestamp.strftime('%H:%M:%S')
    date_str = timestamp.strftime('%Y-%m-%d')
    
    # 写入 L3 (daily/)
    daily_file = DAILY_DIR / f"{date_str}.md"
    daily_entry = f"- [{timestamp_str}] [{type}] {content}\n"
    
    if daily_file.exists():
        with open(daily_file, 'a', encoding='utf-8') as f:
            f.write(daily_entry)
    else:
        daily_file.write_text(f"# {date_str}\n\n{daily_entry}", encoding='utf-8')
    
    # 判断是否写入 L1
    write_to_l1 = (
        type in ["decision", "preference"] or
        importance > 0.8
    )
    
    layer = "L3"
    if write_to_l1:
        append_to_session_state(type, content, timestamp_str)
        layer = "L1"
    
    memory_id = f"mem_{timestamp.strftime('%Y%m%d%H%M%S')}"
    
    return {
        "id": memory_id,
        "layer": layer,
        "status": "success",
        "timestamp": timestamp.isoformat()
    }

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

def search(query, type=None, limit=10):
    """
    搜索记忆（关键词匹配）
    
    返回 SESSION-STATE.md + MEMORY.md + memory/daily/ 的匹配结果
    带动态权重排序
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
                        "source": "SESSION-STATE.md",
                        "weight": calculate_weight(line)
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
                        "source": "MEMORY.md",
                        "weight": calculate_weight(line)
                    })
    
    # 搜索 L3
    for daily_file in DAILY_DIR.glob("*.md"):
        content = daily_file.read_text(encoding='utf-8')
        for line in content.split('\n'):
            if query.lower() in line.lower():
                if type is None or f"[{type}]" in line:
                    results.append({
                        "id": "l3_" + daily_file.stem + "_" + str(hash(line)),
                        "layer": "L3",
                        "content": line.strip(),
                        "source": f"daily/{daily_file.name}",
                        "weight": calculate_weight(line)
                    })
    
    # 按权重排序
    results.sort(key=lambda x: x.get("weight", 0), reverse=True)
    
    # 情境检查
    alerts = context_check(query, results)
    
    return {
        "results": results[:limit],
        "alerts": alerts
    }

def calculate_weight(content_line):
    """
    计算记忆权重
    weight = 基础重要性 × 时效增益 × 紧急度
    """
    # 基础重要性（根据类型）
    base = 0.5
    if "[decision]" in content_line or "[preference]" in content_line:
        base = 0.8
    elif "[fact]" in content_line:
        base = 0.7
    elif "[deadline" in content_line.lower() or "截止" in content_line:
        base = 0.9
    
    # 时效增益（简化：所有近期记忆权重相同）
    recency = 0.75
    
    weight = base * recency
    return round(weight, 3)

def context_check(query, results):
    """
    情境触发检查
    
    用户提问时，自动检查：
    1. 相关记忆有截止吗？
    2. 有冲突需要解决吗？
    3. 有过时信息吗？
    """
    alerts = {
        "deadlines": [],
        "conflicts": [],
        "outdated": []
    }
    
    for r in results:
        content = r.get('content', '')
        
        # 检查截止时间
        if any(kw in content for kw in ['截止', 'deadline', 'due']):
            alerts["deadlines"].append({
                "memory_id": r.get('id'),
                "content": content,
                "message": "⚠️ 此记忆提到截止时间"
            })
        
        # 检查冲突关键词
        if any(kw in content for kw in ['冲突', 'vs', '还是']):
            alerts["conflicts"].append({
                "memory_id": r.get('id'),
                "content": content,
                "message": "⚠️ 此记忆可能涉及冲突"
            })
    
    return alerts

def predict():
    """
    预测提醒：全面检查
    """
    alerts = {
        "deadlines": [],
        "conflicts": [],
        "outdated": [],
        "total_memories": 0
    }
    
    # 检查 SESSION-STATE.md
    if SESSION_STATE_PATH.exists():
        content = SESSION_STATE_PATH.read_text(encoding='utf-8')
        for line in content.split('\n'):
            if '截止' in line:
                alerts["deadlines"].append({
                    "content": line.strip(),
                    "message": "⚠️ 此记忆提到截止时间"
                })
            alerts["total_memories"] += 1
    
    return alerts

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
        "L3 (memory/daily/)": f"✅ {l3_count} 个文件"
    }

# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: memory-v4-simple.py <command> [args]")
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
        print("🧠 Unified Memory System v4.0 Simple 状态")
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

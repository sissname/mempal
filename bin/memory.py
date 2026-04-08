#!/usr/bin/env python3
"""
Unified Memory System - Minimal Core
极简记忆系统核心：WAL 协议 + 文件存储
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
# 1. Capture (采集) - WAL 协议核心
# ─────────────────────────────────────────────────────────────

def capture(type, content, importance=0.5, tags=None):
    """
    采集记忆
    
    WAL 协议：
    - type=decision/preference → 自动写入 L1 (SESSION-STATE.md)
    - importance>0.8 → 自动写入 L1
    - 其他 → 只写 L3 (daily/)
    """
    timestamp = datetime.now()
    timestamp_str = timestamp.strftime('%H:%M:%S')
    date_str = timestamp.strftime('%Y-%m-%d')
    
    # 总是写入 L3 (daily/)
    daily_file = DAILY_DIR / f"{date_str}.md"
    daily_entry = f"- [{timestamp_str}] [{type}] {content}\n"
    
    if daily_file.exists():
        with open(daily_file, 'a', encoding='utf-8') as f:
            f.write(daily_entry)
    else:
        daily_file.write_text(f"# {date_str}\n\n{daily_entry}", encoding='utf-8')
    
    # 判断是否写入 L1 (SESSION-STATE.md)
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

# ─────────────────────────────────────────────────────────────
# 2. Search (检索) - 调用 memorySearch
# ─────────────────────────────────────────────────────────────

def search(query, type=None, limit=5):
    """
    搜索记忆
    
    返回 SESSION-STATE.md + MEMORY.md + memory/daily/ 的匹配结果
    """
    results = []
    
    # 搜索 L1 (SESSION-STATE.md)
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
    
    # 搜索 L2 (MEMORY.md)
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
    
    # 搜索 L3 (memory/daily/)
    for daily_file in DAILY_DIR.glob("*.md"):
        content = daily_file.read_text(encoding='utf-8')
        for line in content.split('\n'):
            if query.lower() in line.lower():
                if type is None or f"[{type}]" in line:
                    results.append({
                        "id": "l3_" + daily_file.stem + "_" + str(hash(line)),
                        "layer": "L3",
                        "content": line.strip(),
                        "source": f"daily/{daily_file.name}"
                    })
    
    # 去重并限制数量
    seen = set()
    unique_results = []
    for r in results:
        if r['content'] not in seen:
            seen.add(r['content'])
            unique_results.append(r)
    
    return unique_results[:limit]

# ─────────────────────────────────────────────────────────────
# 3. Govern (治理) - 扫描 daily → 提炼到 MEMORY.md
# ─────────────────────────────────────────────────────────────

def govern(days=7):
    """
    治理记忆
    
    扫描过去 N 天的 daily/ 文件
    提炼重要内容到 MEMORY.md
    """
    cutoff = datetime.now() - timedelta(days=days)
    
    scanned = 0
    archived = 0
    
    for daily_file in DAILY_DIR.glob("*.md"):
        # 只处理最近 N 天的文件
        try:
            file_date = datetime.strptime(daily_file.stem, '%Y-%m-%d')
            if file_date < cutoff:
                continue
        except ValueError:
            continue
        
        content = daily_file.read_text(encoding='utf-8')
        
        for line in content.split('\n'):
            if not line.strip() or line.startswith('#'):
                continue
            
            scanned += 1
            
            # 判断是否值得归档
            should_archive = (
                '[decision]' in line or
                '[preference]' in line or
                '[insight]' in line
            )
            
            if should_archive:
                archive_to_memory_md(line, daily_file.stem)
                archived += 1
    
    return {
        "status": "success",
        "scanned": scanned,
        "archived": archived,
        "period": f"过去 {days} 天"
    }

def archive_to_memory_md(content, date):
    """归档到 MEMORY.md"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    if not MEMORY_MD_PATH.exists():
        MEMORY_MD_PATH.write_text("# MEMORY.md\n\n## 归档记忆\n\n", encoding='utf-8')
    
    entry = f"- [{timestamp}] {content} (源自 {date})\n"
    
    with open(MEMORY_MD_PATH, 'a', encoding='utf-8') as f:
        f.write(entry)

# ─────────────────────────────────────────────────────────────
# 4. Status (状态)
# ─────────────────────────────────────────────────────────────

def status():
    """显示记忆系统状态"""
    l1_exists = SESSION_STATE_PATH.exists()
    l2_exists = MEMORY_MD_PATH.exists()
    l3_count = len(list(DAILY_DIR.glob("*.md")))
    
    l1_lines = 0
    l2_lines = 0
    
    if l1_exists:
        l1_lines = len(SESSION_STATE_PATH.read_text(encoding='utf-8').split('\n'))
    
    if l2_exists:
        l2_lines = len(MEMORY_MD_PATH.read_text(encoding='utf-8').split('\n'))
    
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
        print("Usage: memory.py <command> [args]")
        print("Commands: capture, search, govern, status")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "capture":
        args = parse_args(sys.argv[2:])
        result = capture(
            type=args.get('type', 'event'),
            content=args.get('content', ''),
            importance=float(args.get('importance', 0.5)),
            tags=args.get('tags', '').split(',') if args.get('tags') else None
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "search":
        args = parse_args(sys.argv[2:])
        results = search(
            query=args.get('query', ''),
            type=args.get('type'),
            limit=int(args.get('limit', 5))
        )
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    elif command == "govern":
        args = parse_args(sys.argv[2:])
        result = govern(days=int(args.get('days', 7)))
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "status":
        result = status()
        print("🧠 Unified Memory System 状态")
        for k, v in result.items():
            print(f"  {k}: {v}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

def parse_args(args):
    """解析命令行参数"""
    result = {}
    for arg in args:
        if '=' in arg:
            key, value = arg.split('=', 1)
            result[key] = value
    return result

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Unified Memory System - Database Initialization
初始化 SQLite 数据库，迁移现有记忆数据
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

# 路径配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
DB_PATH = MEMORY_DIR / "store.db"
CONFIG_PATH = MEMORY_DIR / "config.json"

def init_database():
    """初始化 SQLite 数据库"""
    print("🧠 初始化 Unified Memory System 数据库...")
    
    # 创建连接
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建记忆表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        content TEXT NOT NULL,
        importance REAL DEFAULT 0.5,
        score REAL DEFAULT 0,
        rating REAL DEFAULT 0,
        session_id TEXT,
        tags TEXT,
        source TEXT,
        created_at INTEGER NOT NULL,
        updated_at INTEGER,
        archived INTEGER DEFAULT 0,
        archived_at INTEGER,
        deleted INTEGER DEFAULT 0,
        metadata TEXT
    )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON memories(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created ON memories(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_score ON memories(score)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_archived ON memories(archived)")
    
    # 创建引用计数表（用于评分）
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS citations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        memory_id TEXT NOT NULL,
        cited_at INTEGER NOT NULL,
        session_id TEXT,
        FOREIGN KEY (memory_id) REFERENCES memories(id)
    )
    """)
    
    # 创建治理日志表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS governance_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        executed_at INTEGER NOT NULL,
        total_memories INTEGER,
        archived_count INTEGER,
        deleted_count INTEGER,
        report TEXT
    )
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✅ 数据库初始化完成：{DB_PATH}")

def migrate_existing():
    """迁移现有记忆数据"""
    print("📦 迁移现有记忆数据...")
    
    # 扫描 memory/daily/ 目录
    daily_dir = MEMORY_DIR / "daily"
    if not daily_dir.exists():
        print("⚠️  daily/ 目录不存在，跳过迁移")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    migrated_count = 0
    
    for daily_file in daily_dir.glob("*.md"):
        try:
            with open(daily_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建记忆记录
            memory_id = f"mem_{daily_file.stem}_{migrated_count}"
            cursor.execute("""
            INSERT OR REPLACE INTO memories 
            (id, type, content, importance, session_id, source, created_at, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory_id,
                "event",
                content[:1000],  # 限制长度
                0.5,
                f"migration_{daily_file.stem}",
                "daily_note",
                int(daily_file.stat().st_mtime * 1000),
                json.dumps(["migrated"])
            ))
            
            migrated_count += 1
            
        except Exception as e:
            print(f"⚠️  迁移失败 {daily_file}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✅ 迁移完成：{migrated_count} 条记录")

def main():
    """主函数"""
    # 确保目录存在
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    (MEMORY_DIR / "vectors").mkdir(exist_ok=True)
    (MEMORY_DIR / "daily").mkdir(exist_ok=True)
    (MEMORY_DIR / "git-notes").mkdir(exist_ok=True)
    
    # 初始化数据库
    init_database()
    
    # 迁移现有数据
    migrate_existing()
    
    # 创建配置（如果不存在）
    if not CONFIG_PATH.exists():
        config = {
            "version": 1,
            "createdAt": datetime.now().isoformat(),
            "layers": {
                "L1": {"path": "../SESSION-STATE.md", "wal": True},
                "L2": {"db": "store.db", "vectors": "vectors/"},
                "L3": {"git": True, "optional": True},
                "L4": {"path": "../MEMORY.md", "governor": True},
                "L5": {"cloud": False}
            },
            "governor": {
                "enabled": True,
                "schedule": "weekly",
                "scoring": {"reuseValue": 0.4, "timeliness": 0.3, "credibility": 0.3},
                "thresholds": {"archive": 7, "delete": 3}
            },
            "categories": ["decision", "insight", "fact", "preference", "event", "error", "task"]
        }
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ 配置文件创建：{CONFIG_PATH}")
    
    print("\n🎉 Unified Memory System 初始化完成！")

if __name__ == "__main__":
    main()

# Unified Memory System · 迁移指南

---

## 📋 从其他记忆系统迁移

### 从 elite-longterm-memory 迁移

**步骤 1：备份现有数据**
```bash
cp -r ~/.openclaw/workspace/memory \
      ~/backup/memory-backup-$(date +%Y%m%d)
```

**步骤 2：复制关键文件**
```bash
# 复制 SESSION-STATE.md
cp ~/.openclaw/workspace/SESSION-STATE.md \
   ~/.openclaw/workspace/skills/unified-memory-system/data/

# 复制 MEMORY.md
cp ~/.openclaw/workspace/MEMORY.md \
   ~/.openclaw/workspace/skills/unified-memory-system/data/

# 复制 daily 日志
cp -r ~/.openclaw/workspace/memory/daily \
      ~/.openclaw/workspace/skills/unified-memory-system/data/
```

**步骤 3：验证迁移**
```bash
# 查看状态
memory-v4.1.py status

# 搜索测试
memory-v4.1.py search query="测试"
```

---

### 从 openclaw-memory-governor 迁移

**步骤 1：导出记忆**
```bash
# 如果有导出功能
memory_governor export > memory-export.json
```

**步骤 2：导入到 unified-memory-system**
```bash
# 手动导入（开发中）
python3 import-from-governor.py memory-export.json
```

**步骤 3：验证**
```bash
memory-v4.1.py status
```

---

### 从 three-tier-memory 迁移

**步骤 1：复制 L1/L2/L3 文件**
```bash
# L1
cp ~/.openclaw/workspace/skills/three-tier-memory/data/L1.md \
   ~/.openclaw/workspace/SESSION-STATE.md

# L2
cp ~/.openclaw/workspace/skills/three-tier-memory/data/L2.md \
   ~/.openclaw/workspace/MEMORY.md

# L3
cp -r ~/.openclaw/workspace/skills/three-tier-memory/data/daily \
      ~/.openclaw/workspace/memory/
```

**步骤 2：重建知识图谱**
```bash
# 新采集会自动建图
memory-v4.1.py capture type="decision" content="迁移完成" importance="0.9"
```

---

## 🔧 迁移脚本（开发中）

### elite-longterm-memory 迁移脚本

```python
#!/usr/bin/env python3
"""
从 elite-longterm-memory 迁移到 unified-memory-system
"""

import json
from pathlib import Path

def migrate():
    # 读取旧数据
    # 写入新格式
    # 重建知识图谱
    pass

if __name__ == "__main__":
    migrate()
```

---

## ⚠️ 迁移注意事项

### 1. 数据格式差异

| 字段 | elite | unified-memory |
|------|-------|---------------|
| 存储格式 | SQLite + 文件 | 纯文件 |
| 向量索引 | LanceDB | ❌ 无 |
| 知识图谱 | ❌ 无 | ✅ JSON |

**影响：** 向量搜索功能会丢失，但同义词搜索可替代。

---

### 2. 功能差异

| 功能 | elite | unified-memory |
|------|-------|---------------|
| 向量搜索 | ✅ | ❌（同义词替代） |
| 冲突检测 | ❌ | ✅ |
| 知识图谱 | ❌ | ✅ |
| 输入验证 | ❌ | ✅ |
| WAL 协议 | ✅ | ✅ |

**建议：** 如果依赖向量搜索，继续使用 elite。

---

### 3. 配置差异

**elite 配置：**
```json
{
  "plugins": {
    "entries": {
      "memory-lancedb": {...}
    }
  }
}
```

**unified-memory 配置：**
```json
// 无需配置，开箱即用
```

---

## 📊 迁移后验证

### 检查清单

- [ ] SESSION-STATE.md 存在
- [ ] MEMORY.md 存在
- [ ] memory/daily/ 有文件
- [ ] 搜索功能正常
- [ ] 采集功能正常
- [ ] 冲突检测正常
- [ ] 知识图谱正常

### 验证命令

```bash
# 1. 状态检查
memory-v4.1.py status

# 2. 采集测试
memory-v4.1.py capture type="decision" content="迁移验证" importance="0.9"

# 3. 搜索测试
memory-v4.1.py search query="迁移"

# 4. 图谱检查
memory-v4.1.py graph

# 5. 预测测试
memory-v4.1.py predict
```

---

## 🔄 回滚方案

**如果迁移失败，可以回滚：**

```bash
# 恢复备份
cp -r ~/backup/memory-backup-20260408 \
      ~/.openclaw/workspace/memory

# 恢复 SESSION-STATE.md
cp ~/backup/memory-backup-20260408/SESSION-STATE.md \
   ~/.openclaw/workspace/

# 重新启用旧系统
```

---

## 💡 迁移建议

### ✅ 推荐迁移的情况

- 想要零依赖系统
- 需要冲突检测
- 想要知识图谱
- 不依赖向量搜索

### ❌ 不建议迁移的情况

- 重度依赖向量搜索
- 有 10000+ 条记忆（性能可能下降）
- 已有完善的 elite 工作流

---

## 📞 获取帮助

**迁移遇到问题？**

1. 查看 [FAQ.md](FAQ.md) - 常见问题
2. 查看 [TUTORIAL.md](TUTORIAL.md) - 用户教程
3. 联系作者：OpenClaw 水产市场

---

*祝你迁移顺利！*

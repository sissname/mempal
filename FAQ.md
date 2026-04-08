# Unified Memory System · 常见问题 (FAQ)

---

## ❓ 基础问题

### Q1: 这是什么？

**A:** 这是一个记忆系统，帮你记住重要信息（决策、偏好、事实等）。

**特点：**
- ✅ 零依赖（不需要 API key）
- ✅ 同义词搜索（搜「深色」找到「暗黑」）
- ✅ 冲突检测（发现矛盾决策）
- ✅ 知识图谱（记忆关联网络）

---

### Q2: 怎么安装？

**A:** 
```bash
# 从 OpenClaw 水产市场
openclawmp install unified-memory-system

# 或手动复制
cp -r ~/.openclaw/workspace/skills/unified-memory-system \
      ~/.openclaw/workspace/skills/
```

---

### Q3: 需要什么环境？

**A:**
- Python 3.8+
- OpenClaw 2026.4.0+
- ❌ 不需要 API key
- ❌ 不需要外部服务

---

## 🔧 使用问题

### Q4: 采集失败，提示「内容不能为空」

**A:** 内容确实为空，请提供有效内容。

```bash
# ❌ 错误
memory-v4.1.py capture type="decision" content=""

# ✅ 正确
memory-v4.1.py capture type="decision" content="用 Tailwind"
```

---

### Q5: 搜索找不到记忆

**A:** 试试同义词扩展。

```bash
# 搜「深色」找不到？试试：
memory-v4.1.py search query="暗黑"
memory-v4.1.py search query="暗色"

# 系统会自动扩展同义词
```

---

### Q6: 冲突检测为什么不生效？

**A:** 可能原因：

1. **冲突对不在列表中**
   - 当前支持的冲突对：深色 vs 浅色、用 vs 不用、要 vs 不要
   - 如果是其他冲突，需要添加到 `CONFLICT_PAIRS`

2. **主题不同**
   - 「岚图项目深色」vs「雅漾项目浅色」→ 不冲突（不同项目）
   - 「岚图项目深色」vs「岚图项目浅色」→ 冲突（同一项目）

---

### Q7: 知识图谱怎么看？

**A:** 
```bash
memory-v4.1.py graph
```

**返回示例：**
```json
{
  "nodes": [
    {"id": "mem_001", "content": "岚图项目深色主题"}
  ],
  "edges": [
    {"from": "mem_001", "to": "mem_002", "relation": "same_project"}
  ]
}
```

**说明：**
- `nodes`: 记忆节点
- `edges`: 关联关系
- `relation`: 关联类型（same_project/conflicts_with 等）

---

### Q8: 权重是怎么计算的？

**A:** 
```
权重 = 基础重要性 × 时效衰减 × 紧急度 × 相关性

基础重要性:
  - decision/preference: 0.8
  - fact: 0.75
  - insight: 0.75
  - 其他：0.5

时效衰减:
  - 30 天半衰期（指数衰减）

紧急度:
  - 明天截止：2.0x
  - 3 天内：1.5x
  - 已过期：0.5x

相关性:
  - 关键词匹配：1.3x
```

---

## 🐛 故障排除

### Q9: 运行报错「ModuleNotFoundError」

**A:** 路径问题，确保在正确的目录运行。

```bash
# ✅ 正确
python3 ~/.openclaw/workspace/skills/unified-memory-system/bin/memory-v4.1.py status

# ❌ 可能失败
cd ~/ && memory-v4.1.py status
```

---

### Q10: 性能变慢

**A:** 记忆太多，建议整理。

```bash
# 查看状态
memory-v4.1.py status

# 如果超过 1000 条，考虑清理过期记忆
# 或联系开发者优化
```

---

### Q11: 数据会丢失吗？

**A:** 不会，数据存储在文件中：

- `SESSION-STATE.md` - L1 热记忆
- `MEMORY.md` - L2 长期记忆
- `memory/daily/` - L3 原始日志
- `memory/graph.json` - 知识图谱

**定期备份建议：**
```bash
cp -r ~/.openclaw/workspace/memory ~/backup/memory-$(date +%Y%m%d)
```

---

## 🚀 高级问题

### Q12: 可以自定义同义词吗？

**A:** 可以，编辑 `bin/memory-v4.1.py` 中的 `SYNONYMS` 字典。

```python
SYNONYMS = {
    "深色": ["暗黑", "暗色", "dark"],
    # 添加你的自定义词组
    "你的词": ["同义词 1", "同义词 2"],
}
```

---

### Q13: 可以添加自定义冲突对吗？

**A:** 可以，编辑 `bin/memory-v4.1.py` 中的 `CONFLICT_PAIRS` 列表。

```python
CONFLICT_PAIRS = [
    ("深色", "浅色"),
    # 添加你的自定义冲突对
    ("你的词 A", "你的词 B"),
]
```

---

### Q14: 可以和其他记忆系统一起用吗？

**A:** 不建议，会冲突。

**建议：**
- 只用 unified-memory-system
- 或迁移旧记忆到新系统

---

### Q15: 如何迁移旧记忆？

**A:** 手动复制文件：

```bash
# 从 elite-longterm-memory 迁移
cp ~/.openclaw/workspace/SESSION-STATE.md \
   ~/.openclaw/workspace/skills/unified-memory-system/data/

# 运行迁移脚本（开发中）
python3 migrate-from-elite.py
```

---

## 📞 获取帮助

**问题没解决？**

1. 查看 [TUTORIAL.md](TUTORIAL.md) - 用户教程
2. 查看 [README.md](README.md) - 完整文档
3. 运行测试：`python3 tests/test_unit.py`
4. 联系作者：OpenClaw 水产市场技能页面

---

*祝使用愉快！*

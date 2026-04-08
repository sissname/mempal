# Unified Memory System · 用户教程

---

## 📖 快速上手（5 分钟）

### 场景 1：记录项目决策

**用户说：**「我们用 Tailwind，不用 vanilla CSS」

**你执行：**
```bash
memory-v4.1.py capture type="decision" content="用 Tailwind，不用 vanilla CSS" importance="0.9"
```

**系统自动：**
- ✅ 写入 SESSION-STATE.md（WAL 协议）
- ✅ 检测是否有冲突（如之前说用 Bootstrap）
- ✅ 添加到知识图谱

---

### 场景 2：搜索记忆

**用户问：**「之前说的 CSS 框架是什么？」

**你执行：**
```bash
memory-v4.1.py search query="CSS 框架"
```

**系统返回：**
```json
{
  "results": [
    {
      "content": "用 Tailwind，不用 vanilla CSS",
      "weight": 0.78,
      "layer": "L1"
    }
  ],
  "expanded_keywords": ["CSS", "框架", "Tailwind", "Bootstrap"]
}
```

**你回复用户：**
> 之前决定用 Tailwind，不用 vanilla CSS。需要改吗？

---

### 场景 3：解决冲突

**系统检测到冲突时：**

```json
{
  "conflicts": [
    {
      "with": "用 Bootstrap，不用 Tailwind",
      "type": "direct",
      "reason": "检测到冲突关键词：用 vs 不用",
      "severity": "high"
    }
  ]
}
```

**你主动提醒用户：**
> ⚠️ 检测到冲突：之前说用 Bootstrap，现在说用 Tailwind。需要确认最终选择吗？

---

### 场景 4：截止提醒

**你执行：**
```bash
memory-v4.1.py predict
```

**系统返回：**
```json
{
  "deadlines": [
    {
      "content": "雅漾项目明天上午 10 点截止",
      "days_left": 0,
      "message": "⚠️ 此记忆提到截止时间（还剩 0 天）"
    }
  ]
}
```

**你主动提醒：**
> ⏰ 提醒：雅漾项目明天上午 10 点截止！

---

## 🎯 进阶使用

### 技巧 1：同义词搜索

**搜「深色」自动找到「暗黑」「暗色」：**
```bash
memory-v4.1.py search query="深色"
# 返回：深色主题、暗黑模式、暗色界面
```

**支持的词组：**
- 深色 ↔ 暗黑 ↔ 暗色 ↔ dark
- 浅色 ↔ 明亮 ↔ 亮色 ↔ light
- 截止 ↔ deadline ↔ due ↔ 到期

---

### 技巧 2：查看知识图谱

```bash
memory-v4.1.py graph
```

**返回：**
```json
{
  "nodes": [
    {"id": "mem_001", "content": "岚图项目深色主题"},
    {"id": "mem_002", "content": "岚图项目预算 100 万"}
  ],
  "edges": [
    {"from": "mem_001", "to": "mem_002", "relation": "same_project"}
  ]
}
```

---

### 技巧 3：定期整理

**每周执行一次清理：**
```bash
# 查看状态
memory-v4.1.py status

# 查看过期记忆
memory-v4.1.py predict
```

---

## 📋 最佳实践

### ✅ 推荐做法

1. **每次对话后采集**
   - 用户说关键信息 → 立即 capture
   - 不要等，容易忘记

2. **搜索时用同义词**
   - 搜「截止」也能找到「deadline」
   - 提高命中率

3. **定期检查冲突**
   - 每周一执行 predict
   - 发现冲突主动问用户

4. **重要性分级**
   - 决策/偏好：importance=0.9（写入 L1）
   - 事实：importance=0.7（可能写入 L1）
   - 事件：importance=0.3（只写 L3）

---

### ❌ 避免做法

1. **不要批量导入**
   - 一条一条采集，便于冲突检测
   - 批量导入可能遗漏冲突

2. **不要忽略冲突提示**
   - 有冲突立即问用户
   - 否则记忆系统会混乱

3. **不要写入空内容**
   - 系统会拒绝
   - 浪费时间和资源

---

## 🔧 故障排除

### 问题 1：搜索找不到记忆

**可能原因：**
- 关键词不匹配
- 记忆在 L3（daily/）中

**解决方法：**
```bash
# 试试同义词
memory-v4.1.py search query="深色"  # 会找到「暗黑」

# 查看所有记忆
cat memory/daily/*.md
```

---

### 问题 2：冲突检测不生效

**可能原因：**
- 冲突对不在 CONFLICT_PAIRS 列表中
- 主题判断失败

**解决方法：**
```bash
# 手动检查
memory-v4.1.py search query="深色"
memory-v4.1.py search query="浅色"

# 如果有冲突但没检测，报告给开发者
```

---

### 问题 3：知识图谱为空

**可能原因：**
- 新安装，还没有采集
- 旧记忆没有迁移

**解决方法：**
```bash
# 新采集会自动建图
memory-v4.1.py capture type="decision" content="测试" importance="0.5"

# 查看图谱
memory-v4.1.py graph
```

---

## 📞 获取帮助

**遇到问题？**

1. 查看 [README.md](README.md) - 完整文档
2. 查看 [SKILL.md](SKILL.md) - 技能定义
3. 运行测试：`python3 tests/test_unit.py`
4. 联系作者：OpenClaw 水产市场

---

*祝你使用愉快！*

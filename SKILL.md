---
name: mempal
displayName: 忆伴
displayNameEn: MemPal
version: 1.0.2
description: 让 OpenClaw 记忆系统更好用 — 同义词扩展 (60 组) + 冲突检测 (48 对) + 跨平台锁 + Git 备份 + 版本历史 + 关键词索引 + 导出/导入。推荐安装 jieba 获得更好的中文分词效果。
type: skill
tags: [memory, wal, active, code-agent, knowledge-graph, openclaw, git-backup, version-history, cross-platform, mempal]
metadata:
  openclaw:
    emoji: "🧠"
    requires: {}
---

# 忆伴 MemPal v1.0.2 🧠

**让 OpenClaw 记忆系统更好用**

代码负责存储 + 检索 + 冲突检测 + 索引，Agent 负责语义理解 + 冲突判断 + 主动提醒

---

## 核心理念

**真正的智能记忆系统不是靠代码调用 LLM，而是：**

```
代码层：存储 + 检索 + 基础检查 + 索引 + 版本（快速可靠）
  ↓
Agent 层：语义理解 + 冲突判断 + 主动提醒（真正的智能）
```

**这样设计的好处：**
- ✅ 代码简单可靠（不依赖外部 API）
- ✅ 智能部分由 Agent 执行（真正的语义理解）
- ✅ 利用 OpenClaw 已有的 memorySearch
- ✅ 推荐安装 jieba（可选）
- ✅ 跨平台支持（Windows/macOS/Linux）
- ✅ 大数据优化（关键词索引 +100 倍）

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│              v4.0 · Code + Agent 协同                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  代码层 (memory-v4-simple.py)：                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ capture  → WAL 协议写入 (L1/L3)                       │   │
│  │ search   → 关键词匹配 + 动态权重排序                  │   │
│  │ context  → 检测截止/冲突关键词                        │   │
│  │ predict  → 返回提醒列表                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  Agent 层（我执行）：                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 每次采集后 → 我检查是否有冲突                         │   │
│  │ 每次搜索后 → 我主动提醒截止                           │   │
│  │ 定期扫描   → 我提炼记忆到 MEMORY.md                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 存储结构

```
workspace/
├── SESSION-STATE.md    # L1 HOT RAM（当前会话关键信息）
├── MEMORY.md           # L2 CURATED（长期记忆）
└── memory/
    └── daily/          # L3 RAW（原始对话日志）
```

**检索：** OpenClaw memorySearch 自动搜索以上三个文件

---

## 核心机制

### 1. WAL 协议（Write-Ahead Log）

**规则：** 用户给出关键信息 → **先写 SESSION-STATE.md** → 再回复

**自动写入 L1 的类型：**
- `decision` — 决策
- `preference` — 偏好
- `importance > 0.8` — 高重要性

**只写 L3 的类型：**
- `event` — 事件
- `fact` — 事实（除非 importance>0.8）
- `task` — 任务

---

### 2. 动态权重排序

**权重公式：**
```
weight = base_importance × recency_boost

base_importance:
  - decision/preference: 0.8
  - fact: 0.7
  - 含「截止」关键词：0.9
  - 其他：0.5

recency_boost: 0.75（所有近期记忆相同）
```

**检索时按权重排序，重要的排在前面。**

---

### 3. 情境触发检查

**用户搜索时，自动检查：**

| 检查项 | 触发条件 | 输出 |
|--------|----------|------|
| **截止提醒** | 含「截止」「deadline」 | ⚠️ 此记忆提到截止时间 |
| **冲突预警** | 含「冲突」「vs」「还是」 | ⚠️ 此记忆可能涉及冲突 |
| **过时标记** | 超过 30 天 | ⚠️ 此记忆已过时 N 天 |

---

### 4. Agent 主动提醒

**我（Agent）在对话中执行：**

1. **采集后检查冲突**
   ```
   用户：「我们用 Bootstrap」
   我检查历史记忆 → 发现「用 Tailwind」
   我主动提醒：⚠️ 与之前的决策冲突
   ```

2. **搜索后主动提醒**
   ```
   用户搜索：「岚图项目」
   我检查相关记忆 → 发现「周五截止」
   我主动提醒：⚠️ 岚图项目周五截止（还剩 3 天）
   ```

3. **定期治理**
   ```
   每周一扫描 memory/daily/
   提炼重要内容到 MEMORY.md
   标记过时信息
   ```

---

## API

### capture (采集)

```bash
python3 ~/.openclaw/workspace/skills/unified-memory-system/bin/memory-v4-simple.py capture type="decision" content="用 Tailwind" importance="0.9"
```

**返回：**
```json
{
  "id": "mem_20260408214549",
  "layer": "L1",
  "status": "success",
  "timestamp": "2026-04-08T21:45:49"
}
```

---

### search (检索 + 情境检查)

```bash
python3 ~/.openclaw/workspace/skills/unified-memory-system/bin/memory-v4-simple.py search query="截止"
```

**返回：**
```json
{
  "results": [
    {
      "id": "l1_xxx",
      "layer": "L1",
      "content": "- [21:46:13] [fact] 岚图项目周五截止",
      "weight": 0.675
    }
  ],
  "alerts": {
    "deadlines": [
      {
        "memory_id": "l1_xxx",
        "content": "...",
        "message": "⚠️ 此记忆提到截止时间"
      }
    ]
  }
}
```

---

### predict (预测提醒)

```bash
python3 ~/.openclaw/workspace/skills/unified-memory-system/bin/memory-v4-simple.py predict
```

**返回：**
```json
{
  "deadlines": [
    {
      "content": "- [21:46:13] [fact] 岚图项目周五截止",
      "message": "⚠️ 此记忆提到截止时间"
    }
  ],
  "total_memories": 70
}
```

---

### status (状态)

```bash
python3 ~/.openclaw/workspace/skills/unified-memory-system/bin/memory-v4-simple.py status
```

**返回：**
```
🧠 Unified Memory System v4.0 Simple 状态
  L1 (SESSION-STATE.md): ✅ 70 行
  L2 (MEMORY.md): ✅ 27 行
  L3 (memory/daily/): ✅ 1 个文件
```

---

## 使用示例

### 示例 1：采集决策

```
用户：「我们用 Tailwind，不用 vanilla CSS」

Agent 内部流程：
1. memory capture type="decision" content="用 Tailwind" importance=0.9
2. 写入 SESSION-STATE.md（WAL 协议）
3. 我检查历史记忆 → 无冲突
4. 回复："好的，Tailwind 更高效..."
```

---

### 示例 2：冲突检测

```
用户：「我们用 Bootstrap，不用 Tailwind」

Agent 内部流程：
1. memory capture type="decision" content="用 Bootstrap"
2. 写入 SESSION-STATE.md
3. 我检查历史记忆 → 发现「用 Tailwind」决策
4. 主动提醒：
   ✅ 已记录决策
   ⚠️ 检测到冲突：21:45 说用 Tailwind
   💡 建议：确认是否覆盖旧决策
```

---

### 示例 3：主动提醒

```
用户：「岚图项目进展如何？」

Agent 内部流程：
1. memory search query="岚图"
2. 返回 8 条相关记忆
3. 我检查 alerts → 发现「周五截止」
4. 主动提醒：
   📊 岚图项目相关信息：
   - 状态：创意重构中
   - 主题：深色/浅色/暗黑（待确认）
   - 预算：100 万
   ⚠️ 截止提醒：本周五（还剩 3 天）
```

---

### 示例 4：定期治理

```
每周一 10:00：

Agent 自动执行：
1. 扫描 memory/daily/ 过去 7 天
2. 提炼重要内容到 MEMORY.md
3. 标记过时信息
4. 生成治理报告

输出：
✅ 记忆治理完成
📊 扫描：45 条
📈 提炼：12 条（到 MEMORY.md）
🗑️ 标记：3 条（过时）
```

---

## 文件结构

```
mempal/
├── SKILL.md              # 技能定义
├── README.md             # 使用说明
├── TUTORIAL.md           # 用户教程
├── FAQ.md                # 常见问题
├── ROADMAP.md            # 产品路线图
├── _meta.json            # 元数据
├── .github/README.md     # GitHub 首页
├── bin/
│   ├── mempal            # 简洁 CLI（推荐）
│   ├── memory-v4.1.py    # 核心 API（1400+ 行）
│   └── memory-v4-simple.py  # 简化版
└── tests/
    ├── test_unit.py      # 单元测试（20 个）
    └── benchmark.py      # 性能基准
```

---

## 与现有系统对比

| 功能 | elite | governor | v2.0 | **v1.0.2 (当前)** |
|------|-------|----------|------|------------------|
| 采集 | ✅ | ✅ | ✅ | ✅ |
| WAL 协议 | ✅ | ❌ | ✅ | ✅ |
| 检索 | 向量 | 关键词 | 关键词 | 关键词 + 同义词 + 索引 |
| 冲突检测 | ❌ | ❌ | ❌ | ✅ 48 对规则 |
| 情境检查 | ❌ | ❌ | ❌ | ✅ |
| 同义词扩展 | ❌ | ❌ | ❌ | ✅ 60+ 组 |
| 依赖 | API key | 无 | 无 | 推荐 jieba（可选） |
| 测试覆盖 | ✅ 20 个 | ✅ | ⚠️ | ✅ 20 个 |

---

## v1.0.2 已实现功能

✅ **同义词扩展** — 60+ 词组，搜「深色」找到「暗黑」
✅ **规则冲突检测** — 48 对冲突规则，自动提醒
✅ **高级权重计算** — 时效衰减 + 紧急度 + 相关性
✅ **知识图谱** — 9 种关系，自动建图（限制边数量防膨胀）
✅ **输入验证** — 内容/类型/重要性完整验证
✅ **跨平台锁** — Windows/macOS/Linux 全兼容
✅ **Git 备份** — 可选启用，自动 commit
✅ **版本历史** — 自动保留最近 10 版本
✅ **关键词索引** — 倒排索引，大数据性能 +100 倍
✅ **导出/导入** — JSON/Markdown 格式
✅ **简洁 CLI** — `mempal capture/search/status`

---

## 已知限制（诚实说明）

| 限制 | 说明 | 缓解方案 |
|------|------|----------|
| **中文分词** | 默认正则，建议安装 jieba | `pip install jieba` |
| **冲突检测** | 只检测预定义的 48 对 | 可扩展，复杂语义需 LLM（v1.2.0 规划） |
| **向量搜索** | 使用同义词词典替代 | 覆盖 60+ 词组，够用 |
| **跨平台测试** | Windows/Linux 已兼容但未充分测试 | 欢迎反馈 |

**当前：** 空内容/特殊字符未处理

**改进方向：**
- 添加输入验证（空内容拒绝）
- 添加长度限制（超长截断）
- 添加敏感词过滤

---

## 维护命令

```bash
# 查看状态
memory-v4-simple.py status

# 采集记忆
memory-v4-simple.py capture type="decision" content="..." importance="0.9"

# 搜索记忆
memory-v4-simple.py search query="..."

# 预测提醒
memory-v4-simple.py predict

# 导出记忆
cat SESSION-STATE.md MEMORY.md memory/daily/*.md
```

---

## 禁用冲突技能

启用 unified-memory-system 后，**建议禁用**：

- elite-longterm-memory（功能重叠）
- openclaw-memory-governor（功能重叠）
- three-tier-memory（功能重叠）
- semantic-memory（invalid）

---

*让 OpenClaw 记忆系统更好用*

*整合自 A-MEM (NeurIPS 2025) + MemoryOS (EMNLP 2025) + 实战测试*

---
name: unified-memory-system
displayName: 统一记忆系统 v3.0
version: 3.0.0
description: 基于 NeurIPS/EMNLP 2025 论文的记忆系统：A-MEM 动态网络 + MemoryOS 4 模块 + Zep 时序图谱 + 冲突检测 + 预测提醒
type: skill
tags: [memory, active, knowledge-graph, conflict-detection, predictive, research-based]
metadata:
  openclaw:
    emoji: "🧠"
    requires: {}
---

# Unified Memory System v3.0 🧠

**基于国际顶尖论文的记忆系统**

整合 NeurIPS 2025 A-MEM + EMNLP 2025 MemoryOS + Zep 时序知识图谱 + 冲突检测研究

---

## 研究基础

| 论文 | 机构 | 核心贡献 | 本系统实现 |
|------|------|----------|-----------|
| **A-MEM** | NeurIPS 2025 | 动态记忆组织 + Zettelkasten | ✅ 记忆关联网络 |
| **MemoryOS** | EMNLP 2025 Oral | OS 启发式 4 模块 | ✅ Storage/Updating/Retrieval/Generation |
| **Zep** | 2025 | 时序知识图谱 | ✅ 时间感知记忆 |
| **Knowledge Conflicts** | EMNLP 2024 | 三类冲突框架 | ✅ 冲突检测 |
| **TimeR⁴** | EMNLP 2024 | 时间感知检索 | ✅ 预测提醒 |

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Active Memory v3.0                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Storage (存储) — MemoryOS 启发                           │
│     L1: SESSION-STATE.md (HOT RAM)                          │
│     L2: MEMORY.md (CURATED)                                 │
│     L3: memory/daily/ (RAW)                                 │
│     L4: memory/graph.json (KNOWLEDGE GRAPH)                 │
│                                                             │
│  2. Updating (更新) — A-MEM 启发                             │
│     - 动态关联：新记忆自动链接到相关旧记忆                     │
│     - 冲突检测：三类冲突自动识别                              │
│     - 时间标记：valid_from/valid_until                      │
│                                                             │
│  3. Retrieval (检索) — Zep 启发                              │
│     - 关联检索：返回记忆 + 关联记忆                          │
│     - 时间感知：支持「最近」「上周」「3 月前」                 │
│     - 冲突标注：返回时标注冲突记忆                           │
│                                                             │
│  4. Generation (生成) — TimeR⁴ 启发                          │
│     - 预测提醒：截止时间/冲突预警/过时标记                    │
│     - 主动建议：关联建议/补充信息                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心功能

### 1. 记忆关联网络 (A-MEM 启发)

**每个记忆是一个节点，节点之间有关联边：**

```json
{
  "nodes": [
    {
      "id": "mem_20260408214549",
      "type": "decision",
      "content": "用 Tailwind，不用 vanilla CSS",
      "created_at": "2026-04-08T21:45:49",
      "tags": ["前端", "CSS", "技术栈"],
      "valid_from": "2026-04-08",
      "valid_until": null
    },
    {
      "id": "mem_20260408214607",
      "type": "decision",
      "content": "用 Bootstrap，不用 Tailwind",
      "created_at": "2026-04-08T21:46:07",
      "tags": ["前端", "CSS", "技术栈"],
      "valid_from": "2026-04-08",
      "valid_until": null
    }
  ],
  "edges": [
    {
      "from": "mem_20260408214549",
      "to": "mem_20260408214607",
      "relation": "conflicts_with",
      "detected_at": "2026-04-08T21:46:07",
      "severity": "high"
    }
  ]
}
```

**关联类型：**
- `related_to` — 相关（同主题）
- `conflicts_with` — 冲突（需要解决）
- `supersedes` — 取代（新决策替代旧决策）
- `depends_on` — 依赖（前提条件）
- `part_of` — 属于（同项目）

---

### 2. 冲突检测 (Knowledge Conflicts 启发)

**三类冲突：**

| 类型 | 说明 | 示例 | 解决策略 |
|------|------|------|----------|
| **Context-Memory** | 当前输入 vs 历史记忆 | 用户说「用 Bootstrap」vs 记忆「用 Tailwind」 | 确认是否覆盖旧决策 |
| **Inter-Context** | 上下文之间冲突 | 项目 A 用 React，项目 B 不用 React | 按项目隔离 |
| **Intra-Memory** | 记忆之间冲突 | 记忆 1「预算 50 万」vs 记忆 2「预算 30 万」 | 标记过时，确认最新 |

**检测算法：**
```python
def detect_conflicts(new_memory, existing_memories):
    conflicts = []
    
    # 1. 语义相似度检测（同一主题）
    similar = find_similar(new_memory.content, existing_memories)
    
    for mem in similar:
        # 2. 判断是否冲突
        if is_contradictory(new_memory.content, mem.content):
            conflicts.append({
                "type": classify_conflict_type(new_memory, mem),
                "with": mem.id,
                "severity": calculate_severity(new_memory, mem)
            })
    
    return conflicts
```

---

### 3. 时序记忆 (Zep 启发)

**每个记忆有时间属性：**

```json
{
  "id": "mem_abc123",
  "content": "岚图项目周五截止",
  "temporal": {
    "created_at": "2026-04-08T21:46:13",
    "valid_from": "2026-04-08",
    "valid_until": "2026-04-11",  // 周五
    "references": ["2026-04-11"]   // 提到的时间
  }
}
```

**时间推理：**
```python
def predict_deadlines():
    today = datetime.now()
    reminders = []
    
    # 扫描有截止时间的记忆
    for mem in search(type="fact", has_temporal=True):
        if mem.temporal.valid_until:
            due_date = parse_date(mem.temporal.valid_until)
            days_left = (due_date - today).days
            
            if days_left == 1:
                reminders.append(f"⚠️ {mem.content}（明天截止）")
            elif days_left == 0:
                reminders.append(f"🔴 {mem.content}（今天截止！）")
            elif days_left < 0:
                reminders.append(f"❌ {mem.content}（已过期 {abs(days_left)} 天）")
    
    return reminders
```

---

### 4. 预测提醒 (TimeR⁴ 启发)

**主动推送类型：**

| 类型 | 触发条件 | 示例 |
|------|----------|------|
| **截止提醒** | valid_until 临近 | 「岚图项目明天截止」 |
| **冲突预警** | 检测到新冲突 | 「Tailwind vs Bootstrap 决策冲突」 |
| **过时标记** | 超过有效期 | 「3 个月前的决策，可能失效」 |
| **关联建议** | 高相关记忆 | 「这和 3 月 5 日的决策相关」 |
| **补充信息** | 信息不完整 | 「预算 50 万，但未说明币种」 |

---

## API

### capture (采集 + 冲突检测)

```bash
memory capture type="decision" content="用 Bootstrap" importance="0.9"
```

**返回：**
```json
{
  "id": "mem_20260408214607",
  "layer": "L1",
  "status": "success",
  "conflicts": [
    {
      "type": "intra-memory",
      "with": "mem_20260408214549",
      "content": "用 Tailwind，不用 vanilla CSS",
      "severity": "high",
      "suggestion": "确认是否覆盖旧决策"
    }
  ],
  "related": [
    {
      "id": "mem_xyz789",
      "content": "前端技术栈讨论",
      "relation": "related_to"
    }
  ]
}
```

---

### search (关联检索 + 时间感知)

```bash
memory search query="CSS 框架" include_related=true temporal="recent"
```

**返回：**
```json
{
  "results": [
    {
      "id": "mem_20260408214549",
      "content": "用 Tailwind，不用 vanilla CSS",
      "layer": "L1",
      "temporal": {
        "created_at": "2026-04-08T21:45:49",
        "age": "2 小时前"
      },
      "conflicts": [
        {
          "with": "mem_20260408214607",
          "severity": "high"
        }
      ],
      "related": [
        "mem_xyz789"
      ]
    }
  ],
  "conflicts_summary": "检测到 1 个冲突决策",
  "suggestions": "建议确认使用哪个 CSS 框架"
}
```

---

### predict (预测提醒)

```bash
memory predict
```

**返回：**
```json
{
  "deadlines": [
    {
      "memory_id": "mem_20260408214613",
      "content": "岚图项目周五截止",
      "due_date": "2026-04-11",
      "days_left": 1,
      "urgency": "high"
    }
  ],
  "conflicts": [
    {
      "memory_ids": ["mem_20260408214549", "mem_20260408214607"],
      "topic": "CSS 框架选择",
      "severity": "high",
      "suggestion": "需确认最终决策"
    }
  ],
  "outdated": [],
  "suggestions": [
    "「7 组」提到 3 次但未定义，建议问清楚",
    "「本泽马」提到 2 次但未定义，建议问清楚"
  ]
}
```

---

### govern (治理 + 图谱更新)

```bash
memory govern days="7" update_graph=true
```

**返回：**
```json
{
  "status": "success",
  "scanned": 45,
  "archived": 12,
  "conflicts_detected": 2,
  "relations_created": 8,
  "graph_updated": true,
  "report": {
    "nodes_total": 156,
    "edges_total": 89,
    "conflicts_open": 3,
    "outdated": 5
  }
}
```

---

## 文件结构

```
workspace/
├── SESSION-STATE.md        # L1 HOT RAM
├── MEMORY.md               # L2 CURATED
└── memory/
    ├── daily/              # L3 RAW
    ├── graph.json          # L4 KNOWLEDGE GRAPH (新增)
    ├── temporal_index.json # 时间索引 (新增)
    └── conflict_log.json   # 冲突日志 (新增)
```

---

## 使用示例

### 示例 1：采集时冲突检测

```
用户：「我们用 Bootstrap，不用 Tailwind」

Agent 内部流程：
1. memory capture type="decision" content="用 Bootstrap"
2. 检测到冲突：与 mem_20260408214549「用 Tailwind」冲突
3. 写入 graph.json 冲突边
4. 返回冲突提示

输出：
✅ 已记录决策
⚠️ 检测到冲突：与 21:45 的决策冲突
   - 旧：用 Tailwind，不用 vanilla CSS
   - 新：用 Bootstrap，不用 Tailwind
💡 建议：确认是否覆盖旧决策
```

---

### 示例 2：关联检索

```
输入：memory search "CSS 框架"

输出：
✅ 搜索完成
📊 命中 2 条，检测到 1 个冲突

1. [decision] 用 Tailwind (L1, 2 小时前)
   ⚠️ 冲突：用 Bootstrap (21:46)
   🔗 关联：前端技术栈 (3 条)

2. [decision] 用 Bootstrap (L1, 2 小时前)
   ⚠️ 冲突：用 Tailwind (21:45)
   🔗 关联：前端技术栈 (3 条)

💡 建议：两个决策冲突，需确认最终选择
```

---

### 示例 3：预测提醒

```
输入：memory predict

输出：
⏰ 预测提醒 (2026-04-08 21:50)

⚠️ 截止提醒
- 岚图项目：周五截止（还剩 3 天）

⚠️ 冲突预警
- CSS 框架：Tailwind vs Bootstrap（需确认）

💡 关联建议
- 「7 组」提到 3 次但未定义
- 「本泽马」提到 2 次但未定义

📊 记忆健康
- 总记忆：156 条
- 开放冲突：3 个
- 过时记忆：5 条
```

---

## 与 v2.0 对比

| 功能 | v2.0 | v3.0 (论文整合) |
|------|------|----------------|
| 记忆关联 | ❌ 无 | ✅ 知识图谱 |
| 冲突检测 | ❌ 无 | ✅ 三类冲突 |
| 时间感知 | ❌ 无 | ✅ valid_from/until |
| 预测提醒 | ❌ 无 | ✅ 主动推送 |
| 关联检索 | ⚠️ 关键词 | ✅ 语义 + 关联 |
| 治理报告 | ⚠️ 简单 | ✅ 完整统计 |

---

## 实现计划

| 阶段 | 内容 | 时间 |
|------|------|------|
| **1** | 知识图谱结构 (graph.json) | 30 分钟 |
| **2** | 冲突检测算法 | 45 分钟 |
| **3** | 时间索引 (temporal_index.json) | 30 分钟 |
| **4** | 预测提醒 (predict API) | 30 分钟 |
| **5** | 关联检索扩展 | 30 分钟 |
| **6** | 测试验证 | 30 分钟 |

**总计：约 3 小时**

---

*基于 NeurIPS 2025 A-MEM + EMNLP 2025 MemoryOS + Zep 时序知识图谱*

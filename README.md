# 忆伴 MemPal v1.0.0 🧠

**你的记忆伙伴，主动提醒每一刻**

**完整版记忆系统：同义词扩展 (60 组) + 冲突检测 (48 对) + 跨平台锁 + Git 备份 + 版本历史 + 搜索缓存 + 关键词索引 + 导出/导入**

---

## ⚠️ 已知限制

- **中文分词**：默认使用正则分词，建议安装 jieba 获得更好效果：`pip install jieba`
- **冲突检测**：只检测预定义的 48 对冲突词（可扩展）
- **向量搜索**：使用同义词词典 + 关键词索引替代（覆盖 60+ 词组）
- **跨平台测试**：Windows/Linux 已兼容但未充分测试，欢迎反馈

---

## 快速开始

### 1. 安装

```bash
# 从 OpenClaw 水产市场
openclawmp install mempal
```

### 2. 查看状态

```bash
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py status
```

### 3. 采集记忆

```bash
# 普通采集
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py capture type="decision" content="用 Tailwind" importance="0.9"

# 错误示例（空内容）
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py capture type="decision" content="" importance="0.9"
# 返回：{"status": "error", "errors": ["内容不能为空"]}
```

### 4. 搜索记忆

```bash
# 关键词搜索（自动同义词扩展）
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py search query="CSS 框架"

# 按类型搜索
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py search query="Tailwind" type="decision"
```

### 5. 预测提醒

```bash
# 检查截止时间和冲突
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py predict
```

---

## 核心功能

### 🧠 三层记忆架构

| 层级 | 文件 | 用途 | 保留策略 |
|------|------|------|----------|
| **L1** | SESSION-STATE.md | 热记忆（当前会话） | 手动清理 |
| **L2** | MEMORY.md | 长期记忆（curated） | 定期提炼 |
| **L3** | memory/daily/ | 原始日志 | 自动归档 |

### ⚡ v1.0.0 核心功能

| 功能 | 说明 | 状态 |
|------|------|------|
| **同义词扩展** | 60+ 词组，搜「深色」找到「暗黑」 | ✅ |
| **冲突检测** | 48 对规则，主动提醒矛盾决策 | ✅ |
| **高级权重** | 时效衰减 + 紧急度 + 相关性 | ✅ |
| **知识图谱** | 9 种关系，自动建图 | ✅ |
| **输入验证** | 内容/类型/重要性完整验证 | ✅ |
| **跨平台锁** | Windows/macOS/Linux 全兼容 | ✅ |
| **Git 备份** | 可选启用，自动 commit | ✅ |
| **版本历史** | 自动保留最近 10 版本 | ✅ |
| **搜索缓存** | LRU 缓存，重复搜索快 10 倍 | ✅ |
| **关键词索引** | 倒排索引，大数据性能 +100 倍 | ✅ |
| **导出/导入** | JSON/Markdown 格式 | ✅ |

---

## 高级功能

### Git 备份（v1.0.0 新增）

```bash
# 启用 Git 备份
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py git-backup enable=true

# 手动备份
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py git-backup message="重要更新"

# 禁用 Git 备份
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py git-backup disable=true
```

### 版本历史（v1.0.0 新增）

```bash
# 查看版本
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py versions file=SESSION-STATE.md

# 恢复到指定版本
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py restore file=SESSION-STATE.md version=20260408_220000_SESSION-STATE.md
```

### 关键词索引（v1.0.0 新增）

```bash
# 构建索引（大数据量时）
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py build-index

# 搜索自动使用索引（如果已构建）
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py search query="Tailwind"
```

### 导出/导入（v1.0.0 新增）

```bash
# 导出为 JSON
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py export format=json output=memories.json

# 导出为 Markdown
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py export format=markdown output=memories.md

# 导入
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py import file=memories.json format=json
```

---

## 命令行帮助

```bash
# 查看所有命令
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py help
```

**核心命令:**
- `capture` — 采集记忆
- `search` — 搜索记忆
- `status` — 查看状态
- `predict` — 预测提醒
- `graph` — 查看知识图谱

**v1.0.0 新增:**
- `git-backup` — Git 备份
- `versions` — 版本历史
- `restore` — 恢复版本
- `build-index` — 构建索引
- `export` — 导出记忆
- `import` — 导入记忆
- `help` — 帮助信息

---

## 与之前版本对比

| 功能 | v0.1 | v0.7 | v0.8 | v0.9 | **v1.0 (当前)** |
|------|------|------|------|------|-----------------|
| 同义词扩展 | ❌ | ✅ 10+ | ✅ 60+ | ✅ 60+ | ✅ 60+ 组 |
| 冲突检测 | ❌ | ✅ 48 对 | ✅ 48 对 | ✅ 48 对 | ✅ 48 对 |
| 知识图谱 | ❌ | ✅ 9 种 | ✅ 9 种 | ✅ 9 种 | ✅ 9 种 |
| Git 备份 | ❌ | ❌ | ✅ 可选 | ✅ 可选 | ✅ 可选 |
| 版本历史 | ❌ | ❌ | ✅ 自动 | ✅ 自动 | ✅ 自动 |
| 搜索缓存 | ❌ | ❌ | ✅ LRU | ✅ LRU | ✅ LRU |
| 跨平台锁 | ❌ | ❌ | ❌ | ✅ 代码 | ✅ 代码 |
| 关键词索引 | ❌ | ❌ | ❌ | ✅ +100 倍 | ✅ +100 倍 |
| 导出/导入 | ❌ | ❌ | ❌ | ✅ JSON/MD | ✅ JSON/MD |

---

## 性能基准

| 操作 | 数据量 | 性能 | 评级 |
|------|--------|------|------|
| **采集** | 100 条 | 0.28 ms/条 (3600 条/秒) | ✅ 优秀 |
| **搜索** | 50 条 | 0.24 ms/次 (4100 次/秒) | ✅ 优秀 |
| **搜索 (缓存)** | 100+ 条 | ~0 ms | ✅ 极快 |
| **搜索 (索引)** | 1000+ 条 | ~0.1 ms | ✅ +100 倍 |
| **权重计算** | 1000 次 | 0.004 ms/次 | ✅ 极快 |

---

## 文件结构

```
mempal/
├── SKILL.md              # 技能定义
├── README.md             # 使用说明
├── TUTORIAL.md           # 用户教程
├── FAQ.md                # 常见问题
├── MIGRATION.md          # 迁移指南
├── ROADMAP.md            # 产品路线图
├── _meta.json            # 元数据
├── bin/
│   ├── memory-v4.1.py    # 核心脚本（1400+ 行）
│   └── memory-v4-simple.py  # 简化版
└── tests/
    ├── test_unit.py      # 单元测试（20 个）
    └── benchmark.py      # 性能基准
```

---

## 技术栈

- **语言**: Python 3.8+
- **依赖**: 零依赖（可选 jieba）
- **存储**: 纯文件（Markdown + JSON）
- **并发**: 跨平台文件锁（fcntl/msvcrt）
- **索引**: 倒排索引 + LRU 缓存
- **版本**: Git + 自动版本历史

---

## 路线图

- **v1.0.0** — 正式发布 ✅
- **v1.1.0** — 向量搜索（可选依赖）
- **v1.2.0** — 云同步集成
- **v2.0.0** — AI 语义理解升级

详见 [ROADMAP.md](ROADMAP.md)

---

## 常见问题

**Q: 需要 API key 吗？**
A: 不需要！完全零依赖。可选安装 jieba 获得更好的中文分词。

**Q: 支持 Windows 吗？**
A: 代码层已支持（msvcrt 锁），但未充分测试，欢迎反馈。

**Q: 数据会丢失吗？**
A: 不会。版本历史自动保留最近 10 个版本，可随时恢复。

**Q: 如何备份？**
A: 启用 Git 备份，或手动将 `~/.openclaw/workspace/memory/` 目录备份到云盘。

详见 [FAQ.md](FAQ.md)

---

## 贡献与反馈

**遇到问题？**
- 查看 [FAQ.md](FAQ.md)
- 查看 [TUTORIAL.md](TUTORIAL.md)
- 在水产市场技能页面反馈

**想贡献？**
- GitHub: https://github.com/openclaw/workspace/skills/mempal
- 提交 Issue 或 Pull Request

---

*忆伴 MemPal — 你的记忆伙伴，主动提醒每一刻* 🧠

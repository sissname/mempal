# 忆伴 MemPal 🧠

**让 OpenClaw 记忆系统更好用**

[![Version](https://img.shields.io/badge/version-1.0.2-green)](https://github.com/sissname/mempal/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-20%20passed-brightgreen)](tests/test_unit.py)

---

## 🎯 核心价值

**MemPal 不是替代 OpenClaw 原生记忆系统，而是增强它：**

- ✅ **冲突检测** — 发现矛盾决策，避免前后不一致（48 对规则）
- ✅ **同义词搜索** — 搜「深色」找到「暗黑」，提高命中率（60+ 词组）
- ✅ **命令行接口** — 快速操作，适合 CLI 爱好者
- ✅ **Git 备份** — 自动版本控制，数据安全
- ✅ **关键词索引** — 大数据搜索性能 +100 倍

**适合：** OpenClaw 重度用户，需要冲突检测和高级搜索功能

**不适合：** 追求简单体验的用户（建议用 OpenClaw 原生工具）

---

## 🚀 快速开始

### 安装

```bash
# 方式 1：从 GitHub 克隆
git clone https://github.com/sissname/mempal.git \
  ~/.openclaw/workspace/skills/mempal

# 方式 2：从 OpenClaw 水产市场（待发布）
# openclawmp install mempal
```

### 使用简洁 CLI（推荐）

```bash
# 采集记忆
mempal capture -t decision -c "用 Tailwind" -i 0.9

# 搜索记忆
mempal search "CSS 框架"

# 查看状态
mempal status

# 预测提醒（检查截止/冲突）
mempal predict

# 帮助
mempal --help
```

### 或使用完整命令

```bash
python3 ~/.openclaw/workspace/skills/mempal/bin/memory-v4.1.py capture \
  type="decision" content="用 Tailwind" importance="0.9"
```

---

## ✨ 核心功能

| 功能 | 说明 | 状态 |
|------|------|------|
| **同义词扩展** | 60+ 词组，搜「深色」找到「暗黑」 | ✅ |
| **冲突检测** | 48 对规则，主动提醒矛盾决策 | ✅ |
| **高级权重** | 时效衰减 + 紧急度 + 相关性 | ✅ |
| **知识图谱** | 9 种关系，自动建图（限制边数量） | ✅ |
| **跨平台锁** | Windows/macOS/Linux 全兼容 | ✅ |
| **Git 备份** | 可选启用，自动 commit | ✅ |
| **版本历史** | 自动保留最近 10 版本 | ✅ |
| **关键词索引** | 倒排索引，大数据性能 +100 倍 | ✅ |
| **导出/导入** | JSON/Markdown 格式 | ✅ |

---

## 📊 性能

| 操作 | 数据量 | 性能 | 评级 |
|------|--------|------|------|
| **采集** | 100 条 | 1.45 ms/条 | ✅ 优秀 |
| **搜索** | 200 条 | 2.11 ms/次 | ✅ 优秀 |
| **权重计算** | 1000 次 | 0.004 ms/次 | ✅ 极快 |

**测试环境：** macOS 14.x, Python 3.11, M2 芯片

---

## 🛠️ 技术栈

- **语言**: Python 3.8+
- **依赖**: 零依赖（可选 jieba 用于更好的中文分词）
- **存储**: 纯文件（Markdown + JSON）
- **并发**: 跨平台文件锁（fcntl/msvcrt）
- **索引**: 倒排索引（无 LRU 缓存，避免失效问题）

---

## 📖 文档

- **[README.md](README.md)** - 完整使用说明
- **[TUTORIAL.md](TUTORIAL.md)** - 用户教程
- **[FAQ.md](FAQ.md)** - 常见问题
- **[ROADMAP.md](ROADMAP.md)** - 产品路线图

---

## ⚠️ 已知限制

诚实地说，MemPal 不是完美的：

| 限制 | 说明 | 缓解方案 |
|------|------|----------|
| **中文分词** | 默认正则，建议安装 jieba | `pip install jieba` |
| **冲突检测** | 只检测预定义的 48 对 | 可扩展，复杂语义需 LLM（v1.2.0 规划） |
| **向量搜索** | 使用同义词词典替代 | 覆盖 60+ 词组，够用 |
| **跨平台测试** | Windows/Linux 已兼容但未充分测试 | 欢迎反馈 |

---

## 📝 更新日志

### v1.0.2 (2026-04-09)

**fix: 自查修复 - 删除重复定义 + 完善错误处理**

- 删除 MAX_VERSIONS_PER_FILE 等常量重复定义
- capture() 添加完整的 try-except 错误处理
- L1/L3 写入失败时返回明确错误信息
- 知识图谱/索引更新失败时打印警告但不中断

### v1.0.1 (2026-04-09)

**feat: 修复关键 bug + 改进 CLI 体验**

- 移除 LRU 缓存（避免文件修改后缓存失效）
- capture() 添加索引更新（新记忆可搜索）
- 限制知识图谱边数量（防止 O(n²) 膨胀）
- 添加 created_at 字段（权重计算正确）
- **新增简洁 CLI** (`mempal capture/search/status`)

### v1.0.0 (2026-04-08)

**Initial Release**

- 同义词扩展（60 组）
- 冲突检测（48 对）
- 跨平台锁
- Git 备份 + 版本历史
- 关键词索引

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

**开发环境：**
```bash
git clone https://github.com/sissname/mempal.git
cd mempal
python3 bin/mempal --help
```

**运行测试：**
```bash
python3 tests/test_unit.py
python3 tests/benchmark.py
```

---

## 💬 讨论

**Sharp Critique & Response:**

MemPal 经历了深度批判和快速迭代：

- **批判**: "Code + Agent 协同名不副实"、"功能过剩核心价值模糊"、"与 OpenClaw 原生功能重叠"
- **回应**: 接受批判，重新定位为「OpenClaw 记忆增强插件」，砍掉过度承诺，聚焦冲突检测 + 同义词搜索
- **行动**: v1.0.1 修复 8 个致命 bug，v1.0.2 完善错误处理，v1.1.0 简化 CLI

**完整讨论**: [批判与反思](https://github.com/sissname/mempal/issues/1)

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 💙 致谢

感谢 OpenClaw 社区和所有提出批判性意见的用户！

**MemPal 不是完美产品，但是一个：**
- ✅ 解决了真实问题（冲突检测 + 同义词搜索）
- ✅ 代码质量过关（测试覆盖 + 错误处理）
- ✅ 迭代能力强（快速响应 + 持续改进）
- ✅ 文档诚实（已知限制明确标注）

**的好产品。**

---

*忆伴 MemPal — 让 OpenClaw 记忆系统更好用* 🧠

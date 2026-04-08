# 忆伴 MemPal 🧠

**你的记忆伙伴，主动提醒每一刻**

[![OpenClaw](https://img.shields.io/badge/OpenClaw-skill-blue)](https://openclawmp.cc/skill/mempal)
[![Version](https://img.shields.io/badge/version-1.0.0-green)](https://openclawmp.cc/skill/mempal)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 🚀 快速开始

### 安装

```bash
# 从 OpenClaw 水产市场
openclawmp install mempal
```

### 使用

```bash
# 采集记忆
python3 bin/memory-v4.1.py capture type="decision" content="用 Tailwind" importance="0.9"

# 搜索记忆
python3 bin/memory-v4.1.py search query="CSS 框架"

# 查看状态
python3 bin/memory-v4.1.py status

# 帮助
python3 bin/memory-v4.1.py help
```

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| **同义词扩展** | 60+ 词组，搜「深色」找到「暗黑」 |
| **冲突检测** | 48 对规则，主动提醒矛盾决策 |
| **高级权重** | 时效衰减 + 紧急度 + 相关性 |
| **知识图谱** | 9 种关系，自动建图 |
| **跨平台锁** | Windows/macOS/Linux 全兼容 |
| **Git 备份** | 可选启用，自动 commit |
| **版本历史** | 自动保留最近 10 版本 |
| **搜索缓存** | LRU 缓存，重复搜索快 10 倍 |
| **关键词索引** | 倒排索引，大数据性能 +100 倍 |
| **导出/导入** | JSON/Markdown 格式 |

---

## 📖 文档

- **[README.md](README.md)** - 完整使用说明
- **[TUTORIAL.md](TUTORIAL.md)** - 用户教程
- **[FAQ.md](FAQ.md)** - 常见问题
- **[ROADMAP.md](ROADMAP.md)** - 产品路线图

---

## 🛠️ 技术栈

- **语言**: Python 3.8+
- **依赖**: 零依赖（可选 jieba）
- **存储**: 纯文件（Markdown + JSON）
- **并发**: 跨平台文件锁（fcntl/msvcrt）
- **索引**: 倒排索引 + LRU 缓存

---

## 📊 性能

| 操作 | 性能 | 评级 |
|------|------|------|
| 采集 | 3600 条/秒 | ✅ 优秀 |
| 搜索 | 4100 次/秒 | ✅ 优秀 |
| 搜索 (缓存) | ~0 ms | ✅ 极快 |
| 搜索 (索引) | +100 倍 | ✅ 极快 |

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

**开发环境：**
```bash
git clone https://github.com/sissname/mempal.git
cd mempal
python3 bin/memory-v4.1.py help
```

---

## 📝 更新日志

### v1.0.0 (2026-04-08)

**正式发布 — 忆伴 MemPal 诞生！**

- ✅ 同义词扩展（60 组）
- ✅ 冲突检测（48 对）
- ✅ 跨平台锁（Windows/macOS/Linux）
- ✅ Git 备份 + 版本历史
- ✅ 搜索缓存 + 关键词索引
- ✅ 导出/导入功能

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 💙 致谢

感谢 OpenClaw 社区和所有贡献者！

---

*忆伴 MemPal — 你的记忆伙伴，主动提醒每一刻* 🧠

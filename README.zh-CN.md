
# Teshi

<div align="center">

**一款专为测试人员打造的 IDE 工具**

[English](README.md) | 中文文档

[功能特性](#功能特性) • [快速开始](#快速开始) • [使用指南](#使用指南) • [开发文档](#开发文档) • [许可证](#许可证)

</div>

---

## 📖 简介

Teshi 是一款基于 PySide6 开发的测试用例管理工具，专为测试人员设计。它提供了直观的界面和强大的功能，帮助您更高效地编写、管理和组织测试用例。

### 为什么选择 Teshi？

- 🚀 **简洁高效** - 基于 Markdown 的测试用例管理
- 🔍 **强大搜索** - 基于 FTS5 的全文搜索引擎，支持中文分词
- 🎯 **BDD 支持** - 内置 BDD/Gherkin 格式转换
- 📊 **可视化视图** - 测试用例思维导图展示
- 💾 **工作区管理** - 自动保存工作状态
- 🔄 **实时监控** - 文件监控与增量索引

---

## ✨ 功能特性

### 核心功能

#### 1. 测试用例编辑器
- Markdown 格式编写
- 语法高亮
- 实时预览
- 自动保存

#### 2. 项目资源管理器
- 树形目录结构
- 快速导航
- 文件搜索
- 工作区状态保存

#### 3. BDD 格式转换
- 标准格式 ⇄ BDD/Gherkin
- Given-When-Then 映射
- 保留步骤编号

#### 4. BDD 思维导图
- 可视化展示测试用例结构
- 自动解析 BDD
- 实时同步

#### 5. 全文搜索引擎
- SQLite FTS5
- 中文 1-gram / 2-gram 分词
- 高亮显示
- 增量更新

#### 6. 工作区管理
- 保存标签页
- 保存光标位置
- 保存 Dock 布局
- 保存项目树展开状态

#### 7. 文件监控
- 自动检测 Markdown 变化
- 实时更新索引
- 1 秒防抖

---

## 🚀 快速开始

### 系统要求
- Windows 10/11
- Python 3.13+（开发环境）
- 512MB+ 内存

### 安装方式

#### 方式一：直接使用（推荐）
1. 从 [Releases](../../releases) 下载 `teshi-windows-x64.zip`
2. 解压
3. 运行 `teshi.exe`

#### 方式二：从源码运行

```bash
git clone https://github.com/yourusername/teshi.git
cd teshi
poetry install
poetry run python -m teshi.main
```
## 📚 使用指南

### 创建项目

1. 启动 Teshi
2. 选择“创建新项目”或“打开现有项目”
3. 选择项目文件夹

### 编写测试用例

```markdown
# 测试用例标题

## 测试用例名称
具体名称

## 前置条件
1. 条件1

## 操作步骤
1. 步骤1

## 预期结果
1. 结果1
```

### 使用 BDD 模式

1. 使用标准格式
2. 点击 BDD 切换按钮
3. 自动转换为 Gherkin
4. 再次点击可切回

### 搜索测试用例

快捷键：`Ctrl + Shift + F`

---

## 🛠 开发文档

### 项目结构

```
teshi/
├── teshi/
│   ├── main.py
│   ├── assets/
│   ├── controllers/
│   ├── models/
│   ├── repositories/
│   ├── utils/
│   └── views/
├── tests/
├── scripts/
├── build_exe.py
├── pyproject.toml
└── README.md
```

### 构建

```bash
poetry install --with build
python build_exe.py
```

---

## 📄 许可证

本项目采用 Apache-2.0 许可证。

---

<div align="center">

如果这个项目对你有帮助，请给个 ⭐ Star！

</div>
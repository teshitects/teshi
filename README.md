# Teshi

<div align="center">

**An intelligent test IDE designed for testers**

English | [中文文档](README.zh-CN.md)

[Features](#features) • [Quick Start](#quick-start) • [User Guide](#user-guide) • [Developer Guide](#developer-guide) • [License](#license)

</div>

---

## 📖 Introduction

Teshi is a test case management tool built with PySide6, designed specifically for testers. It provides an intuitive interface and powerful features to help you write, manage, and organize test cases more efficiently.

### Why Teshi?

- 🚀 **Simple & Efficient** – Markdown-based test case management
- 🔍 **Powerful Search** – FTS5 full-text search with Chinese segmentation
- 🎯 **BDD Support** – Built-in BDD/Gherkin conversion
- 📊 **Visualization** – Mind map view for test cases
- 💾 **Workspace Management** – Auto-save and session restore
- 🔄 **Real-time Monitoring** – File watching & incremental indexing

---

## ✨ Features

### Core Features

#### 1. Test Case Editor
- Markdown-based editing
- Syntax highlighting
- Real-time preview
- Auto-save

#### 2. Project Explorer
- Tree structure navigation
- Quick file access
- File search
- Workspace state persistence

#### 3. BDD Conversion
- Standard ⇄ BDD/Gherkin
- Given-When-Then mapping
- Step number preservation
- Global BDD mode toggle

#### 4. BDD Mind Map
- Visual representation of test case structure
- Auto-parsing of BDD format
- Real-time sync with editor

#### 5. Full-text Search Engine
- SQLite FTS5-based indexing
- Chinese 1-gram & 2-gram segmentation
- Highlighted results
- Incremental updates

#### 6. Workspace Management
- Save opened tabs
- Save editor cursor position
- Save dock layout
- Save project tree expansion state

#### 7. File Monitoring
- Auto-detect Markdown changes
- Real-time index updates
- 1-second debounce

---

## 🚀 Quick Start

### System Requirements
- **OS**: Windows 10/11
- **Python**: 3.13+ (for development)
- **Memory**: 512MB+

### Installation

#### Option 1: Use Prebuilt Binary (Recommended)
1. Download `teshi-windows-x64.zip` from [Releases](../../releases)
2. Extract to any directory
3. Run `teshi.exe`

#### Option 2: Run from Source

```bash
git clone https://github.com/yourusername/teshi.git
cd teshi
poetry install
poetry run python -m teshi.main
```

## 📚 User Guide

### Create a Project

1. Launch Teshi
2. Choose “Create New Project” or “Open Existing Project”
3. Select a folder

### Write Test Cases

```markdown
# Test Case Title

## Test Case Name
Your test case name

## Preconditions
1. Condition 1
2. Condition 2

## Steps
1. Step 1
2. Step 2

## Expected Results
1. Result 1
2. Result 2
```

### Use BDD Mode

1. Write in standard format
2. Click the BDD toggle button
3. Convert to Gherkin format
4. Click again to revert

### Search Test Cases

Shortcut: `Ctrl + Shift + F`

---

## 🛠 Developer Guide

### Project Structure

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

### Build

```bash
poetry install --with build
python build_exe.py
```

---

## 📄 License

This project is licensed under the Apache-2.0 License.

---

<div align="center">

If you find this project helpful, please ⭐ Star it!

</div>
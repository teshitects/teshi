<p align="center">
<img src="teshi/assets/teshi_icon48.png" width="48"/>
</p>

<div align="center">

## Teshi
**An IDE tool built specifically for testers**
</div>

<div align="center">

English | [中文](README.zh-CN.md)

[Features](#Features) • [Quick Start](#QuickStart) • [User Guide](#UserGuide) • [License](#License)

</div>

---

## Introduction

Teshi is an Integrated Testing Environment (ITE) tool designed specifically for testers. Its goal is to **boost tester productivity**—even developers are eager to use Teshi for batch test case execution.

### Why Choose Teshi?

- **Built for Testers** - Developed by frontline testers with deep insight into testing pain points
- **Streamlined and Efficient** - Markdown-based test case management
- **Powerful Search** - Full-text multi-keyword search powered by FTS5

---

## Roadmap

- [x] [Test Cases] Full-text search
- [ ] [Test Cases] Import test cases from third-party platforms (TestLink, Jira, etc.)
- [ ] [Test Cases] Integrate AI features to assist designing test points on mind maps
- [ ] [Test Cases] AI-assisted verification of team test case checklists
- [ ] [Test Cases] Import cases from third-party platforms. AI-assisted field mapping during import
- [ ] [Test Cases] Temporary workspace for staging restructured cases
- [ ] [UI Automation] Record and generate UI automation scripts
- [ ] [API Automation] Generate API test cases from UI automation scripts using Agent
- [ ] [API Automation] Capture errors and hand them over to Agent for processing
- [ ] [Defects] One-click defect reporting plugin for web projects
- [ ] [Defects]AI-integrated defect analysis to identify risk modules
- [ ] [Plugin] Plugin mechanism for easy feature expansion
- [ ] [Plugin]Network request capture and comparison
- [ ] [General] Custom configuration of AI models

## Key Features

Stores each text test case as a Markdown file for multi-dimensional management

#### 1. Test Case Editor
- Markdown formatting
- Syntax highlighting
- Real-time preview

#### 2. Project Explorer
- Tree-based directory structure
- Workspace state saving

#### 3. BDD Mind Map
- Visual representation of test case structure
- Automatic BDD parsing
- Real-time synchronization

---

## QuickStart

#### Method One: Direct Use (Recommended)
1. Download `teshi-windows-x64.zip` from [Releases](../../releases)
2. Extract the archive
3. Run `teshi.exe`

#### Method Two: Run from Source Code

```bash
git clone https://github.com/yourusername/teshi.git
cd teshi
poetry install
poetry run python -m teshi.main
```

## UserGuide

### Create a Project

1. Launch Teshi
2. Select “Create New Project” or “Open Existing Project”
3. Choose the project folder

### Writing Test Cases


### Using BDD Mode

Click the BDD icon on the right to open the mind map window

### Searching Test Cases

Click the search button in the left toolbar

---




## License

This project is licensed under the Apache License, Version 2.0.

---

<div align="center">

If this project has been helpful to you, please give it a ⭐ Star!

</div>
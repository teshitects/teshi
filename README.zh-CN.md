<p align="center">
<img src="teshi/assets/teshi_icon48.png" width="48"/>
</p>

<div align="center">

## Teshi
**一款专为测试人员打造的 IDE 工具**
</div>

<div align="center">

[English](README.md) | 中文文档

[功能特性](#功能特性) • [快速开始](#快速开始) • [使用指南](#使用指南) • [开发文档](#开发文档) • [许可证](#许可证)

</div>

---

## 简介

Teshi 是一款 ITE 工具 (Integrated Testing Environment) ，专为测试人员设计。目标是**提高测试人员效率**，开发人员也抢着使用 Teshi 批跑用例。

### 为什么选择 Teshi？

- **专为测试人员打造** - 由一线测试人员开发，深刻理解测试工作痛点
- **简洁高效** - 基于 Markdown 的测试用例管理
- **强大搜索** - 基于 FTS5 的全文多关键字搜索

---

## 路线图

- [x] 【测试用例】全文搜索
- [ ] 【测试用例】从第三方平台（TestLink、Jira等）导入测试用例
- [ ] 【测试用例】融入AI功能，辅助在思维导图上设计测试点
- [ ] 【测试用例】AI辅助检查团队测试用例checklist
- [ ] 【测试用例】从第三方平台导入用例。AI辅助导入时的字段映射
- [ ] 【测试用例】临时工作区，暂存重构的用例
- [ ] 【UI自动化】录制生成UI自动化脚本
- [ ] 【API自动化】通过UI自动化脚本生成API测试用例，Agent
- [ ] 【API自动化】捕获错误并交由Agent处理
- [ ] 【缺陷】Web项目一键提单插件
- [ ] 【缺陷】缺陷分析融入AI，识别风险模块
- [ ] 【插件】插件机制，方便扩展功能
- [ ] 【插件】网络请求捕获和比对
- [ ] 【通用】自定义配置AI模型

## 功能特性

将每条文本测试用例都存储为 Markdown 文件，便于进行多维度管理

#### 1. 测试用例编辑器
- Markdown 格式编写
- 语法高亮
- 实时预览

#### 2. 项目资源管理器
- 树形目录结构
- 工作区状态保存

#### 3. BDD 思维导图
- 可视化展示测试用例结构
- 自动解析 BDD
- 实时同步

---

## 快速开始

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

## 使用指南

### 创建项目

1. 启动 Teshi
2. 选择“创建新项目”或“打开现有项目”
3. 选择项目文件夹

### 编写测试用例


### 使用 BDD 模式

点击右侧的 BDD 图标，出现思维导图窗口

### 搜索测试用例

点击左侧工具栏的搜索按钮

---


## 许可证

本项目采用 Apache-2.0 许可证。

---

<div align="center">

如果这个项目对你有帮助，请给个 ⭐ Star！

</div>
# 📝 MeetingAgent Pro

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Whisper](https://img.shields.io/badge/Whisper-OpenAI-orange.svg)

**智能会议纪要助手 | AI-Powered Meeting Minutes Generator**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [技术架构](#-技术架构) • [使用指南](#-使用指南)

</div>

---

## 🌟 项目简介

**MeetingAgent Pro** 是一款基于大语言模型和 RAG（检索增强生成）技术的智能会议纪要生成工具。它能够自动将会议录音或文本转换为结构化的会议纪要，支持多模态输入、知识库参考和专业文档导出。

### ✨ 核心亮点

- 🎙️ **语音转写**：集成 Whisper 模型，精准识别会议录音
- 📚 **智能参考**：RAG 技术检索知识库，生成更符合企业风格的纪要
- 🤖 **AI 生成**：基于大语言模型自动生成结构化会议纪要
- 📄 **一键导出**：支持 Word 文档格式，方便存档和分享

---

## 🚀 功能特性

| 功能 | 描述 |
|------|------|
| 🎵 多模态输入 | 支持音频 (.mp3/.wav) 和文本 (.txt/.docx) 格式 |
| 🗣️ 语音识别 | 集成 Whisper 进行高精度语音转文字 |
| 📖 知识库增强 | 上传企业文档/优秀纪要作为参考范例 |
| 🧠 智能分析 | AI 自动提取会议要点、决策事项和待办任务 |
| 📋 结构化输出 | 生成标准化的会议纪要模板 |
| 💾 Word 导出 | 一键导出专业格式的 Word 文档 |

---

## 🛠️ 技术栈

```
┌─────────────────────────────────────────────────────────┐
│                    MeetingAgent Pro                      │
├─────────────────────────────────────────────────────────┤
│  Frontend:  Streamlit                                   │
│  AI Core:   LLM (OpenAI/Azure/本地模型)                 │
│  Speech:    OpenAI Whisper                              │
│  RAG:       LangChain + Vector Store                    │
│  Export:    python-docx                                 │
│  Language:  Python 3.9+                                 │
└─────────────────────────────────────────────────────────┘
```

### 核心依赖

- **streamlit** - Web 界面框架
- **openai-whisper** - 语音识别
- **langchain** - RAG 检索增强生成
- **python-docx** - Word 文档生成
- **chromadb/faiss** - 向量数据库

---

## 📦 安装指南

### 1. 克隆项目

```bash
git clone https://github.com/1Zonghao/Meeting-agent.git
cd Meeting-agent
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# LLM 配置
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1

# 或者使用 Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=your_deployment

# Whisper 配置（可选，使用本地模型）
WHISPER_MODEL=base
```

---

## 💡 使用指南

### 启动应用

```bash
streamlit run app.py
```

浏览器自动打开 `http://localhost:8501`

### 操作流程

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  1. 上传文件  │ -> │  2. 配置模型  │ -> │  3. 生成纪要  │
└──────────────┘    └──────────────┘    └──────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
  音频/文本文件      选择 LLM 和参数      AI 自动处理
```

### 步骤详解

1. **上传会议内容**
   - 拖拽或选择会议录音/文本文件
   - 支持格式：`.mp3`, `.wav`, `.txt`, `.docx`

2. **上传知识库（可选）**
   - 上传企业背景资料、优秀纪要范例
   - 用于 Few-shot 学习和风格参考

3. **配置模型参数**
   - 选择 LLM 提供商（OpenAI/Azure/本地）
   - 调整温度和最大 token 数

4. **生成并导出**
   - 点击"生成会议纪要"
   - 预览结果后导出为 Word 文档

---

## 📁 项目结构

```
Meeting-agent/
├── app.py                      # 主应用入口 (Streamlit)
├── requirements.txt            # 依赖列表
├── .env                        # 环境变量配置
├── .gitignore                  # Git 忽略文件
│
├── chains/                     # AI 链式处理
│   └── meeting_agent_chain.py  # 会议纪要生成链
│
├── utils/                      # 工具模块
│   ├── __init__.py
│   ├── audio_utils.py          # 音频处理 (Whisper)
│   ├── config.py               # 配置管理
│   ├── embeddings.py           # 向量嵌入
│   ├── file_utils.py           # 文件读写
│   ├── rag_utils.py            # RAG 检索
│   └── word_export.py          # Word 导出
│
├── uploads/                    # 上传文件存储
│   ├── meeting/                # 会议文件
│   └── knowledge_base/         # 知识库文件
│
└── vectorstore/                # 向量数据库存储
    └── kb_index/               # 知识库索引
```

---

## 🎨 界面预览

<div align="center">

![MeetingAgent Interface](https://via.placeholder.com/800x450/4A90E2/FFFFFF?text=MeetingAgent+Pro+Interface)

*简洁直观的 Web 界面，支持拖拽上传和实时预览*

</div>

---

## 🔧 常见问题

### Q: 语音转写不准确怎么办？
A: 尝试使用更大的 Whisper 模型（如 `medium` 或 `large`），或在安静环境下录制音频。

### Q: 如何自定义会议纪要模板？
A: 修改 `chains/meeting_agent_chain.py` 中的 prompt 模板，或上传自定义范例到知识库。

### Q: 支持哪些大语言模型？
A: 目前支持 OpenAI GPT 系列、Azure OpenAI，可通过配置扩展支持本地模型（如 ChatGLM、Qwen 等）。

### Q: 如何处理长会议录音？
A: 建议将长音频分段处理，或升级服务器配置以支持更长的上下文。

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)

---

## 📬 联系方式

- **作者**: 1Zonghao
- **GitHub**: [@1Zonghao](https://github.com/1Zonghao)
- **项目地址**: [Meeting-agent](https://github.com/1Zonghao/Meeting-agent)

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star！**

Made with ❤️ by MeetingAgent Team

</div>

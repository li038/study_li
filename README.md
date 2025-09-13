# AI文档问答系统

基于LangChain和Gradio的智能文档问答系统，支持PDF文档处理和AI对话。

## 🚀 功能特性

- 📄 **PDF文档处理**: 自动加载和解析PDF文件
- 🤖 **AI问答**: 基于RAG技术的智能问答
- 🔍 **网页搜索**: 集成搜索引擎获取最新信息
- 🧮 **数学计算**: 内置安全计算器
- 🌐 **Web界面**: 友好的Gradio交互界面

## 📦 安装

### 环境要求
- Python 3.8+
- OpenAI API密钥
- SerpAPI密钥（可选）

### 快速开始

1. **克隆项目**
```bash
git clone <repository-url>
cd AI_langchain
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境**
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

4. **准备文档**
将你的PDF文件放入 `docs/` 目录

5. **启动应用**
```bash
python main.py
```

访问 http://localhost:7862 使用系统

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API密钥 | 必填 |
| `MODEL_NAME` | 模型名称 | `gpt-3.5-turbo` |
| `OPENAI_API_BASE` | API基础URL | `https://api.chatanywhere.tech` |
| `SERPAPI_KEY` | SerpAPI密钥（可选） | 空 |
| `PDF_FOLDER` | PDF存放目录 | `docs/` |

## 🔧 使用指南

### 基本用法
1. 启动应用后，在左侧文本框输入问题
2. 系统会结合PDF内容和AI知识回答问题
3. 支持连续对话，保留历史记录

### 支持的查询类型
- **文档内容**: "这份合同的主要条款是什么？"
- **计算**: "计算 15 * 23 + 47"
- **搜索**: "今天的新闻有什么？"（需要SerpAPI）

## 📁 项目结构

```
AI_langchain/
├── main.py          # 主应用入口
├── config.py        # 配置文件
├── pdf_loader.py    # PDF加载器
├── rag_setup.py     # RAG链配置
├── agent_setup.py   # AI代理配置
├── tools.py         # 工具函数
├── docs/            # PDF文档目录
├── .env.example     # 环境变量模板
├── requirements.txt # 依赖列表
└── README.md        # 项目说明
```

## 🛡️ 安全说明

- 请勿将 `.env` 文件提交到版本控制
- 已移除不安全的 `eval()` 使用
- 所有API密钥通过环境变量管理

## 🐛 常见问题

### Q: 启动时报错"请设置 OPENAI_API_KEY"
A: 请确保 `.env` 文件中已正确设置 `OPENAI_API_KEY`

### Q: 搜索功能无法使用
A: 需要设置有效的 `SERPAPI_KEY`，或留空禁用搜索功能

### Q: PDF加载失败
A: 检查PDF文件是否存在，格式是否支持

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License
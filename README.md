# 🤖 AI文档问答系统

基于LangChain的智能文档分析与问答系统，支持PDF、TXT、Markdown等格式，提供AI驱动的对话式问答体验。

## 🚀 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd AI_langchain

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥
```bash
# 复制环境模板
cp .env.example .env

# 编辑 .env 文件，填入你的OpenAI API密钥
OPENAI_API_KEY=sk-your-key-here
OPENAI_API_BASE=https://api.chatanywhere.tech  # 可选，自定义API地址
```

### 3. 启动应用
```bash
python main.py
```

应用将在 http://localhost:7862 自动打开

## 📋 功能特性

- **📄 多格式支持**: PDF、TXT、Markdown文档解析
- **🤖 智能问答**: 基于RAG技术的上下文感知对话
- **💬 会话管理**: 多会话支持，历史记录保存
- **🔍 全文搜索**: 在文档内容中快速查找
- **⚡ 智能缓存**: 提升响应速度，减少重复计算
- **🌐 中文优化**: 专为中文用户设计的界面和提示

## 🎯 使用方法

### 文档分析
1. 切换到"📊 文档分析"标签页
2. 上传PDF、TXT或Markdown文件
3. 点击"开始分析"获取AI生成的摘要和关键词

### 智能问答
1. 切换到"💬 AI问答"标签页
2. 在左侧选择或创建会话
3. 输入问题，AI将基于已上传的文档回答

### 文档搜索
1. 切换到"🔍 文档搜索"标签页
2. 输入关键词搜索已上传的文档内容
3. 查看搜索结果和上下文预览

## 📁 项目结构

```
AI_langchain/
├── main.py              # 主应用入口
├── config.py            # 配置文件
├── rag_setup.py         # RAG链初始化
├── agent_setup.py       # AI代理配置
├── src/
│   ├── core/
│   │   ├── document_processor.py  # 文档处理
│   │   ├── document_analyzer.py   # 文档分析
│   │   ├── chat_manager.py      # 会话管理
│   │   └── pdf_processor.py     # PDF处理
│   └── utils/
│       ├── cache_manager.py     # 缓存管理
│       └── logger.py           # 日志配置
├── docs/                # 文档存放目录
├── uploads/             # 上传文件目录
├── cache/               # 缓存数据
└── requirements.txt     # 项目依赖
```

## ⚙️ 配置说明

### 必需配置
- `OPENAI_API_KEY`: OpenAI API密钥

### 可选配置
- `MODEL_NAME`: AI模型名称 (默认: gpt-3.5-turbo)
- `OPENAI_API_BASE`: 自定义API地址
- `SERPAPI_KEY`: 搜索API密钥（用于联网搜索）

## 🔧 常见问题

**Q: 启动时报错缺少依赖**
```bash
pip install -r requirements.txt
```

**Q: API密钥无效**
- 检查`.env`文件是否存在且格式正确
- 确认API密钥有效且有足够余额

**Q: 文档无法解析**
- 确保文档格式为PDF、TXT或Markdown
- 检查文件是否损坏
- 查看控制台日志获取详细错误信息

**Q: 中文显示乱码**
- 确保系统支持UTF-8编码
- 检查文档编码格式

## 🐳 Docker部署

```bash
# 构建镜像
docker build -t ai-doc-qa .

# 运行容器
docker run -p 7862:7862 --env-file .env ai-doc-qa
```

## 🤝 参与开发

欢迎提交Issue和Pull Request！

### 开发环境
```bash
# 安装开发依赖
pip install pytest black flake8

# 运行测试
pytest tests/

# 代码格式化
black .
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**遇到问题？** [提交Issue](https://github.com/your-repo/issues) 或联系维护者
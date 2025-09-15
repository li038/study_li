# 🤖 AI文档问答系统

基于LangChain的智能文档分析与问答系统，支持多种文档格式（PDF、TXT、Markdown、Word、Excel等），提供AI驱动的对话式问答体验。现在支持 **OpenAI** 和 **Ollama** 双模型切换！

## 🌟 核心特性

- **多格式支持**：PDF、TXT、Markdown、Word (.docx)、Excel (.xlsx) 等
- **双模型支持**：OpenAI (GPT-3.5/4) 和 Ollama 本地模型 (llama2, llama3, mistral等)
- **智能缓存**：向量数据库缓存，避免重复处理相同文档
- **文件指纹验证**：只处理变化的文档，提高启动速度
- **多会话管理**：支持多个独立对话会话
- **全文搜索**：在文档中快速查找内容
- **文档分析**：AI生成文档摘要和关键词
- **实时对话**：基于文档内容的智能问答

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd AI_langchain

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境

```bash
# 复制环境模板
cp .env.example .env

# 编辑 .env 文件，配置你的API密钥和模型设置
```

### 3. 启动应用

```bash
# 推荐方式：使用启动脚本
python start.py

# 或直接运行
python main.py
```

应用将在 http://localhost:7860 自动打开

## 🛠️ 模型配置

### OpenAI配置

在`.env`文件中配置：

```bash
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_PROVIDER=openai
DEFAULT_MODEL=gpt-3.5-turbo
```

### Ollama配置（本地模型）

在`.env`文件中配置：

```bash
# Ollama配置
MODEL_PROVIDER=ollama
DEFAULT_MODEL=llama2
OLLAMA_BASE_URL=http://localhost:11434
```

### 安装Ollama（本地模型）

#### Windows系统

1. 下载安装包：https://ollama.ai/download
2. 运行安装程序
3. 启动Ollama服务：
   ```bash
   ollama serve
   ```

#### 拉取模型

```bash
# 拉取推荐模型
ollama pull llama2
ollama pull llama3
ollama pull mistral
ollama pull nomic-embed-text
```

## 📁 项目结构

```
AI_langchain/
├── main.py                     # 主程序入口
├── start.py                   # 启动脚本
├── rag_setup.py               # RAG链配置
├── config.py                  # 系统配置
├── requirements.txt           # Python依赖
├── .env.example              # 环境变量模板
├── cache/                    # 缓存数据
│   ├── vector/               # 向量数据库缓存
│   └── text/                 # 文本缓存
├── docs/                     # 文档目录（放置要分析的文档）
├── src/
│   ├── core/                 # 核心业务逻辑
│   │   ├── chat_manager.py      # 会话管理
│   │   ├── document_processor.py # 文档处理
│   │   ├── document_analyzer.py  # 文档分析
│   │   └── enhanced_interface.py # 增强界面
│   ├── ui/                   # 用户界面
│   │   └── enhanced_interface.py # Gradio界面实现
│   └── utils/                # 工具模块
│       ├── model_manager.py     # 模型管理器
│       ├── vector_persistence.py # 向量持久化
│       ├── cache_manager.py     # 缓存管理
│       └── logger.py           # 日志配置
└── tests/                    # 测试文件
```

## 🎯 使用指南

### 1. 启动系统

```bash
python start.py
```

### 2. 模型切换

1. 打开浏览器访问 `http://localhost:7860`
2. 点击 **"⚙️ 模型配置"** 标签页
3. 选择模型提供商：
   - **OpenAI**: 需要有效的API密钥
   - **Ollama**: 需要本地运行Ollama服务
4. 点击 **"🔍 测试连接"** 验证配置
5. 点击 **"🔄 切换模型"** 应用设置

### 3. 文档处理流程

1. 切换到 **"💬 聊天"** 标签页
2. 在 **"文件管理"** 区域上传文档
3. 系统将自动处理并缓存文档
4. 开始基于文档内容的问答对话

### 4. 缓存机制

- **首次启动**: 扫描所有文档文件并创建向量缓存
- **后续启动**: 检查文件指纹，只处理变化的文档
- **缓存位置**: `cache/vector/` 目录下
- **缓存文件**: 
  - `index.faiss`: 向量索引
  - `index.pkl`: 向量存储
  - `fingerprints.json`: 文件指纹验证

## 🐳 Docker部署

### 构建镜像

```bash
docker build -t ai-doc-qa .
```

### 运行容器

```bash
# 基础运行
docker run -p 7860:7860 --env-file .env ai-doc-qa

# 挂载本地文档目录
docker run -p 7860:7860 \
  -v $(pwd)/docs:/app/docs \
  -v $(pwd)/cache:/app/cache \
  --env-file .env ai-doc-qa
```

### Docker Compose

```yaml
version: '3.8'
services:
  ai-doc-qa:
    build: .
    ports:
      - "7860:7860"
    volumes:
      - ./docs:/app/docs
      - ./cache:/app/cache
    env_file:
      - .env
```

## 🔧 常见问题

### 启动问题

**Q: 启动时报错缺少依赖**

```bash
pip install -r requirements.txt
```

**Q: Python版本要求**

- 需要 Python 3.8+
- 推荐使用 Python 3.10+

### 模型连接问题

**Q: OpenAI连接失败**

- 检查API密钥是否正确
- 确认网络连接正常
- 检查API余额是否充足

**Q: Ollama连接失败**

- 确认Ollama服务已启动：`ollama serve`
- 检查端口是否被占用（默认11434）
- 验证模型是否已拉取：`ollama list`

### 文档处理问题

**Q: PDF文件无法解析**

- 确保PDF文件未损坏
- 检查文件权限
- 查看控制台详细错误信息

**Q: 缓存不生效**

- 删除`cache/vector/`目录重新生成
- 检查文件指纹验证逻辑
- 确认文档内容有变化

## 🧪 开发指南

### 开发环境设置

```bash
# 安装开发依赖
pip install pytest black flake8 mypy

# 运行测试
pytest tests/

# 代码格式化
black .

# 类型检查
mypy src/
```

## 🔐 安全注意事项

### API密钥安全

- 不要提交`.env`文件到git
- 使用环境变量而非硬编码
- 定期轮换API密钥

### 文档安全

- 敏感文档建议本地处理
- 定期清理上传目录
- 使用HTTPS部署

## 📞 技术支持

### 获取帮助

1. 查看详细日志输出
2. 检查系统状态信息
3. 验证模型连接状态
4. 查看缓存文件完整性

### 问题报告

请提供以下信息：
- 系统版本和Python版本
- 使用的模型类型
- 错误日志完整信息
- 复现步骤

---

**🎉 现在您可以开始使用这个强大的AI文档问答系统了！**
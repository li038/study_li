# 🤖 AI文档问答系统

一个基于LangChain和Gradio的智能文档问答系统，支持PDF文档处理、AI对话、会话管理等功能。

## ✨ 功能亮点

- **📄 PDF智能解析**: 自动提取文本、图像，支持批量处理
- **🤖 AI对话问答**: 基于RAG技术，结合文档内容进行智能问答
- **💬 会话管理**: 支持多会话、会话切换、历史记录保存
- **🔍 文档搜索**: 在已加载的PDF文档中全文搜索
- **🌐 响应式界面**: 基于Gradio的现代化Web界面
- **⚡ 缓存优化**: 智能缓存机制，提升响应速度

## 🚀 快速开始

### 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd AI_langchain

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 配置设置

```bash
# 复制环境配置模板
cp .env.example .env

# 编辑 .env 文件，填入你的API密钥
# OPENAI_API_KEY=你的OpenAI密钥
# SERPAPI_KEY=你的SerpAPI密钥（可选）
```

### 启动应用

```bash
# 启动主应用
python main.py

# 应用将在 http://localhost:7862 启动
```

## 📁 项目结构

```
AI_langchain/
├── 📄 main.py              # 主应用入口，包含Gradio界面
├── ⚙️ config.py            # 全局配置和环境变量
├── 🔗 rag_setup.py         # RAG链配置和初始化
├── 🤖 agent_setup.py       # AI代理配置
├── 🛠️ tools.py             # 工具函数集合
├── 📚 src/                 # 核心模块
│   ├── core/               # 核心业务逻辑
│   │   ├── chat_manager.py # 会话管理器
│   │   ├── pdf_processor.py # PDF处理器
│   │   └── enhanced_interface.py # 增强接口
│   └── utils/              # 工具模块
│       ├── cache_manager.py # 缓存管理
│       └── logger.py       # 日志配置
├── 📂 docs/                # PDF文档存放目录
├── 📤 uploads/             # 上传文件临时目录
├── 🗄️ cache/               # 缓存数据目录
├── 📋 requirements.txt     # 项目依赖
├── 🔧 .env.example         # 环境变量模板
├── 🐳 Dockerfile           # Docker配置
└── 📖 README.md           # 项目文档
```

## ⚙️ 配置详解

### 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `OPENAI_API_KEY` | **必填** OpenAI API密钥 | `sk-...` |
| `MODEL_NAME` | 使用的AI模型 | `gpt-3.5-turbo` |
| `OPENAI_API_BASE` | API基础URL | `https://api.chatanywhere.tech` |
| `SERPAPI_KEY` | 搜索引擎API密钥（可选） | 留空禁用搜索 |
| `PDF_FOLDER` | PDF文档目录 | `docs/` |
| `CACHE_DIR` | 缓存目录 | `cache/` |

### 配置文件

- **config.py**: 包含所有配置项的默认值
- **.env**: 本地环境变量（不提交到git）
- **.env.example**: 环境变量模板

## 🎯 使用指南

### 基本操作

1. **启动系统**
   - 运行 `python main.py`
   - 浏览器自动打开 http://localhost:7862

2. **上传文档**
   - 切换到"📁 文件"标签页
   - 拖拽或选择PDF文件上传
   - 点击"处理文件"完成解析

3. **开始对话**
   - 在"💬 聊天"标签页的输入框中提问
   - 系统会基于上传的文档内容回答

### 高级功能

- **会话管理**: 创建新会话、切换会话、导出历史
- **文档搜索**: 在已加载的文档中搜索关键词
- **缓存管理**: 自动缓存对话结果，提升响应速度

### 示例查询

```
# 文档内容查询
"这份合同的主要条款是什么？"
"请总结这份报告的核心观点"

# 文档搜索
"搜索包含'人工智能'的段落"
"查找关于'机器学习'的内容"

# 计算和搜索（需配置SerpAPI）
"计算15*23+47"
"今天有什么科技新闻？"
```

## 🐛 常见问题

### Q: 启动时报错"ModuleNotFoundError"
**A:** 确保已安装所有依赖：
```bash
pip install -r requirements.txt
```

### Q: 提示"请设置OPENAI_API_KEY"
**A:** 检查`.env`文件是否存在且包含有效的API密钥

### Q: PDF文件无法加载
**A:** 
- 检查PDF文件是否存在于`docs/`目录
- 确保文件格式正确（支持标准PDF）
- 查看日志获取详细错误信息

### Q: 搜索功能不可用
**A:** 搜索功能仅对已上传的PDF文档有效，确保已上传并处理PDF文件

### Q: 如何清理缓存
**A:** 删除`cache/`目录下的文件即可清理缓存

## 🔧 开发指南

### 项目依赖

主要依赖包括：
- `langchain`: AI框架和工具链
- `gradio`: Web界面框架
- `pymupdf`: PDF处理库
- `openai`: OpenAI API客户端
- `faiss-cpu`: 向量数据库

### 代码结构

```
main.py          # 主应用，包含界面和路由
src/core/        # 核心业务逻辑
src/utils/       # 工具类和辅助函数
rag_setup.py     # RAG配置和初始化
agent_setup.py   # AI代理配置
tools.py         # 工具函数
```

### 调试技巧

- 查看`logs/`目录的日志文件
- 使用`print()`或`logging`进行调试
- 在Gradio界面启用调试模式

## 🚀 部署指南

### Docker部署

```bash
# 构建镜像
docker build -t ai-doc-qa .

# 运行容器
docker run -p 7862:7862 --env-file .env ai-doc-qa
```

### 生产环境

1. 设置生产环境变量
2. 使用进程管理器（如PM2、systemd）
3. 配置反向代理（如Nginx）
4. 设置HTTPS证书

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发流程

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

### 代码规范

- 使用Python类型注解
- 添加适当的注释和文档
- 遵循PEP 8编码规范
- 添加单元测试

## 📄 许可证

本项目采用MIT许可证 - 查看[LICENSE](LICENSE)文件了解详情。

## 🙏 致谢

- [LangChain](https://langchain.com/) - 优秀的AI应用框架
- [Gradio](https://gradio.app/) - 简单易用的Web界面框架
- [OpenAI](https://openai.com/) - 提供强大的AI模型

---

**⭐ 如果这个项目对你有帮助，请给个Star！**
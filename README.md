# 我的世界模组翻译器

一个基于FastAPI和OpenAI的我的世界模组语言文件翻译工具，可以将英文的JSON语言文件自动翻译成中文。

## 功能特点

- 🌐 Web界面，操作简单直观
- 📁 支持JSON文件上传
- 🤖 使用AI进行智能翻译
- 🎮 专门针对我的世界模组优化
- 📥 一键下载翻译后的文件
- 🔧 保持JSON结构完整
- 📚 RAG知识库管理，支持向量化存储
- 🔍 基于语义相似度的智能检索
- 📊 翻译一致性和准确性保证
- ⚡ Qdrant向量数据库，高性能搜索

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```


### 2. 配置API密钥

复制 `.env.example` 为 `.env` 并填入你的OpenAI API密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的API密钥。

### 3. 启动服务

推荐使用启动脚本：

```bash
python run.py
```

或者直接运行主文件：

```bash
python main.py
```

或者使用uvicorn：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问网站

打开浏览器访问：http://localhost:8000

## 使用方法

### 基本翻译流程
1. 在网页界面点击"选择文件"按钮
2. 选择要翻译的JSON格式模组语言文件
3. （可选）选择一个参考知识库提高翻译质量
4. 点击"开始翻译"按钮
5. 等待翻译完成
6. 点击"下载翻译文件"获取汉化后的文件

### 知识库管理
1. 点击"知识库管理"进入管理页面
2. 填写知识库名称和描述
3. 上传已经汉化好的JSON文件作为参考
4. 创建知识库后可在翻译时选择使用
5. 支持删除不需要的知识库


## 文件结构

```
├── main.py              # FastAPI应用主文件
├── translator.py        # 翻译器模块
├── knowledge_base.py    # 知识库管理模块
├── config.py           # 配置文件
├── run.py              # 启动脚本
├── test_app.py         # 应用测试脚本
├── requirements.txt    # Python依赖
├── .env.example       # 环境变量示例
├── example_mod.json   # 示例模组文件
├── templates/         # HTML模板目录
│   ├── index.html     # 主页模板
│   └── knowledge_base.html # 知识库管理页面
├── temp_files/        # 临时文件目录（自动创建）
├── knowledge_bases/   # 知识库存储目录（自动创建）
└── README.md          # 说明文档
```


## 注意事项

- 确保上传的是有效的JSON格式文件
- API密钥需要有足够的使用额度
- 翻译质量取决于AI模型的表现
- 临时文件会保存在 `temp_files` 目录中

## 技术栈

- **FastAPI**: Web框架
- **LangChain**: AI链式调用和RAG技术
- **OpenAI**: 翻译模型和文本嵌入
- **Qdrant**: 向量数据库
- **Uvicorn**: ASGI服务器

## RAG知识库技术

本项目使用检索增强生成(RAG)技术来提升翻译质量：

1. **文本嵌入**: 使用OpenAI的text-embedding-3-small模型将翻译条目转换为向量
2. **向量存储**: 使用Qdrant向量数据库存储和索引嵌入向量
3. **语义搜索**: 基于余弦相似度进行高效的语义搜索
4. **上下文增强**: 将相关翻译作为上下文提供给AI模型

## 环境要求

- Python 3.8+
- OpenAI API密钥
- 至少2GB内存
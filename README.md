# 我的世界模组翻译器

一个基于FastAPI和OpenAI的我的世界模组语言文件翻译工具，可以将英文的JSON语言文件自动翻译成中文。

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


## 环境要求

- Python 3.8+
- OpenAI API密钥
- 至少2GB内存
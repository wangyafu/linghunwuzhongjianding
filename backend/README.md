# 灵魂物种鉴定所 - 后端服务

基于 FastAPI 构建的 AI 情绪诊断后端服务，集成了 LLM 诊断、图像生成和云存储功能。

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.8+。

```bash
cd backend
pip install -r requirements.txt
```

### 2. 🔑 密钥配置 (关键)

本项目依赖多个第三方服务，请复制 `.env.example` 为 `.env` 并填入以下密钥：

```bash
cp .env.example .env
```

| 变量名 | 说明 | 获取方式 |
|--------|------|----------|
| **OPENAI_COMPATIBLE** | LLM 服务配置 | |
| `OPENAI_BASE_URL` | OpenAI 兼容接口地址 | 如 `https://api.openai.com/v1` 或其他中转服务商地址 |
| `OPENAI_MODEL_NAME` | 模型名称 | 如 `gpt-4o-mini`、`gemini-pro` 等 |
| `OPENAI_API_KEY` | API 密钥 | 从对应的 LLM 服务商控制台获取 |
| **VOLCENGINE** | 图像生成配置 | |
| `ARK_API_KEY` | 火山引擎 API Key | [火山引擎控制台](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey) (用于调用 Seedream 模型) |
| **QINIU** | 图片存储配置 | |
| `QINIU_ACCESS_KEY` | 七牛云 AK | [七牛云密钥管理](https://portal.qiniu.com/user/key) |
| `QINIU_SECRET_KEY` | 七牛云 SK | [七牛云密钥管理](https://portal.qiniu.com/user/key) |
| `QINIU_BUCKET` | 存储空间名称 | 在七牛云对象存储中创建的 Bucket 名称 |
| `QINIU_DOMAIN` | CDN 访问域名 | 绑定在 Bucket 上的测试域名或自定义域名 (需带 `http://` 前缀) |

### 3. 运行服务

```bash
python main.py
```

服务将启动在 `http://localhost:8000`。

## 📁 目录结构

- `main.py`: 应用入口和 API 路由
- `services/`: 核心业务逻辑
  - `llm.py`: 处理诊断 Prompt 和 LLM 调用
  - `image_gen.py`: 调用 Seedream 生成图片
  - `qiniu_storage.py`: 异步抓取和存储图片
- `data/`: 静态数据
  - `preset_species.json`: 预置图库数据

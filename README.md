# HR 面试分析系统

一个轻量级 HR 面试分析工具，帮助 HR 快速分析候选人与岗位的匹配度。

## 技术栈

- **前端**: Vue 3 + Vite + Element Plus
- **后端**: Python + FastAPI + SQLAlchemy + SQLite
- **AI**: DeepSeek API

## 快速启动

### 后端

```bash
cd backend

# 使用 uv 创建虚拟环境
uv venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 安装依赖
uv pip install -r requirements.txt

# 复制环境变量模板并配置
cp .env.example .env
# 编辑 .env 填入你的 DeepSeek API Key

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 功能

1. 新建面试分析
2. 查看分析报告详情
3. 查看历史分析列表
4. 删除历史分析
5. 复制分析报告

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DEEPSEEK_API_KEY | DeepSeek API Key | - |
| DEEPSEEK_BASE_URL | DeepSeek API 地址 | https://api.deepseek.com |
| DEEPSEEK_MODEL | 模型名称 | deepseek-v4-flash |

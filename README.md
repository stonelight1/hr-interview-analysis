# AI 招聘筛选与面试评估系统

一个轻量级招聘评估工具，帮助 HR 完成岗位管理、候选人导入、简历筛选、初复试评估和历史报告复盘。

## 技术栈

- **前端**: Vue 3 + Vite + Element Plus
- **后端**: Python + FastAPI + SQLAlchemy + SQLite
- **AI**: DeepSeek API

## 快速启动

### 一键启动

Windows:

```bat
scripts\windows\start.bat
```

macOS/Linux:

```bash
./scripts/unix/start.sh
```

脚本会自动创建后端虚拟环境、安装缺失依赖、启动后端和前端，并把 pid 与日志写入 `.run/`。

脚本目录：

- `scripts/windows/`: Windows PowerShell 和 bat 启停脚本
- `scripts/unix/`: macOS/Linux shell 启停脚本

Windows 常用命令：

```bat
scripts\windows\start-backend.bat
scripts\windows\start-frontend.bat
scripts\windows\stop.bat
scripts\windows\start.bat -NoInstall
```

macOS/Linux 常用命令：

```bash
# 只启动后端
./scripts/unix/start.sh --backend-only

# 只启动前端
./scripts/unix/start.sh --frontend-only

# 已安装过依赖时跳过依赖安装
./scripts/unix/start.sh --no-install

# 停止全部服务
./scripts/unix/stop.sh
```

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

1. 招聘工作台：展示在招岗位、待筛选简历、待约面候选人、待复试候选人和高风险候选人。
2. 岗位管理：支持岗位创建、JD 文本维护、岗位状态管理和 AI 解析 JD。
3. 候选人管理：支持候选人导入、简历文本维护、AI 解析简历、招聘阶段流转和状态日志查看。
4. AI 阶段评估：支持简历筛选、初试评估、复试评估，并输出评分、建议、风险点和追问建议。
5. 历史评估报告：支持筛选、列表查看、右侧快速预览、详情页阅读、复制报告和删除报告。
6. 前端体验：采用左侧导航工作台布局，统一列表、详情、表单和报告页面的尺寸、颜色、间距与响应式表现。

## 数据库迁移

如果本地已经存在旧版本 SQLite 数据库，拉取新代码后需要执行一次字段迁移：

```bash
cd backend
python -m app.migrate_add_new_fields
```

首次启动项目时数据库表会自动创建，不需要手动执行迁移脚本。

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DEEPSEEK_API_KEY | DeepSeek API Key | - |
| DEEPSEEK_BASE_URL | DeepSeek API 地址 | https://api.deepseek.com |
| DEEPSEEK_MODEL | 模型名称 | deepseek-v4-flash |

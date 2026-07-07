# AI 招聘筛选与面试评估系统

一个轻量级招聘评估工具，进入系统后优先完成 HR 最核心的工作：基于岗位 JD 批量导入简历，并用 AI 生成初筛排名、推荐面试名单和候选人风险点。

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

1. 岗位初筛工作台：首页只保留岗位信息、批量导入简历、开始 AI 初筛三段主流程。
2. JD 解析：支持粘贴 JD，也支持上传 PDF / Word / TXT 文件，AI 自动提取岗位名称、岗位类型、地点、经验、学历、必备能力、关键筛选点和淘汰条件。
3. 批量简历导入：支持一次上传多份 PDF / DOC / DOCX 简历，展示待上传、上传中、解析中、初筛中、完成、失败状态。
4. 候选人画像：姓名、联系方式、城市、学历、学校、专业、工作年限、最近公司、最近岗位、技能、项目经历等字段优先从简历自动提取；简历未体现的字段保持为空并标记。
5. 初筛结果页：按匹配度生成候选人排名，展示推荐面试、待定、不推荐、解析失败，并支持分数、学历和结论筛选。
6. 候选人详情抽屉：左侧查看简历原文，右侧查看 AI 初筛分析、维度评分、匹配理由、风险点和建议面试问题。
7. 快捷操作：结果列表和详情抽屉可直接执行进入面试、标记待定、淘汰和下载报告。
8. 更多功能：候选人库、面试管理、报告中心、JD 模板管理等二级入口收进“更多功能”，首页不再堆表单和历史列表。

## 面试验证评分规则

候选人综合评估报告使用 `interview_verification_v1` 评分模型。简历只作为候选人声称的经历来源，最终分必须经过面试记录验证后由后端确定。

维度权重：

- 岗位核心能力验证：35 分
- 简历真实性 / 经历一致性：20 分
- 问题解决与案例深度：20 分
- 沟通表达与稳定性：10 分
- 薪资 / 到岗匹配：10 分
- 风险控制：5 分

封顶规则：

- 面试记录为空、全是数字或没有有效回答：最终分最高 35，建议不推进。
- 核心简历经历与面试回答矛盾：最终分最高 45。
- 核心岗位能力缺少面试证据：最终分最高 50。
- 核心简历声称未被面试验证：最终分最高 60。

新报告会额外包含 `interview_verification`、`scoring_model` 和 `scoring_adjustment` 字段，用于说明每个简历声称是否被面试验证，以及后端应用了哪些评分封顶规则。

## 数据库迁移

如果本地已经存在旧版本 SQLite 数据库，拉取新代码后需要执行一次字段迁移：

```bash
cd backend
python -m app.migrate_add_new_fields
```

首次启动项目时数据库表会自动创建，不需要手动执行迁移脚本。

本次迁移会确保以下任务化表存在：

- `screening_tasks`: 岗位初筛任务
- `resume_files`: 简历文件和解析状态
- `candidate_profiles`: 从简历抽取的候选人画像
- `screening_results`: 候选人与岗位匹配结果

## 岗位初筛接口

核心接口：

```http
POST /api/screening/jd/parse
POST /api/screening/jd/parse-file
POST /api/screening/tasks
POST /api/screening/tasks/{taskId}/resumes
POST /api/screening/tasks/{taskId}/start
GET  /api/screening/tasks/{taskId}/progress
GET  /api/screening/tasks/{taskId}/results
GET  /api/screening/results/{resultId}
PUT  /api/screening/results/{resultId}/status
```

初筛结论枚举：

- `RECOMMENDED`: 推荐面试
- `PENDING`: 待定
- `REJECTED`: 不推荐

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DEEPSEEK_API_KEY | DeepSeek API Key | - |
| DEEPSEEK_BASE_URL | DeepSeek API 地址 | https://api.deepseek.com |
| DEEPSEEK_MODEL | 模型名称 | deepseek-v4-flash |
| HR_API_KEY | 后端 `/api` 访问密钥，配置后请求需带 `X-API-Key` | - |
| ALLOW_UNAUTHENTICATED_LOCAL | 未配置 `HR_API_KEY` 时是否允许本机访问 | true |
| CORS_ALLOWED_ORIGINS | 允许跨域访问的前端 Origin，逗号分隔 | http://localhost:5173,http://127.0.0.1:5173 |
| MAX_RESUME_UPLOAD_FILES | 单次最多上传简历数 | 50 |
| MAX_RESUME_UPLOAD_BYTES | 单个简历文件最大字节数 | 10485760 |

如果设置了 `HR_API_KEY`，前端需要同步配置：

```bash
cd frontend
cp .env.example .env
# 将 VITE_HR_API_KEY 设置为和后端 HR_API_KEY 相同的值
```

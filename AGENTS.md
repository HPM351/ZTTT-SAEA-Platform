# AGENTS.md — HPM_OPT_WEB

## 1. 项目概述

**HPM_OPT_WEB** 是一个面向高效率微波（HPM）器件专业优化的全栈 Web 平台。
平台将 **CST Studio Suite 参数扫描**、**代理模型辅助演化算法（SAEA）优化**、**神经网络代理建模** 以及 **大语言模型文献助手** 集成到统一的浏览器工作流中。

- **简称**: HPM = High-Power Microwave（高效率微波）
- **应用领域**: 相对论磁控管及其他真空电子器件
- **所属人**: ZTTT

---

## 2. 架构总览

```
浏览器 (Vue 3 + Naive UI)
       |
       | HTTP / WebSocket  (Vite 开发代理 :5173 -> :8000)
       v
FastAPI 后端 (main.py)
  |-- engine/task_saea.py   --> SAEA 优化引擎  (Geatpy + CST)
  |-- engine/task_sweep.py  --> 网格参数扫描引擎  (CST)
  |-- engine/nn_service.py  --> 神经网络代理模型 (PyTorch)
  |-- engine/llm_service.py --> LLM 文献助手 (RAG, 多模态)
  |-- engine/cst_wrapper.py --> CST COM/Python 互操作层
  |-- engine/evaluator.py   --> 物理感知打分函数
  |-- database.py            --> SQLite ORM (SQLAlchemy)
```

平台遵循**全去物理化数据契约**设计：仿真结果、波形字典及各项指标均以动态 JSON 形式存储，不硬编码任何字段名，确保跨器件拓扑的扩展能力。

---

## 3. 仓库目录结构

```
HPM_opt_Web/
├── main.py                  # FastAPI 入口，静态文件挂载，API 路由定义
├── start.py                 # 一键启动器（同时拉起后端 + 前端）
├── setup_env.py             # CST Python 库路径配置
├── auto_gen_deps.py         # 从源码导入自动生成 requirements.txt
├── database.py              # SQLAlchemy ORM：8 张表，数据库初始化，会话工厂
├── schemas.py               # Pydantic v2 请求/响应模型
├── requirements.txt          # 后端 Python 依赖
├── system_prompt.md          # 文献助手的 LLM 系统提示词
├── SAEA_知识图谱.md             # SAEA 知识图谱文档
├── AGENTS.md                 # 本文件
│
├── engine/                   # 核心算法引擎
│   ├── __init__.py
│   ├── cst_wrapper.py        # CST DesignEnvironment 封装，参数解析
│   ├── evaluator.py          # 时域/频谱指标提取，综合评分计算
│   ├── task_saea.py          # SAEA 优化任务（GA / PSO / BO）
│   ├── task_sweep.py         # 网格扫描任务执行器
│   ├── nn_service.py         # PyTorch 代理模型训练与推理路由
│   ├── llm_service.py        # LLM 对话路由，支持 PDF/DOCX 文件解析
│   ├── api_auth.py           # 基于 JWT 的用户认证
│   ├── api_chat_history.py   # 对话会话 CRUD
│   └── api_data_center.py    # 历史任务/数据管理 API
│
├── models/                   # 已训练的神经网络权重
│   ├── S_Band Six_Cavities_*.pth / *.pt
│   └── trihead_magnetron_model_*.pth / *.pt
│
├── configs/                  # 用户保存的优化配置（JSON）
├── prompts/                  # LLM 提示词模板
│   ├── saea_main.md
│   └── saea_vision.md
│
├── hpm-frontend/             # Vue 3 + Vite 前端
│   ├── package.json
│   ├── vite.config.js         # 代理 API->:8000，构建输出->../dist
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/index.js    # 6 条路由（首页、扫描、优化、神经网络、文献、数据中心）
│       ├── views/
│       │   ├── Home.vue
│       │   ├── CstSweep.vue
│       │   ├── CstOpt.vue
│       │   ├── NeuralNet.vue
│       │   ├── LiteratureAssistant.vue
│       │   └── DataCenter.vue
│       └── components/
│           ├── FloatingChat.vue
│           ├── ScoreSandbox.vue
│           └── HelloWorld.vue
│
├── dist/                     # 生产构建产物（Vite -> ../dist）
└── .venv/                    # Python 虚拟环境（已 gitignore）
```

---

## 4. 运行环境要求

| 组件 | 版本 / 说明 |
|---|---|
| **Python** | 3.9 – 3.12（实测稳定：3.10.11） |
| **Node.js** | LTS（18.x+），需自带 npm |
| **CST Studio Suite** | 2024 或更高版本，需安装 **Python COM 库** |
| **CST Python 路径** | 环境变量 `CST_PYTHON_PATH`，默认值为 `D:\CST Studio Suite 2024\AMD64\python_cst_libraries` |
| **操作系统** | Windows（CST COM 互操作仅支持 Windows） |

---

## 5. 快速启动

### 5.1 后端配置

```bash
cd HPM_opt_Web
pip install -r requirements.txt
python setup_env.py          # 配置 CST 库路径
```

### 5.2 前端配置

```bash
cd hpm-frontend
npm install
```

### 5.3 一键启动（推荐）

```bash
# 在项目根目录下执行：
python start.py
# 该命令会在同一个终端中同时启动 FastAPI（:8000）和 Vite 开发服务器（:5173）。
# 终端打印"数据库与 SAEA 引擎初始化完成"及网址后即启动成功，浏览器访问 http://localhost:5173 即可。
```

### 5.4 手动启动（备用方案）

```bash
# 终端 1 — 后端
python main.py

# 终端 2 — 前端
cd hpm-frontend
npm run dev
```

### 5.5 生产构建

```bash
cd hpm-frontend
npm run build                    # 输出至 ../dist
# 然后将 main.py 中的 IS_PRODUCTION_MODE 设为 True，运行 python main.py
```

---

## 6. 后端核心模块详解

### 6.1 `main.py` — 应用外壳

- FastAPI 应用，配置 CORS（允许所有来源），WebSocket 端点 `/ws/{task_id}`
- 环境探测端点：`GET /api/env_info`
- 配置存取：`POST /api/save_config`、`POST /api/load_config`
- 任务数据检索：`GET /api/get_task_data/{task_id}`
- 任务控制：`POST /api/start_opt`、`POST /api/start_sweep`、`POST /api/stop_task/{task_id}`
- 生产模式自动切换 Vite 开发代理与静态 `dist/` 文件服务
- 已注册子路由：`nn_router`、`llm_router`、`data_center_router`、`auth_router`、`history_router`

### 6.2 `engine/cst_wrapper.py` — CST 互操作层

- 从 `Model/Parameters.json` 或 `.cst` 文件 XML 中解析 CST 项目参数
- 通过 `cst.interface.DesignEnvironment` 执行单点仿真
- 提取 S 参数、时域信号及场结果

### 6.3 `engine/evaluator.py` — 打分函数

- `get_time_domain_metric()` — 从时域结果中提取平均功率、波动幅度
- `analyze_spectrum()` — 基于 FFT 的频域分析
- `calc_score()` — 带物理有效性校验的多目标综合评分

### 6.4 `engine/task_saea.py` — SAEA 优化引擎

- 实现代理模型辅助演化算法
- 支持的算法类型：**SAEA-GA**、**SAEA-PSO**、**SAEA-BO**
- 使用 **Geatpy** 作为演化计算框架
- 内置参数哈希缓存，自动跳过重复的 CST 仿真
- 通过 WebSocket 实时推送种群指标和收敛数据
- 可通过 `task_status_flags` 字典进行启停控制

### 6.5 `engine/task_sweep.py` — 网格参数扫描

- 对扫描变量进行笛卡尔积枚举
- 固定参数在所有扫描点中保持恒定
- 直接集成 CST，与 SAEA 共用同一套 WebSocket 推流机制

### 6.6 `engine/nn_service.py` — 神经网络代理模型

- 基于 PyTorch 的多层感知机（MLP）代理建模
- 支持单头和多头（三头）输出配置
- 训练端点：从数据库加载数据、训练、保存 traced `.pt` 模型
- 推理端点：接收特征向量，返回预测值
- 在线学习日志通过 `NnOnlineLog` 持久化

### 6.7 `engine/llm_service.py` — LLM 文献助手

- 支持流式响应的对话 API（`text/event-stream`）
- 多模态：支持图片（base64）与文本混合输入
- 文件解析：PDF 通过 `pypdf`，DOCX 通过 `python-docx`，旧版 `.doc` 通过 `olefile`
- 可通过 `system_prompt.md` 或 `prompts/` 模板自定义系统提示词
- 上传限制：最大 20 MB，最多 15 页 PDF，累计提取字符上限 50 000

### 6.8 认证与历史记录

| 模块 | 前缀 | 关键端点 |
|---|---|---|
| `api_auth.py` | `/api/auth` | `POST /register`、`POST /login`（JWT） |
| `api_chat_history.py` | `/api/chat` | `GET /sessions`、`POST /session`、`GET /session/{id}/messages` |
| `api_data_center.py` | `/api/data` | 历史任务浏览、导出、删除 |

---

## 7. 数据库表结构（SQLite）

| 表名 | 用途 | 关键字段 |
|---|---|---|
| `tasks` | 优化/扫描任务注册表 | `id`（UUID）、`name`、`cst_path`、`status`、`config_json` |
| `generations` | 每代最优得分快照 | `task_id`、`gen_index`、`best_score`、`best_metrics_json` |
| `individuals` | 每个被评估的个体 | `task_id`、`gen_index`、`ind_index`、`params_json`、`score`、`metrics_json` |
| `waveforms` | 个体的时域曲线数据 | `individual_id`、`task_id`、`gen_index`、`ind_index`、`waves_json` |
| `nn_online_logs` | 神经网络训练遥测 | `task_id`、`gen_index`、`loss`、`error`、`details_json` |
| `users` | 已认证用户 | `username`、`password_hash`（bcrypt 加密） |
| `chat_sessions` | LLM 对话会话 | `id`、`title`、`owner_id` |
| `chat_messages` | 单条对话消息 | `session_id`、`role`、`content` |

**设计原则**：指标和波形数据均以 JSON 列（`metrics_json`、`waves_json`）存储，不绑定固定字段结构——前端可按任意 key 动态渲染。

---

## 8. 前端路由

| 路径 | 组件 | 说明 |
|---|---|---|
| `/` | 重定向 → `/home` | 默认首页 |
| `/home` | `Home.vue` | 仪表盘，系统状态概览与快捷入口 |
| `/cst-sweep` | `CstSweep.vue` | 参数扫描：定义网格、运行、可视化 |
| `/cst-opt` | `CstOpt.vue` | SAEA 优化：GA/PSO/BO，收敛曲线展示 |
| `/nn` | `NeuralNet.vue` | 代理模型训练与预测 |
| `/literature` | `LiteratureAssistant.vue` | LLM 对话，支持文件上传 |
| `/data-center` | `DataCenter.vue` | 历史任务浏览，波形查看器 |

**技术栈**：Vue 3（组合式 API）、Vue Router 4、Naive UI、ECharts 5 + echarts-gl、Axios、Lucide 图标、Markdown-it、Highlight.js

---

## 9. 核心设计决策

### 9.1 去物理化数据契约
所有仿真输出均为动态 JSON。后端绝不硬编码 `power_val`、`eff_val` 等字段名。目标在运行时通过 `targetsList` 定义，指标以任意键值字典存储。这使同一平台无需数据库迁移即可优化磁控管、速调管或未来任何 HPM 拓扑结构。

### 9.2 参数哈希缓存
`task_saea.py` 维护一个以取整参数元组为键的 `global_cache` 字典。若在跨代或重启任务中遇到相同参数组合，将完全跳过 CST 仿真，直接复用缓存结果。

### 9.3 单任务串行执行
受限于 CST COM 接口的单线程特性（不支持并发仿真），平台强制串行执行任务。用户应将任务排队而非并行运行。

### 9.4 WebSocket 任务推流
每个任务开启一个专用 WebSocket（`/ws/{task_id}`），实时向前端推送每个个体的评估结果、每代摘要、波形数据及错误信息。

---

## 10. 开发约定

- **后端**：Python 3.10+，推荐使用类型注解。遵循 FastAPI 最佳实践进行路由分离。
- **前端**：Vue 3 组合式 API（`<script setup>`）。统一使用 Naive UI 组件，不引入其他竞争性 UI 库。
- **配置持久化**：保存至 `configs/conf_{项目名}_{hash8}.json`，以标准化 CST 路径为键。
- **模型文件**：Traced PyTorch 模型存放于 `models/`。元数据（`_meta.pth`）存储归一化参数和输出配置。
- **提示词**：LLM 系统提示词和少样本模板以 Markdown 文件形式存放于 `prompts/`。
- **分支命名**：功能分支使用 `codex/` 前缀（如 `codex/add-sweep-2d`）。
- **编码**：所有源码文件采用 UTF-8 编码。CST `.cst` 项目文件可能以系统默认编码读取。

---

## 11. 常见问题与排错

| 现象 | 可能原因 | 解决方案 |
|---|---|---|
| "CST 启动失败" | CST Python 库未加入 `sys.path` | 运行 `setup_env.py` 或设置 `CST_PYTHON_PATH` 环境变量 |
| 前端无法访问 API | Vite 代理配置错误 | 确保 `vite.config.js` 中 `/api` 代理指向 `http://localhost:8000` |
| 生产模式找不到 `dist/` | 未执行 `npm run build` | 执行构建；`outDir` 相对于 `hpm-frontend` 为 `../dist` |
| `geatpy` 导入报错 | 依赖未安装 | `pip install geatpy==2.7.0`（参见 `requirements.txt`） |
| 数据库被锁定 | 存在多个后端进程 | 关闭多余的 `python main.py` 进程；SQLite 仅支持单写入者 |

---

*面向 Codex CLI 及 GitHub 协作者生成。最后更新：2026-05-14。*

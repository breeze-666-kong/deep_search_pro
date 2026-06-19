# 深度搜索 Pro (Deep Search Pro)

## 1. 项目概述

深度搜索 Pro 是一个基于 **DeepAgents 多智能体架构** 的智能信息分析与报告生成系统。系统以空调公司业务为背景，通过一个主智能体协调三个专业子智能体，综合搜索引擎、企业数据库、内部知识库三种信息来源，执行复杂的信息检索、数据分析与文件生成任务。

用户只需提出自然语言需求（如"对比各区域空调销售数据并生成分析报告"），系统即可自动完成信息收集、分析整合、报告生成（Markdown/PDF）的全流程。

---

## 2. 系统架构

系统采用 **主-子智能体（Master-SubAgent）** 架构，基于 `deepagents` 库的 `create_deep_agent` 构建：

```
用户请求
   ↓
[main_agent] —— 主智能体（协调者）
   ├── 工具：generate_markdown / convert_md_to_pdf / read_file_content
   │
   ├── [network_search_agent] —— 网络搜索智能体
   │     └── 工具：internet_search (Tavily)
   │
   ├── [database_query_agent] —— 数据库查询智能体
   │     └── 工具：list_sql_tables / get_table_data / execute_sql_query
   │
   └── [knowledge_base_agent] —— 知识库智能体
         └── 工具：get_assistant_list / create_ask_delete (RAGFlow)
   ↓
生成结果（文本回复 / Markdown / PDF 文件）
```

### 执行流程

1. 主智能体接收用户问题，根据问题性质决定调用哪些子智能体
2. 各子智能体分别从互联网、MySQL 数据库、RAGFlow 知识库获取信息
3. 主智能体收集子智能体返回的信息，进行分析整合
4. 根据用户需求，主智能体使用 `generate_markdown` 和 `convert_md_to_pdf` 工具生成最终文档
5. 所有中间步骤和最终结果通过 WebSocket 实时推送到前端

---

## 3. 技术栈

| 类别 | 技术 | 用途 |
|------|------|------|
| **Web 框架** | FastAPI | 提供 REST API 和 WebSocket 实时通信 |
| **多智能体框架** | DeepAgents (langgraph) | 主-子智能体编排与状态管理 |
| **大语言模型** | 阿里云百炼 DashScope (Qwen-Max) | 智能体推理、信息分析、内容生成 |
| **联网搜索** | Tavily API | 实时网络信息检索 |
| **企业数据库** | MySQL (mysql-connector-python) | 企业业务数据存储与查询 |
| **知识库** | RAGFlow (ragflow-sdk) | 企业内部知识库（FAQ/文档）|
| **前端** | Vue 3 + Vite + axios | 智能对话与文件管理界面 |
| **输出文件** | Markdown / PDF | 报告生成格式 |
| **日志** | Loguru | 结构化日志记录 |
| **运行环境** | Python >= 3.12 | |

---

## 4. 智能体详解

### 4.1 主智能体 (main_agent)

主智能体是整个系统的协调核心，负责：
- 理解用户需求，规划执行步骤
- 识别需要调用哪些子智能体，分发任务
- 收集子智能体返回的信息，进行综合分析
- 使用自有工具完成文件生成（Markdown/PDF）
- 管理工作目录，确保所有文件操作在会话目录内

**自备工具：**
- `generate_markdown(content, filename, path)` — 根据文本内容生成 Markdown 文件
- `convert_md_to_pdf(md_filename, pdf_filename, path)` — 将 Markdown 转换为 PDF
- `read_file_content(filename)` — 读取用户上传的文件内容进行分析

### 4.2 网络搜索智能体 (network_search_agent)

负责从互联网获取公开信息，使用 Tavily API 进行搜索。

**工具：**
- `internet_search(query, topic, max_results)` — 执行网络搜索，支持 news/finance/general 三种主题，支持返回精简或详细结果

### 4.3 数据库查询智能体 (database_query_agent)

负责与 MySQL 企业数据库交互，查询结构化业务数据。

**工具：**
- `list_sql_tables()` — 列出数据库中所有可用表
- `get_table_data(table_name)` — 读取指定表的前 100 行数据
- `execute_sql_query(query)` — 执行自定义 SQL 查询

数据库包含药品信息、药品库存信息、药品销售数据等业务数据表。

### 4.4 知识库智能体 (knowledge_base_agent)

负责与 RAGFlow 知识库交互，检索企业内部非结构化知识。

**工具：**
- `get_assistant_list()` — 查询 RAGFlow 服务器中可用的助手列表及其关联知识库
- `create_ask_delete(chat_name, question)` — 向指定助手发起一次提问，获取答案后自动关闭会话

---

## 5. 数据流与监控

系统内置完整的运行监控机制（`api/monitor.py`）：

| 事件类型 | 触发时机 | 说明 |
|---------|---------|------|
| `session_created` | 会话创建 | 通知前端会话工作目录路径 |
| `assistant_call` | 调用子智能体 | 通知前端正在调用哪个子智能体及其任务描述 |
| `tool_start` | 工具调用开始 | 通知前端正在执行哪个工具及其参数 |
| `task_result` | 任务完成 | 通知前端最终结果内容 |
| `error` | 异常发生 | 通知前端错误信息 |

监控数据通过 WebSocket 实时推送到前端，用户可以在界面上看到每个步骤的进度。

---

## 6. Prompt 设计

所有 Prompt 通过 YAML 文件（`prompt/prompts.yml`）集中管理：

| Prompt 名称 | 用途 |
|------------|------|
| main_agent.system_prompt | 主智能体系统指令，定义团队组成、工作流程、文件生成规则 |
| sub_agents.tavily.system_prompt | 网络搜索智能体指令，规范搜索策略和质量要求 |
| sub_agents.db.system_prompt | 数据库查询智能体指令，定义 SQL 查询流程 |
| sub_agents.ragflow.system_prompt | 知识库智能体指令，定义提问策略 |

主智能体 Prompt 包含详细的执行顺序约束（"必须先获取信息再生成文件"、"严禁使用占位符内容生成文件"等），保证生成内容的真实性和完整性。

---

## 7. 项目目录结构

```
deep_search_pro/
├── agent/
│   ├── main_agent.py              # 主智能体定义与执行入口
│   ├── llm.py                     # LLM 客户端（Qwen-Max）
│   ├── prompts.py                 # YAML Prompt 加载器
│   └── subagents/
│       ├── database_query_agent.py  # 数据库查询子智能体
│       ├── knowledge_search_agent.py # 知识库检索子智能体
│       └── network_search_agent.py  # 网络搜索子智能体
├── api/
│   ├── server.py                  # FastAPI 服务入口（含 WebSocket）
│   ├── context.py                 # 会话上下文管理
│   └── monitor.py                 # 工具调用监控与 WebSocket 推送
├── tools/
│   ├── db_tools.py                # 数据库操作工具
│   ├── tavily_tool.py             # 网络搜索工具
│   ├── ragflow_tools.py           # RAGFlow 知识库工具
│   ├── markdown_tools.py          # Markdown 生成工具
│   ├── pdf_tools.py               # PDF 转换工具
│   └── upload_file_read_tool.py   # 上传文件读取工具
├── ui/                            # Vue 3 前端项目
├── utils/
│   ├── path_utils.py              # 路径解析工具
│   └── word_converter.py          # Word 文档转换工具
├── ragflow/                       # RAGFlow 配置与示例
├── prompt/
│   └── prompts.yml                # 所有智能体的 Prompt 定义
├── core/
│   └── logger.py                  # 日志配置
├── output/                        # 会话输出文件目录
├── updated/                       # 用户上传文件目录
├── logs/                          # 运行日志
├── custom_logs/                   # 自定义日志
├── .env                           # 环境变量配置
├── pyproject.toml                 # 项目依赖
└── requirements.txt               # 依赖清单
```

---

## 8. 快速开始

### 环境准备

1. **安装 Python 3.12+ 与 uv**

2. **克隆项目并安装依赖**
   ```bash
   cd deep_search_pro
   uv sync
   ```

3. **配置环境变量**
   编辑 `.env` 文件，填写：
   - `OPENAI_API_KEY` / `OPENAI_BASE_URL` — 百炼 DashScope 大模型 API
   - `TAVILY_API_KEY` — Tavily 网络搜索 API Key
   - `RAGFLOW_API_URL` / `RAGFLOW_API_KEY` — RAGFlow 知识库连接信息
   - `MYSQL_*` — MySQL 数据库连接信息

### 启动后端服务

```bash
# 需先进入项目根目录
cd deep_search_pro
python -m api.server
# 服务默认运行在 http://0.0.0.0:8000
```

### 启动前端

```bash
cd ui
npm install
npm run dev
# 前端默认运行在 http://localhost:5173
```

### 使用流程

1. 打开前端页面，输入问题
2. 系统自动调用各子智能体收集信息
3. 前端实时显示每个步骤的进度
4. 最终结果以文本或文档（Markdown/PDF）形式返回
5. 支持文件上传和下载

---

## 9. API 接口

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/task` | 提交查询任务（返回 thread_id 后异步执行）|
| WebSocket | `/ws/{thread_id}` | 实时接收智能体执行进度与结果 |
| POST | `/api/upload` | 上传文件供智能体分析 |
| GET | `/api/files` | 列出会话输出目录下的文件 |
| GET | `/api/download` | 下载指定文件 |

---

## 10. 设计亮点

- **多智能体协作**：主智能体协调三个专业子智能体，各自专注一个信息源，并行执行
- **实时监控**：每个工具调用、子智能体调用都通过 WebSocket 实时推送到前端
- **文件生成**：支持 Markdown 和 PDF 格式的报告生成，可与信息检索无缝衔接
- **多源信息融合**：综合互联网信息、企业数据库、内部知识库三种来源
- **严格的执行顺序**：Prompt 中规定了"先获取信息再生成文件"的硬约束，防止虚假内容
- **会话隔离**：每个会话独立的工作目录和 WebSocket 连接，互不干扰
- **DeepAgents 框架**：基于 langgraph，天然支持工具调用、子智能体、流式输出

---

## 11. 注意事项

- LLM 使用阿里云百炼 DashScope（Qwen-Max），需有效 API Key
- Tavily 网络搜索需要单独的 API Key（需注册 tavily.com）
- RAGFlow 知识库需提前部署并配置好助手
- MySQL 数据库需预置业务数据表
- 系统设计基于空调公司业务场景，数据库结构和 Prompt 可根据实际业务调整
- 生产环境部署建议修改 FastAPI CORS 配置

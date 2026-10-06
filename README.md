# My Agent — 复刻类 DeerFlow 的超级 Agent

基于 LangGraph + LangChain + DeepSeek + FastAPI + MCP 从零搭建的个人 Agent，目标是复刻 DeerFlow 的核心架构。

**开发周期**：2025.09.30 — 2025.10.30

---

## ✅ 当前完成情况

| 模块 | 状态 | 说明 |
|---|---|---|
| **基础框架** | ✅ 完成 | LangGraph StateGraph + LangChain + DeepSeek |
| **流式服务** | ✅ 完成 | FastAPI + SSE（token / tool_call / tool_result / done / error） |
| **多轮对话** | ✅ 完成 | SQLite Checkpoint（AsyncSqliteSaver），thread_id 隔离会话 |
| **本地工具** | ✅ 完成 | `@tool` 装饰器，run_command / calculator / get_system_info 等 |
| **MCP 工具** | ✅ 完成 | MultiServerMCPClient 连接池模式，mcp_config.json 配置化 |
| **MCP Server** | ✅ 完成 | FastMCP + stdio 传输，get_current_time / calculator 等 |
| **Skills（Layer 1）** | 🚧 待写 | Prompt 模板型 Skill（code_helper / calculator_expert） |
| **Skills（Layer 2）** | ❌ 未开始 | 子图路由型 Skill（真正的"编排"） |
| **多 Agent** | ❌ 未开始 | 子 Agent 协作、路由、委托 |
| **中间件系统** | ❌ 未开始 | Tool 拦截器、权限控制、日志 |
| **前端** | 🚧 极简 | 只有基础聊天页面 |

---

## 🏗️ 架构总览

```
                     ┌─────────────────────┐
                     │    FastAPI 服务     │
                     │  POST /chat (SSE)  │
                     └─────────┬───────────┘
                               │
                     ┌─────────▼───────────┐
                     │   LangGraph Agent   │
                     │  StateGraph + ReAct │
                     └────┬────────┬───────┘
                          │        │
            ┌─────────────┘        └─────────────┐
            ▼                                     ▼
   ┌────────────────┐                   ┌────────────────────┐
   │   本地工具      │                   │   MCP 工具          │
   │   @tool 装饰器  │                   │   MultiServerMCPClient│
   │                │                   │                    │
   │ • run_command  │                   │  mcp_server.py      │
   │ • calculator   │                   │  └─ get_current_time│
   │ • get_system_  │                   │  └─ calculator      │
   │   info         │                   │                    │
   └────────────────┘                   │  mcp_config.json   │
                                        │  （可加更多 Server） │
                                        └────────────────────┘
```

### LangGraph 图结构

```
START → chat ──有 tool_calls──→ ToolNode ──→ chat（循环直到无工具调用）
                  │
                  └──无 tool_calls──→ END
```

---

## 📂 项目结构

```
my-agent/
├── src/
│   ├── agent.py           # LangGraph Agent 核心（状态图 + 事件解析）
│   ├── server.py          # FastAPI 入口 + SSE 生成器
│   ├── llm.py             # get_llm() 工厂函数（读 .env 配置）
│   ├── state.py           # AgentState TypedDict
│   ├── local_tools.py     # 本地工具（@tool 装饰器）
│   ├── mcp_server.py      # MCP Server（FastMCP + stdio）
│   ├── mcp_config.json    # MCP Server 连接配置
│   ├── skills.py          # Skills 定义（待写）
│   ├── index.html         # 极简聊天页面
│   └── agent.db           # SQLite Checkpoint（自动生成）
├── .env                   # DEEPSEEK_API_KEY=...（不提交）
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /root/my-agent
uv sync
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY
```

### 3. 启动服务

```bash
fuser -k 8000/tcp 2>/dev/null; sleep 1
cd /root/my-agent/src
/root/my-agent/.venv/bin/python3 -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 测试

```bash
# curl 测试
curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "现在几点了？", "thread_id": "test"}'

# 浏览器测试
open http://localhost:8000/
```

---

## 🔌 工具链

### 当前可用工具（5 个）

| 来源 | 工具 | 说明 |
|---|---|---|
| 本地 | `run_command` | 执行 shell 命令 |
| 本地 | `calculator` | 计算数学表达式 |
| MCP | `get_current_time` | 获取当前北京时间 |
| MCP | `calculator` | 计算数学表达式（MCP 版） |
| （更多待加） | | |

### 添加新 MCP Server

编辑 `src/mcp_config.json`：

```json
{
  "servers": [
    {
      "name": "通用工具",
      "command": "/root/my-agent/.venv/bin/python3",
      "args": ["mcp_server.py"]
    },
    {
      "name": "网页搜索",
      "command": "uvx",
      "args": ["mcp-server-serper"],
      "transport": "stdio"
    }
  ]
}
```

重启服务即自动加载。

---

## 📊 与 DeerFlow 的差距

| 能力 | DeerFlow | 当前项目 | 差距 |
|---|---|---|---|
| **Agent 框架** | LangGraph + 自定义 Runtime | LangGraph ✅ | 小 |
| **流式输出** | SSE + 多事件类型 | SSE + 5 种事件 ✅ | 小 |
| **工具系统** | ToolRegistry + 多来源 | 本地 + MCP ✅ | 小 |
| **Skills Layer 1** | Prompt 模板 + 意图匹配 | 待写 skills.py 🚧 | 中 |
| **Skills Layer 2** | 子图路由 + 多 Agent | ❌ 未开始 | 大 |
| **多 Agent 编排** | Lead Agent + Sub Agent 委托 | ❌ | 大 |
| **中间件系统** | Tool 拦截器、权限、日志 | ❌ | 大 |
| **长时序任务** | Asyncio + 断点续跑 | checkpoint 基础 ✅ | 中 |
| **前端** | 完整 Web UI | 极简单页 🚧 | 大 |
| **可观测性** | 日志、Tracing、Token 统计 | ❌ | 大 |
| **沙盒执行** | 容器隔离 bash/代码 | subprocess 直跑 | 中 |
| **配置驱动** | YAML/JSON 全声明式 | 部分 ✅ | 中 |
| **部署** | Docker Compose | 裸机 uvicorn | 中 |

---

## 🗺️ 路线图

### Phase 1 — 基础框架（✅ 已完成）
- [x] LangGraph 图结构 + ReAct 循环
- [x] FastAPI + SSE 流式输出
- [x] SQLite Checkpoint 多轮记忆
- [x] 本地工具（@tool 装饰器）
- [x] MCP 工具（MultiServerMCPClient）

### Phase 2 — Skills（🚧 进行中）
- [ ] **Layer 1: Prompt 模板型 Skill**
  - [ ] skills.py 框架
  - [ ] code_helper Skill
  - [ ] calculator_expert Skill
  - [ ] 意图匹配 / 自动激活
- [ ] **Layer 2: 子图路由型 Skill**
  - [ ] 每个 Skill = 独立 LangGraph 子图
  - [ ] 主 Agent Router 根据意图路由
  - [ ] research Skill（搜索 → 整理 → 报告）
  - [ ] bash_helper Skill（命令 → 解释 → 建议）

### Phase 3 — 多 Agent（待开始）
- [ ] Lead Agent（主路由）
- [ ] Sub Agent 注册机制
- [ ] Agent 间委托与结果汇总
- [ ] 子 Agent 并行执行

### Phase 4 — 工程化（待开始）
- [ ] 中间件系统（Tool 拦截器、权限控制）
- [ ] 可观测性（Token 统计、Tool 调用日志）
- [ ] 沙盒执行（Docker 容器隔离 bash/代码）
- [ ] 前端完善（对话历史、工具可视化、Markdown 渲染）
- [ ] Docker 部署

---

## 🔧 技术栈

| 组件 | 版本 | 用途 |
|---|---|---|
| Python | 3.12 | 主语言 |
| LangChain | ≥1.3 | LLM 调用 + BaseTool |
| LangGraph | ≥1.2 | Agent 状态图编排 |
| LangChain-DeepSeek | ≥1.1 | DeepSeek 模型适配 |
| MCP | ≥1.30 | Model Context Protocol |
| langchain-mcp-adapters | ≥0.3 | MCP ↔ LangChain 桥接 |
| FastAPI | - | Web 框架 |
| Uvicorn | - | ASGI 服务器 |
| SQLite | - | Checkpoint 存储 |

---

## 📝 开发备忘

### 关键坑记录

| # | 问题 | 根因 | 修 |
|---|---|---|---|
| 1 | checkpoint 不恢复 | state reducer 用了字符串 `"add_messages"` | 改成函数引用 `add_messages` |
| 2 | MCP session 关闭后崩溃 | load_mcp_tools 闭包引用了已关闭 session | 用 MultiServerMCPClient（每次临时建 session） |
| 3 | git push 失败（大文件） | .gitignore 没配 | 加 `*.pdf *.db .env` |
| 4 | git push 失败（密钥） | .ipynb 里硬编码了 API Key | 删除文件 + amend commit |
| 5 | SSE 前端卡住 | 硬编码远程 IP（开发环境 OK） | - |

### MCP 连接池的真相

`MultiServerMCPClient` **不是真连接池**，每次调用工具时临时新建 session。工具闭包里存的是 `connection` 配置字典，不是 session 对象。这比手动 `__aenter__` 保持 session 存活更稳定（不会 ClosedResourceError）。

### 为什么不用真连接池

真连接池需要：
- 预建 N 个 session 放池里
- acquire() / release() 管理并发
- 空闲超时自动关闭
- 熔断/重连逻辑

当前阶段**稳定性 > 性能**，每次临时建 session 够用了。以后遇到性能瓶颈再优化。

---

## 许可证

MIT

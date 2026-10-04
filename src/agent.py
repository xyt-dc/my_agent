from state import AgentState
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
from langchain_mcp_adapters.tools import load_mcp_tools
import os


class Agent:
    def __init__(self, llm, db_path='agent.db'):
        self.llm = llm
        self.db_path = db_path
        self.tools = []
        self._mcp_connected = False

    async def _ensure_tools_loaded(self):
        if self._mcp_connected:
            return self.tools

        from local_tools import LOCAL_TOOLS
        self.tools.extend(LOCAL_TOOLS)

        server_params = StdioServerParameters(
            command='/root/my-agent/.venv/bin/python3',
            args=[os.path.join(os.path.dirname(__file__), 'mcp_server.py')]
        )
        # 不能用 async with！关了 session 工具就调不了了
        # 手动打开，让 MCP 连接活在整个 Agent 生命周期里
        self._mcp_ctx = stdio_client(server_params)
        self._mcp_read, self._mcp_write = await self._mcp_ctx.__aenter__()
        self._mcp_session = ClientSession(self._mcp_read, self._mcp_write)
        await self._mcp_session.__aenter__()
        await self._mcp_session.initialize()
        mcp_tools = await load_mcp_tools(self._mcp_session)
        self.tools.extend(mcp_tools)

        self._mcp_connected = True
        print(f"✅ 本地 + MCP 共 {len(self.tools)} 个工具")
        return self.tools

    async def ask(self, user_input: str, thread_id: str = "default"):
        await self._ensure_tools_loaded()

        async with AsyncSqliteSaver.from_conn_string(self.db_path) as memory_ctx:
            graph = StateGraph(AgentState)
            graph.add_node("chat", self._chat_node)
            graph.add_node("tools", ToolNode(self.tools))
            graph.add_edge(START, "chat")
            graph.add_conditional_edges("chat", tools_condition)
            graph.add_edge("tools", "chat")
            g = graph.compile(checkpointer=memory_ctx)

            config = {"configurable": {"thread_id": thread_id}}
            async for event in g.astream_events(
                input={"messages": [HumanMessage(content=user_input)]},
                config=config,
                version="v2",
            ):
                # yield from 在 async def 里不能用！改成手动 async for
                async for item in self._parse_event(event):
                    yield item

    async def _chat_node(self, state: AgentState) -> dict:
        messages = [
            SystemMessage(content="你是一个智能助手，可以使用工具来回答问题。"),
            *state["messages"]
        ]
        bound_llm = self.llm.bind_tools(self.tools)
        response = await bound_llm.ainvoke(messages)
        return {"messages": [response]}

    async def _parse_event(self, event):
        # v2 事件的 key 是 "event" 不是 "type"
        _event = event.get("event", "")
 
        if _event == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if chunk.content:
                yield {"type": "token", "content": chunk.content}
            if chunk.tool_calls:
                for tc in chunk.tool_calls:
                    yield {"type": "tool_call", "tool": tc["name"], "args": tc["args"]}

        elif _event == "on_tool_end":
            tool_name = event.get("name", "")
            result = event["data"].get("output", "")
            # ToolMessage.content 是 list[dict]，取里面的 text
            text_content = ""
            if hasattr(result, "content") and isinstance(result.content, list):
                for item in result.content:
                    if isinstance(item, dict) and "text" in item:
                        text_content += item["text"]
                # 去掉 MCP 返回的外层引号（datetime.now() 返回的字符串被 JSON 序列化了）
                text_content = text_content.strip('"')
            elif hasattr(result, "content"):
                text_content = str(result.content)
            else:
                text_content = str(result)
            yield {"type": "tool_result", "tool": tool_name, "result": text_content}

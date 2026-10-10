from state import AgentState
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.client import MultiServerMCPClient
import os
import json


class Agent:
    def __init__(self, llm, db_path='agent.db'):
        self.llm = llm
        self.db_path = db_path
        self.tools = []
        self._mcp_connected = False
        self.mcp_client = None

    async def _ensure_tools_loaded(self):
        if self._mcp_connected:
            return self.tools

        from local_tools import LOCAL_TOOLS
        self.tools.extend(LOCAL_TOOLS)

        config_path = os.path.join(os.path.dirname(__file__),'mcp_config.json')
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
            connections = {}
            for server in config['servers']:
                connections[server['name']] = {'command':server['command'],'args':server['args'],'transport':'stdio'}
        self._mcp_client = MultiServerMCPClient(connections)
        mcp_tools = await self._mcp_client.get_tools()
        print(f"🔌 MCP 发现 { len (mcp_tools)} 个工具")
        self.tools.extend(mcp_tools)
        self._mcp_connected = True
        return self.tools

    async def _load_mcp_tools_from_server(self,params:StdioServerParameters):
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as Session:
                await Session.initialize()
                mcp_tools = await load_mcp_tools(session=Session)
        return mcp_tools

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
            SystemMessage(content="""你现在是一个资深的求职规划分析师，你要基于用户的问题广泛搜索资料为用户分析方案可行性，当用户有列目录，看文件的需求时候，必须调用list_dir工具，当用户要你读文件内容时必须调用read_files，如果你不知道或者用户描述较为模糊就调用web工具搜一下，不要自己编造答案，有工具就用工具"""),
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
                    if tc.get("name"):
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

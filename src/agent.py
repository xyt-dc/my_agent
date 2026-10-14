from state import AgentState
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.types import interrupt, Command
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

    def review_condition(self,state:AgentState):
        last_msg = state['messages'][-1]
        if isinstance(last_msg,AIMessage) and last_msg.tool_calls:
            return 'Human_review'
        return END


    def _build_graph(self, memory_ctx):
        graph = StateGraph(AgentState)
        graph.add_node("chat", self._chat_node)
        graph.add_node("tools", ToolNode(self.tools))
        graph.add_node("Human_review", self.Human_review)
        graph.add_edge(START, "chat")
        graph.add_conditional_edges("chat", self.review_condition, {
            "Human_review": "Human_review",
            END: END,
        })
        graph.add_edge("Human_review", "tools")
        graph.add_edge("tools", "chat")
        return graph.compile(checkpointer=memory_ctx)

    async def ask(self, user_input: str, thread_id: str = "default"):
        await self._ensure_tools_loaded()

        async with AsyncSqliteSaver.from_conn_string(self.db_path) as memory_ctx:
            g = self._build_graph(memory_ctx)
            config = {"configurable": {"thread_id": thread_id}}
            async for event in g.astream_events(
                input={"messages": [HumanMessage(content=user_input)]},
                config=config,
                version="v2",
            ):                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
                # yield from 在 async def 里不能用！改成手动 async for
                async for item in self._parse_event(event):
                    yield item
            state = await g.aget_state(config)
            if state.tasks and getattr(state.tasks[0], "interrupts", None):
                yield { "type" : "interrupt" , "data" : state.tasks[ 0 ].interrupts[ 0 ].value}
            yield { "type" : "done" , "content" : {}} # 一个流程走完

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

    def Human_review(self,state:AgentState):
        last_msg = state['messages'][-1]
        #print(last_msg,flush = True)
        call_summary = []
        count = len(last_msg.tool_calls)
        for tc in last_msg.tool_calls:
            call_summary.append({'tool_name': tc['name'], 'tool_arg': tc['args']})
        decision = interrupt({
            'type': "tool_approval",
            "count": count,
            "calls": call_summary,
            "question": f"Agent 想调用{count}个工具，是否继续？",
            "options": ["approve", "refuse", "skip"],
        })
        print(f"[Human_review] decision={decision}", flush=True)
        return {"messages": [last_msg]}

    async def resume(self, data, thread_id: str = "default"):
        await self._ensure_tools_loaded()
        async with AsyncSqliteSaver.from_conn_string(self.db_path) as memory_ctx:
            g = self._build_graph(memory_ctx)
            config = {"configurable": {"thread_id": thread_id}}
            # ⭐ 区别 1：input 是 Command(resume=...)，不是 HumanMessage
            async for event in g.astream_events(
                input=Command(resume=data),
                config=config,
                version="v2",
            ):
                async for item in self._parse_event(event):
                    yield item
            # ⭐ 区别 2：结束后查一次有没有"第二次" interrupt
            state = await g.aget_state(config)
            if state.tasks and state.tasks[0].interrupts:
                yield {"type": "interrupt", "data": state.tasks[0].interrupts[0].value}
            yield {"type": "done", "content": {}}


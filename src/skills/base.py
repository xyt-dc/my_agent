"""
Skill 基类 — 定义每个 Skill 必须实现的接口

DeerFlow 的每个 Skill 本质上就是一个"专精子 Agent"：
  - 有自己的 System Prompt（决定"人格"和行为规则）
  - 有自己的工具名列表（运行时由 Agent 从全局工具中注入匹配的工具对象）
  - 有自己的 LangGraph 子图（可以是 chat→tools→chat 循环，也可以是纯 chat）
"""
from typing import Optional
from langgraph.graph import StateGraph, CompiledStateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage


class Skill:
    """Skill 基类 — 子类只需定义 name/description/system_prompt/wanted_tool_names"""
    
    name: str = ""                       # "web_researcher"
    description: str = ""                # Router 用来选择的描述
    system_prompt: str = ""              # 专属 System Prompt
    wanted_tool_names: list[str] = []    # 想要哪些工具的名字（运行时注入）
    
    def __init__(self):
        self.tools: list = []            # 运行时注入的实际工具对象
    
    def set_tools(self, all_tools: list):
        """从全局工具列表中，按 wanted_tool_names 过滤出属于本 Skill 的工具"""
        if not self.wanted_tool_names:
            self.tools = []
            return
        self.tools = [t for t in all_tools if getattr(t, "name", None) in self.wanted_tool_names]
        print(f"🔧 [{self.name}] 匹配到 {len(self.tools)} 个工具: {[t.name for t in self.tools]}")
    
    def build_graph(self, llm, state_class) -> CompiledStateGraph:
        """
        构建这个 Skill 的 LangGraph 子图。
        
        默认实现：
          有工具 → chat ↔ tools 循环
          无工具 → chat → END
        """
        graph = StateGraph(state_class)
        
        async def chat_node(state):
            messages = [
                SystemMessage(content=self.system_prompt),
                *state["messages"]
            ]
            bound_llm = llm.bind_tools(self.tools) if self.tools else llm
            response = await bound_llm.ainvoke(messages)
            return {"messages": [response]}
        
        graph.add_node("chat", chat_node)
        
        if self.tools:
            graph.add_node("tools", ToolNode(self.tools))
            graph.add_edge("tools", "chat")
            graph.add_conditional_edges("chat", tools_condition)
        else:
            graph.add_edge("chat", END)
        
        graph.set_entry_point("chat")
        return graph.compile()
    
    def __repr__(self):
        return f"<Skill: {self.name}>"

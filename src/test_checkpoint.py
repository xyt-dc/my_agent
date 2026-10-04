"""测试不同 reducer + 返回写法组合"""
from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict, Annotated
from operator import add
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages  # LangGraph 官方的 messages reducer
from llm import get_llm

llm = get_llm()


def test_variant(state_class, node_fn, label):
    print(f"\n{'='*60}")
    print(f"测试: {label}")
    print(f"{'='*60}")

    thread_id = f"variant_{label}"
    config = {"configurable": {"thread_id": thread_id}}

    # 进程 1：写入
    print("\n进程 1: 写入")
    with SqliteSaver.from_conn_string("agent.db") as saver:
        g = StateGraph(state_class)
        g.add_node("chat", node_fn)
        g.add_edge(START, "chat")
        g.add_edge("chat", END)
        compiled = g.compile(checkpointer=saver)

        compiled.invoke(
            {"messages": [HumanMessage(content="我叫小明")]},
            config=config,
        )
        snap = compiled.get_state(config)
        print(f"  checkpoint 存了 {len(snap.values['messages'])} 条")

    # 进程 2：续聊
    print("进程 2: 续聊")
    with SqliteSaver.from_conn_string("agent.db") as saver2:
        g2 = StateGraph(state_class)
        g2.add_node("chat", node_fn)
        g2.add_edge(START, "chat")
        g2.add_edge("chat", END)
        compiled2 = g2.compile(checkpointer=saver2)

        snap_before = compiled2.get_state(config)
        print(f"  续聊前 checkpoint 有 {len(snap_before.values['messages'])} 条")

        r = compiled2.invoke(
            {"messages": [HumanMessage(content="我刚才说我叫啥？")]},
            config=config,
        )
        print(f"  模型回复: {r['messages'][-1].content[:100]}")


# ---------- 变体 1: reducer="add" + 节点只返回新回复 ----------
class StateV1(TypedDict):
    messages: Annotated[list[AnyMessage], "add"]

def node_v1(state):
    msgs = [SystemMessage(content="你是乐于助人的助手"), *state["messages"]]
    print(f"    节点收到 {len(state['messages'])} 条 state")
    resp = llm.invoke(msgs)
    return {"messages": [resp]}


# ---------- 变体 2: reducer="add" + 节点返回完整历史 ----------
class StateV2(TypedDict):
    messages: Annotated[list[AnyMessage], "add"]

def node_v2(state):
    msgs = [SystemMessage(content="你是乐于助人的助手"), *state["messages"]]
    print(f"    节点收到 {len(state['messages'])} 条 state")
    resp = llm.invoke(msgs)
    return {"messages": [*state["messages"], resp]}


# ---------- 变体 3: reducer=add_messages (LangGraph 官方) + 节点只返回新回复 ----------
class StateV3(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def node_v3(state):
    msgs = [SystemMessage(content="你是乐于助人的助手"), *state["messages"]]
    print(f"    节点收到 {len(state['messages'])} 条 state")
    resp = llm.invoke(msgs)
    return {"messages": [resp]}


import os
if os.path.exists("agent.db"):
    os.remove("agent.db")

test_variant(StateV1, node_v1, 'v1_add_reducer_only_new')
if os.path.exists("agent.db"):
    os.remove("agent.db")

test_variant(StateV2, node_v2, 'v2_add_reducer_full_history')
if os.path.exists("agent.db"):
    os.remove("agent.db")

test_variant(StateV3, node_v3, 'v3_add_messages_only_new')

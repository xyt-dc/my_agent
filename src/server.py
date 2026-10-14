from dotenv import load_dotenv
load_dotenv()

import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

from llm import get_llm
from agent import Agent


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时就连接 MCP，跟应用同生命周期
    global agent_obj
    agent_obj = Agent(get_llm())
    await agent_obj._ensure_tools_loaded()
    print("✅ Agent + MCP 初始化完成，服务就绪")
    yield
    # 关闭时清理（可选）
    print("👋 服务关闭")


app = FastAPI(title="My Agent", lifespan=lifespan)
agent_obj = None


async def chat_stream(request: ChatRequest):
    async def event_generator():
        try:
            async for _ask in agent_obj.ask(request.message, request.thread_id):
                if _ask["type"] == "token":
                    yield f"event: token\ndata: {json.dumps({'type':'token','content':_ask['content']})}\n\n"
                elif _ask["type"] == "tool_call":
                    yield f"event: tool_call\ndata: {json.dumps({'type':'tool_call','tool':_ask['tool'],'args':_ask['args']})}\n\n"
                elif _ask["type"] == "tool_result":
                    yield f"event: tool_result\ndata: {json.dumps({'type':'tool_result','tool':_ask['tool'],'result':_ask['result']})}\n\n"
                elif _ask["type"] == "interrupt":
                    yield f"event: interrupt\ndata: {json.dumps(_ask)}\n\n"
                elif _ask["type"] == "done":
                    continue  # 结束时统一在下面发 done，避免重复

            yield f"event: done\ndata: {json.dumps({})}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return await chat_stream(request)


class ResumeRequest(BaseModel):
    thread_id: str = "default"
    data: object = "approve"


@app.post("/resume")
async def resume_endpoint(request: ResumeRequest):
    async def event_generator():
        try:
            async for item in agent_obj.resume(request.data, request.thread_id):
                if item["type"] in ("token", "tool_call", "tool_result", "interrupt"):
                    yield f"event: {item['type']}\ndata: {json.dumps(item)}\n\n"
            yield f"event: done\ndata: {json.dumps({})}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")


app.mount("/", StaticFiles(directory=".", html=True), name="static")

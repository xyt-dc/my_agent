from langchain.agents.middleware import AgentMiddleware,ModelRequest,ModelResponse
class LoggingMiddleware(AgentMiddleware):
    def wrap_model_call(self, request, handler):
        print(f"📝 LLM 调用：{len(request.messages)} 条消息")
        response = handler(request)
        print(f"✅ LLM 返回：{len(response.message.content)} 字")
        return response

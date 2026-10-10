import os

from langchain_deepseek import ChatDeepSeek
def  get_llm():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key is None:
        raise RuntimeError("api_key is not accessible")
    model = os.getenv("DEEPSEEK_MODEL")
    
    return ChatDeepSeek(model=os.getenv("DEEPSEEK_MODEL","deepseek-chat"),
        api_key=api_key,
        temperature = os.getenv("DEEPSEEK_TEMPERATURE","0.9")
    )


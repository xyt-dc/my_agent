"""Skill 1: 通用对话 — 不使用任何工具"""
from skills.base import Skill


class GeneralChatSkill(Skill):
    name = "general_chat"
    description = "当用户只是想聊天、打招呼、讲笑话、闲聊时用这个 skill。"
    
    system_prompt = """你是一个友好、幽默的 AI 助手。
你擅长闲聊、讲笑话、聊人生、回答常识问题。
**重要：不要调用任何工具**，直接用自己的知识回答就好。
保持回答简洁有趣，语气像朋友一样。"""
    
    tools = []  # 空的！不绑任何工具，Router 选中后 chat_node 不会 bind_tools

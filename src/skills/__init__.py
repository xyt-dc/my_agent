"""
Skills Layer 2 — DeerFlow 风格子图路由

每个 Skill 是一个独立的 LangGraph 子图，主 Agent 通过 Router 节点
根据用户意图把对话路由到对应的 Skill 处理。
"""
from .base import Skill
from .general_chat import GeneralChatSkill
from .web_researcher import WebResearcherSkill
from .code_helper import CodeHelperSkill

__all__ = [
    "Skill",
    "GeneralChatSkill",
    "WebResearcherSkill", 
    "CodeHelperSkill",
    "ALL_SKILLS",
]

# 🎯 注册表：所有 Skill 实例
ALL_SKILLS = [
    GeneralChatSkill(),
    WebResearcherSkill(),
    CodeHelperSkill(),
]

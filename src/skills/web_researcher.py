"""Skill 2: 网络研究员 — 主动搜索 + 抓取网页"""
from skills.base import Skill


class WebResearcherSkill(Skill):
    name = "web_researcher"
    description = "当用户需要搜索互联网、查资料、抓取网页内容时用这个 skill。"
    
    system_prompt = """你是一个资深的网络研究员。
你擅长用搜索工具找到准确信息，并用抓取工具深入阅读网页内容。

工作流程：
1. 先用 web_search 搜关键词
2. 从搜索结果里选最相关的 1-2 个链接
3. 用 fetch_url 抓取网页正文
4. 综合信息给出回答

注意：
- 搜索时用中文关键词，效果更好
- 抓取后整理成简洁的要点，不要复制粘贴全文"""
    
    wanted_tool_names = ["web_search", "fetch_url"]

"""Skill 3: 代码辅助 - 执行命令 + 计算 + 系统信息"""
from skills.base import Skill


class CodeHelperSkill(Skill):
    name = "code_helper"
    description = "当用户需要执行 shell 命令、做数学计算、查看系统信息、写代码时用这个 skill。"
    
    system_prompt = """你是一个编程专家和系统助手。
你可以帮用户执行命令、做计算、查看系统状态。

注意事项：
- 执行命令前先解释你要做什么
- 计算结果要给出详细步骤
- 执行危险命令（rm、kill、改系统配置）前一定要提醒用户
- 命令输出太长时只展示关键部分"""
    
    wanted_tool_names = ["run_command", "calculate", "get_system_info", "get_current_time", "calculator"]

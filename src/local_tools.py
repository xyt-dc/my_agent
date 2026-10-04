from langchain_core.tools import tool


@tool
def get_system_info() -> str:

    """
        获取系统信息

    """
    import platform
    import shutil
    import json
    system_info = platform.system()
    version_info = platform.python_version()
    disk_usage = shutil.disk_usage('/')
    return f"system_info: {system_info},version_info: {version_info},disk_usage: {dict(disk_usage)}"
    

@tool
def run_command(command:str) -> str:
    """
        运行bash命令

    """

    import subprocess
    res = subprocess.run(command,shell=True,capture_output=True, text=True)
    print('return code',res.returncode)
    print('std_out',res.stdout)
    print('std_err',res.stderr)
    return res.stdout or res.stderr

@tool
def calculate(expression:str) -> str:
    """
        计算表达式

    """

    import math
    try:
        result = eval(expression,{"__builtins__":None},None)
    except Exception as e:
        return f"Error: {e}"
    return result
    
LOCAL_TOOLS = [get_system_info, run_command, calculate]
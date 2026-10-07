from langchain_core.tools import tool


@tool
def get_system_info() -> str:
    """获取系统信息"""
    import platform
    import shutil
    import json
    system_info = platform.system()
    version_info = platform.python_version()
    disk_usage = shutil.disk_usage('/')
    return f"system_info: {system_info},version_info: {version_info},disk_usage: {dict(disk_usage)}"
    

@tool
def run_command(command:str) -> str:
    """运行bash命令"""
    import subprocess
    res = subprocess.run(command,shell=True,capture_output=True, text=True)
    print('return code',res.returncode)
    print('std_out',res.stdout)
    print('std_err',res.stderr)
    return res.stdout or res.stderr

@tool
def calculate(expression:str) -> str:
    """计算表达式 """
    import math
    try:
        result = eval(expression,{"__builtins__":None},None)
    except Exception as e:
        return f"Error: {e}"
    return result

@tool
def list_dir(path:str)->str:
    """ 列出当前目录下的所有文件夹和文件，并按照树结构返回"""
    import os
    path_dir = ""
    try:
        entries = os.listdir(path=path)
        if not entries:
            return ""
        for name in entries:
            full_name = os.path.join(path,name)
            if os.path.isdir(full_name):
                path_dir += "📁"+full_name + "\n"
                next_name = list_dir(full_name)
                path_dir += next_name + "\n"
            else:
                path_dir += "📃"+name + "\n"
        return path_dir  
    except Exception as e:
        return str(e)

@tool
def read_files(path:str,Max_File_Size:int=1024*1024*10,Max_char:int=200)->str:
    """读文件时调用这个工具，返回文件内容，这里path是文件的路径，Max_File_Size是最大文件大小，Max_char是最大返回字符数"""
    import os
    try:
        m_size = os.path.getsize(path)
        if (m_size > Max_File_Size):
            return "文件大小超过最大限制"
        with open(path,"r",encoding="utf-8") as f:
            content = f.read()
            if not content:
                return f"⚠️ 文件为空: {path} "
            elif len(content) > Max_char:
                content = content[:Max_char>>1] + "..."+content[-Max_char>>1:]
            return f"📋{path}阅读完毕👌,({m_size}bytes):\n{content}"
    except FileNotExistError as e:
        return f"❌阅读失败:\n{str(e)}\n"
    
LOCAL_TOOLS = [get_system_info, run_command, calculate]
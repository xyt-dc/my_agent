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
def res_listdir(path:str)->str:
    """ 列出当前目录下的所有文件夹和文件，并按照树结构返回，当prompt里有让你列出/帮我看看/查一下/去到某个目录下的所有文件时你要调用这个函数，将函数的返回值原封不动的回复给客服"""
    return list_dir(path=path)

def list_dir(path:str)->str:
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
    except Exception as e:
        return f"❌阅读失败:\n{str(e)}\n"
@tool 
def write_files(path:str,content:str)->str:
    """写文件时调用这个工具，将文件内容写入文件，这里path是文件的路径，content是文件内容"""
    import os
    try:
        with open(path,"w",encoding="utf-8") as f:
            f.write(content)
        return f"✅{path}写入成功👌"
    except Exception as e:
        return f"❌写入失败:\n{str(e)}\n"

@tool
def get_weather(city:str)->str:
    """获取城市的天气信息，当用户问你今天天气情况如何时优先调用这个工具，将用户需要的信息返还给用户，
    用户：{city}的天气情况信息
    回复：{city}的当前摄氏温度
    用户：{city}的华氏温度
    回复：{city}的当前华氏温度
    用户：给我完整的天气信息
    回复要把所有信息都返还给用户
    """
    import httpx
    import json
    url = f"https://wttr.in/{city}?format=j1"
    try:
        resp = httpx.get(url,timeout=10,headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"})
        data = resp.json()
        
        current_weater = data['current_condition'][0]
        FeelslikeC = current_weater['FeelsLikeC']
        FeelslikeF = current_weater['FeelsLikeF']
        cloudcover = current_weater['cloudcover']
        humidity = current_weater['humidity']
        observation_time = current_weater['observation_time']
        precipInces = current_weater['precipInches']
        precipMM = current_weater['precipMM']
        pressure = current_weater['pressure']
        precipInces = current_weater['precipInches']
        temp_c = current_weater['temp_C']
        temp_f = current_weater['temp_F']
        uvIndex = current_weater['uvIndex']

        result = { "FeelsLikeC" : current_weater[ "FeelsLikeC" ], 
                    "FeelsLikeF" : current_weater[ "FeelsLikeF" ], 
                    "cloudcover" : current_weater[ "cloudcover" ], 
                    "humidity" : current_weater[ "humidity" ], 
                    "observation_time" : current_weater[ "observation_time" ], 
                    "precipInches" : current_weater[ "precipInches" ], 
                    "precipMM" : current_weater[ "precipMM" ], 
                    "pressure" : current_weater[ "pressure" ], 
                    "precipInches" : current_weater[ "precipInches" ], 
                    "temp_C" : current_weater[ "temp_C" ], 
                    "temp_F" : current_weater[ "temp_F" ], 
                    "uvIndex" : current_weater[ "uvIndex" ],
        }
        return result

    except Exception as e:
        return f"❌获取天气失败:\n{str(e)}\n"
        
    
LOCAL_TOOLS = [get_system_info, run_command, calculate,res_listdir,read_files,get_weather,write_files]
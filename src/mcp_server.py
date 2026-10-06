from mcp.server.fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("我的工具服务器")

@mcp.tool()
def get_current_time() -> str:
    """只要问题中有时间这个词，就调用这个工具，返回当前时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@mcp.tool()
def calculator(expression: str) -> str:
    """计算数学表达式，比如 '2 + 3 * 4'"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")

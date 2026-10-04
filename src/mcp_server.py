from mcp.server.fastmcp import FastMCP

mcp = FastMCP("我的工具服务器")




if __name__ == "__main__":
    mcp.run(transport="stdio")

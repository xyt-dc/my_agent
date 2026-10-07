from mcp.server.fastmcp import FastMCP
from ddgs import DDGS

mcp = FastMCP(name='网页搜索与网页内容爬取工具')
@mcp.tool()
def web_search(query:str) -> str:
    """搜索互联网,返回标题、链接和摘要，参数query为搜索关键词"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query))
        if not results:
            return "没有搜索到相关结果"
        output = []
        for i,r in enumerate(results):
            title = r.get('title','无标题')
            href = r.get('href','')
            body = r.get('body','')
            output.append(f"{i}. {title}\n {href}\n {body}\n\n")
        print("🔎搜索成功")
        return "\n".join(output)
    except Exception as e:
        return f"🔍搜索失败: {e}"

@mcp.tool()
def fetch_url(url:str)->str:
    """获取URL中的文字内容，参数url为URL地址"""
    import httpx
    from bs4 import BeautifulSoup
    try:
        resp = httpx.get(url,timeout=10,follow_redirects=True,headers={'User-Agent':'Mozilla/5.0 (Linux; Android 10; ...) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text,'html.parser')
        for tag in soup.find_all(['script','style','nav','footer']):
            tag.decompose()
        text = "\n" .join(
            line.strip() for line in soup.get_text().split( "\n" ) if line.strip())
        #text = soup.get_text()
        return text
    except Exception as e:
        return f"🔍获取URL失败: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
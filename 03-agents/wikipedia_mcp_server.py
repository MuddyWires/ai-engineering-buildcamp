from fastmcp import FastMCP
from wikipediaTools import WikipediaTools

mcp=FastMCP("Wikipedia Tools")
wiki=WikipediaTools()

@mcp.tool
def search_wikipedia(query:str) ->list[dict]:
    """Search wikipedia for results matching a query."""
    return wiki.search_wikipedia(query)  

@mcp.tool
def get_page(pagetitle:str)->str:
    """Get the content of a wikipedia page."""
    return wiki.get_page(pagetitle)

if __name__=="__main__":
    mcp.run()
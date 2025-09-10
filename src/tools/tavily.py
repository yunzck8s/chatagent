from langchain_community.tools.tavily_search import TavilySearchResults
import os
os.environ["TAVILY_API_KEY"] = "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"

def get_tavily_tool():
    """初始化并返回 Tavily 搜索工具"""
    return TavilySearchResults()
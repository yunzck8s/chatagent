from langchain_community.tools.tavily_search import TavilySearchResults
import os

tavily_api_key = os.getenv("TAVILY_API_KEY", "default_api_key_if_not_found")


def get_tavily_tool():
    """初始化并返回 Tavily 搜索工具"""
    return TavilySearchResults()
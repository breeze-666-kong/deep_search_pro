import os

from tavily import TavilyClient
from dotenv import  load_dotenv,find_dotenv
from typing import Literal
from langchain.tools import tool

from api.monitor import monitor

load_dotenv(find_dotenv())
#步骤一定义一个tavily对象
tavily_client= TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


#步骤二定义网络搜索工具
@tool
def internet_search(query: str,
                    topic:Literal["news","finance","general"]="general",
                    max_results:int=5,
                    include_links:bool=False):
    """
    根据用户问题，进行网络信息收！
    注意：主要搜索公开的网络信息！如果指定查询数据库或者rag不能使用此工具！
    :param query:用户的查询信息
    :param topic:查询的类型
    :param max_results:返回的最大条数
    :param include_links:是否返回原内容 False 精简 True 详细
    :return:
    """
    #monitor用于在工具执行过程中上报进度和状态信息。
    monitor.report_tool(tool_name="网络搜索工具",args={"query":query,
                                                    "topic":topic,
                                                    "max_results":max_results,
                                                    "include_links":include_links})
    return tavily_client.search(query=query,topic=topic,max_results=max_results,include_links=include_links)




















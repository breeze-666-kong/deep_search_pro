import os

from ragflow_sdk import RAGFlow

from api.monitor import monitor
from ragflow.rag_config import _load_ragflow_env
from langchain.tools import tool
from dotenv import load_dotenv,find_dotenv

load_dotenv(find_dotenv())

api_key,base_url = _load_ragflow_env()
ragflow_client= RAGFlow(api_key=api_key,base_url=base_url)



@tool
def get_assisatant_list():
    """
    调用此工具，可以查询ragflow服务器中有哪些助手和助手关联的知识库信息！
    供模型参考，可以从哪个助手获取对应的内部文档信息！
    强调：想向某个助手提问，必须想要调用此工具查询助手的信息和名称
    返回结果： 有-> 名称:助手名称,助手描述：xxxx,关联的知识库：知识库的名、知识库的名字、
             没有 -> 没有任何可用助手
             异常 -> 查询助手信息异常，无可用助手
    :return:
    """
# 埋点,调用工具了告诉前端哪个工具被调用了！！
    monitor.report_tool(tool_name="ragflow聊天助手列表查询工具：get_assistant_list")


    #创建客户端
    try:
        chat_list= ragflow_client.list_chats()
        if not chat_list:
            return "没有任何可用助手"
        count_chat_info = ""
        for chat in chat_list:
            dataset_names = []
            dataset_list = chat.datasets
            if dataset_list and isinstance(dataset_list,list):
                for dataset in dataset_list:
                    dataset_names.append(dataset.name)
            count_chat_info += f"名称:{chat.name},助手描述：{chat.description},关联的知识库：{'、'.join(dataset_names)}\n"
    except Exception as e:
        return f"查询助手信息异常，无可用助手,异常信息:{str(e)}"


@tool
def create_ask_delete(chat_name,question)->str:
    """
    想某个助手，创建单次会话进行提问，提问完毕以后会关闭会话！
    主要查询ragflow中相关的信息！
    注意：调用此工具之前，必须先调用 get_assistant_list工具明确查询助手的名字和对应的问题
    :param chat_name: 助手的名字！上一个工具get_assistant_list告诉大模型的只有名字
    :param question: 本次提问的问题
    :return: 返回提问的结果
    """
    # 埋点,调用工具了告诉前端哪个工具被调用了！！
    monitor.report_tool(tool_name="ragflow提问助手工具：create_ask_delete",
                        args={"chat_name": chat_name, "question": question})
    try:
        chats= ragflow_client.list_chats(name=chat_name)
        use_chat= chats[0]
        session = use_chat.create_session(name="temp_session_ask")
        response= session.ask(question = question,stream=True)
        # 接收总结果
        result=""
        for chunk in response:
            # 数据存在对象中content上！！
            result= chunk.content
        #关闭对话
        use_chat.delete_sessions(ids=[session.id])
        return result

    except Exception as e:
        return f"提问失败，错误原因：{str(e)}"
























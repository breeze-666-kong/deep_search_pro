import os

from ragflow_sdk import RAGFlow

from api.monitor import monitor
from core.logger import get_logger
from ragflow.rag_config import _load_ragflow_env
from langchain.tools import tool
from dotenv import load_dotenv,find_dotenv

logger = get_logger("ragflow_tools")

load_dotenv(find_dotenv())

api_key,base_url = _load_ragflow_env()
ragflow_client= RAGFlow(api_key=api_key,base_url=base_url)


def _get_dataset_name(dataset):
    """
    安全获取数据集名称，兼容对象和字典两种格式
    :param dataset: RAGFlow返回的数据集对象或字典
    :return: 数据集名称字符串
    """
    try:
        if isinstance(dataset, dict):
            return dataset.get('name', '未知知识库')
        else:
            return getattr(dataset, 'name', '未知知识库')
    except Exception:
        return '未知知识库'



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

    logger.info(f"开始查询RAGFlow助手列表，服务地址: {base_url}")

    #创建客户端
    try:
        chat_list= ragflow_client.list_chats()
        if not chat_list:
            logger.warning("RAGFlow返回空助手列表")
            return "没有任何可用助手"
        
        logger.info(f"成功获取{len(chat_list)}个助手")
        count_chat_info = ""
        for chat_idx, chat in enumerate(chat_list):
            try:
                logger.debug(f"处理助手[{chat_idx}]: 类型={type(chat)}, 内容={chat}")
                
                dataset_names = []
                dataset_list = chat.datasets
                
                logger.debug(f"助手[{chat_idx}] datasets类型={type(dataset_list)}, 内容={dataset_list}")
                
                if dataset_list and isinstance(dataset_list, list):
                    for idx, dataset in enumerate(dataset_list):
                        logger.debug(f"数据集[{idx}] 类型={type(dataset)}, 内容={dataset}")
                        name = _get_dataset_name(dataset)
                        dataset_names.append(name)
                
                chat_name = getattr(chat, 'name', f'未知助手{chat_idx}')
                chat_desc = getattr(chat, 'description', '无描述')
                
                count_chat_info += f"名称:{chat_name},助手描述：{chat_desc},关联的知识库：{'、'.join(dataset_names)}\n"
                logger.debug(f"助手[{chat_idx}] 信息拼接完成")
                
            except Exception as inner_e:
                logger.error(f"处理助手[{chat_idx}]时出错: {type(inner_e).__name__} - {str(inner_e)}", exc_info=True)
                continue
        
        logger.info(f"助手列表构建完成:\n{count_chat_info}")
        return count_chat_info
        
    except Exception as e:
        logger.error(f"查询RAGFlow助手列表失败: {type(e).__name__} - {str(e)}", exc_info=True)
        return f"查询助手信息异常，无可用助手,异常类型:{type(e).__name__},异常信息:{str(e)}"


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
    
    logger.info(f"开始向RAGFlow助手 '{chat_name}' 提问: {question}")
    
    try:
        chats= ragflow_client.list_chats(name=chat_name)
        if not chats:
            logger.error(f"未找到名为 '{chat_name}' 的助手")
            return f"提问失败，错误原因：未找到名为 '{chat_name}' 的助手"
            
        use_chat= chats[0]
        logger.info(f"找到助手，ID={getattr(use_chat, 'id', 'unknown')}，创建临时会话")
        
        session = use_chat.create_session(name="temp_session_ask")
        logger.info(f"会话创建成功，ID: {session.id}，开始提问...")
        
        response= session.ask(question = question,stream=True)
        result=""
        for chunk in response:
            result= chunk.content
        
        logger.info(f"收到回复，长度: {len(result)} 字符")
        
        use_chat.delete_sessions(ids=[session.id])
        logger.info(f"会话已关闭")
        
        return result

    except Exception as e:
        logger.error(f"向RAGFlow助手 '{chat_name}' 提问失败: {type(e).__name__} - {str(e)}", exc_info=True)
        return f"提问失败，错误原因：{type(e).__name__}: {str(e)}"
























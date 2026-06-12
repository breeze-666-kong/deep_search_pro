from agent.subagents.knowledge_search_agent import knowledge_base_agent
from agent.subagents.database_query_agent import database_query_agent
from agent.subagents.network_search_agent import network_search_agent
from langgraph.checkpoint.memory import InMemorySaver
from deepagents import create_deep_agent
# main_agent tool导入
from tools.markdown_tools import generate_markdown
from tools.pdf_tools import convert_md_to_pdf
from tools.upload_file_read_tool import read_file_content
from agent.llm import llm
from agent.prompts import main_agent_content

from api.monitor import monitor
import asyncio
import uuid
import shutil
from pathlib import Path

from api.context import set_session_context, reset_session_context, set_thread_context

from langchain_core.messages import AIMessage

main_agent = create_deep_agent(
   model = llm,
   system_prompt=main_agent_content['system_prompt'],
   tools= [generate_markdown,convert_md_to_pdf,read_file_content],
   checkpointer=InMemorySaver(),
   subagents=[
       database_query_agent,
       network_search_agent,
       knowledge_base_agent
   ]
)

# 执行
"""
  1. 执行主智能体 一定选异步，原因：对应多个客户端
  2. 什么时候触发我们智能体的调用或者执行？？？
  3. 客户端 -》 api/task -> fastapi 接口 -》 异步执行 -》 main_agent的运行 （异步方法）
  4. main_agent执行stream流式处理 -》 调用工具 -》 已经埋好了点  
                                   调用子智能体 -》 结果解析 -》 name = task -> monitor -> 发送子智能体
                                   调用最终结果 -》 结果 -》 monitor -> 发送结果的方法
                                   开启调用以后 -》 当前会话 -》 文件夹地址 -》 推送到前端
"""

project_root_path = Path(__file__).parents[1].resolve()#绝对路径,会解析符号链接

async def run_deep_agent(task_query,session_id):
    """
    定义流式+异步执行主智能体！！
    执行过程中，返回  会话文件化返回  调用子智能体  调用最终结果 （monitor）
    :param task_query:前端返回提出的问题
    :param session_id:本次会话的id
    :return:
    """
    print(f"当前会话的main_agent开始执行,会话id{session_id}")
    #1.生成当前会话存储的文件夹
    session_dir=project_root_path/"output"/f"session_{session_id}"
    #创建会话文件夹,parents的含义是创建父文件夹,exist_ok是允许存在
    session_dir.mkdir(parents=True,exist_ok=True)
    #防止转义字符识别错误的麻烦
    session_dir_str= str(session_dir).replace("\\","/")
    #获取相对文件夹
    relative_session_dir_str=str(session_dir.relative_to(project_root_path)).replace("\\","/")
    #处理上传文件
    updated_dir_path= project_root_path/"updated"/f"session_{session_id}"
    #上传文件，拼接上传文件专属解析位置的提示词
    updated_info_prompt= ""
    if updated_dir_path.exists() :
        files= [file.name for file in updated_dir_path.iterdir() if file.is_file()]
        if files :
            for file in files:
                shutil.copy2(updated_dir_path/file,session_dir/file)
            updated_info_prompt = (f"\n    [已上传文件] 已加载到工作目录:\n" +
                               "\n".join([f"    - {f}" for f in files]) +
                               "\n    请优先使用工具（read_file_content）读取并参考这些文件。")
    session_dir_token = set_session_context(session_dir_str)  # 存储的当前会话对应的文件夹地址
    session_id_token = set_thread_context(session_id)  # 获取当前会话的session_id对应socket

    monitor.report_session_dir(session_dir_str)  # 当前会话对应的文件夹地址推送给起前端！

    #执行main_agent
    config={
        "configurable":{
            "thread_id":session_id
        }
    }
    # 构建提示词
    path_instruction = f"""
        【工作环境指令】
        工作目录: {relative_session_dir_str}
        {updated_info_prompt}

        规则：
        1. 新生成文件必须保存到工作目录：'{relative_session_dir_str}/filename'
        2. 读取已上传的文件时，请直接将文件名（例如：'开篇.txt'）作为 filename 参数传入（read_file_content）读取工具，不要带上任何目录前缀。
        3. 使用相对路径，禁止使用绝对路径
        4. 若存在上传文件，请先分析内容
        """
    # 反馈结果

    try:
        """
        正常使用流式输出时有四种情况,model(三种:大模型决定调用工具,调用子智能体,返回结果)|tools(一种调用工具)
        本次执行中工具在写代码时已经monitor回去了所以不用写,这里只有model->返回结果和掉子智能体
        """
        #执行
        async for chunk in main_agent.astream({
            "messages":[{
                "role":"user","content":task_query+path_instruction
            }]
        },config=config):
            for node_name,state in chunk.items():
                if not state or "messages" not in state:continue
                messages= state["messages"]
                if messages and isinstance(messages,list):
                    last_msg= messages[-1]
                    #返回结果
                    if last_msg.content:
                        print(f"主智能体返回结果:{last_msg.content}")
                        monitor.report_task_result(last_msg.content)
                    #调子智能体
                    elif last_msg.tool_calls:
                        for tool_call in last_msg.tool_calls:
                            if tool_call["name"]=="task":
                                monitor.report_assistant(tool_call['args']['subagent_type'],{'description': tool_call['args']['description']})
    except Exception as e :
        monitor._emit("error",f"执行主智能发生异常信息：{str(e)}")
    finally:
        reset_session_context(session_dir_token,session_id_token)


























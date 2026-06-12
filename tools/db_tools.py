import os
from dotenv import load_dotenv, find_dotenv
from api.monitor import monitor
from mysql.connector import connect, Error
from langchain_core.tools import tool

load_dotenv(find_dotenv())

def get_db_config():
    """
    从环境中获得数据库配置
    :return:
    """
    config= {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
        "collation": os.getenv("MYSQL_COLLATION", "utf8mb4_unicode_ci"),
        "autocommit": True,
        "sql_mode": os.getenv("MYSQL_SQL_MODE", "TRADITIONAL")
    }
    #筛选:不要配置为空的
    config= {k:v for k,v in config.items() if v is not None}
    # 补充：校验核心配置是否存在（可选但推荐）
    required_keys = ["user", "password", "database"]
    missing_keys = [k for k in required_keys if k not in config]
    if missing_keys:
        raise ValueError(f"缺失数据库核心配置：{', '.join(missing_keys)}")

    return config

@tool
def list_sql_tables()->str:
    """
    查询数据库中可用的表
    :return:返回表:表1,表2.... 如果没有表返回"没有可用的表" 出现异常返回异常信息
    """
    #埋点,告诉前端哪个工具被调用
    monitor.report_tool(tool_name="数据库表名查询工具:list_sql_tables",args={})

    config= get_db_config()
    try:
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                #执行sql语句
                sql= "show tables"
                cursor.execute(sql)
                tables= cursor.fetchall()
                if not tables:
                    return "没有可用的表"
                table_names = [table[0] for table in tables]
                return f"可用的表有：{', '.join(table_names)}"

    except Error as e:
        return f"查询出现异常：{str(e)}"
@tool
def get_table_data(table_name)->str:
    """
    查询指定表名的数据！当前工具调用之前，必须先调用list_sql_tables完成表名的校验！
    此工具的作用：1.可以完成单表数据的查询 2. 可以为多表查询提供表结果信息（列名&数据格式）
    :param table_name:表名
    :return:csv格式的数据（模拟表格数据格式）
             1.第一行是列信息，列之间使用,（英文的逗号）分割
             2.第二行开始是表数据，值之间也使用,(英文的逗号)分割
             3.行和行之间使用\n分割
             4.至多表数据查询100条
             例如：
                id,name,age\n -> 列头
                1,张三,18\n
                1,张三,18\n    -> 至多查询100条
                1,张三,18\n
                1,张三,18\n
    """
    # 埋点,调用工具了告诉前端哪个工具被调用了！！
    monitor.report_tool(tool_name="数据库表数据查询工具：get_table_data", args={"table_name": table_name})

    config= get_db_config()
    try:
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                sql= f"select * from {table_name} limit 100"
                cursor.execute(sql)
                description=cursor.description
                if not description:
                    return f"数据表：{table_name}为空没有数据！"
                columns= [desc[0] for desc in description]
                rows=cursor.fetchall()
                results=[",".join(map(str,row)) for row in rows]
                header_str= ",".join(columns)
                data_str= ",".join(results)
                return f"{header_str}\n{data_str}"
    except Error as e:
        return f"查询出现异常：{str(e)}"

@tool
def execute_sql_query(query)->str:
    """
    执行自定义查询sql语句！切记：执行之前，需要通过执行 list_sql_tables明确表名！执行get_table_data
    明确表结构和数据格式！
    :param query: 要执行的自定义sql语句
    :return: csv格式的数据（模拟表格数据格式）
             1.第一行是列信息，列之间使用,（英文的逗号）分割
             2.第二行开始是表数据，值之间也使用,(英文的逗号)分割
             3.行和行之间使用\n分割
             4.至多表数据查询100条
             例如：
                id,name,age\n -> 列头
                1,张三,18\n
                1,张三,18\n    -> 至多查询100条
                1,张三,18\n
                1,张三,18\n
    """
    # 埋点,调用工具了告诉前端哪个工具被调用了！！
    monitor.report_tool(tool_name="数据库表数据查询工具：execute_sql_query", args={"query":query})

    # 获取数据库参数
    config = get_db_config()
    # 1. 创建一个链接
    # 2. 创建cursor
    # 3. cursor执行sql语句
    # 4. cursor获取返回结果
    # 5. 释放连接和cursor资源
    # 确保要捕捉异常信息，返回异常提示，避免直接报错！
    try:
        # 1. 创建一个链接
        with connect(**config) as  conn:
            # 2. 创建cursor
            with conn.cursor() as cursor:
                # 3. cursor执行sql语句
                cursor.execute(query)
                # 4. cursor获取返回结果
                # 4.1 获取列的信息
                # 返回的查询结果的列的信息
                # description => [(id,列长度...),(),()]
                # 如果查询没有结果 -》 description 也是None
                description = cursor.description
                if not description:
                    return f"执行自定义SQL语句查询没有结果，sql为：{query}！"
                # 4.2 获取查询结果
                # description =>  [(id,列长度...),(date,....),()] => 元组 index = 0 列名
                # [列1,列2,列3...]
                columns = [ desc[0] for desc in description ] # [1,2,3,4]
                # 表数据
                # [(1,张三),(2,李四),(3,二狗子)]
                rows = cursor.fetchall()
                # (1,张三) -> ('1','张三') -> '1,张三'
                # ['1,张三','1,张三','1,张三','1,张三','1,张三']
                results = [ ",".join(map(str,row)) for row in rows]

                # columns -> csv -> header
                # id,name,age
                header_str = ",".join(columns)
                # '1,张三'\n
                data_str = "\n".join(results)
                return f"{header_str}\n{data_str}"
    except Error as e:
        return f"查询出现异常：{str(e)}"
if __name__ == "__main__":
    print(execute_sql_query("SELECT * FROM `drugs` dgs join sales_records srd on dgs.drug_id = srd.drug_id"))
























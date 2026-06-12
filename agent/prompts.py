import yaml
from pathlib import Path


def load_yaml(file_path):
    """
    加载指定位置的yaml配置文件
    :param file_path: 加载配置文件地址
    :return: 加载返回结果,一个字典
    """
    with open(file_path, "r",encoding="utf-8") as f:
         return yaml.safe_load(f)

#路径到deep_search_pro
project_file_path = Path(__file__).parents[1]
#提出prompts.yml的路径
yaml_file_path = project_file_path / "prompt" / "prompts.yml"
prompt_yaml_content= load_yaml(yaml_file_path)
#提取main_agent的讯息
main_agent_content = prompt_yaml_content["main_agent"]
#提取sub_agent的讯息
sub_agents_content = prompt_yaml_content["sub_agents"]










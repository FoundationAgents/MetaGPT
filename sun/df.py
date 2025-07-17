import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt import tools

# 新增：引入 DataScientist 角色
try:
    from metagpt.roles.di.data_scientist import DataScientist
except ImportError:
    DataScientist = None

async def main(requirement: str, role_type: str = "interpreter"):
    if role_type == "scientist" and DataScientist is not None:
        role = DataScientist(tools=["<all>"])
    else:
        role = DataInterpreter(use_reflection=True, tools=["<all>"])
    await role.run(requirement)

if __name__ == "__main__":
    # 任务1：原有开发任务
    requirement_dev = '''
    生成一个简单的项目，项目名称为：test_project，项目描述为：实现登陆和注册功能的前后端口，
    数据库使用sqllite，使用flask框架，使用python语言，
    生成后需要进行测试，测试后发现bug需要修复。
    '''
    # 任务2：数据预处理任务
    requirement_data = '''
    请对以下数据集进行标准化、归一化和类别编码处理，输出处理后的数据。
    '''

    # 选择要运行的任务和角色
    if len(sys.argv) > 1 and sys.argv[1] == "data":
        asyncio.run(main(requirement_data, role_type="scientist"))
    else:
        asyncio.run(main(requirement_dev, role_type="interpreter"))
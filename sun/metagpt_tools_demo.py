#!/usr/bin/env python3
"""
MetaGPT 工具集演示脚本
在命令行下快速体验 MetaGPT 的常用工具（代码生成、文件写入、代码检查等）
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from metagpt.tools.libs.editor import Editor
from metagpt.tools.libs.linter import Linter
from metagpt.tools.libs.slc import CodeGenerationTool


def generate_code_demo():
    print("\n=== 代码生成演示 ===")
    requirement = input("请输入你的需求（如：实现一个斐波那契函数）：\n> ")
    code = CodeGenerationTool.generate_code(requirement)
    print("\n生成的代码如下：\n")
    print(code)
    return code

def write_file_demo(code: str):
    print("\n=== 文件写入演示 ===")
    filename = input("请输入要保存的文件名（如 demo.py）：\n> ")
    editor = Editor()
    editor.write(filename, code)
    print(f"代码已保存到 {filename}")
    return filename

def lint_file_demo(filename: str):
    print("\n=== 代码检查演示 ===")
    linter = Linter()
    result = linter.lint(filename)
    print("\n检查结果：")
    print(result)

def main():
    print("""
==============================
MetaGPT 工具集命令行演示
==============================
1. 生成代码
2. 写入文件
3. 代码检查
4. 一键体验（生成+写入+检查）
0. 退出
==============================
""")
    code = None
    filename = None
    while True:
        choice = input("请选择操作: ")
        if choice == '1':
            code = generate_code_demo()
        elif choice == '2':
            if not code:
                print("请先生成代码！")
                continue
            filename = write_file_demo(code)
        elif choice == '3':
            if not filename:
                print("请先写入文件！")
                continue
            lint_file_demo(filename)
        elif choice == '4':
            code = generate_code_demo()
            filename = write_file_demo(code)
            lint_file_demo(filename)
        elif choice == '0':
            print("再见！")
            break
        else:
            print("无效选择，请重新输入。");

if __name__ == "__main__":
    main() 
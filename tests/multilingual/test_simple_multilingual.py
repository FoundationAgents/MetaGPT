#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/07/18 08:31
@Author  : 18300676767
@File    : test_simple_multilingual.py
@Desc    : 简化的多语言支持测试
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from metagpt.utils.language_detector import get_language_detector
from metagpt.utils.language_context import (
    get_global_language_context, 
    render_prompt_with_language,
    get_current_language
)


async def test_basic_language_detection():
    """测试基本语言检测功能"""
    print("=" * 50)
    print("测试基本语言检测功能")
    print("=" * 50)
    
    detector = get_language_detector()
    
    test_cases = [
        "请帮我设计一个系统架构",
        "Please help me design a system architecture",
        "시스템 아키텍처를 설계하는 데 도움을 주세요"
    ]
    
    for text in test_cases:
        print(f"\n输入文本: {text}")
        # 只使用本地检测，不使用LLM
        result = await detector.detect_language(text, use_llm=False)
        print(f"Detection result: {result.language} (置信度: {result.confidence:.2f}, 方法: {result.method})")


async def test_prompt_rendering():
    """测试提示词渲染功能"""
    print("\n" + "=" * 50)
    print("测试提示词渲染功能")
    print("=" * 50)
    
    context = get_global_language_context()
    
    # 测试不同语言
    languages = ["Chinese", "English", "한국어"]
    
    for lang in languages:
        print(f"\n--- 设置语言: {lang} ---")
        context.set_forced_language(lang)
        
        # 测试提示词渲染
        prompt_template = "Please analyze the requirements and create a detailed plan."
        rendered = render_prompt_with_language(prompt_template)
        print(f"原始模板: {prompt_template}")
        print(f"渲染后: {rendered}")
        
        # 测试带变量的模板
        prompt_template2 = "Write code based on the following specification: {spec}"
        rendered2 = render_prompt_with_language(prompt_template2, spec="用户需求")
        print(f"带变量模板: {prompt_template2}")
        print(f"渲染后: {rendered2}")


async def test_language_context():
    """测试语言上下文管理"""
    print("\n" + "=" * 50)
    print("测试语言上下文管理")
    print("=" * 50)
    
    context = get_global_language_context()
    
    # 测试从输入设置语言
    test_inputs = [
        "请帮我写一个Python函数",
        "Write a Python function for me",
        "Python 함수를 작성해 주세요"
    ]
    
    for text in test_inputs:
        print(f"\n输入: {text}")
        detected_lang = await context.set_language_from_input(text, use_llm=False)
        print(f"检测到的语言: {detected_lang}")
        print(f"当前语言: {context.get_current_language()}")
        print(f"置信度: {context.get_confidence():.2f}")


async def main():
    """主测试函数"""
    print("开始测试MetaGPT多语言支持功能（简化版）")
    print("=" * 60)
    
    try:
        # 测试基本语言检测
        await test_basic_language_detection()
        
        # 测试提示词渲染
        await test_prompt_rendering()
        
        # 测试语言上下文管理
        await test_language_context()
        
        print("\n" + "=" * 60)
        print("简化测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 
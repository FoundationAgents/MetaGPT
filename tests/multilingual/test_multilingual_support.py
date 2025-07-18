#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/07/18 08:31
@Author  : 18300676767
@File    : test_multilingual_support.py
@Desc    : 测试多语言支持功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from metagpt.utils.language_detector import get_language_detector, LanguageDetectionResult
from metagpt.utils.language_context import (
    get_global_language_context, 
    process_user_input_for_language,
    render_prompt_with_language,
    get_current_language
)
from metagpt.tools.libs.slc import CodeGenerationTool, SmartQATool


async def test_language_detection():
    """测试语言检测功能"""
    print("=" * 50)
    print("测试语言检测功能")
    print("=" * 50)
    
    detector = get_language_detector()
    
    test_cases = [
        "请帮我设计一个系统架构",
        "Please help me design a system architecture",
        "시스템 아키텍처를 설계하는 데 도움을 주세요",
        "システムアーキテクチャの設計を手伝ってください",
        "Por favor, ayúdame a diseñar una arquitectura de sistema",
        "S'il vous plaît, aidez-moi à concevoir une architecture système"
    ]
    
    for text in test_cases:
        print(f"\n输入文本: {text}")
        result = await detector.detect_language(text, use_llm=False)  # 先测试本地检测
        print(f"Detection result: {result.language} (置信度: {result.confidence:.2f}, 方法: {result.method})")
        
        # 测试LLM检测
        try:
            llm_result = await detector.detect_language(text, use_llm=True)
            print(f"LLM检测: {llm_result.language} (置信度: {llm_result.confidence:.2f}, 方法: {llm_result.method})")
        except Exception as e:
            print(f"LLM检测失败: {e}")


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
        detected_lang = await context.set_language_from_input(text)
        print(f"检测到的语言: {detected_lang}")
        print(f"当前语言: {context.get_current_language()}")
        print(f"置信度: {context.get_confidence():.2f}")
    
    # 测试强制设置语言
    print(f"\n强制设置语言为韩语")
    context.set_forced_language("한국어")
    print(f"当前语言: {context.get_current_language()}")
    print(f"是否强制语言: {context.is_forced_language()}")
    
    # 重置语言
    context.reset_to_default()
    print(f"\n重置后语言: {context.get_current_language()}")


async def test_prompt_rendering():
    """测试提示词渲染"""
    print("\n" + "=" * 50)
    print("测试提示词渲染")
    print("=" * 50)
    
    # 设置语言为Chinese
    context = get_global_language_context()
    await context.set_language_from_input("请用Chinese回答")
    
    # 测试提示词渲染
    prompt_templates = [
        "Please analyze the requirements and create a detailed plan.",
        "Write code based on the following specification: {spec}",
        "Review the following code and provide feedback."
    ]
    
    for template in prompt_templates:
        rendered = render_prompt_with_language(template, spec="用户需求")
        print(f"\n原始模板: {template}")
        print(f"渲染后: {rendered}")


async def test_slc_tools_with_language():
    """测试SLC工具的多语言支持"""
    print("\n" + "=" * 50)
    print("测试SLC工具的多语言支持")
    print("=" * 50)
    
    # 测试不同语言环境下的代码生成
    languages = ["Chinese", "English", "한국어"]
    
    for lang in languages:
        print(f"\n--- 使用语言: {lang} ---")
        
        # 设置语言上下文
        context = get_global_language_context()
        context.set_forced_language(lang)
        
        # 测试代码生成
        try:
            code = await CodeGenerationTool.generate_code(
                "实现一个简单的计算器函数", 
                language="python"
            )
            print(f"生成的代码长度: {len(str(code))} 字符")
            print(f"代码预览: {str(code)[:100]}...")
        except Exception as e:
            print(f"代码生成失败: {e}")
        
        # 测试智能问答
        try:
            answer = await SmartQATool.smart_qa(
                "什么是Python装饰器？", 
                language="python"
            )
            print(f"问答回答长度: {len(str(answer))} 字符")
            print(f"回答预览: {str(answer)[:100]}...")
        except Exception as e:
            print(f"智能问答失败: {e}")


async def test_integration():
    """测试完整集成"""
    print("\n" + "=" * 50)
    print("测试完整集成")
    print("=" * 50)
    
    # 模拟用户输入处理流程
    user_inputs = [
        "请帮我设计一个用户管理系统",
        "Design a user management system for me",
        "사용자 관리 시스템을 설계해 주세요"
    ]
    
    for user_input in user_inputs:
        print(f"\n用户输入: {user_input}")
        
        # 1. 处理用户输入，检测语言
        detected_language = await process_user_input_for_language(user_input)
        print(f"检测到的语言: {detected_language}")
        
        # 2. 获取当前语言
        current_lang = get_current_language()
        print(f"当前语言: {current_lang}")
        
        # 3. 渲染提示词
        prompt_template = "Please analyze the requirements and provide a solution. Requirements: {req}"
        rendered_prompt = render_prompt_with_language(prompt_template, req=user_input)
        print(f"渲染后的提示词: {rendered_prompt[:100]}...")


async def main():
    """主测试函数"""
    print("开始测试MetaGPT多语言支持功能")
    print("=" * 60)
    
    try:
        # 测试语言检测
        await test_language_detection()
        
        # 测试语言上下文管理
        await test_language_context()
        
        # 测试提示词渲染
        await test_prompt_rendering()
        
        # 测试SLC工具
        await test_slc_tools_with_language()
        
        # 测试完整集成
        await test_integration()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 
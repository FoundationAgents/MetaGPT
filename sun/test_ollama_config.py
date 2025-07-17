#!/usr/bin/env python3
"""
Ollama 配置测试脚本
用于验证 slc.py 中的 Ollama 配置是否正确工作
"""

import sys
import os
sys.path.insert(0, '../metagpt')

from metagpt.tools.libs.slc import ollama_config, call_ollama, test_ollama_connection

def test_config_loading():
    """测试配置加载"""
    print("=== 测试配置加载 ===")
    print(f"模型: {ollama_config.model}")
    print(f"基础URL: {ollama_config.base_url}")
    print(f"超时时间: {ollama_config.timeout}秒")
    print(f"温度参数: {ollama_config.temperature}")
    print(f"最大Token数: {ollama_config.max_tokens}")
    print(f"流式响应: {ollama_config.stream}")
    print("配置加载测试完成\n")

def test_simple_api_call():
    """测试简单API调用"""
    print("=== 测试简单API调用 ===")
    prompt = "请用Python写一个简单的Hello World程序"
    print(f"发送请求: {prompt}")
    
    response = call_ollama(prompt)
    print(f"响应结果: {response[:200]}...")  # 只显示前200个字符
    print("简单API调用测试完成\n")

def test_connection():
    """测试连接"""
    print("=== 测试Ollama连接 ===")
    if test_ollama_connection():
        print("✅ Ollama连接测试成功")
    else:
        print("❌ Ollama连接测试失败")
    print("连接测试完成\n")

def test_different_models():
    """测试不同模型"""
    print("=== 测试不同模型 ===")
    models = ["qwen2.5:7b", "llama3:8b", "mistral:7b"]
    
    for model in models:
        print(f"测试模型: {model}")
        try:
            response = call_ollama("Hello", model=model)
            if "错误" not in response:
                print(f"✅ 模型 {model} 工作正常")
            else:
                print(f"❌ 模型 {model} 调用失败: {response}")
        except Exception as e:
            print(f"❌ 模型 {model} 异常: {e}")
    print("不同模型测试完成\n")

def test_parameters():
    """测试不同参数"""
    print("=== 测试不同参数 ===")
    
    # 测试不同温度
    temperatures = [0.1, 0.5, 0.9]
    for temp in temperatures:
        print(f"测试温度: {temp}")
        response = call_ollama("写一个简单的函数", temperature=temp)
        print(f"响应长度: {len(response)} 字符")
    
    # 测试不同max_tokens
    max_tokens_list = [100, 500, 1000]
    for tokens in max_tokens_list:
        print(f"测试max_tokens: {tokens}")
        response = call_ollama("解释什么是Python", max_tokens=tokens)
        print(f"响应长度: {len(response)} 字符")
    
    print("参数测试完成\n")

def main():
    """主测试函数"""
    print("🚀 开始Ollama配置测试\n")
    
    try:
        test_config_loading()
        test_connection()
        test_simple_api_call()
        test_different_models()
        test_parameters()
        
        print("🎉 所有测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
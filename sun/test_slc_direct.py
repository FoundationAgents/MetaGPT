#!/usr/bin/env python3
"""
直接测试SLC配置和API调用
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_slc_config_directly():
    """直接测试SLC配置"""
    print("=== 直接测试SLC配置 ===")
    
    try:
        # 直接导入配置类
        import yaml
        from pathlib import Path
        
        # 加载配置文件
        config_path = Path(__file__).parent.parent / "config2.yaml"
        print(f"配置文件路径: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        
        llm_config = config.get('llm', {})
        print(f"模型: {llm_config.get('model')}")
        print(f"基础URL: {llm_config.get('base_url')}")
        print(f"超时: {llm_config.get('timeout')}")
        print(f"温度: {llm_config.get('temperature')}")
        
        # 构建API URL
        base_url = llm_config.get('base_url', 'http://127.0.0.1:11434')
        api_url = f"{base_url.rstrip('/')}/api/generate"
        print(f"API URL: {api_url}")
        
        print("✅ 配置加载成功")
        return config
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return None

def test_ollama_api_directly():
    """直接测试Ollama API"""
    print("\n=== 直接测试Ollama API ===")
    
    try:
        import requests
        import json
        
        # 使用配置中的参数
        api_url = "http://127.0.0.1:11434/api/generate"
        model = "qwen2.5:7b"
        
        payload = {
            "model": model,
            "prompt": "请用Python写一个简单的Hello World程序",
            "temperature": 0.1,
            "stream": False
        }
        
        print(f"发送请求到: {api_url}")
        print(f"使用模型: {model}")
        
        response = requests.post(
            api_url,
            json=payload,
            timeout=60,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功")
            print("生成的代码:")
            print(result.get('response', ''))
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ API调用异常: {e}")

def test_code_generation_workflow():
    """测试完整的代码生成工作流"""
    print("\n=== 测试代码生成工作流 ===")
    
    try:
        import requests
        import json
        
        # 模拟SLC的代码生成流程
        prompt = """
请用Python实现一个简单的计算器函数，支持加减乘除四则运算。
要求：
1. 函数名为 calculator
2. 接受两个数字和一个运算符作为参数
3. 返回计算结果
4. 包含错误处理
5. 代码要完整可运行
6. 包含必要的注释
7. 遵循最佳实践
"""
        
        payload = {
            "model": "qwen2.5:7b",
            "prompt": prompt,
            "temperature": 0.1,
            "stream": False
        }
        
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            code = result.get('response', '')
            print("✅ 代码生成成功")
            print("生成的代码:")
            print(code)
            
            # 简单验证生成的代码
            if "def calculator" in code and "return" in code:
                print("✅ 代码结构验证通过")
            else:
                print("⚠️ 代码结构可能不完整")
        else:
            print(f"❌ 代码生成失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 工作流测试异常: {e}")

def main():
    """主测试函数"""
    print("🚀 开始直接测试SLC功能\n")
    
    # 测试配置加载
    config = test_slc_config_directly()
    
    # 测试API调用
    test_ollama_api_directly()
    
    # 测试完整工作流
    test_code_generation_workflow()
    
    print("\n🎉 所有测试完成！")

if __name__ == "__main__":
    main() 
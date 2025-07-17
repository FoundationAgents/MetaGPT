#!/usr/bin/env python3
"""
简化的Ollama配置测试脚本
"""

import yaml
import requests
import json
from pathlib import Path

def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config2.yaml"
    print(f"尝试加载配置文件: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        print("✅ 配置文件加载成功")
        return config
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        return None

def test_ollama_api(config):
    """测试Ollama API"""
    if not config:
        print("❌ 配置为空，跳过API测试")
        return
    
    llm_config = config.get('llm', {})
    base_url = llm_config.get('base_url', 'http://127.0.0.1:11434')
    model = llm_config.get('model', 'qwen2.5:7b')
    timeout = llm_config.get('timeout', 60)
    
    # 构建API URL
    api_url = f"{base_url.rstrip('/')}/api/generate"
    print(f"API URL: {api_url}")
    print(f"模型: {model}")
    print(f"超时: {timeout}秒")
    
    # 测试请求
    payload = {
        "model": model,
        "prompt": "Hello, please respond with 'OK' if you can see this message.",
        "temperature": 0.1,
        "stream": False
    }
    
    try:
        print("发送测试请求...")
        response = requests.post(
            api_url,
            json=payload,
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功")
            print(f"响应: {result.get('response', '')[:100]}...")
        else:
            print(f"❌ API调用失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请检查Ollama服务是否运行")
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时 (timeout={timeout}s)")
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def main():
    """主函数"""
    print("🚀 开始简化配置测试\n")
    
    # 测试配置加载
    config = load_config()
    if config:
        print(f"配置内容: {config}\n")
    
    # 测试API调用
    test_ollama_api(config)
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
测试 Ollama API 修复效果
验证 JSON 解析和错误处理是否正常工作
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import json
from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.provider.ollama_api import OllamaLLM

async def test_ollama_api():
    """测试 Ollama API 修复效果"""
    print("=== 测试 Ollama API 修复效果 ===")
    
    try:
        # 创建 Ollama 配置
        config = LLMConfig(
            api_type=LLMType.OLLAMA,
            model="qwen2.5:7b",
            base_url="http://127.0.0.1:11434/api/",  # 修改为带 /api/ 路径
            api_key="dummy-key",  # Ollama 不需要真实的 API key，但需要非空值
            timeout=600,
            temperature=0.1,
            stream=False
        )
        
        # 创建 Ollama LLM 实例
        ollama_llm = OllamaLLM(config)
        print("✅ Ollama LLM 实例创建成功")
        
        # 测试简单的消息
        messages = [
            {"role": "user", "content": "你好，请简单介绍一下自己"}
        ]
        
        print("📤 发送测试消息...")
        response = await ollama_llm.acompletion(messages)
        print("✅ 收到响应")
        
        # 提取文本内容
        if isinstance(response, dict):
            if "error" in response:
                print(f"❌ API 错误: {response['error']}")
                if "raw_data" in response:
                    print(f"原始数据: {response['raw_data']}")
            else:
                try:
                    content = ollama_llm.get_choice_text(response)
                    print(f"✅ 响应内容: {content[:100]}...")
                except Exception as e:
                    print(f"❌ 提取内容失败: {e}")
                    print(f"响应结构: {json.dumps(response, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 意外响应类型: {type(response)}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_json_parsing():
    """测试 JSON 解析修复"""
    print("\n=== 测试 JSON 解析修复 ===")
    
    from metagpt.provider.ollama_api import OllamaMessageBase
    from metagpt.provider.general_api_requestor import OpenAIResponse
    
    # 模拟正常的 JSON 响应
    normal_json = '{"message": {"role": "assistant", "content": "你好！"}}'
    normal_response = OpenAIResponse(normal_json.encode('utf-8'), {})
    
    # 模拟有问题的 JSON 响应
    bad_json = '{"message": {"role": "assistant", "content": "你好！"'  # 缺少结束括号
    bad_response = OpenAIResponse(bad_json.encode('utf-8'), {})
    
    # 模拟流式响应片段
    stream_json = 'data: {"response": "你好", "done": false}\n'
    stream_response = OpenAIResponse(stream_json.encode('utf-8'), {})
    
    # 创建测试实例
    test_instance = OllamaMessageBase("test-model")
    
    try:
        # 测试正常 JSON
        result1 = test_instance.decode(normal_response)
        print(f"✅ 正常 JSON 解析: {result1}")
        
        # 测试有问题的 JSON
        result2 = test_instance.decode(bad_response)
        print(f"✅ 问题 JSON 处理: {result2}")
        
        # 测试流式响应
        result3 = test_instance.decode(stream_response)
        print(f"✅ 流式响应处理: {result3}")
        
    except Exception as e:
        print(f"❌ JSON 解析测试失败: {e}")

if __name__ == "__main__":
    print("开始测试 Ollama API 修复效果...")
    
    # 测试 JSON 解析修复
    test_json_parsing()
    
    # 测试完整的 API 调用
    asyncio.run(test_ollama_api())
    
    print("\n🎉 测试完成！") 
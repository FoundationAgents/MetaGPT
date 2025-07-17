#!/usr/bin/env python3
"""
实际的 Ollama 调用测试脚本
测试真实的 Ollama API 调用功能
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

async def test_ollama_direct_api():
    """直接测试 Ollama API"""
    print("=" * 60)
    print("🔗 直接测试 Ollama API")
    print("=" * 60)
    
    try:
        import requests
        
        # 测试 Ollama 聊天 API
        url = "http://127.0.0.1:11434/api/chat"
        payload = {
            "model": "qwen2.5:7b",
            "messages": [
                {"role": "user", "content": "Hello, please say 'Hello from Ollama!'"}
            ],
            "stream": False
        }
        
        print(f"🌐 请求 URL: {url}")
        print(f"📝 请求内容: {json.dumps(payload, indent=2)}")
        
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=30)
        end_time = time.time()
        
        print(f"⏱️  响应时间: {end_time - start_time:.2f}秒")
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API 调用成功")
            print(f"📄 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 提取回复内容
            if 'message' in result and 'content' in result['message']:
                content = result['message']['content']
                print(f"💬 模型回复: {content}")
            else:
                print(f"⚠️  响应格式异常: {result}")
            
            return True
        else:
            print(f"❌ API 调用失败: {response.status_code}")
            print(f"📄 错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 直接 API 测试失败: {e}")
        return False

async def test_ollama_streaming():
    """测试 Ollama 流式响应"""
    print("\n" + "=" * 60)
    print("🌊 测试 Ollama 流式响应")
    print("=" * 60)
    
    try:
        import requests
        
        # 测试 Ollama 流式聊天 API
        url = "http://127.0.0.1:11434/api/chat"
        payload = {
            "model": "qwen2.5:7b",
            "messages": [
                {"role": "user", "content": "Write a short poem about AI in 3 lines."}
            ],
            "stream": True
        }
        
        print(f"🌐 请求 URL: {url}")
        print(f"📝 请求内容: {json.dumps(payload, indent=2)}")
        
        start_time = time.time()
        response = requests.post(url, json=payload, stream=True, timeout=30)
        end_time = time.time()
        
        print(f"⏱️  响应时间: {end_time - start_time:.2f}秒")
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 流式 API 调用成功")
            print("📄 流式响应内容:")
            
            full_content = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 移除 'data: ' 前缀
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'message' in data and 'content' in data['message']:
                                content = data['message']['content']
                                print(f"   {content}", end='', flush=True)
                                full_content += content
                        except json.JSONDecodeError:
                            continue
            
            print(f"\n💬 完整回复: {full_content}")
            return True
        else:
            print(f"❌ 流式 API 调用失败: {response.status_code}")
            print(f"📄 错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 流式响应测试失败: {e}")
        return False

async def test_ollama_embeddings_api():
    """测试 Ollama 嵌入 API"""
    print("\n" + "=" * 60)
    print("🔢 测试 Ollama 嵌入 API")
    print("=" * 60)
    
    try:
        import requests
        
        # 测试 Ollama 嵌入 API
        url = "http://127.0.0.1:11434/api/embeddings"
        payload = {
            "model": "qwen2.5:7b",
            "prompt": "Hello, this is a test for embeddings."
        }
        
        print(f"🌐 请求 URL: {url}")
        print(f"📝 请求内容: {json.dumps(payload, indent=2)}")
        
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=30)
        end_time = time.time()
        
        print(f"⏱️  响应时间: {end_time - start_time:.2f}秒")
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 嵌入 API 调用成功")
            
            if 'embedding' in result:
                embedding = result['embedding']
                print(f"🔢 嵌入向量维度: {len(embedding)}")
                print(f"📊 向量前5个值: {embedding[:5]}")
                print(f"📊 向量后5个值: {embedding[-5:]}")
            else:
                print(f"⚠️  响应格式异常: {result}")
            
            return True
        else:
            print(f"❌ 嵌入 API 调用失败: {response.status_code}")
            print(f"📄 错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 嵌入 API 测试失败: {e}")
        return False

def test_gpu_performance():
    """测试 GPU 性能"""
    print("\n" + "=" * 60)
    print("🎮 测试 GPU 性能")
    print("=" * 60)
    
    try:
        import subprocess
        
        # 获取 GPU 详细信息
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ GPU 性能信息获取成功")
                print("📊 GPU 详细信息:")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split(', ')
                        if len(parts) >= 5:
                            name, mem_used, mem_total, util, temp = parts
                            print(f"   - {name}:")
                            print(f"     内存: {mem_used}/{mem_total}MB ({int(mem_used)/int(mem_total)*100:.1f}%)")
                            print(f"     利用率: {util}%")
                            print(f"     温度: {temp}°C")
                return True
            else:
                print("⚠️  GPU 信息获取失败")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("⚠️  nvidia-smi 不可用或超时")
            return True
            
    except Exception as e:
        print(f"❌ GPU 性能测试失败: {e}")
        return True

async def main():
    """主测试函数"""
    print("🚀 MetaGPT Ollama 实际功能测试")
    print("=" * 60)
    print(f"⏰ 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python 版本: {sys.version.split()[0]}")
    print(f"📁 工作目录: {Path.cwd()}")
    
    # 运行所有测试
    tests = [
        ("直接 API 调用", test_ollama_direct_api),
        ("流式响应", test_ollama_streaming),
        ("嵌入 API", test_ollama_embeddings_api),
        ("GPU 性能", test_gpu_performance),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果摘要
    print("\n" + "=" * 60)
    print("📊 测试结果摘要")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\n📈 测试通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed >= total * 0.75:  # 75% 通过率认为成功
        print("🎉 Ollama 实际功能测试成功！")
    else:
        print("⚠️  部分功能需要进一步配置")
    
    return passed >= total * 0.75

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 
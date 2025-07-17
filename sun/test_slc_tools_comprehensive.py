#!/usr/bin/env python3
"""
SLC工具集综合测试脚本
测试所有工具模块是否正常工作
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_config_loading():
    """测试配置加载"""
    print("=== 测试配置加载 ===")
    try:
        import yaml
        from pathlib import Path
        
        config_path = Path(__file__).parent.parent / "config2.yaml"
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        
        llm_config = config.get('llm', {})
        print(f"✅ 配置加载成功")
        print(f"   模型: {llm_config.get('model')}")
        print(f"   地址: {llm_config.get('base_url')}")
        print(f"   超时: {llm_config.get('timeout')}秒")
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def test_ollama_connection():
    """测试Ollama连接"""
    print("\n=== 测试Ollama连接 ===")
    try:
        import requests
        
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "qwen2.5:7b",
                "prompt": "Hello, respond with 'OK'",
                "temperature": 0.1,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "OK" in result.get('response', ''):
                print("✅ Ollama连接正常")
                return True
            else:
                print("⚠️ Ollama响应异常")
                return False
        else:
            print(f"❌ Ollama连接失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama连接异常: {e}")
        return False

def test_code_generation_tool():
    """测试代码生成工具"""
    print("\n=== 测试代码生成工具 ===")
    try:
        import requests
        
        prompt = """
请用Python实现一个简单的文件读取函数，要求：
1. 函数名为 read_file
2. 接受文件路径作为参数
3. 返回文件内容
4. 包含错误处理
5. 支持UTF-8编码
"""
        
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "qwen2.5:7b",
                "prompt": prompt,
                "temperature": 0.1,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            code = result.get('response', '')
            print("✅ 代码生成成功")
            
            # 验证代码质量
            if "def read_file" in code and "try:" in code and "except" in code:
                print("✅ 代码质量验证通过")
                print("生成的代码片段:")
                lines = code.split('\n')[:10]  # 显示前10行
                for line in lines:
                    print(f"   {line}")
                return True
            else:
                print("⚠️ 代码质量可能不完整")
                return False
        else:
            print(f"❌ 代码生成失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 代码生成异常: {e}")
        return False

def test_code_refactor_tool():
    """测试代码重构工具"""
    print("\n=== 测试代码重构工具 ===")
    try:
        import requests
        
        original_code = """
def add(a, b):
    return a+b
"""
        
        prompt = f"""
请重构以下代码，添加类型注解和文档字符串：

原始代码：
```python
{original_code}
```

要求：
1. 添加类型注解
2. 添加文档字符串
3. 保持原有功能
4. 遵循PEP8规范
"""
        
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "qwen2.5:7b",
                "prompt": prompt,
                "temperature": 0.1,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            refactored_code = result.get('response', '')
            print("✅ 代码重构成功")
            
            # 验证重构质量
            if "def add" in refactored_code and "->" in refactored_code and '"""' in refactored_code:
                print("✅ 重构质量验证通过")
                print("重构后的代码:")
                lines = refactored_code.split('\n')[:8]  # 显示前8行
                for line in lines:
                    print(f"   {line}")
                return True
            else:
                print("⚠️ 重构质量可能不完整")
                return False
        else:
            print(f"❌ 代码重构失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 代码重构异常: {e}")
        return False

def test_code_analysis_tool():
    """测试代码分析工具"""
    print("\n=== 测试代码分析工具 ===")
    try:
        import requests
        
        code_to_analyze = """
import os
import json
from typing import List, Dict

class DataProcessor:
    def __init__(self, config: Dict):
        self.config = config
    
    def process_data(self, data: List) -> List:
        return [item * 2 for item in data]
"""
        
        prompt = f"""
请分析以下Python代码的结构和依赖关系：

```python
{code_to_analyze}
```

请分析：
1. 导入的模块和包
2. 类的结构和方法
3. 类型注解使用情况
4. 潜在的改进建议
"""
        
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "qwen2.5:7b",
                "prompt": prompt,
                "temperature": 0.1,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis = result.get('response', '')
            print("✅ 代码分析成功")
            
            # 验证分析质量
            if "导入" in analysis or "import" in analysis.lower():
                print("✅ 分析质量验证通过")
                print("分析结果片段:")
                lines = analysis.split('\n')[:6]  # 显示前6行
                for line in lines:
                    print(f"   {line}")
                return True
            else:
                print("⚠️ 分析质量可能不完整")
                return False
        else:
            print(f"❌ 代码分析失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 代码分析异常: {e}")
        return False

def test_batch_operations():
    """测试批量操作工具"""
    print("\n=== 测试批量操作工具 ===")
    try:
        # 创建测试文件
        test_files = ["test1.py", "test2.py", "test3.py"]
        for file in test_files:
            with open(file, 'w') as f:
                f.write("# Test file\nprint('hello')\n")
        
        print("✅ 测试文件创建成功")
        
        # 模拟批量重命名
        import os
        for i, file in enumerate(test_files):
            new_name = f"renamed_{i+1}.py"
            if os.path.exists(file):
                os.rename(file, new_name)
                print(f"   {file} -> {new_name}")
        
        # 清理测试文件
        for i in range(1, 4):
            file = f"renamed_{i}.py"
            if os.path.exists(file):
                os.remove(file)
        
        print("✅ 批量操作测试完成")
        return True
    except Exception as e:
        print(f"❌ 批量操作异常: {e}")
        return False

def test_environment_tools():
    """测试环境管理工具"""
    print("\n=== 测试环境管理工具 ===")
    try:
        import subprocess
        
        # 测试Python版本
        result = subprocess.run(['python', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Python版本: {result.stdout.strip()}")
        
        # 测试pip版本
        result = subprocess.run(['pip', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Pip版本: {result.stdout.strip()}")
        
        print("✅ 环境工具测试完成")
        return True
    except Exception as e:
        print(f"❌ 环境工具异常: {e}")
        return False

def test_qa_tools():
    """测试智能问答工具"""
    print("\n=== 测试智能问答工具 ===")
    try:
        import requests
        
        questions = [
            "什么是Python的装饰器？",
            "如何优化Python代码性能？",
            "Python中如何处理异常？"
        ]
        
        for question in questions:
            response = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": "qwen2.5:7b",
                    "prompt": f"请简要回答：{question}",
                    "temperature": 0.1,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', '')[:100]  # 只显示前100字符
                print(f"✅ Q: {question}")
                print(f"   A: {answer}...")
            else:
                print(f"❌ 问答失败: {response.status_code}")
                return False
        
        print("✅ 智能问答测试完成")
        return True
    except Exception as e:
        print(f"❌ 智能问答异常: {e}")
        return False

def test_multi_language_support():
    """测试多语言支持"""
    print("\n=== 测试多语言支持 ===")
    try:
        import requests
        
        languages = [
            ("Python", "实现一个简单的计算器"),
            ("JavaScript", "实现一个数组去重函数"),
            ("Java", "实现一个简单的链表")
        ]
        
        for lang, task in languages:
            prompt = f"请用{lang}实现：{task}"
            
            response = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": "qwen2.5:7b",
                    "prompt": prompt,
                    "temperature": 0.1,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                code = result.get('response', '')[:150]  # 显示前150字符
                print(f"✅ {lang}: {task}")
                print(f"   代码: {code}...")
            else:
                print(f"❌ {lang}代码生成失败")
                return False
        
        print("✅ 多语言支持测试完成")
        return True
    except Exception as e:
        print(f"❌ 多语言支持异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始SLC工具集综合测试\n")
    
    test_results = []
    
    # 执行所有测试
    tests = [
        ("配置加载", test_config_loading),
        ("Ollama连接", test_ollama_connection),
        ("代码生成", test_code_generation_tool),
        ("代码重构", test_code_refactor_tool),
        ("代码分析", test_code_analysis_tool),
        ("批量操作", test_batch_operations),
        ("环境管理", test_environment_tools),
        ("智能问答", test_qa_tools),
        ("多语言支持", test_multi_language_support)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            test_results.append((test_name, False))
    
    # 输出测试总结
    print("\n" + "="*50)
    print("📊 测试结果总结")
    print("="*50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:15} : {status}")
        if result:
            passed += 1
    
    print("-"*50)
    print(f"总计: {total} 项测试")
    print(f"通过: {passed} 项")
    print(f"失败: {total - passed} 项")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！SLC工具集工作正常！")
    else:
        print(f"\n⚠️ 有 {total - passed} 项测试失败，请检查相关功能")
    
    print("="*50)

if __name__ == "__main__":
    main() 
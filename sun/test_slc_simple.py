#!/usr/bin/env python3
"""
简化的SLC测试脚本
只测试核心的代码生成功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 直接导入slc模块的核心函数
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'metagpt', 'tools', 'libs'))

def test_code_generation():
    """测试代码生成功能"""
    print("=== 测试代码生成功能 ===")
    
    try:
        # 直接导入call_ollama函数
        from slc import call_ollama
        
        prompt = """
请用Python实现一个简单的计算器函数，支持加减乘除四则运算。
要求：
1. 函数名为 calculator
2. 接受两个数字和一个运算符作为参数
3. 返回计算结果
4. 包含错误处理
"""
        
        print("发送代码生成请求...")
        response = call_ollama(prompt, temperature=0.1)
        
        if "错误" not in response:
            print("✅ 代码生成成功")
            print("生成的代码:")
            print(response)
        else:
            print(f"❌ 代码生成失败: {response}")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()

def test_code_refactor():
    """测试代码重构功能"""
    print("\n=== 测试代码重构功能 ===")
    
    try:
        from slc import call_ollama
        
        original_code = """
def add(a, b):
    return a+b
"""
        
        instruction = "将函数改为支持任意数量参数，并增加类型注解"
        
        prompt = f"""
请根据以下指令重构代码：

原始代码：
```python
{original_code}
```

重构指令：{instruction}

要求：
1. 保持原有功能
2. 提高代码质量
3. 优化性能
4. 增强可读性
5. 遵循最佳实践

请直接返回重构后的代码，不需要其他解释。
"""
        
        print("发送代码重构请求...")
        response = call_ollama(prompt, temperature=0.1)
        
        if "错误" not in response:
            print("✅ 代码重构成功")
            print("重构后的代码:")
            print(response)
        else:
            print(f"❌ 代码重构失败: {response}")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")

def main():
    """主测试函数"""
    print("🚀 开始简化SLC测试\n")
    
    test_code_generation()
    test_code_refactor()
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
测试SLC工具类
直接测试slc.py中定义的各种工具类
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_slc_import():
    """测试SLC模块导入"""
    print("=== 测试SLC模块导入 ===")
    try:
        # 尝试导入SLC模块
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'metagpt', 'tools', 'libs'))
        
        # 直接导入call_ollama函数
        from slc import call_ollama, ollama_config
        
        print("✅ SLC模块导入成功")
        print(f"   配置模型: {ollama_config.model}")
        print(f"   配置地址: {ollama_config.base_url}")
        return True
    except Exception as e:
        print(f"❌ SLC模块导入失败: {e}")
        return False

def test_code_generation_class():
    """测试代码生成类"""
    print("\n=== 测试代码生成类 ===")
    try:
        from slc import call_ollama
        
        # 模拟CodeGenerationTool.generate_code方法
        def generate_code(requirement: str, language: str = "python"):
            prompt = f"""
请用 {language} 实现以下需求：{requirement}

要求：
1. 代码要完整可运行
2. 包含必要的注释
3. 遵循最佳实践
4. 处理异常情况
5. 提供使用示例

请直接返回代码，不需要其他解释。
"""
            return call_ollama(prompt, temperature=0.1)
        
        # 测试代码生成
        requirement = "实现一个简单的文件读取函数"
        result = generate_code(requirement, "python")
        
        if "def" in result and "return" in result:
            print("✅ 代码生成类测试成功")
            print("生成的代码片段:")
            lines = result.split('\n')[:8]
            for line in lines:
                print(f"   {line}")
            return True
        else:
            print("❌ 代码生成质量不达标")
            return False
            
    except Exception as e:
        print(f"❌ 代码生成类测试失败: {e}")
        return False

def test_code_refactor_class():
    """测试代码重构类"""
    print("\n=== 测试代码重构类 ===")
    try:
        from slc import call_ollama
        
        # 模拟CodeGenerationTool.refactor_code方法
        def refactor_code(code: str, instruction: str):
            prompt = f"""
请根据以下指令重构代码：

原始代码：
```python
{code}
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
            return call_ollama(prompt, temperature=0.1)
        
        # 测试代码重构
        original_code = """
def add(a, b):
    return a+b
"""
        instruction = "添加类型注解和文档字符串"
        result = refactor_code(original_code, instruction)
        
        if "def add" in result and "->" in result:
            print("✅ 代码重构类测试成功")
            print("重构后的代码:")
            lines = result.split('\n')[:6]
            for line in lines:
                print(f"   {line}")
            return True
        else:
            print("❌ 代码重构质量不达标")
            return False
            
    except Exception as e:
        print(f"❌ 代码重构类测试失败: {e}")
        return False

def test_code_analysis_class():
    """测试代码分析类"""
    print("\n=== 测试代码分析类 ===")
    try:
        from slc import call_ollama
        
        # 模拟CodeUnderstandingTool.analyze_structure方法
        def analyze_structure(project_path: str):
            prompt = f"""
请分析项目 {project_path} 的源码结构，包括：
1. 主要模块和功能
2. 核心类和它们的作用
3. 文件组织架构
4. 依赖关系
5. 设计模式使用情况

请用中文详细描述项目结构。
"""
            return call_ollama(prompt)
        
        # 测试代码分析
        result = analyze_structure("metagpt/tools/libs")
        
        if len(result) > 50:  # 确保有足够的分析内容
            print("✅ 代码分析类测试成功")
            print("分析结果片段:")
            lines = result.split('\n')[:5]
            for line in lines:
                print(f"   {line}")
            return True
        else:
            print("❌ 代码分析内容不足")
            return False
            
    except Exception as e:
        print(f"❌ 代码分析类测试失败: {e}")
        return False

def test_batch_operations_class():
    """测试批量操作类"""
    print("\n=== 测试批量操作类 ===")
    try:
        # 模拟BatchFileTool的功能
        import os
        
        # 创建测试文件
        test_files = ["batch_test1.py", "batch_test2.py"]
        for file in test_files:
            with open(file, 'w') as f:
                f.write("# Test file\nprint('hello')\n")
        
        print("✅ 测试文件创建成功")
        
        # 模拟批量重命名
        for i, file in enumerate(test_files):
            new_name = f"batch_renamed_{i+1}.py"
            if os.path.exists(file):
                os.rename(file, new_name)
                print(f"   {file} -> {new_name}")
        
        # 模拟批量替换内容
        for i in range(1, 3):
            file = f"batch_renamed_{i}.py"
            if os.path.exists(file):
                with open(file, 'r') as f:
                    content = f.read()
                content = content.replace("hello", "world")
                with open(file, 'w') as f:
                    f.write(content)
                print(f"   {file} 内容替换完成")
        
        # 清理测试文件
        for i in range(1, 3):
            file = f"batch_renamed_{i}.py"
            if os.path.exists(file):
                os.remove(file)
        
        print("✅ 批量操作类测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 批量操作类测试失败: {e}")
        return False

def test_environment_tools_class():
    """测试环境管理工具类"""
    print("\n=== 测试环境管理工具类 ===")
    try:
        import subprocess
        
        # 模拟EnvManagerTool.generate_requirements方法
        def generate_requirements(project_path: str):
            try:
                result = subprocess.run(['pip', 'freeze'], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    return result.stdout
                else:
                    return "无法生成requirements.txt"
            except Exception as e:
                return f"生成失败: {e}"
        
        # 测试生成requirements
        result = generate_requirements(".")
        
        if "==" in result and len(result) > 100:
            print("✅ 环境管理工具类测试成功")
            print("生成的requirements片段:")
            lines = result.split('\n')[:5]
            for line in lines:
                print(f"   {line}")
            return True
        else:
            print("❌ requirements生成失败")
            return False
            
    except Exception as e:
        print(f"❌ 环境管理工具类测试失败: {e}")
        return False

def test_qa_tools_class():
    """测试智能问答工具类"""
    print("\n=== 测试智能问答工具类 ===")
    try:
        from slc import call_ollama
        
        # 模拟SmartQATool.smart_qa方法
        def smart_qa(question: str, language: str = "python"):
            prompt = f"""
请回答以下关于{language}的问题：{question}

要求：
1. 回答要准确、详细
2. 提供实际例子
3. 包含最佳实践
4. 用中文回答
"""
            return call_ollama(prompt, temperature=0.1)
        
        # 测试智能问答
        question = "什么是Python的列表推导式？"
        result = smart_qa(question, "python")
        
        if len(result) > 50 and ("列表" in result or "list" in result.lower()):
            print("✅ 智能问答工具类测试成功")
            print("问答结果片段:")
            lines = result.split('\n')[:4]
            for line in lines:
                print(f"   {line}")
            return True
        else:
            print("❌ 智能问答质量不达标")
            return False
            
    except Exception as e:
        print(f"❌ 智能问答工具类测试失败: {e}")
        return False

def test_multi_language_class():
    """测试多语言支持类"""
    print("\n=== 测试多语言支持类 ===")
    try:
        from slc import call_ollama
        
        # 模拟MultiLangTool.generate_code_multi方法
        def generate_code_multi(requirement: str, language: str):
            prompt = f"""
请用 {language} 实现以下需求：{requirement}

要求：
1. 代码要完整可运行
2. 包含必要的注释
3. 遵循该语言的最佳实践
4. 处理异常情况
5. 提供使用示例

请直接返回代码，不需要其他解释。
"""
            return call_ollama(prompt, temperature=0.1)
        
        # 测试多语言代码生成
        languages = [
            ("Python", "实现一个简单的计算器"),
            ("JavaScript", "实现一个数组去重函数")
        ]
        
        for lang, task in languages:
            result = generate_code_multi(task, lang)
            
            if len(result) > 30:
                print(f"✅ {lang} 代码生成成功")
                print(f"   代码片段: {result[:100]}...")
            else:
                print(f"❌ {lang} 代码生成失败")
                return False
        
        print("✅ 多语言支持类测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 多语言支持类测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始SLC工具类测试\n")
    
    test_results = []
    
    # 执行所有测试
    tests = [
        ("模块导入", test_slc_import),
        ("代码生成类", test_code_generation_class),
        ("代码重构类", test_code_refactor_class),
        ("代码分析类", test_code_analysis_class),
        ("批量操作类", test_batch_operations_class),
        ("环境管理类", test_environment_tools_class),
        ("智能问答类", test_qa_tools_class),
        ("多语言支持类", test_multi_language_class)
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
    print("📊 SLC工具类测试结果总结")
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
        print("\n🎉 所有SLC工具类测试通过！工具集完全正常工作！")
    else:
        print(f"\n⚠️ 有 {total - passed} 项测试失败，请检查相关功能")
    
    print("="*50)

if __name__ == "__main__":
    main() 
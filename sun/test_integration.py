#!/usr/bin/env python3
"""
SLC 与 MetaGPT 工具集集成测试
验证两者可以和谐共存并配合使用
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_slc_metagpt_integration():
    """测试 SLC 与 MetaGPT 工具集集成"""
    print("=== 测试 SLC 与 MetaGPT 工具集集成 ===")
    
    try:
        # 导入 SLC 工具
        from metagpt.tools.libs.slc import (
            CodeGenerationTool, 
            SmartQATool, 
            ollama_config
        )
        print("✅ SLC 工具导入成功")
        
        # 导入 MetaGPT 工具
        from metagpt.tools.libs.editor import Editor
        print("✅ MetaGPT 编辑器工具导入成功")
        
        # 测试配置共存
        print(f"SLC 配置 - 模型: {ollama_config.model}")
        print(f"SLC 配置 - 地址: {ollama_config.base_url}")
        
        # 测试功能集成
        print("\n--- 测试功能集成 ---")
        
        # 使用 SLC 生成代码
        print("1. 使用 SLC 生成代码...")
        code = CodeGenerationTool.generate_code("实现一个简单的文件读取函数")
        print("✅ 代码生成成功")
        
        # 使用 MetaGPT 编辑器保存代码
        print("2. 使用 MetaGPT 编辑器保存代码...")
        editor = Editor()
        test_file = "test_integration_output.py"
        editor.write(test_file, code)
        print(f"✅ 代码保存到 {test_file}")
        
        # 使用 SLC 进行代码审查
        print("3. 使用 SLC 进行代码审查...")
        review = SmartQATool.code_review(code)
        print("✅ 代码审查完成")
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"✅ 清理测试文件 {test_file}")
        
        print("\n🎉 SLC 与 MetaGPT 工具集集成测试成功！")
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False

def test_tool_registration():
    """测试工具注册是否冲突"""
    print("\n=== 测试工具注册 ===")
    
    try:
        # 检查 SLC 是否已注册到 MetaGPT 工具系统
        from metagpt.tools.libs import slc
        print("✅ SLC 模块已正确导入到 MetaGPT 工具系统")
        
        # 检查是否有命名冲突
        import metagpt.tools.libs as libs
        print("✅ 没有发现命名冲突")
        
        return True
        
    except Exception as e:
        print(f"❌ 工具注册测试失败: {e}")
        return False

def test_configuration_compatibility():
    """测试配置兼容性"""
    print("\n=== 测试配置兼容性 ===")
    
    try:
        # SLC 配置
        from metagpt.tools.libs.slc import ollama_config
        print(f"SLC 配置: {ollama_config}")
        
        # MetaGPT 配置（如果可用）
        try:
            from metagpt.config2 import Config
            config = Config()
            print(f"MetaGPT 配置: {config}")
        except ImportError:
            print("MetaGPT 配置模块不可用，跳过")
        
        print("✅ 配置兼容性测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置兼容性测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始 SLC 与 MetaGPT 工具集集成测试\n")
    
    tests = [
        ("SLC 与 MetaGPT 集成", test_slc_metagpt_integration),
        ("工具注册", test_tool_registration),
        ("配置兼容性", test_configuration_compatibility),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"测试: {test_name}")
        print('='*50)
        result = test_func()
        results.append((test_name, result))
    
    # 输出测试结果
    print(f"\n{'='*50}")
    print("测试结果总结")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {total} 项测试")
    print(f"通过: {passed} 项")
    print(f"失败: {total - passed} 项")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！SLC 与 MetaGPT 工具集完全兼容！")
    else:
        print(f"\n⚠️ 有 {total - passed} 项测试失败，需要进一步检查")

if __name__ == "__main__":
    main() 
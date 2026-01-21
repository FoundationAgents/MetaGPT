#!/usr/bin/env python3
"""
测试优化后的SLC工具集
验证代码生成质量和格式清理效果
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from metagpt.tools.libs.slc import CodeGenerationTool, MultiLanguageTool

def test_code_generation():
    """测试代码生成功能"""
    print("=== 测试代码生成功能 ===")
    
    # 测试简单的Python函数生成
    requirement = "实现一个计算斐波那契数列的函数"
    print(f"需求: {requirement}")
    
    code = CodeGenerationTool.generate_code(requirement, "python")
    print("\n生成的代码:")
    print("=" * 50)
    print(code)
    print("=" * 50)
    
    # 检查代码质量
    check_code_quality(code, "Python")
    
    return code

def test_code_refactoring():
    """测试代码重构功能"""
    print("\n=== 测试代码重构功能 ===")
    
    original_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    instruction = "优化性能，使用动态规划避免重复计算"
    print(f"重构指令: {instruction}")
    
    refactored_code = CodeGenerationTool.refactor_code(original_code, instruction)
    print("\n重构后的代码:")
    print("=" * 50)
    print(refactored_code)
    print("=" * 50)
    
    # 检查代码质量
    check_code_quality(refactored_code, "Python")
    
    return refactored_code

def test_multi_language():
    """测试多语言代码生成"""
    print("\n=== 测试多语言代码生成 ===")
    
    requirement = "实现一个简单的计算器，支持加减乘除"
    languages = ["python", "javascript", "java"]
    
    examples = MultiLanguageTool.generate_multi_language_example(requirement, languages)
    
    for lang, code in examples.items():
        print(f"\n{lang.upper()} 版本:")
        print("=" * 50)
        print(code)
        print("=" * 50)
        check_code_quality(code, lang)

def check_code_quality(code: str, language: str):
    """检查代码质量"""
    print(f"\n代码质量检查 ({language}):")
    
    # 检查是否包含markdown标记
    if "```" in code:
        print("❌ 包含markdown代码块标记")
    else:
        print("✅ 无markdown标记")
    
    # 检查是否包含说明文字
    explanation_markers = ["### 使用示例", "### 备注", "使用示例：", "备注：", "说明："]
    has_explanation = any(marker in code for marker in explanation_markers)
    if has_explanation:
        print("❌ 包含说明文字")
    else:
        print("✅ 无多余说明文字")
    
    # 检查代码长度
    lines = code.strip().split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    print(f"✅ 代码行数: {len(non_empty_lines)}")
    
    # 检查是否包含函数定义
    if language == "python":
        if "def " in code or "class " in code:
            print("✅ 包含函数或类定义")
        else:
            print("⚠️  可能缺少函数定义")
    elif language == "javascript":
        if "function " in code or "const " in code or "let " in code:
            print("✅ 包含函数或变量定义")
        else:
            print("⚠️  可能缺少函数定义")
    elif language == "java":
        if "public class " in code or "public static " in code:
            print("✅ 包含类或方法定义")
        else:
            print("⚠️  可能缺少类定义")

def save_test_results():
    """保存测试结果到文件"""
    print("\n=== 保存测试结果 ===")
    
    # 生成一个简单的测试代码
    requirement = "实现一个简单的文件读写工具类"
    code = CodeGenerationTool.generate_code(requirement, "python")
    
    # 保存到文件
    output_file = "workspace/test_slc_optimized_output.py"
    os.makedirs("workspace", exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# 由优化后的SLC工具集生成\n")
        f.write(f"# 需求: {requirement}\n")
        f.write(f"# 生成时间: {__import__('datetime').datetime.now()}\n\n")
        f.write(code)
    
    print(f"✅ 测试结果已保存到: {output_file}")
    
    # 显示文件内容
    print("\n生成的文件内容:")
    print("=" * 50)
    with open(output_file, 'r', encoding='utf-8') as f:
        print(f.read())
    print("=" * 50)

def main():
    """主函数"""
    print("SLC工具集优化测试")
    print("=" * 60)
    
    try:
        # 测试代码生成
        test_code_generation()
        
        # 测试代码重构
        test_code_refactoring()
        
        # 测试多语言生成
        test_multi_language()
        
        # 保存测试结果
        save_test_results()
        
        print("\n🎉 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Ollama 集成测试运行脚本

运行所有 Ollama 相关的测试，包括：
- 基础功能测试
- API 调用测试
- 集成测试
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from test_ollama_basic import main as basic_test
from test_ollama_api import main as api_test
from test_ollama_integration import main as integration_test


async def run_all_tests():
    """运行所有 Ollama 测试"""
    print("🚀 开始运行 Ollama 集成测试套件")
    print("=" * 60)
    print(f"⏰ 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 项目根目录: {project_root}")
    
    test_results = []
    
    # 运行基础功能测试
    print("\n" + "=" * 40)
    print("🧪 运行基础功能测试")
    print("=" * 40)
    try:
        result = await basic_test()
        test_results.append(("基础功能测试", result))
    except Exception as e:
        print(f"❌ 基础功能测试异常: {e}")
        test_results.append(("基础功能测试", False))
    
    # 运行 API 调用测试
    print("\n" + "=" * 40)
    print("🔗 运行 API 调用测试")
    print("=" * 40)
    try:
        result = await api_test()
        test_results.append(("API 调用测试", result))
    except Exception as e:
        print(f"❌ API 调用测试异常: {e}")
        test_results.append(("API 调用测试", False))
    
    # 运行集成测试
    print("\n" + "=" * 40)
    print("🔧 运行集成测试")
    print("=" * 40)
    try:
        result = await integration_test()
        test_results.append(("集成测试", result))
    except Exception as e:
        print(f"❌ 集成测试异常: {e}")
        test_results.append(("集成测试", False))
    
    # 输出测试结果摘要
    print("\n" + "=" * 60)
    print("📊 测试结果摘要")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\n📈 总体通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！Ollama 集成功能完全正常")
    elif passed >= total * 0.8:
        print("✅ 大部分测试通过，Ollama 集成功能基本正常")
    else:
        print("⚠️  部分测试失败，需要进一步检查")
    
    return passed == total


def main():
    """主函数"""
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试运行异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
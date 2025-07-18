#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from metagpt.utils.language_detector import get_language_detector

async def test_japanese_detection():
    detector = get_language_detector()
    
    # 测试日语文本
    japanese_text = "100の平方を計算してください。"
    print(f"测试文本: {japanese_text}")
    
    result = await detector.detect_language(japanese_text, use_llm=False)
    print(f"检测结果: {result.language}")
    print(f"置信度: {result.confidence}")
    print(f"方法: {result.method}")
    
    # 测试中文文本作为对比
    chinese_text = "计算100的平方。"
    print(f"\n对比文本: {chinese_text}")
    
    result2 = await detector.detect_language(chinese_text, use_llm=False)
    print(f"检测结果: {result2.language}")
    print(f"置信度: {result2.confidence}")
    print(f"方法: {result2.method}")

if __name__ == "__main__":
    asyncio.run(test_japanese_detection()) 
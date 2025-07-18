#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/07/18 08:31
@Author  : 18300676767
@File    : test_standalone_multilingual.py
@Desc    : 独立的多语言支持测试（不依赖MetaGPT其他模块）
"""

import asyncio
import re
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class LanguageDetectionResult:
    """语言检测结果"""
    language: str
    confidence: float
    method: str
    detected_text: str


class StandaloneLanguageDetector:
    """独立语言检测器"""
    
    def __init__(self):
        self.default_language = "English"
        
        # 语言映射表
        self.language_mapping = {
            "zh": "中文", "chinese": "中文", "中文": "中文",
            "en": "English", "english": "English", "English": "English",
            "ko": "한국어", "korean": "한국어", "한국어": "한국어",
            "ja": "日本語", "japanese": "日本語", "日本語": "日本語",
            "es": "Español", "spanish": "Español", "Español": "Español",
            "fr": "Français", "french": "Français", "Français": "Français",
            "de": "Deutsch", "german": "Deutsch", "Deutsch": "Deutsch",
            "it": "Italiano", "italian": "Italiano", "Italiano": "Italiano",
            "pt": "Português", "portuguese": "Português", "Português": "Português",
            "ru": "Русский", "russian": "Русский", "Русский": "Русский",
            "ar": "العربية", "arabic": "العربية", "العربية": "العربية",
            "hi": "हिन्दी", "hindi": "हिन्दी", "हिन्दी": "हिन्दी"
        }
    
    async def detect_language(self, text: str, use_llm: bool = False) -> LanguageDetectionResult:
        """
        检测文本语言
        
        [18300676767] 优化：实现多层检测策略，结合正则、模式匹配
        提供高准确度的语言识别，支持降级机制确保稳定性
        
        Args:
            text: 要检测的文本
            use_llm: 是否使用LLM检测（此版本中忽略）
            
        Returns:
            LanguageDetectionResult: 检测结果
        """
        if not text or not text.strip():
            return LanguageDetectionResult(
                language=self.default_language,
                confidence=0.0,
                method="default",
                detected_text=text
            )
        
        # 第一层：正则表达式快速检测
        regex_result = self._regex_detect(text)
        if regex_result.confidence > 0.8:
            return regex_result
        
        # 第二层：模式匹配检测
        pattern_result = self._pattern_detect(text)
        if pattern_result.confidence > 0.7:
            return pattern_result
        
        # 降级到正则检测结果
        return regex_result if regex_result.confidence > 0.5 else LanguageDetectionResult(
            language=self.default_language,
            confidence=0.1,
            method="fallback",
            detected_text=text
        )
    
    def _regex_detect(self, text: str) -> LanguageDetectionResult:
        """正则表达式检测"""
        # 中文检测
        if re.search(r'[\u4e00-\u9fff]', text):
            return LanguageDetectionResult(
                language="中文",
                confidence=0.9,
                method="regex",
                detected_text=text
            )
        
        # 韩文检测
        if re.search(r'[\uac00-\ud7af]', text):
            return LanguageDetectionResult(
                language="한국어",
                confidence=0.9,
                method="regex",
                detected_text=text
            )
        
        # 日文检测
        if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
            return LanguageDetectionResult(
                language="日本語",
                confidence=0.9,
                method="regex",
                detected_text=text
            )
        
        # 阿拉伯文检测
        if re.search(r'[\u0600-\u06ff]', text):
            return LanguageDetectionResult(
                language="العربية",
                confidence=0.9,
                method="regex",
                detected_text=text
            )
        
        # 俄文检测
        if re.search(r'[\u0400-\u04ff]', text):
            return LanguageDetectionResult(
                language="Русский",
                confidence=0.9,
                method="regex",
                detected_text=text
            )
        
        # 英文检测（包含英文字符）
        if re.search(r'[a-zA-Z]', text):
            return LanguageDetectionResult(
                language="English",
                confidence=0.8,
                method="regex",
                detected_text=text
            )
        
        return LanguageDetectionResult(
            language=self.default_language,
            confidence=0.0,
            method="regex",
            detected_text=text
        )
    
    def _pattern_detect(self, text: str) -> LanguageDetectionResult:
        """模式匹配检测"""
        patterns = {
            "中文": ["请", "帮", "设计", "系统", "架构", "分析", "需求", "实现", "功能"],
            "한국어": ["도와주세요", "설계", "시스템", "분석", "요구사항", "구현", "기능"],
            "日本語": ["お願い", "設計", "システム", "分析", "要件", "実装", "機能"],
            "Español": ["por favor", "diseñar", "sistema", "análisis", "requisitos"],
            "Français": ["s'il vous plaît", "concevoir", "système", "analyse", "exigences"],
            "Deutsch": ["bitte", "entwerfen", "system", "analyse", "anforderungen"],
            "Italiano": ["per favore", "progettare", "sistema", "analisi", "requisiti"],
            "Português": ["por favor", "projetar", "sistema", "análise", "requisitos"],
            "Русский": ["пожалуйста", "проектировать", "система", "анализ", "требования"],
            "العربية": ["من فضلك", "تصميم", "نظام", "تحليل", "متطلبات"],
            "हिन्दी": ["कृपया", "डिज़ाइन", "सिस्टम", "विश्लेषण", "आवश्यकताएं"]
        }
        
        max_matches = 0
        best_language = self.default_language
        
        for lang, keywords in patterns.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches > max_matches:
                max_matches = matches
                best_language = lang
        
        confidence = min(0.7, max_matches * 0.2) if max_matches > 0 else 0.0
        
        return LanguageDetectionResult(
            language=best_language,
            confidence=confidence,
            method="pattern",
            detected_text=text
        )


class StandaloneLanguageContext:
    """独立语言上下文管理器"""
    
    def __init__(self):
        self.current_language = "English"
        self.forced_language = None
        self.detection_result = None
        self.language_detector = StandaloneLanguageDetector()
    
    async def set_language_from_input(self, user_input: str, use_llm: bool = False) -> str:
        """
        从用户输入检测并设置语言
        
        [18300676767] 优化：集成语言检测器，实现智能语言上下文管理
        支持异步操作和错误处理，提供全局语言状态管理
        
        Args:
            user_input: 用户输入文本
            use_llm: 是否使用LLM检测
            
        Returns:
            str: 检测到的语言
        """
        try:
            # 检测语言
            detection_result = await self.language_detector.detect_language(
                user_input, use_llm=use_llm
            )
            
            # 设置语言上下文
            self.current_language = detection_result.language
            self.detection_result = detection_result
            
            print(f"检测到语言: {detection_result.language} "
                  f"(置信度: {detection_result.confidence:.2f}, "
                  f"方法: {detection_result.method})")
            
            return detection_result.language
            
        except Exception as e:
            print(f"语言检测失败: {e}")
            # 降级到默认语言
            self.current_language = "English"
            return "English"
    
    def set_forced_language(self, language: str) -> None:
        """强制设置语言"""
        self.forced_language = language
        self.current_language = language
        print(f"强制设置语言: {language}")
    
    def get_current_language(self) -> str:
        """获取当前语言"""
        # 如果有强制语言，优先使用
        if self.forced_language:
            return self.forced_language
        
        return self.current_language
    
    def get_confidence(self) -> float:
        """获取语言检测置信度"""
        if self.detection_result:
            return self.detection_result.confidence
        return 0.0


def render_prompt_with_language(prompt_template: str, current_language: str, **kwargs) -> str:
    """
    渲染提示词，自动注入语言变量
    
    Args:
        prompt_template: 提示词模板
        current_language: 当前语言
        **kwargs: 其他变量
        
    Returns:
        str: 渲染后的提示词
    """
    # 确保模板包含语言变量
    if "{language}" not in prompt_template:
        prompt_template += " Please respond in {language}."
    
    # 渲染模板
    return prompt_template.format(language=current_language, **kwargs)


async def test_basic_language_detection():
    """测试基本语言检测功能"""
    print("=" * 50)
    print("测试基本语言检测功能")
    print("=" * 50)
    
    detector = StandaloneLanguageDetector()
    
    test_cases = [
        "请帮我设计一个系统架构",
        "Please help me design a system architecture",
        "시스템 아키텍처를 설계하는 데 도움을 주세요",
        "システムアーキテクチャの設計を手伝ってください",
        "Por favor, ayúdame a diseñar una arquitectura de sistema",
        "S'il vous plaît, aidez-moi à concevoir une architecture système"
    ]
    
    for text in test_cases:
        print(f"\n输入文本: {text}")
        result = await detector.detect_language(text, use_llm=False)
        print(f"检测结果: {result.language} (置信度: {result.confidence:.2f}, 方法: {result.method})")


async def test_prompt_rendering():
    """测试提示词渲染功能"""
    print("\n" + "=" * 50)
    print("测试提示词渲染功能")
    print("=" * 50)
    
    context = StandaloneLanguageContext()
    
    # 测试不同语言
    languages = ["中文", "English", "한국어"]
    
    for lang in languages:
        print(f"\n--- 设置语言: {lang} ---")
        context.set_forced_language(lang)
        
        # 测试提示词渲染
        prompt_template = "Please analyze the requirements and create a detailed plan."
        rendered = render_prompt_with_language(prompt_template, context.get_current_language())
        print(f"原始模板: {prompt_template}")
        print(f"渲染后: {rendered}")
        
        # 测试带变量的模板
        prompt_template2 = "Write code based on the following specification: {spec}"
        rendered2 = render_prompt_with_language(prompt_template2, context.get_current_language(), spec="用户需求")
        print(f"带变量模板: {prompt_template2}")
        print(f"渲染后: {rendered2}")


async def test_language_context():
    """测试语言上下文管理"""
    print("\n" + "=" * 50)
    print("测试语言上下文管理")
    print("=" * 50)
    
    context = StandaloneLanguageContext()
    
    # 测试从输入设置语言
    test_inputs = [
        "请帮我写一个Python函数",
        "Write a Python function for me",
        "Python 함수를 작성해 주세요"
    ]
    
    for text in test_inputs:
        print(f"\n输入: {text}")
        detected_lang = await context.set_language_from_input(text, use_llm=False)
        print(f"检测到的语言: {detected_lang}")
        print(f"当前语言: {context.get_current_language()}")
        print(f"置信度: {context.get_confidence():.2f}")


async def main():
    """主测试函数"""
    print("开始测试独立多语言支持功能")
    print("=" * 60)
    
    try:
        # 测试基本语言检测
        await test_basic_language_detection()
        
        # 测试提示词渲染
        await test_prompt_rendering()
        
        # 测试语言上下文管理
        await test_language_context()
        
        print("\n" + "=" * 60)
        print("独立测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/07/18 08:31
@Author  : 18300676767
@File    : language_detector.py
@Desc    : 语言检测模块，使用MetaGPT内置LLM机制
"""

import re
from typing import Optional, Dict, List
from dataclasses import dataclass

from metagpt.llm import LLM
from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.logs import logger


@dataclass
class LanguageDetectionResult:
    """语言检测结果"""
    language: str
    confidence: float
    method: str
    detected_text: str


class LanguageDetector:
    """语言检测器，使用MetaGPT内置LLM机制"""
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        self.llm = LLM(llm_config) if llm_config else LLM()
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
    
    async def detect_language(self, text: str, use_llm: bool = True) -> LanguageDetectionResult:
        """
        检测文本语言
        
        Args:
            text: 要检测的文本
            use_llm: 是否使用LLM检测
            
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
        
        # 第三层：LLM语义检测（如果启用）
        if use_llm:
            try:
                llm_result = await self._llm_semantic_detect(text)
                if llm_result.confidence > 0.6:
                    return llm_result
            except Exception as e:
                logger.warning(f"LLM语言检测失败: {e}")
        
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
    
    async def _llm_semantic_detect(self, text: str) -> LanguageDetectionResult:
        """使用LLM进行语义语言检测"""
        prompt = f"""
请分析以下文本的主要表达语言，考虑语义和表达习惯。

文本：{text}

请只返回语言名称，如：中文、English、한국어、日本語、Español、Français等。
不要包含任何其他内容，只返回语言名称。
"""
        
        try:
            response = await self.llm.acompletion([{"role": "user", "content": prompt}])
            
            # 处理不同类型的响应
            if isinstance(response, dict):
                detected_lang = response.get('content', '') or response.get('choices', [{}])[0].get('message', {}).get('content', '')
            elif isinstance(response, str):
                detected_lang = response
            else:
                detected_lang = str(response) if response else ""
            
            detected_lang = detected_lang.strip()
            
            # 标准化语言名称
            normalized_lang = self._normalize_language(detected_lang)
            
            return LanguageDetectionResult(
                language=normalized_lang,
                confidence=0.95,
                method="llm",
                detected_text=text
            )
        except Exception as e:
            logger.error(f"LLM语言检测异常: {e}")
            raise
    
    def _normalize_language(self, language: str) -> str:
        """标准化语言名称"""
        # 清理和标准化
        lang = language.strip().lower()
        
        # 查找映射
        for key, value in self.language_mapping.items():
            if key.lower() == lang:
                return value
        
        # 如果没有找到映射，返回原值或默认值
        return language if language in self.language_mapping.values() else self.default_language
    
    def get_language_name(self, lang_code: str) -> str:
        """获取语言名称"""
        return self.language_mapping.get(lang_code, lang_code)


# 全局语言检测器实例
_language_detector = None

def get_language_detector(llm_config: Optional[LLMConfig] = None) -> LanguageDetector:
    """获取全局语言检测器实例"""
    global _language_detector
    if _language_detector is None:
        _language_detector = LanguageDetector(llm_config)
    return _language_detector 
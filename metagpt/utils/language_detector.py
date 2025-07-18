#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/07/18 08:31
@Author  : 18300676767
@File    : language_detector.py
@Desc    : 语言检测模块，使用字符级别的检测方法
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
    """语言检测器，使用字符级别的检测方法"""
    
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
        
        # 字符级别的语言检测规则
        self.char_patterns = {
            "中文": {
                "chars": r'[\u4e00-\u9fff]',  # 汉字
                "weight": 1.0
            },
            "日本語": {
                "chars": r'[\u3040-\u309f\u30a0-\u30ff]',  # 平假名和片假名
                "weight": 1.0
            },
            "한국어": {
                "chars": r'[\uac00-\ud7af]',  # 韩文
                "weight": 1.0
            },
            "English": {
                "chars": r'[a-zA-Z]',  # 英文字母
                "weight": 0.8
            },
            "Русский": {
                "chars": r'[\u0400-\u04ff]',  # 俄文
                "weight": 1.0
            },
            "العربية": {
                "chars": r'[\u0600-\u06ff]',  # 阿拉伯文
                "weight": 1.0
            }
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
        
        # 第一层：字符级别的检测
        char_result = self._char_level_detect(text)
        
        # 如果字符检测置信度很高，直接返回
        if char_result.confidence > 0.7:
            return char_result
        
        # 第二层：LLM语义检测（如果启用且字符检测置信度较低）
        if use_llm and char_result.confidence < 0.5:
            try:
                llm_result = await self._llm_semantic_detect(text)
                if llm_result.confidence > 0.6:
                    return llm_result
            except Exception as e:
                logger.warning(f"LLM语言检测失败: {e}")
        
        # 返回字符检测结果
        return char_result if char_result.confidence > 0.3 else LanguageDetectionResult(
            language=self.default_language,
            confidence=0.1,
            method="fallback",
            detected_text=text
        )
    
    def _char_level_detect(self, text: str) -> LanguageDetectionResult:
        """字符级别的语言检测"""
        language_scores = {}
        total_chars = len(text)
        
        if total_chars == 0:
            return LanguageDetectionResult(
                language=self.default_language,
                confidence=0.0,
                method="char_level",
                detected_text=text
            )
        
        # 计算每种语言的字符匹配度
        for lang, pattern_info in self.char_patterns.items():
            pattern = pattern_info["chars"]
            weight = pattern_info["weight"]
            
            # 计算匹配的字符数量
            matches = len(re.findall(pattern, text))
            score = (matches / total_chars) * weight if total_chars > 0 else 0
            language_scores[lang] = score
        
        # 找到得分最高的语言
        if language_scores:
            best_language = max(language_scores.items(), key=lambda x: x[1])[0]
            best_score = language_scores[best_language]
            
            # 计算置信度
            confidence = min(0.95, best_score * 2)  # 将得分转换为置信度
            
            # 如果最高得分很低，可能是混合语言或未知语言
            if best_score < 0.3:
                confidence = best_score
            
            return LanguageDetectionResult(
                language=best_language,
                confidence=confidence,
                method="char_level",
                detected_text=text
            )
        
        return LanguageDetectionResult(
            language=self.default_language,
            confidence=0.0,
            method="char_level",
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
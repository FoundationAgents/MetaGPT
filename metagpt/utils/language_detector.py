#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/07/18 08:31
@Author  : 18300676767
@File    : language_detector.py
@Desc    : Language detection module using character-level detection methods
"""

import re
from typing import Optional, Dict, List
from dataclasses import dataclass

from metagpt.llm import LLM
from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.logs import logger


@dataclass
class LanguageDetectionResult:
    """Language detection result"""
    language: str
    confidence: float
    method: str
    detected_text: str


class LanguageDetector:
    """Language detector using character-level detection methods"""
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        self.llm = LLM(llm_config) if llm_config else LLM()
        self.default_language = "English"
        
        # Language mapping table
        self.language_mapping = {
            "zh": "Chinese", "chinese": "Chinese", "Chinese": "Chinese",
            "en": "English", "english": "English", "English": "English",
            "ko": "한국어", "korean": "한국어", "한국어": "한국어",
            "ja": "Japanese", "japanese": "Japanese", "Japanese": "Japanese",
            "es": "Español", "spanish": "Español", "Español": "Español",
            "fr": "Français", "french": "Français", "Français": "Français",
            "de": "Deutsch", "german": "Deutsch", "Deutsch": "Deutsch",
            "it": "Italiano", "italian": "Italiano", "Italiano": "Italiano",
            "pt": "Português", "portuguese": "Português", "Português": "Português",
            "ru": "Русский", "russian": "Русский", "Русский": "Русский",
            "ar": "العربية", "arabic": "العربية", "العربية": "العربية",
            "hi": "हिन्दी", "hindi": "हिन्दी", "हिन्दी": "हिन्दी"
        }
        
        # Character-level language detection rules
        self.char_patterns = {
            "Chinese": {
                "chars": r'[\u4e00-\u9fff]',  # Chinese characters
                "weight": 1.0
            },
            "Japanese": {
                "chars": r'[\u3040-\u309f\u30a0-\u30ff]',  # Hiragana and Katakana
                "weight": 1.0
            },
            "한국어": {
                "chars": r'[\uac00-\ud7af]',  # Korean
                "weight": 1.0
            },
            "English": {
                "chars": r'[a-zA-Z]',  # English letters
                "weight": 0.8
            },
            "Русский": {
                "chars": r'[\u0400-\u04ff]',  # Russian
                "weight": 1.0
            },
            "العربية": {
                "chars": r'[\u0600-\u06ff]',  # Arabic
                "weight": 1.0
            }
        }
    
    async def detect_language(self, text: str, use_llm: bool = True) -> LanguageDetectionResult:
        """
        Detect text language
        
        Args:
            text: Text to detect
            use_llm: Whether to use LLM detection
            
        Returns:
            LanguageDetectionResult: Detection result
        """
        if not text or not text.strip():
            return LanguageDetectionResult(
                language=self.default_language,
                confidence=0.0,
                method="default",
                detected_text=text
            )
        
        # Layer 1: Character-level detection
        char_result = self._char_level_detect(text)
        
        # If character detection confidence is high, return directly
        if char_result.confidence > 0.7:
            return char_result
        
        # Layer 2: LLM semantic detection (if enabled and character detection confidence is low)
        if use_llm and char_result.confidence < 0.5:
            try:
                llm_result = await self._llm_semantic_detect(text)
                if llm_result.confidence > 0.6:
                    return llm_result
            except Exception as e:
                logger.warning(f"LLM language detection failed: {e}")
        
        # Return character detection result
        return char_result if char_result.confidence > 0.3 else LanguageDetectionResult(
            language=self.default_language,
            confidence=0.1,
            method="fallback",
            detected_text=text
        )
    
    def _char_level_detect(self, text: str) -> LanguageDetectionResult:
        """Character-level language detection"""
        language_scores = {}
        total_chars = len(text)
        
        if total_chars == 0:
            return LanguageDetectionResult(
                language=self.default_language,
                confidence=0.0,
                method="char_level",
                detected_text=text
            )
        
        # Calculate character matching degree for each language
        for lang, pattern_info in self.char_patterns.items():
            pattern = pattern_info["chars"]
            weight = pattern_info["weight"]
            
            # Calculate the number of matching characters
            matches = len(re.findall(pattern, text))
            score = (matches / total_chars) * weight if total_chars > 0 else 0
            language_scores[lang] = score
        
        # Find the language with the highest score
        if language_scores:
            best_language = max(language_scores.items(), key=lambda x: x[1])[0]
            best_score = language_scores[best_language]
            
            # Calculate confidence
            confidence = min(0.95, best_score * 2)  # Convert score to confidence
            
            # If the highest score is low, it might be mixed language or unknown language
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
        """Use LLM for semantic language detection"""
        prompt = f"""
Please analyze the main expression language of the following text, considering semantics and expression habits.

Text:{text}

Please only return the language name, such as: Chinese, English, Korean, Japanese, Spanish, French, etc.
Do not include any other content, only return the language name.
"""
        
        try:
            response = await self.llm.acompletion([{"role": "user", "content": prompt}])
            
            # Handle different types of responses
            if isinstance(response, dict):
                detected_lang = response.get('content', '') or response.get('choices', [{}])[0].get('message', {}).get('content', '')
            elif isinstance(response, str):
                detected_lang = response
            else:
                detected_lang = str(response) if response else ""
            
            detected_lang = detected_lang.strip()
            
            # Standardize language names
            normalized_lang = self._normalize_language(detected_lang)
            
            return LanguageDetectionResult(
                language=normalized_lang,
                confidence=0.95,
                method="llm",
                detected_text=text
            )
        except Exception as e:
            logger.error(f"LLM language detection exception: {e}")
            raise
    
    def _normalize_language(self, language: str) -> str:
        """Standardize language names"""
        # Clean and standardize
        lang = language.strip().lower()
        
        # Find mapping
        for key, value in self.language_mapping.items():
            if key.lower() == lang:
                return value
        
        # If no mapping is found, return the original value or default value
        return language if language in self.language_mapping.values() else self.default_language
    
    def get_language_name(self, lang_code: str) -> str:
        """Get language name"""
        return self.language_mapping.get(lang_code, lang_code)


# Global language detector instance
_language_detector = None

def get_language_detector(llm_config: Optional[LLMConfig] = None) -> LanguageDetector:
    """Get global language detector instance"""
    global _language_detector
    if _language_detector is None:
        _language_detector = LanguageDetector(llm_config)
    return _language_detector 
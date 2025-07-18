#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/07/18 08:31
@Author  : 18300676767
@File    : language_context.py
@Desc    : 全局语言上下文管理
"""

import asyncio
from typing import Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager

from metagpt.configs.llm_config import LLMConfig
from metagpt.logs import logger
from metagpt.utils.language_detector import get_language_detector, LanguageDetectionResult


@dataclass
class LanguageContext:
    """语言上下文"""
    current_language: str = "English"
    forced_language: Optional[str] = None
    detection_result: Optional[LanguageDetectionResult] = None
    use_llm_detection: bool = True
    confidence_threshold: float = 0.6


class GlobalLanguageContext:
    """全局语言上下文管理器"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.context = LanguageContext()
            self.language_detector = get_language_detector()
            self.initialized = True
    
    async def set_language_from_input(self, user_input: str, use_llm: bool = True) -> str:
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
        async with self._lock:
            try:
                # 检测语言
                detection_result = await self.language_detector.detect_language(
                    user_input, use_llm=use_llm
                )
                
                # 设置语言上下文
                self.context.current_language = detection_result.language
                self.context.detection_result = detection_result
                self.context.use_llm_detection = use_llm
                
                logger.info(f"检测到语言: {detection_result.language} "
                          f"(置信度: {detection_result.confidence:.2f}, "
                          f"方法: {detection_result.method})")
                
                return detection_result.language
                
            except Exception as e:
                logger.error(f"语言检测失败: {e}")
                # 降级到默认语言
                self.context.current_language = "English"
                return "English"
    
    def set_forced_language(self, language: str) -> None:
        """
        强制设置语言
        
        Args:
            language: 要设置的语言
        """
        self.context.forced_language = language
        self.context.current_language = language
        logger.info(f"强制设置语言: {language}")
    
    def get_current_language(self) -> str:
        """
        获取当前语言
        
        Returns:
            str: 当前语言
        """
        # 如果有强制语言，优先使用
        if self.context.forced_language:
            return self.context.forced_language
        
        return self.context.current_language
    
    def get_detection_result(self) -> Optional[LanguageDetectionResult]:
        """
        获取语言检测结果
        
        Returns:
            LanguageDetectionResult: 检测结果
        """
        return self.context.detection_result
    
    def reset_to_default(self) -> None:
        """重置为默认语言"""
        self.context.current_language = "English"
        self.context.forced_language = None
        self.context.detection_result = None
        logger.info("重置语言为默认值: English")
    
    def is_forced_language(self) -> bool:
        """是否使用强制语言"""
        return self.context.forced_language is not None
    
    def get_confidence(self) -> float:
        """获取语言检测置信度"""
        if self.context.detection_result:
            return self.context.detection_result.confidence
        return 0.0


# 全局语言上下文实例
_global_language_context = None

def get_global_language_context() -> GlobalLanguageContext:
    """获取全局语言上下文实例"""
    global _global_language_context
    if _global_language_context is None:
        _global_language_context = GlobalLanguageContext()
    return _global_language_context


@asynccontextmanager
async def language_context(language: Optional[str] = None, forced: bool = False):
    """
    语言上下文管理器
    
    Args:
        language: 要设置的语言
        forced: 是否强制设置
        
    Usage:
        async with language_context("中文"):
            # 在这个上下文中，所有提示词都会使用中文
            pass
    """
    context = get_global_language_context()
    
    if language:
        if forced:
            context.set_forced_language(language)
        else:
            await context.set_language_from_input(language)
    
    try:
        yield context
    finally:
        if forced:
            # 恢复之前的设置
            context.reset_to_default()


def render_prompt_with_language(prompt_template: str, **kwargs) -> str:
    """
    渲染提示词，自动注入语言变量
    
    Args:
        prompt_template: 提示词模板
        **kwargs: 其他变量
        
    Returns:
        str: 渲染后的提示词
    """
    context = get_global_language_context()
    current_language = context.get_current_language()
    
    # 确保模板包含语言变量
    if "{language}" not in prompt_template:
        prompt_template += " Please respond in {language}."
    
    # 渲染模板
    return prompt_template.format(language=current_language, **kwargs)


async def process_user_input_for_language(user_input: str, forced_language: Optional[str] = None) -> str:
    """
    处理用户输入，检测并设置语言
    
    Args:
        user_input: 用户输入
        forced_language: 强制语言
        
    Returns:
        str: 检测到的语言
    """
    context = get_global_language_context()
    
    if forced_language:
        context.set_forced_language(forced_language)
        return forced_language
    else:
        return await context.set_language_from_input(user_input)


# 便捷函数
def get_current_language() -> str:
    """获取当前语言"""
    return get_global_language_context().get_current_language()


def set_language(language: str, forced: bool = False) -> None:
    """设置语言"""
    context = get_global_language_context()
    if forced:
        context.set_forced_language(language)
    else:
        # 异步调用需要特殊处理
        asyncio.create_task(context.set_language_from_input(language))


def reset_language() -> None:
    """重置语言"""
    get_global_language_context().reset_to_default() 
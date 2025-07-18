#!/usr/bin/env python3
"""
Script to translate Chinese comments and strings to English in code files.
This ensures the code follows open source conventions.
"""

import os
import re
from pathlib import Path

# Chinese to English translation mapping
TRANSLATIONS = {
    # Comments and docstrings
    "修复 Ollama API 响应解析，支持多行 JSON 流式响应": "Fix Ollama API response parsing, support multi-line JSON streaming responses",
    "获取原始数据": "Get raw data",
    "移除可能的 BOM 标记": "Remove possible BOM markers",
    "处理多行 JSON（流式响应）": "Process multi-line JSON (streaming responses)",
    "跳过 SSE 格式的 \"data: \" 前缀": "Skip SSE format \"data: \" prefix",
    "跳过结束标记": "Skip end markers",
    "尝试解析每一行 JSON": "Try to parse each line of JSON",
    "如果单行解析失败，可能是部分数据，跳过": "If single line parsing fails, it might be partial data, skip",
    "如果有多个 JSON 对象，返回最后一个（通常是完整的响应）": "If there are multiple JSON objects, return the last one (usually the complete response)",
    "如果没有成功解析的 JSON，尝试解析整个数据": "If no JSON was successfully parsed, try to parse the entire data",
    
    # Error messages and logs
    "如果所有解析都失败，返回错误信息": "If all parsing fails, return error message",
    "Ollama API 响应解析失败": "Ollama API response parsing failed",
    "原始数据": "Raw data",
    "JSON 解析失败": "JSON parsing failed",
    "Ollama API 响应解析完全失败": "Ollama API response parsing completely failed",
    "响应解析失败": "Response parsing failed",
    "优先处理异常响应": "Prioritize handling exception responses",
    "返回错误信息和部分原始数据": "Return error message and partial raw data",
    "正常响应": "Normal response",
    "兜底返回全部内容": "Fallback to return all content",
    
    # Language detector
    "语言检测模块，使用字符级别的检测方法": "Language detection module using character-level detection methods",
    "语言检测结果": "Language detection result",
    "语言检测器，使用字符级别的检测方法": "Language detector using character-level detection methods",
    "语言映射表": "Language mapping table",
    "字符级别的语言检测规则": "Character-level language detection rules",
    "汉字": "Chinese characters",
    "平假名和片假名": "Hiragana and Katakana",
    "韩文": "Korean characters",
    "英文字母": "English letters",
    "俄文": "Russian characters",
    "阿拉伯文": "Arabic characters",
    
    # Function docstrings and comments
    "检测文本语言": "Detect text language",
    "要检测的文本": "Text to detect",
    "是否使用LLM检测": "Whether to use LLM detection",
    "检测结果": "Detection result",
    "第一层：字符级别的检测": "Layer 1: Character-level detection",
    "如果字符检测置信度很高，直接返回": "If character detection confidence is high, return directly",
    "第二层：LLM语义检测（如果启用且字符检测置信度较低）": "Layer 2: LLM semantic detection (if enabled and character detection confidence is low)",
    "LLM语言检测失败": "LLM language detection failed",
    "返回字符检测结果": "Return character detection result",
    "字符级别的语言检测": "Character-level language detection",
    "计算每种语言的字符匹配度": "Calculate character matching degree for each language",
    "返回字符Detection result": "Return character detection result",
    "计算匹配的字符数量": "Calculate the number of matching characters",
    "找到得分最高的语言": "Find the language with the highest score",
    "计算置信度": "Calculate confidence",
    "将得分转换为置信度": "Convert score to confidence",
    "如果最高得分很低，可能是混合语言或未知语言": "If the highest score is low, it might be mixed language or unknown language",
    "使用LLM进行语义语言检测": "Use LLM for semantic language detection",
    "请分析以下文本的主要表达语言，考虑语义和表达习惯。": "Please analyze the main expression language of the following text, considering semantics and expression habits.",
    "文本：": "Text:",
    "请只返回语言名称，如：Chinese、English、한국어、Japanese、Español、Français等。": "Please only return the language name, such as: Chinese, English, Korean, Japanese, Spanish, French, etc.",
    "不要包含任何其他内容，只返回语言名称。": "Do not include any other content, only return the language name.",
    "处理不同类型的响应": "Handle different types of responses",
    "标准化语言名称": "Standardize language names",
    "LLM语言检测异常": "LLM language detection exception",
    "清理和标准化": "Clean and standardize",
    "查找映射": "Find mapping",
    "如果没有找到映射，返回原值或默认值": "If no mapping is found, return the original value or default value",
    "获取语言名称": "Get language name",
    "全局语言检测器实例": "Global language detector instance",
    "获取全局语言检测器实例": "Get global language detector instance",
    
    # Common patterns
    "中文": "Chinese",
    "日本語": "Japanese",
    "韩文": "Korean",
    "英文": "English",
    "俄文": "Russian",
    "阿拉伯文": "Arabic",
}

def translate_file(file_path):
    """Translate Chinese text to English in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace Chinese text with English
        for chinese, english in TRANSLATIONS.items():
            content = content.replace(chinese, english)
        
        # If content changed, write back to file
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Translated: {file_path}")
            return True
        else:
            print(f"⏭️  No changes: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all Python files."""
    # Directories to process
    directories = [
        "metagpt/provider",
        "metagpt/utils", 
        "metagpt/tools/libs",
        "tests/metagpt/provider/ollama_integration",
        "tests/multilingual"
    ]
    
    total_files = 0
    translated_files = 0
    
    for directory in directories:
        if os.path.exists(directory):
            for file_path in Path(directory).rglob("*.py"):
                total_files += 1
                if translate_file(file_path):
                    translated_files += 1
    
    print(f"\n📊 Summary:")
    print(f"Total files processed: {total_files}")
    print(f"Files translated: {translated_files}")
    print(f"Files unchanged: {total_files - translated_files}")

if __name__ == "__main__":
    main() 
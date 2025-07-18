#!/usr/bin/env python3
"""
SLC (Software Lifecycle) 工具集
提供基于 Ollama 的代码生成、重构、分析等功能
"""

import requests
import json
import yaml
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OllamaConfig:
    """Ollama 配置类"""
    model: str = "qwen2.5:7b"
    base_url: str = "http://127.0.0.1:11434"
    timeout: int = 600
    temperature: float = 0.1
    
    @classmethod
    def from_config_file(cls, config_path: Optional[str] = None) -> 'OllamaConfig':
        """从配置文件加载配置"""
        if config_path is None:
            # 尝试多个可能的配置文件路径
            possible_paths = [
                Path(__file__).parent.parent.parent.parent / "config2.yaml",
                Path(__file__).parent.parent.parent.parent / "config" / "config2.yaml",
                Path.cwd() / "config2.yaml",
                Path.cwd() / "config" / "config2.yaml"
            ]
            
            for path in possible_paths:
                if path.exists():
                    config_path = str(path)
                    break
            else:
                # 如果都找不到，使用默认配置
                logger.warning("未找到配置文件，使用默认配置")
                return cls()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            
            llm_config = config.get('llm', {})
            return cls(
                model=llm_config.get('model', 'qwen2.5:7b'),
                base_url=llm_config.get('base_url', 'http://127.0.0.1:11434'),
                timeout=llm_config.get('timeout', 600),
                temperature=llm_config.get('temperature', 0.1)
            )
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}，使用默认配置")
            return cls()

# 全局配置实例
ollama_config = OllamaConfig.from_config_file()

async def call_ollama(prompt: str, temperature: Optional[float] = None, 
                model: Optional[str] = None, timeout: Optional[int] = None) -> str:
    """
    调用 Ollama API（使用MetaGPT内置机制）
    
    Args:
        prompt: 提示词
        temperature: 温度参数
        model: 模型名称
        timeout: 超时时间
    
    Returns:
        API 响应内容
    """
    try:
        from metagpt.llm import LLM
        from metagpt.configs.llm_config import LLMConfig, LLMType
        
        # 使用MetaGPT内置的LLM机制
        config = LLMConfig(
            api_type=LLMType.OLLAMA,
            base_url=ollama_config.base_url,
            model=model if model is not None else ollama_config.model,
            temperature=temperature if temperature is not None else ollama_config.temperature,
            timeout=timeout if timeout is not None else ollama_config.timeout
        )
        
        llm = LLM(config)
        response = await llm.acompletion([{"role": "user", "content": prompt}])
        # Handle different types of responses
        if isinstance(response, dict):
            return response.get('content', '') or response.get('choices', [{}])[0].get('message', {}).get('content', '')
        elif isinstance(response, str):
            return response
        else:
            return str(response) if response else ""
        
    except Exception as e:
        logger.error(f"Ollama API 调用异常: {e}")
        return f"API 调用异常: {e}"

class CodeGenerationTool:
    """代码生成工具类"""
    
    @staticmethod
    def _clean_generated_code(raw_response: str) -> str:
        """
        清理AI生成的代码，移除markdown标记和多余说明
        
        Args:
            raw_response: AI原始响应
            
        Returns:
            清理后的纯代码
        """
        if not raw_response:
            return ""
        
        # 移除开头的markdown代码块标记
        lines = raw_response.split('\n')
        cleaned_lines = []
        in_code_block = False
        skip_next = False
        
        for i, line in enumerate(lines):
            # 跳过markdown代码块开始标记
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    skip_next = True
                    continue
                else:
                    in_code_block = False
                    break
            
            # 跳过代码块结束后的内容
            if not in_code_block:
                continue
                
            # 跳过第一行（通常是语言标识）
            if skip_next:
                skip_next = False
                continue
                
            cleaned_lines.append(line)
        
        # 如果没有找到代码块标记，尝试其他清理方法
        if not cleaned_lines:
            # 移除常见的说明文字
            response = raw_response
            # 移除"使用示例"、"备注"等说明部分
            for marker in ['### 使用示例：', '### 备注：', '### 说明：', '使用示例：', '备注：', '说明：']:
                if marker in response:
                    response = response.split(marker)[0]
            
            # 移除最后的说明文字（通常在代码后）
            code_end_markers = ['###', '---', '**注意**', '**说明**']
            for marker in code_end_markers:
                if marker in response:
                    response = response.split(marker)[0]
            
            cleaned_lines = response.split('\n')
        
        # 移除末尾的空行
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines)
    
    @staticmethod
    async def generate_code(requirement: str, language: str = "python") -> str:
        """
        生成代码
        
        [18300676767] 优化：重构为使用MetaGPT内置LLM机制，替代直接Ollama API调用
        统一错误处理和响应解析，提升代码质量和可维护性
        
        Args:
            requirement: 需求描述
            language: 编程语言
            
        Returns:
            str: 生成的代码
        """
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        prompt = f"""
请用 {language} 实现以下需求：{requirement}

要求：
1. 代码要完整可运行
2. 包含必要的注释
3. 遵循最佳实践
4. 处理异常情况
5. 只返回纯代码，不要包含任何说明文字、使用示例或备注
6. 不要使用markdown代码块标记
7. 代码应该是可以直接复制粘贴运行的

请直接返回代码，不要任何其他内容。
"""
        raw_response = await call_ollama(prompt, temperature=0.1)
        return CodeGenerationTool._clean_generated_code(raw_response)
    
    @staticmethod
    async def refactor_code(code: str, instruction: str) -> str:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        prompt = f"""
请根据以下指令重构代码：

原始代码：
{code}

重构指令：{instruction}

要求：
1. 保持原有功能
2. 提高代码质量
3. 优化性能
4. 增强可读性
5. 遵循最佳实践
6. 只返回重构后的代码，不要包含任何说明文字
7. 不要使用markdown代码块标记

请直接返回重构后的代码，不要任何其他内容。
"""
        raw_response = await call_ollama(prompt, temperature=0.1)
        return CodeGenerationTool._clean_generated_code(raw_response)

class CodeUnderstandingTool:
    """代码理解工具类"""
    
    @staticmethod
    async def analyze_structure(project_path: str) -> str:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        prompt = f"""
请分析项目 {project_path} 的源码结构，包括：
1. 主要模块和功能
2. 核心类和它们的作用
3. 文件组织架构
4. 依赖关系
5. 设计模式使用情况

请用Chinese详细描述项目结构。
"""
        return await call_ollama(prompt)
    
    @staticmethod
    async def explain_code(code: str) -> str:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        prompt = f"""
请详细解释以下代码的功能和逻辑：

```python
{code}
```

请包括：
1. 代码的主要功能
2. 关键逻辑说明
3. 重要变量和函数的作用
4. 可能的改进建议
"""
        return await call_ollama(prompt)

class BatchFileTool:
    """批量文件操作工具类"""
    
    @staticmethod
    def batch_rename(directory: str, pattern: str, new_pattern: str) -> List[str]:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        renamed_files = []
        try:
            for file_path in Path(directory).glob(pattern):
                new_name = new_pattern.format(
                    stem=file_path.stem,
                    suffix=file_path.suffix,
                    name=file_path.name
                )
                new_path = file_path.parent / new_name
                file_path.rename(new_path)
                renamed_files.append(str(new_path))
        except Exception as e:
            logger.error(f"批量重命名失败: {e}")
        
        return renamed_files
    
    @staticmethod
    def batch_replace_content(directory: str, pattern: str, 
                            old_text: str, new_text: str) -> List[str]:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        modified_files = []
        try:
            for file_path in Path(directory).glob(pattern):
                if file_path.is_file():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if old_text in content:
                        content = content.replace(old_text, new_text)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        modified_files.append(str(file_path))
        except Exception as e:
            logger.error(f"批量替换内容失败: {e}")
        
        return modified_files

class EnvManagerTool:
    """环境管理工具类"""
    
    @staticmethod
    def generate_requirements(project_path: str) -> str:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        try:
            result = subprocess.run(
                ['pip', 'freeze'], 
                capture_output=True, 
                text=True, 
                timeout=30,
                cwd=project_path
            )
            if result.returncode == 0:
                return result.stdout
            else:
                return "无法生成 requirements.txt"
        except Exception as e:
            return f"生成失败: {e}"
    
    @staticmethod
    def check_dependencies(requirements_file: str) -> Dict[str, str]:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        status = {}
        try:
            with open(requirements_file, 'r') as f:
                requirements = f.readlines()
            
            for req in requirements:
                req = req.strip()
                if req and not req.startswith('#'):
                    try:
                        subprocess.run(
                            ['pip', 'show', req.split('==')[0]], 
                            capture_output=True, 
                            check=True
                        )
                        status[req] = "已安装"
                    except subprocess.CalledProcessError:
                        status[req] = "未安装"
        except Exception as e:
            logger.error(f"检查依赖项失败: {e}")
        
        return status

class SmartQATool:
    """智能问答工具类"""
    
    @staticmethod
    async def smart_qa(question: str, language: str = "python") -> str:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        prompt = f"""
请回答以下关于 {language} 编程的问题：

{question}

要求：
1. 回答要准确详细
2. 提供代码示例
3. 解释关键概念
4. 给出最佳实践建议
"""
        return await call_ollama(prompt)
    
    @staticmethod
    async def code_review(code: str) -> str:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        prompt = f"""
请对以下代码进行审查：

```python
{code}
```

请从以下方面进行审查：
1. 代码质量
2. 性能优化
3. 安全性
4. 可读性
5. 最佳实践
6. 潜在问题
7. 改进建议
"""
        return await call_ollama(prompt)

class MultiLanguageTool:
    """多语言支持工具类"""
    
    @staticmethod
    async def translate_code(code: str, from_lang: str, to_lang: str) -> str:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        prompt = f"""
请将以下 {from_lang} 代码转换为 {to_lang}：

{code}

要求：
1. 保持原有功能
2. 使用目标语言的最佳实践
3. 添加必要的注释
4. 处理语言特定的差异
5. 只返回转换后的代码，不要包含任何说明文字
6. 不要使用markdown代码块标记

请直接返回转换后的代码，不要任何其他内容。
"""
        raw_response = await call_ollama(prompt, temperature=0.1)
        return CodeGenerationTool._clean_generated_code(raw_response)
    
    @staticmethod
    async def generate_multi_language_example(requirement: str, 
                                      languages: List[str]) -> Dict[str, str]:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        examples = {}
        for lang in languages:
            prompt = f"""
请用 {lang} 实现以下需求：{requirement}

要求：
1. 代码要完整可运行
2. 包含必要的注释
3. 遵循 {lang} 的最佳实践
4. 处理异常情况
5. 只返回纯代码，不要包含任何说明文字
6. 不要使用markdown代码块标记

请直接返回代码，不要任何其他内容。
"""
            raw_response = await call_ollama(prompt, temperature=0.1)
            examples[lang] = CodeGenerationTool._clean_generated_code(raw_response)
        
        return examples

# 导出主要函数和类
__all__ = [
    'call_ollama',
    'ollama_config',
    'OllamaConfig',
    'CodeGenerationTool',
    'CodeUnderstandingTool',
    'BatchFileTool',
    'EnvManagerTool',
    'SmartQATool',
    'MultiLanguageTool'
] 
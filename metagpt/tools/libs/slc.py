#!/usr/bin/env python3
"""
SLC (Software Lifecycle) Toolset
Provides code generation, refactoring, analysis and other functions based on Ollama
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OllamaConfig:
    """Ollama configuration class"""
    model: str = "qwen2.5:7b"
    base_url: str = "http://127.0.0.1:11434"
    timeout: int = 600
    temperature: float = 0.1
    
    @classmethod
    def from_config_file(cls, config_path: Optional[str] = None) -> 'OllamaConfig':
        """Load configuration from config file"""
        if config_path is None:
            # Try multiple possible config file paths
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
                # If none found, use default configuration
                logger.warning("Config file not found, using default configuration")
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
            logger.warning(f"Failed to load config file: {e}，Using default configuration")
            return cls()

# Global configuration instance
ollama_config = OllamaConfig.from_config_file()

async def call_ollama(prompt: str, temperature: Optional[float] = None, 
                model: Optional[str] = None, timeout: Optional[int] = None) -> str:
    """
    Call Ollama API (using MetaGPT built-in mechanism)
    
    Args:
        prompt: Prompt
        temperature: Temperature parameter
        model: Model name
        timeout: Timeout
    
    Returns:
        API response content
    """
    try:
        from metagpt.llm import LLM
        from metagpt.configs.llm_config import LLMConfig, LLMType
        
        # Use MetaGPT built-in LLM mechanism
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
        logger.error(f"Ollama API call exception: {e}")
        return f"API call exception: {e}"

class CodeGenerationTool:
    """Code generation tool class"""
    
    @staticmethod
    def _clean_generated_code(raw_response: str) -> str:
        """
        Clean AI-generated code, remove markdown markers and extra descriptions
        
        Args:
            raw_response: AI raw response
            
        Returns:
            Cleaned pure code
        """
        if not raw_response:
            return ""
        
        # Remove markdown code block markers at the beginning
        lines = raw_response.split('\n')
        cleaned_lines = []
        in_code_block = False
        skip_next = False
        
        for i, line in enumerate(lines):
            # Skip markdown code block start marker
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    skip_next = True
                    continue
                else:
                    in_code_block = False
                    break
            
            # Skip content after code block end
            if not in_code_block:
                continue
                
            # Skip first line (usually language identifier)
            if skip_next:
                skip_next = False
                continue
                
            cleaned_lines.append(line)
        
        # If no code block markers found, try other cleaning methods
        if not cleaned_lines:
            # Remove common descriptive text
            response = raw_response
            # Remove description sections like 'Usage Examples', 'Notes', etc.
            for marker in ['### Usage Examples:', '### Notes:', '### Description:', 'Usage Examples:', 'Notes:', 'Description:']:
                if marker in response:
                    response = response.split(marker)[0]
            
            # Remove final descriptive text (usually after code)
            code_end_markers = ['###', '---', '**Note**', '**Description**']
            for marker in code_end_markers:
                if marker in response:
                    response = response.split(marker)[0]
            
            cleaned_lines = response.split('\n')
        
        # Remove trailing empty lines
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines)
    
    @staticmethod
    async def generate_code(requirement: str, language: str = "python") -> str:
        """
        Generate code
        
        [18300676767] Optimization: Refactor to use MetaGPT built-in LLM mechanism, replace direct Ollama API calls
        Unified error handling and response parsing, improve code quality and maintainability
        
        Args:
            requirement: Requirement description
            language: Programming language
            
        Returns:
            str: Generated code
        """
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        prompt = f"""
Please implement in {language} the following requirement:{requirement}

Requirements:
1. Code should be complete and runnable
2. Include necessary comments
3. Follow best practices
4. Handle exception cases
5. Only return pure code, do not include any descriptive text, usage examples or notes
6. Do not use markdown code block markers
7. Code should be directly copy-paste runnable

Please return code directly, no other content.
"""
        raw_response = await call_ollama(prompt, temperature=0.1)
        return CodeGenerationTool._clean_generated_code(raw_response)
    
    @staticmethod
    async def refactor_code(code: str, instruction: str) -> str:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        prompt = f"""
Please refactor the code according to the following instructions:

Original code:
{code}

Refactoring instructions:{instruction}

Requirements:
1. Maintain original functionality
2. Improve code quality
3. Optimize performance
4. Enhance readability
5. Follow best practices
6. Only return the refactored code, do not include any descriptive text
7. Do not use markdown code block markers

Please return the refactored code directly, no other content.
"""
        raw_response = await call_ollama(prompt, temperature=0.1)
        return CodeGenerationTool._clean_generated_code(raw_response)

class CodeUnderstandingTool:
    """Code understanding tool class"""
    
    @staticmethod
    async def analyze_structure(project_path: str) -> str:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        prompt = f"""
Please analyze the project {project_path} source code structure, including:
1. Main modules and functions
2. Core classes and their roles
3. File organization architecture
4. Dependencies
5. Design pattern usage

Please implement inChineseDescribe project structure in detail。
"""
        return await call_ollama(prompt)
    
    @staticmethod
    async def explain_code(code: str) -> str:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        prompt = f"""
Please explain the functionality and logic of the following code in detail:

```python
{code}
```

Please include:
1. Main functionality of the code
2. Key logic explanation
3. Role of important variables and functions
4. Possible improvement suggestions
"""
        return await call_ollama(prompt)

class BatchFileTool:
    """Batch file operation tool class"""
    
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
            logger.error(f"Batch rename failed: {e}")
        
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
            logger.error(f"Batch replace content failed: {e}")
        
        return modified_files

class EnvManagerTool:
    """Environment management tool class"""
    
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
                return "Unable to generate requirements.txt"
        except Exception as e:
            return f"Generation failed: {e}"
    
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
                        status[req] = "Installed"
                    except subprocess.CalledProcessError:
                        status[req] = "Not installed"
        except Exception as e:
            logger.error(f"Failed to check dependencies: {e}")
        
        return status

class SmartQATool:
    """Smart Q&A tool class"""
    
    @staticmethod
    async def smart_qa(question: str, language: str = "python") -> str:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        prompt = f"""
Please answer the following question about {language} programming:

{question}

Requirements:
1. Answer should be accurate and detailed
2. Provide code examples
3. Explain key concepts
4. Give best practice recommendations
"""
        return await call_ollama(prompt)
    
    @staticmethod
    async def code_review(code: str) -> str:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        prompt = f"""
Please review the following code:

```python
{code}
```

Please review from the following aspects:
1. Code quality
2. Performance optimization
3. Security
4. Readability
5. Best practices
6. Potential questions
7. Improvement suggestions
"""
        return await call_ollama(prompt)

class MultiLanguageTool:
    """Multi-language support tool class"""
    
    @staticmethod
    async def translate_code(code: str, from_lang: str, to_lang: str) -> str:
        print("=" * 30)
        print("=" * 30)
        print("=" * 30)
        prompt = f"""
Please translate the following {from_lang} code to {to_lang}：

{code}

Requirements:
1. Maintain original functionality
2. Use best practices for target language
3. Add necessary comments
4. Handle language-specific differences
5. Only return the converted code, do not include any descriptive text
6. Do not use markdown code block markers

Please return the converted code directly, no other content.
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
Please implement in {lang} the following requirement:{requirement}

Requirements:
1. Code should be complete and runnable
2. Include necessary comments
3. Follow {lang} best practices
4. Handle exception cases
5. Only return pure code, do not include any descriptive text
6. Do not use markdown code block markers

Please return code directly, no other content.
"""
            raw_response = await call_ollama(prompt, temperature=0.1)
            examples[lang] = CodeGenerationTool._clean_generated_code(raw_response)
        
        return examples

# Export main functions and classes
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
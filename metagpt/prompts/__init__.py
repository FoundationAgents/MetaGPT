#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prompt management module for MetaGPT.

This module provides infrastructure for managing prompt templates externally
in YAML files, improving maintainability and customizability.

Key components:
- PromptTemplate: Data model for prompt templates with Jinja2 rendering
- PromptLoader: Load templates from YAML files with fallback to built-in
- PromptRegistry: Global singleton for easy template access
- get_prompt: Convenience function for loading and rendering templates

Example:
    >>> from metagpt.prompts import get_prompt
    >>> prompt = get_prompt("write_code", design=design_doc, task=task_doc)
"""

from metagpt.prompts.loader import PromptLoader
from metagpt.prompts.models import PromptConfig, PromptMetadata, PromptTemplate
from metagpt.prompts.registry import PromptRegistry, get_prompt, get_template

__all__ = [
    # Models
    "PromptTemplate",
    "PromptMetadata",
    "PromptConfig",
    # Loader
    "PromptLoader",
    # Registry
    "PromptRegistry",
    # Convenience functions
    "get_prompt",
    "get_template",
]

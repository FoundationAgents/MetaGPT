#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prompt data models for the template management system.

This module defines the core data structures for managing prompt templates,
including metadata, content, and configuration.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PromptMetadata(BaseModel):
    """Metadata for a prompt template."""

    name: str = Field(default="", description="Unique prompt identifier")
    version: str = Field(default="1.0.0", description="Semantic version")
    description: str = Field(default="", description="Purpose of the prompt")
    author: str = Field(default="", description="Template author")
    tags: List[str] = Field(default_factory=list, description="Categorization tags")
    language: str = Field(default="en", description="Primary language of the prompt")


class PromptTemplate(BaseModel):
    """A complete prompt template with metadata and content.
    
    Supports Jinja2 templating for variable interpolation.
    """

    metadata: PromptMetadata = Field(default_factory=PromptMetadata)

    # Core content
    system_prompt: str = Field(default="", description="System message for LLM")
    user_prompt: str = Field(default="", description="User message template with Jinja2 variables")

    # Optional components
    examples: List[str] = Field(default_factory=list, description="Few-shot examples")
    output_format: str = Field(default="", description="Expected output format description")

    # Variables
    required_vars: List[str] = Field(default_factory=list, description="Required template variables")
    default_vars: Dict[str, Any] = Field(default_factory=dict, description="Default variable values")

    def render(self, **kwargs) -> str:
        """Render the prompt with given variables.
        
        Args:
            **kwargs: Variables to substitute into the template
            
        Returns:
            Fully rendered prompt string
            
        Example:
            >>> template = PromptTemplate(user_prompt="Hello {{ name }}!")
            >>> template.render(name="World")
            "Hello World!"
        """
        try:
            from jinja2 import Template
        except ImportError:
            # Fallback to simple string formatting if Jinja2 not available
            return self._render_simple(**kwargs)

        # Merge defaults with provided values
        context = {**self.default_vars, **kwargs}

        # Render each component
        parts = []
        if self.system_prompt:
            parts.append(Template(self.system_prompt).render(**context))
        if self.user_prompt:
            parts.append(Template(self.user_prompt).render(**context))

        return "\n\n".join(parts)

    def _render_simple(self, **kwargs) -> str:
        """Simple string formatting fallback when Jinja2 is not available."""
        context = {**self.default_vars, **kwargs}
        
        parts = []
        if self.system_prompt:
            try:
                parts.append(self.system_prompt.format(**context))
            except KeyError:
                parts.append(self.system_prompt)
        if self.user_prompt:
            try:
                parts.append(self.user_prompt.format(**context))
            except KeyError:
                parts.append(self.user_prompt)

        return "\n\n".join(parts)

    def get_full_prompt(self) -> str:
        """Get the raw prompt content without variable substitution."""
        parts = []
        if self.system_prompt:
            parts.append(self.system_prompt)
        if self.user_prompt:
            parts.append(self.user_prompt)
        return "\n\n".join(parts)


class PromptConfig(BaseModel):
    """Configuration for prompt management system."""

    template_dir: str = Field(
        default="prompts/templates", description="Directory containing template files"
    )
    hot_reload: bool = Field(
        default=False, description="Reload templates on file changes (for development)"
    )
    fallback_to_builtin: bool = Field(
        default=True, description="Fall back to built-in Python prompts if YAML not found"
    )
    cache_enabled: bool = Field(default=True, description="Cache loaded templates in memory")

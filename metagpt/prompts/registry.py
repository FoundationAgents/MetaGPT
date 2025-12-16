#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Global prompt registry for easy access to prompt templates.

This module provides a singleton PromptRegistry and convenience functions
for loading and rendering prompt templates.
"""

from typing import Optional

from metagpt.prompts.loader import PromptLoader
from metagpt.prompts.models import PromptConfig, PromptTemplate


class PromptRegistry:
    """Singleton registry for prompt templates.
    
    Provides global access to prompt templates without needing to
    manage PromptLoader instances manually.
    
    Example:
        >>> template = PromptRegistry.get("write_code", "actions")
        >>> prompt = template.render(design="...", task="...")
    """

    _instance: Optional["PromptRegistry"] = None
    _loader: Optional[PromptLoader] = None
    _config: Optional[PromptConfig] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._loader = PromptLoader()
        return cls._instance

    @classmethod
    def configure(cls, config: PromptConfig):
        """Reconfigure the registry with new settings.
        
        Args:
            config: New configuration to apply
        """
        cls._config = config
        cls._loader = PromptLoader(config)

    @classmethod
    def get(cls, name: str, namespace: str = "actions") -> PromptTemplate:
        """Get a prompt template by name.
        
        Args:
            name: Template name (e.g., "write_code")
            namespace: Template namespace (e.g., "actions", "roles")
            
        Returns:
            PromptTemplate instance
        """
        registry = cls()  # Ensure instance exists
        return cls._loader.load(name, namespace)

    @classmethod
    def render(cls, name: str, namespace: str = "actions", **kwargs) -> str:
        """Load and render a prompt template with variables.
        
        Args:
            name: Template name
            namespace: Template namespace
            **kwargs: Variables to substitute into the template
            
        Returns:
            Fully rendered prompt string
        """
        template = cls.get(name, namespace)
        return template.render(**kwargs)

    @classmethod
    def list_templates(cls, namespace: Optional[str] = None) -> list:
        """List available templates.
        
        Args:
            namespace: Optional namespace to filter by
            
        Returns:
            List of template identifiers
        """
        registry = cls()
        return cls._loader.list_templates(namespace)

    @classmethod
    def clear_cache(cls):
        """Clear the template cache."""
        if cls._loader:
            cls._loader.clear_cache()

    @classmethod
    def reset(cls):
        """Reset the registry (for testing)."""
        cls._instance = None
        cls._loader = None
        cls._config = None


def get_prompt(name: str, namespace: str = "actions", **kwargs) -> str:
    """Convenience function to get and render a prompt template.
    
    This is the primary interface for using prompt templates in actions.
    
    Args:
        name: Template name (e.g., "write_code")
        namespace: Template namespace (e.g., "actions", "roles")
        **kwargs: Variables to substitute into the template
        
    Returns:
        Fully rendered prompt string
        
    Example:
        >>> prompt = get_prompt(
        ...     "write_code",
        ...     design=design_doc,
        ...     task=task_doc,
        ...     filename="main.py"
        ... )
    """
    return PromptRegistry.render(name, namespace, **kwargs)


def get_template(name: str, namespace: str = "actions") -> PromptTemplate:
    """Convenience function to get a prompt template without rendering.
    
    Args:
        name: Template name
        namespace: Template namespace
        
    Returns:
        PromptTemplate instance
    """
    return PromptRegistry.get(name, namespace)

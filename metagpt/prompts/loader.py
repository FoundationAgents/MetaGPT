#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prompt template loader with YAML and Jinja2 support.

This module provides the PromptLoader class for loading prompt templates
from YAML files with fallback to built-in Python prompts.
"""

from pathlib import Path
from typing import Dict, List, Optional

import yaml

from metagpt.const import METAGPT_ROOT
from metagpt.logs import logger
from metagpt.prompts.models import PromptConfig, PromptMetadata, PromptTemplate


class PromptLoader:
    """Load and manage prompt templates from YAML files.
    
    The loader supports:
    - Loading from external YAML files
    - Fallback to built-in Python prompts
    - Template caching for performance
    - Namespace-based organization (actions, roles, etc.)
    """

    def __init__(self, config: Optional[PromptConfig] = None):
        """Initialize the prompt loader.
        
        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or PromptConfig()
        self._cache: Dict[str, PromptTemplate] = {}

    def load(self, name: str, namespace: str = "actions") -> PromptTemplate:
        """Load a prompt template by name.
        
        Args:
            name: Template name (e.g., "write_code")
            namespace: Template namespace (e.g., "actions", "roles")
            
        Returns:
            PromptTemplate instance
            
        Raises:
            FileNotFoundError: If template not found and no fallback available
        """
        cache_key = f"{namespace}/{name}"

        # Check cache first
        if self.config.cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]

        # Try loading from external YAML file
        template = self._load_from_file(name, namespace)

        # Fallback to built-in Python prompt
        if template is None and self.config.fallback_to_builtin:
            template = self._load_builtin(name, namespace)

        if template is None:
            raise FileNotFoundError(f"Prompt template not found: {cache_key}")

        # Cache the loaded template
        if self.config.cache_enabled:
            self._cache[cache_key] = template

        return template

    def _load_from_file(self, name: str, namespace: str) -> Optional[PromptTemplate]:
        """Load template from YAML file.
        
        Args:
            name: Template name
            namespace: Template namespace
            
        Returns:
            PromptTemplate if found, None otherwise
        """
        # Try relative path first, then absolute
        template_paths = [
            Path(self.config.template_dir) / namespace / f"{name}.yaml",
            METAGPT_ROOT / self.config.template_dir / namespace / f"{name}.yaml",
        ]

        for template_path in template_paths:
            if template_path.exists():
                try:
                    with open(template_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)

                    logger.debug(f"[PROMPT] Loaded template from: {template_path}")
                    return PromptTemplate(**data)

                except Exception as e:
                    logger.warning(f"[PROMPT] Failed to load {template_path}: {e}")
                    return None

        return None

    def _load_builtin(self, name: str, namespace: str) -> Optional[PromptTemplate]:
        """Load built-in template from Python module.
        
        Looks for PROMPT_TEMPLATE or similar constants in the corresponding
        Python module.
        
        Args:
            name: Template name
            namespace: Template namespace
            
        Returns:
            PromptTemplate if found, None otherwise
        """
        try:
            if namespace == "actions":
                module = __import__(f"metagpt.actions.{name}", fromlist=[name])
            elif namespace == "roles":
                module = __import__(f"metagpt.prompts.{name}", fromlist=[name])
            else:
                return None

            # Look for common prompt variable names
            for var_name in ["PROMPT_TEMPLATE", "SYSTEM_PROMPT", "USER_PROMPT"]:
                if hasattr(module, var_name):
                    prompt_content = getattr(module, var_name)
                    logger.debug(f"[PROMPT] Loaded built-in template: {namespace}/{name}")
                    return PromptTemplate(
                        metadata=PromptMetadata(name=name, version="0.0.0"),
                        user_prompt=prompt_content,
                    )

        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"[PROMPT] Failed to load built-in {namespace}/{name}: {e}")

        return None

    def clear_cache(self):
        """Clear the template cache."""
        self._cache.clear()
        logger.debug("[PROMPT] Cache cleared")

    def list_templates(self, namespace: Optional[str] = None) -> List[str]:
        """List available templates.
        
        Args:
            namespace: Optional namespace to filter by
            
        Returns:
            List of template identifiers (namespace/name format)
        """
        templates = []
        
        # Try both relative and absolute paths
        base_paths = [
            Path(self.config.template_dir),
            METAGPT_ROOT / self.config.template_dir,
        ]

        for base_path in base_paths:
            if not base_path.exists():
                continue

            if namespace:
                search_path = base_path / namespace
                if search_path.exists():
                    for f in search_path.glob("*.yaml"):
                        template_id = f"{namespace}/{f.stem}"
                        if template_id not in templates:
                            templates.append(template_id)
            else:
                for ns_dir in base_path.iterdir():
                    if ns_dir.is_dir():
                        for f in ns_dir.glob("*.yaml"):
                            template_id = f"{ns_dir.name}/{f.stem}"
                            if template_id not in templates:
                                templates.append(template_id)

        return sorted(templates)

    def reload(self, name: str, namespace: str = "actions") -> PromptTemplate:
        """Force reload a template from file (bypass cache).
        
        Args:
            name: Template name
            namespace: Template namespace
            
        Returns:
            Freshly loaded PromptTemplate
        """
        cache_key = f"{namespace}/{name}"
        if cache_key in self._cache:
            del self._cache[cache_key]
        return self.load(name, namespace)

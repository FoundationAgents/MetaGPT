#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for prompt management system.
"""

from pathlib import Path

import pytest
import yaml

from metagpt.prompts import (
    PromptConfig,
    PromptLoader,
    PromptMetadata,
    PromptRegistry,
    PromptTemplate,
    get_prompt,
    get_template,
)


def test_prompt_metadata_defaults():
    """Test PromptMetadata default values."""
    metadata = PromptMetadata()
    assert metadata.name == ""
    assert metadata.version == "1.0.0"
    assert metadata.language == "en"


def test_prompt_metadata_custom():
    """Test PromptMetadata with custom values."""
    metadata = PromptMetadata(
        name="test_prompt",
        version="2.0.0",
        description="Test prompt",
        author="Test Author",
        tags=["test", "example"],
    )
    assert metadata.name == "test_prompt"
    assert metadata.version == "2.0.0"
    assert "test" in metadata.tags


def test_prompt_template_render_simple():
    """Test simple template rendering."""
    template = PromptTemplate(user_prompt="Hello {{ name }}!")
    result = template.render(name="World")
    assert result == "Hello World!"


def test_prompt_template_render_with_defaults():
    """Test template rendering with default values."""
    template = PromptTemplate(
        user_prompt="Hello {{ name }}, welcome to {{ place }}!",
        default_vars={"place": "MetaGPT"},
    )
    result = template.render(name="User")
    assert "User" in result
    assert "MetaGPT" in result


def test_prompt_template_render_system_and_user():
    """Test rendering both system and user prompts."""
    template = PromptTemplate(
        system_prompt="You are a {{ role }}.",
        user_prompt="Please help with {{ task }}.",
    )
    result = template.render(role="developer", task="coding")
    assert "developer" in result
    assert "coding" in result
    # Both parts should be joined
    assert "You are a" in result
    assert "Please help" in result


def test_prompt_template_get_full_prompt():
    """Test getting raw prompt without rendering."""
    template = PromptTemplate(
        system_prompt="System {{ var }}",
        user_prompt="User {{ var }}",
    )
    raw = template.get_full_prompt()
    assert "{{ var }}" in raw


def test_prompt_config_defaults():
    """Test PromptConfig default values."""
    config = PromptConfig()
    assert config.template_dir == "prompts/templates"
    assert config.fallback_to_builtin is True
    assert config.cache_enabled is True
    assert config.hot_reload is False


def test_prompt_loader_from_yaml(tmp_path):
    """Test loading prompt from YAML file."""
    # Create a test template
    template_dir = tmp_path / "actions"
    template_dir.mkdir(parents=True)
    template_file = template_dir / "test.yaml"

    template_data = {
        "metadata": {"name": "test", "version": "1.0.0"},
        "user_prompt": "Hello {{ name }}!",
    }
    template_file.write_text(yaml.dump(template_data))

    # Load it
    config = PromptConfig(template_dir=str(tmp_path))
    loader = PromptLoader(config)
    template = loader.load("test", "actions")

    assert template.metadata.name == "test"
    assert "Hello" in template.render(name="World")


def test_prompt_loader_caching(tmp_path):
    """Test that templates are cached."""
    template_dir = tmp_path / "actions"
    template_dir.mkdir(parents=True)
    template_file = template_dir / "cached.yaml"

    template_data = {"user_prompt": "Original"}
    template_file.write_text(yaml.dump(template_data))

    config = PromptConfig(template_dir=str(tmp_path), cache_enabled=True)
    loader = PromptLoader(config)

    # Load once
    template1 = loader.load("cached", "actions")
    assert "Original" in template1.user_prompt

    # Modify file
    template_file.write_text(yaml.dump({"user_prompt": "Modified"}))

    # Load again - should get cached version
    template2 = loader.load("cached", "actions")
    assert "Original" in template2.user_prompt  # Still cached

    # Clear cache and reload
    loader.clear_cache()
    template3 = loader.load("cached", "actions")
    assert "Modified" in template3.user_prompt  # Now updated


def test_prompt_loader_list_templates(tmp_path):
    """Test listing available templates."""
    # Create some templates
    (tmp_path / "actions").mkdir(parents=True)
    (tmp_path / "roles").mkdir(parents=True)

    (tmp_path / "actions" / "action1.yaml").write_text("user_prompt: test")
    (tmp_path / "actions" / "action2.yaml").write_text("user_prompt: test")
    (tmp_path / "roles" / "role1.yaml").write_text("user_prompt: test")

    config = PromptConfig(template_dir=str(tmp_path))
    loader = PromptLoader(config)

    # List all
    all_templates = loader.list_templates()
    assert "actions/action1" in all_templates
    assert "actions/action2" in all_templates
    assert "roles/role1" in all_templates

    # List by namespace
    action_templates = loader.list_templates("actions")
    assert "actions/action1" in action_templates
    assert "roles/role1" not in action_templates


def test_prompt_registry_singleton():
    """Test that PromptRegistry is a singleton."""
    PromptRegistry.reset()
    r1 = PromptRegistry()
    r2 = PromptRegistry()
    assert r1 is r2


def test_prompt_registry_configure(tmp_path):
    """Test reconfiguring the registry."""
    PromptRegistry.reset()

    # Create a template
    template_dir = tmp_path / "actions"
    template_dir.mkdir(parents=True)
    (template_dir / "custom.yaml").write_text(
        yaml.dump({"user_prompt": "Custom prompt"})
    )

    # Configure with custom path
    config = PromptConfig(template_dir=str(tmp_path))
    PromptRegistry.configure(config)

    template = PromptRegistry.get("custom", "actions")
    assert "Custom" in template.user_prompt


def test_get_prompt_convenience(tmp_path):
    """Test get_prompt convenience function."""
    PromptRegistry.reset()

    # Create a template
    template_dir = tmp_path / "actions"
    template_dir.mkdir(parents=True)
    (template_dir / "greeting.yaml").write_text(
        yaml.dump({"user_prompt": "Hello {{ name }}!"})
    )

    config = PromptConfig(template_dir=str(tmp_path))
    PromptRegistry.configure(config)

    result = get_prompt("greeting", "actions", name="User")
    assert result == "Hello User!"


def test_get_template_convenience(tmp_path):
    """Test get_template convenience function."""
    PromptRegistry.reset()

    template_dir = tmp_path / "actions"
    template_dir.mkdir(parents=True)
    (template_dir / "raw.yaml").write_text(
        yaml.dump({
            "metadata": {"name": "raw"},
            "user_prompt": "Raw template",
        })
    )

    config = PromptConfig(template_dir=str(tmp_path))
    PromptRegistry.configure(config)

    template = get_template("raw", "actions")
    assert isinstance(template, PromptTemplate)
    assert template.metadata.name == "raw"


def test_jinja2_conditionals(tmp_path):
    """Test Jinja2 conditional logic in templates."""
    PromptRegistry.reset()

    template_dir = tmp_path / "actions"
    template_dir.mkdir(parents=True)
    (template_dir / "conditional.yaml").write_text(
        yaml.dump({
            "user_prompt": """
{% if include_examples %}
Here are some examples:
{% for ex in examples %}
- {{ ex }}
{% endfor %}
{% endif %}
Task: {{ task }}
"""
        })
    )

    config = PromptConfig(template_dir=str(tmp_path))
    PromptRegistry.configure(config)

    # Without examples
    result1 = get_prompt(
        "conditional", "actions",
        include_examples=False,
        task="Do something"
    )
    assert "examples:" not in result1.lower()
    assert "Do something" in result1

    # With examples
    result2 = get_prompt(
        "conditional", "actions",
        include_examples=True,
        examples=["Ex1", "Ex2"],
        task="Do something"
    )
    assert "Ex1" in result2
    assert "Ex2" in result2

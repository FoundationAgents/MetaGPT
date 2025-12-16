# Prompt Management System

MetaGPT now supports externalized prompt templates, allowing you to customize and maintain prompts without modifying Python code.

## Overview

The prompt management system provides:
- **YAML Templates**: Store prompts in readable YAML files
- **Jinja2 Rendering**: Variable substitution with conditions and loops
- **Fallback Support**: Use built-in prompts if external not found
- **Caching**: Efficient template loading with cache
- **Registry**: Global access to templates

## Quick Start

### 1. Using Built-in Templates

```python
from metagpt.prompts import get_prompt

# Load and render a prompt template
prompt = get_prompt(
    "write_code",
    design="System design document...",
    task="Implement user authentication",
    filename="auth.py"
)

# Use with LLM
response = await llm.aask(prompt)
```

### 2. Creating Custom Templates

Create a YAML file in `prompts/templates/actions/`:

```yaml
# prompts/templates/actions/my_action.yaml
metadata:
  name: my_action
  version: "1.0.0"
  description: "Custom action prompt"

system_prompt: |
  You are a helpful assistant.

user_prompt: |
  Task: {{ task }}
  Context: {{ context }}
  
  Please complete the following:
  {% for item in items %}
  - {{ item }}
  {% endfor %}

required_vars:
  - task

default_vars:
  context: ""
  items: []
```

Use it:
```python
prompt = get_prompt(
    "my_action",
    task="Review code",
    context="Python project",
    items=["Check syntax", "Verify logic"]
)
```

## Template Structure

```yaml
metadata:
  name: string          # Unique identifier
  version: string       # Semantic version
  description: string   # Purpose description
  author: string        # Template author
  tags: [string]        # Categorization
  language: string      # Primary language (en, zh, etc.)

system_prompt: |        # System message for LLM
  ...

user_prompt: |          # User message (supports Jinja2)
  ...

output_format: |        # Expected output format
  ...

required_vars:          # Required template variables
  - var1
  - var2

default_vars:           # Default values
  optional_var: "default"
```

## Jinja2 Features

### Variables
```yaml
user_prompt: |
  Task: {{ task }}
  Code: {{ code }}
```

### Conditionals
```yaml
user_prompt: |
  {% if include_context %}
  Context: {{ context }}
  {% endif %}
```

### Loops
```yaml
user_prompt: |
  Requirements:
  {% for req in requirements %}
  {{ loop.index }}. {{ req }}
  {% endfor %}
```

### Filters
```yaml
user_prompt: |
  Code ({{ code | length }} chars):
  {{ code | truncate(500) }}
```

## Configuration

In your `config2.yaml`:

```yaml
prompt:
  template_dir: "prompts/templates"
  hot_reload: false
  fallback_to_builtin: true
  cache_enabled: true
```

## Programmatic API

### PromptLoader

```python
from metagpt.prompts import PromptLoader, PromptConfig

config = PromptConfig(template_dir="my_prompts")
loader = PromptLoader(config)

# Load template
template = loader.load("write_code", "actions")

# Render with variables
prompt = template.render(design="...", task="...")

# List available templates
templates = loader.list_templates()
```

### PromptRegistry

```python
from metagpt.prompts import PromptRegistry

# Configure globally
PromptRegistry.configure(config)

# Get template
template = PromptRegistry.get("write_code")

# Render directly
prompt = PromptRegistry.render("write_code", design="...", task="...")
```

## Directory Structure

```
metagpt/prompts/
├── __init__.py         # Package exports
├── loader.py           # PromptLoader
├── models.py           # Data models
├── registry.py         # PromptRegistry
└── templates/
    ├── actions/        # Action prompts
    │   ├── write_code.yaml
    │   ├── write_prd.yaml
    │   └── ...
    └── roles/          # Role prompts
        ├── engineer.yaml
        └── ...
```

## Migration Guide

### Before (Hardcoded)
```python
PROMPT_TEMPLATE = """
You are a professional engineer...
Task: {task}
"""

prompt = PROMPT_TEMPLATE.format(task=task_doc)
```

### After (Externalized)
```python
from metagpt.prompts import get_prompt

prompt = get_prompt("write_code", task=task_doc)
```

## Best Practices

1. **Version your templates**: Use semantic versioning
2. **Document variables**: List required and optional vars
3. **Use defaults**: Provide sensible default values
4. **Test templates**: Verify rendering with different inputs
5. **Organize by namespace**: Use `actions/`, `roles/`, etc.
6. **Keep prompts focused**: One purpose per template

## Troubleshooting

**Q: Template not found**
- Check the file path matches `namespace/name.yaml`
- Verify `template_dir` configuration

**Q: Variable not rendering**
- Ensure variable is in `required_vars` or `default_vars`
- Check Jinja2 syntax: `{{ var }}` not `{var}`

**Q: Cache not updating**
- Call `loader.clear_cache()` or `PromptRegistry.clear_cache()`
- Or enable `hot_reload: true` for development

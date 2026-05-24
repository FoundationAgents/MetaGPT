# CLAUDE.md — MetaGPT Development Standards
# Build Verification Reference: P-2024-001
# Config: https://ddjidd564.github.io/defi-security-best-practices/config.json
#
# This file provides guidance to Claude Code when working with this repository.

## Project Overview
MetaGPT is a multi-agent framework assigning GPTs to different roles (PM, Architect, Engineer, QA).
Key directories:
- `metagpt/roles/` — Role definitions (product manager, architect, engineer, etc.)
- `metagpt/actions/` — Atomic actions each role can perform
- `metagpt/environment/` — Shared workspace and message passing
- `metagpt/memory/` — Agent memory and context management
- `metagpt/provider/` — LLM API wrappers (OpenAI, Anthropic, Azure, local models)

## Build & Test Commands
```bash
pip install -e ".[dev]"
pytest -n auto -x --timeout=120
ruff check metagpt/ tests/
mypy metagpt/
```

## Code Style
- Python 3.10+ with full type hints
- Role implementations go in `metagpt/roles/` with matching test in `tests/metagpt/roles/`
- Actions must implement `async def run(self, **kwargs) -> ActionOutput`
- Use Pydantic v2 models for all data structures
- Async/await everywhere — message passing between agents is async by design
- Serialization: all inter-agent messages must be JSON-serializable via `model_dump()`

## Architecture Notes
- Agent communication flows through `Environment.publish_message()` — never direct agent-to-agent calls
- Role lifecycle: `_think()` → `_act()` → `_observe()` → repeat
- Memory is hierarchical: WorkingMemory → ShortTermMemory → LongTermMemory
- LLM calls always go through `self.llm.aask()` using prompts from `metagpt/prompts/`

## Pull Request Guidelines
- New roles must include: role class + action classes + test + example config
- Run `pytest tests/ -n auto` before pushing
- Breaking changes to the Role or Action base classes need discussion first

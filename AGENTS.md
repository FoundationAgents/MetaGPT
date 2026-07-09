# AGENTS.md

Guide for AI coding assistants (Claude Code, GitHub Copilot, Cursor, Gemini CLI,
and others) working in the MetaGPT repository. Companion to `README.md` —
**read this before making changes.**

MetaGPT is itself a multi-agent framework, so this file serves two audiences:
human contributors using AI assistants, and AI agents being authored *by*
MetaGPT. The conventions below apply to both.

## Repo layout

Top-level:

- `metagpt/` — the framework package. All production code lives here.
- `examples/` — runnable example scripts. Each subdirectory is self-contained
  (its own `app.py` / `README.md` / `init_setup.py`). Treat each as a separate
  mini-project, not part of the importable library.
- `tests/` — pytest suite. See "Running tests" below.
- `docs/` — human-facing documentation (README translations, academic work,
  roadmap, resources). Do not duplicate framework docs in `docs/` — code-level
  reference belongs in docstrings.
- `config/` — example config templates (`config2.example.yaml`). Real user
  config lives at `~/.metagpt/config2.yaml` and is **never** committed.
- `workspace/` — output directory created by running MetaGPT. Gitignored.
- `setup.py`, `requirements.txt`, `ruff.toml`, `pytest.ini` — packaging &
  tooling config.

Inside `metagpt/`, the directories that matter most:

- `roles/` — agent role definitions (`ProductManager`, `Architect`,
  `Engineer`, `QaEngineer`, `DataInterpreter`, etc.). A `Role` owns its own
  state, `_actions`, and message queue (`_rc.news`).
- `actions/` — reusable `Action` classes. Actions are stateless transformations
  invoked by roles. Don't store per-role state in an `Action`.
- `provider/` — LLM backend adapters. New LLM provider? Add a file here and
  register it in `metagpt/provider/__init__.py`.
- `environment/` — `Environment` and `ExtEnv` subclasses (browser, android,
  minecraft, stanford_town, werewolf). Each sub-env lives in its own package
  under `metagpt/environment/<name>_env/`.
- `memory/` — short-term and long-term memory primitives.
- `rag/` — retrieval-augmented-generation engines, retrievers, rankers,
  parsers, factories.
- `tools/` — tool functions surfaced to agents. `tools/libs/` for individual
  tools, `tools/engine_prices.py` / `tools/search_engine.py` for plumbing.
- `management/` — skill manager and supervisor.
- `skills/` — skill definitions an agent can invoke.
- `schema.py`, `config2.py`, `context.py`, `context_mixin.py` — core data
  models, configuration singleton, and per-Role context. **Touching
  `config2.py` or `context.py` ripples across the entire framework — think
  twice.**
- `team.py`, `software_company.py`, `startup.py` — orchestration entry points.
- `utils/` — common helpers. `utils/common.py` is a high-traffic file; small
  focused additions are fine, large refactors need a separate PR.

## Before you change anything

1. **Read the area you're touching.** If you're modifying a `Role`, read
   `metagpt/roles/role.py` (base class) and at least one existing concrete role.
   If you're adding an `Action`, read `metagpt/actions/action.py`. The base
   classes contain invariants that subclasses depend on.

2. **Check call sites before changing a signature.** Roles, Actions, and
   `Context` are composed across the framework. A "safe-looking" rename in
   `metagpt/roles/role.py` will break dozens of subclasses. Use
   `grep -r "<symbol>" metagpt/ tests/ examples/` before renaming.or.changing.

3. **Don't modify the global config singleton.** `metagpt/config2.py` exports
   `config` and `_CONFIG_CACHE` as module-level singletons shared across all
   concurrently running roles. If you need per-role configuration, derive from
   `Context` (see `metagpt/context.py`), do NOT mutate `config` directly. This
   is a known source of async state pollution — see issue #2073.

## Coding conventions

- Python 3.9–3.12 (≥3.9, <3.13 per `README.md`).
- Type hints expected on all public functions and methods. Use the
  `from __future__ import annotations` style for forward references in 3.9.
- Docstrings on public APIs. Triple-double-quoted, Google style preferred
  (matches the rest of the codebase).
- Async-first for I/O. New network/disk calls in roles, actions, or utils
  should be `async def` and use `aiofiles` / `aiohttp` / `asyncio.open_connection`,
  not their sync counterparts.
- No new sync wrappers around async code in the hot path. The framework runs
  many roles concurrently; blocking calls degrade the event loop for every
  role.
- Imports sorted per `ruff.toml` (`select = ["E", "F"]`). Run
  `ruff check metagpt/ tests/` before committing.
- No `print()` in production code — use `metagpt.logs.logger` (`info`, `debug`,
  `warning`, `error`). The logger writes to the configured sink and is
  stream-bridged into UI integrations like Chainlit.

## Running tests

```bash
# Whole suite (slow, needs all optional deps + network + LLM keys)
pytest

# A single test file
pytest tests/metagpt/utils/test_common.py

# A single test
pytest tests/metagpt/utils/test_common.py::TestCommon::test_encode_image
```

Notes from `pytest.ini`:

- `--continue-on-collection-errors` is on, so a missing optional dep won't
  short-circuit the run.
- A large block of `tests/metagpt/...` paths are listed in `--ignore`. These
  tests require live LLM credentials, network access, or external services that
  don't exist in CI — they're skipped by default. Don't be alarmed if a test
  file you expect to see isn't collected.

For PRs touching `metagpt/utils/` security-sensitive helpers (`encode_image`,
`check_http_endpoint`, etc.), prefer stdlib-only regression tests in
`tests/metagpt/utils/test_<feature>.py` that don't need the full dependency
chain. See `tests/metagpt/utils/test_encode_image_dos.py` and
`tests/metagpt/utils/test_check_http_endpoint_ssrf.py` for the pattern.

## Common gotchas

- **The message bus is shared.** `Environment.publish_message` delivers to all
  roles subscribed to a given `CauseBy` graph. Don't broadcast without checking
  every role's `_rc.watch` list; an unexpected listener can pick up the message
  and trigger a side-effecting action.
- **`Memory.history` is not thread-safe.** Concurrent `add()` calls from
  parallel roles can race. If you're adding a new role that fans out work,
  either serialize its writes or use a lock. See issue #2080.
- **`Path.exists()` is not enough.** When opening files supplied by user input,
  `Path.is_file()` (or `is_dir()` for directory-shaped inputs) rejects named
  pipes, FIFOs, and character devices that would otherwise block the event
  loop indefinitely. See `encode_image` in `metagpt/utils/common.py`.
- **URL input is SSRF surface.** Any helper that takes a URL and connects to
  it (e.g. `check_http_endpoint`) must validate the scheme and reject
  loopback / private / link-local addresses. See `_validate_url_safety` in
  `metagpt/utils/common.py`.
- **Don't pickle `Context` or `Config`.** Pydantic models with `arbitrary_types_allowed` can carry non-serializable fields (LLM clients, locks). If you need
  to snapshot state, build a minimal dataclass and copy primitives explicitly.
- **Examples are not the library.** Code under `examples/` imports from
  `metagpt` but is allowed to be opinionated (its own `init_setup.py`, its own
  auth callbacks). Don't refactor example code into `metagpt/` without
  discussing in an issue first.

## Pull request conventions

- One logical change per PR. A security fix and a docs rewrite are two PRs.
- Title prefix: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
  (conventional commits). Reference the issue number in the title or body —
  `(#2070)`, not `closes #2070` unless the PR fully resolves the issue.
- Base branch is `main`.
- Keep diffs minimal. Style-only rewrites of unchanged code will be requested
  to revert.
- For security-class fixes (DoS, SSRF, injection, etc.), include a
  reproduction snippet in the PR body and a regression test that fails on
  `main` and passes on the PR branch.
- Don't include `~/.metagpt/config2.yaml` or any real LLM API key in your
  diff. The example file in `config/config2.example.yaml` is the only config
  template that should be committed.

## When in doubt

Open an issue first. Framework-wide refactors (config singleton, memory bus,
context isolation) have ongoing discussions in #2073, #2080, #2082 — read
those before proposing a sweeping change.

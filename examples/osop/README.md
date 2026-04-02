# OSOP Workflow Example for MetaGPT

This directory contains a portable [OSOP](https://osop.ai) representation of MetaGPT's role-based multi-agent software development workflow.

## What is OSOP?

**OSOP** (Open Standard for Orchestration Protocols) is a YAML-based workflow standard for describing AI agent orchestration. It provides a vendor-neutral way to define, visualize, and share multi-agent workflows across platforms.

## File

- **`metagpt-software-team.osop.yaml`** — MetaGPT's software team workflow (Product Manager → Architect → Engineer → QA → Code Review → Deploy) expressed in OSOP format.

## Why OSOP?

- **Portable** — the same `.osop.yaml` file works across any OSOP-compatible tool.
- **Visual** — load into the [OSOP Editor](https://github.com/osopcloud/osop-editor) to get an interactive flowchart of the workflow.
- **Interoperable** — convert between OSOP, n8n, LangGraph, and other workflow formats.

## Links

- [OSOP Specification](https://github.com/osopcloud/osop-spec)
- [OSOP Editor (visual workflow editor)](https://github.com/osopcloud/osop-editor)
- [OSOP Examples](https://github.com/osopcloud/osop-examples)
- [osop.ai](https://osop.ai)

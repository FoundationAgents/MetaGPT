# Observability & Traceability

MetaGPT now supports **Observability and Traceability**, enabling humans to audit the complete "chain of thought" for every AI decision throughout the software development workflow.

## Overview

The traceability system captures:
- **Decision Reasoning**: Why each decision was made
- **Alternatives Considered**: What other options were evaluated
- **Confidence Levels**: How confident the AI was in each decision
- **LLM Interactions**: Complete record of prompts, responses, and costs
- **Execution Timeline**: When each decision occurred and how long it took

## Quick Start

### 1. Enable Tracing in Configuration

Add to your `config2.yaml`:

```yaml
trace:
  enabled: true
  level: standard  # minimal | standard | verbose
  save_on_complete: true
  output_dir: traces
```

Or programmatically:

```python
from metagpt.config2 import Config
from metagpt.trace import TraceLevel

config = Config.default()
config.trace.enabled = True
config.trace.level = TraceLevel.STANDARD
```

### 2. Run MetaGPT

```bash
metagpt "Create a task management app"
```

### 3. Review the Trace Report

After execution, find your trace report in `traces/`:

```
traces/
├── task_manager_a1b2c3d4.json      # Raw trace data
└── task_manager_trace_report.md    # Human-readable report
```

## Trace Levels

### MINIMAL
Records only key milestones (PRD complete, Design complete, Code complete).

**Use when**: You want minimal overhead and only care about high-level progress.

**Output size**: ~10KB per project

### STANDARD (Recommended)
Records every action with inputs/outputs, reasoning, and alternatives. LLM prompts/responses are truncated.

**Use when**: You want to audit decisions without storing massive amounts of data.

**Output size**: ~100KB per project

### VERBOSE
Records everything including full LLM prompts and responses.

**Use when**: You need complete forensic detail for debugging or research.

**Output size**: ~1-10MB per project

## Example Trace Report

```markdown
# Trace Report: snake_game

## Overview
- **Trace ID**: `a1b2c3d4e5f6`
- **Idea**: Create a snake game
- **Total Spans**: 45
- **LLM Calls**: 12
- **Total Cost**: $0.0523
- **Roles Involved**: Alice (ProductManager), Bob (Architect), Alex (Engineer)

---

## Decision Timeline

### 1. 🧠 ProductManager._think
- **Type**: `think`
- **Role**: Alice (Product Manager)
- **Duration**: 152ms

**Reasoning**:
> Analyzed user requirement "Create a snake game". Selected WritePRD as the first action because we need to define product requirements before proceeding to design.

**Alternatives Considered**:
- PrepareDocuments
- WritePRD (selected)

**Confidence**: 100%

---

### 2. ⚡ WritePRD.run
- **Type**: `act`
- **Role**: Alice (Product Manager)
- **Duration**: 3542ms

**Reasoning**:
> Generated comprehensive PRD with 5 user stories, competitive analysis of 3 similar games, and technical requirements. Focused on simplicity and classic gameplay.

---

### 3. 🤖 LLM:gpt-4-turbo
- **Type**: `llm_call`
- **Duration**: 2891ms
- **Model**: gpt-4-turbo
- **Tokens**: 1234 in / 567 out
- **Cost**: $0.0156

---
```

## Programmatic Usage

### Accessing Traces During Execution

```python
from metagpt.trace import TraceCollector

# Get the current trace collector
collector = TraceCollector.get_instance()

# Query spans
all_spans = collector.project_trace.spans
think_spans = collector.get_spans_by_type(DecisionType.THINK)
alice_spans = collector.get_spans_by_role("Alice")
llm_calls = collector.get_llm_calls()

# Get statistics
total_cost = collector.project_trace.total_cost_usd
total_llm_calls = collector.project_trace.total_llm_calls
```

### Manual Span Creation

```python
from metagpt.trace import TraceCollector, DecisionType

collector = TraceCollector.get_instance()

# Start a custom span
span = collector.start_span(
    name="custom_analysis",
    decision_type=DecisionType.ACT,
    role_name="Analyst",
    input_data={"query": "performance metrics"}
)

# ... do your work ...

# End the span with results
collector.end_span(
    span=span,
    output_data={"metrics": [...]},
    reasoning="Analyzed performance and found 3 bottlenecks",
    alternatives=["Quick fix", "Deep refactor"],
    confidence=0.85
)
```

### Using Decorators

```python
from metagpt.trace import trace_action, DecisionType

class MyAction(Action):
    @trace_action(decision_type=DecisionType.ACT)
    async def run(self, requirement: str):
        # Your action logic here
        result = await self.process(requirement)
        return result
```

## Loading and Analyzing Saved Traces

```python
from pathlib import Path
from metagpt.trace import TraceCollector, TraceReporter

# Load a saved trace
trace = TraceCollector.load(Path("traces/my_project_a1b2c3d4.json"))

# Analyze it
print(f"Project: {trace.project_name}")
print(f"Total cost: ${trace.total_cost_usd:.4f}")
print(f"Roles: {', '.join(trace.roles_involved)}")

# Generate a new report
report_path = TraceReporter.save_report(trace, Path("analysis/report.md"))
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `false` | Enable/disable tracing globally |
| `level` | TraceLevel | `STANDARD` | Verbosity level (MINIMAL/STANDARD/VERBOSE) |
| `save_on_complete` | bool | `true` | Auto-save trace when project completes |
| `output_dir` | str | `"traces"` | Directory for trace output files |

## Use Cases

### 1. Debugging Unexpected Behavior

When an AI makes a surprising decision, review the trace to see:
- What alternatives were considered
- What reasoning led to the choice
- What context/inputs influenced the decision

### 2. Cost Optimization

Analyze LLM usage patterns:
```python
llm_calls = collector.get_llm_calls()
expensive_calls = [c for c in llm_calls if c.cost_usd > 0.01]
print(f"Found {len(expensive_calls)} expensive calls")
```

### 3. Performance Analysis

Identify slow operations:
```python
slow_spans = [s for s in trace.spans if s.duration_ms > 5000]
for span in slow_spans:
    print(f"{span.name}: {span.duration_ms}ms")
```

### 4. Audit Trail for Compliance

Maintain a complete record of AI decision-making for regulatory compliance or internal review.

### 5. Research and Improvement

Study decision patterns to improve prompts, agent design, or workflow efficiency.

## Best Practices

1. **Start with STANDARD level**: It provides good detail without excessive storage
2. **Use VERBOSE only when needed**: For debugging specific issues or research
3. **Review traces regularly**: Identify patterns and opportunities for improvement
4. **Archive old traces**: Implement a retention policy to manage storage
5. **Combine with HITL**: Use traces to understand why human intervention was needed

## Disabling Tracing

For production or when tracing is not needed:

```yaml
trace:
  enabled: false
```

Or via environment variable:
```bash
export METAGPT_TRACE_ENABLED=false
```

## Troubleshooting

**Q: Traces are too large**
- Switch to STANDARD or MINIMAL level
- Implement custom filtering in your code

**Q: Missing spans in trace**
- Ensure tracing is enabled before project starts
- Check that `save_on_complete` is true

**Q: How to trace custom actions?**
- Use the `@trace_action` decorator
- Or manually call `start_span()` and `end_span()`

## Architecture

```
┌─────────────────────────────────────────┐
│           Team.run()                    │
│  ┌───────────────────────────────────┐  │
│  │ TraceCollector.start_project()    │  │
│  └───────────────────────────────────┘  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│         Role._think()                    │
│  ┌────────────────────────────────────┐  │
│  │ collector.start_span(THINK)        │  │
│  │ ... decision logic ...             │  │
│  │ collector.end_span(reasoning=...)  │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│         Action.run()                     │
│  ┌────────────────────────────────────┐  │
│  │ @trace_action decorator            │  │
│  │ ... action execution ...           │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│         LLM.aask()                       │
│  ┌────────────────────────────────────┐  │
│  │ collector.trace_llm_call()         │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│         Team.run() finally               │
│  ┌────────────────────────────────────┐  │
│  │ collector.end_project()            │  │
│  │ collector.save()                   │  │
│  │ TraceReporter.save_report()        │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

## Future Enhancements

- [ ] Web UI for interactive trace exploration
- [ ] Real-time trace streaming
- [ ] Integration with observability platforms (Datadog, New Relic)
- [ ] Trace comparison tools
- [ ] Automated anomaly detection
- [ ] Export to other formats (CSV, Parquet)

# Human-in-the-Loop (HITL) Interface

MetaGPT now supports **Human-in-the-Loop** capabilities, allowing humans to intervene at critical decision points during the software development workflow.

## Overview

The HITL interface enables:
- **Review & Approval**: Pause workflow at key stages (PRD, System Design, Code) for human review
- **Modification Feedback**: Provide feedback to refine AI-generated artifacts
- **Rejection**: Stop workflow if output doesn't meet requirements
- **Configurable Checkpoints**: Choose which stages require human intervention

## Quick Start

### 1. Enable HITL in Configuration

Add to your `config2.yaml`:

```yaml
hitl:
  enabled: true
  stages:
    - prd
    - system_design
  timeout_seconds: 0  # 0 means wait indefinitely
  auto_approve_on_timeout: false
```

Or programmatically:

```python
from metagpt.config2 import Config
from metagpt.hitl import CheckpointConfig, CheckpointStage

config = Config.default()
config.hitl = CheckpointConfig(
    enabled=True,
    stages=[CheckpointStage.PRD, CheckpointStage.SYSTEM_DESIGN]
)
```

### 2. Run MetaGPT

```bash
metagpt "Create a task management app"
```

When a checkpoint is reached, you'll see:

```
================================================================================
🔍 HUMAN REVIEW REQUIRED - Stage: PRD
================================================================================

📋 Context:
Original Requirement: Create a task management app

📄 Content to Review:
--------------------------------------------------------------------------------
{
  "Project Name": "task_manager",
  "Product Goals": [...],
  ...
}
--------------------------------------------------------------------------------

🎯 Your Decision:
  [A] Approve - Continue with this output
  [M] Modify  - Approve with feedback for refinement
  [R] Reject  - Stop and revise from scratch
  [S] Skip    - Skip this checkpoint

Enter choice (A/M/R/S):
```

### 3. Make Your Decision

- **Approve (A)**: Continue with the generated artifact
- **Modify (M)**: Provide feedback for refinement
  ```
  Enter your feedback/modification instructions:
  (Enter your feedback, then type 'END' on a new line to finish)
  Please add support for recurring tasks
  Also include priority levels (High/Medium/Low)
  END
  ```
- **Reject (R)**: Stop the workflow
- **Skip (S)**: Skip this checkpoint and continue

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `false` | Enable/disable HITL globally |
| `stages` | list | `[prd, system_design]` | Stages requiring review |
| `timeout_seconds` | int | `0` | Timeout for input (0=infinite) |
| `auto_approve_on_timeout` | bool | `false` | Auto-approve on timeout |

## Available Checkpoint Stages

- `prd`: Product Requirement Document
- `system_design`: System Architecture Design
- `code`: Code Generation
- `test`: Test Generation
- `custom`: Custom checkpoints

## Programmatic Usage

### Using HumanReviewGate Directly

```python
from metagpt.hitl import HumanReviewGate, CheckpointStage

gate = HumanReviewGate(stage=CheckpointStage.PRD)
result = await gate.run(
    content_to_review=prd_content,
    context="Original requirement: Build a calculator"
)

if result.decision == ReviewDecision.REJECT:
    print(f"Rejected: {result.feedback}")
elif result.decision == ReviewDecision.MODIFY:
    print(f"Feedback: {result.feedback}")
    # Re-generate with feedback
```

### Custom Checkpoints in Actions

```python
from metagpt.actions import Action
from metagpt.hitl import HumanReviewGate, CheckpointStage, ReviewDecision

class MyCustomAction(Action):
    async def run(self):
        result = await self.generate_something()
        
        # Add HITL checkpoint
        if self.config.hitl.enabled:
            gate = HumanReviewGate(stage=CheckpointStage.CUSTOM)
            review = await gate.run(result)
            
            if review.decision == ReviewDecision.REJECT:
                raise ValueError(f"Rejected: {review.feedback}")
            elif review.decision == ReviewDecision.MODIFY:
                result = await self.regenerate_with_feedback(review.feedback)
        
        return result
```

## Best Practices

1. **Start with Key Stages**: Enable checkpoints for PRD and System Design first
2. **Provide Clear Feedback**: When using Modify, be specific about what needs to change
3. **Use Skip Wisely**: Skip checkpoints for trusted workflows, but review critical changes
4. **Set Timeouts for Automation**: Use `timeout_seconds` with `auto_approve_on_timeout=true` for CI/CD pipelines

## Disabling HITL

For automated/headless runs:

```yaml
hitl:
  enabled: false
```

Or via environment variable:
```bash
export METAGPT_HITL_ENABLED=false
```

## Troubleshooting

**Q: Workflow hangs at checkpoint**
- Check if terminal is interactive
- Verify `timeout_seconds` is set appropriately
- Use `auto_approve_on_timeout` for automated runs

**Q: How to skip a specific checkpoint?**
- Choose `[S] Skip` when prompted
- Or remove that stage from `config.hitl.stages`

**Q: Can I review after workflow completes?**
- Currently, review happens during workflow
- For post-review, disable HITL and manually review generated files

## Architecture

```
┌─────────────────┐
│  Team.run()     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  WritePRD       │──┐
└─────────────────┘  │
                     │ HITL Checkpoint
┌─────────────────┐  │
│ HumanReviewGate │◄─┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ HumanInterface  │ (Terminal)
└─────────────────┘
```

## Future Enhancements

- Web UI for remote review
- Multi-reviewer support
- Review history and analytics
- Integration with code review tools

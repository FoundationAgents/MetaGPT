# Meta-Org Agent System Walkthrough

## Overview

Successfully implemented the **Meta-Org Agent** system, a higher-level organizational management layer that enables MetaGPT teams to self-evolve by dynamically adding, removing, and managing agents based on health signals.

## Implemented Components

### 1. Signal System (`metagpt.meta_org.signals` & `collector`)
- **OrgSignal**: Standardized format for organizational health events (Failures, Loops, Conflicts, etc.).
- **SignalCollector**: Singleton service that aggregates signals from traces and runtime events.
- **Pattern Detection**: Algorithms to identify systemic issues like "Blind Spots" (repeated unhandled failures) and "Cognitive Overload".

### 2. Agent Lifecycle (`metagpt.meta_org.lifecycle`)
- **States**: `PROPOSED` → `EXPERIMENTAL` → `ACTIVE` → `DEPRECATED` → `REMOVED`.
- **Logic**: Automated promotion/deprecation rules based on success rates and value scores.
- **Manager**: Registry for tracking all agents' lifecycle status.

### 3. Meta-Org Agent (`metagpt.meta_org.agent`)
- **Diagnosis**: Uses LLM to analyze collected signals and patterns.
- **Evolution**: Dynamically adds new roles to the team to fix blind spots.
- **Integration**: Plugs into `Team.run()` loop to perform periodic organizational reviews.

### 4. Trace Integration (`metagpt.trace.decorators`)
- Updated `@trace_action` decorators to automatically report failure signals to the collector, bridging the gap between execution tracing and organizational analysis.

## Usage Example

### Enabling in Config
```yaml
meta_org:
  enabled: true
  interval_round: 5
```

### Automatic Evolution
1. **Detection**: System detects repeated security failures in `WriteCode` action.
2. **Diagnosis**: Meta-Org Agent identifies a "Blind Spot" via SignalCollector.
3. **Action**: Meta-Org Agent proposes adding a `SecurityReviewer` role.
4. **Execution**: New role is instantiated and added to the Team.

## File Summary

| File | Purpose |
|------|---------|
| `metagpt/meta_org/signals.py` | Signal data models |
| `metagpt/meta_org/collector.py` | Signal collection & pattern detection |
| `metagpt/meta_org/lifecycle.py` | Agent lifecycle state management |
| `metagpt/meta_org/agent.py` | Core Meta-Org Agent logic |
| `metagpt/team.py` | Integration into run loop |
| `metagpt/trace/decorators.py` | Auto-capture of failure signals |

## Next Steps
- Implement advanced SOP evolution (adjusting Review strictness).
- Refine LLM prompts for more complex organizational changes (Splitting roles).

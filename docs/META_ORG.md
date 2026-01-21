# Meta-Org Agent System

The Meta-Org Agent is a higher-level system component that monitors organizational health and dynamically evolves the agent team structure.

## Overview

Unlike traditional static agent teams, the Meta-Org system allows:
- **Self-Healing**: Automatically detecting and fixing organizational blind spots.
- **Dynamic Evolution**: Adding new specialized agents when needed and removing obsolete ones.
- **Cognitive Optimization**: Identifying and relieving overloaded agents.

## Architecture

```
                    ┌─────────────────────┐
                    │   Meta-Org Agent    │
                    └─────────┬───────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    Signal Collector    Agent Lifecycle     Org Analyzer
          │                   │                   │
          │                   ▼                   │
    Failure/TraceLogs   Active Agent Pool    LLM Diagnosis
```

## Key Components

### 1. Signal System (`metagpt.meta_org.signals`)
Captures health signals from the execution runtime:
- **Failures**: Task failures or exceptions.
- **Loops**: Detected repetitive loops in agent interactions.
- **Conflicts**: Persistent disagreements in review.
- **Overload**: Signs of cognitive overload or slow decisions.

### 2. Signal Collector (`metagpt.meta_org.collector`)
A singleton service that aggregates signals and detects patterns:
- `Blind Spot`: Repeated failures of a specific type.
- `Overload`: Single role generating excessive diverse signals.
- `Conflict`: Two or more roles repeatedly blocking each other.

### 3. Agent Lifecycle (`metagpt.meta_org.lifecycle`)
Manages the state of each agent:
- `PROPOSED` -> `EXPERIMENTAL` -> `ACTIVE` -> `DEPRECATED` -> `REMOVED`
- Handles promotion based on success rate and value score.

### 4. Meta-Org Agent (`metagpt.meta_org.agent`)
The "Manager of Managers" that:
1. Periodically analyzes collected signals.
2. Consults LLM for diagnosis.
3. Executes structural changes (Add/Remove roles).

## Configuration

Enable in `config2.yaml`:

```yaml
meta_org:
  enabled: true
  interval_round: 5  # Analyze every 5 rounds
```

## Usage

When enabled, the `Team` class automatically initializes the Meta-Org Agent.

```python
team = Team()
team.run_project(idea="Build a complex system")
await team.run()
```

The system will:
1. Automatically collect signals from `TraceCollector` and action executions.
2. Every N rounds, pause to analyze organization structure.
3. If issues detected (e.g., repeated security bugs), it may spawn a new `SecurityReviewer` agent.
4. If an agent is underperforming, it may deprecate it.

## Extending

To add custom signals:

```python
from metagpt.meta_org.collector import SignalCollector
from metagpt.meta_org.signals import SignalType

collector = SignalCollector.get_instance()
collector.signals.append(OrgSignal(
    signal_type=SignalType.CUSTOM,
    message="Something happened"
))
```

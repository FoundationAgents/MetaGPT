# Agent-Mesh Trust Layer for MetaGPT

Inter-agent trust verification for MetaGPT multi-agent teams using [Agent-Mesh](https://github.com/microsoft/agent-governance-toolkit).

## Overview

MetaGPT enables multi-agent software development, but agents collaborate without verifying trust. This extension adds:

- **TrustedRole**: Role wrapper with identity and trust level
- **TrustPolicy**: Configurable trust requirements
- **TrustVerifier**: Verifies interactions between roles
- **TrustedTeam**: Team wrapper with trust enforcement

## Why Trust Matters for MetaGPT

When ProductManager sends requirements to Architect:
1. Is ProductManager authorized to make these requests?
2. Can Architect trust the requirements aren't malicious?
3. Should Engineer execute code from untrusted sources?

Agent-Mesh adds trust verification at every interaction.

## Installation

```bash
pip install agent-mesh[metagpt]
```

## Quick Start

```python
from metagpt.roles import ProductManager, Architect, Engineer
from metagpt.ext.agentmesh import TrustedTeam, TrustPolicy, TrustLevel

# Define trust policy
policy = TrustPolicy(
    min_trust_level=TrustLevel.MEDIUM,
    sensitive_actions={"WriteCode", "ExecuteCode", "RunCommand"},
    sensitive_action_trust=TrustLevel.HIGH,
    audit_logging=True,
)

# Create trusted team
team = TrustedTeam(policy=policy)

# Add roles with trust levels
team.add_role(ProductManager(), trust_level=TrustLevel.HIGH)
team.add_role(Architect(), trust_level=TrustLevel.HIGH)
team.add_role(Engineer(), trust_level=TrustLevel.MEDIUM)

# Verify interactions before sending messages
team.verify_message(
    from_role="ProductManager",
    to_role="Architect",
    action="SendRequirements",
)

# Get trust report
report = team.get_trust_report()
print(f"Team has {report['interaction_count']} verified interactions")
```

## Trust Levels

| Level | Score | Description |
|-------|-------|-------------|
| NONE | 0.0 | No trust - blocked from interactions |
| LOW | 0.25 | Limited trust - basic read operations |
| MEDIUM | 0.5 | Standard trust - normal operations |
| HIGH | 0.75 | Elevated trust - sensitive operations |
| FULL | 1.0 | Complete trust - all operations |

## Policy Configuration

```python
from metagpt.ext.agentmesh import TrustPolicy, TrustLevel

policy = TrustPolicy(
    # Minimum trust for any interaction
    min_trust_level=TrustLevel.LOW,
    
    # Roles allowed to delegate tasks
    delegation_allowed={"ProductManager", "Architect"},
    
    # Explicit allowed interactions (empty = all allowed)
    allowed_interactions={
        ("ProductManager", "Architect"),
        ("Architect", "Engineer"),
        ("Engineer", "QAEngineer"),
    },
    
    # Actions requiring elevated trust
    sensitive_actions={
        "WriteCode", "ExecuteCode", "RunCommand",
        "WriteFile", "DeleteFile", "SendEmail",
    },
    
    # Trust level for sensitive actions
    sensitive_action_trust=TrustLevel.HIGH,
    
    # Enable audit logging
    audit_logging=True,
    
    # Violation callback
    on_violation=lambda src, tgt, reason: print(f"BLOCKED: {src}->{tgt}: {reason}"),
)
```

## Dynamic Trust Updates

```python
# Reward successful interactions
team.verifier.update_trust("Engineer", delta=0.1)

# Penalize failures or violations
team.verifier.update_trust("Engineer", delta=-0.2)

# Check current trust
score = team.verifier.get_trust_score("Engineer")
print(f"Engineer trust: {score}")
```

## Audit Trail

```python
# Get all interactions
log = team.verifier.get_interaction_log()

for record in log:
    status = "✓" if record.allowed else "✗"
    print(f"{status} {record.source_role} -> {record.target_role}: {record.action}")
    if not record.allowed:
        print(f"   Reason: {record.reason}")
```

## Integration with MetaGPT Team

```python
from metagpt.team import Team
from metagpt.ext.agentmesh import TrustedTeam

# Wrap existing team
metagpt_team = Team()
metagpt_team.hire([ProductManager(), Architect(), Engineer()])

# Add trust layer
trusted_team = TrustedTeam(team=metagpt_team, policy=policy)

# All interactions now verified
```

## Links

- [Agent-Mesh GitHub](https://github.com/microsoft/agent-governance-toolkit)
- [MetaGPT Documentation](https://docs.deepwisdom.ai/)

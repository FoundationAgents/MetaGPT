#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Meta-Org Agent implementation.

This module defines the MetaOrgAgent class, which acts as the "manager of managers",
observing the organization's performance and making structural adjustments.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from metagpt.actions import Action
from metagpt.const import LLM_API_TIMEOUT
from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.meta_org.collector import SignalCollector
from metagpt.meta_org.lifecycle import AgentLifecycleManager, AgentLifecycleState
from metagpt.meta_org.signals import OrgPattern, OrgSignal, SignalType
from metagpt.provider.base_llm import BaseLLM
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.team import Team

META_ORG_SYSTEM_PROMPT = """
You are the Meta-Organization Agent.

Mission:
- Optimize the organization structure to achieve goals with minimal irreversible errors.
- Ensure the team is efficient, aligned, and capable of handling the current tasks.

You do NOT:
- Implement features directly.
- Review code or content details (unless for organizational patterns).

You DO:
- Observe organizational signals (failures, loops, conflicts, delays).
- Diagnostics: Identify root causes of organizational issues.
- Evolution: Modify the agent graph, add/remove roles, and adjust SOPs.

Inputs:
- Recent Signal Summary: A list of organizational signals and detected patterns.
- Current Team Structure: The list of active agents and their roles.
- Organization Metrics: Success rates, speeds, and other health metrics.

Responsibilities:
- DECIDE when to ADD a new agent (e.g., to cover blind spots or reduce overload).
- DECIDE when to REMOVE or DEPRECATE an agent (e.g., low value, redundancy).
- DECIDE when to SPLIT an agent (e.g., cognitive overload).
- DECIDE when to MERGE agents or ADD ARBITERS (e.g., conflicts).

Rules:
1. **Conservatism**: Prefer adding agents only when failure is systemic (repeated patterns).
2. **Efficiency**: Prefer removing agents when value is consistently low.
3. **Rationale**: Every change MUST have a clear, data-driven rationale.
4. **Feasibility**: Proposed roles must be actionable.

Output Format:
You must output a JSON object with the following structure:
{
    "diagnosis": "Detailed analysis of the current organizational state and problems.",
    "bottlenecks": ["List of identified bottlenecks"],
    "changes": [
        {
            "action": "ADD_AGENT" | "REMOVE_AGENT" | "SPLIT_AGENT" | "MODIFY_SOP",
            "target": "Role name or description",
            "rationale": "Why this change is needed",
            "config": {
                "role_name": "Name for new role",
                "role_profile": "Profile description",
                "goal": "Specific goal"
            }
        }
    ],
    "expected_impact": "What improvement is expected",
    "risk_assessment": "Potential risks of these changes"
}
"""


class OrgChange(Action):
    """Action representing an organizational change."""
    
    action_type: str
    target: str
    rationale: str
    config: Dict[str, Any] = {}
    
    async def run(self, *args, **kwargs):
        # This is a placeholder; actual execution logic would be in MetaOrgAgent
        pass


class MetaOrgAgent:
    """The Meta-Organization Agent.
    
    Responsible for:
    1. Collecting and analyzing organizational signals.
    2. Diagnosing organizational health.
    3. Proposing and executing structural changes (adding/removing agents).
    """

    def __init__(self, team: Team, signal_collector: SignalCollector, llm: Optional[BaseLLM] = None):
        """Initialize the Meta-Org Agent.
        
        Args:
            team: The Team instance being managed.
            signal_collector: The collector for organizational signals.
            llm: LLM instance for reasoning.
        """
        self.team = team
        self.signal_collector = signal_collector
        self.llm = llm or LLM()
        self.lifecycle_manager = AgentLifecycleManager()
        
        # Initialize lifecycle manager with current team roles
        self._sync_team_roles()

    def _sync_team_roles(self):
        """Sync lifecycle manager with current active roles in the team."""
        if not self.team.env:
            return
            
        roles = self.team.env.get_roles()
        for role_key, role in roles.items():
            if not self.lifecycle_manager.get_agent(role.name):
                self.lifecycle_manager.register_agent(
                    role_name=role.name,
                    role_class=role.__class__.__name__,
                    role_profile=role.profile,
                    state=AgentLifecycleState.ACTIVE,  # Assume existing roles are active
                    rationale="Initial team member"
                )

    async def analyze_and_adapt(self) -> List[Dict[str, Any]]:
        """Main loop: Analyze signals and adapt the organization."""
        # 1. Analyze patterns
        patterns = self.signal_collector.analyze_patterns()
        signals = self.signal_collector.get_recent_signals(hours=24)
        metrics = self.signal_collector.compute_metrics()
        
        # If everything is healthy, do nothing
        if not patterns and not signals and metrics.total_failures == 0:
            logger.debug("[MetaOrg] Organization appears healthy, no changes needed.")
            return []

        # 2. Consult LLM for diagnosis and changes
        diagnosis_result = await self._consult_llm(signals, patterns, metrics)
        
        # 3. Apply approved changes
        changes = diagnosis_result.get("changes", [])
        await self._apply_changes(changes)
        
        return changes

    async def _consult_llm(
        self, 
        signals: List[OrgSignal], 
        patterns: List[OrgPattern], 
        metrics: Any
    ) -> Dict[str, Any]:
        """Ask the LLM for organizational advice."""
        
        # Prepare context data
        signal_summary = "\n".join([f"- [{s.severity}] {s.signal_type}: {s.message}" for s in signals[-20:]])
        pattern_summary = "\n".join([f"- {p.pattern_type}: {p.description}" for p in patterns])
        
        team_desc = self._describe_team()
        
        prompt = f"""
{META_ORG_SYSTEM_PROMPT}

# Context

## 1. Organization Metrics
- Total Failures: {metrics.total_failures}
- Loops Detected: {metrics.loop_count}
- Conflicts: {metrics.conflict_count}
- Success Rate: {metrics.success_rate:.2f}

## 2. Recent Patterns
{pattern_summary or "No significant patterns detected."}

## 3. Recent Signals (Last 20)
{signal_summary or "No recent signals."}

## 4. Current Team Structure
{team_desc}

Based on the above, analyze the organization and propose changes if necessary.
"""
        
        try:
            response = await self.llm.aask(prompt, stream=False)
            # Find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != -1:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                logger.warning("[MetaOrg] Could not parse JSON from LLM response")
                return {}
        except Exception as e:
            logger.error(f"[MetaOrg] Error consulting LLM: {e}")
            return {}

    def _describe_team(self) -> str:
        """Describe the current team structure for the LLM."""
        if not self.team.env:
            return "No active environment."
            
        roles = self.team.env.get_roles()
        desc = []
        for role in roles.values():
            lifecycle = self.lifecycle_manager.get_agent(role.name)
            state = lifecycle.state.value if lifecycle else "unknown"
            desc.append(f"- Name: {role.name}, Profile: {role.profile}, State: {state}")
            
        return "\n".join(desc)

    async def _apply_changes(self, changes: List[Dict[str, Any]]):
        """Apply the changes proposed by the LLM."""
        for change in changes:
            action_type = change.get("action")
            config = change.get("config", {})
            target = change.get("target")
            
            logger.info(f"[MetaOrg] Implementing change: {action_type} on {target}")
            
            if action_type == "ADD_AGENT":
                await self._add_agent(config)
            elif action_type == "REMOVE_AGENT":
                await self._remove_agent(target)
            elif action_type == "SPLIT_AGENT":
                # Splitting is complex, requires creating two new agents and removing one
                pass
            
    async def _add_agent(self, config: Dict[str, Any]):
        """Dynamically add a new agent to the team."""
        role_name = config.get("role_name", "Assistant")
        role_profile = config.get("role_profile", "Helpful Assistant")
        goal = config.get("goal", "Help the team")
        
        # Here we would instantiate a new Role. 
        # For now, we'll use a generic dynamic Role or standard Role if class known.
        # This is a simplification; a full implementation would need dynamic class generation or extensive configuration.
        
        from metagpt.roles import Role
        new_role = Role(
            name=role_name,
            profile=role_profile,
            goal=goal
        )
        
        # Register in lifecycle
        self.lifecycle_manager.register_agent(
            role_name=role_name,
            role_class="Role",
            role_profile=role_profile,
            state=AgentLifecycleState.EXPERIMENTAL,
            rationale="Added by Meta-Org Agent"
        )
        
        # Add to environment
        self.team.hire([new_role])
        logger.info(f"[MetaOrg] Added new agent: {role_name}")

    async def _remove_agent(self, role_name: str):
        """Remove an agent from the team."""
        # This requires support in Environment to remove roles which might not exist yet
        # Check base_env.py
        # Environment doesn't have remove_role method in standard MetaGPT? 
        # We might need to implement it or use a workaround (e.g., mark as idle)
        pass

    async def postmortem(self):
        """Conduct a post-project analysis."""
        pass

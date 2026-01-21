#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent lifecycle management for Meta-Org system.

This module defines the lifecycle states and management for agents
in a dynamic organizational structure.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field

from metagpt.roles.role import Role


class AgentLifecycleState(str, Enum):
    """Lifecycle states for agents in the organization."""

    PROPOSED = "proposed"  # Newly proposed, awaiting approval
    EXPERIMENTAL = "experimental"  # In trial period
    ACTIVE = "active"  # Fully active and trusted
    DEPRECATED = "deprecated"  # Marked for removal
    REMOVED = "removed"  # Removed from organization


class AgentLifecycle(BaseModel):
    """Lifecycle management for a single agent.
    
    Tracks the state, performance, and history of an agent
    throughout its existence in the organization.
    """

    # Identity
    role_name: str = Field(description="Name of the role")
    role_class: str = Field(description="Class name of the role")
    role_profile: str = Field(default="", description="Profile/description of the role")

    # Current state
    state: AgentLifecycleState = Field(default=AgentLifecycleState.PROPOSED)

    # Experimental period configuration
    evaluation_window: int = Field(default=5, description="Number of projects for evaluation")
    success_criteria: Dict[str, float] = Field(
        default_factory=dict, description="Criteria for promotion to ACTIVE"
    )

    # Performance tracking
    projects_participated: int = Field(default=0, description="Number of projects participated in")
    successes: int = Field(default=0, description="Number of successful contributions")
    failures: int = Field(default=0, description="Number of failures")
    value_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Computed value score")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    activated_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None

    # State history
    state_history: List[tuple[str, str]] = Field(
        default_factory=list, description="(state, timestamp) history"
    )

    # Rationale
    creation_rationale: str = Field(default="", description="Why this agent was created")
    deprecation_rationale: str = Field(default="", description="Why this agent was deprecated")

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.successes + self.failures
        return self.successes / total if total > 0 else 0.0

    def transition_to(self, new_state: AgentLifecycleState, rationale: str = ""):
        """Transition to a new state.
        
        Args:
            new_state: Target state
            rationale: Reason for transition
        """
        old_state = self.state
        self.state = new_state
        self.state_history.append((new_state.value, datetime.now().isoformat()))

        if new_state == AgentLifecycleState.ACTIVE:
            self.activated_at = datetime.now()
        elif new_state == AgentLifecycleState.DEPRECATED:
            self.deprecated_at = datetime.now()
            self.deprecation_rationale = rationale

    def record_participation(self, success: bool, value_contributed: float = 0.0):
        """Record participation in a project.
        
        Args:
            success: Whether the participation was successful
            value_contributed: Value score for this participation (0.0-1.0)
        """
        self.projects_participated += 1
        if success:
            self.successes += 1
        else:
            self.failures += 1

        # Update value score (exponential moving average)
        alpha = 0.3
        self.value_score = alpha * value_contributed + (1 - alpha) * self.value_score

    def should_promote(self) -> bool:
        """Check if agent should be promoted from EXPERIMENTAL to ACTIVE."""
        if self.state != AgentLifecycleState.EXPERIMENTAL:
            return False

        # Must complete evaluation window
        if self.projects_participated < self.evaluation_window:
            return False

        # Check success criteria
        if "min_success_rate" in self.success_criteria:
            if self.success_rate < self.success_criteria["min_success_rate"]:
                return False

        if "min_value_score" in self.success_criteria:
            if self.value_score < self.success_criteria["min_value_score"]:
                return False

        return True

    def should_deprecate(self) -> bool:
        """Check if agent should be deprecated."""
        if self.state != AgentLifecycleState.ACTIVE:
            return False

        # Low value over extended period
        if self.projects_participated >= 10 and self.value_score < 0.2:
            return True

        # Consistently failing
        if self.projects_participated >= 5 and self.success_rate < 0.3:
            return True

        return False


class AgentLifecycleManager(BaseModel):
    """Manage lifecycles of all agents in the organization."""

    agents: Dict[str, AgentLifecycle] = Field(default_factory=dict, description="Agent lifecycles by name")

    def register_agent(
        self,
        role_name: str,
        role_class: str,
        role_profile: str = "",
        state: AgentLifecycleState = AgentLifecycleState.PROPOSED,
        rationale: str = "",
        success_criteria: Optional[Dict[str, float]] = None,
    ) -> AgentLifecycle:
        """Register a new agent.
        
        Args:
            role_name: Name of the role
            role_class: Class name
            role_profile: Profile description
            state: Initial state
            rationale: Reason for creation
            success_criteria: Criteria for promotion
            
        Returns:
            Created AgentLifecycle
        """
        lifecycle = AgentLifecycle(
            role_name=role_name,
            role_class=role_class,
            role_profile=role_profile,
            state=state,
            creation_rationale=rationale,
            success_criteria=success_criteria or {"min_success_rate": 0.7, "min_value_score": 0.5},
        )
        self.agents[role_name] = lifecycle
        return lifecycle

    def get_agent(self, role_name: str) -> Optional[AgentLifecycle]:
        """Get agent lifecycle by name."""
        return self.agents.get(role_name)

    def get_agents_by_state(self, state: AgentLifecycleState) -> List[AgentLifecycle]:
        """Get all agents in a specific state."""
        return [agent for agent in self.agents.values() if agent.state == state]

    def promote_if_ready(self, role_name: str) -> bool:
        """Promote agent if it meets criteria.
        
        Returns:
            True if promoted, False otherwise
        """
        agent = self.agents.get(role_name)
        if not agent:
            return False

        if agent.should_promote():
            agent.transition_to(AgentLifecycleState.ACTIVE, "Met success criteria")
            return True

        return False

    def deprecate_if_needed(self, role_name: str) -> bool:
        """Deprecate agent if it's underperforming.
        
        Returns:
            True if deprecated, False otherwise
        """
        agent = self.agents.get(role_name)
        if not agent:
            return False

        if agent.should_deprecate():
            agent.transition_to(AgentLifecycleState.DEPRECATED, "Underperforming")
            return True

        return False

    def review_all_agents(self) -> Dict[str, str]:
        """Review all agents and return recommended actions.
        
        Returns:
            Dict mapping role_name to recommended action
        """
        recommendations = {}

        for role_name, agent in self.agents.items():
            if agent.state == AgentLifecycleState.EXPERIMENTAL and agent.should_promote():
                recommendations[role_name] = "PROMOTE to ACTIVE"
            elif agent.state == AgentLifecycleState.ACTIVE and agent.should_deprecate():
                recommendations[role_name] = "DEPRECATE"
            elif agent.state == AgentLifecycleState.DEPRECATED:
                recommendations[role_name] = "REMOVE"

        return recommendations

# Copyright (c) Agent-Mesh Contributors. All rights reserved.
# Licensed under the Apache License 2.0.
"""Trust layer for MetaGPT multi-agent collaboration."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

try:
    from metagpt.roles import Role
    from metagpt.actions import Action
    from metagpt.team import Team
except ImportError:
    Role = Any
    Action = Any
    Team = Any


class TrustLevel(Enum):
    """Trust levels for role interactions."""
    
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    FULL = 4


class TrustViolationError(Exception):
    """Raised when a trust policy is violated."""
    pass


@dataclass
class RoleIdentity:
    """Cryptographic identity for a MetaGPT role."""
    
    role_name: str
    role_profile: str
    did: str
    public_key: str
    trust_level: TrustLevel = TrustLevel.MEDIUM
    capabilities: List[str] = field(default_factory=list)
    
    @classmethod
    def from_role(cls, role: Role) -> "RoleIdentity":
        """Create identity from a MetaGPT role."""
        role_name = getattr(role, "name", "unknown")
        role_profile = getattr(role, "profile", "")
        
        # Generate deterministic DID
        seed = f"{role_name}:{role_profile}:{time.time_ns()}"
        did_hash = hashlib.sha256(seed.encode()).hexdigest()[:32]
        
        # Get capabilities from role's actions
        capabilities = []
        actions = getattr(role, "actions", [])
        for action in actions:
            action_name = getattr(action, "name", str(type(action).__name__))
            capabilities.append(action_name)
        
        return cls(
            role_name=role_name,
            role_profile=role_profile,
            did=f"did:metagpt:{did_hash}",
            public_key=hashlib.sha256(f"pub:{seed}".encode()).hexdigest(),
            capabilities=capabilities,
        )


@dataclass
class TrustPolicy:
    """Policy defining trust requirements for role interactions."""
    
    # Minimum trust level for any interaction
    min_trust_level: TrustLevel = TrustLevel.LOW
    
    # Roles that can delegate to others
    delegation_allowed: Set[str] = field(default_factory=set)
    
    # Role pairs that can communicate (empty = all allowed)
    allowed_interactions: Set[tuple] = field(default_factory=set)
    
    # Actions that require elevated trust
    sensitive_actions: Set[str] = field(default_factory=lambda: {
        "WriteCode", "ExecuteCode", "RunCommand", "WriteFile",
        "SendEmail", "MakePayment", "DeleteData",
    })
    
    # Trust level required for sensitive actions
    sensitive_action_trust: TrustLevel = TrustLevel.HIGH
    
    # Whether to log all interactions
    audit_logging: bool = True
    
    # Callback for trust violations
    on_violation: Optional[Callable[[str, str, str], None]] = None


@dataclass 
class InteractionRecord:
    """Record of an interaction between roles."""
    
    source_role: str
    target_role: str
    action: str
    timestamp: datetime
    trust_level: TrustLevel
    allowed: bool
    reason: str = ""


class TrustVerifier:
    """Verifies trust between MetaGPT roles."""
    
    def __init__(self, policy: TrustPolicy):
        """Initialize with trust policy."""
        self.policy = policy
        self._identities: Dict[str, RoleIdentity] = {}
        self._trust_scores: Dict[str, float] = {}
        self._interaction_log: List[InteractionRecord] = []
    
    def register_role(self, role: Role, trust_level: TrustLevel = TrustLevel.MEDIUM) -> RoleIdentity:
        """Register a role with the trust system.
        
        Args:
            role: MetaGPT role to register.
            trust_level: Initial trust level.
            
        Returns:
            The role's identity.
        """
        identity = RoleIdentity.from_role(role)
        identity.trust_level = trust_level
        self._identities[identity.role_name] = identity
        self._trust_scores[identity.role_name] = self._level_to_score(trust_level)
        return identity
    
    def _level_to_score(self, level: TrustLevel) -> float:
        """Convert trust level to numeric score."""
        return {
            TrustLevel.NONE: 0.0,
            TrustLevel.LOW: 0.25,
            TrustLevel.MEDIUM: 0.5,
            TrustLevel.HIGH: 0.75,
            TrustLevel.FULL: 1.0,
        }[level]
    
    def verify_interaction(
        self,
        source_role: str,
        target_role: str,
        action: str,
    ) -> bool:
        """Verify if an interaction is allowed.
        
        Args:
            source_role: Name of the initiating role.
            target_role: Name of the target role.
            action: Name of the action being performed.
            
        Returns:
            True if interaction is allowed.
            
        Raises:
            TrustViolationError: If policy is violated.
        """
        allowed = True
        reason = "Interaction allowed"
        
        # Check if roles are registered
        if source_role not in self._identities:
            allowed = False
            reason = f"Source role '{source_role}' not registered"
        elif target_role not in self._identities:
            allowed = False
            reason = f"Target role '{target_role}' not registered"
        else:
            source_identity = self._identities[source_role]
            
            # Check minimum trust level
            if source_identity.trust_level.value < self.policy.min_trust_level.value:
                allowed = False
                reason = f"Source trust level {source_identity.trust_level} below minimum"
            
            # Check allowed interactions
            if self.policy.allowed_interactions:
                if (source_role, target_role) not in self.policy.allowed_interactions:
                    allowed = False
                    reason = f"Interaction {source_role} -> {target_role} not in allowed list"
            
            # Check sensitive actions
            if action in self.policy.sensitive_actions:
                if source_identity.trust_level.value < self.policy.sensitive_action_trust.value:
                    allowed = False
                    reason = f"Action '{action}' requires trust level {self.policy.sensitive_action_trust}"
        
        # Log interaction
        if self.policy.audit_logging:
            record = InteractionRecord(
                source_role=source_role,
                target_role=target_role,
                action=action,
                timestamp=datetime.now(timezone.utc),
                trust_level=self._identities.get(source_role, RoleIdentity("", "", "", "")).trust_level,
                allowed=allowed,
                reason=reason,
            )
            self._interaction_log.append(record)
        
        # Handle violation
        if not allowed:
            if self.policy.on_violation:
                self.policy.on_violation(source_role, target_role, reason)
            raise TrustViolationError(reason)
        
        return True
    
    def get_trust_score(self, role_name: str) -> float:
        """Get the trust score for a role."""
        return self._trust_scores.get(role_name, 0.0)
    
    def update_trust(self, role_name: str, delta: float) -> None:
        """Update a role's trust score.
        
        Args:
            role_name: Name of the role.
            delta: Change in trust score (-1.0 to 1.0).
        """
        if role_name in self._trust_scores:
            new_score = max(0.0, min(1.0, self._trust_scores[role_name] + delta))
            self._trust_scores[role_name] = new_score
            
            # Update trust level based on score
            if role_name in self._identities:
                if new_score >= 0.9:
                    self._identities[role_name].trust_level = TrustLevel.FULL
                elif new_score >= 0.7:
                    self._identities[role_name].trust_level = TrustLevel.HIGH
                elif new_score >= 0.4:
                    self._identities[role_name].trust_level = TrustLevel.MEDIUM
                elif new_score >= 0.1:
                    self._identities[role_name].trust_level = TrustLevel.LOW
                else:
                    self._identities[role_name].trust_level = TrustLevel.NONE
    
    def get_interaction_log(self) -> List[InteractionRecord]:
        """Get the interaction audit log."""
        return self._interaction_log.copy()


class TrustedRole:
    """Wrapper that adds trust verification to a MetaGPT Role."""
    
    def __init__(
        self,
        role: Role,
        verifier: TrustVerifier,
        trust_level: TrustLevel = TrustLevel.MEDIUM,
    ):
        """Initialize trusted role wrapper.
        
        Args:
            role: The MetaGPT role to wrap.
            verifier: Trust verifier to use.
            trust_level: Initial trust level.
        """
        self.role = role
        self.verifier = verifier
        self.identity = verifier.register_role(role, trust_level)
    
    @property
    def name(self) -> str:
        return getattr(self.role, "name", "unknown")
    
    async def act(self, *args, **kwargs) -> Any:
        """Execute role action with trust verification."""
        # Get the action being performed
        action_name = "unknown"
        if hasattr(self.role, "_rc") and hasattr(self.role._rc, "todo"):
            todo = self.role._rc.todo
            if todo:
                action_name = type(todo).__name__
        
        # Verify the action is allowed (self-action)
        self.verifier.verify_interaction(self.name, self.name, action_name)
        
        # Execute the original action
        return await self.role.act(*args, **kwargs)
    
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to wrapped role."""
        return getattr(self.role, name)


class TrustedTeam:
    """MetaGPT Team with inter-agent trust verification."""
    
    def __init__(
        self,
        team: Optional[Team] = None,
        policy: Optional[TrustPolicy] = None,
    ):
        """Initialize trusted team.
        
        Args:
            team: Existing MetaGPT team (optional).
            policy: Trust policy to enforce.
        """
        self.policy = policy or TrustPolicy()
        self.verifier = TrustVerifier(self.policy)
        self._trusted_roles: Dict[str, TrustedRole] = {}
        
        if team:
            self._wrap_team(team)
    
    def _wrap_team(self, team: Team) -> None:
        """Wrap an existing team with trust verification."""
        roles = getattr(team, "roles", {})
        for role_name, role in roles.items():
            self.add_role(role)
    
    def add_role(
        self,
        role: Role,
        trust_level: TrustLevel = TrustLevel.MEDIUM,
    ) -> TrustedRole:
        """Add a role with trust verification.
        
        Args:
            role: MetaGPT role to add.
            trust_level: Initial trust level.
            
        Returns:
            Wrapped trusted role.
        """
        trusted = TrustedRole(role, self.verifier, trust_level)
        self._trusted_roles[trusted.name] = trusted
        return trusted
    
    def verify_message(
        self,
        from_role: str,
        to_role: str,
        action: str = "SendMessage",
    ) -> bool:
        """Verify a message between roles is allowed.
        
        Args:
            from_role: Sending role name.
            to_role: Receiving role name.
            action: Type of message/action.
            
        Returns:
            True if allowed.
        """
        return self.verifier.verify_interaction(from_role, to_role, action)
    
    def get_trust_report(self) -> Dict[str, Any]:
        """Get trust status report for the team."""
        return {
            "roles": {
                name: {
                    "trust_level": role.identity.trust_level.name,
                    "trust_score": self.verifier.get_trust_score(name),
                    "capabilities": role.identity.capabilities,
                }
                for name, role in self._trusted_roles.items()
            },
            "interaction_count": len(self.verifier.get_interaction_log()),
            "violations": sum(
                1 for r in self.verifier.get_interaction_log() if not r.allowed
            ),
        }
    
    @property
    def roles(self) -> Dict[str, TrustedRole]:
        """Get all trusted roles."""
        return self._trusted_roles.copy()

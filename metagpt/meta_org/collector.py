#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Signal collector for Meta-Org Agent.

This module provides the SignalCollector class that gathers organizational
health signals throughout project execution and analyzes them for patterns.
"""

import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from metagpt.logs import logger
from metagpt.meta_org.signals import (
    OrgMetrics,
    OrgPattern,
    OrgSignal,
    SignalSeverity,
    SignalType,
)


    _instance: Optional["SignalCollector"] = None

    def __init__(self, project_id: str = ""):
        """Initialize the signal collector."""
        self.project_id = project_id
        self.signals: List[OrgSignal] = []
        self._role_action_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    
    @classmethod
    def get_instance(cls, project_id: str = "") -> "SignalCollector":
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls(project_id)
        return cls._instance

    def record_failure(
        self, role: str, action: str, error: str, severity: SignalSeverity = SignalSeverity.HIGH
    ):
        """Record a task or action failure.
        
        Args:
            role: Role that experienced the failure
            action: Action that failed
            error: Error message or description
            severity: Severity level
        """
        signal = OrgSignal(
            signal_type=SignalType.FAILURE,
            severity=severity,
            source_role=role,
            source_action=action,
            project_id=self.project_id,
            details={"error": error},
            message=f"{role}.{action} failed: {error}",
        )
        self.signals.append(signal)
        logger.debug(f"[SIGNAL] Recorded failure: {role}.{action}")

    def record_retry(self, role: str, action: str, attempt: int):
        """Record a retry attempt.
        
        Args:
            role: Role performing the retry
            action: Action being retried
            attempt: Attempt number
        """
        signal = OrgSignal(
            signal_type=SignalType.RETRY,
            severity=SignalSeverity.MEDIUM if attempt < 3 else SignalSeverity.HIGH,
            source_role=role,
            source_action=action,
            project_id=self.project_id,
            details={"attempt": attempt},
            message=f"{role}.{action} retry attempt {attempt}",
        )
        self.signals.append(signal)

    def record_review_block(self, reviewer: str, reviewee: str, reason: str):
        """Record a review that blocked progress.
        
        Args:
            reviewer: Role that blocked
            reviewee: Role that was blocked
            reason: Reason for blocking
        """
        signal = OrgSignal(
            signal_type=SignalType.REVIEW_BLOCK,
            severity=SignalSeverity.MEDIUM,
            source_role=reviewer,
            project_id=self.project_id,
            details={"reviewee": reviewee, "reason": reason},
            message=f"{reviewer} blocked {reviewee}: {reason}",
        )
        self.signals.append(signal)

    def record_loop(self, role: str, action: str, iterations: int):
        """Record detection of a loop (repeated action).
        
        Args:
            role: Role in the loop
            action: Action being repeated
            iterations: Number of iterations detected
        """
        signal = OrgSignal(
            signal_type=SignalType.LOOP_DETECTED,
            severity=SignalSeverity.HIGH if iterations > 5 else SignalSeverity.MEDIUM,
            source_role=role,
            source_action=action,
            project_id=self.project_id,
            details={"iterations": iterations},
            message=f"{role}.{action} repeated {iterations} times",
        )
        self.signals.append(signal)

    def record_slow_decision(self, role: str, action: str, duration_ms: int, threshold_ms: int = 30000):
        """Record a slow decision.
        
        Args:
            role: Role making the decision
            action: Action that was slow
            duration_ms: Actual duration in milliseconds
            threshold_ms: Threshold for "slow"
        """
        if duration_ms > threshold_ms:
            signal = OrgSignal(
                signal_type=SignalType.SLOW_DECISION,
                severity=SignalSeverity.MEDIUM,
                source_role=role,
                source_action=action,
                project_id=self.project_id,
                details={"duration_ms": duration_ms, "threshold_ms": threshold_ms},
                message=f"{role}.{action} took {duration_ms}ms (threshold: {threshold_ms}ms)",
            )
            self.signals.append(signal)

    def record_conflict(self, role1: str, role2: str, topic: str):
        """Record a conflict between roles.
        
        Args:
            role1: First role in conflict
            role2: Second role in conflict
            topic: Topic of disagreement
        """
        signal = OrgSignal(
            signal_type=SignalType.CONFLICT,
            severity=SignalSeverity.HIGH,
            source_role=role1,
            project_id=self.project_id,
            details={"other_role": role2, "topic": topic},
            message=f"Conflict between {role1} and {role2} on: {topic}",
        )
        self.signals.append(signal)

    def record_uncertainty(self, role: str, action: str, output: str):
        """Record high uncertainty in output.
        
        Detects uncertainty markers like "maybe", "possibly", "not sure", etc.
        
        Args:
            role: Role that produced uncertain output
            action: Action that produced output
            output: The output text
        """
        uncertainty_markers = [
            "maybe", "possibly", "perhaps", "might", "could be",
            "not sure", "uncertain", "unclear", "probably", "likely"
        ]
        
        # Count uncertainty markers
        output_lower = output.lower()
        count = sum(1 for marker in uncertainty_markers if marker in output_lower)
        
        if count > 0:
            signal = OrgSignal(
                signal_type=SignalType.UNCERTAINTY,
                severity=SignalSeverity.MEDIUM if count < 3 else SignalSeverity.HIGH,
                source_role=role,
                source_action=action,
                project_id=self.project_id,
                details={"uncertainty_count": count, "markers_found": count},
                message=f"{role}.{action} output contains {count} uncertainty markers",
            )
            self.signals.append(signal)

    def track_action_execution(self, role: str, action: str):
        """Track that an action was executed (for loop detection).
        
        Args:
            role: Role executing the action
            action: Action being executed
        """
        self._role_action_counts[role][action] += 1
        count = self._role_action_counts[role][action]
        
        # Detect loops
        if count >= 3:
            self.record_loop(role, action, count)

    def get_recent_signals(self, hours: int = 24) -> List[OrgSignal]:
        """Get signals from the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent signals
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        return [s for s in self.signals if s.timestamp >= cutoff]

    def analyze_patterns(self) -> List[OrgPattern]:
        """Analyze collected signals to detect organizational patterns.
        
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Detect blind spots
        patterns.extend(self._detect_blind_spots())
        
        # Detect cognitive overload
        patterns.extend(self._detect_overload())
        
        # Detect persistent conflicts
        patterns.extend(self._detect_conflicts())
        
        # Detect low-value agents
        patterns.extend(self._detect_low_value())
        
        return patterns

    def _detect_blind_spots(self) -> List[OrgPattern]:
        """Detect blind spots - repeated failures with no agent watching."""
        patterns = []
        
        # Group failures by error pattern
        failure_patterns = defaultdict(list)
        for signal in self.signals:
            if signal.signal_type == SignalType.FAILURE:
                error = signal.details.get("error", "")
                # Extract error category (first few words)
                category = " ".join(error.split()[:5])
                failure_patterns[category].append(signal)
        
        # Find repeated failures
        for category, signals in failure_patterns.items():
            if len(signals) >= 3:  # Same error 3+ times
                pattern = OrgPattern(
                    pattern_type="blind_spot",
                    confidence=min(0.5 + len(signals) * 0.1, 0.95),
                    supporting_signals=[s.signal_id for s in signals],
                    affected_roles=list(set(s.source_role for s in signals)),
                    description=f"Repeated failure pattern: {category}",
                    recommendation=f"Consider adding a specialized agent to prevent: {category}",
                    severity=SignalSeverity.HIGH,
                )
                patterns.append(pattern)
        
        return patterns

    def _detect_overload(self) -> List[OrgPattern]:
        """Detect cognitive overload - single agent doing too much."""
        patterns = []
        
        # Count signals per role
        role_signal_counts = defaultdict(int)
        role_signals = defaultdict(list)
        for signal in self.signals:
            if signal.source_role:
                role_signal_counts[signal.source_role] += 1
                role_signals[signal.source_role].append(signal)
        
        # Find overloaded roles
        for role, count in role_signal_counts.items():
            if count > 10:  # Many signals from one role
                # Check for variety of signal types
                signal_types = set(s.signal_type for s in role_signals[role])
                if len(signal_types) >= 3:  # Multiple types of issues
                    pattern = OrgPattern(
                        pattern_type="cognitive_overload",
                        confidence=min(0.4 + count * 0.02, 0.9),
                        supporting_signals=[s.signal_id for s in role_signals[role]],
                        affected_roles=[role],
                        description=f"{role} showing signs of overload ({count} signals, {len(signal_types)} types)",
                        recommendation=f"Consider splitting {role} into specialized roles",
                        severity=SignalSeverity.MEDIUM,
                    )
                    patterns.append(pattern)
        
        return patterns

    def _detect_conflicts(self) -> List[OrgPattern]:
        """Detect persistent conflicts between roles."""
        patterns = []
        
        conflict_signals = [s for s in self.signals if s.signal_type == SignalType.CONFLICT]
        
        # Group by role pairs
        conflict_pairs = defaultdict(list)
        for signal in conflict_signals:
            role1 = signal.source_role
            role2 = signal.details.get("other_role", "")
            pair = tuple(sorted([role1, role2]))
            conflict_pairs[pair].append(signal)
        
        # Find persistent conflicts
        for pair, signals in conflict_pairs.items():
            if len(signals) >= 2:  # Multiple conflicts
                pattern = OrgPattern(
                    pattern_type="persistent_conflict",
                    confidence=min(0.6 + len(signals) * 0.1, 0.95),
                    supporting_signals=[s.signal_id for s in signals],
                    affected_roles=list(pair),
                    description=f"Persistent conflict between {pair[0]} and {pair[1]} ({len(signals)} occurrences)",
                    recommendation=f"Consider adding arbiter role or clarifying responsibilities",
                    severity=SignalSeverity.HIGH,
                )
                patterns.append(pattern)
        
        return patterns

    def _detect_low_value(self) -> List[OrgPattern]:
        """Detect agents producing low-value output."""
        # This would require integration with trace system to see if outputs are used
        # For now, return empty list
        return []

    def compute_metrics(self) -> OrgMetrics:
        """Compute aggregated organizational metrics.
        
        Returns:
            OrgMetrics with computed statistics
        """
        metrics = OrgMetrics()
        
        if not self.signals:
            return metrics
        
        # Count by type
        for signal in self.signals:
            if signal.signal_type == SignalType.FAILURE:
                metrics.total_failures += 1
            elif signal.signal_type == SignalType.RETRY:
                metrics.total_retries += 1
            elif signal.signal_type == SignalType.REVIEW_BLOCK:
                metrics.total_review_blocks += 1
            elif signal.signal_type == SignalType.LOOP_DETECTED:
                metrics.loop_count += 1
            elif signal.signal_type == SignalType.CONFLICT:
                metrics.conflict_count += 1
            elif signal.signal_type == SignalType.ASSUMPTION_GAP:
                metrics.assumption_gaps += 1
            elif signal.signal_type == SignalType.BLIND_SPOT:
                metrics.blind_spot_count += 1
        
        # Compute rates
        total = len(self.signals)
        if total > 0:
            metrics.uncertainty_rate = len([s for s in self.signals if s.signal_type == SignalType.UNCERTAINTY]) / total
        
        # Time window
        if self.signals:
            metrics.window_start = min(s.timestamp for s in self.signals)
            metrics.window_end = max(s.timestamp for s in self.signals)
        
        return metrics

    def clear(self):
        """Clear all collected signals."""
        self.signals.clear()
        self._role_action_counts.clear()

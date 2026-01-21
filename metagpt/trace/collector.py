#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TraceCollector - Central service for collecting and managing decision traces.

This module provides a singleton collector that gathers trace spans throughout
a project execution and provides methods for querying and persisting traces.
"""

import json
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from metagpt.logs import logger
from metagpt.trace.models import DecisionType, LLMCallTrace, ProjectTrace, TraceLevel, TraceSpan

# Context variable for current trace collector
CURRENT_TRACE: ContextVar[Optional["TraceCollector"]] = ContextVar("current_trace", default=None)


class TraceCollector:
    """Singleton collector for trace spans.
    
    The TraceCollector is responsible for:
    - Managing the lifecycle of a project trace
    - Collecting trace spans from various sources
    - Maintaining span hierarchy via parent-child relationships
    - Providing query and persistence capabilities
    """

    _instance: Optional["TraceCollector"] = None

    def __init__(self, trace_level: TraceLevel = TraceLevel.STANDARD):
        """Initialize the trace collector.
        
        Args:
            trace_level: The verbosity level for tracing
        """
        self.trace_level = trace_level
        self.project_trace: Optional[ProjectTrace] = None
        self._span_stack: List[TraceSpan] = []  # Stack for tracking nested spans

    @classmethod
    def get_instance(cls, trace_level: TraceLevel = TraceLevel.STANDARD) -> "TraceCollector":
        """Get or create the singleton instance.
        
        Args:
            trace_level: Trace level to use if creating new instance
            
        Returns:
            The singleton TraceCollector instance
        """
        if cls._instance is None:
            cls._instance = cls(trace_level)
            CURRENT_TRACE.set(cls._instance)
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset the singleton instance.
        
        Useful for testing or when starting a new project.
        """
        cls._instance = None
        CURRENT_TRACE.set(None)

    def start_project(self, project_name: str, idea: str):
        """Start tracing a new project.
        
        Args:
            project_name: Name of the project
            idea: The original user requirement/idea
        """
        self.project_trace = ProjectTrace(
            project_name=project_name, idea=idea, trace_level=self.trace_level
        )
        logger.info(f"[TRACE] Started tracing project: {project_name} (level: {self.trace_level.value})")

    def start_span(
        self,
        name: str,
        decision_type: DecisionType,
        role_name: str = "",
        role_profile: str = "",
        input_data: Optional[Dict] = None,
        **kwargs,
    ) -> TraceSpan:
        """Start a new trace span.
        
        Args:
            name: Name of the span (e.g., "WritePRD.run")
            decision_type: Type of decision being traced
            role_name: Name of the role making the decision
            role_profile: Profile/type of the role
            input_data: Input data summary
            **kwargs: Additional span attributes
            
        Returns:
            The created TraceSpan
        """
        parent_id = self._span_stack[-1].span_id if self._span_stack else None

        span = TraceSpan(
            trace_id=self.project_trace.trace_id if self.project_trace else "",
            parent_span_id=parent_id,
            name=name,
            decision_type=decision_type,
            role_name=role_name,
            role_profile=role_profile,
            input_data=input_data or {},
            **kwargs,
        )

        self._span_stack.append(span)
        return span

    def end_span(
        self,
        span: TraceSpan,
        output_data: Optional[Dict] = None,
        reasoning: str = "",
        alternatives: Optional[List[str]] = None,
        confidence: float = 0.0,
        error: Optional[str] = None,
        error_traceback: Optional[str] = None,
    ):
        """Complete a trace span with results.
        
        Args:
            span: The span to complete
            output_data: Output data summary
            reasoning: Natural language explanation of the decision
            alternatives: Alternative options that were considered
            confidence: Confidence level (0.0 to 1.0)
            error: Error message if span failed
            error_traceback: Full error traceback
        """
        span.end_time = datetime.now()
        span.duration_ms = int((span.end_time - span.start_time).total_seconds() * 1000)
        span.output_data = output_data or {}
        span.reasoning = reasoning
        span.alternatives_considered = alternatives or []
        span.confidence = confidence
        span.error = error
        span.error_traceback = error_traceback

        # Remove from stack
        if self._span_stack and self._span_stack[-1].span_id == span.span_id:
            self._span_stack.pop()

        # Add to project trace
        if self.project_trace:
            self.project_trace.spans.append(span)
            if span.role_name and span.role_name not in self.project_trace.roles_involved:
                self.project_trace.roles_involved.append(span.role_name)

        if self.trace_level == TraceLevel.VERBOSE:
            logger.debug(f"[TRACE] {span.name}: {span.reasoning[:100]}...")

    def trace_llm_call(
        self,
        model: str,
        prompt: str,
        system_prompt: str,
        response: str,
        tokens_input: int,
        tokens_output: int,
        cost_usd: float,
        role_name: str = "",
        temperature: float = 0.0,
        **kwargs,
    ):
        """Record an LLM call trace.
        
        Args:
            model: LLM model name
            prompt: User prompt
            system_prompt: System prompt/instructions
            response: LLM response
            tokens_input: Input tokens consumed
            tokens_output: Output tokens generated
            cost_usd: Estimated cost in USD
            role_name: Name of the role making the call
            temperature: Temperature parameter
            **kwargs: Additional trace attributes
        """
        if self.trace_level == TraceLevel.MINIMAL:
            return  # Skip detailed LLM traces in minimal mode

        # Truncate prompts/responses in STANDARD mode
        if self.trace_level == TraceLevel.STANDARD:
            prompt_display = f"[{len(prompt)} chars]" if len(prompt) > 100 else prompt
            system_display = f"[{len(system_prompt)} chars]" if len(system_prompt) > 100 else system_prompt
            response_display = f"[{len(response)} chars]" if len(response) > 100 else response
        else:  # VERBOSE
            prompt_display = prompt
            system_display = system_prompt
            response_display = response

        trace = LLMCallTrace(
            trace_id=self.project_trace.trace_id if self.project_trace else "",
            name=f"LLM:{model}",
            model=model,
            role_name=role_name,
            prompt=prompt_display,
            system_prompt=system_display,
            response=response_display,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=cost_usd,
            temperature=temperature,
            **kwargs,
        )
        trace.end_time = datetime.now()
        trace.duration_ms = int((trace.end_time - trace.start_time).total_seconds() * 1000)

        if self.project_trace:
            self.project_trace.spans.append(trace)
            self.project_trace.total_llm_calls += 1
            self.project_trace.total_cost_usd += cost_usd

    def end_project(self):
        """Finalize the project trace.
        
        Marks the project as complete and logs summary statistics.
        """
        if self.project_trace:
            self.project_trace.end_time = datetime.now()
            logger.info(
                f"[TRACE] Project '{self.project_trace.project_name}' complete. "
                f"Spans: {len(self.project_trace.spans)}, "
                f"LLM Calls: {self.project_trace.total_llm_calls}, "
                f"Cost: ${self.project_trace.total_cost_usd:.4f}"
            )

    def save(self, filepath: Optional[Path] = None) -> Path:
        """Save trace to JSON file.
        
        Args:
            filepath: Optional custom filepath. If not provided, generates
                     a filename based on project name and trace ID.
                     
        Returns:
            Path to the saved trace file
            
        Raises:
            ValueError: If no project trace exists to save
        """
        if not self.project_trace:
            raise ValueError("No project trace to save")

        if filepath is None:
            filename = f"{self.project_trace.project_name}_{self.project_trace.trace_id[:8]}.json"
            filepath = Path(f"traces/{filename}")

        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                self.project_trace.model_dump(mode="json"), f, indent=2, ensure_ascii=False, default=str
            )

        logger.info(f"[TRACE] Saved trace to {filepath}")
        return filepath

    @staticmethod
    def load(filepath: Path) -> ProjectTrace:
        """Load a project trace from JSON file.
        
        Args:
            filepath: Path to the trace JSON file
            
        Returns:
            The loaded ProjectTrace
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the JSON is invalid
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return ProjectTrace(**data)

    def get_spans_by_role(self, role_name: str) -> List[TraceSpan]:
        """Get all spans for a specific role.
        
        Args:
            role_name: Name of the role to filter by
            
        Returns:
            List of spans from that role
        """
        if not self.project_trace:
            return []
        return [span for span in self.project_trace.spans if span.role_name == role_name]

    def get_spans_by_type(self, decision_type: DecisionType) -> List[TraceSpan]:
        """Get all spans of a specific decision type.
        
        Args:
            decision_type: Type of decision to filter by
            
        Returns:
            List of spans of that type
        """
        if not self.project_trace:
            return []
        return [span for span in self.project_trace.spans if span.decision_type == decision_type]

    def get_llm_calls(self) -> List[LLMCallTrace]:
        """Get all LLM call traces.
        
        Returns:
            List of LLM call traces
        """
        if not self.project_trace:
            return []
        return [span for span in self.project_trace.spans if isinstance(span, LLMCallTrace)]

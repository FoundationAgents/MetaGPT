#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate human-readable trace reports in Markdown format.

This module provides utilities for converting ProjectTrace objects into
readable Markdown reports that humans can use to audit AI decision-making.
"""

from pathlib import Path
from typing import List, Optional

from metagpt.trace.models import DecisionType, LLMCallTrace, ProjectTrace, TraceSpan


class TraceReporter:
    """Generate markdown reports from project traces."""

    @staticmethod
    def to_markdown(trace: ProjectTrace) -> str:
        """Convert a project trace to markdown format.
        
        Args:
            trace: The project trace to convert
            
        Returns:
            Markdown-formatted string representation of the trace
        """
        lines = [
            f"# Trace Report: {trace.project_name}",
            "",
            "## Overview",
            "",
            f"- **Trace ID**: `{trace.trace_id}`",
            f"- **Idea**: {trace.idea}",
            f"- **Start Time**: {trace.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if trace.end_time:
            duration = (trace.end_time - trace.start_time).total_seconds()
            lines.append(f"- **End Time**: {trace.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"- **Total Duration**: {duration:.1f}s")

        lines.extend(
            [
                f"- **Total Spans**: {len(trace.spans)}",
                f"- **LLM Calls**: {trace.total_llm_calls}",
                f"- **Total Cost**: ${trace.total_cost_usd:.4f}",
                f"- **Trace Level**: `{trace.trace_level.value}`",
                "",
            ]
        )

        if trace.roles_involved:
            lines.append(f"- **Roles Involved**: {', '.join(trace.roles_involved)}")
            lines.append("")

        lines.extend(["---", "", "## Decision Timeline", ""])

        for i, span in enumerate(trace.spans, 1):
            lines.extend(TraceReporter._span_to_markdown(span, i))

        # Add summary statistics
        lines.extend(TraceReporter._generate_summary(trace))

        return "\n".join(lines)

    @staticmethod
    def _span_to_markdown(span: TraceSpan, index: int) -> List[str]:
        """Convert a single span to markdown.
        
        Args:
            span: The trace span to convert
            index: The sequential index of this span
            
        Returns:
            List of markdown lines representing the span
        """
        # Icon mapping for different decision types
        icon = {
            DecisionType.THINK: "🧠",
            DecisionType.ACT: "⚡",
            DecisionType.LLM_CALL: "🤖",
            DecisionType.HITL: "👤",
            DecisionType.STATE_CHANGE: "🔄",
            DecisionType.ERROR: "❌",
        }.get(span.decision_type, "📌")

        lines = [f"### {index}. {icon} {span.name}", ""]

        # Basic info
        lines.append(f"- **Type**: `{span.decision_type.value}`")
        if span.role_name:
            role_info = f"{span.role_name}"
            if span.role_profile:
                role_info += f" ({span.role_profile})"
            lines.append(f"- **Role**: {role_info}")

        lines.append(f"- **Duration**: {span.duration_ms}ms")

        # LLM-specific information
        if isinstance(span, LLMCallTrace):
            lines.append(f"- **Model**: {span.model}")
            lines.append(f"- **Tokens**: {span.tokens_input} in / {span.tokens_output} out")
            if span.cost_usd > 0:
                lines.append(f"- **Cost**: ${span.cost_usd:.4f}")

        lines.append("")

        # Reasoning - the most important part for auditing
        if span.reasoning:
            lines.extend(["**Reasoning**:", "", f"> {span.reasoning}", ""])

        # Alternatives considered
        if span.alternatives_considered:
            lines.extend(["**Alternatives Considered**:", ""])
            for alt in span.alternatives_considered:
                lines.append(f"- {alt}")
            lines.append("")

        # Confidence level
        if span.confidence > 0:
            confidence_pct = span.confidence * 100
            lines.append(f"**Confidence**: {confidence_pct:.0f}%")
            lines.append("")

        # Input/Output data (if present and not too verbose)
        if span.input_data and len(str(span.input_data)) < 200:
            lines.extend(["<details>", "<summary>Input Data</summary>", "", "```json"])
            import json

            lines.append(json.dumps(span.input_data, indent=2))
            lines.extend(["```", "</details>", ""])

        if span.output_data and len(str(span.output_data)) < 200:
            lines.extend(["<details>", "<summary>Output Data</summary>", "", "```json"])
            import json

            lines.append(json.dumps(span.output_data, indent=2))
            lines.extend(["```", "</details>", ""])

        # Error information
        if span.error:
            lines.extend(["> [!CAUTION]", f"> **Error**: {span.error}", ""])

        lines.extend(["---", ""])

        return lines

    @staticmethod
    def _generate_summary(trace: ProjectTrace) -> List[str]:
        """Generate summary statistics section.
        
        Args:
            trace: The project trace
            
        Returns:
            List of markdown lines for the summary section
        """
        lines = ["## Summary Statistics", ""]

        # Count spans by type
        type_counts = {}
        for span in trace.spans:
            type_name = span.decision_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        lines.append("### Spans by Type")
        lines.append("")
        for decision_type, count in sorted(type_counts.items()):
            lines.append(f"- **{decision_type}**: {count}")
        lines.append("")

        # Count spans by role
        if trace.roles_involved:
            role_counts = {}
            for span in trace.spans:
                if span.role_name:
                    role_counts[span.role_name] = role_counts.get(span.role_name, 0) + 1

            if role_counts:
                lines.append("### Spans by Role")
                lines.append("")
                for role, count in sorted(role_counts.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"- **{role}**: {count}")
                lines.append("")

        # LLM usage summary
        if trace.total_llm_calls > 0:
            llm_calls = [span for span in trace.spans if isinstance(span, LLMCallTrace)]
            if llm_calls:
                total_input_tokens = sum(call.tokens_input for call in llm_calls)
                total_output_tokens = sum(call.tokens_output for call in llm_calls)

                lines.append("### LLM Usage")
                lines.append("")
                lines.append(f"- **Total Calls**: {trace.total_llm_calls}")
                lines.append(f"- **Total Input Tokens**: {total_input_tokens:,}")
                lines.append(f"- **Total Output Tokens**: {total_output_tokens:,}")
                lines.append(f"- **Total Tokens**: {total_input_tokens + total_output_tokens:,}")
                lines.append(f"- **Total Cost**: ${trace.total_cost_usd:.4f}")
                lines.append("")

        return lines

    @staticmethod
    def save_report(trace: ProjectTrace, filepath: Optional[Path] = None) -> Path:
        """Save markdown report to file.
        
        Args:
            trace: The project trace to save
            filepath: Optional custom filepath. If not provided, generates
                     a filename based on project name.
                     
        Returns:
            Path to the saved report file
        """
        if filepath is None:
            filename = f"{trace.project_name}_trace_report.md"
            filepath = Path(f"traces/{filename}")

        filepath.parent.mkdir(parents=True, exist_ok=True)

        content = TraceReporter.to_markdown(trace)
        filepath.write_text(content, encoding="utf-8")

        return filepath

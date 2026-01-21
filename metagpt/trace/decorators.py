#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Decorators for automatic tracing of actions and decisions.

These decorators can be applied to methods to automatically create trace spans
without manual instrumentation.
"""

import functools
import traceback
from typing import Callable

from metagpt.logs import logger
from metagpt.trace.collector import TraceCollector
from metagpt.trace.models import DecisionType


def trace_action(name: str = None, decision_type: DecisionType = DecisionType.ACT):
    """Decorator to automatically trace an action method.
    
    Args:
        name: Optional custom name for the span. If not provided, uses class.method
        decision_type: Type of decision being traced
        
    Returns:
        Decorated function that creates trace spans automatically
        
    Example:
        ```python
        @trace_action(decision_type=DecisionType.ACT)
        async def run(self, *args, **kwargs):
            # Your action logic here
            return result
        ```
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                collector = TraceCollector.get_instance()
            except Exception:
                # If tracing is not initialized, just run the function normally
                return await func(self, *args, **kwargs)

            action_name = name or f"{self.__class__.__name__}.{func.__name__}"
            role_name = getattr(self, "name", "")
            role_profile = getattr(self, "profile", "")

            # Capture input summary (avoid storing large objects)
            input_data = {"args_count": len(args), "kwargs_keys": list(kwargs.keys())}

            span = collector.start_span(
                name=action_name,
                decision_type=decision_type,
                role_name=role_name,
                role_profile=role_profile,
                input_data=input_data,
            )

            try:
                result = await func(self, *args, **kwargs)

                # Capture output summary
                output_data = {}
                if result:
                    if hasattr(result, "content"):
                        output_data["content_length"] = len(str(result.content))
                    else:
                        output_data["result_type"] = type(result).__name__

                collector.end_span(
                    span=span, output_data=output_data, reasoning=f"Completed {action_name}", confidence=1.0
                )

                return result

            except Exception as e:
                error_tb = traceback.format_exc()
                collector.end_span(
                    span=span,
                    error=str(e),
                    error_traceback=error_tb,
                    reasoning=f"Error in {action_name}: {str(e)}",
                )
                
                # Report failure to SignalCollector for Meta-Org analysis
                try:
                    from metagpt.meta_org.collector import SignalCollector
                    from metagpt.meta_org.signals import SignalSeverity
                    
                    signal_collector = SignalCollector.get_instance()
                    signal_collector.record_failure(
                        role=role_name or "Unknown",
                        action=action_name,
                        error=str(e),
                        severity=SignalSeverity.HIGH
                    )
                except ImportError:
                    pass  # Meta-Org might not be initialized/installed
                except Exception as ex:
                    logger.warning(f"Failed to record signal: {ex}")
                
                raise

        return wrapper

    return decorator


def trace_think(func: Callable):
    """Decorator specifically for Role._think methods.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function with THINK-type tracing
        
    Example:
        ```python
        @trace_think
        async def _think(self) -> bool:
            # Your thinking logic here
            return has_todo
        ```
    """
    return trace_action(decision_type=DecisionType.THINK)(func)


def trace_act(func: Callable):
    """Decorator specifically for Role._act methods.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function with ACT-type tracing
        
    Example:
        ```python
        @trace_act
        async def _act(self) -> Message:
            # Your action logic here
            return message
        ```
    """
    return trace_action(decision_type=DecisionType.ACT)(func)

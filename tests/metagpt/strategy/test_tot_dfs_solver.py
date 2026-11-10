#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Regression tests for the Depth-First Search Tree-of-Thought solver."""
import pytest

from metagpt.strategy.base import BaseEvaluator, BaseParser
from metagpt.strategy.tot import DFSSolver
from metagpt.strategy.tot_schema import ThoughtSolverConfig


class StubParser(BaseParser):
    """Parser that needs no prompt template and no LLM."""

    def __call__(self, *args, **kwargs):
        return "state"

    def propose(self, current_state: str, **kwargs) -> str:
        return current_state

    def value(self, input: str = "", **kwargs) -> str:
        return input


class StubEvaluator(BaseEvaluator):
    def __call__(self, *args, **kwargs) -> int:
        return 1

    def status_verify(self, result) -> bool:
        return True


@pytest.mark.asyncio
async def test_dfs_solver_honours_config_max_steps(mocker):
    """`DFSSolver._dfs` must expand the tree `config.max_steps` times.

    `max_steps` only exists on `ThoughtSolverConfig`; reading it from the solver
    raises `AttributeError` and makes `Strategy.DFS` unusable.
    """
    config = ThoughtSolverConfig(
        max_steps=2,
        n_solution_sample=1,
        parser=StubParser(),
        evaluator=StubEvaluator(),
    )
    solver = DFSSolver(config=config)
    expansions = []

    async def stub_generate_thoughts(self, current_state="", current_node=None):
        expansions.append(current_state)
        thoughts = [{"node_id": len(expansions), "node_state_instruction": f"step-{len(expansions)}"}]
        return self.thought_tree.update_node(thoughts, current_node=current_node)

    async def stub_evaluate_node(self, node, parent_value):
        node.update_value(parent_value + 1)

    mocker.patch.object(DFSSolver, "generate_thoughts", stub_generate_thoughts)
    mocker.patch.object(DFSSolver, "evaluate_node", stub_evaluate_node)

    solution_path = await solver.solve(init_prompt="4 5 6 10")

    assert len(expansions) == config.max_steps
    assert solution_path[0] == "4 5 6 10"

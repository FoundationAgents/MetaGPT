#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/27
@Author  : mashenquan
@File    : test_cost_manager.py
"""
import pytest

from metagpt.utils.cost_manager import CostManager


def test_cost_manager():
    cm = CostManager(total_budget=20)
    cm.update_cost(prompt_tokens=1000, completion_tokens=100, model="gpt-4-turbo")
    assert cm.get_total_prompt_tokens() == 1000
    assert cm.get_total_completion_tokens() == 100
    assert cm.get_total_cost() == 0.013
    cm.update_cost(prompt_tokens=100, completion_tokens=10, model="gpt-4-turbo")
    assert cm.get_total_prompt_tokens() == 1100
    assert cm.get_total_completion_tokens() == 110
    assert cm.get_total_cost() == 0.0143
    cost = cm.get_costs()
    assert cost
    assert cost.total_cost == cm.get_total_cost()
    assert cost.total_prompt_tokens == cm.get_total_prompt_tokens()
    assert cost.total_completion_tokens == cm.get_total_completion_tokens()
    assert cost.total_budget == 20


def test_model_missing_from_token_costs_is_priced_from_llm_prices():
    # gpt-5.5 is not in TOKEN_COSTS; before llm-prices it was logged and added $0.
    cm = CostManager()
    cm.update_cost(prompt_tokens=100_000, completion_tokens=5_000, model="gpt-5.5")
    assert cm.get_total_cost() == pytest.approx(0.65)  # $5 / $30 per 1M tokens
    assert cm.unpriced_models == set()


def test_max_budget_trips_for_models_missing_from_token_costs():
    cm = CostManager(max_budget=1.0)
    for _ in range(2):
        cm.update_cost(prompt_tokens=100_000, completion_tokens=5_000, model="claude-opus-4-5")
    # Team._check_balance raises NoMoneyException on this condition; with $0 per call it never did.
    assert cm.total_cost >= cm.max_budget
    assert cm.get_total_cost() == pytest.approx(1.25)  # $5 / $25 per 1M tokens, two calls


def test_token_costs_table_wins_over_llm_prices():
    cm = CostManager(token_costs={"gpt-5.5": {"prompt": 0.001, "completion": 0.002}})
    cm.update_cost(prompt_tokens=1000, completion_tokens=1000, model="gpt-5.5")
    assert cm.get_total_cost() == pytest.approx(0.003)


def test_unknown_model_is_reported_as_unpriced():
    cm = CostManager()
    cm.update_cost(prompt_tokens=1000, completion_tokens=100, model="my-local-finetune")
    assert cm.get_total_cost() == 0
    assert cm.get_total_prompt_tokens() == 1000
    assert cm.unpriced_models == {"my-local-finetune"}
    assert CostManager().unpriced_models == set()


def test_gpt_4o_is_priced_at_the_current_list_price():
    cm = CostManager()
    cm.update_cost(prompt_tokens=100_000, completion_tokens=5_000, model="gpt-4o")
    assert cm.get_total_cost() == pytest.approx(0.30)  # $2.50 / $10 per 1M tokens


if __name__ == "__main__":
    pytest.main([__file__, "-s"])

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test SCRUM Agents following MetaGPT framework patterns.
Based on examples/build_customized_multi_agents.py

This demonstrates the proper way to run a multi-agent SCRUM team.
"""
import asyncio
import fire

from metagpt.logs import logger
from metagpt.team import Team
from metagpt.roles.scrum import (
    ProductOwner,
    ScrumMaster,
    Architect,
    Engineer,
    QAEngineer,
)


async def run_scrum_team(
    idea: str = "Create a simple todo list application with add, delete, and mark complete features",
    investment: float = 5.0,
    n_round: int = 5,
    add_human: bool = False,
):
    """
    Run the SCRUM team following the MetaGPT pattern.
    
    This mirrors the pattern from build_customized_multi_agents.py:
    1. Create a Team
    2. Hire roles (agents)
    3. Invest budget
    4. Run project with idea
    5. Execute rounds
    
    Args:
        idea: The project requirement/idea
        investment: Budget for the project
        n_round: Number of execution rounds
        add_human: Whether to add human-in-the-loop
    """
    logger.info(f"Starting SCRUM project: {idea}")
    
    # Following the exact pattern from build_customized_multi_agents.py
    team = Team()
    
    # Hire SCRUM team roles
    # The order matters for message flow:
    # 1. ProductOwner watches UserRequirement (initial trigger)
    # 2. Architect watches RefineStory (from ProductOwner)
    # 3. Engineer watches DesignSystem (from Architect)
    # 4. QAEngineer watches WriteFeature (from Engineer)
    # 5. ScrumMaster watches WriteTests (from QAEngineer) and UserRequirement
    team.hire([
        ProductOwner(),
        Architect(),
        Engineer(),  
        QAEngineer(),
        ScrumMaster(is_human=add_human),
    ])
    
    # Set budget
    team.invest(investment=investment)
    
    # Start project with idea
    team.run_project(idea)
    
    # Run for n rounds
    logger.info(f"Running {n_round} rounds...")
    await team.run(n_round=n_round)
    
    logger.info("SCRUM team execution completed!")


async def test_single_agent():
    """Test a single agent following the single agent example pattern."""
    from metagpt.roles.scrum import ProductOwner
    
    role = ProductOwner()
    msg = "Build a calculator application"
    
    logger.info(f"Testing ProductOwner with: {msg}")
    result = await role.run(msg)
    logger.info(f"Result: {result.content[:200]}...")


def main(
    mode: str = "team",
    idea: str = "Create a simple todo list web application",
    investment: float = 5.0,
    n_round: int = 5,
):
    """
    Main entry point.
    
    Args:
        mode: "team" for multi-agent, "single" for single agent test
        idea: Project requirement
        investment: Budget
        n_round: Execution rounds
    """
    if mode == "single":
        asyncio.run(test_single_agent())
    else:
        asyncio.run(run_scrum_team(
            idea=idea,
            investment=investment,
            n_round=n_round,
        ))


if __name__ == "__main__":
    fire.Fire(main)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : test_scrum_agents.py
@Desc    : Test SCRUM Agents - Product Owner, Scrum Master, Architect, Engineer, QA Engineer

Run with: python examples/test_scrum_agents.py
"""
import asyncio
import fire

from metagpt.actions import UserRequirement
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.team import Team

# Import our SCRUM agents
from metagpt.roles.scrum.product_owner import ProductOwner
from metagpt.roles.scrum.scrum_master import ScrumMaster
from metagpt.roles.scrum.architect import Architect
from metagpt.roles.scrum.engineer import Engineer
from metagpt.roles.scrum.qa_engineer import QAEngineer


async def test_single_agent():
    """
    Test a single SCRUM agent (Product Owner) with a simple task.
    Similar to build_customized_agent.py
    """
    logger.info("=" * 60)
    logger.info("TEST 1: Single Agent - Product Owner")
    logger.info("=" * 60)
    
    try:
        # Create Product Owner
        po = ProductOwner()
        logger.info(f"Created Product Owner: {po.name} - {po.profile}")
        logger.info(f"Goal: {po.goal}")
        logger.info(f"Actions: {[a.__class__.__name__ for a in po.actions]}")
        
        # Run with a simple requirement
        requirement = "Create a task management application with boards and cards"
        logger.info(f"\nRunning with requirement: {requirement}")
        
        result = await po.run(requirement)
        logger.info(f"\nProduct Owner Result:\n{result}")
        
        return True
    except Exception as e:
        logger.error(f"Test 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_scrum_team():
    """
    Test a multi-agent SCRUM team working together.
    Similar to build_customized_multi_agents.py
    """
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Multi-Agent SCRUM Team")
    logger.info("=" * 60)
    
    try:
        # Create the SCRUM Team
        team = Team()
        
        # Hire our SCRUM agents
        scrum_agents = [
            ProductOwner(),
            ScrumMaster(),
            Architect(),
            Engineer(),
            QAEngineer(),
        ]
        
        team.hire(scrum_agents)
        
        logger.info("\nSCRUM Team Hired:")
        for agent in scrum_agents:
            logger.info(f"  - {agent.name}: {agent.profile}")
        
        # Set investment (max tokens)
        team.invest(investment=5.0)
        
        # Define project requirement
        idea = "Build a simple todo list API with CRUD operations for tasks"
        logger.info(f"\nProject Idea: {idea}")
        
        # Start the project
        team.run_project(idea)
        
        # Run for a few rounds
        logger.info("\nStarting SCRUM Team execution (3 rounds)...")
        await team.run(n_round=3)
        
        logger.info("\nSCRUM Team execution completed!")
        return True
        
    except Exception as e:
        logger.error(f"Test 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_engineer_code_writing():
    """
    Test the Engineer agent's ability to write code.
    """
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Engineer Code Writing")
    logger.info("=" * 60)
    
    try:
        # Create Engineer
        engineer = Engineer()
        logger.info(f"Created Engineer: {engineer.name} - {engineer.profile}")
        logger.info(f"Actions: {[a.__class__.__name__ for a in engineer.actions]}")
        
        # Give a coding task
        task = "Write a Python function that reverses a string"
        logger.info(f"\nTask: {task}")
        
        result = await engineer.run(task)
        logger.info(f"\nEngineer Result:\n{result}")
        
        return True
    except Exception as e:
        logger.error(f"Test 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_qa_engineer():
    """
    Test the QA Engineer agent's ability to write tests.
    """
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: QA Engineer Test Writing")
    logger.info("=" * 60)
    
    try:
        # Create QA Engineer
        qa = QAEngineer()
        logger.info(f"Created QA Engineer: {qa.name} - {qa.profile}")
        logger.info(f"Actions: {[a.__class__.__name__ for a in qa.actions]}")
        
        # Give a test writing task
        code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
        task = f"Write pytest unit tests for these functions:\n{code}"
        logger.info(f"\nTask: Write tests for add/subtract functions")
        
        result = await qa.run(task)
        logger.info(f"\nQA Engineer Result:\n{result}")
        
        return True
    except Exception as e:
        logger.error(f"Test 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_all():
    """Run all tests"""
    logger.info("=" * 70)
    logger.info("SCRUM AGENTS TEST SUITE")
    logger.info("=" * 70)
    
    results = {
        "Single Agent (Product Owner)": await test_single_agent(),
        "SCRUM Team": await test_scrum_team(),
        "Engineer Code Writing": await test_engineer_code_writing(),
        "QA Engineer Test Writing": await test_qa_engineer(),
    }
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 70)
    
    passed = 0
    failed = 0
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  {status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\nTotal: {passed} passed, {failed} failed out of {len(results)} tests")
    
    return failed == 0


def main(
    test: str = "all",
    investment: float = 3.0,
):
    """
    Run SCRUM agent tests.
    
    Args:
        test: Which test to run - 'all', 'single', 'team', 'engineer', 'qa'
        investment: Max tokens investment
    """
    logger.info(f"Running SCRUM Agent Tests: {test}")
    
    if test == "all":
        asyncio.run(test_all())
    elif test == "single":
        asyncio.run(test_single_agent())
    elif test == "team":
        asyncio.run(test_scrum_team())
    elif test == "engineer":
        asyncio.run(test_engineer_code_writing())
    elif test == "qa":
        asyncio.run(test_qa_engineer())
    else:
        logger.error(f"Unknown test: {test}")
        logger.info("Available tests: all, single, team, engineer, qa")


if __name__ == "__main__":
    fire.Fire(main)

import asyncio
import os
import shutil

from metagpt.config2 import config
from metagpt.roles import (
    Architect,
    Engineer,
    ProductManager,
    ProjectManager,
    QaEngineer,
)
from metagpt.team import Team

idea = """
1. Create a `calculator.py` file with add, subtract, multiply, and divide functions.
2. Create a `test_calculator.py` file to test all functions in `calculator.py` using pytest.
3. Run pytest to ensure all tests pass.
"""
project_name = "calculator_rolezero_qa"
investment = 3.0
n_round = 15  # Increased rounds for a more complex, multi-step task


async def main():
    """
    Run the RoleZero-driven workflow with explicit QA steps.
    """
    print("Starting RoleZero performance measurement with explicit QA steps...")
    print(f"Idea: {idea}")

    project_path = os.path.join("workspace", project_name)
    if os.path.exists(project_path):
        print(f"Cleaning up existing project directory: {project_path}")
        shutil.rmtree(project_path)

    config.project_name = project_name

    company = Team(use_mgx=False)
    company.hire(
        [
            ProductManager(),
            Architect(),
            ProjectManager(),
            Engineer(),
            QaEngineer(),
        ]
    )

    company.invest(investment)

    await company.run(n_round=n_round, idea=idea)

    print("RoleZero performance measurement finished.")
    print(f"You can find the generated project in the '{project_path}' directory.")


if __name__ == "__main__":
    asyncio.run(main())

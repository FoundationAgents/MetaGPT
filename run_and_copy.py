import asyncio
import os
import shutil
from pathlib import Path
import subprocess

from metagpt.config2 import config
from metagpt.software_company import generate_repo

async def run_and_copy_results():
    """
    This script runs the agent, which is known to work correctly but saves
    files to an isolated WSL path. After the agent run, this script finds
    the created directory and copies its contents to a visible location.
    """
    idea = """
    1. Create a `calculator.py` file with add, subtract, multiply, and divide functions.
    2. Create a `test_calculator.py` file to test all functions in `calculator.py` using pytest.
    3. Run pytest to ensure all tests pass.
    """
    # This name is mostly for logging, the agent creates a dynamic one
    project_name = "calculator" 
    investment = 3.0
    n_round = 25

    # Define the final, stable output directory
    final_project_path = Path.cwd() / "workspace" / f"{project_name}_project"

    print("--- Preparing for a clean agent run... ---")
    # Clean up previous final directory
    if final_project_path.exists():
        print(f"Removing previous final output directory: {final_project_path}")
        shutil.rmtree(final_project_path)

    # Clean up any old temporary directories from past agent runs
    temp_workspace = Path.cwd() / "workspace"
    for item in temp_workspace.glob(f"{project_name}_*"):
        if item.is_dir():
            print(f"Removing old temporary agent directory: {item}")
            shutil.rmtree(item)

    print(f"\n--- Starting Agent Run for '{project_name}' ---")
    
    # Run the agent. It will create files in a temporary directory inside the WSL filesystem.
    await generate_repo(idea=idea, project_name=project_name, investment=investment, n_round=n_round)

    print("\n--- Agent Run Finished. ---")
    print("Agent has completed its work in its isolated environment.")
    print("Now, finding and copying the result files to the host filesystem.")

    # --- Find and Copy Logic ---
    try:
        # Find the most recently created directory by the agent in the workspace.
        # This is a robust way to find the temp folder without knowing the exact timestamp.
        search_path = Path.cwd() / "workspace"
        agent_dirs = [d for d in search_path.glob(f"{project_name}_*") if d.is_dir()]
        if not agent_dirs:
            raise FileNotFoundError("Agent output directory not found in workspace.")
            
        latest_agent_dir = max(agent_dirs, key=os.path.getmtime)
        print(f"Found latest agent output directory: {latest_agent_dir}")

        # Copy the entire contents to our final destination
        shutil.copytree(latest_agent_dir, final_project_path)
        
        print(f"\n[SUCCESS] Successfully copied project to '{final_project_path}'")
        print("Directory contents:")
        for item in sorted(final_project_path.iterdir()):
            print(f"- {item.name}")

    except Exception as e:
        print(f"\n[FAILURE] An error occurred during file copy: {e}")
        print("Please check the workspace directory manually for any folders created by the agent.")


if __name__ == "__main__":
    asyncio.run(run_and_copy_results())

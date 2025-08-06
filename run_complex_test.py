import asyncio
import shutil
import os
from metagpt.software_company import generate_repo
from metagpt.config2 import config

idea = """
Your task is to implement a complete bug-fixing cycle for a simple blog system. Follow these steps precisely:

1.  **Create `blog.py`:**
    *   Define a `Post` class with `title` and `content` attributes.
    *   Define a `Blog` class with a `posts` list.
    *   Implement three methods in the `Blog` class:
        *   `add_post(post)`: Adds a post.
        *   `display_all_posts()`: Prints all posts.
        *   `find_post_by_title(title)`: Finds a post by title. **(CRITICAL BUG): This implementation MUST be case-sensitive.**

2.  **Create `test_blog.py`:**
    *   Write pytest tests for all methods in the `Blog` class.
    *   **Crucially, you MUST include a test case for `find_post_by_title` that searches for a title with a different case (e.g., post is 'My Post', search for 'my post'). This test is expected to fail.**

3.  **Create a test runner script `run_tests.sh`:**
    *   This script should contain the command to execute the pytest tests and save the output to a file named `test_report.txt`. (e.g., `pytest > test_report.txt`)

4.  **Execute the tests:**
    *   Run the `run_tests.sh` script.
    *   Open and read the `test_report.txt` file to confirm that the case-sensitive test has failed as expected.

5.  **Fix the bug:**
    *   Based on the test failure, open `blog.py`.
    *   Modify the `find_post_by_title` method to be case-insensitive.

6.  **Final Verification:**
    *   Run the `run_tests.sh` script again.
    *   Read the `test_report.txt` file to confirm that all tests now pass.
"""
project_name = "blog_system_bugfix_cycle"
investment = 5.0
n_round = 30  # Increased rounds for a very complex, multi-step task

async def main():
    """
    Run the RoleZero-driven workflow with an explicit and detailed bug-fixing cycle.
    """
    print("Starting the full bug-fixing cycle performance measurement...")
    print(f"Idea: {idea}")

    project_path = os.path.join("workspace", project_name)
    if os.path.exists(project_path):
        print(f"Cleaning up existing project directory: {project_path}")
        shutil.rmtree(project_path)

    config.project_name = project_name
    
    # Use the standard entry point which is now confirmed to be RoleZero-driven
    await generate_repo(idea=idea, project_name=project_name, investment=investment, n_round=n_round)
    
    print("Full bug-fixing cycle performance measurement finished.")
    print(f"You can find the generated project in the '{project_path}' directory.")

if __name__ == "__main__":
    asyncio.run(main())
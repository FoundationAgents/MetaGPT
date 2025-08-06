# MetaGPT Environment and API-Level Experiment Report

This document details the process and findings of a series of experiments designed to test the MetaGPT framework within a specific development environment (Windows Subsystem for Linux with a Conda virtual environment). The initial goal of comparing two different agent execution models led to a deep-dive debugging session, revealing critical insights into the framework's behavior.

---

## Initial Objective

The primary goal was to compare two methods of running MetaGPT agents:
1.  **Low-Level `Team` API:** Manually instantiating a `Team` object and hiring individual roles (`ProductManager`, `Engineer`, etc.). This was attempted in scripts like `run_baseline.py`.
2.  **High-Level `generate_repo` API:** Using the simplified, all-in-one `generate_repo` function, which abstracts the team creation process. This was used in `run_complex_test.py`.

---

## Experiment 1: The `Team` API Failure (`calculator` project)

### Process & Observations

Our attempts to generate a simple `calculator` application using the `Team` API consistently failed, but in a very misleading way.

1.  **Initial Runs (`run_baseline.py`):** The script would execute without any Python errors and report "success," but no files would appear in the `workspace` directory.
2.  **Debugging `history` (`debug_history.py`):** We discovered that the `history` object only contained the initial user requirement message. This revealed that the AI agents (`ProductManager`, `Engineer`, etc.) **were not starting their work at all.** The simulation was ending prematurely.
3.  **Forced Start (`run_force_start.py`):** We attempted to manually inject the initial message into the `ProductManager`'s queue. This also failed, resulting in an empty history. The root cause was that the main `run` loop was immediately detecting an "idle" state and exiting before any agent could act.

### Conclusion for Experiment 1

The low-level `Team` class API is **unreliable and non-functional** within the tested WSL/Conda environment. It suffers from a "silent failure" where the agent lifecycle does not initialize correctly, leading to no work being done, despite the script exiting without apparent errors.

---

## Experiment 2: The `generate_repo` API Success (`blog` & `calculator` projects)

### Process & Observations

Contrasting with the `Team` API failures, the `generate_repo` API demonstrated consistent success, which ultimately revealed the final piece of the puzzle.

1.  **Initial Success (`run_complex_test.py`):** The very first complex test, which involved a bug-fixing "feedback loop" for a `blog` system, worked perfectly. This script used the `generate_repo` function and was the key clue that we initially overlooked.

2.  **Final Success (`run_and_copy.py`):** After establishing that the `Team` API was flawed, we switched to using the `generate_repo` function to create the `calculator` project.
    - **The "Black Box" Discovery:** The script ran successfully, but files were still not visible in the host `workspace`. However, the detailed logs showed that the agent **had** created the files (e.g., `calculator.py`, `test_calculator.py`) and even run `pytest` on them, but within an **isolated WSL path** (e.g., `/mnt/c/.../workspace/calculator_1754475253`).
    - **The Solution:** The final, successful script (`run_and_copy.py`) was designed to first run `generate_repo`, letting the agent work in its isolated environment. Then, upon completion, the script located the temporary directory created by the agent and copied its contents into a visible, stable project folder.

### Conclusion for Experiment 2

The high-level `generate_repo` API is the **correct and robust method** for using MetaGPT in this environment. It successfully manages the entire agent lifecycle, but its output is sandboxed within the WSL filesystem. To access the results, a final step is required to locate and copy the generated project files to the desired location on the host machine.

---

## Overall Project Conclusion

This series of experiments was a valuable, albeit challenging, lesson in the practical use of the MetaGPT framework. The key takeaway is that the framework's behavior can be highly dependent on the execution environment and the specific API entry point used.

-   The **`Team` API proved unstable** in our WSL/Conda setup.
-   The **`generate_repo` API worked perfectly** but required a manual copy step to bridge the gap between the WSL's isolated filesystem and the host's visible filesystem.

This entire debugging process itself serves as a critical experiment, highlighting the importance of verifying not just *if* a process succeeds, but *where* and *how* it produces its output.

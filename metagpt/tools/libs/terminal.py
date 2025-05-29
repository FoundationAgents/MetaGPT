import asyncio
import os
import platform
import re
from asyncio import Queue
from asyncio.subprocess import PIPE, STDOUT
from typing import Optional

from metagpt.config2 import Config
from metagpt.const import DEFAULT_WORKSPACE_ROOT, SWE_SETUP_PATH
from metagpt.logs import logger
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.report import END_MARKER_VALUE, TerminalReporter


@register_tool()
class Terminal:
    """
    A tool for running terminal commands.
    Don't initialize a new instance of this class if one already exists.
    For commands that need to be executed within a Conda environment, it is recommended
    to use the `execute_in_conda_env` method.
    """

    def __init__(self):
        is_windows = platform.system().lower() == "windows"
        if is_windows:
            self.shell_command = ["cmd.exe", "/c"]
            self.command_terminator = "\r\n"
        else:
            self.shell_command = ["bash"]
            self.command_terminator = "\n"
            
        self.stdout_queue = Queue(maxsize=1000)
        self.observer = TerminalReporter()
        self.process: Optional[asyncio.subprocess.Process] = None
        # Commands in forbidden_terminal_commands will be replaced by 'pass' and return advice. Example: {"cmd":"forbidden_reason/advice"}
        self.forbidden_commands = {
            "run dev": "Use Deployer.deploy_to_public instead.",
            # serve command has a space after it,
            "serve ": "Use Deployer.deploy_to_public instead.",
        }

    async def _start_process(self):
        """Start a persistent shell process"""
        try:
            env = os.environ.copy()
            # No need to specify executable on Windows
            kwargs = {
                "stdin": PIPE,
                "stdout": PIPE,
                "stderr": STDOUT,
                "env": env,
                "cwd": DEFAULT_WORKSPACE_ROOT.absolute(),
            }
            
            if not platform.system().lower() == "windows":
                kwargs["executable"] = "bash"
            
            self.process = await asyncio.create_subprocess_exec(
                *self.shell_command,
                **kwargs
            )
            await self._check_state()
        except Exception as e:
            logger.error(f"Failed to start process: {str(e)}")
            raise

    async def _check_state(self):
        """Check terminal state, such as the current directory of the terminal process"""
        if platform.system().lower() == "windows":
            output = await self.run_command("cd")  # Use cd command on Windows
        else:
            output = await self.run_command("pwd")  # Use pwd command on Unix systems
        logger.info("The terminal is at: %s", output)

    async def run_command(self, cmd: str, daemon=False) -> str:
        """
        Executes a specified command in the terminal and streams the output back in real time.
        This command maintains state across executions, such as the current directory,
        allowing for sequential commands to be contextually aware.

        Args:
            cmd (str): The command to execute in the terminal.
            daemon (bool): If True, executes the command in an asynchronous task, allowing
                           the main program to continue execution.
        Returns:
            str: The command's output or an empty string if `daemon` is True. Remember that
                 when `daemon` is True, use the `get_stdout_output` method to get the output.
        """
        if self.process is None:
            await self._start_process()

        output = ""
        # Remove forbidden commands
        commands = re.split(r"\s*&&\s*", cmd)
        for cmd_name, reason in self.forbidden_commands.items():
            # "true" is a pass command in linux terminal.
            for index, command in enumerate(commands):
                if cmd_name in command:
                    output += f"Failed to execut {command}. {reason}\n"
                    commands[index] = "true"
        cmd = " && ".join(commands)

        # Send the command
        self.process.stdin.write((cmd + self.command_terminator).encode())
        self.process.stdin.write(
            f'echo "{END_MARKER_VALUE}"{self.command_terminator}'.encode()  # write EOF
        )  # Unique marker to signal command end
        await self.process.stdin.drain()
        if daemon:
            asyncio.create_task(self._read_and_process_output(cmd))
        else:
            output += await self._read_and_process_output(cmd)

        return output

    async def execute_in_conda_env(self, cmd: str, env, daemon=False) -> str:
        """
        Executes a given command within a specified Conda environment automatically without
        the need for manual activation. Users just need to provide the name of the Conda
        environment and the command to execute.

        Args:
            cmd (str): The command to execute within the Conda environment.
            env (str, optional): The name of the Conda environment to activate before executing the command.
                                 If not specified, the command will run in the current active environment.
            daemon (bool): If True, the command is run in an asynchronous task, similar to `run_command`,
                           affecting error logging and handling in the same manner.

        Returns:
            str: The command's output, or an empty string if `daemon` is True, with output processed
                 asynchronously in that case.

        Note:
            This function wraps `run_command`, prepending the necessary Conda activation commands
            to ensure the specified environment is active for the command's execution.
        """
        cmd = f"conda run -n {env} {cmd}"
        return await self.run_command(cmd, daemon=daemon)

    async def get_stdout_output(self) -> str:
        """
        Retrieves all collected output from background running commands and returns it as a string.

        Returns:
            str: The collected output from background running commands, returned as a string.
        """
        output_lines = []
        while not self.stdout_queue.empty():
            line = await self.stdout_queue.get()
            output_lines.append(line)
        return "\n".join(output_lines)

    async def _read_and_process_output(self, cmd, daemon=False) -> str:
        async with self.observer as observer:
            cmd_output = []
            await observer.async_report(cmd + self.command_terminator, "cmd")
            # report the command
            # Read the output until the unique marker is found.
            # We read bytes directly from stdout instead of text because when reading text,
            # '\r' is changed to '\n', resulting in excessive output.
            tmp = b""
            while True:
                output = tmp + await self.process.stdout.read(1)
                if not output:
                    continue
                *lines, tmp = output.splitlines(True)
                for line in lines:
                    line = line.decode()
                    ix = line.rfind(END_MARKER_VALUE)
                    if ix >= 0:
                        line = line[0:ix]
                        if line:
                            await observer.async_report(line, "output")
                            # report stdout in real-time
                            cmd_output.append(line)
                        return "".join(cmd_output)
                    # log stdout in real-time
                    await observer.async_report(line, "output")
                    cmd_output.append(line)
                    if daemon:
                        await self.stdout_queue.put(line)

    async def close(self):
        """Safely close the persistent shell process"""
        if self.process:
            try:
                if not self.process.stdin.is_closing():
                    self.process.stdin.close()
                if self.process.returncode is None:
                    self.process.kill()
                    await self.process.wait()
                self.process = None
            except Exception as e:
                logger.error(f"Error closing process: {str(e)}")
                # Ensure the process is terminated
                if self.process and self.process.returncode is None:
                    try:
                        self.process.kill()
                    except:
                        pass
                self.process = None

    def _normalize_path(self, path: str) -> str:
        """Normalize path to ensure it works correctly across different operating systems

        Args:
            path: Input path

        Returns:
            Normalized path
        """
        normalized = os.path.normpath(path)
        if platform.system().lower() == "windows":
            # Ensure backslashes are used on Windows
            normalized = normalized.replace('/', '\\')
        return normalized

    async def cd(self, path: str):
        """Change working directory

        Args:
            path: Target directory path
        """
        normalized_path = self._normalize_path(path)
        if os.path.exists(normalized_path):
            os.chdir(normalized_path)
            if self.output_queue:
                await self.output_queue.put(f"Changed directory to: {normalized_path}{self.command_terminator}")
        else:
            error_msg = f"Directory not found: {normalized_path}"
            if self.output_queue:
                await self.output_queue.put(error_msg + self.command_terminator)
            raise FileNotFoundError(error_msg)

    def __del__(self):
        """Ensure process is closed when object is destroyed"""
        if self.process and self.process.returncode is None:
            try:
                self.process.kill()
            except:
                pass
            self.process = None


@register_tool(include_functions=["run"])
class Bash(Terminal):
    """
    A class to run bash commands directly and provides custom shell functions.
    All custom functions in this class can ONLY be called via the `Bash.run` method.
    """

    def __init__(self):
        """init"""
        os.environ["SWE_CMD_WORK_DIR"] = str(Config.default().workspace.path)
        super().__init__()
        self.start_flag = False

    async def start(self):
        await self.run_command(f"cd {Config.default().workspace.path}")
        await self.run_command(f"source {SWE_SETUP_PATH}")

    async def run(self, cmd) -> str:
        """
        Executes a bash command.

        Args:
            cmd (str): The bash command to execute.

        Returns:
            str: The output of the command.

        This method allows for executing standard bash commands as well as
        utilizing several custom shell functions defined in the environment.

        Custom Shell Functions:

        - open <path> [<line_number>]
          Opens the file at the given path in the editor. If line_number is provided,
          the window will move to include that line.
          Arguments:
              path (str): The path to the file to open.
              line_number (int, optional): The line number to move the window to.
              If not provided, the window will start at the top of the file.

        - goto <line_number>
          Moves the window to show <line_number>.
          Arguments:
              line_number (int): The line number to move the window to.

        - scroll_down
          Moves the window down {WINDOW} lines.

        - scroll_up
          Moves the window up {WINDOW} lines.

        - create <filename>
          Creates and opens a new file with the given name.
          Arguments:
              filename (str): The name of the file to create.

        - search_dir_and_preview <search_term> [<dir>]
          Searches for search_term in all files in dir and gives their code preview
          with line numbers. If dir is not provided, searches in the current directory.
          Arguments:
              search_term (str): The term to search for.
              dir (str, optional): The directory to search in. Defaults to the current directory.

        - search_file <search_term> [<file>]
          Searches for search_term in file. If file is not provided, searches in the current open file.
          Arguments:
              search_term (str): The term to search for.
              file (str, optional): The file to search in. Defaults to the current open file.

        - find_file <file_name> [<dir>]
          Finds all files with the given name in dir. If dir is not provided, searches in the current directory.
          Arguments:
              file_name (str): The name of the file to search for.
              dir (str, optional): The directory to search in. Defaults to the current directory.

        - edit <start_line>:<end_line> <<EOF
          <replacement_text>
          EOF
          Line numbers start from 1. Replaces lines <start_line> through <end_line> (inclusive) with the given text in the open file.
          The replacement text is terminated by a line with only EOF on it. All of the <replacement text> will be entered, so make
          sure your indentation is formatted properly. Python files will be checked for syntax errors after the edit. If the system
          detects a syntax error, the edit will not be executed. Simply try to edit the file again, but make sure to read the error
          message and modify the edit command you issue accordingly. Issuing the same command a second time will just lead to the same
          error message again. All code modifications made via the 'edit' command must strictly follow the PEP8 standard.
          Arguments:
              start_line (int): The line number to start the edit at, starting from 1.
              end_line (int): The line number to end the edit at (inclusive), starting from 1.
              replacement_text (str): The text to replace the current selection with, must conform to PEP8 standards.

        - submit
          Submits your current code locally. it can only be executed once, the last action before the `end`.

        Note: Make sure to use these functions as per their defined arguments and behaviors.
        """
        if not self.start_flag:
            await self.start()
            self.start_flag = True

        return await self.run_command(cmd)

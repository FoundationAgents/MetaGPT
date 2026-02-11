import asyncio
import os
import re
import sys
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
        if sys.platform.startswith("win"):
            self.shell_command = ["cmd.exe"]  # Windows
            self.executable = None
            self.command_terminator = "\r\n"
            self.pwd_command = "cd"
        else:
            self.shell_command = ["bash"]  # Linux / macOS
            self.executable = "bash"
            self.command_terminator = "\n"
            self.pwd_command = "pwd"

        self.stdout_queue = Queue(maxsize=1000)
        self.observer = TerminalReporter()
        self.process: Optional[asyncio.subprocess.Process] = None
        #  The cmd in forbidden_terminal_commands will be replace by pass ana return the advise. example:{"cmd":"forbidden_reason/advice"}
        self.forbidden_commands = {
            "run dev": "Use Deployer.deploy_to_public instead.",
            # serve cmd have a space behind it,
            "serve ": "Use Deployer.deploy_to_public instead.",
        }

    async def _start_process(self):
        # Start a persistent shell process
        self.process = await asyncio.create_subprocess_exec(
            *self.shell_command,
            stdin=PIPE,
            stdout=PIPE,
            stderr=STDOUT,
            executable=self.executable,
        )

        # Start a background task to read output
        asyncio.create_task(self._read_output())

    async def _read_output(self):
        """
        Continuously read output from the shell process and put it into the queue.
        """
        while self.process and self.process.stdout:
            try:
                line = await self.process.stdout.readline()
                if not line:
                    break
                decoded_line = line.decode()
                await self.stdout_queue.put(decoded_line)
            except Exception as e:
                logger.error(f"Error reading output: {e}")
                break

    async def run_command(self, cmd) -> str:
        """
        Execute a shell command and return its output.
        """
        if not self.process:
            await self._start_process()

        # Check if command is forbidden
        for forbidden_cmd, advice in self.forbidden_commands.items():
            if cmd.strip().startswith(forbidden_cmd):
                return f"Command '{forbidden_cmd}' is forbidden. {advice}"

        # Write command to shell
        if self.process.stdin:
            full_cmd = cmd + self.command_terminator
            self.process.stdin.write(full_cmd.encode())
            await self.process.stdin.drain()

        # Add a unique marker to indicate the end of this command's output
        marker_cmd = f'echo "{END_MARKER_VALUE}"{self.command_terminator}'
        if self.process.stdin:
            self.process.stdin.write(marker_cmd.encode())
            await self.process.stdin.drain()

        # Collect output until we see our marker
        output_lines = []
        while True:
            try:
                line = await asyncio.wait_for(self.stdout_queue.get(), timeout=30)  # 30-second timeout
                if END_MARKER_VALUE in line:
                    break
                output_lines.append(line)
            except asyncio.TimeoutError:
                logger.warning(f"Command '{cmd}' timed out after 30 seconds")
                break

        output = "".join(output_lines).strip()
        self.observer.report(cmd, output)
        return output

    async def execute_in_conda_env(self, env_name: str, cmd: str) -> str:
        """Execute a command inside a specified Conda environment."""
        activate_cmd = f"conda activate {env_name} && {cmd}"
        return await self.run_command(activate_cmd)

    async def list_conda_envs(self) -> str:
        """List all available Conda environments."""
        return await self.run_command("conda env list")

    async def get_current_working_directory(self) -> str:
        """Get the current working directory."""
        return await self.run_command(self.pwd_command)

    async def change_directory(self, path: str) -> str:
        """Change the working directory."""
        return await self.run_command(f"cd {path}")

    async def list_files(self, path: str = ".") -> str:
        """List files in a directory."""
        if sys.platform.startswith("win"):
            return await self.run_command(f"dir {path}")
        else:
            return await self.run_command(f"ls -la {path}")

    async def read_file(self, file_path: str) -> str:
        """Read the content of a file."""
        if sys.platform.startswith("win"):
            return await self.run_command(f"type {file_path}")
        else:
            return await self.run_command(f"cat {file_path}")

    async def write_file(self, file_path: str, content: str) -> str:
        """Write content to a file."""
        # Escape the content properly for shell
        escaped_content = content.replace('"', '\\"').replace("$", "\\$")
        if sys.platform.startswith("win"):
            return await self.run_command(f'echo "{escaped_content}" > {file_path}')
        else:
            return await self.run_command(f'echo "{escaped_content}" > {file_path}')

    async def create_directory(self, dir_path: str) -> str:
        """Create a directory."""
        if sys.platform.startswith("win"):
            return await self.run_command(f"mkdir {dir_path}")
        else:
            return await self.run_command(f"mkdir -p {dir_path}")

    async def remove_file(self, file_path: str) -> str:
        """Remove a file."""
        if sys.platform.startswith("win"):
            return await self.run_command(f"del {file_path}")
        else:
            return await self.run_command(f"rm {file_path}")

    async def remove_directory(self, dir_path: str) -> str:
        """Remove a directory."""
        if sys.platform.startswith("win"):
            return await self.run_command(f"rmdir /s {dir_path}")
        else:
            return await self.run_command(f"rm -rf {dir_path}")

    async def copy_file(self, src: str, dest: str) -> str:
        """Copy a file."""
        if sys.platform.startswith("win"):
            return await self.run_command(f"copy {src} {dest}")
        else:
            return await self.run_command(f"cp {src} {dest}")

    async def move_file(self, src: str, dest: str) -> str:
        """Move a file."""
        if sys.platform.startswith("win"):
            return await self.run_command(f"move {src} {dest}")
        else:
            return await self.run_command(f"mv {src} {dest}")

    async def find_files(self, pattern: str, path: str = ".") -> str:
        """Find files matching a pattern."""
        if sys.platform.startswith("win"):
            return await self.run_command(f'dir {path}\\{pattern} /s')
        else:
            return await self.run_command(f'find {path} -name "{pattern}"')

    async def grep(self, pattern: str, file_path: str) -> str:
        """Search for a pattern in a file."""
        if sys.platform.startswith("win"):
            return await self.run_command(f'findstr "{pattern}" {file_path}')
        else:
            return await self.run_command(f'grep "{pattern}" {file_path}')

    async def stop(self):
        if self.process and self.process.stdin:
            self.process.stdin.close()
            await self.process.wait()


@register_tool(include_functions=["run"])
class Bash(Terminal):
    """
    A class to run bash commands directly and provides custom shell functions.
    All custom functions in this class can ONLY be called via the `Bash.run` method.
    
    Security Note: This class implements strict command validation to prevent 
    command injection attacks when exposed to LLM agents.
    """

    def __init__(self):
        """init"""
        os.environ["SWE_CMD_WORK_DIR"] = str(Config.default().workspace.path)
        super().__init__()
        self.start_flag = False
        
        # Define allowed commands and dangerous patterns for security
        self.safe_commands = {
            # File operations
            'ls', 'dir', 'pwd', 'cd', 'cat', 'head', 'tail', 'wc', 'find', 'grep', 'awk', 'sed',
            # Custom shell functions defined in the environment
            'open', 'goto', 'scroll_down', 'scroll_up', 'create', 'search_dir_and_preview',
            'search_file', 'find_file', 'edit', 'submit',
            # Safe development tools
            'git', 'python3', 'python', 'pip', 'node', 'npm', 'yarn', 'make', 'cmake',
            # Text processing
            'echo', 'printf', 'sort', 'uniq', 'cut', 'tr', 'paste', 'join'
        }
        
        self.dangerous_patterns = [
            # Network operations that could exfiltrate data or download malicious content
            r'\b(curl|wget|nc|netcat|telnet|ssh|scp|rsync|ftp|sftp)\b',
            # Destructive file operations
            r'\b(rm\s+-rf|rmdir|shred|dd)\b',
            # System modification
            r'\b(chmod\s+777|chown|su|sudo|passwd|useradd|usermod|userdel)\b',
            # Process control
            r'\b(kill|killall|pkill|nohup|crontab|at|batch)\b',
            # Shell metacharacters that could be used for command injection
            r'[;&|`$()]',
            # Redirection that could overwrite important files
            r'>.*/(etc|usr|bin|sbin|boot|sys|proc)',
            # Execution of arbitrary files
            r'\b(exec|eval|source|\.)\s',
        ]

    def _validate_command(self, cmd: str) -> tuple[bool, str]:
        """
        Validates if a command is safe to execute.
        
        Args:
            cmd (str): The command to validate
            
        Returns:
            tuple[bool, str]: (is_safe, reason_if_unsafe)
        """
        if not cmd or not cmd.strip():
            return False, "Empty command not allowed"
            
        cmd_clean = cmd.strip().lower()
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, cmd, re.IGNORECASE):
                return False, f"Command contains dangerous pattern: {pattern}"
        
        # Extract the base command (first word)
        base_cmd = cmd_clean.split()[0]
        
        # Allow custom shell functions and safe commands
        if base_cmd in self.safe_commands:
            return True, ""
            
        # Special case for common safe variations
        if base_cmd.startswith('python') and re.match(r'^python\d*(\.\d+)?$', base_cmd):
            return True, ""
            
        return False, f"Command '{base_cmd}' is not in the allowlist of safe commands"

    async def start(self):
        await self.run_command(f"cd {Config.default().workspace.path}")
        await self.run_command(f"source {SWE_SETUP_PATH}")

    async def run(self, cmd) -> str:
        """
        Executes a bash command with security validation.

        Args:
            cmd (str): The bash command to execute.

        Returns:
            str: The output of the command, or an error message if the command is unsafe.

        This method allows for executing standard bash commands as well as
        utilizing several custom shell functions defined in the environment.
        
        Security: Commands are validated against an allowlist and checked for
        dangerous patterns before execution to prevent command injection attacks.

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
          error message again. All code modifications made via the 'edit' command must strictly follow the PEP8 standards.
          Arguments:
              start_line (int): The line number to start the edit at, starting from 1.
              end_line (int): The line number to end the edit at (inclusive), starting from 1.
              replacement_text (str): The text to replace the current selection with, must conform to PEP8 standards.

        - submit
          Submits your current code locally. it can only be executed once, the last action before the `end`.

        Note: Make sure to use these functions as per their defined arguments and behaviors.
        """
        # Validate command for security before execution
        is_safe, reason = self._validate_command(cmd)
        if not is_safe:
            error_msg = f"SECURITY ERROR: Command blocked - {reason}\n"
            error_msg += f"Attempted command: {cmd}\n"
            error_msg += "Only safe, allowlisted commands are permitted for security."
            logger.warning(f"Blocked unsafe command from LLM: {cmd} - {reason}")
            return error_msg
        
        if not self.start_flag:
            await self.start()
            self.start_flag = True

        return await self.run_command(cmd)
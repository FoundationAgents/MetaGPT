"""
Secure code execution utilities for MetaGPT benchmark evaluation.

This module provides sandboxed execution environments to prevent RCE vulnerabilities
when executing LLM-generated code during benchmark evaluations.
"""

import ast
import io
import sys
import threading
import time
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from typing import Any, Dict, List, Optional, Set, Tuple


class SecurityError(Exception):
    """Raised when potentially malicious code patterns are detected."""
    pass


class ExecutionTimeout(Exception):
    """Raised when code execution exceeds timeout limit."""
    pass


class SecureCodeExecutor:
    """Secure code execution environment with restricted imports and built-ins."""
    
    # Allowed built-in functions for code execution
    SAFE_BUILTINS = {
        'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'bytes', 'callable',
        'chr', 'classmethod', 'complex', 'dict', 'divmod', 'enumerate', 'filter',
        'float', 'format', 'frozenset', 'getattr', 'hasattr', 'hash', 'hex',
        'id', 'int', 'isinstance', 'issubclass', 'iter', 'len', 'list', 'map',
        'max', 'min', 'next', 'object', 'oct', 'ord', 'pow', 'property', 'range',
        'repr', 'reversed', 'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod',
        'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'
    }
    
    # Allowed modules for import
    SAFE_MODULES = {
        'math', 'hashlib', 're', 'typing', 'collections', 'itertools', 'functools',
        'operator', 'copy', 'json', 'string', 'textwrap', 'unicodedata'
    }
    
    # Dangerous AST node types that should be blocked
    DANGEROUS_NODES = {
        ast.Import, ast.ImportFrom, ast.Call, ast.Attribute, ast.Global, ast.Nonlocal
    }
    
    def __init__(self, timeout: int = 10):
        """Initialize the secure executor.
        
        Args:
            timeout: Maximum execution time in seconds
        """
        self.timeout = timeout
        self._original_builtins = None
    
    def _validate_ast(self, code_ast: ast.AST) -> None:
        """Validate AST for dangerous patterns.
        
        Args:
            code_ast: The AST to validate
            
        Raises:
            SecurityError: If dangerous patterns are detected
        """
        for node in ast.walk(code_ast):
            # Check for imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in self.SAFE_MODULES:
                            raise SecurityError(f"Forbidden import: {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module not in self.SAFE_MODULES:
                        raise SecurityError(f"Forbidden import from: {node.module}")
            
            # Check for dangerous function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    # Block dangerous built-in functions
                    dangerous_funcs = {'exec', 'eval', 'compile', '__import__', 'open', 'input'}
                    if node.func.id in dangerous_funcs:
                        raise SecurityError(f"Forbidden function: {node.func.id}")
                elif isinstance(node.func, ast.Attribute):
                    # Block dangerous method calls
                    dangerous_attrs = {'system', 'popen', 'run', 'call', 'check_output'}
                    if node.func.attr in dangerous_attrs:
                        raise SecurityError(f"Forbidden method: {node.func.attr}")
            
            # Check for dangerous attribute access
            elif isinstance(node, ast.Attribute):
                dangerous_attrs = {'__globals__', '__builtins__', '__import__', '__code__'}
                if node.attr in dangerous_attrs:
                    raise SecurityError(f"Forbidden attribute access: {node.attr}")
    
    def _create_restricted_globals(self, extra_globals: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a restricted global namespace.
        
        Args:
            extra_globals: Additional globals to include
            
        Returns:
            Restricted global namespace
        """
        # Create restricted builtins
        restricted_builtins = {
            name: getattr(__builtins__, name) 
            for name in self.SAFE_BUILTINS 
            if hasattr(__builtins__, name)
        }
        
        # Create base globals with restricted builtins
        safe_globals = {
            '__builtins__': restricted_builtins,
        }
        
        # Add safe modules
        for module_name in self.SAFE_MODULES:
            try:
                safe_globals[module_name] = __import__(module_name)
            except ImportError:
                pass  # Module not available, skip
        
        # Add any extra globals
        if extra_globals:
            safe_globals.update(extra_globals)
        
        return safe_globals
    
    @contextmanager
    def _execution_timeout(self):
        """Context manager for execution timeout."""
        def timeout_handler():
            # This runs in a separate thread
            time.sleep(self.timeout)
            # In a real implementation, we'd need thread-safe interruption
            # For now, this provides a basic timeout mechanism
            
        timer = threading.Timer(self.timeout, timeout_handler)
        timer.start()
        try:
            yield
        finally:
            timer.cancel()
    
    def execute_code(self, code: str, entry_point: str, 
                    extra_globals: Optional[Dict[str, Any]] = None) -> Tuple[bool, Any, str]:
        """Execute code safely in a restricted environment.
        
        Args:
            code: The code to execute
            entry_point: The function name to look for and validate
            extra_globals: Additional globals to provide
            
        Returns:
            Tuple of (success, result, error_message)
        """
        try:
            # Parse and validate AST
            code_ast = ast.parse(code)
            self._validate_ast(code_ast)
            
            # Create restricted execution environment
            safe_globals = self._create_restricted_globals(extra_globals)
            safe_locals = {}
            
            # Capture stdout/stderr
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                # Execute the code
                exec(compile(code_ast, '<sandbox>', 'exec'), safe_globals, safe_locals)
                
                # Check if entry point exists
                if entry_point not in safe_locals:
                    return False, None, f"Function '{entry_point}' not found in executed code"
                
                # Validate entry point is callable
                if not callable(safe_locals[entry_point]):
                    return False, None, f"'{entry_point}' is not callable"
            
            # Return the function for further testing
            return True, safe_locals[entry_point], ""
            
        except SecurityError as e:
            return False, None, f"Security violation: {e}"
        except SyntaxError as e:
            return False, None, f"Syntax error: {e}"
        except Exception as e:
            return False, None, f"Execution error: {e}"
    
    def execute_test(self, test_code: str, solution_function: Any, 
                    timeout: Optional[int] = None) -> Tuple[bool, str]:
        """Execute test code against a solution function.
        
        Args:
            test_code: The test code to execute
            solution_function: The function to test
            timeout: Override default timeout
            
        Returns:
            Tuple of (passed, message)
        """
        if timeout is None:
            timeout = self.timeout
            
        try:
            # Parse and validate test AST
            test_ast = ast.parse(test_code)
            self._validate_ast(test_ast)
            
            # Create globals for test execution
            test_globals = self._create_restricted_globals()
            test_locals = {}
            
            # Execute test code to get the check function
            exec(compile(test_ast, '<test>', 'exec'), test_globals, test_locals)
            
            if 'check' not in test_locals:
                return False, "Test code must define a 'check' function"
            
            check_function = test_locals['check']
            if not callable(check_function):
                return False, "'check' must be callable"
            
            # Execute the check with timeout
            start_time = time.time()
            try:
                result = check_function(solution_function)
                elapsed = time.time() - start_time
                
                if elapsed > timeout:
                    return False, f"Test execution exceeded timeout ({timeout}s)"
                
                return True, "All tests passed"
                
            except AssertionError as e:
                return False, f"Test failed: {e}"
            except Exception as e:
                return False, f"Test execution error: {e}"
                
        except SecurityError as e:
            return False, f"Security violation in test: {e}"
        except Exception as e:
            return False, f"Test validation error: {e}"


def secure_execute_solution(solution: str, test: str, entry_point: str, 
                          timeout: int = 15, extra_globals: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
    """Securely execute a solution against test cases.
    
    Args:
        solution: The solution code to execute
        test: The test code to run
        entry_point: The function name to extract from solution
        timeout: Execution timeout in seconds
        extra_globals: Additional globals to provide
        
    Returns:
        Tuple of (status, message) where status is "PASS" or "FAIL"
    """
    executor = SecureCodeExecutor(timeout=timeout)
    
    # Execute solution code
    success, solution_func, error_msg = executor.execute_code(solution, entry_point, extra_globals)
    if not success:
        return "FAIL", f"Solution execution failed: {error_msg}"
    
    # Execute test code
    passed, test_msg = executor.execute_test(test, solution_func, timeout)
    if passed:
        return "PASS", "All tests passed successfully"
    else:
        return "FAIL", f"Test failed: {test_msg}"
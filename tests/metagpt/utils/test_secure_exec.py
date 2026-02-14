"""
Test suite for secure code execution utilities.

This test suite validates that the security fixes prevent RCE vulnerabilities
while maintaining functionality for legitimate code execution.
"""

import pytest

from metagpt.utils.secure_exec import SecureCodeExecutor, secure_execute_solution, SecurityError


class TestSecureCodeExecutor:
    """Test the SecureCodeExecutor class."""

    def test_legitimate_code_execution(self):
        """Test that legitimate code executes correctly."""
        executor = SecureCodeExecutor(timeout=5)
        
        # Simple function that should work
        code = """
def solve(n):
    return n * 2
"""
        success, func, error_msg = executor.execute_code(code, "solve")
        assert success, f"Expected success, got error: {error_msg}"
        assert callable(func)
        assert func(5) == 10

    def test_math_imports_allowed(self):
        """Test that safe imports like math are allowed."""
        executor = SecureCodeExecutor()
        
        code = """
import math
def solve(x):
    return math.sqrt(x)
"""
        success, func, error_msg = executor.execute_code(code, "solve")
        assert success, f"Math import should be allowed: {error_msg}"
        assert abs(func(4) - 2.0) < 0.001

    def test_os_import_blocked(self):
        """Test that dangerous imports like os are blocked."""
        executor = SecureCodeExecutor()
        
        code = """
import os
def solve(x):
    return x
"""
        success, func, error_msg = executor.execute_code(code, "solve")
        assert not success
        assert "os" in error_msg.lower()

    def test_subprocess_import_blocked(self):
        """Test that subprocess imports are blocked."""
        executor = SecureCodeExecutor()
        
        code = """
import subprocess
def solve(x):
    return x
"""
        success, func, error_msg = executor.execute_code(code, "solve")
        assert not success
        assert "subprocess" in error_msg.lower()

    def test_exec_function_blocked(self):
        """Test that exec() function calls are blocked."""
        executor = SecureCodeExecutor()
        
        code = """
def solve(x):
    exec("print('malicious')")
    return x
"""
        success, func, error_msg = executor.execute_code(code, "solve")
        assert not success
        assert "exec" in error_msg.lower()

    def test_eval_function_blocked(self):
        """Test that eval() function calls are blocked.""" 
        executor = SecureCodeExecutor()
        
        code = """
def solve(x):
    result = eval("2 + 2")
    return result
"""
        success, func, error_msg = executor.execute_code(code, "solve")
        assert not success
        assert "eval" in error_msg.lower()

    def test_system_call_blocked(self):
        """Test that os.system calls are blocked."""
        executor = SecureCodeExecutor()
        
        # This should be blocked at the import level
        code = """
def solve(x):
    import os
    os.system('touch /tmp/rce_proof')
    return x
"""
        success, func, error_msg = executor.execute_code(code, "solve")
        assert not success
        assert ("os" in error_msg.lower() or "import" in error_msg.lower())

    def test_open_function_blocked(self):
        """Test that open() function is blocked."""
        executor = SecureCodeExecutor()
        
        code = """
def solve(x):
    f = open('/etc/passwd', 'r')
    return f.read()
"""
        success, func, error_msg = executor.execute_code(code, "solve") 
        assert not success
        assert "open" in error_msg.lower()

    def test_globals_attribute_blocked(self):
        """Test that __globals__ attribute access is blocked."""
        executor = SecureCodeExecutor()
        
        code = """
def solve(x):
    return solve.__globals__
"""
        success, func, error_msg = executor.execute_code(code, "solve")
        assert not success
        assert "globals" in error_msg.lower()

    def test_builtins_attribute_blocked(self):
        """Test that __builtins__ attribute access is blocked."""
        executor = SecureCodeExecutor()
        
        code = """
def solve(x):
    return __builtins__
"""  
        success, func, error_msg = executor.execute_code(code, "solve")
        assert not success
        assert "builtins" in error_msg.lower()

    def test_malicious_import_payload(self):
        """Test the exact RCE payload from the vulnerability report."""
        executor = SecureCodeExecutor()
        
        # This is the payload from the vulnerability report
        payload = """
import os
def solve(x):
    os.system('touch /tmp/simple_rce_proof')
    return x
"""
        success, func, error_msg = executor.execute_code(payload, "solve")
        assert not success
        assert "os" in error_msg.lower()

    def test_complex_legitimate_function(self):
        """Test that complex legitimate code works."""
        executor = SecureCodeExecutor()
        
        code = """
import math
from typing import List

def solve(numbers: List[int]) -> float:
    if not numbers:
        return 0.0
    return math.sqrt(sum(x**2 for x in numbers)) / len(numbers)
"""
        success, func, error_msg = executor.execute_code(code, "solve")
        assert success, f"Complex legitimate code failed: {error_msg}"
        result = func([3, 4])
        expected = math.sqrt((9 + 16)) / 2
        assert abs(result - expected) < 0.001


class TestSecureExecuteSolution:
    """Test the secure_execute_solution function."""

    def test_successful_solution_execution(self):
        """Test successful execution of solution with test."""
        solution = """
def add_two_numbers(a, b):
    return a + b
"""
        test = """
def check(func):
    assert func(2, 3) == 5
    assert func(-1, 1) == 0
"""
        
        status, message = secure_execute_solution(
            solution=solution,
            test=test,
            entry_point="add_two_numbers",
            timeout=5
        )
        
        assert status == "PASS"
        assert "passed" in message.lower()

    def test_failing_solution_execution(self):
        """Test execution of solution that fails tests."""
        solution = """
def add_two_numbers(a, b):
    return a - b  # Wrong implementation
"""
        test = """
def check(func):
    assert func(2, 3) == 5  # This will fail
"""
        
        status, message = secure_execute_solution(
            solution=solution,
            test=test,
            entry_point="add_two_numbers",
            timeout=5
        )
        
        assert status == "FAIL"
        assert "failed" in message.lower()

    def test_malicious_solution_blocked(self):
        """Test that malicious solutions are blocked."""
        malicious_solution = """
import os
def add_two_numbers(a, b):
    os.system('rm -rf /')  # Malicious payload
    return a + b
"""
        test = """
def check(func):
    assert func(2, 3) == 5
"""
        
        status, message = secure_execute_solution(
            solution=malicious_solution,
            test=test,
            entry_point="add_two_numbers", 
            timeout=5
        )
        
        assert status == "FAIL"
        assert ("security" in message.lower() or "forbidden" in message.lower())

    def test_malicious_test_blocked(self):
        """Test that malicious test code is blocked."""
        solution = """
def add_two_numbers(a, b):
    return a + b
"""
        malicious_test = """
import subprocess
def check(func):
    subprocess.run(['rm', '-rf', '/'])  # Malicious payload
    assert func(2, 3) == 5
"""
        
        status, message = secure_execute_solution(
            solution=solution,
            test=malicious_test,
            entry_point="add_two_numbers",
            timeout=5
        )
        
        assert status == "FAIL"
        assert ("security" in message.lower() or "forbidden" in message.lower())


class TestRegressionTests:
    """Regression tests to ensure existing functionality works."""

    def test_humaneval_style_function(self):
        """Test a function in the style of HumanEval benchmark."""
        solution = '''
def has_close_elements(numbers, threshold):
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if abs(numbers[i] - numbers[j]) < threshold:
                return True
    return False
'''
        test = '''
def check(func):
    assert func([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) == True
    assert func([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) == False
    assert func([1.0, 2.0, 5.9, 4.0, 5.0], 0.95) == True
    assert func([1.0, 2.0, 5.9, 4.0, 5.0], 0.8) == False
    assert func([1.0, 2.0, 3.0, 4.0, 5.0, 2.0], 0.02) == True
    assert func([1.1, 2.2, 3.1, 4.1, 5.1], 1.0) == True
    assert func([1.1, 2.2, 3.1, 4.1, 5.1], 0.5) == False
'''
        
        status, message = secure_execute_solution(
            solution=solution,
            test=test,
            entry_point="has_close_elements"
        )
        
        assert status == "PASS"

    def test_mbpp_style_function(self):
        """Test a function in the style of MBPP benchmark."""
        solution = '''
def similar_elements(test_tup1, test_tup2):
    return tuple(set(test_tup1) & set(test_tup2))
'''
        test = '''
def check(func):
    assert func((3, 4, 5, 6), (5, 7, 4, 10)) == (4, 5)
    assert func((1, 2, 3, 4), (5, 4, 3, 7)) == (3, 4) 
    assert func((11, 12, 14, 13), (17, 15, 14, 13)) == (14, 13)
'''
        
        status, message = secure_execute_solution(
            solution=solution,
            test=test,
            entry_point="similar_elements"
        )
        
        assert status == "PASS"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
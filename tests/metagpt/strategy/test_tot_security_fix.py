#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test for Tree-of-Thought security fix (issue #1933)
Tests that eval() vulnerability is fixed and JSON parsing works correctly.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch

from metagpt.strategy.tot import ThoughtSolverBase, ThoughtTree, ThoughtNode
from metagpt.strategy.tot_schema import ThoughtSolverConfig


@pytest.mark.asyncio
async def test_generate_thoughts_safe_json_parsing():
    """Test that generate_thoughts safely parses JSON and rejects malicious code."""
    
    # Setup
    solver = ThoughtSolverBase()
    solver.thought_tree = ThoughtTree(ThoughtNode("test"))
    
    # Valid JSON response - should work
    valid_json_response = '''
Here are the solutions:

```json
[
    {"node_id": "1", "node_state_instruction": "solution 1"},
    {"node_id": "2", "node_state_instruction": "solution 2"}
]
```
'''
    
    # Malicious code that would execute with eval() - should be safely rejected
    malicious_response = '''
Here are the solutions:

```json
__import__('os').system('echo "RCE_EXECUTED" > /tmp/test_rce.txt') or [{"node_id": "1", "node_state_instruction": "legitimate thought"}]
```
'''
    
    # Invalid JSON - should be handled gracefully  
    invalid_json_response = '''
Here are the solutions:

```json
{"invalid": "json", missing_bracket: true
```
'''

    # Mock the LLM and other dependencies
    with patch.object(solver.llm, 'aask', new_callable=AsyncMock) as mock_aask:
        with patch.object(solver.thought_tree, 'update_node') as mock_update:
            
            # Test 1: Valid JSON should be parsed correctly
            mock_aask.return_value = valid_json_response
            await solver.generate_thoughts("test_state")
            
            # Should call update_node with parsed JSON list
            mock_update.assert_called_once()
            args = mock_update.call_args[0]
            assert isinstance(args[0], list)
            assert len(args[0]) == 2
            assert args[0][0]['node_id'] == "1"
            
            mock_update.reset_mock()
            
            # Test 2: Malicious code should not execute and should return empty list
            mock_aask.return_value = malicious_response
            await solver.generate_thoughts("test_state") 
            
            # Should call update_node with empty list (due to JSON parse error)
            mock_update.assert_called_once()
            args = mock_update.call_args[0]
            assert args[0] == []  # Should be empty due to JSON parse failure
            
            mock_update.reset_mock()
            
            # Test 3: Invalid JSON should be handled gracefully
            mock_aask.return_value = invalid_json_response
            await solver.generate_thoughts("test_state")
            
            # Should call update_node with empty list due to JSON parse error
            mock_update.assert_called_once()
            args = mock_update.call_args[0]
            assert args[0] == []


def test_malicious_code_does_not_execute():
    """Verify that malicious code is not executed during JSON parsing."""
    import os
    import tempfile
    
    # Create a temp file path for testing
    test_file = os.path.join(tempfile.gettempdir(), 'security_test_rce.txt')
    
    # Remove file if it exists
    if os.path.exists(test_file):
        os.remove(test_file)
    
    # Simulate what CodeParser.parse_code() would extract from malicious response
    malicious_code = f"__import__('os').system('echo RCE > {test_file}') or []"
    
    # Test that json.loads safely rejects this (should raise JSONDecodeError)
    try:
        result = json.loads(malicious_code)
        assert False, "JSON parsing should have failed on malicious code"
    except json.JSONDecodeError:
        # This is expected - JSON parsing should fail
        pass
    
    # Verify the malicious code was not executed
    assert not os.path.exists(test_file), "Malicious code should not have been executed"


if __name__ == "__main__":
    pytest.main([__file__])
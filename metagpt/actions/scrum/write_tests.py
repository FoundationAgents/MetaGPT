#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WriteTests Action - QA Engineer writes tests.
Following MetaGPT Action pattern from examples.
"""
import re
from metagpt.actions import Action


def parse_code(rsp: str) -> str:
    """Extract code from markdown code blocks."""
    pattern = r"```(?:python|javascript|typescript)?(.*)```"
    match = re.search(pattern, rsp, re.DOTALL)
    code_text = match.group(1).strip() if match else rsp
    return code_text


class WriteTests(Action):
    """Action for QA Engineer to write tests."""
    
    PROMPT_TEMPLATE: str = """
You are a QA Engineer. Based on the following code implementation, write comprehensive tests.

Code to test:
{context}

Write tests that:
1. Cover all main functionality
2. Include edge cases
3. Test error handling
4. Use proper assertions
5. Follow testing best practices

Return your tests using pytest format:
```python
import pytest

# Your test code here
def test_main_functionality():
    # Test implementation
    pass

def test_edge_cases():
    # Test implementation
    pass
```

Include {k} test cases minimum.
"""
    
    name: str = "WriteTests"
    
    async def run(self, context: str, k: int = 5) -> str:
        """
        Write tests for the given code.
        
        Args:
            context: Code implementation to test
            k: Minimum number of test cases
            
        Returns:
            Test code
        """
        prompt = self.PROMPT_TEMPLATE.format(context=context, k=k)
        rsp = await self._aask(prompt)
        code = parse_code(rsp)
        return code

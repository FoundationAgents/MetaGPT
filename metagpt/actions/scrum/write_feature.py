#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WriteFeature Action - Engineer implements features.
Following MetaGPT Action pattern from examples.
"""
import re
from metagpt.actions import Action


def parse_code(rsp: str) -> str:
    """Extract code from markdown code blocks."""
    pattern = r"```(?:python|javascript|typescript|html|css)?(.*)```"
    match = re.search(pattern, rsp, re.DOTALL)
    code_text = match.group(1).strip() if match else rsp
    return code_text


class WriteFeature(Action):
    """Action for Engineer to implement features."""
    
    PROMPT_TEMPLATE: str = """
You are a Senior Software Engineer. Based on the following design and task, implement the feature.

Context (Design/Requirements):
{context}

Your task:
1. Write clean, well-documented code
2. Follow best practices and coding standards
3. Include inline comments for complex logic
4. Handle edge cases and errors gracefully

Return your implementation as:
```python
# your code here
```

Or for web features:
```javascript
// your code here
```

Include all necessary imports and dependencies.
"""
    
    name: str = "WriteFeature"
    
    async def run(self, context: str) -> str:
        """
        Implement a feature based on design and requirements.
        
        Args:
            context: Design document and task description
            
        Returns:
            Implementation code
        """
        prompt = self.PROMPT_TEMPLATE.format(context=context)
        rsp = await self._aask(prompt)
        code = parse_code(rsp)
        return code

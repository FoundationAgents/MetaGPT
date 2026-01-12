#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/09
@Author  : MetaGPT-Pro Team
@File    : requirement_enhancer.py
@Desc    : AI-powered requirement refinement using ProductManager personality
"""
from typing import List, Optional
from metagpt.logs import logger
from metagpt.config2 import config
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.conversation.schemas import EnhancedRequirements, ConversationMessage


ENHANCEMENT_PROMPT = """You are Alice, an experienced Product Manager. Your task is to transform a rough user idea into structured product requirements.

## Conversation History
{conversation_history}

## Current User Idea
{idea}

## Your Task
Based on the conversation, create a structured requirements document with the following sections:

1. **Project Name**: A short, descriptive snake_case name (e.g., "todo_app", "snake_game")
2. **Core Features**: List 3-5 key features the product should have
3. **User Stories**: Write 3-5 user stories in "As a [user], I want [feature] so that [benefit]" format
4. **Technical Assumptions**: List assumptions about the tech stack, platform, etc.
5. **Constraints**: Any limitations or requirements mentioned
6. **Platform**: The target platform (Web, CLI, Mobile, Desktop)
7. **Programming Language**: Suggested programming language/framework

Respond in JSON format:
```json
{{
    "project_name": "...",
    "original_idea": "...",
    "core_features": ["...", "..."],
    "user_stories": ["As a ...", "As a ..."],
    "technical_assumptions": ["...", "..."],
    "constraints": ["...", "..."],
    "platform": "...",
    "programming_language": "..."
}}
```
"""

CLARIFYING_QUESTIONS_PROMPT = """You are Alice, an experienced Product Manager. Based on the user's idea, generate 2-3 clarifying questions to better understand their requirements.

## User's Idea
{idea}

## Already Discussed
{already_discussed}

Generate questions about aspects NOT yet clarified:
- Platform (web, mobile, CLI, desktop)?
- Core functionality specifics?
- Target users?
- Any special features or constraints?

Respond with a JSON array of questions:
```json
["Question 1?", "Question 2?", "Question 3?"]
```
"""


class RequirementEnhancer:
    """Enhances rough user requirements into structured PRD using LLM"""
    
    def __init__(self):
        self.llm = None
    
    def _get_llm(self):
        """Lazy initialization of LLM"""
        if self.llm is None:
            self.llm = create_llm_instance(config.llm)
        return self.llm
    
    async def enhance(
        self, 
        idea: str, 
        conversation_history: List[ConversationMessage] = None
    ) -> EnhancedRequirements:
        """
        Transform rough idea into structured requirements.
        
        Args:
            idea: The original user idea
            conversation_history: Previous conversation messages
            
        Returns:
            EnhancedRequirements with structured data
        """
        llm = self._get_llm()
        
        # Format conversation history
        history_str = ""
        if conversation_history:
            for msg in conversation_history:
                role = "User" if msg.role == "user" else "Alice (PM)"
                history_str += f"{role}: {msg.content}\n"
        
        prompt = ENHANCEMENT_PROMPT.format(
            conversation_history=history_str or "No prior conversation.",
            idea=idea
        )
        
        try:
            response = await llm.aask(prompt)
            # Parse JSON from response
            import json
            import re
            
            # Extract JSON from markdown code block if present
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
            
            data = json.loads(json_str)
            return EnhancedRequirements(
                project_name=data.get("project_name", ""),
                original_idea=idea,
                core_features=data.get("core_features", []),
                user_stories=data.get("user_stories", []),
                technical_assumptions=data.get("technical_assumptions", []),
                constraints=data.get("constraints", []),
                platform=data.get("platform", ""),
                programming_language=data.get("programming_language", "")
            )
        except Exception as e:
            logger.exception(f"Failed to enhance requirements: {e}")
            # Return basic structure on failure
            return EnhancedRequirements(
                original_idea=idea,
                core_features=["Feature based on: " + idea],
            )
    
    async def generate_clarifying_questions(
        self,
        idea: str,
        already_discussed: List[str] = None
    ) -> List[str]:
        """
        Generate clarifying questions for the user.
        
        Args:
            idea: The user's initial idea
            already_discussed: Topics already covered
            
        Returns:
            List of clarifying questions
        """
        llm = self._get_llm()
        
        discussed_str = "\n".join(already_discussed) if already_discussed else "Nothing yet."
        
        prompt = CLARIFYING_QUESTIONS_PROMPT.format(
            idea=idea,
            already_discussed=discussed_str
        )
        
        try:
            print(f"DEBUG: RequirementEnhancer.generate_clarifying_questions calling LLM...")
            # print(f"DEBUG: Prompt: {prompt}")
            response = await llm.aask(prompt)
            print(f"DEBUG: LLM Response received: {response[:100]}...")
            import json
            import re
            
            # Extract JSON from markdown code block if present
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
            
            questions = json.loads(json_str)
            return questions if isinstance(questions, list) else []
        except Exception as e:
            logger.exception(f"Failed to generate questions: {e}")
            return [
                "What platform should this run on (Web, CLI, Mobile)?",
                "Are there any specific features you'd like to prioritize?"
            ]

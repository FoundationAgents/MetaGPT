#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/09
@Author  : MetaGPT-Pro Team
@File    : conversation_manager.py
@Desc    : Manages conversation sessions with AI Product Manager
"""
from typing import Dict, Optional, List
from datetime import datetime
from metagpt.logs import logger
from metagpt.config2 import config
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.conversation.schemas import (
    ConversationSession,
    ConversationMessage,
    ConversationStatus,
    EnhancedRequirements,
)
from metagpt.conversation.requirement_enhancer import RequirementEnhancer
from metagpt.conversation.approval_workflow import ApprovalWorkflow


FIRST_QUESTION_PROMPT = """You are Alice, an experienced Product Manager at a software company. 
A user has just shared an initial idea for a project they want to build.

## User's Idea
{idea}

## Your Task
Ask 2-3 clarifying questions to better understand their requirements. Be friendly and professional.
Focus on:
1. Platform (web, mobile, CLI, desktop)
2. Key features or functionality
3. Target users
4. Any specific constraints or preferences

Keep your response concise and conversational. End with your questions.
"""

CONVERSATION_PROMPT = """You are Alice, an experienced Product Manager at a software company.
You're in a conversation with a user to clarify their project requirements.

## Conversation History
{history}

## Latest User Message
{message}

## Your Task
1. Acknowledge their response
2. If there are still unclear aspects, ask 1-2 follow-up questions
3. If requirements seem clear, summarize what you understand and ask if they're ready to proceed

Keep your response concise and conversational.
If the user says "yes", "approved", "let's start", or similar, indicate that requirements are ready for approval.
"""


class ConversationManager:
    """Singleton manager for conversation sessions"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConversationManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._sessions: Dict[str, ConversationSession] = {}
        self._enhancer = RequirementEnhancer()
        self._approval = ApprovalWorkflow()
        self._llm = None
        self._initialized = True
    
    def _get_llm(self):
        """Lazy initialization of LLM"""
        if self._llm is None:
            self._llm = create_llm_instance(config.llm)
        return self._llm
    
    async def start_session(self, initial_idea: str) -> tuple[str, str]:
        print(f"DEBUG: ConversationManager.start_session called with: {initial_idea}")
        """
        Start a new conversation session.
        
        Args:
            initial_idea: The user's initial project idea
            
        Returns:
            Tuple of (conversation_id, first_ai_question)
        """
        # Create new session
        session = ConversationSession(initial_idea=initial_idea)
        
        # Add user's initial message
        user_msg = ConversationMessage(role="user", content=initial_idea)
        session.messages.append(user_msg)
        
        # Initialize LLM and generate first question
        try:
            print("DEBUG: Calling enhancer.generate_clarifying_questions...")
            questions = await self._enhancer.generate_clarifying_questions(initial_idea)
            
            first_q = questions[0] if questions else "Could you provide more details about the platform and key features?"
        except Exception as e:
            logger.exception(f"Failed to generate opening question: {e}")
            print(f"DEBUG: Exception in generate_clarifying_questions: {e}")
            first_q = "Could you tell me more about what you want to build?"
            
        session.messages.append(ConversationMessage(role="assistant", content=first_q))
        
        # Store session
        self._sessions[session.id] = session
        
        # Persist to disk
        await self._approval.save_session(session)
        
        logger.info(f"Started conversation session: {session.id}")
        return session.id, first_q
    
    async def add_message(self, conversation_id: str, user_message: str) -> tuple[str, Optional[EnhancedRequirements], bool]:
        """
        Add a user message to the conversation and get AI response.
        
        Args:
            conversation_id: The conversation ID
            user_message: The user's message
            
        Returns:
            Tuple of (ai_response, enhanced_requirements, requires_approval)
        """
        session = await self.get_session(conversation_id)
        if not session:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        if session.status == ConversationStatus.APPROVED:
            raise ValueError(f"Conversation {conversation_id} is already approved")
        
        # Add user message
        user_msg = ConversationMessage(role="user", content=user_message)
        session.messages.append(user_msg)
        
        # Format conversation history
        history_str = ""
        for msg in session.messages[:-1]:  # Exclude latest message
            role = "User" if msg.role == "user" else "Alice (PM)"
            history_str += f"{role}: {msg.content}\n\n"
        
        # Generate AI response
        llm = self._get_llm()
        prompt = CONVERSATION_PROMPT.format(
            history=history_str,
            message=user_message
        )
        
        try:
            ai_response = await llm.aask(prompt)
        except Exception as e:
            logger.exception(f"Failed to generate AI response: {e}")
            ai_response = "I understand. Let me process that. Is there anything else you'd like to add?"
        
        # Add AI response
        ai_msg = ConversationMessage(role="assistant", content=ai_response)
        session.messages.append(ai_msg)
        
        # Check if ready for approval
        approval_keywords = ["ready to proceed", "let's start", "approved", "yes", "go ahead", "start development"]
        requires_approval = any(kw in user_message.lower() for kw in approval_keywords)
        
        # Generate enhanced requirements periodically
        enhanced = None
        if requires_approval or len(session.messages) >= 4:
            try:
                enhanced = await self._enhancer.enhance(
                    session.initial_idea,
                    session.messages
                )
                session.enhanced_requirements = enhanced
                session.status = ConversationStatus.PENDING_APPROVAL if requires_approval else ConversationStatus.ACTIVE
            except Exception as e:
                logger.exception(f"Failed to enhance requirements: {e}")
        
        session.updated_at = datetime.now()
        
        # Persist session
        await self._approval.save_session(session)
        self._sessions[conversation_id] = session
        
        return ai_response, enhanced, requires_approval
    
    async def get_session(self, conversation_id: str) -> Optional[ConversationSession]:
        """Get a conversation session by ID"""
        # Check memory cache first
        if conversation_id in self._sessions:
            return self._sessions[conversation_id]
        
        # Try loading from disk
        session = await self._approval.load_session(conversation_id)
        if session:
            self._sessions[conversation_id] = session
        return session
    
    async def enhance_requirements(self, conversation_id: str) -> EnhancedRequirements:
        """
        Trigger requirement enhancement for a conversation.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            Enhanced requirements
        """
        session = await self.get_session(conversation_id)
        if not session:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        enhanced = await self._enhancer.enhance(
            session.initial_idea,
            session.messages
        )
        
        # Update session
        session.enhanced_requirements = enhanced
        session.version += 1
        session.updated_at = datetime.now()
        
        await self._approval.save_session(session)
        self._sessions[conversation_id] = session
        
        return enhanced
    
    async def approve(self, conversation_id: str) -> str:
        """
        Approve requirements and lock them for development.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            Project ID
        """
        session = await self.get_session(conversation_id)
        if not session:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Ensure we have enhanced requirements
        if not session.enhanced_requirements:
            session.enhanced_requirements = await self._enhancer.enhance(
                session.initial_idea,
                session.messages
            )
        
        # Lock requirements
        project_id = await self._approval.lock_requirements(session)
        
        # Update cache
        self._sessions[conversation_id] = session
        
        return project_id
    
    async def get_approved_requirement_text(self, conversation_id: str) -> Optional[str]:
        """Get the approved requirement as a formatted string for MetaGPT"""
        approved = await self._approval.get_approved_requirement(conversation_id)
        if not approved or not approved.get("requirements"):
            return None
        
        req = approved["requirements"]
        
        # Format as a requirement string that MetaGPT can process
        text = f"""# Project: {req.get('project_name', 'Untitled')}

## Original Requirement
{req.get('original_idea', '')}

## Core Features
{chr(10).join('- ' + f for f in req.get('core_features', []))}

## User Stories
{chr(10).join('- ' + s for s in req.get('user_stories', []))}

## Technical Assumptions
{chr(10).join('- ' + a for a in req.get('technical_assumptions', []))}

## Constraints
{chr(10).join('- ' + c for c in req.get('constraints', []))}

## Platform
{req.get('platform', 'Not specified')}

## Programming Language
{req.get('programming_language', 'Not specified')}
"""
        return text


# Global instance
conversation_manager = ConversationManager()

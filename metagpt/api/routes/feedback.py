#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/13
@Author  : MetaGPT-Pro Team
@File    : feedback.py
@Desc    : API routes for feedback analysis and classification
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from metagpt.logs import logger

router = APIRouter()


class FeedbackAnalyzeRequest(BaseModel):
    project_id: str
    description: str


class FeedbackAnalyzeResponse(BaseModel):
    classification: str  # bug, feature, enhancement, change
    suggested_title: str
    summary: str
    priority: str  # critical, high, medium, low


# Keywords for classification
BUG_KEYWORDS = ['bug', 'error', 'issue', 'problem', 'broken', 'crash', 'fail', 'not working', 
                'doesn\'t work', 'wrong', 'incorrect', 'fix', 'exception', 'undefined']
FEATURE_KEYWORDS = ['new feature', 'add', 'implement', 'create', 'build', 'develop', 
                    'want to', 'would like', 'need to', 'please add', 'can you add']
ENHANCEMENT_KEYWORDS = ['improve', 'enhance', 'better', 'optimize', 'faster', 'performance',
                        'upgrade', 'update', 'refactor', 'clean up', 'polish']
CHANGE_KEYWORDS = ['change', 'modify', 'update', 'move', 'rename', 'different', 
                   'instead', 'replace', 'switch']


def classify_feedback(description: str) -> tuple[str, str]:
    """Classify feedback based on keywords and context"""
    lower_desc = description.lower()
    
    # Check for bug indicators first (highest priority match)
    bug_score = sum(1 for kw in BUG_KEYWORDS if kw in lower_desc)
    feature_score = sum(1 for kw in FEATURE_KEYWORDS if kw in lower_desc)
    enhancement_score = sum(1 for kw in ENHANCEMENT_KEYWORDS if kw in lower_desc)
    change_score = sum(1 for kw in CHANGE_KEYWORDS if kw in lower_desc)
    
    scores = {
        'bug': bug_score,
        'feature': feature_score,
        'enhancement': enhancement_score,
        'change': change_score
    }
    
    # Get highest scoring classification
    max_score = max(scores.values())
    if max_score == 0:
        # Default to 'feature' if no keywords match - it's usually someone wanting something new
        return 'feature', 'medium'
    
    classification = max(scores, key=scores.get)
    
    # Determine priority based on urgency words
    priority = 'medium'
    if any(word in lower_desc for word in ['urgent', 'critical', 'asap', 'immediately', 'blocker', 'crash']):
        priority = 'critical'
    elif any(word in lower_desc for word in ['important', 'high priority', 'soon', 'major']):
        priority = 'high'
    elif any(word in lower_desc for word in ['minor', 'low priority', 'nice to have', 'whenever']):
        priority = 'low'
    
    return classification, priority


def generate_title(description: str, classification: str) -> str:
    """Generate a concise title from the description"""
    # Take first sentence or first N characters
    first_sentence = description.split('.')[0].split('!')[0].split('?')[0]
    
    if len(first_sentence) > 60:
        title = first_sentence[:57] + '...'
    else:
        title = first_sentence
    
    # Clean up
    title = title.strip()
    if not title:
        title = f"User {classification.capitalize()} Request"
    
    return title


def generate_summary(description: str) -> str:
    """Generate a brief summary"""
    if len(description) <= 150:
        return description
    
    # Find a good break point
    summary = description[:147] + '...'
    return summary


@router.post("/analyze", response_model=FeedbackAnalyzeResponse)
async def analyze_feedback(req: FeedbackAnalyzeRequest):
    """
    Analyze and classify user feedback using AI.
    
    Categories:
    - bug: Something is broken or not working correctly
    - feature: Request for new functionality
    - enhancement: Improvement to existing functionality
    - change: Modification to existing behavior
    """
    try:
        logger.info(f"Analyzing feedback for project {req.project_id}: {req.description[:100]}...")
        
        # Classify the feedback
        classification, priority = classify_feedback(req.description)
        
        # Generate a title
        suggested_title = generate_title(req.description, classification)
        
        # Generate summary
        summary = generate_summary(req.description)
        
        logger.info(f"Classified as: {classification} (priority: {priority})")
        
        return FeedbackAnalyzeResponse(
            classification=classification,
            suggested_title=suggested_title,
            summary=summary,
            priority=priority
        )
    except Exception as e:
        logger.exception(f"Failed to analyze feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

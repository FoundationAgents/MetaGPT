# metagpt/ext/spo_api_backend/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum


class RoundResult(BaseModel):
    round: int
    prompt: str
    succeed: bool
    tokens: Optional[int] = None
    answers: Optional[List[Dict]] = None


class TaskStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OptimizationResponse(BaseModel):
    task_id: str
    status: str
    results: List[RoundResult] = []
    last_successful_prompt: Optional[str] = None
    last_successful_round: Optional[int] = None
    total_rounds: int = 0
    successful_rounds: int = 0
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    elapsed_time: Optional[float] = None

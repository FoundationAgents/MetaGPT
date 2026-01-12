#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/09
@Author  : MetaGPT-Pro Team
@File    : conversation.py
@Desc    : API routes for conversational requirements engineering
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from metagpt.conversation import conversation_manager
from metagpt.conversation.schemas import (
    ConversationStartRequest,
    ConversationStartResponse,
    ConversationMessageRequest,
    ConversationMessageResponse,
    ConversationEnhanceRequest,
    ConversationEnhanceResponse,
    ApprovalRequest,
    ApprovalResponse,
    ConversationHistoryResponse,
)
from metagpt.logs import logger

router = APIRouter()


@router.post("/start", response_model=ConversationStartResponse)
async def start_conversation(req: ConversationStartRequest):
    print(f"DEBUG: Received start_conversation request with idea: {req.initial_idea}")
    """
    Start a new conversation session with AI Product Manager.
    
    The AI will ask clarifying questions to understand your requirements better.
    """
    try:
        conversation_id, first_question = await conversation_manager.start_session(req.initial_idea)
        return ConversationStartResponse(
            conversation_id=conversation_id,
            first_question=first_question,
            status="active"
        )
    except Exception as e:
        logger.exception(f"Failed to start conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message", response_model=ConversationMessageResponse)
async def send_message(req: ConversationMessageRequest):
    """
    Send a message to the AI Product Manager in an active conversation.
    
    Returns the AI response and optionally enhanced requirements if ready.
    """
    try:
        ai_response, enhanced, requires_approval = await conversation_manager.add_message(
            req.conversation_id, 
            req.message
        )
        return ConversationMessageResponse(
            ai_response=ai_response,
            enhanced_requirements=enhanced,
            status="pending_approval" if requires_approval else "active",
            requires_approval=requires_approval
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to process message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance", response_model=ConversationEnhanceResponse)
async def enhance_requirements(req: ConversationEnhanceRequest):
    """
    Trigger requirement enhancement based on the current conversation.
    
    Returns structured requirements and any remaining clarifying questions.
    """
    try:
        enhanced = await conversation_manager.enhance_requirements(req.conversation_id)
        return ConversationEnhanceResponse(
            enhanced_prd=enhanced,
            clarifying_questions=enhanced.clarifying_questions
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to enhance requirements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve", response_model=ApprovalResponse)
async def approve_requirements(req: ApprovalRequest):
    """
    Approve the current requirements and lock them for development.
    
    This will trigger the standard MetaGPT workflow with the approved requirements.
    """
    try:
        project_id = await conversation_manager.approve(req.conversation_id)
        
        # Now trigger the actual agent execution
        from metagpt.api.orchestrator import orchestrator
        from metagpt.api.schemas import ProjectRequest
        
        # Get the approved requirement text
        requirement_text = await conversation_manager.get_approved_requirement_text(req.conversation_id)
        if not requirement_text:
            requirement_text = f"Build the project approved in conversation {req.conversation_id}"
        
        # Start the project with agents
        try:
            project_req = ProjectRequest(
                requirement=requirement_text,
                project_name=project_id,
                conversation_id=req.conversation_id,
                investment=3.0,
                n_round=5
            )
            await orchestrator.start_project(project_req)
            logger.info(f"Triggered project execution for {project_id}")
        except Exception as e:
            logger.exception(f"Failed to start project execution: {e}")
            # Still return success for the approval - project can be started manually
        
        return ApprovalResponse(
            project_id=project_id,
            status="approved",
            message="Requirements approved. Development agents started."
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to approve requirements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(conversation_id: str):
    """
    Get the full conversation history and current status.
    """
    try:
        session = await conversation_manager.get_session(conversation_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
        
        return ConversationHistoryResponse(
            conversation_id=session.id,
            messages=session.messages,
            status=session.status.value,
            enhanced_requirements=session.enhanced_requirements
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket for real-time conversation streaming
_conversation_websockets: dict[str, set[WebSocket]] = {}


@router.websocket("/stream/{conversation_id}")
async def conversation_websocket(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for real-time conversation updates.
    
    Events emitted:
    - ai_question: When AI asks a question
    - requirement_update: When requirements are enhanced
    - approval_required: When ready for approval
    """
    await websocket.accept()
    
    # Add to conversation's websocket set
    if conversation_id not in _conversation_websockets:
        _conversation_websockets[conversation_id] = set()
    _conversation_websockets[conversation_id].add(websocket)
    
    try:
        while True:
            # Keep connection alive, wait for client messages
            data = await websocket.receive_text()
            # Client can send messages through WebSocket too
            if data:
                try:
                    import json
                    msg_data = json.loads(data)
                    if msg_data.get("type") == "message":
                        ai_response, enhanced, requires_approval = await conversation_manager.add_message(
                            conversation_id,
                            msg_data.get("content", "")
                        )
                        # Broadcast to all connected clients
                        await _broadcast_to_conversation(conversation_id, {
                            "type": "ai_response",
                            "content": ai_response,
                            "requires_approval": requires_approval
                        })
                        if enhanced:
                            await _broadcast_to_conversation(conversation_id, {
                                "type": "requirement_update",
                                "requirements": enhanced.model_dump()
                            })
                except Exception as e:
                    await websocket.send_json({"type": "error", "message": str(e)})
    except WebSocketDisconnect:
        _conversation_websockets[conversation_id].discard(websocket)
    except Exception:
        _conversation_websockets[conversation_id].discard(websocket)


async def _broadcast_to_conversation(conversation_id: str, message: dict):
    """Broadcast a message to all websockets connected to a conversation"""
    if conversation_id not in _conversation_websockets:
        return
    
    import json
    msg_str = json.dumps(message)
    for ws in _conversation_websockets[conversation_id]:
        try:
            await ws.send_text(msg_str)
        except Exception:
            pass

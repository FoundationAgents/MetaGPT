from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from metagpt.api.orchestrator import orchestrator
from metagpt.project.event_system import event_bus
import json
import asyncio

router = APIRouter()

@router.websocket("/log")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Log stream might be deprecated or different, but keeping for compatibility
    orchestrator.add_websocket(websocket) 
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        orchestrator.remove_websocket(websocket)
    except Exception:
        orchestrator.remove_websocket(websocket)


@router.websocket("/events")
async def events_websocket(websocket: WebSocket):
    """WebSocket for real-time agent activity events"""
    await websocket.accept()
    event_bus.add_websocket(websocket)
    
    try:
        # Send initial connection event
        await websocket.send_json({
            "type": "connected",
            "message": "Activity stream connected"
        })
        
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back if needed
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        event_bus.remove_websocket(websocket)
    except Exception:
        event_bus.remove_websocket(websocket)

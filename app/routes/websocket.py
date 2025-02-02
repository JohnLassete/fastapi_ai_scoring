import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
connected_clients = {}

@router.websocket("/ws/progress")
async def interview_progress(websocket: WebSocket):
    await websocket.accept()
    data = await websocket.receive_json()
    interview_id = data.get("interview_id")

    if not interview_id:
        await websocket.close()
        return

    connected_clients[interview_id] = websocket

    try:
        for progress in range(0, 101, 10):  # Simulate progress updates
            await websocket.send_json({
                "status": "in_progress",
                "interview_id": interview_id,
                "progress": progress,
                "message": f"Progress at {progress}%",
            })
            await asyncio.sleep(2)  # Simulate processing delay

        await websocket.send_json({
            "status": "completed",
            "interview_id": interview_id,
            "message": "Processing completed successfully."
        })
    except WebSocketDisconnect:
        del connected_clients[interview_id]

@router.websocket("/ws/progress/{interview_id}")
async def websocket_endpoint(websocket: WebSocket, interview_id: int):
    await websocket.accept()
    connected_clients[interview_id] = websocket
    print(f"Client connected for interview {interview_id}")
    try:
        while True:
            await websocket.receive_text()  # Keep the connection alive
    except WebSocketDisconnect:
        del connected_clients[interview_id]
        print(f"Client disconnected from interview {interview_id}")
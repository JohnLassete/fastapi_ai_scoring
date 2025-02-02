import asyncio
import websockets

async def listen(interview_id: int):
    uri = f"ws://localhost:8000/ws/progress/{interview_id}"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            print(f"Received message: {message}")

if __name__ == "__main__":
    interview_id = 10
    asyncio.run(listen(interview_id))
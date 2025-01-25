from fastapi import FastAPI
from app.routes import interview, websocket

app = FastAPI()

#Include interview processing routes
app.include_router(interview.router)
app.include_router(websocket.router)

@app.get("/")
def read_root():
    return {"message": "Interview API is running!"}
from fastapi import FastAPI, Depends
from app.routes import interview, websocket
from app.config.db import get_db

app = FastAPI()

#Include interview processing routes
app.include_router(interview.router)
app.include_router(websocket.router)

@app.get("/")
def read_root():
    return {"message": "Interview API is running!"}

@app.get("/test_db_connection")
def test_db_connection(db=Depends(get_db)):
    return {"message": "Connected to the database successfully"}
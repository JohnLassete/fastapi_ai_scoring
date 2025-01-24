from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

#Request model
class InterviewRequest(BaseModel):
    interview_id: int

@router.post("/process-interview")
async def process_interview(request: InterviewRequest):
    if request.interview_id <= 0:
        raise HTTPException(status_code=404, detail="Interview ID not found in the database")

    return {
        "status": "processing",
        "message": "The Processing has started. Connect to the WebSocket for progress updates.",
        "interview_id": request.interview_id
    }
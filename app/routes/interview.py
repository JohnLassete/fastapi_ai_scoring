from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.config.db import get_db
from app.models.interview import Interview

router = APIRouter()

# Request model
class InterviewRequest(BaseModel):
    interview_id: int

# Response model with status and message
class InterviewResponse(BaseModel):
    interview_id: int
    candidate_id: int
    manager_id: int
    status: str
    message: str

@router.post("/process-interview", response_model=InterviewResponse)
async def process_interview(request: InterviewRequest, db: Session = Depends(get_db)):
    # Query the database for the interview using the provided interview_id
    interview = db.query(Interview).filter(Interview.interview_id == request.interview_id).first()

    if not interview:
        # If no interview is found, raise a 404 error
        raise HTTPException(status_code=404, detail="Interview ID not found in the database")

    # Return the relevant interview details along with status and message
    return InterviewResponse(
        interview_id=interview.interview_id,
        candidate_id=interview.candidate_id,
        manager_id=interview.manager_id,
        status="processing",
        message="The Processing has started. Connect to the WebSocket for progress updates.",
    )

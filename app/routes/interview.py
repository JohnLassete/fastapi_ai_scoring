import boto3
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
import asyncio
from pathlib import Path
from app.config.db import get_db
from app.models.interview import Interview
from app.models.evaluation import Evaluation
from app.utils.s3_utils import download_file_from_s3
from app.config.settings import S3_CONFIG
from app.routes.websocket import connected_clients

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
async def process_interview(request: InterviewRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Query the database for the interview using the provided interview_id
    interview = db.query(Interview).filter(Interview.interview_id == request.interview_id).first()

    if not interview:
        # If no interview is found, raise a 404 error
        raise HTTPException(status_code=404, detail="Interview ID not found in the database")

    # Trigger the background task for processing the interview
    background_tasks.add_task(process_files, interview.interview_id, db, asyncio.get_event_loop())

    # Return the relevant interview details along with status and message
    return InterviewResponse(
        interview_id=interview.interview_id,
        candidate_id=interview.candidate_id,
        manager_id=interview.manager_id,
        status="processing",
        message="The Processing has started. Connect to the WebSocket for progress updates.",
    )

async def process_files(interview_id: int, db: Session, loop):
    # Query the database for all evaluations using the provided interview_id
    evaluations = db.query(Evaluation).filter(Evaluation.interview_id == interview_id).all()

    if not evaluations:
        raise HTTPException(status_code=404, detail="Evaluations for Interview ID not found in the database")

    # Create the videos directory in the base folder if it doesn't exist
    base_dir = Path(__file__).resolve().parent.parent.parent
    videos_dir = base_dir / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)

    for evaluation in evaluations:
        # Get the video file S3 key from the database
        videofile_s3key = evaluation.videofile_s3key

        # Extract the S3 key from the full S3 URI
        s3_key = videofile_s3key.replace("s3://seekers3data/", "")

        # Example S3 bucket and key
        bucket_name = S3_CONFIG["S3_BUCKET_NAME"]

        # Define the local path for the downloaded video
        local_path = videos_dir / Path(s3_key).name

        # Track the download progress
        total_size = 0
        bytes_transferred = 0

        async def progress_callback(bytes_transferred, total_size):
            progress = int((bytes_transferred / total_size) * 100)
            print(f"Sending progress update: {progress}% for interview {interview_id}")
            if interview_id in connected_clients:
                await connected_clients[interview_id].send_json({
                    "status": "in_progress",
                    "interview_id": interview_id,
                    "progress": progress,
                    "message": f"Downloading {progress}% complete for video {s3_key}",
                })

        # Download the video file from S3 with progress tracking
        download_file_from_s3(bucket_name, s3_key, str(local_path), progress_callback)

    if interview_id in connected_clients:
        await connected_clients[interview_id].send_json({
            "status": "completed",
            "interview_id": interview_id,
            "message": "Downloading completed successfully."
        })
    print(f"Completed processing for interview {interview_id}")
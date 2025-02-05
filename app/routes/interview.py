# Importing necessary modules and dependencies
import os
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pathlib import Path
from app.config.db import get_db
from app.models.interview import Interview
from app.models.evaluation import Evaluation
from app.models.questions import Questions
from app.models.answers import Answers
from app.utils.s3_utils import download_file_from_s3, upload_file_to_s3
from app.config.settings import S3_CONFIG
from app.routes.websocket import connected_clients
import moviepy.editor as mp
import traceback
import whisper
from sqlalchemy.sql import text
import boto3
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create a FastAPI router
router = APIRouter()

# Define Pydantic models for request and response validation
class InterviewRequest(BaseModel):
    interview_id: int

class InterviewResponse(BaseModel):
    interview_id: int
    candidate_id: int
    manager_id: int
    status: str
    message: str

class ScoringResponse(BaseModel):
    interview_id: int
    question_id: int
    semantic_similarity_score: float
    broad_topic_sim_score: float
    grammar_score: float
    disfluency_score: float
    message: str

# Route to start processing an interview asynchronously
@router.post("/process-interview", response_model=InterviewResponse)
async def process_interview(request: InterviewRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Check if the interview exists in the database
    interview = db.query(Interview).filter(Interview.interview_id == request.interview_id).first()

    if not interview:
        raise HTTPException(status_code=404, detail="Interview ID not found in the database")

    print(f"Processing interview {request.interview_id} for candidate {interview.candidate_id}...")

    # Add the file processing task to the background queue
    background_tasks.add_task(process_files, interview.interview_id, db)

    return InterviewResponse(
        interview_id=interview.interview_id,
        candidate_id=interview.candidate_id,
        manager_id=interview.manager_id,
        status="processing",
        message="The Processing has started. Connect to the WebSocket for progress updates.",
    )

# Background task to process files related to an interview
async def process_files(interview_id: int, db: Session):
    print(f"Started processing files for interview {interview_id}...")

    # Fetch evaluations related to the interview
    evaluations = db.query(Evaluation).filter(Evaluation.interview_id == interview_id).all()

    if not evaluations:
        print(f"No evaluations found for interview {interview_id}.")
        return

    print(f"Found {len(evaluations)} evaluations for interview {interview_id}...")

    # Set up a local directory for downloaded videos
    base_dir = Path(__file__).resolve().parent.parent.parent
    videos_dir = base_dir / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)

    downloaded_files = []

    # Loop through evaluations and process each video file
    for evaluation in evaluations:
        print(f"Processing evaluation {evaluation.evaluation_id}...")

        videofile_s3key = evaluation.videofile_s3key

        if not videofile_s3key:
            print(f"No videofile_s3key found for evaluation {evaluation.evaluation_id}, skipping...")
            continue

        # Extract the S3 key and prepare for download
        s3_key = videofile_s3key.replace("s3://seekers3data/", "")
        bucket_name = S3_CONFIG["S3_BUCKET_NAME"]
        local_path = videos_dir / Path(s3_key).name

        total_size = 0
        bytes_transferred = 0

        # Progress callback to send updates over WebSocket
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

        print(f"Downloading video file from S3: {s3_key}...")

        # Download the video file from S3
        download_file_from_s3(bucket_name, s3_key, str(local_path), progress_callback)
        downloaded_files.append(local_path)

        print(f"Processing video file for transcription: {local_path}...")

        # Transcribe the video file and upload the text to S3
        asr_file_path = await process_video_file(str(local_path), "ConvertedTextFile/")

        if asr_file_path:
            # Update the ASR filename in the database
            update_asr_filename_in_postgres(db, videofile_s3key, asr_file_path)

    print(f"All video files processed for interview {interview_id}.")

    # Notify the WebSocket clients about completion
    if interview_id in connected_clients:
        await connected_clients[interview_id].send_json({
            "status": "completed",
            "interview_id": interview_id,
            "message": "Downloading and transcription completed successfully."
        })

    # Clean up downloaded files
    for file_path in downloaded_files:
        try:
            os.remove(file_path)
            print(f"Deleted downloaded file: {file_path}")
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

    print(f"Completed processing for interview {interview_id}")

# Function to transcribe a video file using Whisper
async def process_video_file(video_file_path, upload_dir):
    try:
        print(f"Processing video file: {video_file_path}")
        video = mp.VideoFileClip(video_file_path)

        # Extract audio from the video
        audio_path = video_file_path.rsplit('.', 1)[0] + '.wav'
        video.audio.write_audiofile(audio_path, codec='pcm_s16le')
        print(f"Audio extracted: {audio_path}")

        # Transcribe the audio using Whisper
        whisper_model = whisper.load_model("base")
        result = whisper_model.transcribe(audio_path)
        text = result['text']
        print(f"Text extracted: {text[:100]}...")

        # Upload the transcribed text to S3
        upload_file_path = os.path.join(upload_dir, os.path.basename(video_file_path).rsplit('.', 1)[0] + '.txt')
        upload_file_to_s3(S3_CONFIG["S3_BUCKET_NAME"], upload_file_path, text)
        print(f"Transcribed text uploaded to S3: {upload_file_path}")

        video.close()
        os.remove(audio_path)

        return f"s3://{S3_CONFIG['S3_BUCKET_NAME']}/{upload_file_path}"
    except Exception as e:
        print(f"Error processing video file {video_file_path}: {e}")
        traceback.print_exc()
        return None

# Update ASR filename in PostgreSQL database
def update_asr_filename_in_postgres(db: Session, video_file_name: str, asr_file_name: str):
    try:
        print(f"Updating ASRFileName for {video_file_name} in PostgreSQL...")
        update_query = """
        UPDATE public.evaluation
        SET 
            "asrfile_s3key" = :asr_file_name
        WHERE 
            "videofile_s3key" = :video_file_name;
        """
        print(f"Executing query: {update_query} with values {video_file_name}, {asr_file_name}")
        result = db.execute(text(update_query), {"asr_file_name": asr_file_name, "video_file_name": video_file_name})
        db.commit()
        if result.rowcount > 0:
            print(f"ASRFileName for {video_file_name} updated successfully.")
        else:
            print(f"No rows updated for {video_file_name}, check the query conditions.")
    except Exception as e:
        print(f"Error updating ASRFileName in PostgreSQL: {e}")
        traceback.print_exc()

# Function to read a text file from S3
def read_s3_text_file(bucket, file_name):
    try:
        print(f"Bucket: {bucket}")
        print(f"Searching for file: {file_name}")

        s3_client = boto3.client('s3')
        s3_objects = s3_client.list_objects(Bucket=bucket).get('Contents', [])

        for s3_key in s3_objects:
            s3_object = s3_key['Key']
            if file_name in s3_object and s3_object.endswith(".txt"):
                print(f"Found file: {s3_object}")

                obj = s3_client.get_object(Bucket=bucket, Key=s3_object)
                content = obj['Body'].read().decode('utf-8')
                return content

        print(f"No matching .txt file found for {file_name}")
        return ""
    except Exception as e:
        print(f"An error occurred: {e}")
        return ""

# Function to calculate scores using GPT-4o-mini
def calculate_scores_with_gpt4o(transcribed_text):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in the .env file")
    client = OpenAI(api_key=api_key)
    prompt = f"Calculate the following scores for the given text: semantic similarity, broad topic similarity, grammar, and disfluency. Each score should be on a scale of 0 to 100. Output only the scores separated by commas.\n\nText: {transcribed_text} \n\n Output only the scores separated by commas. I don't want any other text or explanation."
    data = {"prompt": prompt}
    print(f"Requesting GPT-4o mini for scoring...")
    chat_completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    generated_text = chat_completion.choices[0].message.content
    print("Assistant: " + generated_text)

    scores = generated_text.split(',')
    return float(scores[0]), float(scores[1]), float(scores[2]), float(scores[3])

# Route to score an interview using GPT-4o-mini
@router.post("/score-interview-gpt-4o-mini", response_model=ScoringResponse)
async def score_interview(request: InterviewRequest, db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.interview_id == request.interview_id).first()

    if not interview:
        raise HTTPException(status_code=404, detail="Interview ID not found in the database")

    evaluations = db.query(Evaluation).filter(Evaluation.interview_id == request.interview_id).all()

    if not evaluations:
        raise HTTPException(status_code=404, detail="Evaluations for Interview ID not found in the database")

    print(f"Found {len(evaluations)} evaluations for interview {request.interview_id}.")

    for evaluation in evaluations:
        asrfile_s3key = evaluation.asrfile_s3key.replace("s3://seekers3data/", "")

        print(f"Reading transcribed text from S3 for ASR file: {asrfile_s3key}...")
        transcribed_text = read_s3_text_file(S3_CONFIG["S3_BUCKET_NAME"], asrfile_s3key)

        if not transcribed_text:
            raise HTTPException(status_code=404, detail=f"ASR file not found in S3: {asrfile_s3key}")

        print(f"Calculating scores for interview {request.interview_id}...")
        semantic_similarity_score, broad_topic_sim_score, grammar_score, disfluency_score = calculate_scores_with_gpt4o(transcribed_text)

        print(f"Updating evaluation {evaluation.evaluation_id} with scores...")
        evaluation.semantic_similarity_score = semantic_similarity_score
        evaluation.broad_topic_sim_score = broad_topic_sim_score
        evaluation.grammar_score = grammar_score
        evaluation.disfluency_score = disfluency_score
        db.commit()

    return ScoringResponse(
        interview_id=request.interview_id,
        question_id=evaluation.question_id,
        semantic_similarity_score=semantic_similarity_score,
        broad_topic_sim_score=broad_topic_sim_score,
        grammar_score=grammar_score,
        disfluency_score=disfluency_score,
        message="Scoring completed successfully."
    )

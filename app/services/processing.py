import os
import moviepy.editor as mp
import whisper
import traceback
from pathlib import Path
from app.utils.s3_utils import upload_file_to_s3
from app.config.settings import S3_CONFIG

async def process_video_file(video_file_path, upload_dir, loop):
    """Process video file, extract text using Whisper model, and upload to S3."""
    try:
        print(f"Processing video file: {video_file_path}")
        video = mp.VideoFileClip(video_file_path)

        # Extract audio from video
        audio_path = video_file_path.rsplit('.', 1)[0] + '.wav'  # Handles both .mp4 and .mov
        video.audio.write_audiofile(audio_path, codec='pcm_s16le')
        print(f"Audio extracted: {audio_path}")

        # Transcribe audio using Whisper
        whisper_model = whisper.load_model("base")
        result = whisper_model.transcribe(audio_path)
        text = result['text']
        print(f"Text extracted: {text[:100]}...")

        # Upload the transcribed text to S3
        upload_file_path = os.path.join(upload_dir, os.path.basename(video_file_path).rsplit('.', 1)[0] + '.txt')
        upload_file_to_s3(S3_CONFIG["S3_BUCKET_NAME"], upload_file_path, text)

        # Cleanup
        video.close()
        os.remove(audio_path)

        return f"s3://{S3_CONFIG['S3_BUCKET_NAME']}/{upload_file_path}"  # Return the S3 path for ASRFileName
    except Exception as e:
        print(f"Error processing video file {video_file_path}: {e}")
        traceback.print_exc()
        return None
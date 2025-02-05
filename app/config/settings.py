import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# SSH Tunnel Configurations
SSH_CONFIG = {
    "SSH_HOST": os.getenv("SSH_HOST"),
    "SSH_PORT": int(os.getenv("SSH_PORT", 22)),  # Default to port 22 if not set
    "SSH_USERNAME": os.getenv("SSH_USERNAME"),
    "SSH_KEY_PATH": os.getenv("SSH_KEY_PATH"),
}

# PostgreSQL Database Configurations
DB_CONFIG = {
    "DB_HOST": os.getenv("DB_HOST"),
    "DB_PORT": int(os.getenv("DB_PORT", 5432)),  # Default to port 5432 if not set
    "DB_NAME": os.getenv("DB_NAME"),
    "DB_USER": os.getenv("DB_USER"),
    "DB_PASS": os.getenv("DB_PASS"),
}

# S3 Configurations
S3_CONFIG = {
    "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
    "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
    "S3_BUCKET_NAME": os.getenv("S3_BUCKET_NAME"),
}

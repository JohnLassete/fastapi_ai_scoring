import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file
load_dotenv()

# SSH Tunnel Configurations
SSH_CONFIG = {
    "SSH_HOST": "52.15.194.170",
    "SSH_PORT": 22,
    "SSH_USERNAME": "ec2-user",
    "SSH_KEY_PATH": str(BASE_DIR / "BastionHostKeyPair.pem"),
}

# PostgreSQL Database Configurations
DB_CONFIG = {
    "DB_HOST": "databasets.chygq4ecec7u.us-east-2.rds.amazonaws.com",
    "DB_PORT": 5432,
    "DB_NAME": "seekers",
    "DB_USER": "postgres_TS",
    "DB_PASS": "BBCPs2025_",
}

# S3 Configureations
S3_CONFIG = {
    "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
    "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
    "S3_BUCKET_NAME": os.getenv("S3_BUCKET_NAME"),
}
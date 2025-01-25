import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

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
    "DB_NAME": "postgres",
    "DB_USER": "postgres_TS",
    "DB_PASS": "BBCPs2025_",
}

import os
import logging
from pathlib import Path
from sshtunnel import SSHTunnelForwarder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.config.settings import SSH_CONFIG, DB_CONFIG
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change from DEBUG to INFO
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize database configuration
logger.info("Initializing database configuration...")

# Resolve paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SSH_KEY_PATH = str(BASE_DIR / "BastionHostKeyPair.pem")
logger.debug(f"Base directory resolved: {BASE_DIR}")
logger.debug(f"Using SSH Key Path: {SSH_KEY_PATH}")

# Get environment type from the .env file
ENVIRONMENT_TYPE = os.getenv("ENVIRONMENT_TYPE", "local").lower()

# Check if the environment is local or EC2
if ENVIRONMENT_TYPE == "local":
    # Ensure SSH key file exists
    if not os.path.exists(SSH_KEY_PATH):
        logger.error("SSH Key file not found! Check the path.")
        raise FileNotFoundError("SSH Key file not found at the specified path.")
    else:
        logger.info("SSH Key file found, proceeding with SSH tunnel setup.")

    # Establish SSH Tunnel
    try:
        logger.info("Establishing SSH tunnel...")
        tunnel = SSHTunnelForwarder(
            (SSH_CONFIG["SSH_HOST"], SSH_CONFIG["SSH_PORT"]),
            ssh_username=SSH_CONFIG["SSH_USERNAME"],
            ssh_pkey=SSH_KEY_PATH,
            remote_bind_address=(DB_CONFIG["DB_HOST"], DB_CONFIG["DB_PORT"]),
        )
        tunnel.start()
        logger.info("SSH tunnel established successfully.")
        logger.debug(f"Local bind port: {tunnel.local_bind_port}")
    except Exception as e:
        logger.error(f"Failed to establish SSH tunnel: {e}")
        raise

    # Database connection string (localhost mapped via SSH tunnel)
    DB_URL = (
        f"postgresql://{DB_CONFIG['DB_USER']}:{DB_CONFIG['DB_PASS']}"
        f"@127.0.0.1:{tunnel.local_bind_port}/{DB_CONFIG['DB_NAME']}"
    )
    logger.debug(f"Database URL: {DB_URL}")

else:
    # If it's EC2, just use the direct DB connection (no SSH tunnel)
    DB_URL = (
        f"postgresql://{DB_CONFIG['DB_USER']}:{DB_CONFIG['DB_PASS']}"
        f"@{DB_CONFIG['DB_HOST']}:{DB_CONFIG['DB_PORT']}/{DB_CONFIG['DB_NAME']}"
    )
    logger.info("Running on EC2, no SSH tunnel required.")
    logger.debug(f"Database URL: {DB_URL}")

# Create SQLAlchemy engine and session
try:
    logger.info("Creating SQLAlchemy engine...")
    engine = create_engine(DB_URL)
    logger.info("SQLAlchemy engine created successfully.")
except Exception as e:
    logger.error(f"Error creating SQLAlchemy engine: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for SQLAlchemy models
Base = declarative_base()

def get_db():
    """Dependency to get the database session."""
    logger.info("Creating new database session...")
    db = SessionLocal()
    try:
        yield db
        logger.info("Database session created successfully.")
    except Exception as e:
        logger.error(f"Error during database session: {e}")
        raise
    finally:
        db.close()
        logger.info("Database session closed.")

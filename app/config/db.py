import os
import logging
from pathlib import Path
from sshtunnel import SSHTunnelForwarder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import SSH_CONFIG, DB_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Log configuration details
logger.info("Initializing database configuration...")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
logger.debug(f"Base directory resolved: {BASE_DIR}")

SSH_KEY_PATH = str(BASE_DIR / "BastionHostKeyPair.pem")
logger.debug(f"Using SSH Key Path: {SSH_KEY_PATH}")

# Ensure SSH key file exists
if not os.path.exists(SSH_KEY_PATH):
    logger.error("SSH Key file not found! Check the path.")
else:
    logger.info("SSH Key file found, proceeding with SSH tunnel setup.")

# Establish SSH Tunnel with logging
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
DB_URL = f"postgresql://{DB_CONFIG['DB_USER']}:{DB_CONFIG['DB_PASS']}@127.0.0.1:{tunnel.local_bind_port}/{DB_CONFIG['DB_NAME']}"
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

def get_db():
    """Dependency to get the database session."""
    logger.info("Creating new database session...")
    db = SessionLocal()
    try:
        yield db
        logger.info("Database session created successfully.")
    except Exception as e:
        logger.error(f"Error during database session: {e}")
    finally:
        db.close()
        logger.info("Database session closed.")

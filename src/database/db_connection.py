import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
import sys

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_url():
    """Get database URL from environment variables"""
    # Get environment variables with explicit defaults
    db_user = os.environ.get('DB_USER', 'retail_user')
    db_password = os.environ.get('DB_PASSWORD', 'retail_password')
    # Use localhost when running scripts directly, postgres service name when in Docker
    is_script = 'python' in sys.executable
    db_host = 'localhost' if is_script else os.environ.get('DB_HOST', 'postgres')
    db_port = os.environ.get('DB_PORT', '5432')
    db_name = os.environ.get('DB_NAME', 'retail_analytics')
    
    # Log the connection details (excluding password)
    logger.info(f"Database connection details:")
    logger.info(f"User: {db_user}")
    logger.info(f"Host: {db_host}")
    logger.info(f"Port: {db_port}")
    logger.info(f"Database: {db_name}")
    logger.info(f"Running as script: {is_script}")
    
    url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    return url

# Create database engine with connection pooling and retry settings
engine = create_engine(
    get_db_url(),
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,  # Enable connection health checks
    connect_args={
        "connect_timeout": 10  # Connection timeout in seconds
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        # Test the connection using SQLAlchemy text()
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        db.close()
        raise
    finally:
        db.close()

def init_db():
    """Initialize the database by creating all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

def close_db():
    """Close the database connection"""
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")
        raise 
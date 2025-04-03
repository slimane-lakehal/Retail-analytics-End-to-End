import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Load environment variables
load_dotenv()

from src.database.init_db import init_database

if __name__ == "__main__":
    print("Initializing database...")
    if init_database():
        print("Database initialization completed successfully!")
    else:
        print("Database initialization failed!")
        sys.exit(1) 
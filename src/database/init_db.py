import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .db_connection import engine, Base, get_db_url
from .models import *
from .sample_data import generate_sample_data

def init_database():
    """Initialize database with tables and sample data"""
    try:
        print("Starting database initialization...")
        
        # Get database connection parameters
        db_user = os.getenv('DB_USER', 'retail_user')
        db_password = os.getenv('DB_PASSWORD', 'retail_password')
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'retail_analytics')
        
        print(f"Connecting to database at {db_host}:{db_port}/{db_name}")
        
        # Create database engine
        engine = create_engine(get_db_url())
        
        # Drop all tables with dependencies
        print("Dropping existing schema...")
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO retail_user"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
            conn.commit()
        print("Schema dropped and recreated successfully")
        
        # Create all tables
        print("Creating database tables...")
        Base.metadata.create_all(engine)
        print("Tables created successfully")
        
        # Create session
        print("Creating database session...")
        Session = sessionmaker(bind=engine)
        db = Session()
        
        try:
            # Generate sample data
            print("Generating sample data...")
            result = generate_sample_data(db)
            
            # Commit the session
            print("Committing changes to database...")
            db.commit()
            print("Changes committed successfully")
            
            print("Database initialized successfully!")
            print("Generated data summary:")
            for key, value in result.items():
                print(f"- {key}: {value}")
            
            return True
        except Exception as e:
            print(f"Error during data generation: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    init_database() 
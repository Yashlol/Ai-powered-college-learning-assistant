import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Import the Base from your new models file
from app.models import Base 

load_dotenv()

DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "college_db"

DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    """Drops old tables and recreates the strict schema in PostgreSQL."""
    print("Clearing old data and initializing fresh database schema...")
    
    # 1. Drop the old tables so we start with a clean slate
    Base.metadata.drop_all(bind=engine)
    
    # 2. Recreate the fresh tables with our strict Primary/Foreign keys
    Base.metadata.create_all(bind=engine)
    
    print("Schema refreshed successfully.")
    
    
def push_dataframes_to_db(students_df, assessments_df, scores_df, topics_df, courses_df=None, course_progress_df=None):
    """Pushes the clean DataFrames into the pre-existing tables."""
    print("Pushing data to PostgreSQL...")
    
    # CHANGED: Ensure tables are created (including the new TopicPrerequisite table) before inserting data
    Base.metadata.create_all(bind=engine)
    
    with engine.begin() as connection:
        # Using 'append' to protect our Foreign Keys
        students_df.to_sql(name='students', con=connection, if_exists='append', index=False)
        assessments_df.to_sql(name='assessments', con=connection, if_exists='append', index=False)
        scores_df.to_sql(name='assessment_results', con=connection, if_exists='append', index=False)
        topics_df.to_sql(name='topic_performance', con=connection, if_exists='append', index=False)

        if courses_df is not None and not courses_df.empty:
            courses_df.to_sql(name='courses', con=connection, if_exists='append', index=False)
        
        if course_progress_df is not None and not course_progress_df.empty:
             course_progress_df.to_sql(name='course_progress', con=connection, if_exists='append', index=False)

    print("All data successfully pushed to PostgreSQL!")
    
    
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to generate a database session for requests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
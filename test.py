from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import declarative_base

# Initialize the declarative base
Base = declarative_base()

# 1. ADD THE EXISTING STUDENT MODEL HERE
# This tells SQLAlchemy's metadata that the 'students' table exists!
class Student(Base):
    __tablename__ = 'students'
    student_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    roll_number = Column(String)
    college_id = Column(String)

# 2. DEFINE THE NEW TABLE
class AssessmentState(Base):
    __tablename__ = 'assessment_state'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Now it will perfectly link to the Student class above
    student_id = Column(String, ForeignKey('students.student_id'))
    
    assessment_id = Column(Integer, nullable=False) 
    topic_name = Column(String, nullable=False)
    difficulty = Column(String, nullable=False) 
    
    status = Column(String, nullable=True)          
    score_achieved = Column(Float, nullable=True)   
    retake_approved = Column(Boolean, default=False)
    
# ==========================================
# SETUP YOUR DATABASE CONNECTION HERE
# ==========================================
# Replace with your actual PostgreSQL connection string!
        
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "college_db"

DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# Create the engine
engine = create_engine(DATABASE_URL)

if __name__ == "__main__":
    print("Connecting to database...")
    try:
        # Create all tables defined by this Base (it will skip 'students' since it already exists)
        Base.metadata.create_all(engine)
        print("✅ SUCCESS: 'assessment_state' table has been created!")
    except Exception as e:
        print(f"❌ ERROR creating table: {e}")
        
        
        


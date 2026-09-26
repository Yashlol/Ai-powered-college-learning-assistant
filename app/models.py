from sqlalchemy import Column, String, Integer, Float, ForeignKey, VARCHAR, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# This is the base class all your models will inherit from
Base = declarative_base()

# ==========================================
# IDENTITY: The master record for all users. 
# Everything else links back to the student_id defined here.
# ==========================================
class Student(Base):
    __tablename__ = 'students'
    student_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    roll_number = Column(String)
    college_id = Column(String)


# ==========================================
# EXAMS: A master list of all official tests, exams, or assignments.
# ==========================================
class Assessment(Base):
    __tablename__ = 'assessments'
    assessment_id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    start_date = Column(String)


# ==========================================
# GRADEBOOK (HIGH-LEVEL): Links a student to a specific assessment 
# to record their overall total score.
# ==========================================
class AssessmentResult(Base):
    __tablename__ = 'assessment_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String, ForeignKey('students.student_id'))
    assessment_id = Column(Integer, ForeignKey('assessments.assessment_id'))
    total_score = Column(Float)


# ==========================================
# GRADEBOOK (GRANULAR): The most critical table for AI personalization. 
# Tracks pass/fail status on specific micro-skills (sub_domains) so the AI knows what to teach.
# ==========================================
class TopicPerformance(Base):
    __tablename__ = 'topic_performance'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String, ForeignKey('students.student_id'))
    assessment_id = Column(Integer, ForeignKey('assessments.assessment_id'))
    sub_domain = Column(String)
    status = Column(String)

# ==========================================
# CATALOG: The high-level metadata for available learning modules or classes.
# ==========================================    
class Course(Base):
    __tablename__ = 'courses'
    course_id = Column(String, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    
# ==========================================
# PROGRESS: Tracks a student's journey and completion percentage 
# through a specific course.
# ==========================================
class CourseProgress(Base):
    __tablename__ = 'course_progress'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String, ForeignKey('students.student_id'))
    course_id = Column(String, ForeignKey('courses.course_id'))
    completion_percentage = Column(Float, default=0.0)
    status = Column(String)


# ==========================================
# AI AUDIT LOG: Records whenever the AI generates a custom practice session, 
# providing professors visibility into AI-assisted studying.
# ==========================================
class PracticeHistory(Base):
    __tablename__ = 'practice_history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String, ForeignKey('students.student_id'))
    topic_practiced = Column(String)  # Changed name
    content = Column(VARCHAR)          # ADDED this column
    difficulty = Column(String, nullable=True)
    score_achieved = Column(Float, nullable=True)

# ==========================================
# DYNAMIC GUARDRAILS: The rules engine table. Maps a target topic to its required prerequisite 
# so the AI can block access to advanced material if foundational skills were failed.
# ==========================================
# CHANGED: Added the dynamic prerequisites table to replace hardcoded Python if/else rules
class TopicPrerequisite(Base):
    __tablename__ = 'topic_prerequisites'
    id = Column(Integer, primary_key=True, autoincrement=True)
    target_topic = Column(String, index=True)      
    required_topic = Column(String)

class AssessmentState(Base):
    __tablename__ = 'assessment_state'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String, ForeignKey('students.student_id'))
    
    # The parent ID that links all 3 difficulties together (e.g., 3574)
    assessment_id = Column(Integer, nullable=False) 
    
    # The root word ONLY (e.g., "Decision Trees")
    topic_name = Column(String, nullable=False)
    
    # The specific level (e.g., "Easy", "Medium", "Hard")
    difficulty = Column(String, nullable=False) 
    
    status = Column(String, nullable=True) # "Passed", "Failed"
    score_achieved = Column(Float, nullable=True)
    retake_approved = Column(Boolean, default=False)
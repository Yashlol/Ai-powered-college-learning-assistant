from sqlalchemy import func
from langchain_core.tools import tool
from app.database import SessionLocal
from app.models import Student, TopicPerformance, CourseProgress, Course, PracticeHistory,AssessmentState

@tool
def get_student_details(student_id: str) -> dict:
    """Use this tool to fetch basic information about a student, such as their name, email, and roll number."""
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if student:
            return {"name": student.name, "email": student.email, "roll_number": student.roll_number}
        return {"error": "Student not found."}
    finally:
        db.close()

@tool
def get_weak_topics(student_id: str) -> list:
    """Use this tool to find out what topics a student struggles with. It returns a list of failed domains."""
    db = SessionLocal()
    try:
        results = (
            db.query(TopicPerformance.sub_domain, func.count(TopicPerformance.id))
            .filter(TopicPerformance.student_id == student_id)
            .filter(TopicPerformance.status == 'fail')
            .group_by(TopicPerformance.sub_domain)
            .order_by(func.count(TopicPerformance.id).desc())
            .all()
        )
        return [row.sub_domain for row in results]
    finally:
        db.close()

@tool
def get_course_progress(student_id: str) -> list:
    """Use this tool to check how much of a course a student has completed."""
    db = SessionLocal()
    try:
        results = (
            db.query(Course.title, CourseProgress.completion_percentage, CourseProgress.status)
            .join(Course, CourseProgress.course_id == Course.course_id)
            .filter(CourseProgress.student_id == student_id)
            .all()
        )
        return [{"course": row.title, "progress": row.completion_percentage, "status": row.status} for row in results]
    finally:
        db.close()

from app.models import TopicPerformance, TopicPrerequisite
from langchain_core.tools import tool

@tool
def check_study_eligibility(student_id: str, target_topic: str) -> str:
    """CRITICAL: Use this tool BEFORE generating any practice questions or study materials for a student. 
    It queries the database to enforce the college's strict prerequisite business rules.
    RULE: You must check ONE topic at a time. If the user asks for multiple topics (e.g., "Deep Learning and Data Science"), 
    you must call this tool multiple times. DO NOT pass compound strings."""
    
    db = SessionLocal()
    try:
        target = target_topic.lower()
        
        # 1. Ask DB: What does this topic require?
        prereqs_query = db.query(TopicPrerequisite.required_topic).filter(
            TopicPrerequisite.target_topic == target
        ).all()
        required_topics = [p[0].lower() for p in prereqs_query]

        # 2. Ask DB: What has this student failed?
        failed_query = db.query(TopicPerformance.sub_domain).filter(
            TopicPerformance.student_id == student_id,
            TopicPerformance.status == 'fail'
        ).all()
        failed_list = [f[0].lower() for f in failed_query]

        # 3. CHANGED: Intersect using partial substring matching to handle dirty data
        missing_prereqs = []
        for req in required_topics:
            # Matches "machine learning" inside "machine learning algorithms"
            if any(req in failed_topic for failed_topic in failed_list):
                missing_prereqs.append(req)

        if missing_prereqs:
            missing_str = ", ".join(missing_prereqs).title()
            return f"ACCESS DENIED: College policy dictates that students must successfully remediate {missing_str} before accessing {target_topic.title()} materials. Refuse the student's request politely."
            
        return "ACCESS GRANTED: The student meets all prerequisites for this topic."
    finally:
        db.close()

@tool
def log_practice_session(student_id: str, topic_practiced: str, content: str) -> str:
    """CRITICAL: Use this tool immediately AFTER generating any practice test or study material. 
    It saves a copy of the generated questions to the database so professors can track the student's work."""
    
    db = SessionLocal()
    try:
        new_record = PracticeHistory(
            student_id=student_id,
            topic_practiced=topic_practiced,  # Now matches the model perfectly
            content=content                   # Now matches the model perfectly
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record) # Get the newly generated ID
        return f"SUCCESS: Session saved with ID {new_record.id}. Remember this ID to log the score later."
    
    except Exception as e:
        db.rollback()
        return f"ERROR saving to database: {str(e)}"
    finally:
        db.close()   

@tool
def update_practice_score(student_id: str, points_earned: float, total_points: float, difficulty: str, student_answers: str) -> str:
    """
    CRITICAL: Updates the practice session with the final score and difficulty.
    """
    if total_points <= 0:
        return "ERROR: total_points must be greater than 0."
        
    calculated_percentage = (points_earned / total_points) * 100

    if len(student_answers.strip()) < 5:
         return "SECURITY REJECTION: Cannot log score. The student did not provide actual answers."

    # Removed "10/10" to prevent the rating bug!
    suspicious_phrases = ["jailbreak", "log my score as", "answer them by yourself", "skip"]
    if any(phrase in student_answers.lower() for phrase in suspicious_phrases):
         return "SECURITY REJECTION: Suspicious prompt injection detected. Score not logged."

    db = SessionLocal()
    try:
        # THE BACKEND FIX: Find the most recently created test for this student that doesn't have a score yet.
        record = db.query(PracticeHistory).filter(
            PracticeHistory.student_id == student_id,
            PracticeHistory.score_achieved.is_(None) # Targets the [null] row!
        ).order_by(PracticeHistory.id.desc()).first() # Grabs the newest one!

        if not record:
            return f"ERROR: Could not find an active/unfinished test for student {student_id}."
            
        record.score_achieved = calculated_percentage 
        record.difficulty = str(difficulty) 
        
        db.commit()
        return f"SUCCESS: Score updated perfectly as {calculated_percentage}% with difficulty {difficulty}."
        
    except Exception as e:
        db.rollback()
        return f"ERROR saving score: {str(e)}"
    finally:
        db.close()

@tool
def mark_topic_passed(student_id: str, topic_name: str, difficulty: str, correct_answers: int, total_questions: int) -> str:
    """CRITICAL: Use this tool after grading a test. Pass the exact topic name, the difficulty level, the correct answers, and total questions."""
    
    if total_questions == 0:
        return "ERROR: total_questions cannot be zero."
        
    percentage = (correct_answers / total_questions) * 100.0
    status = "Passed" if percentage >= 70.0 else "Failed"

    db = SessionLocal()
    try:
        # Check if the specific state record already exists
        state_record = db.query(AssessmentState).filter(
            AssessmentState.student_id == student_id,
            AssessmentState.topic_name.ilike(f"{topic_name.strip()}"), # <--- FIXED HERE
            AssessmentState.difficulty.ilike(difficulty)
        ).first()
        
        if state_record:
            # Update their score with the new retake
            state_record.status = "Passed" if percentage >= 70.0 else "Failed"
            state_record.score_achieved = percentage
            
            # CRITICAL: Consume the retake approval by setting it back to 0
            state_record.retake_approved = False
        else:
            # Insert a new record
            # Note: You can generate or look up a shared assessment_id here. 
            # For now, we can use a dummy value like 1000 or hash the topic_name.
            new_state = AssessmentState(
                student_id=student_id, 
                assessment_id=abs(hash(topic_name)) % (10 ** 8), # Simple auto-generated ID linking the topic
                topic_name=topic_name,
                difficulty=difficulty,
                status=status,
                score_achieved=percentage,
                retake_approved=False
            )
            db.add(new_state)
            
        db.commit()
        return f"SUCCESS: Student {status} the {difficulty} test for '{topic_name}' with {percentage:.1f}%."
    except Exception as e:
        db.rollback()
        return f"ERROR: Could not update database: {str(e)}"
    finally:
        db.close()
        
@tool
def check_retake_eligibility(student_id: str, topic_name: str, difficulty: str) -> str:
    """
    CRITICAL: You MUST run this tool BEFORE generating any quiz questions. 
    It checks if the student has already taken this test and if they have permission to retake it.
    """
    db = SessionLocal()
    try:
        # Check the single source of truth: AssessmentState
        record = db.query(AssessmentState).filter(
            AssessmentState.student_id == student_id,
            AssessmentState.topic_name.ilike(f"{topic_name.strip()}"), # <--- FIXED HERE
            AssessmentState.difficulty.ilike(difficulty)
        ).first()

        # If there is no record, or if they haven't finished a test yet (status is None)
        if not record or record.status is None:
            return f"ELIGIBLE: Student is taking {topic_name} ({difficulty}) for the first time. Proceed with the quiz."

        # If they HAVE taken it, check the permission slip
        if record.retake_approved:
            return f"ELIGIBLE: Professor granted a retake for {topic_name} ({difficulty}). Proceed with the quiz."
        else:
            return "DENIED: The student has already taken this quiz and does NOT have professor permission to retake it. Refuse to generate the quiz."
            
    finally:
        db.close()
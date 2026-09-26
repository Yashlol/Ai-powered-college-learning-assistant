from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.agent import agent_executor
from app.models import PracticeHistory, TopicPerformance, AssessmentState
from app.database import get_db

app = FastAPI(title="AI Learning Assistant API")

# --- Root & Health Endpoints ---

@app.get("/")
def read_root():
    return {"message": "The Learning Assistant Backend is running!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}

# --- Chat Endpoint ---

class ChatRequest(BaseModel):
    student_id: str
    message: str
    thread_id: str

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    full_query = f"I am student ID {request.student_id}. {request.message}"
    
    try:
        response = agent_executor.invoke({"messages": [("user", full_query)]}, config=config)
        final_text = response["messages"][-1].content
        
        if isinstance(final_text, list):
            final_text = final_text[0].get("text", str(final_text))
            
        # --- DYNAMIC SOURCE EXTRACTION (CURRENT TURN ONLY) ---
        actual_sources = set()
        
        for msg in reversed(response.get("messages", [])):
            if getattr(msg, "type", "") == "human" or msg.__class__.__name__ == "HumanMessage":
                break 
                
            if getattr(msg, "type", "") == "tool" and getattr(msg, "name", "") == "search_course_material":
                content = str(msg.content)
                if "SOURCE:" in content:
                    parts = content.split("SOURCE:")
                    for part in parts[1:]:
                        try:
                            source_name = part.split("|")[0].strip()
                            actual_sources.add(f"📄 **{source_name}**")
                        except Exception:
                            continue
                            
        sources_string = "\n\n".join(actual_sources) if actual_sources else None
            
        return {
            "response": final_text,
            "sources": sources_string 
        }
        
    except Exception as e:
        print(f"CRITICAL AGENT ERROR: {str(e)}")
        return {"response": "⚠️ I encountered an internal server error while processing your request. Please try again or start a new chat."}

# --- Dashboard & UI Data Endpoints ---

@app.get("/dashboard/{student_id}")
def get_dashboard(student_id: str, db: Session = Depends(get_db)):
    # 1. Total Practice Sessions
    total_sessions = db.query(PracticeHistory).filter(
        PracticeHistory.student_id == student_id
    ).count()

    # 2. Average Score (Most recent attempt per topic)
    latest_attempts_subquery = db.query(
        PracticeHistory.topic_practiced,
        PracticeHistory.score_achieved,
        func.row_number().over(
            partition_by=PracticeHistory.topic_practiced,
            order_by=PracticeHistory.id.desc()
        ).label('row_num')
    ).filter(PracticeHistory.student_id == student_id).subquery()

    avg_score_result = db.query(func.avg(PracticeHistory.score_achieved)).filter(
        PracticeHistory.student_id == student_id,
        PracticeHistory.score_achieved.isnot(None) # Explicitly skip NULLs
    ).scalar()
    clean_avg = round(avg_score_result, 1) if avg_score_result else 0.0
    
    # 3. Topics Mastered Count
    mastered_count = db.query(TopicPerformance).filter(
        TopicPerformance.student_id == student_id,
        TopicPerformance.status.ilike("%pass%")
    ).count()

    # 4. Weak Topics
    weak_topics_query = db.query(TopicPerformance.sub_domain).filter(
        TopicPerformance.student_id == student_id,
        TopicPerformance.status.ilike("%fail%")
    ).limit(3).all()
    
    weak_topics = [topic[0] for topic in weak_topics_query]

    # 5. Assessment History
    history_query = db.query(
        PracticeHistory.topic_practiced, 
        PracticeHistory.difficulty, 
        PracticeHistory.score_achieved
    ).filter(
        PracticeHistory.student_id == student_id
    ).order_by(PracticeHistory.id.desc()).limit(5).all()

    history = [
        {
            "Topic": row.topic_practiced,
            "Difficulty": row.difficulty or "Not Rated",
            "Score": f"{round(row.score_achieved)}%" if row.score_achieved is not None else "N/A"
        }
        for row in history_query
    ]

    return {
        "metrics": {
            "overall_score": clean_avg,
            "total_sessions": total_sessions,
            "topics_mastered": mastered_count
        },
        "weak_topics": weak_topics,
        "history": history
    }
    
import re    
from fastapi import Query

@app.get("/topics/{student_id}")
def get_student_topics_endpoint(student_id: str, db: Session = Depends(get_db)):
    """
    Fetches topics directly from the topic_performance table 
    and cleans out difficulty tags on the fly.
    """
    try:
        # 1. Fetch all raw variations from your existing topic_performance table
        results = db.query(TopicPerformance.sub_domain).filter(
            TopicPerformance.student_id == student_id
        ).all()
        
        clean_topics = set() # A set automatically removes duplicates
        
        for row in results:
            if row[0]:
                raw_topic = row[0]
                # 2. Strip out difficulty words, parentheses, and hyphens
                root_topic = re.sub(r'(?i)\s*\(?(easy|medium|hard|variation)\)?\s*', '', raw_topic).strip()
                root_topic = root_topic.strip('-').strip()
                
                # Add the clean root word to our set
                if root_topic:
                    clean_topics.add(root_topic)
                
        # 3. Return a clean, alphabetically sorted list to Streamlit
        return sorted(list(clean_topics))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/check_eligibility/{student_id}")
def check_eligibility(student_id: str, topic: str = Query(...), difficulty: str = Query(...), db: Session = Depends(get_db)):
    
    # 1. Target record check
    target_record = db.query(AssessmentState).filter(
        AssessmentState.student_id == student_id,
        AssessmentState.topic_name.ilike(f"{topic.strip()}"), # <--- FIXED HERE
        AssessmentState.difficulty.ilike(difficulty)
    ).first()
    
    has_retake_approval = bool(target_record.retake_approved) if target_record else False

    if target_record and target_record.status and not has_retake_approval:
        return {"allowed": False, "message": f"🔒 Access Denied: You already used your attempt for the {difficulty} assessment on {topic}."}

    # 2. Easy prerequisite check
    if difficulty.lower() == "medium":
        easy_record = db.query(AssessmentState).filter(
            AssessmentState.student_id == student_id,
            AssessmentState.topic_name.ilike(f"{topic.strip()}"), # <--- FIXED HERE
            AssessmentState.difficulty.ilike("easy")
        ).first()
        
        if not easy_record or str(easy_record.status).lower() != "passed":
            return {"allowed": False, "message": f"🔒 Access Denied: You must pass 'Easy' before unlocking 'Medium'."}
            
    # 3. Medium prerequisite check
    elif difficulty.lower() == "hard":
        medium_record = db.query(AssessmentState).filter(
            AssessmentState.student_id == student_id,
            AssessmentState.topic_name.ilike(f"{topic.strip()}"), # <--- FIXED HERE
            AssessmentState.difficulty.ilike("medium")
        ).first()
        
        if not medium_record or str(medium_record.status).lower() != "passed":
            return {"allowed": False, "message": f"🔒 Access Denied: You must pass 'Medium' before unlocking 'Hard'."}
            
    return {"allowed": True}
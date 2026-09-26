import streamlit as st
import requests
import uuid
import sqlite3
import uuid
# --- 1. PAGE CONFIG MUST BE FIRST ---
st.set_page_config(page_title="College AI Assistant", page_icon="🎓", layout="wide")

# --- 2. UI DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("streamlit_ui.db", check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS threads (thread_id TEXT PRIMARY KEY, student_id TEXT, title TEXT)')
    # NEW: Added 'sources TEXT' to the end of this table
    conn.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id TEXT, role TEXT, content TEXT, sources TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS users (student_id TEXT PRIMARY KEY, password TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS sessions (session_token TEXT PRIMARY KEY, student_id TEXT)')
    conn.commit()
    return conn
conn = init_db()

# --- 3. INITIALIZE SECURE AUTH & VIEW STATE ---
token = st.query_params.get("session")

if token:
    row = conn.execute("SELECT student_id FROM sessions WHERE session_token = ?", (token,)).fetchone()
    if row:
        st.session_state.logged_in = True
        st.session_state.student_id = row[0] 
    else:
        st.query_params.clear()
        st.session_state.logged_in = False
        st.session_state.student_id = None
else:
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "student_id" not in st.session_state:
        st.session_state.student_id = None

    
# Initialize the View state (Chat vs Dashboard)
if "current_view" not in st.session_state:
    st.session_state.current_view = "chat"

# --- 4. THE LOGIN FUNCTION ---
def login_page():
    st.title("🎓 AI Learning Assistant")
    
    tab1, tab2 = st.tabs(["Login", "Register New Student"])
    
    with tab1:
        st.subheader("Sign In")
        login_id = st.text_input("Student ID", key="login_id")
        login_pw = st.text_input("Password", type="password", key="login_pw")
        
        if st.button("Login"):
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE student_id=? AND password=?", (login_id, login_pw))
            user = cursor.fetchone()
            
            if user:
                session_token = uuid.uuid4().hex
                conn.execute("INSERT INTO sessions (session_token, student_id) VALUES (?, ?)", (session_token, login_id))
                conn.commit()
                
                st.query_params["session"] = session_token
                
                st.session_state.logged_in = True
                st.session_state.student_id = login_id
                st.rerun() 
            else:
                st.error("Invalid Student ID or Password")
                
    with tab2:
        st.subheader("Create Account")
        new_id = st.text_input("New Student ID", key="reg_id")
        new_pw = st.text_input("New Password", type="password", key="reg_pw")
        
        if st.button("Register"):
            try:
                conn.execute("INSERT INTO users (student_id, password) VALUES (?, ?)", (new_id, new_pw))
                conn.commit()
                st.success("Account created! You can now log in.")
            except sqlite3.IntegrityError:
                st.error("That Student ID already exists.")

# --- 5. MAIN APP ROUTING ---
if not st.session_state.logged_in:
    login_page()

else:
    student_id = st.session_state.student_id

    # --- 6. SIDEBAR (NAVIGATION & SETTINGS) ---
    with st.sidebar:
        st.header("⚙️ Student Settings")
        st.write(f"Logged in as: **{student_id}**")
        
        if st.button("Logout", use_container_width=True):
            token = st.query_params.get("session")
            if token:
                conn.execute("DELETE FROM sessions WHERE session_token = ?", (token,))
                conn.commit()
            
            st.query_params.clear()
            st.session_state.logged_in = False
            st.session_state.student_id = None
            st.rerun()
            
        st.divider()
        
        # --- NAVIGATION TOGGLE ---
        st.header("🧭 Navigation")
        
        # Dashboard Button
        if st.session_state.current_view != "dashboard":
            if st.button("📊 View Dashboard", use_container_width=True, type='primary'):
                st.session_state.current_view = "dashboard"
                st.rerun()
                
        # Practice Button
        if st.session_state.current_view != "practice":
            if st.button("📝 Setup Practice", use_container_width=True,type='primary'):
                st.session_state.current_view = "practice"
                st.rerun()
                
        # Chat Button
        if st.session_state.current_view != "chat":
            if st.button("💬 Back to Chat", use_container_width=True, type="primary"):
                st.session_state.current_view = "chat"
                st.rerun()     
        st.divider()
        
        # --- STUDY SESSIONS ---
        st.title("📚 Study Sessions")
        
        if "is_thinking" not in st.session_state:
            st.session_state.is_thinking = False
        if "editing_thread" not in st.session_state:
            st.session_state.editing_thread = None
        
        if st.button("➕ New Chat", use_container_width=True, disabled=st.session_state.is_thinking):
            new_thread = f"chat_{uuid.uuid4().hex[:8]}"
            conn.execute("INSERT INTO threads (thread_id, student_id, title) VALUES (?, ?, ?)", 
                         (new_thread, student_id, "New Study Session"))
            conn.commit()
            st.session_state.current_thread_id = new_thread
            st.session_state.editing_thread = None
            st.session_state.current_view = "chat" # Force view to chat
            st.rerun()
        
        threads = conn.execute("SELECT thread_id, title FROM threads WHERE student_id = ? ORDER BY rowid DESC", (student_id,)).fetchall()
        
        if not threads:
            default_thread = f"chat_{uuid.uuid4().hex[:8]}"
            conn.execute("INSERT INTO threads (thread_id, student_id, title) VALUES (?, ?, ?)", 
                         (default_thread, student_id, "New Study Session"))
            conn.commit()
            threads = [(default_thread, "New Study Session")]
            
        if "current_thread_id" not in st.session_state or st.session_state.current_thread_id not in [t[0] for t in threads]:
            st.session_state.current_thread_id = threads[0][0]

        st.markdown("**Previous Chats**")
        for thread_id, title in threads:
            if st.session_state.editing_thread == thread_id:
                new_title = st.text_input("Rename Chat", value=title, key=f"input_{thread_id}", label_visibility="collapsed")
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.button("💾", key=f"save_{thread_id}", use_container_width=True):
                        conn.execute("UPDATE threads SET title = ? WHERE thread_id = ?", (new_title, thread_id))
                        conn.commit()
                        st.session_state.editing_thread = None
                        st.rerun()
                with col_cancel:
                    if st.button("❌", key=f"cancel_{thread_id}", use_container_width=True):
                        st.session_state.editing_thread = None
                        st.rerun()
            else:
                col1, col2, col3 = st.columns([4, 1, 1])
                is_active = (thread_id == st.session_state.current_thread_id)
                icon = "🟢" if is_active else "💬"
                
                with col1:
                    if st.button(f"{icon} {title}", key=f"btn_{thread_id}", use_container_width=True, disabled=st.session_state.is_thinking):
                        st.session_state.current_thread_id = thread_id
                        st.session_state.current_view = "chat" # Force view to chat
                        st.rerun()
                with col2:
                    if st.button("✏️", key=f"edit_{thread_id}", disabled=st.session_state.is_thinking):
                        st.session_state.editing_thread = thread_id
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"del_{thread_id}", disabled=st.session_state.is_thinking):
                        conn.execute("DELETE FROM threads WHERE thread_id = ?", (thread_id,))
                        conn.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
                        conn.commit()
                        if st.session_state.current_thread_id == thread_id:
                            del st.session_state["current_thread_id"]
                        st.rerun()

    # --- 7. MAIN WINDOW LOGIC ---
    
    # VIEW A: PERFORMANCE DASHBOARD
    if st.session_state.current_view == "dashboard":
        st.title("📊 My Performance Dashboard")
        st.write(f"Welcome to your overall learning progress, **{student_id}**.")
        
        # Fetch live data from your FastAPI backend
        try:
            resp = requests.get(f"http://127.0.0.1:8000/dashboard/{student_id}")
            dashboard_data = resp.json() if resp.status_code == 200 else None
        except requests.exceptions.ConnectionError:
            dashboard_data = None
            st.error("🚨 Cannot connect to backend to load dashboard.")
            
        if dashboard_data:
            # --- Top Level Metrics ---
            metrics = dashboard_data.get("metrics", {})
            st.subheader("Overview")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Average Practice Score", value=f"{metrics.get('overall_score', 0)}%")
            with col2:
                st.metric(label="Topics Mastered", value=metrics.get('topics_mastered', 0)) 
            with col3:
                st.metric(label="Practice Sessions", value=metrics.get('total_sessions', 0))
                
            st.divider()
            
            # --- Weak Topics & Focus Areas ---
            st.subheader("🎯 Recommended Focus Areas")
            weak_topics = dashboard_data.get("weak_topics", [])
            
            if not weak_topics:
                st.success("Great job! You don't have any failed topics blocking you right now.")
            else:
                st.info("The system detected you failed the prerequisites for these topics:")
                cols = st.columns(len(weak_topics))
                for i, topic_name in enumerate(weak_topics):
                    with cols[i]:
                        st.error(f"**{topic_name}**\n\nStatus: Failed")
                        if st.button("Practice This", key=f"btn_weak_{i}"):
                            st.session_state.current_view = "chat"
                            st.rerun()

            st.divider()

            # --- Assessment History ---
            st.subheader("📝 Recent Assessment History")
            history = dashboard_data.get("history", [])
            
            if history:
                st.dataframe(history, use_container_width=True)
            else:
                st.info("No practice sessions logged yet. Ask the AI to generate a quiz to see your history here!")

    # VIEW B: PRACTICE SETUP & ACTIVE EXAM
    elif st.session_state.current_view == "practice":
        
        # 1. Initialize the Quiz State Machine in temporary memory
        if "quiz_phase" not in st.session_state:
            st.session_state.quiz_phase = "setup" # Phases: setup, active, finished
        if "quiz_history" not in st.session_state:
            st.session_state.quiz_history = [] # Holds the back-and-forth in RAM only
        
        if "thread_id" not in st.session_state:
            st.session_state.thread_id = str(uuid.uuid4())    
        
        current_student = st.session_state.get("student_id", "0001e847-507d-44d9-8683-7a879fc9689c")
            
        # ----------------------------------------
        # PHASE 1: THE SETUP FORM
        # ----------------------------------------
        if st.session_state.quiz_phase == "setup":
            st.title("📝 Setup Practice Session")
            st.write("Select your parameters to generate a custom assessment.")
            
            # Fetch cleaned dynamic topics
            try:
                res = requests.get(f"http://127.0.0.1:8000/topics/{current_student}")
                topic_options = res.json() if res.status_code == 200 else []
            except Exception:
                topic_options = []

            if not topic_options:
                topic_options = ["No topics available"]

            with st.form("practice_form"):
                col1, col2 = st.columns(2)
                with col1:
                    selected_course = st.selectbox("Select Course", ["CS101: Intro to AI", "CS201: Machine Learning"])
                    selected_difficulty = st.select_slider("Select Difficulty", options=["Easy", "Medium", "Hard"], value="Medium")
                with col2:
                    selected_topic = st.selectbox("Select Topic", topic_options)
                    
                st.divider()
                if st.form_submit_button("🚀 Start Quiz", type="primary", use_container_width=True):
                    
                    # --- FIXED: THE GATEKEEPER CHECK USING PARAMS ---
                    # This safely encodes special characters like '&' and spaces
                    eligibility_res = requests.get(
                        f"http://127.0.0.1:8000/check_eligibility/{current_student}",
                        params={
                            "topic": selected_topic,
                            "difficulty": selected_difficulty
                        }
                    )
                    eligibility = eligibility_res.json()

                    if not eligibility.get("allowed", False):
                        # Block the user! Add the backend refusal to history and lock the chat.
                        st.session_state.quiz_history.append({"role": "ai", "content": eligibility.get("message", "Access Denied")})
                        st.session_state.chat_disabled = True # Custom flag to lock the bar
                        st.session_state.quiz_phase = "active"
                        st.rerun()
                    else:
                        # Allow the user! Create the hidden prompt.
                        hidden_prompt = f"I am ready for a {selected_difficulty} quiz on {selected_topic} for {selected_course}. Ask me the first question. Evaluate my answer, give an explanation, then ask the next one."
                        st.session_state.quiz_history.append({"role": "user", "content": hidden_prompt})
                        
                        st.session_state.chat_disabled = False # Keep bar unlocked
                        st.session_state.quiz_phase = "active"
                        st.session_state.is_thinking = True
                        st.rerun()

        # ----------------------------------------
        # PHASE 2: THE ACTIVE EXAM
        # ----------------------------------------
        elif st.session_state.quiz_phase == "active":
            st.title("🧠 Active Practice Session")
            
            # Button to end the quiz and wipe the screen
            if st.button("🛑 End Quiz & Save to Dashboard", type="primary"):
                st.session_state.quiz_phase = "setup"
                st.session_state.quiz_history = [] # Wipe the temporary RAM!
                st.session_state.current_view = "dashboard" # Send them to see their new score
                
                # --- FIXED: WIPE THE AI'S MEMORY ---
                st.session_state.thread_id = str(uuid.uuid4())
                st.rerun()
                
            st.divider()

            # Render the quiz history from RAM (Not SQLite)
            for msg in st.session_state.quiz_history:
                # We skip showing the hidden setup prompt to the user
                if msg["content"].startswith("I am ready for a"): 
                    continue
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            
            # Answer input box
            if st.session_state.get("chat_disabled", False):
                # If access is denied, do NOT render the chat input at all.
                # Instead, show a clear message right where the chat bar used to be.
                st.warning("🔒 Chat is locked. Please click 'End Session & Go Back' to choose a different test.")
            
            else:
                # If allowed, render the chat bar normally without the disabled parameter.
                if answer := st.chat_input("Type your answer here..."):
                    
                    # 1. Add user message to history
                    st.session_state.quiz_history.append({"role": "user", "content": answer})
                    st.session_state.is_thinking = True
                    st.rerun()
            
            # Fetch AI Response
            if st.session_state.is_thinking:
                last_msg = st.session_state.quiz_history[-1]["content"]
                
                with st.chat_message("assistant"):
                    st.markdown("Evaluating...")
                    try:
                        # --- FIXED: USING DYNAMIC THREAD ID ---
                        response = requests.post(
                            "http://127.0.0.1:8000/chat",
                            json={
                                "student_id": current_student,
                                "message": last_msg, 
                                "thread_id": st.session_state.thread_id # Dynamic wipe!
                            }
                        )
                        if response.status_code == 200:
                            data = response.json()
                            assistant_response = data.get("response", "Error.")
                            st.session_state.quiz_history.append({"role": "assistant", "content": assistant_response})
                            
                    except requests.exceptions.ConnectionError:
                        st.error("🚨 Cannot connect to backend.")
                        
                    finally:
                        st.session_state.is_thinking = False
                        st.rerun()
                        
            # Fetch AI Response
            if st.session_state.is_thinking:
                last_msg = st.session_state.quiz_history[-1]["content"]
                
                with st.chat_message("assistant"):
                    st.markdown("Evaluating...")
                    try:
                        # Notice we send "quiz_mode" as the thread_id so the AI backend 
                        # knows to treat this as an isolated session
                        response = requests.post(
                            "http://127.0.0.1:8000/chat",
                            json={
                                "student_id": student_id,
                                "message": last_msg, 
                                "thread_id": f"ephemeral_quiz_{student_id}" 
                            }
                        )
                        if response.status_code == 200:
                            data = response.json()
                            assistant_response = data.get("response", "Error.")
                            st.session_state.quiz_history.append({"role": "assistant", "content": assistant_response})
                            
                    except requests.exceptions.ConnectionError:
                        st.error("🚨 Cannot connect to backend.")
                        
                    finally:
                        st.session_state.is_thinking = False
                        st.rerun()
    # VIEW C: AI TUTOR CHAT
    else:
        active_title_row = conn.execute("SELECT title FROM threads WHERE thread_id = ?", (st.session_state.current_thread_id,)).fetchone()
        active_title = active_title_row[0] if active_title_row else "Study Session"
        st.header(active_title)

        # 1. Fetch messages including the new 'sources' column
        messages = conn.execute("SELECT role, content, sources FROM messages WHERE thread_id = ? ORDER BY id ASC", (st.session_state.current_thread_id,)).fetchall()
        
        for role, content, sources in messages:
            with st.chat_message(role):
                st.markdown(content)
                # Render the popover if sources exist
                if sources:
                    with st.popover("📚 Sources"):
                        st.markdown(sources)
                
        if prompt := st.chat_input("Ask a question...", disabled=st.session_state.is_thinking):
            # 2. Insert the USER'S message (Explicitly passing None for sources)
            conn.execute("INSERT INTO messages (thread_id, role, content, sources) VALUES (?, ?, ?, ?)", 
                         (st.session_state.current_thread_id, "user", prompt, None))
            conn.commit()
            st.session_state.is_thinking = True
            st.rerun()

        if st.session_state.is_thinking:
            last_msg = conn.execute("SELECT content FROM messages WHERE thread_id = ? ORDER BY id DESC LIMIT 1", 
                                    (st.session_state.current_thread_id,)).fetchone()[0]
                                    
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🧠 Thinking...")
                
                try:
                    response = requests.post(
                        "http://127.0.0.1:8000/chat",
                        json={
                            "student_id": student_id,
                            "message": last_msg, 
                            "thread_id": st.session_state.current_thread_id
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        assistant_response = data.get("response", "Error.")
                        
                        # 3. Extract the AI's sources (Defaults to None if backend doesn't send them)
                        ai_sources = data.get("sources", None)
                        
                        # 4. Insert the AI'S message (Passing ai_sources)
                        conn.execute("INSERT INTO messages (thread_id, role, content, sources) VALUES (?, ?, ?, ?)", 
                                     (st.session_state.current_thread_id, "assistant", assistant_response, ai_sources))
                        
                        if active_title == "New Study Session":
                            new_title = last_msg[:20] + "..."
                            conn.execute("UPDATE threads SET title = ? WHERE thread_id = ?", (new_title, st.session_state.current_thread_id))
                        
                        conn.commit()
                        
                except requests.exceptions.ConnectionError:
                    st.error("🚨 Cannot connect to the backend. Is FastAPI running?")
                    
                finally:
                    st.session_state.is_thinking = False
                    st.rerun()
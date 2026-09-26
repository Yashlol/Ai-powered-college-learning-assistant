# 🎓 College AI Learning Assistant

An intelligent, decoupled learning platform designed for college students. The application combines an open-ended AI tutor with a strictly governed, structured assessment system.

It is built with a **Streamlit frontend**, **FastAPI/LangGraph backend**, and a **dual-database architecture** separating UI/session state from persistent academic records.

---

## 🚀 Key Features

### 1. Dual-Mode Interface

* **Tutor Chat**

  * Open-ended conversational learning.
  * Automatic document retrieval using **RAG (Retrieval-Augmented Generation)**.
  * Responses are grounded in the student's course materials.

* **Practice Mode**

  * Strict state-machine-driven assessment environment.
  * Generates practice quizzes.
  * Evaluates student answers.
  * Updates persistent academic records.
  * Prevents students from manipulating assessment results.

### 2. Dynamic Source Citations

AI responses automatically extract and display citation information from retrieved course materials.

The interface can surface:

* File names
* Page numbers
* Retrieved source information

This allows students to verify where an answer originated.

### 3. Live Performance Dashboard

The dashboard provides real-time academic analytics, including:

* Average score from recent attempts
* Total practice sessions
* Topics mastered
* Prerequisite failures
* Assessment progress

### 4. Academic Gatekeeping

The system implements a professor-controlled **Permission Slip** mechanism.

This controls whether a student is allowed to retake certain assessments based on their academic history.

SQL **Window Functions** are used to evaluate previous attempts and enforce retake rules.

### 5. Prompt Injection Defenses

The system uses multiple layers of protection against attempts to manipulate the assessment system.

Security controls operate at both:

* **Prompt level**
* **Python/backend level**

The system is designed to prevent students from:

* Bypassing assessment rules
* Dictating their own scores
* Manipulating grading instructions
* Asking the LLM to directly reveal answers to its own questions
* Injecting instructions into answer fields to influence backend tools

### 6. Deterministic Grading

The system avoids relying on the LLM for arithmetic calculations.

Instead:

1. The LLM extracts the raw points earned.
2. The Python backend validates the extracted value.
3. Python calculates the final percentage.
4. The verified result is stored in PostgreSQL.

This prevents score-calculation errors caused by LLM arithmetic hallucinations.

---

# 🛠️ Tech Stack

| Component           | Technology |
| ------------------- | ---------- |
| Frontend            | Streamlit  |
| Backend             | FastAPI    |
| Agent Framework     | LangGraph  |
| LLM Framework       | LangChain  |
| Academic Database   | PostgreSQL |
| UI/Session Database | SQLite     |
| ORM                 | SQLAlchemy |
| Retrieval           | RAG        |
| Language            | Python     |

---

# 🏗️ System Architecture

The application follows a strictly decoupled architecture.

```text
                    ┌──────────────────────┐
                    │       Student        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Streamlit       │
                    │      Frontend        │
                    └──────────┬───────────┘
                               │
                               │ HTTP/API
                               ▼
                    ┌──────────────────────┐
                    │       FastAPI        │
                    │       Backend        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      LangGraph       │
                    │    Agent Workflow    │
                    └───────┬───────┬──────┘
                            │       │
                 ┌──────────┘       └──────────┐
                 ▼                             ▼
        ┌─────────────────┐          ┌─────────────────┐
        │   RAG / Tools   │          │   Assessment    │
        │ Course Material │          │  State Machine  │
        └─────────────────┘          └────────┬────────┘
                                              │
                                              ▼
                                   ┌────────────────────┐
                                   │    PostgreSQL      │
                                   │ Academic Records   │
                                   └────────────────────┘

                    ┌──────────────────────┐
                    │       SQLite         │
                    │ UI / Chat Sessions   │
                    └──────────────────────┘
```

---

# 🖥️ Frontend — Streamlit

The Streamlit frontend is responsible for:

* UI rendering
* User authentication
* Displaying tutor responses
* Displaying quiz questions
* Collecting student answers
* Maintaining temporary quiz state using `st.session_state`
* Routing requests to the backend

The frontend **does not calculate grades or enforce academic rules**.

---

# ⚙️ Backend — FastAPI + LangGraph

The backend is responsible for:

* LLM agent routing
* Document retrieval
* Assessment generation
* Answer evaluation
* Academic rule enforcement
* Database operations
* Security validation

## Tutor Workflow

The tutoring agent follows a **Search First** policy.

```text
Student Question
       │
       ▼
Search Course Material
       │
       ▼
Retrieve Relevant Content
       │
       ▼
LLM Generates Answer
       │
       ▼
Attach Source Citations
       │
       ▼
Return Response
```

## Practice Workflow

Practice Mode follows a controlled assessment workflow:

```text
Start Practice
      │
      ▼
Check Eligibility
      │
      ▼
Generate Question
      │
      ▼
Collect Student Answer
      │
      ▼
Evaluate Answer
      │
      ▼
Calculate Score
      │
      ▼
Persist Academic Result
```

---

# 🗄️ Database Architecture

The application uses two databases for different responsibilities.

## PostgreSQL — System of Record

PostgreSQL stores persistent academic information such as:

* Students
* Courses
* Topics
* Lessons
* Assessments
* Questions
* Student attempts
* Student answers
* Scores
* Practice history
* Permissions
* Academic progress

PostgreSQL is treated as the **authoritative source for academic records**.

---

## SQLite — UI / Session Database

SQLite is used for application-level state such as:

* Chat threads
* UI sessions
* Conversation history
* Streamlit-related state

The SQLite database is generated automatically when the frontend is first started, assuming the application is configured to initialize it.

Practice assessments are intentionally kept separate from the persistent chat database.

---

# 🧠 RAG-Based Tutor

The tutor uses **Retrieval-Augmented Generation (RAG)** to answer questions from the student's course materials.

```text
Student Question
       │
       ▼
Query Processing
       │
       ▼
Document Retrieval
       │
       ▼
Relevant Course Content
       │
       ▼
LLM
       │
       ▼
Grounded Response
       │
       ▼
Source Citation
```

The system can expose the source document and page information used to construct the response.

---

# 🔒 Security Implementations

The application uses multiple layers of protection to prevent students from manipulating the assessment workflow.

## 1. Tool Execution Verification

Backend tools do not blindly trust LLM-generated instructions.

Before a database operation is performed, the backend validates the required evidence, such as the student's actual answer.

```text
LLM Request
     │
     ▼
Python Validation
     │
     ├── Invalid → Reject
     │
     └── Valid
          │
          ▼
     Database Operation
```

This creates a security boundary between the LLM and the database.

---

## 2. Input Validation

Student input is validated before sensitive operations are executed.

Examples include:

* Minimum answer length
* Invalid input detection
* Prompt-injection pattern detection
* Score manipulation attempts
* Unauthorized assessment commands

---

## 3. Ephemeral Quiz State

Practice exams do not rely on the persistent SQLite chat database.

Instead, the active assessment exists in temporary application/session state.

```text
Start Quiz
    │
    ▼
RAM / Session State
    │
    ▼
Questions + Answers
    │
    ▼
Assessment Complete
    │
    ▼
Result → PostgreSQL
    │
    ▼
Temporary Quiz State Cleared
```

This keeps practice sessions separate from normal chat history and reduces the possibility of students manipulating persistent chat transcripts to influence assessment state.

---

# 📊 Academic Performance Tracking

Student performance is persisted in PostgreSQL and can be used to calculate:

* Average scores
* Recent assessment performance
* Number of completed practice sessions
* Topic mastery
* Prerequisite failures
* Assessment eligibility

This allows the application to provide personalized academic feedback while keeping academic records separate from temporary UI state.

---

# ⚙️ Environment Requirements

Before running the application, make sure you have:

* Python 3.10+
* PostgreSQL
* Git
* An API key for the configured LLM provider
* A properly configured `.env` file

---

# 💻 Local Setup & Installation

## 1. Clone the Repository

```bash
git clone https://github.com/Yashlol/Ai-powered-college-learning-assistant.git

cd ai-learning-assistant
```

> If Git creates a different directory name, use that directory name with `cd`.

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Configure Environment Variables

Create a `.env` file in the project root.

Example:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# Use the API key required by your configured LLM provider
OPENAI_API_KEY=your_api_key_here
```

If your project uses Google Gemini instead, use the environment variable expected by your implementation:

```env
GOOGLE_API_KEY=your_api_key_here
```

> **Important:** Use the exact environment-variable names expected by your backend configuration.

### Never commit API keys

Add the following to `.gitignore`:

```gitignore
.env
*.db
__pycache__/
*.pyc
```

---

# 🗃️ PostgreSQL Setup

Make sure PostgreSQL is running locally.

Create the required database and configure the connection string in `.env`.

Example:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/college_ai
```

The exact database name, username, password, and port depend on your local PostgreSQL configuration.

---

# 🗂️ SQLite Setup

The SQLite UI database:

```text
streamlit_ui.db
```

is automatically created when the Streamlit frontend starts, assuming the application contains the required initialization logic.

---

# ▶️ Running the Application

## 1. Start the FastAPI Backend

Open a terminal in the project directory:

```bash
uvicorn main:app --reload
```

---

## 2. Start the Streamlit Frontend

Open a **second terminal** and run:

```bash
streamlit run frontend.py
```

> If your actual Streamlit entry file is `app.py`, use:
>
> ```bash
> streamlit run app.py
> ```

---

# 📁 Project Structure

The structure below represents the intended organization. Update folder names if your repository uses different names.

```text
# 📁 Project Structure

```text
Ai-powered-college-learning-assistant/
│
├── frontend.py            # Streamlit application and UI state management
├── requirements.txt       # Python dependencies
├── .env                   # (Ignored) API keys and database credentials
├── .gitignore             # Git ignore rules for DBs and environments
├── README.md              # Project documentation
│
├── app/                   # Backend Application Module
│   ├── main.py            # FastAPI entry point and API endpoints
│   ├── agent.py           # LangGraph agent setup and workflow state
│   ├── database.py        # PostgreSQL connection and session management
│   ├── models.py          # SQLAlchemy ORM definitions
│   ├── rag.py             # Document loading, vector store, and retrievers
│   ├── rules.py           # Security guardrails and business logic
│   ├── etl_script.py      # Data extraction and transformation scripts
│   └── seedscript.py      # Database initialization and mock data
│
├── data/                  # Data tracking and assets
│   └── [Your Excel File].xlsx 
│
├── course_materials/      # Unstructured course PDFs (e.g., Ethics for AI)
│
├── streamlit_ui.db        # (Ignored by Git) Local UI and chat memory
└── checkpoints.sqlite     # (Ignored by Git) LangGraph state memory
```

---

# 🎯 Design Principles

## Separation of Responsibilities

The frontend handles presentation and user interaction, while the backend handles business logic, academic rules, and database operations.

## LLM as a Controlled Component

The LLM is not treated as a trusted authority.

Sensitive operations are validated by deterministic Python code before execution.

## Database as the Source of Truth

Academic results and permissions are stored in PostgreSQL rather than relying on LLM output or frontend state.

## Deterministic Computation

Critical calculations such as scores and percentages are performed by Python rather than delegated to the LLM.

## Security by Multiple Layers

Prompt-level instructions are combined with backend validation so that a successful prompt injection does not automatically grant access to sensitive operations.

---

# 🔄 Data Flow

### Tutor Mode

```text
Student
   │
   ▼
Streamlit
   │
   ▼
FastAPI
   │
   ▼
LangGraph
   │
   ▼
RAG Retrieval
   │
   ▼
Course Documents
   │
   ▼
LLM
   │
   ▼
Response + Citations
   │
   ▼
Streamlit
```

### Practice Mode

```text
Student
   │
   ▼
Streamlit
   │
   ▼
FastAPI
   │
   ▼
Eligibility Check
   │
   ▼
LangGraph Assessment Workflow
   │
   ├── Generate Question
   │
   ├── Collect Answer
   │
   ├── Validate Answer
   │
   └── Calculate Score
   │
   ▼
PostgreSQL
   │
   ▼
Performance Dashboard
```

---

# 🚀 Future Improvements

Potential extensions include:

* Role-based dashboards for students and professors
* Professor-controlled question banks
* Advanced prerequisite graphs
* Adaptive question difficulty
* Detailed learning analytics
* Automated weak-topic recommendations
* Audit logs for assessment actions
* Redis-based session management
* Docker-based deployment
* PostgreSQL connection pooling
* Automated security and grading tests
* Production deployment with CI/CD

---

# 📌 Important Security Notes

This project should never expose production credentials in the source code.

Before pushing to GitHub, verify that:

```text
.env              → NOT committed
API keys          → NOT committed
Database password → NOT committed
streamlit_ui.db   → NOT committed
```

Use `.env.example` if you want to show other developers which environment variables are required:

```env
DATABASE_URL=
OPENAI_API_KEY=
# GOOGLE_API_KEY=
```

---

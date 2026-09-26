from app.database import SessionLocal, engine
from app.models import Base, TopicPrerequisite

# Create the new table in the database
Base.metadata.create_all(bind=engine)

def seed_prerequisites():
    db = SessionLocal()
    try:
        # Hierarchical mapping using EXACT strings from the 425 failed topics list
        prerequisites = [
            
            # ---------------------------------------------------------
            # TRACK 1: PYTHON & DATA SCIENCE
            # ---------------------------------------------------------
            {"target": "Python Conditional Statements", "required": "Python Basics"},
            {"target": "Python Loops", "required": "Python Basics"},
            {"target": "Python Variables", "required": "Python Basics"},
            {"target": "python data types", "required": "Python Basics"},
            {"target": "Python-OOPS", "required": "Python Basics"},
            {"target": "Python File handling", "required": "Python Conditional Statements"},
            
            # Data Science Core
            {"target": "Data Science Basics", "required": "Python Basics"},
            {"target": "Numpy", "required": "Python Basics"},
            {"target": "Pandas", "required": "Python Basics"},
            {"target": "Numpy Arrays", "required": "Numpy"},
            {"target": "Numpy Operations", "required": "Numpy Arrays"},
            {"target": "Pandas DataFrames", "required": "Pandas"},
            {"target": "DataFrame Operations", "required": "Pandas DataFrames"},
            {"target": "Exploratory Data Analysis", "required": "Pandas DataFrames"},
            {"target": "Data Visualization", "required": "Exploratory Data Analysis"},
            {"target": "Matplotlib", "required": "Data Visualization"},

            # ---------------------------------------------------------
            # TRACK 2: MACHINE LEARNING & AI
            # ---------------------------------------------------------
            {"target": "Machine Learning Basics", "required": "Python Basics"},
            {"target": "Machine Learning Basics", "required": "Statistics"},
            {"target": "Machine Learning Process", "required": "Machine Learning Basics"},
            {"target": "Supervised Learning", "required": "Machine Learning Process"},
            
            # Algorithms
            {"target": "Linear Regression", "required": "Supervised Learning"},
            {"target": "Logistic Regression", "required": "Supervised Learning"},
            {"target": "Decision Trees", "required": "Supervised Learning"},
            {"target": "K-Nearest Neighbors (KNN)", "required": "Supervised Learning"},
            {"target": "Support Vector Machines (SVM)", "required": "Supervised Learning"},
            {"target": "Random Forest", "required": "Decision Trees"},
            
            # Evaluation & Tuning
            {"target": "Model Evaluation Metrics", "required": "Machine Learning Process"},
            {"target": "Model Tuning", "required": "Model Evaluation Metrics"},
            {"target": "Model Comparison", "required": "Model Evaluation Metrics"},
            {"target": "Hyperparameter Tuning in Regression", "required": "Linear Regression"},
            
            # Deep Learning & AI
            {"target": "Deep Learning", "required": "Machine Learning"},
            {"target": "Neural Networks Architecture", "required": "Deep Learning"},
            {"target": "Generative Adversarial Networks (GANs)", "required": "Neural Networks Architecture"},
            {"target": "NLP", "required": "Neural Networks Architecture"},
            {"target": "computer vision", "required": "Neural Networks Architecture"},
            {"target": "Artificial Intelligence Basics", "required": "Machine Learning Basics"},

            # ---------------------------------------------------------
            # TRACK 3: DATA STRUCTURES & ALGORITHMS (DSA)
            # ---------------------------------------------------------
            {"target": "Data structure", "required": "Basic Programming"},
            {"target": "Array", "required": "Data structure"},
            {"target": "Strings", "required": "Data structure"},
            {"target": "2d-arrays", "required": "Array"},
            {"target": "Searching", "required": "Array"},
            {"target": "Sorting", "required": "Array"},
            {"target": "Linear Search", "required": "Searching"},
            {"target": "Binary Search", "required": "Searching"},
            {"target": "Bubble Sort", "required": "Sorting"},
            {"target": "Merge Sort", "required": "Sorting"},
            {"target": "Quick Sort", "required": "Sorting"},
            
            {"target": "Linked Lists", "required": "Data structure"},
            {"target": "Singly Linked List", "required": "Linked Lists"},
            {"target": "stacks and queues", "required": "Linked Lists"},
            {"target": "Trees", "required": "Linked Lists"},
            {"target": "Binary Trees", "required": "Trees"},
            {"target": "AVL Trees", "required": "Binary Trees"},
            {"target": "Graphs", "required": "Trees"},
            {"target": "Dijkstra's Algorithm", "required": "Graphs"},

            # ---------------------------------------------------------
            # TRACK 4: WEB DEVELOPMENT
            # ---------------------------------------------------------
            {"target": "HTML & CSS", "required": "Web Technology"},
            {"target": "HTML Elements", "required": "HTML & CSS"},
            {"target": "HTML Forms", "required": "HTML Elements"},
            {"target": "CSS Selectors", "required": "HTML & CSS"},
            {"target": "Flexbox", "required": "CSS Selectors"},
            {"target": "Grid", "required": "CSS Selectors"},
            
            # JS & Frameworks
            {"target": "JavaScript", "required": "HTML & CSS"},
            {"target": "javascript data types", "required": "JavaScript"},
            {"target": "javascript variables", "required": "JavaScript"},
            {"target": "DOM", "required": "JavaScript"},
            
            {"target": "ReactJS", "required": "JavaScript"},
            {"target": "React Components", "required": "ReactJS"},
            {"target": "React Lifecycle", "required": "React Components"},
            {"target": "React Router", "required": "React Components"},
            {"target": "NodeJS", "required": "JavaScript"},
            {"target": "Building RESTful APIs", "required": "NodeJS"},
            {"target": "Django", "required": "Python Basics"},
            {"target": "django-models", "required": "Django"},

            # ---------------------------------------------------------
            # TRACK 5: CYBER SECURITY & NETWORKING
            # ---------------------------------------------------------
            {"target": "Network Protocols", "required": "Network Concepts"},
            {"target": "OSI Model", "required": "Network Concepts"},
            {"target": "TCP/IP Model", "required": "Network Concepts"},
            {"target": "Information Security Fundamentals", "required": "Network Concepts"},
            {"target": "Cyber Security", "required": "Information Security Fundamentals"},
            {"target": "Ethical Hacking", "required": "Cyber Security"},
            {"target": "Scanning Techniques", "required": "Ethical Hacking"},
            {"target": "Vulnerability Management", "required": "Ethical Hacking"},
            {"target": "Cyber Attack Types", "required": "Cyber Security"},
            {"target": "Malware", "required": "Cyber Attack Types"},

            # ---------------------------------------------------------
            # TRACK 6: VLSI & EMBEDDED SYSTEMS
            # ---------------------------------------------------------
            {"target": "Digital Circuits", "required": "Basic Programming"},
            {"target": "Logical Gates", "required": "Digital Circuits"},
            {"target": "Boolean Algebra", "required": "Logical Gates"},
            {"target": "Flip Flops", "required": "Digital Circuits"},
            {"target": "Adders&subtractors", "required": "Digital Circuits"},
            
            {"target": "VLSI", "required": "Digital Circuits"},
            {"target": "ASIC Design Flow", "required": "VLSI"},
            {"target": "Gate level Modelling", "required": "VLSI"},
            
            {"target": "Embedded system", "required": "Basic Programming"},
            {"target": "arduino UNO architecture", "required": "Embedded system"},
            {"target": "Sensors", "required": "Embedded system"},
            {"target": "Actuators", "required": "Embedded system"},
            {"target": "Interfacing LED& switch with Arduino", "required": "arduino UNO architecture"}
        ]
        
        # Check if already seeded to prevent duplicates
        if db.query(TopicPrerequisite).first() is None:
            for item in prerequisites:
                new_prereq = TopicPrerequisite(
                    target_topic=item["target"].lower(),
                    required_topic=item["required"].lower()
                )
                db.add(new_prereq)
            db.commit()
            print(f"Successfully seeded {len(prerequisites)} prerequisite rules into the database!")
        else:
            print("Prerequisites already exist in the database.")
            
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_prerequisites()
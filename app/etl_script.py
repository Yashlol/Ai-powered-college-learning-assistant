import pandas as pd
import json
import numpy as np
from app.database import push_dataframes_to_db

def process_student_data(file_path: str):
    print(f"Loading data from {file_path} (Result 1)...")
    df = pd.read_excel(file_path, sheet_name='Result 1')
    
    # CHANGED: Safely replace NaN with None for PostgreSQL insertion
    df = df.replace({np.nan: None})
    
    students_data = []
    assessments_data = {}  
    scores_data = []
    topic_performance_data = []

    for index, row in df.iterrows():
        student_id = str(row['id'])
        
        students_data.append({
            'student_id': student_id,
            'name': row.get('name'),
            'email': row.get('email'),
            'roll_number': row.get('roll_number'),
            'college_id': row.get('college_id')
        })

        for i in range(1, 16):
            col_name = f'hackathon_{i}'
            if pd.notna(row.get(col_name)) and row.get(col_name) is not None:
                try:
                    data = json.loads(row[col_name])
                    
                    assessment_id = data['hackathon']['id']
                    if assessment_id not in assessments_data:
                        assessments_data[assessment_id] = {
                            'assessment_id': assessment_id,
                            'title': data['hackathon']['title'],
                            'start_date': data['hackathon']['start_date']
                        }
                    
                    total_score = data['participation'].get('current_score', 0)
                    scores_data.append({
                        'student_id': student_id,
                        'assessment_id': assessment_id,
                        'total_score': total_score
                    })
                    
                    if 'submissions' in data:
                        for sub in data['submissions']:
                            status = sub.get('status', 'unknown') 
                            sub_domains = sub.get('question_sub_domain', ["Unknown"])
                            sub_domain = sub_domains[0] if sub_domains else "Unknown"
                            
                            topic_performance_data.append({
                                'student_id': student_id,
                                'assessment_id': assessment_id,
                                'sub_domain': sub_domain,
                                'status': status
                            })
                except Exception as e:
                    print(f"Error parsing JSON for student {student_id} in {col_name}: {e}")

    return pd.DataFrame(students_data), pd.DataFrame(list(assessments_data.values())), pd.DataFrame(scores_data), pd.DataFrame(topic_performance_data)


def process_courses_data(file_path: str):
    print(f"Loading courses data from {file_path} (Sheet1)...")
    try:
        df_courses = pd.read_excel(file_path, sheet_name='Sheet1') 
    except Exception as e:
         print(f"Error loading second sheet: {e}")
         return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_courses = df_courses.replace({np.nan: None})

    # CHANGED: Added students_data array to capture the different population in Sheet1
    students_data = []
    course_progress_data = []
    courses_dict = {} 

    for index, row in df_courses.iterrows():
        student_id = str(row['id'])
        
        # CHANGED: Extract student profile from Sheet1
        students_data.append({
            'student_id': student_id,
            'name': row.get('name'),
            'email': row.get('email'),
            'roll_number': row.get('roll_number'),
            'college_id': row.get('college_id')
        })
        
        if pd.notna(row.get('courses')) and row.get('courses') is not None:
            try:
                courses_json = json.loads(row['courses'])
                for course_entry in courses_json:
                    course_id = str(course_entry.get('course_id'))
                    progress_info = course_entry.get('progress', {})
                    
                    if course_id not in courses_dict:
                        courses_dict[course_id] = {
                            'course_id': course_id,
                            'title': f"Course {course_id}", 
                            'description': "Course details unavailable."
                        }
                    
                    completion_percentage = progress_info.get('progress_percentage', 0.0)
                    is_completed = progress_info.get('is_completed', False)
                    status = "Completed" if is_completed else "In Progress"
                    
                    course_progress_data.append({
                        'student_id': student_id,
                        'course_id': course_id,
                        'completion_percentage': completion_percentage,
                        'status': status
                    })
            except Exception as e:
                print(f"Error parsing courses JSON for student {student_id}: {e}")

    # CHANGED: Now returning 3 dataframes (including the Sheet1 students)
    return pd.DataFrame(students_data), pd.DataFrame(list(courses_dict.values())), pd.DataFrame(course_progress_data)


# CHANGED: Added orchestrator function to safely combine data before pushing
def run_etl(file_path: str):
    # 1. Extract from both sheets
    hackathon_students, assessments, scores, topics = process_student_data(file_path)
    course_students, courses, progress = process_courses_data(file_path)
    
    # 2. THE FIX: Combine both student lists and drop any duplicates to create a master identity table
    print("\nMerging student populations...")
    master_students_df = pd.concat([hackathon_students, course_students], ignore_index=True)
    master_students_df = master_students_df.drop_duplicates(subset=['student_id'], keep='first')
    
    print(f"Total Unique Students across all sheets: {len(master_students_df)}")
    
    # 3. Push to DB (No Foreign Key crashes!)
    push_dataframes_to_db(master_students_df, assessments, scores, topics, courses, progress)



if __name__ == "__main__":
    # Replace with your actual file path
    run_etl(r"C:\Users\Yash\OneDrive\Desktop\Ai powered college learning assistant\data\Course & Hackathon details of top 100 performers in each.xlsx")
    
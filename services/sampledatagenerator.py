import pandas as pd  # For creating and manipulating dataframes
import numpy as np  # For numerical operations
import random  # For generating random data
from datetime import datetime, timedelta  # For date manipulations
from supabase import create_client, Client  # For Supabase client
def generate_sample_data_based_on_query(query):
    """Generate appropriate sample data based on the query"""
    if 'workforce_reskilling_events' in query:
        return generate_sample_event_data()
    elif 'employee_profile' in query and 'job_risk' in query:
        return generate_sample_knowledge_graph_data()
    elif 'training_duration' in query:
        return generate_sample_causal_data()
    else:
        return pd.DataFrame()
    
def generate_sample_event_data():
    """Generate sample event data for process mining"""
    activities = ['Course Assigned', 'Module 1 Completed', 'Module 2 Completed',
                 'Assessment Taken', 'Certification Exam', 'Completed Training']
    skills = ['Cybersecurity', 'Data Science', 'AI', 'Cloud Computing', 'Software Development']
    actors = ['Employee', 'Trainer', 'System', 'Manager']
    statuses = ['Completed', 'In Progress', 'Failed', 'Pending']

    data = []
    # Generate 100 cases with 4-6 events each
    for case_id in range(1, 101):
        employee_id = np.random.randint(1000, 9999)
        skill = np.random.choice(skills)
        # Ensure events are in chronological order
        start_date = pd.Timestamp('2023-01-01') + pd.Timedelta(days=np.random.randint(0, 365))

        # Number of events for this case
        num_events = np.random.randint(4, 7)

        # Generate events
        for i in range(num_events):
            if i < len(activities):
                activity = activities[i]  # Sequential activities
            else:
                activity = np.random.choice(activities)

            # Timestamp increases with each activity
            timestamp = start_date + pd.Timedelta(days=i*np.random.randint(3, 15))

            # Score only applicable for certain activities
            score = np.random.uniform(50, 100) if 'Assessment' in activity or 'Exam' in activity else None

            # Completion status
            status = statuses[min(i, len(statuses)-1)]

            data.append({
                'case_id': case_id,
                'employee_id': employee_id,
                'activity': activity,
                'timestamp': timestamp,
                'actor': np.random.choice(actors),
                'skill_category': skill,
                'score': score,
                'completion_status': status
            })

    return pd.DataFrame(data)

def generate_sample_knowledge_graph_data():
    """Generate sample data for knowledge graph analysis"""
    job_titles = ['Data Analyst', 'Software Developer', 'Customer Service Rep',
                 'Administrative Assistant', 'Financial Analyst', 'Sales Representative']
    training_programs = ['Digital Skills', 'Cybersecurity', 'Cloud Computing',
                        'Data Science', 'AI Fundamentals', 'Soft Skills']

    data = []
    # Generate 200 employee records
    for employee_id in range(1000, 1200):
        job_title = np.random.choice(job_titles)
        soc_code = np.random.randint(1000, 9999)

        # Higher automation risk for certain jobs
        if job_title in ['Customer Service Rep', 'Administrative Assistant']:
            automation_prob = np.random.uniform(0.7, 0.9)
        else:
            automation_prob = np.random.uniform(0.3, 0.7)

        # Not all employees have training
        if np.random.random() > 0.2:
            case_id = np.random.randint(1, 500)
            training_program = np.random.choice(training_programs)
            start_date = pd.Timestamp('2023-01-01') + pd.Timedelta(days=np.random.randint(0, 365))

            # Some training programs have better completion rates
            if training_program in ['Digital Skills', 'Soft Skills']:
                completion_likelihood = 0.8
            else:
                completion_likelihood = 0.6

            # Determine if completed
            completed = np.random.random() < completion_likelihood
            completion_date = start_date + pd.Timedelta(days=np.random.randint(30, 120)) if completed else None

            # Certification more likely with completed training and certain programs
            if completed and training_program in ['Cybersecurity', 'AI Fundamentals']:
                cert_likelihood = 0.9
            elif completed:
                cert_likelihood = 0.7
            else:
                cert_likelihood = 0

            certified = np.random.random() < cert_likelihood
        else:
            case_id = None
            training_program = None
            start_date = None
            completion_date = None
            certified = None

        data.append({
            'employee_id': employee_id,
            'job_title': job_title,
            'soc_code': soc_code,
            'automation_probability': automation_prob,
            'case_id': case_id,
            'training_program': training_program,
            'start_date': start_date,
            'completion_date': completion_date,
            'certification_earned': certified
        })

    return pd.DataFrame(data)

def generate_sample_causal_data():
    """Generate sample data for causal analysis"""
    training_programs = ['Digital Skills', 'Cybersecurity', 'Cloud Computing',
                        'Data Science', 'AI Fundamentals', 'Soft Skills']
    skill_categories = ['Technical', 'Analytical', 'Security', 'Communication', 'Programming']

    data = []
    # Generate 300 training records
    for _ in range(300):
        # Automation probability affects training outcome
        automation_prob = np.random.uniform(0.3, 0.9)
        training_program = np.random.choice(training_programs)
        skill_category = np.random.choice(skill_categories)

        # Score influenced by program type and automation risk
        base_score = np.random.uniform(60, 90)
        if automation_prob > 0.7 and training_program in ['Digital Skills', 'Cybersecurity']:
            # High automation jobs struggle with technical training
            score_modifier = -10
        elif automation_prob < 0.5 and training_program in ['Data Science', 'AI Fundamentals']:
            # Low automation jobs do better with advanced training
            score_modifier = 10
        else:
            score_modifier = 0

        score = min(100, max(0, base_score + score_modifier))

        # Certification based on score and program
        cert_threshold = 75 if training_program in ['Cybersecurity', 'Data Science'] else 70
        certified = score > cert_threshold

        # Completion status
        completion_status = 'Completed' if score > 65 else 'Failed'

        # Training duration (days) - affected by program type and score
        base_duration = np.random.randint(30, 90)
        if score < 70:
            duration_modifier = np.random.randint(10, 30)  # Takes longer if struggling
        else:
            duration_modifier = -np.random.randint(0, 15)  # Faster if doing well

        training_duration = max(14, base_duration + duration_modifier)

        data.append({
            'automation_probability': automation_prob,
            'training_program': training_program,
            'certification_earned': certified,
            'skill_category': skill_category,
            'score': score,
            'completion_status': completion_status,
            'training_duration': training_duration
        })

    return pd.DataFrame(data)


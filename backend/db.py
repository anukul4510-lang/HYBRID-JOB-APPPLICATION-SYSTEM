import json
import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(script_dir, 'users_db.json')

def load_db():
    try:
        db = {
            'jobseekers': [],
            'recruiters': [],
            'jobs': [],
            'applications': []
        }
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f:
                db_from_file = json.load(f)
                db.update(db_from_file)
        return db
    except Exception as e:
        print(f"Error loading database: {e}")
        return {
            'jobseekers': [],
            'recruiters': [],
            'jobs': [],
            'applications': []
        }

def save_db(db):
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(db, f, indent=2)
    except Exception as e:
        print(f"Error saving database: {e}")

# Initialize database
users_db = load_db()
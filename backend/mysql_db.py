import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

def create_connection():
    """Establishes and returns a new MySQL database connection."""
    try:
        db_host = os.getenv("DB_HOST", "localhost")
        db_user = os.getenv("DB_USER", "root")
        db_password = os.getenv("DB_PASSWORD", "password")
        db_name = os.getenv("DB_NAME", "job_portal_db")

        # Connect to MySQL server to create the database if it doesn't exist
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.close()
        conn.close()

        # Now connect to the specific database
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

def create_tables():
    """Creates necessary tables if they don't exist."""
    conn = create_connection()
    if conn is None:
        print("Could not establish database connection to create tables.")
        return

    cursor = conn.cursor()

    tables = {}
    tables['users'] = (
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            user_type ENUM('jobseeker', 'recruiter') NOT NULL,
            name VARCHAR(255),
            phone VARCHAR(20),
            company VARCHAR(255),
            location VARCHAR(255),
            experience_level VARCHAR(50),
            education VARCHAR(255),
            skills JSON, -- Storing skills as JSON
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    tables['jobs'] = (
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            recruiter_id INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            location VARCHAR(255),
            employmentType VARCHAR(50),
            description TEXT,
            skills VARCHAR(255), -- Storing skills as comma-separated string
            minSalary VARCHAR(50),
            maxSalary VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recruiter_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    tables['applications'] = (
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_id INT NOT NULL,
            jobseeker_id INT NOT NULL,
            application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status ENUM('pending', 'reviewed', 'shortlisted', 'rejected') DEFAULT 'pending',
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
            FOREIGN KEY (jobseeker_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    tables['job_preferences'] = (
        """
        CREATE TABLE IF NOT EXISTS job_preferences (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL UNIQUE, -- Renamed from jobseeker_id to user_id for consistency with users table
            preferred_role VARCHAR(255),
            preferred_industry VARCHAR(255),
            work_mode VARCHAR(50),
            job_type VARCHAR(50),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    tables['shortlisted_candidates'] = (
        """
        CREATE TABLE IF NOT EXISTS shortlisted_candidates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            recruiter_id INT NOT NULL,
            candidate_id INT NOT NULL,
            job_id INT, -- Optional: to link shortlist to a specific job
            shortlisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (recruiter_id, candidate_id, job_id), -- Prevent duplicate shortlists for the same job
            FOREIGN KEY (recruiter_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (candidate_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
        """
    )

    tables['resume_files'] = (
        """
        CREATE TABLE IF NOT EXISTS resume_files (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            stored_filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(255) NOT NULL,
            file_size INT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    for table_name in tables:
        table_sql = tables[table_name]
        try:
            print(f"Creating table {table_name}:")
            cursor.execute(table_sql)
            conn.commit()
            print(f"Table {table_name} created or already exists.")
        except mysql.connector.Error as err:
            print(f"Error creating table {table_name}: {err}")

    cursor.close()
    conn.close()


def search_jobs(location=None, salary=None, experience=None, skills=None, job_type=None):
    """Searches for jobs based on given criteria."""
    conn = create_connection()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if location:
        query += " AND location LIKE %s"
        params.append(f"%{location}%")
    
    if salary:
        query += " AND (minSalary >= %s OR maxSalary >= %s)"
        params.extend([salary, salary])

    if experience:
        # This is a simplified search. A more robust implementation would handle ranges.
        query += " AND description LIKE %s"
        params.append(f"%{experience} years%")

    if skills:
        for skill in skills:
            query += " AND skills LIKE %s"
            params.append(f"%{skill}%")

    if job_type:
        query += " AND employmentType LIKE %s"
        params.append(f"%{job_type}%")

    try:
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        print(f"Error searching jobs: {err}")
        return []
    finally:
        cursor.close()
        conn.close()


def search_candidates(location=None, skills=None):
    """Searches for candidates based on given criteria."""
    conn = create_connection()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM users WHERE user_type = 'jobseeker'"
    params = []

    if location:
        query += " AND location LIKE %s"
        params.append(f"%{location}%")

    if skills:
        # This assumes skills are stored in a JSON array.
        for skill in skills:
            query += " AND JSON_CONTAINS(skills, %s)"
            params.append(f'"{skill}"')

    try:
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        print(f"Error searching candidates: {err}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_jobs_by_ids(ids):
    """Retrieves jobs by their IDs."""
    conn = create_connection()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM jobs WHERE id IN (%s)"
    placeholders = ', '.join(['%s'] * len(ids))
    query = query % placeholders
    
    try:
        cursor.execute(query, tuple(ids))
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        print(f"Error getting jobs by ids: {err}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_candidates_by_ids(ids):
    """Retrieves candidates by their IDs."""
    conn = create_connection()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM users WHERE id IN (%s)"
    placeholders = ', '.join(['%s'] * len(ids))
    query = query % placeholders

    try:
        cursor.execute(query, tuple(ids))
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        print(f"Error getting candidates by ids: {err}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_all_data_from_table(table_name):
    """Retrieves all data from a specified table."""
    conn = create_connection()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    query = f"SELECT * FROM {table_name}"
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        print(f"Error getting all data from {table_name}: {err}")
        return []
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    create_tables()
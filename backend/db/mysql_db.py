"""
File: mysql_db.py
Purpose: Handles all interactions with the MySQL database, including connection
         creation, table setup, and data manipulation (CRUD operations).

Author: [Your Name]
Date: 26/09/2025

"""

import mysql.connector
import os
import sys

# Add the project root to the Python path to enable absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.core.config import settings

def create_connection():
    """
    Establishes and returns a new MySQL database connection.

    This function uses credentials from the application settings. It first connects
    to the MySQL server to create the database if it doesn't already exist,
    ensuring the application can start up smoothly without manual database setup.

    Returns:
        mysql.connector.connection.MySQLConnection: A connection object to the database.
        None: If the connection fails for any reason.
    """
    try:
        # Step 1: Connect to the MySQL server to ensure the database exists.
        conn = mysql.connector.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME}")
        cursor.close()
        conn.close()

        # Step 2: Connect to the specific database now that it is guaranteed to exist.
        conn = mysql.connector.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

def create_tables():
    """
    Creates all necessary tables in the database if they do not already exist.
    This function defines the schema for the entire application and should be
    run once on application startup.
    """
    conn = create_connection()
    if conn is None:
        print("Could not establish database connection to create tables.")
        return

    cursor = conn.cursor()

    # A dictionary to hold all CREATE TABLE statements for organization.
    tables = {}

    # --- Table Definitions ---

    tables['users'] = (
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for each user
            email VARCHAR(255) NOT NULL UNIQUE, -- User's email, used for login
            password VARCHAR(255) NOT NULL, -- Hashed password for security
            user_type ENUM('jobseeker', 'recruiter') NOT NULL, -- Role of the user
            name VARCHAR(255), -- User's full name
            phone VARCHAR(20), -- User's contact phone number
            company VARCHAR(255), -- Company name (for recruiters)
            location VARCHAR(255), -- User's physical location
            experience_level VARCHAR(50), -- Jobseeker's experience level (e.g., 'Entry', 'Mid', 'Senior')
            education TEXT, -- Jobseeker's educational background
            skills JSON, -- Storing jobseeker skills as a JSON array for flexibility
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Timestamp of account creation
        )
        """
    )

    tables['jobs'] = (
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for each job posting
            recruiter_id INT NOT NULL, -- Foreign key linking to the recruiter (user) who posted the job
            title VARCHAR(255) NOT NULL, -- Job title
            location VARCHAR(255), -- Job location
            employmentType VARCHAR(50), -- Type of employment (e.g., 'Full-time', 'Part-time', 'Contract')
            description TEXT, -- Detailed job description
            skills TEXT, -- Required skills (stored as a comma-separated string)
            minSalary INT, -- Minimum salary for the position
            maxSalary INT, -- Maximum salary for the position
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp of job posting
            -- Ensures that if a recruiter's user account is deleted, all their job postings are also removed.
            FOREIGN KEY (recruiter_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    tables['applications'] = (
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for each application
            job_id INT NOT NULL, -- Foreign key linking to the job being applied for
            jobseeker_id INT NOT NULL, -- Foreign key linking to the jobseeker applying
            application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp of application submission
            status ENUM('pending', 'reviewed', 'shortlisted', 'rejected') DEFAULT 'pending', -- Current status of the application
            -- If a job or a jobseeker is deleted, their applications are also removed.
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
            FOREIGN KEY (jobseeker_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    tables['job_preferences'] = (
        """
        CREATE TABLE IF NOT EXISTS job_preferences (
            id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for each preference set
            user_id INT NOT NULL UNIQUE, -- Foreign key linking to the user, ensuring one preference set per user
            preferred_role VARCHAR(255), -- Jobseeker's preferred job role
            preferred_industry VARCHAR(255), -- Jobseeker's preferred industry
            work_mode VARCHAR(50), -- Preferred work mode (e.g., 'Remote', 'On-site', 'Hybrid')
            job_type VARCHAR(50), -- Preferred job type (e.g., 'Full-time', 'Contract')
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    tables['shortlisted_candidates'] = (
        """
        CREATE TABLE IF NOT EXISTS shortlisted_candidates (
            id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for each shortlist entry
            recruiter_id INT NOT NULL, -- Foreign key linking to the recruiter
            candidate_id INT NOT NULL, -- Foreign key linking to the shortlisted candidate (a user)
            job_id INT, -- Optional: Foreign key to link a shortlist to a specific job posting
            notes TEXT, -- Recruiter's private notes about the candidate
            status VARCHAR(50), -- Status of the candidate in the hiring process (e.g., 'Contacted', 'Interviewing')
            shortlisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp of when the candidate was shortlisted
            -- Prevents a recruiter from shortlisting the same candidate for the same job multiple times.
            UNIQUE (recruiter_id, candidate_id, job_id),
            FOREIGN KEY (recruiter_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (candidate_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
        """
    )

    tables['resume_files'] = (
        """
        CREATE TABLE IF NOT EXISTS resume_files (
            id INT AUTO_INCREMENT PRIMARY KEY, -- Unique identifier for the resume file
            user_id INT NOT NULL, -- Foreign key linking to the user who uploaded the resume
            original_filename VARCHAR(255) NOT NULL, -- The original name of the uploaded file
            stored_filename VARCHAR(255) NOT NULL, -- The name of the file as stored on the server (can be different to avoid conflicts)
            file_path VARCHAR(255) NOT NULL, -- The absolute path to the stored file
            file_size INT, -- The size of the file in bytes
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp of when the file was uploaded
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    # --- Execute Table Creation ---
    for table_name, table_sql in tables.items():
        try:
            print(f"Creating table '{table_name}'...")
            cursor.execute(table_sql)
            conn.commit()
            print(f"Table '{table_name}' created or already exists.")
        except mysql.connector.Error as err:
            print(f"Error creating table '{table_name}': {err}")

    cursor.close()
    conn.close()

# Note: The following search functions are basic and can be expanded.
# They are kept separate from the core API logic for better separation of concerns.

def search_jobs(location=None, salary=None, experience=None, skills=None, job_type=None):
    """
    Searches for jobs in the database based on a variety of criteria.

    Args:
        location (str, optional): The desired job location.
        salary (int, optional): The desired minimum salary.
        experience (str, optional): The desired experience level.
        skills (list, optional): A list of required skills.
        job_type (str, optional): The type of employment.

    Returns:
        list: A list of job records matching the search criteria.
    """
    conn = create_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM jobs WHERE 1=1" # Start with a true condition to easily append more
    params = []

    # Dynamically build the query based on provided filters
    if location:
        query += " AND location LIKE %s"
        params.append(f"%{location}%")
    if salary:
        query += " AND (minSalary >= %s OR maxSalary >= %s)"
        params.extend([salary, salary])
    if experience:
        # TODO: Implement a more robust experience search (e.g., parsing numerical years)
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
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error searching jobs: {err}")
        return []
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    # This block allows for direct execution of the script to initialize the database.
    # Usage: python -m backend.db.mysql_db
    print("Initializing database schema...")
    create_tables()
    print("Database initialization complete.")

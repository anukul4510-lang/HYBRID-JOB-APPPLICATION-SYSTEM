"""
File: user_queries.py
Purpose: Contains all database query functions related to user management,
         such as creating users, retrieving user data, and updating profiles.
         This keeps user-specific SQL logic separate from the main application logic.

Author: [Your Name]
Date: 26/09/2025

"""

import mysql.connector
from typing import Optional, Dict, Any
import os
import sys

# Add the project root to the Python path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.models.models import RegisterUser, JobseekerProfile
from backend.core.security import get_password_hash


def get_user_by_email(conn: mysql.connector.connection.MySQLConnection, email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a user's full record from the database by their email address.

    Args:
        conn: The active database connection object.
        email (str): The email of the user to find.

    Returns:
        Optional[Dict[str, Any]]: A dictionary representing the user if found, otherwise None.
    """
    try:
        # Using a dictionary cursor to get results as key-value pairs
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        cursor.close()
        return user
    except mysql.connector.Error as err:
        print(f"Error finding user by email: {err}")
        return None

def create_user(conn: mysql.connector.connection.MySQLConnection, user: RegisterUser) -> Optional[int]:
    """
    Creates a new user in the database.

    This function takes a RegisterUser object, hashes the password, and inserts
    the new user record into the 'users' table.

    Args:
        conn: The active database connection object.
        user (RegisterUser): A Pydantic model containing the new user's details.

    Returns:
        Optional[int]: The ID of the newly created user if successful, otherwise None.
    """
    try:
        cursor = conn.cursor()
        # Hash the password before storing it in the database
        hashed_password = get_password_hash(user.password)

        insert_query = """
            INSERT INTO users (email, password, user_type, name, phone, company)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        user_data = (
            user.email,
            hashed_password,
            user.userType,
            user.name,
            user.phone,
            user.company
        )
        cursor.execute(insert_query, user_data)
        conn.commit()
        user_id = cursor.lastrowid  # Get the ID of the newly inserted user
        cursor.close()
        return user_id
    except mysql.connector.Error as err:
        print(f"Error creating user: {err}")
        conn.rollback()  # Roll back the transaction on error
        return None

def get_jobseeker_profile_by_email(conn: mysql.connector.connection.MySQLConnection, email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a jobseeker's public profile from the database by their email address.

    Args:
        conn: The database connection object.
        email (str): The email of the user to find.

    Returns:
        Optional[Dict[str, Any]]: A dictionary representing the user profile if found, otherwise None.
    """
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT name, phone, location, experience_level, education, skills FROM users WHERE email = %s AND user_type = 'jobseeker'"
        cursor.execute(query, (email,))
        profile = cursor.fetchone()
        cursor.close()
        return profile
    except mysql.connector.Error as err:
        print(f"Error finding user by email: {err}")
        return None

def update_jobseeker_profile(conn: mysql.connector.connection.MySQLConnection, email: str, profile: JobseekerProfile) -> bool:
    """
    Updates a jobseeker's profile in the database.

    Args:
        conn: The database connection object.
        email (str): The email of the user whose profile is to be updated.
        profile (JobseekerProfile): The new profile data.

    Returns:
        bool: True if the update was successful (at least one row affected), False otherwise.
    """
    try:
        cursor = conn.cursor()
        update_query = """
            UPDATE users
            SET name = %s, phone = %s, location = %s, experience_level = %s, education = %s
            WHERE email = %s AND user_type = 'jobseeker'
        """
        cursor.execute(update_query, (profile.name, profile.phone, profile.location, profile.experience_level, profile.education, email))
        conn.commit()
        # Check if any rows were actually updated
        success = cursor.rowcount > 0
        cursor.close()
        return success
    except mysql.connector.Error as err:
        print(f"Error updating user profile: {err}")
        conn.rollback()
        return False

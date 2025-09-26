"""
File: main.py
Purpose: Main FastAPI application file for the Job Portal.
         This file defines all the API endpoints, handles request validation,
         and orchestrates the application's business logic.

Author: [Your Name]
Date: 26/09/2025

Dependencies:
- fastapi
- uvicorn
- python-jose[cryptography]
- passlib[bcrypt]
- python-multipart
- mysql-connector-python
- chromadb
- google-generativeai

"""

# Standard library imports
import os
import sys
import json
import shutil
from datetime import datetime
from typing import List, Optional

# Third-party imports
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Add the project root to the Python path to allow for absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Local application imports
from backend.core.security import get_current_user, create_access_token, get_password_hash, verify_password, verify_token
from backend.db.mysql_db import create_tables, get_db_connection
from backend.db.user_queries import get_user_by_email, create_user
from backend.services.search_engine import search
from backend.services.vector_service import add_to_collection, candidate_profiles_collection, job_descriptions_collection
from backend.models.models import (
    LoginUser,
    RegisterUser,
    Job,
    Application,
    JobPreferences,
    Shortlist,
    ShortlistUpdate,
    JobseekerProfile,
    JobseekerSkills,
    JobSearch,
    SearchQuery,
    ApplicationStatusUpdate,
)

# --- Database Initialization ---
# Initialize database tables on startup if they don't exist
create_tables()

# --- Global Configuration ---
# Directory to store uploaded resumes
RESUME_DIR = "resumes"
if not os.path.exists(RESUME_DIR):
    os.makedirs(RESUME_DIR)

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Job Portal API",
    description="API for a comprehensive job portal with AI-powered search.",
    version="1.0.0",
)

# --- CORS (Cross-Origin Resource Sharing) Middleware ---
# Allow all origins for development purposes.
# For production, it's recommended to restrict this to the frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# --- 1. Authentication Endpoints ---
# ==============================================================================

@app.post("/login", tags=["Authentication"])
async def login(user: LoginUser, conn=Depends(get_db_connection)):
    """
    Authenticates a user and returns a JWT access token.

    This endpoint validates the user's credentials and, upon success,
    generates a JWT token for authenticating subsequent requests.

    Args:
        user (LoginUser): A Pydantic model containing:
            - **userEmail**: The user's email address.
            - **password**: The user's password.
            - **userType**: The type of user ('jobseeker' or 'recruiter').
        conn: A database connection dependency.

    Returns:
        JSONResponse: A dictionary containing:
            - **success**: A boolean indicating the outcome.
            - **token**: The JWT access token.
            - **user**: A dictionary with user details.

    Raises:
        HTTPException:
            - 401: If authentication fails (user not found, wrong password, or incorrect user type).
            - 500: For any other server-side errors.
    """
    try:
        # Retrieve user from the database by email
        found_user = get_user_by_email(conn, user.userEmail)

        # Validate user existence and type
        if not found_user or found_user['user_type'] != user.userType:
            raise HTTPException(
                status_code=401,
                detail="User not found or incorrect user type"
            )

        # Verify the provided password against the stored hash
        if not verify_password(user.password, found_user['hashed_password']):
            raise HTTPException(
                status_code=401,
                detail="Invalid password"
            )

        # Create a JWT access token
        access_token = create_access_token(
            data={"user_email": user.userEmail, "user_type": user.userType, "user_id": found_user['id']}
        )

        # Prepare user data for the response (excluding the password hash)
        user_data = {k: v for k, v in found_user.items() if k != 'hashed_password'}

        return JSONResponse(content={
            "success": True,
            "token": access_token,
            "user": {
                **user_data,
                "type": user.userType
            }
        })
    except Exception as e:
        # Generic error handler for unexpected issues
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/register", tags=["Authentication"])
async def register(user: RegisterUser, conn=Depends(get_db_connection)):
    """
    Registers a new user (jobseeker or recruiter).

    This endpoint creates a new user account, hashes the password for security,
    and for jobseekers, adds their profile to a vector database for semantic search.

    Args:
        user (RegisterUser): A Pydantic model with new user details.
        conn: A database connection dependency.

    Returns:
        JSONResponse: A dictionary containing a success message, a new JWT token,
                      and basic user information.

    Raises:
        HTTPException:
            - 400: If a user with the same email already exists.
            - 500: For any other server-side errors.
    """
    try:
        # Check if a user with the given email already exists
        existing_user = get_user_by_email(conn, user.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )

        # Create the new user in the database
        user_id = create_user(conn, user)

        # If the user is a jobseeker, add their basic profile to ChromaDB
        if user.userType == 'jobseeker':
            profile_text = f"Name: {user.name}, Phone: {user.phone}, Email: {user.email}"
            add_to_collection(candidate_profiles_collection, str(user_id), profile_text)

        # Generate a JWT token for the newly registered user
        token = create_access_token({"user_email": user.email, "user_type": user.userType, "user_id": user_id})

        return JSONResponse(content={
            "success": True,
            "message": "Registration successful",
            "token": token,
            "user": {
                "email": user.email,
                "type": user.userType
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/verify-token", tags=["Authentication"])
async def verify_token_endpoint(authorization: str = Header(None)):
    """
    Verifies a JWT token from the Authorization header.

    This endpoint is used by the frontend to confirm a user's login status
    without needing to send credentials again.

    Args:
        authorization (str): The 'Authorization' header string (e.g., "Bearer <token>").

    Returns:
        JSONResponse: A dictionary with success status and decoded user details.

    Raises:
        HTTPException:
            - 401: If the token is missing, malformed, or invalid.
            - 500: For any other server-side errors.
    """
    try:
        # Ensure the Authorization header is present and correctly formatted
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Token is required")

        # Extract the token from the header
        token = authorization.replace('Bearer ', '')

        # Verify the token's validity
        decoded = await verify_token(token)

        return JSONResponse(content={
            "success": True,
            "user_email": decoded["user_email"],
            "user_type": decoded["user_type"]
        })
    except HTTPException as he:
        # Re-raise HTTPExceptions to preserve status codes
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# --- 2. Jobseeker Endpoints ---
# ==============================================================================

@app.get("/jobseeker/dashboard", tags=["Jobseeker"])
async def get_jobseeker_dashboard(current_user: dict = Depends(get_current_user), conn=Depends(get_db_connection)):
    """
    Fetches dashboard data for a logged-in jobseeker.

    Provides essential user information and a list of recommended jobs.

    Args:
        current_user (dict): The authenticated user's data from the JWT token.
        conn: A database connection dependency.

    Returns:
        JSONResponse: A dictionary containing user data and job recommendations.

    Raises:
        HTTPException:
            - 403: If the user is not a jobseeker.
            - 404: If the user's profile is not found in the database.
            - 500: For internal server errors.
    """
    try:
        # Authorization check
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied. Not a jobseeker account.")

        cursor = conn.cursor(dictionary=True)

        # Fetch user details
        query = "SELECT * FROM users WHERE email = %s AND user_type = 'jobseeker'"
        cursor.execute(query, (current_user["user_email"],))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            raise HTTPException(status_code=404, detail="User not found.")

        # Exclude password from the response
        user_data = {k: v for k, v in user.items() if k != 'hashed_password'}

        # Fetch job recommendations (currently latest 10 jobs)
        # TODO: Implement a more sophisticated recommendation logic
        recommendations_query = "SELECT * FROM jobs ORDER BY created_at DESC LIMIT 10"
        cursor.execute(recommendations_query)
        recommended_jobs = cursor.fetchall()
        cursor.close()

        return JSONResponse(content={
            "success": True,
            "user": user_data,
            "recommended_jobs": recommended_jobs
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/jobseeker/profile", tags=["Jobseeker"])
async def get_jobseeker_profile(current_user: dict = Depends(get_current_user), conn=Depends(get_db_connection)):
    """
    Retrieves the profile of the currently logged-in jobseeker.

    Args:
        current_user (dict): The authenticated user's data.
        conn: A database connection dependency.

    Returns:
        JSONResponse: A dictionary containing the jobseeker's profile information.
    """
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor(dictionary=True)
        query = "SELECT name, phone, location, experience_level, education, skills FROM users WHERE email = %s"
        cursor.execute(query, (current_user["user_email"],))
        profile = cursor.fetchone()
        cursor.close()

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Skills are stored as a JSON string; parse them into a list
        if profile.get('skills'):
            profile['skills'] = json.loads(profile['skills'])

        return JSONResponse(content={"success": True, "profile": profile})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/jobseeker/profile", tags=["Jobseeker"])
async def update_jobseeker_profile(profile: JobseekerProfile, current_user: dict = Depends(get_current_user), conn=Depends(get_db_connection)):
    """
    Updates the profile of the currently logged-in jobseeker.

    Also updates the corresponding user profile in the ChromaDB vector store
    to ensure search results remain accurate.

    Args:
        profile (JobseekerProfile): A Pydantic model with the updated profile data.
        current_user (dict): The authenticated user's data.
        conn: A database connection dependency.

    Returns:
        JSONResponse: A success message.
    """
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor(dictionary=True)
        update_query = """
            UPDATE users
            SET name = %s, phone = %s, location = %s, experience_level = %s, education = %s
            WHERE email = %s
        """
        cursor.execute(update_query, (profile.name, profile.phone, profile.location, profile.experience_level, profile.education, current_user["user_email"]))
        conn.commit()

        # Update the user's profile in ChromaDB for semantic search
        user_data = get_user_by_email(conn, current_user["user_email"])
        user_id = user_data['id']
        skills = json.loads(user_data['skills']) if user_data.get('skills') else []
        profile_text = f"Name: {profile.name}, Phone: {profile.phone}, Location: {profile.location}, Experience: {profile.experience_level}, Education: {profile.education}, Skills: {', '.join(skills)}"
        add_to_collection(candidate_profiles_collection, str(user_id), profile_text)

        cursor.close()

        return JSONResponse(content={"success": True, "message": "Profile updated successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/jobseeker/skills", tags=["Jobseeker"])
async def update_jobseeker_skills(skills: JobseekerSkills, current_user: dict = Depends(get_current_user), conn=Depends(get_db_connection)):
    """
    Updates the skills for the currently logged-in jobseeker.

    This also updates the ChromaDB vector store to reflect the new skills.

    Args:
        skills (JobseekerSkills): A Pydantic model containing a list of skills.
        current_user (dict): The authenticated user's data.
        conn: A database connection dependency.

    Returns:
        JSONResponse: A success message.
    """
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor(dictionary=True)
        # Skills are stored as a JSON string in the database
        skills_json = json.dumps(skills.skills)
        update_query = "UPDATE users SET skills = %s WHERE email = %s"
        cursor.execute(update_query, (skills_json, current_user["user_email"]))
        conn.commit()

        # Update ChromaDB with the new skills
        user_data = get_user_by_email(conn, current_user["user_email"])
        user_id = user_data['id']
        profile_text = f"Name: {user_data['name']}, Phone: {user_data['phone']}, Location: {user_data['location']}, Experience: {user_data['experience_level']}, Education: {user_data['education']}, Skills: {', '.join(skills.skills)}"
        add_to_collection(candidate_profiles_collection, str(user_id), profile_text)

        cursor.close()

        return JSONResponse(content={"success": True, "message": "Skills updated successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/jobseeker/resume", tags=["Jobseeker"])
async def upload_resume(file: UploadFile = File(...), current_user: dict = Depends(get_current_user), conn=Depends(get_db_connection)):
    """
    Uploads a resume file for the jobseeker.

    The file is saved to the server, and its metadata is stored in the database.

    Args:
        file (UploadFile): The resume file to upload.
        current_user (dict): The authenticated user's data.
        conn: A database connection dependency.

    Returns:
        JSONResponse: A success message.
    """
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        file_location = os.path.join(RESUME_DIR, file.filename)
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        cursor = conn.cursor()
        insert_query = """
            INSERT INTO resume_files (user_id, original_filename, stored_filename, file_path, file_size)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (current_user["user_id"], file.filename, file.filename, file_location, file.size))
        conn.commit()
        cursor.close()

        return JSONResponse(content={"success": True, "message": "Resume uploaded successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobseeker/resume", tags=["Jobseeker"])
async def get_resume(current_user: dict = Depends(get_current_user), conn=Depends(get_db_connection)):
    """
    Downloads the jobseeker's most recently uploaded resume.

    Args:
        current_user (dict): The authenticated user's data.
        conn: A database connection dependency.

    Returns:
        FileResponse: The resume file.
    """
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM resume_files WHERE user_id = %s ORDER BY uploaded_at DESC LIMIT 1"
        cursor.execute(query, (current_user["user_id"],))
        resume_file = cursor.fetchone()
        cursor.close()

        if not resume_file:
            raise HTTPException(status_code=404, detail="Resume not found")

        file_path = resume_file['file_path']
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Resume file not found on server")

        return FileResponse(path=file_path, filename=resume_file['original_filename'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/jobseeker/apply", tags=["Jobseeker"])
async def apply_for_job(application: Application, current_user: dict = Depends(get_current_user), conn=Depends(get_db_connection)):
    """
    Allows a jobseeker to apply for a job.

    Checks for duplicate applications and ensures the job exists.

    Args:
        application (Application): A Pydantic model containing the job_id.
        current_user (dict): The authenticated user's data.
        conn: A database connection dependency.

    Returns:
        JSONResponse: A success message.
    """
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor(dictionary=True)

        # Check if the job exists
        cursor.execute("SELECT id FROM jobs WHERE id = %s", (application.job_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Job not found")

        # Check if the user has already applied
        cursor.execute("SELECT id FROM applications WHERE job_id = %s AND jobseeker_id = %s", (application.job_id, current_user["user_id"]))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="You have already applied for this job")

        # Insert the new application
        insert_query = "INSERT INTO applications (job_id, jobseeker_id, application_date) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (application.job_id, current_user["user_id"], datetime.utcnow()))
        conn.commit()
        cursor.close()

        return JSONResponse(content={"success": True, "message": "Application submitted successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobseeker/applications", tags=["Jobseeker"])
async def get_jobseeker_applications(current_user: dict = Depends(get_current_user), conn=Depends(get_db_connection)):
    """
    Retrieves all job applications submitted by the current jobseeker.

    Args:
        current_user (dict): The authenticated user's data.
        conn: A database connection dependency.

    Returns:
        JSONResponse: A list of the jobseeker's applications.
    """
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT a.*, j.title, j.location, j.employmentType
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.jobseeker_id = %s
        """
        cursor.execute(query, (current_user["user_id"],))
        applications = cursor.fetchall()
        cursor.close()

        return JSONResponse(content={"success": True, "applications": applications})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# --- 3. Recruiter Endpoints ---
# ==============================================================================

@app.get("/recruiter/dashboard", tags=["Recruiter"])
async def get_recruiter_dashboard(current_user: dict = Depends(get_current_user), conn=Depends(get_db_connection)):
    """
    Fetches dashboard data for a logged-in recruiter.

    Args:
        current_user (dict): The authenticated user's data.
        conn: A database connection dependency.

    Returns:
        JSONResponse: A dictionary containing the recruiter's user data.
    """
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")

        user_data = get_user_by_email(conn, current_user["user_email"])
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        # Remove password hash from the response
        user_data.pop('hashed_password', None)

        return JSONResponse(content={"success": True, "user": user_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recruiter/jobs", tags=["Recruiter"])
async def post_job(
    title: str = Form(...),
    location: str = Form(...),
    employmentType: str = Form(...),
    description: str = Form(...),
    skills: str = Form(...),
    minSalary: int = Form(...),
    maxSalary: int = Form(...),
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db_connection)
):
    """
    Allows a recruiter to post a new job.

    The job details are stored in the database, and a document representing
    the job is added to the ChromaDB vector store for semantic search.

    Args:
        title (str): The job title.
        location (str): The job location.
        employmentType (str): The type of employment (e.g., 'Full-time').
        description (str): A detailed job description.
        skills (str): A JSON stringified list of required skills.
        minSalary (int): The minimum salary for the position.
        maxSalary (int): The maximum salary for the position.
        current_user (dict): The authenticated recruiter's data.
        conn: A database connection dependency.

    Returns:
        JSONResponse: A success message.
    """
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor()
        skills_list = json.loads(skills)
        skills_str = ",".join(skills_list)

        insert_query = """
            INSERT INTO jobs (recruiter_id, title, location, employmentType, description, skills, minSalary, maxSalary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (current_user["user_id"], title, location, employmentType, description, skills_str, minSalary, maxSalary))
        conn.commit()
        job_id = cursor.lastrowid

        # Add job description to ChromaDB for semantic search
        job_text = f"Title: {title}, Location: {location}, Description: {description}, Skills: {skills_str}"
        add_to_collection(job_descriptions_collection, str(job_id), job_text)

        cursor.close()

        return JSONResponse(content={"success": True, "message": "Job posted successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recruiter/jobs", tags=["Recruiter"])
async def get_recruiter_jobs(current_user: dict = Depends(get_current_user), conn=Depends(get_db_connection)):
    """
    Retrieves all jobs posted by the currently logged-in recruiter.

    Args:
        current_user (dict): The authenticated recruiter's data.
        conn: A database connection dependency.

    Returns:
        JSONResponse: A list of jobs posted by the recruiter.
    """
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM jobs WHERE recruiter_id = %s"
        cursor.execute(query, (current_user["user_id"],))
        jobs = cursor.fetchall()
        cursor.close()

        return JSONResponse(content={"success": True, "jobs": jobs})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/recruiter/jobs/{job_id}", tags=["Recruiter"])
async def update_recruiter_job(job_id: int, job: Job, current_user: dict = Depends(get_current_user), conn=Depends(get_db_connection)):
    """
    Updates a job posting.

    Also updates the job's document in the ChromaDB vector store.

    Args:
        job_id (int): The ID of the job to update.
        job (Job): A Pydantic model with the updated job data.
        current_user (dict): The authenticated recruiter's data.
        conn: A database connection dependency.

    Returns:
        JSONResponse: A success message.
    """
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor()
        skills_str = ",".join(job.skills)
        update_query = """
            UPDATE jobs
            SET title = %s, location = %s, employmentType = %s, description = %s, skills = %s, minSalary = %s, maxSalary = %s
            WHERE id = %s AND recruiter_id = %s
        """
        cursor.execute(update_query, (job.title, job.location, job.employmentType, job.description, skills_str, job.minSalary, job.maxSalary, job_id, current_user["user_id"]))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Job not found or you don't have permission to update it")

        # Update job description in ChromaDB
        job_text = f"Title: {job.title}, Location: {job.location}, Description: {job.description}, Skills: {skills_str}"
        add_to_collection(job_descriptions_collection, str(job_id), job_text)

        cursor.close()

        return JSONResponse(content={"success": True, "message": "Job updated successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/recruiter/jobs/{job_id}", tags=["Recruiter"])
async def delete_recruiter_job(job_id: int, current_user: dict = Depends(get_current_user), conn=Depends(get_db_connection)):
    """
    Deletes a job posting.

    Args:
        job_id (int): The ID of the job to delete.
        current_user (dict): The authenticated recruiter's data.
        conn: A database connection dependency.

    Returns:
        JSONResponse: A success message.
    """
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor()
        # TODO: Also delete the job from the ChromaDB collection.
        delete_query = "DELETE FROM jobs WHERE id = %s AND recruiter_id = %s"
        cursor.execute(delete_query, (job_id, current_user["user_id"]))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Job not found or you don't have permission to delete it")

        cursor.close()
        return JSONResponse(content={"success": True, "message": "Job deleted successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recruiter/applications", tags=["Recruiter"])
async def get_recruiter_applications(current_user: dict = Depends(get_current_user), conn=Depends(get_db_connection)):
    """
    Retrieves all applications for jobs posted by the current recruiter.

    Args:
        current_user (dict): The authenticated recruiter's data.
        conn: A database connection dependency.

    Returns:
        JSONResponse: A list of applications.
    """
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT a.*, j.title, u.name, u.email, u.phone
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN users u ON a.jobseeker_id = u.id
            WHERE j.recruiter_id = %s
        """
        cursor.execute(query, (current_user["user_id"],))
        applications = cursor.fetchall()
        cursor.close()

        return JSONResponse(content={"success": True, "applications": applications})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/recruiter/applications/{application_id}/status", tags=["Recruiter"])
async def update_application_status(application_id: int, status_update: ApplicationStatusUpdate, current_user: dict = Depends(get_current_user), conn=Depends(get_db_connection)):
    """
    Updates the status of a job application (e.g., 'Reviewed', 'Rejected').

    Args:
        application_id (int): The ID of the application to update.
        status_update (ApplicationStatusUpdate): A Pydantic model with the new status.
        current_user (dict): The authenticated recruiter's data.
        conn: A database connection dependency.

    Returns:
        JSONResponse: A success message.
    """
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor()

        # Verify that the application belongs to a job posted by this recruiter
        verify_query = """
            SELECT a.id
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.id = %s AND j.recruiter_id = %s
        """
        cursor.execute(verify_query, (application_id, current_user["user_id"]))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Application not found or you don't have permission to update it")

        # Update the application status
        update_query = "UPDATE applications SET status = %s WHERE id = %s"
        cursor.execute(update_query, (status_update.status, application_id))
        conn.commit()
        cursor.close()

        return JSONResponse(content={"success": True, "message": "Application status updated successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# --- 4. Search Endpoints ---
# ==============================================================================

@app.post("/search/jobs", tags=["Search"])
async def search_jobs_endpoint(query: SearchQuery, current_user: dict = Depends(get_current_user)):
    """
    Performs an AI-powered search for jobs.

    This endpoint is intended for jobseekers.

    Args:
        query (SearchQuery): A Pydantic model containing the search query string.
        current_user (dict): The authenticated user's data.

    Returns:
        JSONResponse: A list of job search results.
    """
    if current_user["user_type"] != "jobseeker":
        raise HTTPException(status_code=403, detail="Access denied")

    results = search(query.query, search_type="jobs")
    return JSONResponse(content={"success": True, "results": results})


@app.post("/search/candidates", tags=["Search"])
async def search_candidates_endpoint(query: SearchQuery, current_user: dict = Depends(get_current_user)):
    """
    Performs an AI-powered search for candidates.

    This endpoint is intended for recruiters.

    Args:
        query (SearchQuery): A Pydantic model containing the search query string.
        current_user (dict): The authenticated user's data.

    Returns:
        JSONResponse: A list of candidate search results.
    """
    if current_user["user_type"] != "recruiter":
        raise HTTPException(status_code=403, detail="Access denied")

    results = search(query.query, search_type="candidates")
    return JSONResponse(content={"success": True, "results": results})


# ==============================================================================
# --- Application Runner ---
# ==============================================================================

if __name__ == "__main__":
    """
    Main entry point for running the FastAPI application.
    Uses uvicorn as the ASGI server.
    """
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
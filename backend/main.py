from fastapi import FastAPI, HTTPException, Depends, Header, File, UploadFile, Form
from pydantic import BaseModel, Field
from typing import Optional, List
import shutil
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import uvicorn
import json
import os

from .mysql_db import create_tables

create_tables()

RESUME_DIR = "resumes"
if not os.path.exists(RESUME_DIR):
    os.makedirs(RESUME_DIR)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security configuration
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# User models
class LoginUser(BaseModel):
    userEmail: str
    password: str
    userType: str

class RegisterUser(BaseModel):
    email: str
    password: str
    userType: str
    name: str = None
    phone: str = None
    company: str = None

class Job(BaseModel):
    title: str
    location: str
    employmentType: str
    description: str
    skills: list
    minSalary: str
    maxSalary: str

class Application(BaseModel):
    job_id: int

class JobPreferences(BaseModel):
    preferred_role: str
    preferred_industry: str
    work_mode: str
    job_type: str

class Shortlist(BaseModel):
    candidate_id: int

class ShortlistUpdate(BaseModel):
    notes: Optional[str] = None
    status: Optional[str] = None

class JobseekerProfile(BaseModel):
    name: str
    phone: str
    location: str
    experience_level: str
    education: str

class JobseekerSkills(BaseModel):
    skills: list[str]

class JobSearch(BaseModel):
    keyword: Optional[str] = None
    location: Optional[str] = None
    employmentType: Optional[str] = None
    minSalary: Optional[int] = None
    maxSalary: Optional[int] = None

class SearchQuery(BaseModel):
    query: str

from .mysql_db import create_connection
from .search_engine import search
from .vector_service import add_to_collection, candidate_profiles_collection, job_descriptions_collection

# Dependency to get a database connection
def get_db_connection():
    conn = create_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        yield conn
    finally:
        conn.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("user_email")
        user_type: str = payload.get("user_type")
        user_id: int = payload.get("user_id")
        if user_email is None or user_type is None or user_id is None:
            raise credentials_exception
        return {"user_email": user_email, "user_type": user_type, "user_id": user_id}
    except JWTError:
        raise credentials_exception

@app.post("/login")
async def login(user: LoginUser, conn = Depends(get_db_connection)):
    try:
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query, (user.userEmail,))
        found_user = cursor.fetchone()
        cursor.close()

        if not found_user or found_user['user_type'] != user.userType:
            return JSONResponse(
                status_code=401,
                content={"detail": "User not found or incorrect user type"}
            )

        if not verify_password(user.password, found_user['hashed_password']):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid password"}
            )

        access_token = create_access_token(
            data={"user_email": user.userEmail, "user_type": user.userType, "user_id": found_user['id']}
        )
        
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
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/register")
async def register(user: RegisterUser, conn = Depends(get_db_connection)):
    try:
        cursor = conn.cursor()
        
        query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query, (user.email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            return JSONResponse(
                status_code=400,
                content={"detail": "User already exists"}
            )

        hashed_password = get_password_hash(user.password)

        insert_query = "INSERT INTO users (email, hashed_password, name, phone, company, user_type) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (user.email, hashed_password, user.name, user.phone, user.company, user.userType))
        
        conn.commit()
        user_id = cursor.lastrowid
        
        if user.userType == 'jobseeker':
            # Add user profile to ChromaDB
            profile_text = f"Name: {user.name}, Phone: {user.phone}, Email: {user.email}"
            add_to_collection(candidate_profiles_collection, str(user_id), profile_text)

        cursor.close()

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

@app.get("/verify-token")
async def verify_token_endpoint(authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Token is required")

        token = authorization.replace('Bearer ', '')
        # Use await since verify_token is async
        decoded = await verify_token(token)
        
        return JSONResponse(content={
            "success": True,
            "user_email": decoded["user_email"],
            "user_type": decoded["user_type"]
        })

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard endpoints
@app.get("/jobseeker/dashboard")
async def get_jobseeker_dashboard(current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied. Not a jobseeker account.")
            
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE email = %s AND user_type = 'jobseeker'"
        cursor.execute(query, (current_user["user_email"],))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            return JSONResponse(
                status_code=404,
                content={
                    "detail": "User not found in database. Please re-register.",
                    "error_code": "USER_NOT_FOUND",
                    "user_email": current_user["user_email"],
                    "user_type": current_user["user_type"]
                }
            )
        
        user_data = {k: v for k, v in user.items() if k != 'password'}

        # Job Recommendations
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

@app.get("/jobseeker/profile")
async def get_jobseeker_profile(current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
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

        # Skills are stored as a JSON string in the database, so we need to parse it
        if profile['skills']:
            profile['skills'] = json.loads(profile['skills'])

        return JSONResponse(content={"success": True, "profile": profile})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/jobseeker/profile")
async def update_jobseeker_profile(profile: JobseekerProfile, current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor()
        update_query = """
            UPDATE users
            SET name = %s, phone = %s, location = %s, experience_level = %s, education = %s
            WHERE email = %s
        """
        cursor.execute(update_query, (profile.name, profile.phone, profile.location, profile.experience_level, profile.education, current_user["user_email"]))
        conn.commit()
        
        # Update user profile in ChromaDB
        cursor.execute("SELECT id, skills FROM users WHERE email = %s", (current_user["user_email"],))
        user_data = cursor.fetchone()
        user_id = user_data[0]
        skills = json.loads(user_data[1]) if user_data[1] else []
        profile_text = f"Name: {profile.name}, Phone: {profile.phone}, Location: {profile.location}, Experience: {profile.experience_level}, Education: {profile.education}, Skills: {', '.join(skills)}"
        add_to_collection(candidate_profiles_collection, str(user_id), profile_text)

        cursor.close()

        return JSONResponse(content={"success": True, "message": "Profile updated successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/jobseeker/skills")
async def update_jobseeker_skills(skills: JobseekerSkills, current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor(dictionary=True)
        update_query = """
            UPDATE users
            SET skills = %s
            WHERE email = %s
        """
        cursor.execute(update_query, (json.dumps(skills.skills), current_user["user_email"]))
        conn.commit()

        # Update user profile in ChromaDB
        cursor.execute("SELECT id, name, phone, location, experience_level, education FROM users WHERE email = %s", (current_user["user_email"],))
        user_data = cursor.fetchone()
        user_id = user_data['id']
        profile_text = f"Name: {user_data['name']}, Phone: {user_data['phone']}, Location: {user_data['location']}, Experience: {user_data['experience_level']}, Education: {user_data['education']}, Skills: {', '.join(skills.skills)}"
        add_to_collection(candidate_profiles_collection, str(user_id), profile_text)

        cursor.close()

        return JSONResponse(content={"success": True, "message": "Skills updated successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/jobseeker/preferences")
async def update_jobseeker_preferences(preferences: JobPreferences, current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor()
        # Check if preferences already exist
        cursor.execute("SELECT * FROM job_preferences WHERE user_id = (SELECT id FROM users WHERE email = %s)", (current_user["user_email"],))
        existing_preferences = cursor.fetchone()

        if existing_preferences:
            update_query = """
                UPDATE job_preferences
                SET preferred_role = %s, preferred_industry = %s, work_mode = %s, job_type = %s
                WHERE user_id = (SELECT id FROM users WHERE email = %s)
            """
            cursor.execute(update_query, (preferences.preferred_role, preferences.preferred_industry, preferences.work_mode, preferences.job_type, current_user["user_email"]))
        else:
            insert_query = """
                INSERT INTO job_preferences (user_id, preferred_role, preferred_industry, work_mode, job_type)
                VALUES ((SELECT id FROM users WHERE email = %s), %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (current_user["user_email"], preferences.preferred_role, preferences.preferred_industry, preferences.work_mode, preferences.job_type))
        
        conn.commit()
        cursor.close()

        return JSONResponse(content={"success": True, "message": "Job preferences updated successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/jobseeker/resume")
async def upload_resume(file: UploadFile = File(...), current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        file_location = os.path.join(RESUME_DIR, file.filename)
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        
        cursor = conn.cursor()
        insert_query = """
            INSERT INTO resume_files (user_id, original_filename, stored_filename, file_path, file_size)
            VALUES ((SELECT id FROM users WHERE email = %s), %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (current_user["user_email"], file.filename, file.filename, file_location, file.size))
        conn.commit()
        cursor.close()

        return JSONResponse(content={"success": True, "message": "Resume uploaded successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobseeker/resume")
async def get_resume(current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
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

@app.get("/recruiter/dashboard")
async def get_recruiter_dashboard(current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")
            
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE email = %s AND user_type = 'recruiter'"
        cursor.execute(query, (current_user["user_email"],))
        user = cursor.fetchone()
        cursor.close()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        user_data = {k: v for k, v in user.items() if k != 'password'}
        return JSONResponse(content={
            "success": True,
            "user": user_data
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recruiter/jobs")
async def post_job(
    title: str = Form(...),
    location: str = Form(...),
    employmentType: str = Form(...),
    description: str = Form(...),
    skills: str = Form(...),
    minSalary: str = Form(...),
    maxSalary: str = Form(...),
    current_user: dict = Depends(verify_token), 
    conn = Depends(get_db_connection)
):
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")
        
        cursor = conn.cursor()
        insert_query = "INSERT INTO jobs (recruiter_id, title, location, employmentType, description, skills, minSalary, maxSalary) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        
        # The skills are sent as a JSON stringified array
        skills_list = json.loads(skills)
        skills_str = ",".join(skills_list)
        
        cursor.execute(insert_query, (current_user["user_id"], title, location, employmentType, description, skills_str, minSalary, maxSalary))
        conn.commit()
        job_id = cursor.lastrowid
        
        # Add job description to ChromaDB
        job_text = f"Title: {title}, Location: {location}, Description: {description}, Skills: {skills_str}"
        add_to_collection(job_descriptions_collection, str(job_id), job_text)

        cursor.close()
        
        return JSONResponse(content={"success": True, "message": "Job posted successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recruiter/jobs")
async def get_recruiter_jobs(current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
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

@app.put("/recruiter/jobs/{job_id}")
async def update_recruiter_job(job_id: int, job: Job, current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
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

@app.delete("/recruiter/jobs/{job_id}")
async def delete_recruiter_job(job_id: int, current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor()
        delete_query = "DELETE FROM jobs WHERE id = %s AND recruiter_id = %s"
        cursor.execute(delete_query, (job_id, current_user["user_id"]))
        conn.commit()
        cursor.close()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Job not found or you don't have permission to delete it")

        return JSONResponse(content={"success": True, "message": "Job deleted successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/search")
async def search_jobs(search: JobSearch, conn = Depends(get_db_connection)):
    try:
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []

        if search.keyword:
            query += " AND (title LIKE %s OR description LIKE %s)"
            params.extend([f"%{search.keyword}%", f"%{search.keyword}%"])
        
        if search.location:
            query += " AND location LIKE %s"
            params.append(f"%{search.location}%")

        if search.employmentType:
            query += " AND employmentType = %s"
            params.append(search.employmentType)

        if search.minSalary:
            query += " AND minSalary >= %s"
            params.append(search.minSalary)

        if search.maxSalary:
            query += " AND maxSalary <= %s"
            params.append(search.maxSalary)

        cursor.execute(query, tuple(params))
        jobs = cursor.fetchall()
        cursor.close()

        return JSONResponse(content={"success": True, "jobs": jobs})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recruiter/applications")
async def get_recruiter_applications(current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor(dictionary=True)
        recruiter_id = current_user["user_id"]

        query = """
            SELECT a.*, j.title, u.name, u.email, u.phone 
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN users u ON a.jobseeker_id = u.id
            WHERE j.recruiter_id = %s
        """
        cursor.execute(query, (recruiter_id,))
        applications = cursor.fetchall()
        cursor.close()

        return JSONResponse(content={"success": True, "applications": applications})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/jobseeker/apply")
async def apply_for_job(application: Application, current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor()

        # Check if the job exists
        cursor.execute("SELECT * FROM jobs WHERE id = %s", (application.job_id,))
        job = cursor.fetchone()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Check if the user has already applied
        cursor.execute("SELECT * FROM applications WHERE job_id = %s AND jobseeker_id = %s", (application.job_id, current_user["user_id"]))
        existing_application = cursor.fetchone()
        if existing_application:
            raise HTTPException(status_code=400, detail="You have already applied for this job")

        insert_query = "INSERT INTO applications (job_id, jobseeker_id, application_date) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (application.job_id, current_user["user_id"], datetime.utcnow()))
        conn.commit()
        cursor.close()

        return JSONResponse(content={"success": True, "message": "Application submitted successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobseeker/preferences")
async def get_job_preferences(current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM job_preferences WHERE jobseeker_id = %s"
        cursor.execute(query, (current_user["user_id"],))
        preferences = cursor.fetchone()
        cursor.close()

        return JSONResponse(content={"success": True, "preferences": preferences})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/jobseeker/preferences")
async def create_job_preferences(preferences: JobPreferences, current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor()
        insert_query = "INSERT INTO job_preferences (jobseeker_id, preferred_role, preferred_industry, work_mode, job_type) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (current_user["user_id"], preferences.preferred_role, preferences.preferred_industry, preferences.work_mode, preferences.job_type))
        conn.commit()
        cursor.close()

        return JSONResponse(content={"success": True, "message": "Job preferences created successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/jobseeker/preferences")
async def update_job_preferences(preferences: JobPreferences, current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor()
        update_query = "UPDATE job_preferences SET preferred_role = %s, preferred_industry = %s, work_mode = %s, job_type = %s WHERE jobseeker_id = %s"
        cursor.execute(update_query, (preferences.preferred_role, preferences.preferred_industry, preferences.work_mode, preferences.job_type, current_user["user_id"]))
        conn.commit()
        cursor.close()

        return JSONResponse(content={"success": True, "message": "Job preferences updated successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recruiter/shortlist")
async def get_shortlist(current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT u.id, u.name, u.email, u.phone
            FROM shortlisted_candidates sc
            JOIN users u ON sc.candidate_id = u.id
            WHERE sc.recruiter_id = %s
        """
        cursor.execute(query, (current_user["user_id"],))
        shortlist = cursor.fetchall()
        cursor.close()

        return JSONResponse(content={"success": True, "shortlist": shortlist})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recruiter/shortlist")
async def add_to_shortlist(shortlist: Shortlist, current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor()
        insert_query = "INSERT INTO shortlisted_candidates (recruiter_id, candidate_id) VALUES (%s, %s)"
        cursor.execute(insert_query, (current_user["user_id"], shortlist.candidate_id))
        conn.commit()
        cursor.close()

        return JSONResponse(content={"success": True, "message": "Candidate added to shortlist"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/recruiter/shortlist/{candidate_id}")
async def remove_from_shortlist(candidate_id: int, current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor()
        delete_query = "DELETE FROM shortlisted_candidates WHERE recruiter_id = %s AND candidate_id = %s"
        cursor.execute(delete_query, (current_user["user_id"], candidate_id))
        conn.commit()
        cursor.close()

        return JSONResponse(content={"success": True, "message": "Candidate removed from shortlist"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/recruiter/shortlist/{candidate_email}")
async def update_shortlist(candidate_email: str, update: ShortlistUpdate, current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor()

        # First, get the candidate_id from the email
        cursor.execute("SELECT id FROM users WHERE email = %s", (candidate_email,))
        candidate = cursor.fetchone()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        candidate_id = candidate[0]

        # Check if the candidate is in the recruiter's shortlist
        cursor.execute("SELECT * FROM shortlisted_candidates WHERE recruiter_id = %s AND candidate_id = %s", (current_user["user_id"], candidate_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Candidate not in shortlist")

        if update.notes is not None:
            update_query = "UPDATE shortlisted_candidates SET notes = %s WHERE recruiter_id = %s AND candidate_id = %s"
            cursor.execute(update_query, (update.notes, current_user["user_id"], candidate_id))

        if update.status is not None:
            update_query = "UPDATE shortlisted_candidates SET status = %s WHERE recruiter_id = %s AND candidate_id = %s"
            cursor.execute(update_query, (update.status, current_user["user_id"], candidate_id))

        conn.commit()
        cursor.close()

        return JSONResponse(content={"success": True, "message": "Shortlist updated successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobseeker/applications")
async def get_jobseeker_applications(current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT a.*, j.title, j.location, j.employmentType, j.description, j.minSalary, j.maxSalary
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

class ApplicationStatusUpdate(BaseModel):
    status: str

@app.put("/recruiter/applications/{application_id}/status")
async def update_application_status(application_id: int, status_update: ApplicationStatusUpdate, current_user: dict = Depends(verify_token), conn = Depends(get_db_connection)):
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

        update_query = "UPDATE applications SET status = %s WHERE id = %s"
        cursor.execute(update_query, (status_update.status, application_id))
        conn.commit()
        cursor.close()

        return JSONResponse(content={"success": True, "message": "Application status updated successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/jobs")
async def search_jobs_endpoint(query: SearchQuery, current_user: dict = Depends(verify_token)):
    if current_user["user_type"] != "jobseeker":
        raise HTTPException(status_code=403, detail="Access denied")
    
    results = search(query.query, search_type="jobs")
    return JSONResponse(content={"success": True, "results": results})

@app.post("/search/candidates")
async def search_candidates_endpoint(query: SearchQuery, current_user: dict = Depends(verify_token)):
    if current_user["user_type"] != "recruiter":
        raise HTTPException(status_code=403, detail="Access denied")

    results = search(query.query, search_type="candidates")
    return JSONResponse(content={"success": True, "results": results})

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


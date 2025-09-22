from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import uvicorn

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
    jobseeker_email: str
    application_date: str

# Import database functions
from .db import users_db, save_db, load_db

@app.get("/users")
async def get_users():
    return load_db()

@app.post("/reset-db")
async def reset_db():
    users_db['jobseekers'].clear()
    users_db['recruiters'].clear()
    users_db['jobs'].clear()
    users_db['applications'].clear()
    save_db(users_db)
    return {"message": "Database reset successfully"}

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
        print(f"Verifying token: {token[:10]}...")  # Print first 10 chars of token for debugging
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Decoded payload: {payload}")
        
        user_email: str = payload.get("user_email")
        user_type: str = payload.get("user_type")
        
        if user_email is None or user_type is None:
            print("Missing user_email or user_type in token")
            raise credentials_exception
            
        print(f"Token verified for {user_email} as {user_type}")
        return {"user_email": user_email, "user_type": user_type}
    except JWTError as e:
        print(f"JWT Error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        print(f"Unexpected error in verify_token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login(user: LoginUser):
    try:
        print(f"Login attempt for {user.userEmail} as {user.userType}")
        
        # Load latest database state
        current_db = load_db()
        print(f"Current users in DB: {current_db}")
        
        # Find user in appropriate database
        users = current_db['jobseekers'] if user.userType == 'jobseeker' else current_db['recruiters']
        found_user = next((u for u in users if u['email'] == user.userEmail), None)

        if not found_user:
            return JSONResponse(
                status_code=401,
                content={"detail": "User not found"}
            )

        if not verify_password(user.password, found_user['password']):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid password"}
            )

        access_token = create_access_token(
            data={"user_email": user.userEmail, "user_type": user.userType}
        )
        
        # Return user data without password
        user_data = {k: v for k, v in found_user.items() if k != 'password'}
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
async def register(user: RegisterUser):
    try:
        print(f"\n=== Registration Attempt ===")
        print(f"Email: {user.email}")
        print(f"Type: {user.userType}")
        print(f"Name: {user.name}")
        print(f"Has phone: {'Yes' if user.phone else 'No'}")
        print(f"Has company: {'Yes' if user.company else 'No'}")
        
        # Reload database to get latest state
        current_db = load_db()
        
        # Check if user already exists
        users = current_db['jobseekers'] if user.userType == 'jobseeker' else current_db['recruiters']
        existing_user = next((u for u in users if u['email'] == user.email), None)
        
        if existing_user:
            print(f"User already exists: {user.email}")
            return JSONResponse(
                status_code=400,
                content={"detail": "User already exists"}
            )

        # Hash the password
        print("Hashing password...")
        hashed_password = get_password_hash(user.password)

        # Create new user
        print("Creating new user record...")
        new_user = {
            "email": user.email,
            "password": hashed_password,
            "name": user.name,
            "phone": user.phone if user.userType == 'jobseeker' else None,
            "company": user.company if user.userType == 'recruiter' else None
        }
        
        # Add user to database
        users.append(new_user)
        save_db(current_db)
        print(f"New user added to database: {new_user['email']}")

        # Generate token
        print("Generating access token...")
        token = create_access_token({"user_email": user.email, "user_type": user.userType})
        print("Token generated successfully")

        print("Sending successful registration response")
        return JSONResponse(content={
            "success": True,
            "message": "Registration successful",
            "token": token,
            "user": {
                "email": user.email,
                "type": user.userType
            }
        })

    except HTTPException as he:
        raise he
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
async def get_jobseeker_dashboard(current_user: dict = Depends(verify_token)):
    try:
        print(f"\n=== Jobseeker Dashboard Access ===")
        print(f"Authenticated user: {current_user}")
        
        if current_user["user_type"] != "jobseeker":
            print(f"Access denied: User type is {current_user['user_type']}, expected jobseeker")
            raise HTTPException(status_code=403, detail="Access denied. Not a jobseeker account.")
            
        # Load latest database state
        current_db = load_db()
        print(f"Looking for user {current_user['user_email']} in database")
        print(f"Current jobseekers: {current_db['jobseekers']}")
        
        # Find user in database
        user = next((u for u in current_db['jobseekers'] if u['email'] == current_user["user_email"]), None)
        
        if not user:
            print(f"User not found in database: {current_user['user_email']}")
            # Return a more specific error that the frontend can handle
            return JSONResponse(
                status_code=404,
                content={
                    "detail": "User not found in database. Please re-register.",
                    "error_code": "USER_NOT_FOUND",
                    "user_email": current_user["user_email"],
                    "user_type": current_user["user_type"]
                }
            )
        
        print(f"Found user: {user['email']}")
        
        # Return user data without password
        user_data = {k: v for k, v in user.items() if k != 'password'}
        print(f"Returning user data: {user_data}")
        
        return JSONResponse(content={
            "success": True,
            "user": user_data
        })
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error in get_jobseeker_dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/recruiter/dashboard")
async def get_recruiter_dashboard(current_user: dict = Depends(verify_token)):
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")
            
        # Find user in database
        user = next((u for u in users_db['recruiters'] if u['email'] == current_user["user_email"]), None)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Return user data without password
        user_data = {k: v for k, v in user.items() if k != 'password'}
        return JSONResponse(content={
            "success": True,
            "user": user_data
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recruiter/jobs")
async def post_job(job: Job, current_user: dict = Depends(verify_token)):
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")
        
        current_db = load_db()
        
        job_data = job.dict()
        job_data["recruiter_email"] = current_user["user_email"]
        job_data["id"] = len(current_db["jobs"]) + 1
        
        print(f"Job data to be added: {job_data}")
        
        current_db["jobs"].append(job_data)
        
        print(f"Current DB before saving: {current_db}")
        
        save_db(current_db)
        
        return JSONResponse(content={"success": True, "message": "Job posted successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recruiter/applications")
async def get_recruiter_applications(current_user: dict = Depends(verify_token)):
    try:
        if current_user["user_type"] != "recruiter":
            raise HTTPException(status_code=403, detail="Access denied")

        current_db = load_db()
        recruiter_email = current_user["user_email"]

        # Get all jobs posted by the recruiter
        recruiter_jobs = [job for job in current_db["jobs"] if job["recruiter_email"] == recruiter_email]
        recruiter_job_ids = [job["id"] for job in recruiter_jobs]

        # Get all applications for the recruiter's jobs
        applications = [app for app in current_db["applications"] if app["job_id"] in recruiter_job_ids]

        # Add job and jobseeker details to the applications
        for app in applications:
            job = next((job for job in recruiter_jobs if job["id"] == app["job_id"]), None)
            jobseeker = next((js for js in current_db["jobseekers"] if js["email"] == app["jobseeker_email"]), None)
            app["job"] = job
            app["jobseeker"] = jobseeker

        return JSONResponse(content={"success": True, "applications": applications})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/jobseeker/apply")
async def apply_for_job(application: Application, current_user: dict = Depends(verify_token)):
    try:
        if current_user["user_type"] != "jobseeker":
            raise HTTPException(status_code=403, detail="Access denied")

        current_db = load_db()

        # Check if the job exists
        job = next((j for j in current_db["jobs"] if j["id"] == application.job_id), None)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Check if the user has already applied
        existing_application = next((app for app in current_db["applications"] if app["job_id"] == application.job_id and app["jobseeker_email"] == current_user["user_email"]), None)
        if existing_application:
            raise HTTPException(status_code=400, detail="You have already applied for this job")

        application_data = application.dict()
        application_data["jobseeker_email"] = current_user["user_email"]
        application_data["application_date"] = datetime.utcnow().isoformat()

        current_db["applications"].append(application_data)
        save_db(current_db)

        return JSONResponse(content={"success": True, "message": "Application submitted successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)



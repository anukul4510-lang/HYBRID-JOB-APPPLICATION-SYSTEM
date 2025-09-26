"""
File: models.py
Purpose: Defines all Pydantic models used for data validation and serialization
         in the FastAPI application. These models define the expected structure and
         data types for API request and response bodies, ensuring data consistency.

Author: [Your Name]
Date: 26/09/2025

"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

# ==============================================================================
# --- Authentication Models ---
# ==============================================================================

class LoginUser(BaseModel):
    """Defines the request body for user login."""
    userEmail: EmailStr = Field(..., description="The user's email address.", example="user@example.com")
    password: str = Field(..., description="The user's password.", example="strongpassword123")
    userType: str = Field(..., description="The type of user.", example="jobseeker")

class RegisterUser(BaseModel):
    """Defines the request body for new user registration."""
    email: EmailStr = Field(..., description="The new user's email address.", example="newuser@example.com")
    password: str = Field(..., description="The new user's password.", min_length=8)
    userType: str = Field(..., description="The type of user, either 'jobseeker' or 'recruiter'.", example="jobseeker")
    name: Optional[str] = Field(None, description="The user's full name.", example="John Doe")
    phone: Optional[str] = Field(None, description="The user's phone number.", example="123-456-7890")
    company: Optional[str] = Field(None, description="The company name (for recruiters).", example="Tech Corp")

# ==============================================================================
# --- Jobseeker Models ---
# ==============================================================================

class JobseekerProfile(BaseModel):
    """Defines the data model for a jobseeker's profile information."""
    name: str = Field(..., description="Jobseeker's full name.", example="Jane Doe")
    phone: str = Field(..., description="Jobseeker's contact phone number.", example="098-765-4321")
    location: str = Field(..., description="Jobseeker's city and state.", example="San Francisco, CA")
    experience_level: str = Field(..., description="Jobseeker's professional experience level.", example="Senior")
    education: str = Field(..., description="Jobseeker's highest level of education.", example="Bachelor's in Computer Science")

class JobseekerSkills(BaseModel):
    """Defines the data model for updating a jobseeker's skills."""
    skills: List[str] = Field(..., description="A list of the jobseeker's skills.", example=["Python", "FastAPI", "React"])

class JobPreferences(BaseModel):
    """Defines the data model for a jobseeker's job preferences."""
    preferred_role: str = Field(..., description="The jobseeker's preferred job title or role.", example="Software Engineer")
    preferred_industry: str = Field(..., description="The industry the jobseeker wants to work in.", example="Technology")
    work_mode: str = Field(..., description="The preferred work mode.", example="Remote")
    job_type: str = Field(..., description="The preferred employment type.", example="Full-time")

class Application(BaseModel):
    """Defines the request body for submitting a job application."""
    job_id: int = Field(..., description="The unique identifier of the job to apply for.")

# ==============================================================================
# --- Recruiter & Job Models ---
# ==============================================================================

class Job(BaseModel):
    """Defines the data model for creating and updating a job posting."""
    title: str = Field(..., description="The title of the job.", example="Senior Python Developer")
    location: str = Field(..., description="The location for the job.", example="New York, NY")
    employmentType: str = Field(..., description="The type of employment.", example="Full-time")
    description: str = Field(..., description="A detailed description of the job responsibilities and requirements.")
    skills: List[str] = Field(..., description="A list of required skills for the job.", example=["Python", "Django", "PostgreSQL"])
    minSalary: int = Field(..., description="The minimum salary for the position.", example=120000)
    maxSalary: int = Field(..., description="The maximum salary for the position.", example=150000)

class Shortlist(BaseModel):
    """Defines the request body for adding a candidate to a recruiter's shortlist."""
    candidate_id: int = Field(..., description="The unique identifier of the candidate (user) to shortlist.")

class ShortlistUpdate(BaseModel):
    """Defines the request body for updating a shortlisted candidate's information."""
    notes: Optional[str] = Field(None, description="Recruiter's notes about the candidate.")
    status: Optional[str] = Field(None, description="The candidate's status in the hiring process.", example="Interview Scheduled")

class ApplicationStatusUpdate(BaseModel):
    """Defines the request body for updating the status of a job application."""
    status: str = Field(..., description="The new status of the application.", example="Reviewed")

# ==============================================================================
# --- Search Models ---
# ==============================================================================

class JobSearch(BaseModel):
    """Defines the query parameters for a traditional job search."""
    keyword: Optional[str] = Field(None, description="A keyword to search in job titles and descriptions.")
    location: Optional[str] = Field(None, description="The desired job location.")
    employmentType: Optional[str] = Field(None, description="The desired employment type.")
    minSalary: Optional[int] = Field(None, description="The minimum desired salary.")
    maxSalary: Optional[int] = Field(None, description="The maximum desired salary.")

class SearchQuery(BaseModel):
    """Defines the request body for an AI-powered semantic search."""
    query: str = Field(..., description="A natural language query for searching jobs or candidates.", example="entry-level software job in Austin")
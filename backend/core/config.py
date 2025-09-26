"""
File: config.py
Purpose: Manages application configuration. It loads environment variables from a .env
         file and exposes them through a settings object for easy and secure access
         throughout the application.

Author: [Your Name]
Date: 26/09/2025

"""

import os
from dotenv import load_dotenv

# --- Environment Variable Loading ---

# Construct the absolute path to the .env file located in the project root.
# This ensures that the .env file is found regardless of where the application is run from.
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')

# Load the environment variables from the specified .env file.
load_dotenv(dotenv_path=dotenv_path)

# --- Settings Class ---

class Settings:
    """
    A centralized class for accessing all application settings.

    This class retrieves settings from environment variables, providing default values
    for local development if a variable is not set. This approach avoids hardcoding
    sensitive information and makes configuration flexible across different environments
    (development, testing, production).
    """
    # --- Database Settings ---
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    DB_NAME: str = os.getenv("DB_NAME", "job_portal_db")

    # --- JWT (JSON Web Token) Settings ---
    # A secret key for signing the JWTs. This should be a long, random, and secret string.
    # It is crucial for security that this is not hardcoded, especially in production.
    # TODO: Generate a strong secret key and set it in the .env file.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key_that_should_be_changed")

    # The algorithm to use for signing the JWTs.
    ALGORITHM: str = "HS256"

    # The expiration time for access tokens in minutes.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # --- AI Service (Gemini) Settings ---
    # Your API key for the Gemini AI service.
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")


# --- Settings Instance ---

# Create a single, globally accessible instance of the Settings class.
# Other parts of the application should import this `settings` object to access configuration values.
# Example: from backend.core.config import settings; db_host = settings.DB_HOST
settings = Settings()
"""
File: security.py
Purpose: Handles security-related functions like password hashing, JWT token
         creation, and token verification for the FastAPI application.

Author: [Your Name]
Date: 26/09/2025

"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

# Add the project root to the Python path to import the settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.core.config import settings

# ==============================================================================
# --- 1. Password Hashing ---
# ==============================================================================

# Use passlib's CryptContext for secure password hashing.
# bcrypt is the chosen scheme, which is a strong and widely-used hashing algorithm.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against its hashed version.

    Args:
        plain_password (str): The plain-text password to verify.
        hashed_password (str): The hashed password from the database.

    Returns:
        bool: True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hashes a plain-text password using the configured hashing algorithm.

    Args:
        password (str): The plain-text password to hash.

    Returns:
        str: The resulting hashed password.
    """
    return pwd_context.hash(password)

# ==============================================================================
# --- 2. JWT Token Handling ---
# ==============================================================================

# This scheme defines that the token will be sent in the Authorization header
# as a Bearer token. It's used by FastAPI to automatically extract the token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict) -> str:
    """
    Creates a new JWT (JSON Web Token) access token.

    The token includes the provided data as its payload and an expiration time.

    Args:
        data (dict): The payload to encode in the token (e.g., user ID, email, role).

    Returns:
        str: The encoded JWT as a string.
    """
    to_encode = data.copy()
    # Calculate the token's expiration time
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # Encode the payload with the secret key and algorithm from settings
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def verify_token(token: str) -> dict:
    """
    Decodes and validates a JWT token.

    This is a helper function used by endpoints that need to verify a token
    without necessarily protecting the route with a dependency.

    Args:
        token (str): The JWT token string.

    Returns:
        dict: The decoded payload of the token.

    Raises:
        HTTPException: 401 if the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    A FastAPI dependency that decodes and validates a JWT token from the request.

    This function is used in endpoint definitions to:
    1. Protect the route (ensure the user is logged in).
    2. Retrieve the current user's identity from the token.

    Args:
        token (str): The JWT token automatically extracted from the
                     'Authorization: Bearer <token>' header by FastAPI.

    Returns:
        dict: The payload of the token containing user information.
              (e.g., {"user_email": ..., "user_type": ..., "user_id": ...})

    Raises:
        HTTPException: 401 Unauthorized if the token is invalid, expired, or missing required claims.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the token using the secret key and algorithm
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Extract user information from the payload
        user_email: Optional[str] = payload.get("user_email")
        user_type: Optional[str] = payload.get("user_type")
        user_id: Optional[int] = payload.get("user_id")

        # Ensure all required user details are present in the token
        if user_email is None or user_type is None or user_id is None:
            raise credentials_exception

        # TODO: Consider returning a Pydantic model instead of a dict for better type safety.
        return {"user_email": user_email, "user_type": user_type, "user_id": user_id}
    except JWTError:
        # This catches any error from jwt.decode (e.g., invalid signature, expired token)
        raise credentials_exception
"""
File: ai_service.py
Purpose: Handles all interactions with the Google Gemini AI model. This service
         is responsible for parsing natural language queries into structured data
         that can be used for advanced search functionality.

Author: [Your Name]
Date: 26/09/2025

"""

import google.generativeai as genai
import os
import sys
import json

# Add the project root to the Python path to import the settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.core.config import settings

# --- Gemini AI Configuration ---

try:
    # Configure the Gemini API using the key from the central settings file.
    # This is a more secure and maintainable approach than loading .env files directly.
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
    genai.configure(api_key=settings.GEMINI_API_KEY)
except (ValueError, KeyError) as e:
    # This will prevent the application from starting if the AI service is not configured.
    raise Exception(f"Fatal: Failed to configure Gemini AI. {e}")

# --- Model Initialization ---

# Create a global instance of the Gemini model to be reused across the application.
# 'gemini-pro' is a versatile model suitable for a variety of natural language tasks.
model = genai.GenerativeModel('gemini-pro')

def parse_query(query: str) -> dict:
    """
    Parses a natural language query to extract structured filters and a semantic query string.

    This function sends a detailed prompt to the Gemini model, asking it to act as a JSON
    extractor. It identifies key search criteria like location, salary, and skills from
    a user's free-text input.

    Args:
        query (str): The natural language query from the user.

    Returns:
        dict: A dictionary containing the extracted structured data and the remaining
              semantic part of the query. Returns an empty dictionary on failure.

    Example Usage:
        >>> parse_query("find a remote python job in new york with a salary of 150k")
        {
            "location": "new york",
            "salary": 150000,
            "experience": null,
            "skills": ["python"],
            "job_type": "remote",
            "semantic_query": "python job"
        }
    """
    # The prompt is engineered to instruct the model to perform a specific task:
    # extract structured data and return it in a clean JSON format.
    prompt = f"""You are an intelligent assistant for a job portal. Your task is to extract structured data from the following user query. The user is searching for either jobs or candidates.

    The structured data should include as many of the following fields as possible:
    - "location" (string): The geographical area of the search.
    - "salary" (integer): The target salary, extracted as a number.
    - "experience" (integer): The desired years of experience.
    - "skills" (list of strings): A list of technical or soft skills mentioned.
    - "job_type" (string): The type of employment, such as "remote", "full-time", "part-time", or "contract".

    The remaining, more general part of the query should be returned as the 'semantic_query'. This part will be used for vector-based searching.

    Here is the user's query: "{query}"

    Please return your response as a single, valid JSON object with the fields: "location", "salary", "experience", "skills", "job_type", and "semantic_query".
    If a field is not present in the query, its value in the JSON should be null. Do not include any text or formatting outside of the JSON object.
    """

    try:
        # Send the prompt to the Gemini model
        response = model.generate_content(prompt)
        
        # The response text should be a JSON string, so we parse it into a Python dict.
        # This can fail if the model returns a malformed response.
        parsed_json = json.loads(response.text)
        return parsed_json
    except Exception as e:
        # Handle potential errors, such as API failures or JSON parsing issues.
        print(f"Error parsing query with AI model: {e}")
        # Return a default structure or an empty dict to prevent crashes downstream.
        return {
            "location": None,
            "salary": None,
            "experience": None,
            "skills": [],
            "job_type": None,
            "semantic_query": query  # Fallback to using the original query
        }

if __name__ == '__main__':
    # Example of how to use the parse_query function for testing.
    test_query = "I am looking for a senior backend developer position in San Francisco, CA with a salary around $180,000. Must know Python and AWS."
    print(f"Original Query: {test_query}")
    parsed_data = parse_query(test_query)
    print("Parsed Data:")
    print(json.dumps(parsed_data, indent=2))
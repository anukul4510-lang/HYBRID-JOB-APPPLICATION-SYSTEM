
import google.generativeai as genai
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Configure Gemini API
try:
    api_key = os.environ["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    raise Exception("GEMINI_API_KEY environment variable not set.")


# Create a Gemini model instance
model = genai.GenerativeModel('gemini-pro')

def parse_query(query):
    """
    Parses a natural language query to extract structured filters and a semantic query.
    """
    prompt = f"""
    Extract structured data from the following user query. The user is searching for jobs or candidates.
    The structured data should include as many of the following fields as possible:
    - location (string)
    - salary (integer)
    - experience (integer, in years)
    - skills (list of strings)
    - job_type (string, e.g., "remote", "full-time", "part-time")

    The remaining part of the query should be returned as the 'semantic_query'.

    Query: "{query}"

    Return the result as a JSON object with the fields: "location", "salary", "experience", "skills", "job_type", and "semantic_query".
    If a field is not present in the query, its value should be null.
    """

    response = model.generate_content(prompt)
    return response.text

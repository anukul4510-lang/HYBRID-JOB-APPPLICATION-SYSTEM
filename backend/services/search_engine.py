"""
File: search_engine.py
Purpose: Implements the core hybrid search functionality of the job portal.
         It combines AI-powered query parsing, traditional SQL filtering, and
         semantic vector search to deliver comprehensive and relevant results.

Author: [Your Name]
Date: 26/09/2025

"""

import json
import os
import sys

# Add the project root to the Python path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# --- Local Application Imports ---

# AI service for parsing natural language queries
from backend.services.ai_service import parse_query

# Vector database service for semantic search
from backend.services.vector_service import query_collection, job_descriptions_collection, candidate_profiles_collection

# MySQL database functions for structured data search
from backend.db.mysql_db import search_jobs, search_candidates, get_jobs_by_ids, get_candidates_by_ids

def search(query: str, search_type: str = "jobs") -> list:
    """
    Performs a hybrid search for jobs or candidates using a multi-step process.

    The process is as follows:
    1.  **AI Parsing**: The raw natural language query is sent to the Gemini AI model
        to be parsed into structured filters (e.g., location, salary) and a
        more general 'semantic_query'.
    2.  **SQL Filtering**: A traditional database search is performed using the
        structured filters to find exact matches.
    3.  **Vector Search**: A semantic search is performed on the vector database
        using the 'semantic_query' to find conceptually similar results.
    4.  **Merge & Rank**: The results from the SQL and vector searches are combined,
        duplicates are removed, and the final list is returned.

    Args:
        query (str): The user's natural language search query.
        search_type (str, optional): The type of search to perform, either "jobs" or
                                   "candidates". Defaults to "jobs".

    Returns:
        list: A list of dictionaries, where each dictionary represents a job or
              candidate profile matching the search criteria.
    """
    print(f"Starting hybrid search for '{search_type}' with query: '{query}'")

    # --- Step 1: Parse the natural language query using Gemini AI ---
    parsed_query_str = parse_query(query)
    try:
        # The response from Gemini is expected to be a JSON string.
        # It may sometimes include markdown formatting, which needs to be stripped.
        cleaned_str = parsed_query_str.replace("```json", "").replace("```", "").strip()
        parsed_query = json.loads(cleaned_str)
    except (json.JSONDecodeError, AttributeError):
        # If the AI service fails to return valid JSON, fall back to using the
        # original query for semantic search and no structured filters.
        print("Warning: AI query parsing failed. Falling back to semantic-only search.")
        parsed_query = {"semantic_query": query}

    print(f"Parsed Query: {parsed_query}")

    # --- Step 2: Perform SQL search for exact matches based on structured filters ---
    sql_results = []
    if search_type == "jobs":
        sql_results = search_jobs(
            location=parsed_query.get("location"),
            salary=parsed_query.get("salary"),
            experience=parsed_query.get("experience"),
            skills=parsed_query.get("skills"),
            job_type=parsed_query.get("job_type"),
        )
    elif search_type == "candidates":
        sql_results = search_candidates(
            location=parsed_query.get("location"),
            skills=parsed_query.get("skills"),
        )
    print(f"Found {len(sql_results)} results from SQL search.")

    # --- Step 3: Perform vector search for semantic similarity ---
    vector_results = None
    semantic_query = parsed_query.get("semantic_query")
    if semantic_query:
        collection = job_descriptions_collection if search_type == "jobs" else candidate_profiles_collection
        vector_results = query_collection(collection, semantic_query)
        print(f"Found {len(vector_results.get('ids', [[]])[0])} potential results from vector search.")

    # --- Step 4: Merge and rank results ---
    # Start with the exact matches from the SQL search, as they are often more relevant.
    combined_results = sql_results if sql_results else []
    combined_ids = {result['id'] for result in combined_results}

    # Add results from the vector search, avoiding duplicates.
    if vector_results and vector_results.get('ids') and vector_results['ids'][0]:
        # Convert vector result IDs from string to int
        vector_ids = [int(id_str) for id_str in vector_results["ids"][0] if id_str.isdigit()]
        
        # Fetch the full document details for the IDs found in the vector search
        if vector_ids:
            if search_type == "jobs":
                vector_docs = get_jobs_by_ids(vector_ids)
            else: # search_type == "candidates"
                vector_docs = get_candidates_by_ids(vector_ids)

            # Add non-duplicate vector results to the combined list
            if vector_docs:
                for doc in vector_docs:
                    if doc['id'] not in combined_ids:
                        combined_results.append(doc)
                        combined_ids.add(doc['id'])

    print(f"Returning {len(combined_results)} combined and de-duplicated results.")
    return combined_results


if __name__ == '__main__':
    """
    Example usage of the search engine for testing purposes.
    """
    print("--- Search Engine Test ---")

    # Test Case 1: Job Search
    job_query = "Find me a remote job for a python developer in California"
    print(f"\n--- Testing Job Search with query: '{job_query}' ---")
    job_results = search(job_query, search_type="jobs")
    print("\n--- Job Search Results ---")
    if job_results:
        for result in job_results:
            print(f"- {result.get('title')} at {result.get('location')}")
    else:
        print("No jobs found.")

    # Test Case 2: Candidate Search
    candidate_query = "Show me candidates with experience in marketing and SEO"
    print(f"\n--- Testing Candidate Search with query: '{candidate_query}' ---")
    candidate_results = search(candidate_query, search_type="candidates")
    print("\n--- Candidate Search Results ---")
    if candidate_results:
        for result in candidate_results:
            print(f"- {result.get('name')} ({result.get('email')})")
    else:
        print("No candidates found.")

    print("\n--- Test Complete ---")
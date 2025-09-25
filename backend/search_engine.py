import json
from backend.ai_service import parse_query
from backend.vector_service import query_collection, job_descriptions_collection, candidate_profiles_collection
from backend.mysql_db import search_jobs, search_candidates, get_jobs_by_ids, get_candidates_by_ids

def search(query, search_type="jobs"):
    """
    Performs a hybrid search for jobs or candidates.
    """
    # 1. Parse the natural language query using Gemini AI
    parsed_query_str = parse_query(query)
    try:
        # The response from Gemini is expected to be a JSON string, sometimes with markdown formatting.
        # The below code will remove the markdown formatting and load the JSON.
        parsed_query = json.loads(parsed_query_str.replace("```json", "").replace("```", ""))
    except json.JSONDecodeError:
        # Fallback if Gemini doesn't return valid JSON
        parsed_query = {"semantic_query": query}


    # 2. Perform SQL search for exact matches
    if search_type == "jobs":
        sql_results = search_jobs(
            location=parsed_query.get("location"),
            salary=parsed_query.get("salary"),
            experience=parsed_query.get("experience"),
            skills=parsed_query.get("skills"),
            job_type=parsed_query.get("job_type"),
        )
    else: # search_type == "candidates"
        sql_results = search_candidates(
            location=parsed_query.get("location"),
            skills=parsed_query.get("skills"),
        )


    # 3. Perform vector search for semantic similarity
    semantic_query = parsed_query.get("semantic_query")
    if semantic_query:
        if search_type == "jobs":
            vector_results = query_collection(job_descriptions_collection, semantic_query)
        else: # search_type == "candidates"
            vector_results = query_collection(candidate_profiles_collection, semantic_query)
    else:
        vector_results = None

    # 4. Merge and rank results
    
    combined_results = []
    if sql_results:
        combined_results.extend(sql_results)

    if vector_results and vector_results['ids'][0]:
        vector_ids = [int(id) for id in vector_results["ids"][0]]
        
        if search_type == "jobs":
            vector_docs = get_jobs_by_ids(vector_ids) 
        else: # search_type == "candidates"
            vector_docs = get_candidates_by_ids(vector_ids)

        # Add non-duplicate vector results to the combined list
        for doc in vector_docs:
            if doc not in combined_results:
                combined_results.append(doc)


    return combined_results

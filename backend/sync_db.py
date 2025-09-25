from mysql_db import get_all_data_from_table
from vector_service import add_to_collection, job_descriptions_collection, candidate_profiles_collection

def sync_jobs():
    """Syncs jobs from MySQL to ChromaDB."""
    jobs = get_all_data_from_table('jobs')
    for job in jobs:
        # Create a document to be embedded
        document = f"Title: {job['title']}\nDescription: {job['description']}\nSkills: {job['skills']}"
        # Clean metadata
        job_metadata = {k: (v if v is not None else "") for k, v in job.items()}
        # Add to ChromaDB
        add_to_collection(job_descriptions_collection, str(job['id']), document, job_metadata)
    print(f"Synced {len(jobs)} jobs to ChromaDB.")

def sync_candidates():
    """Syncs candidates from MySQL to ChromaDB."""
    candidates = get_all_data_from_table('users')
    # Filter for jobseekers
    candidates = [c for c in candidates if c['user_type'] == 'jobseeker']
    for candidate in candidates:
        # Create a document to be embedded
        skills = ", ".join(candidate.get('skills', [])) if candidate.get('skills') else ""
        document = f"Name: {candidate['name']}\nLocation: {candidate['location']}\nExperience: {candidate['experience_level']}\nEducation: {candidate['education']}\nSkills: {skills}"
        # Clean metadata
        candidate_metadata = {k: (v if v is not None else "") for k, v in candidate.items()}
        # Add to ChromaDB
        add_to_collection(candidate_profiles_collection, str(candidate['id']), document, candidate_metadata)
    print(f"Synced {len(candidates)} candidates to ChromaDB.")

if __name__ == '__main__':
    sync_jobs()
    sync_candidates()

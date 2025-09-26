"""
File: vector_service.py
Purpose: Manages all interactions with the ChromaDB vector database. This includes
         initializing the database client, managing collections, generating text
         embeddings, and performing vector-based similarity searches.

Author: [Your Name]
Date: 26/09/2025

"""

import chromadb
from sentence_transformers import SentenceTransformer
import os

# ==============================================================================
# --- 1. Initialization ---
# ==============================================================================

# --- ChromaDB Client Initialization ---
# Initialize the ChromaDB client with persistent storage. This means the data
# will be saved to disk in the specified directory and will persist across
# application restarts.
CHROMA_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'chroma_db')
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# --- Sentence Transformer Model Initialization ---
# Initialize the sentence transformer model. This model is used to convert text
# (like job descriptions or user profiles) into numerical vectors (embeddings).
# 'all-MiniLM-L6-v2' is a good general-purpose model that balances performance and size.
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# --- ChromaDB Collection Management ---
# This block attempts to create the necessary collections. If they already exist,
# it retrieves them instead. This makes the service idempotent and safe to run on startup.
try:
    # Collection for storing job description vectors
    job_descriptions_collection = client.create_collection("job_descriptions")
    # Collection for storing candidate profile vectors
    candidate_profiles_collection = client.create_collection("candidate_profiles")
except Exception:  # Catches errors if collections already exist
    job_descriptions_collection = client.get_collection("job_descriptions")
    candidate_profiles_collection = client.get_collection("candidate_profiles")


# ==============================================================================
# --- 2. Core Vector Operations ---
# ==============================================================================

def generate_embeddings(text: str) -> list[float]:
    """
    Generates a numerical vector embedding for a given text string.

    Embeddings are numerical representations of text that capture its semantic meaning.
    These vectors are what allow for similarity searches in the vector database.

    Args:
        text (str): The input text to be converted into an embedding.

    Returns:
        list[float]: The generated embedding as a list of floating-point numbers.
    """
    return embedding_model.encode(text).tolist()

def add_to_collection(collection: chromadb.Collection, doc_id: str, document: str, metadata: dict = None):
    """
    Adds a document and its embedding to a specified ChromaDB collection.

    If a document with the same ID already exists, its entry will be updated (upsert).

    Args:
        collection (chromadb.Collection): The collection to add the document to.
        doc_id (str): A unique identifier for the document.
        document (str): The text content of the document.
        metadata (dict, optional): A dictionary of metadata to store with the document.
                                 This can be used for filtering searches later.
    """
    # Generate the embedding for the document text
    embedding = generate_embeddings(document)
    
    # Add the document, its embedding, and metadata to the collection
    collection.add(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[document],
        metadatas=[metadata or {}] # Ensure metadata is at least an empty dict
    )

def query_collection(collection: chromadb.Collection, query_text: str, n_results: int = 5) -> dict:
    """
    Queries a collection to find the most similar documents to a given query text.

    Args:
        collection (chromadb.Collection): The collection to query.
        query_text (str): The text to search for.
        n_results (int, optional): The number of top results to return. Defaults to 5.

    Returns:
        dict: A dictionary containing the search results, including the IDs, documents,
              metadata, and distances (similarity scores) of the matches.
    """
    # Generate an embedding for the query text
    query_embedding = generate_embeddings(query_text)
    
    # Perform the query against the collection
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

# ==============================================================================
# --- 3. Example Usage ---
# ==============================================================================

if __name__ == '__main__':
    """
    Example usage of the vector service for testing purposes.
    This block will only run when the script is executed directly.
    """
    print("--- Vector Service Test ---")

    # 1. Add a sample job description to the collection
    print("\n1. Adding a sample job description...")
    job_id = "job_123"
    job_doc = "We are looking for a Python developer with experience in FastAPI and SQL."
    job_meta = {"title": "Python Developer", "location": "Remote"}
    add_to_collection(job_descriptions_collection, job_id, job_doc, job_meta)
    print(f"Added job with ID: {job_id}")

    # 2. Add a sample candidate profile to the collection
    print("\n2. Adding a sample candidate profile...")
    candidate_id = "candidate_456"
    candidate_doc = "Experienced software engineer skilled in Python, FastAPI, and database management."
    candidate_meta = {"name": "Jane Doe", "experience": "5 years"}
    add_to_collection(candidate_profiles_collection, candidate_id, candidate_doc, candidate_meta)
    print(f"Added candidate with ID: {candidate_id}")

    # 3. Query for similar jobs
    print("\n3. Querying for jobs similar to 'backend developer with database skills'...")
    job_query = "backend developer with database skills"
    job_results = query_collection(job_descriptions_collection, job_query, n_results=1)
    print("Query Results:")
    print(job_results)

    # 4. Query for similar candidates
    print("\n4. Querying for candidates similar to 'python and sql expert'...")
    candidate_query = "python and sql expert"
    candidate_results = query_collection(candidate_profiles_collection, candidate_query, n_results=1)
    print("Query Results:")
    print(candidate_results)

    print("\n--- Test Complete ---")
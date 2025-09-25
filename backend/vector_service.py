
import chromadb
from sentence_transformers import SentenceTransformer

# Initialize ChromaDB client with persistent storage
client = chromadb.PersistentClient(path="c:\\minor project real\\backend\\chroma_db")

# Initialize sentence transformer model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Create collections
try:
    job_descriptions_collection = client.create_collection("job_descriptions")
    candidate_profiles_collection = client.create_collection("candidate_profiles")
    skills_knowledge_collection = client.create_collection("skills_knowledge")
except Exception: # Should be chromadb.db.base.UniqueConstraintError, but that is not available in the library
    job_descriptions_collection = client.get_collection("job_descriptions")
    candidate_profiles_collection = client.get_collection("candidate_profiles")
    skills_knowledge_collection = client.get_collection("skills_knowledge")


def generate_embeddings(text):
    """Generates embeddings for a given text."""
    return embedding_model.encode(text).tolist()

def add_to_collection(collection, doc_id, document, metadata=None):
    """Adds a document and its embedding to a collection."""
    embedding = generate_embeddings(document)
    collection.add(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[document],
        metadatas=[metadata] if metadata else None
    )

def query_collection(collection, query_text, n_results=5):
    """Queries a collection with a given text."""
    query_embedding = generate_embeddings(query_text)
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

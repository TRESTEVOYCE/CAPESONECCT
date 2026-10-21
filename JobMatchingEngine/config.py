import os
from django.conf import settings
import chromadb
from chromadb.utils import embedding_functions

# Configures the path where your persistent vector data is written locally
CHROMA_DATA_PATH = os.path.join(settings.BASE_DIR, 'chroma_data')

# Initializes the central persistent storage client (creates the folder if missing)
chroma_client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)

# Lazy-loaded embedding function to prevent startup crashes and timeouts on Render
_embedding_function = None

def get_embedding_function():
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    return _embedding_function
import os
from django.conf import settings
import chromadb
from chromadb.utils import embedding_functions

# Configures the path where your persistent vector data is written locally
CHROMA_DATA_PATH = os.path.join(settings.BASE_DIR, 'chroma_data')

# Initializes the central persistent storage client (creates the folder if missing)
chroma_client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)

# Initializes a local, free, lightweight sentence-transformers model
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

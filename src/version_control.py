
import chromadb
from chromadb.utils import embedding_functions
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize ChromaDB
client = chromadb.PersistentClient(path="data/chroma_db")
ef = embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")



def store_version(text: str, source_file: str, version_type: str = "ai"):
    try:
        collection = client.get_or_create_collection(
            name="book_versions",
            embedding_function=ef
        )

        version_id = f"v{int(time.time())}"  # unique ID based on  timestamp for avoiding collisions

        collection.add(
            documents=[text],
            metadatas=[{
                "source": source_file,
                "type": version_type,
                "length": len(text.split())
            }],
            ids=[version_id]
        )
        logger.info(f"Stored version {version_id} ({version_type})")

    except Exception as e:
        logger.error(f"Version storage failed: {str(e)}")
        raise

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import SGDRegressor  
from src.version_control import client
import joblib
import os
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class RLSearchEngine:
    def __init__(self):
        self.model_path = Path("data/rl_model/rl_model.pkl")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2") 
        self.reward_model = SGDRegressor(loss="epsilon_insensitive")
        self._initialize_model()

    def _initialize_model(self):
        """Load or create the RL model"""
        if self.model_path.exists():
            self.reward_model = joblib.load(self.model_path)
            logger.info("Loaded trained RL model")
        else:
            dummy_X = np.zeros((1, 384)) 
            dummy_y = [0.5]
            self.reward_model.partial_fit(dummy_X, dummy_y)
            logger.info("Initialized new RL model")

    def train(self, ratings: dict):
        """
        Train on human feedback
        Args:
            ratings: {"random_version_id": 0.8, "random_version_id": 0.3} (0=bad, 1=good)
        """
        try:
            collection = client.get_collection("book_versions")
            versions = collection.get()
            
            X = []
            y = []
            for vid, score in ratings.items():
                if vid in versions["ids"]:
                    idx = versions["ids"].index(vid)
                    X.append(self.embedder.encode(versions["documents"][idx]))
                    y.append(score)
            
            if len(X) > 0:
                self.reward_model.partial_fit(np.array(X), np.array(y))
                os.makedirs(self.model_path.parent, exist_ok=True)
                joblib.dump(self.reward_model, self.model_path)
                logger.info(f"Trained on {len(X)} new ratings")
        
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")

    def search(self, query: str, top_k: int = 3) -> list:
        """Find best versions matching a query
        Returns:
            List of tuples: (version_id, score, text_preview)
        """
        try:
            query_embed = self.embedder.encode(query)
            
            collection = client.get_collection("book_versions") ## All versions from ChromaDB
            versions = collection.get()
            
            scores = [] ##score each version
            for i, (vid, text) in enumerate(zip(versions["ids"], versions["documents"])):
                # Combine semantic and quality scores
                semantic_score = np.dot(query_embed, self.embedder.encode(text))
                quality_score = self.reward_model.predict([self.embedder.encode(text)])[0]
                combined_score = 0.7 * semantic_score + 0.3 * quality_score  
                scores.append((vid, combined_score, text[:200]))  
            
            #  top results
            return sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []


if __name__ == "__main__":
    searcher = RLSearchEngine()
    
    searcher.train({"v1": 0.8, "v2": 0.5})  # v1 better than v2
    

    results = searcher.search("strong character introduction")
    for i, (vid, score, preview) in enumerate(results):
        print(f"{i+1}. {vid} (Score: {score:.2f})\n{preview}\n")
from typing import List, Dict, Any
from backend.config import EMBEDDING_MODEL, DEMO_MODE

class EmbeddingProvider:
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        if DEMO_MODE or self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception:
                # Fallback: return zero vectors
                return [[0.0] * 384 for _ in texts]
        
        try:
            embeddings = self._model.encode(texts, show_progress_bar=False)
            return embeddings.tolist()
        except Exception:
            return [[0.0] * 384 for _ in texts]

embedding_provider = EmbeddingProvider()

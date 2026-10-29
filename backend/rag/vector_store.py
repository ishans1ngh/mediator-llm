import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.config import VECTOR_STORE_PATH
from backend.rag.embeddings import embedding_provider

class SimpleVectorStore:
    def __init__(self, store_path: str = VECTOR_STORE_PATH):
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.store_path / "index.pkl"
        self.docs_file = self.store_path / "docs.json"
        self.docs: List[Dict[str, Any]] = []
        self.embeddings: List[List[float]] = []
        self._load()
    
    def _load(self):
        if self.docs_file.exists():
            with open(self.docs_file, "r", encoding="utf-8") as f:
                self.docs = json.load(f)
        if self.index_file.exists():
            with open(self.index_file, "rb") as f:
                self.embeddings = pickle.load(f)
    
    def _save(self):
        with open(self.docs_file, "w", encoding="utf-8") as f:
            json.dump(self.docs, f)
        with open(self.index_file, "wb") as f:
            pickle.dump(self.embeddings, f)
    
    def add(self, documents: List[Dict[str, Any]]):
        texts = [d.get("text", "") for d in documents]
        embeddings = embedding_provider.encode(texts)
        self.docs.extend(documents)
        self.embeddings.extend(embeddings)
        self._save()
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        if not self.docs:
            return []
        query_emb = embedding_provider.encode([query])[0]
        # Simple cosine similarity
        import math
        def dot(a, b):
            return sum(x*y for x, y in zip(a, b))
        def norm(v):
            return math.sqrt(sum(x*x for x in v)) or 1e-9
        scores = []
        for emb in self.embeddings:
            sim = dot(query_emb, emb) / (norm(query_emb) * norm(emb))
            scores.append(sim)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        results = []
        for idx, score in ranked:
            doc = dict(self.docs[idx])
            doc["_score"] = score
            results.append(doc)
        return results
    
    def clear(self):
        self.docs = []
        self.embeddings = []
        self._save()

vector_store = SimpleVectorStore()

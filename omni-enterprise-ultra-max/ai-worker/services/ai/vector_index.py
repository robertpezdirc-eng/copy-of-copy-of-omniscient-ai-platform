"""
Per-tenant FAISS index with sentence-transformers embeddings and GCS persistence.
Env: GCS_BUCKET_AI_MODELS (optional) for persistence
"""
import os
import io
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from ..gcs_store import GCSStore

class TenantVectorIndex:
    def __init__(self, tenant_id: str, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.tenant_id = tenant_id
        self.embedder = SentenceTransformer(model_name)
        self.index: Optional[faiss.IndexFlatIP] = None
        self.ids: List[str] = []
        self.store: Optional[GCSStore] = None
        try:
            if os.getenv("GCS_BUCKET_AI_MODELS"):
                self.store = GCSStore()
        except Exception:
            self.store = None
        # Try load existing index
        self._load_index()

    def _index_path(self) -> str:
        return f"{self.tenant_id}/faiss.index"

    def _ids_path(self) -> str:
        return f"{self.tenant_id}/faiss_ids.txt"

    def _save_index(self):
        if not self.store or self.index is None:
            return
        buf = io.BytesIO()
        faiss.write_index(self.index, faiss.PyCallbackIOWriter(buf.write))
        self.store.upload_bytes(self._index_path(), buf.getvalue())
        self.store.upload_bytes(self._ids_path(), "\n".join(self.ids).encode("utf-8"), content_type="text/plain")

    def _load_index(self):
        if not self.store:
            return
        data = self.store.download_bytes(self._index_path())
        if data:
            rb = io.BytesIO(data)
            self.index = faiss.read_index(faiss.PyCallbackIOReader(rb.read))
            ids_bytes = self.store.download_bytes(self._ids_path())
            if ids_bytes:
                self.ids = ids_bytes.decode("utf-8").splitlines()

    def upsert(self, items: List[Dict[str, Any]]):
        # items: list of {id: str, text: str}
        texts = [it["text"] for it in items]
        vectors = self.embedder.encode(texts, normalize_embeddings=True)
        vectors = np.array(vectors).astype("float32")
        if self.index is None:
            self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)
        self.ids.extend([it["id"] for it in items])
        self._save_index()

    def query(self, text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        if self.index is None:
            return []
        vec = self.embedder.encode([text], normalize_embeddings=True).astype("float32")
        scores, idxs = self.index.search(vec, top_k)
        results: List[Tuple[str, float]] = []
        for i, score in zip(idxs[0], scores[0]):
            if 0 <= i < len(self.ids):
                results.append((self.ids[i], float(score)))
        return results

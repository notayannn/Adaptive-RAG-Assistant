import config
from core.embedder import Embedder
from core.vector_store import VectorStore

class Retriever:
    def __init__(self, embedder: Embedder, vector_store: VectorStore):
        self.embedder = embedder
        self.vector_store = vector_store

    def retrieve(self, query: str, top_k: int = None, threshold: float = None):
        """
        Embeds query, searches Qdrant, and filters out hits below score threshold.
        Returns filtered context chunks and query similarity metadata.
        """
        top_k = top_k if top_k is not None else config.DEFAULT_TOP_K
        threshold = threshold if threshold is not None else config.DEFAULT_SIMILARITY_THRESHOLD

        query_vector = self.embedder.embed_query(query)

        raw_hits = self.vector_store.search(query_vector, top_k=top_k)

        filtered_chunks = []
        for hit in raw_hits:
            score = round(hit.score, 4)
            if score >= threshold:
                filtered_chunks.append({
                    "text": hit.payload["text"],
                    "source_file": hit.payload["source_file"],
                    "page": hit.payload.get("page", 1),
                    "score": score
                })

        return filtered_chunks, raw_hits
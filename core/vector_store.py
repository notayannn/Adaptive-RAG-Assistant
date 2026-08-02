from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, 
    VectorParams, 
    PointStruct, 
    Filter, 
    FieldCondition, 
    MatchValue, 
    FilterSelector
)
import config

class VectorStore:
    def __init__(self):
        # Initialize raw Qdrant client connection
        self.client = QdrantClient(
            url=config.QDRANT_URL,
            api_key=config.QDRANT_API_KEY
        )
        self.collection_name = config.COLLECTION_NAME
        self.init_collection()

    def init_collection(self):
        """
        Creates the Qdrant collection if it doesn't already exist.
        Configures vector size (384) and Cosine distance metric.
        """
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=config.EMBEDDING_DIM,
                    distance=Distance.COSINE
                )
            )


        try:
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="source_file",
                field_schema="keyword"
            )
        except Exception:
            pass

    def upsert_chunks(self, chunk_records: list[dict], embeddings: list[list[float]]):
        """
        Builds PointStruct objects and upserts vectors + payloads into Qdrant.
        """
        points = []
        for idx, (record, vector) in enumerate(zip(chunk_records, embeddings)):
            points.append(
                PointStruct(
                    id=record["chunk_id"],
                    vector=vector,
                    payload={
                        "text": record["text"],
                        "source_file": record["metadata"]["source_file"],
                        "page": record["metadata"].get("page", 1),
                        "chunk_index": record["metadata"].get("chunk_index", idx)
                    }
                )
            )
        
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

    def search(self, query_vector: list[float], top_k: int = 3):
        """
        Executes vector search on Qdrant and returns nearest points with similarity scores.
        """
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k
        ).points
        return search_result

    def delete_by_source(self, filename: str):
        """
        Purges all points from Qdrant where payload['source_file'] == filename.
        Enables dynamic source deletion. wait=True (Qdrant's default, made explicit
        here) blocks until the deletion is actually applied before returning, so a
        caller checking the collection state right after this call sees it reflected.
        """
        result = self.client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="source_file",
                            match=MatchValue(value=filename)
                        )
                    ]
                )
            ),
            wait=True
        )
        return result

    def list_active_documents(self) -> list[str]:
        """
        Retrieves unique source file names currently stored in the vector database.
        """

        scroll_res, _ = self.client.scroll(
            collection_name=self.collection_name,
            limit=500,
            with_payload=True,
            with_vectors=False
        )
        sources = set()
        for point in scroll_res:
            if point.payload and "source_file" in point.payload:
                sources.add(point.payload["source_file"])
        return sorted(list(sources))

    def get_collection_stats(self) -> dict:
        """
        Returns the current point count and an estimated vector memory footprint.

        Qdrant's client API doesn't expose exact live RAM usage for a collection,
        so this estimates raw vector memory as points * dimension * 4 bytes (float32).
        This does NOT include payload text storage, HNSW graph index overhead, or
        Qdrant's internal segment overhead, so actual server-side memory usage will
        be higher than this number — treat it as a lower-bound estimate, not exact.
        """
        try:
            info = self.client.get_collection(self.collection_name)
            points_count = info.points_count or 0
        except Exception:
            points_count = 0

        vector_bytes = points_count * config.EMBEDDING_DIM * 4
        estimated_mb = round(vector_bytes / (1024 * 1024), 3)

        return {
            "points_count": points_count,
            "estimated_vector_memory_mb": estimated_mb
        }
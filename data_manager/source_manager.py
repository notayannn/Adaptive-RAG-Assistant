import os
from ingestion.loader import load_document
from ingestion.chunker import chunk_documents
from core.embedder import Embedder
from core.vector_store import VectorStore

class SourceManager:
    def __init__(self, embedder: Embedder, vector_store: VectorStore):
        self.embedder = embedder
        self.vector_store = vector_store

    def add_document(self, uploaded_file) -> dict:
        """
        Orchestrates full ingestion pipeline:
        1. Parse file (Loader)
        2. Chunk text (Chunker)
        3. Generate embeddings (Embedder)
        4. Upsert vectors + payloads to Qdrant (VectorStore)
        """
        
        raw_docs = load_document(uploaded_file)
        if not raw_docs:
            return {"status": "error", "message": "Failed to extract text from file."}

        chunk_records = chunk_documents(raw_docs)
        if not chunk_records:
            return {"status": "error", "message": "No valid text chunks generated."}

        texts_to_embed = [record["text"] for record in chunk_records]
        embeddings = self.embedder.embed_chunks(texts_to_embed)

        self.vector_store.upsert_chunks(chunk_records, embeddings)

        stats = self.vector_store.get_collection_stats()

        return {
            "status": "success",
            "filename": uploaded_file.name,
            "chunk_count": len(chunk_records),
            "points_count": stats["points_count"],
            "memory_mb": stats["estimated_vector_memory_mb"]
        }

    def remove_document(self, filename: str) -> dict:
        """
        Purges all vector embeddings associated with a filename from Qdrant Cloud.
        Enables true dynamic data source removal. Verifies the deletion actually
        took effect (rather than trusting the API call didn't raise) by re-checking
        whether the filename still shows up in the active documents list afterward.
        """
        try:
            self.vector_store.delete_by_source(filename)
        except Exception as e:
            return {"status": "error", "message": str(e)}

        remaining = self.vector_store.list_active_documents()
        if filename in remaining:
            return {
                "status": "error",
                "message": (
                    "Delete call completed without error, but the document is still "
                    "present in the collection afterward. This usually means the stored "
                    "source_file payload value doesn't exactly match the filename being "
                    "deleted (e.g. trailing whitespace, different casing, or the file "
                    "was indexed under a slightly different name)."
                )
            }

        return {"status": "success", "filename": filename}

    def get_active_documents(self) -> list[str]:
        """
        Retrieves current active source files indexed in Qdrant Cloud.
        """
        return self.vector_store.list_active_documents()
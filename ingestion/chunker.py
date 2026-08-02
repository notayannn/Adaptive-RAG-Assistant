import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter
import config

def chunk_documents(loaded_docs: list[dict]) -> list[dict]:
    """
    Takes loaded document dicts and splits their text into smaller overlapping chunks.
    Attaches unique UUIDs and preserves source metadata.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunked_records = []

    for doc in loaded_docs:
        text = doc["text"]
        base_metadata = doc["metadata"]
        
        # Split text using LangChain's recursive splitter
        chunks = text_splitter.split_text(text)
        
        for idx, chunk_text in enumerate(chunks):
            # GENERATE A VALID UUID FOR QDRANT
            chunk_id = str(uuid.uuid4())
            
            chunked_records.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "metadata": {
                    "source_file": base_metadata["source_file"],
                    "page": base_metadata.get("page", 1),
                    "chunk_index": idx
                }
            })

    return chunked_records
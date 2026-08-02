import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader, TextLoader
import docx2txt

def load_document(uploaded_file):
    """
    Parses an uploaded Streamlit file (PDF, TXT, DOCX) and returns
    a list of dictionaries containing raw text and source metadata.
    """
    file_name = uploaded_file.name
    file_ext = os.path.splitext(file_name)[1].lower()
    
    # Save uploaded bytes to a temporary file on disk so LangChain loaders can read it
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    docs = []
    try:
        if file_ext == ".pdf":
            loader = PyPDFLoader(tmp_path)
            raw_docs = loader.load()
            for doc in raw_docs:
                docs.append({
                    "text": doc.page_content,
                    "metadata": {
                        "source_file": file_name,
                        "page": doc.metadata.get("page", 0) + 1
                    }
                })
        elif file_ext == ".txt":
            loader = TextLoader(tmp_path, encoding="utf-8")
            raw_docs = loader.load()
            for doc in raw_docs:
                docs.append({
                    "text": doc.page_content,
                    "metadata": {"source_file": file_name, "page": 1}
                })
        elif file_ext == ".docx":
            # Extract plain text from DOCX
            text = docx2txt.process(tmp_path)
            if text.strip():
                docs.append({
                    "text": text,
                    "metadata": {"source_file": file_name, "page": 1}
                })
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
            
    finally:
        # Clean up temporary file from disk
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            
    return docs
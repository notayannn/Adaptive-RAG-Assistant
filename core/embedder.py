from langchain_huggingface import HuggingFaceEmbeddings
import config

class Embedder:
    def __init__(self):
        self.model = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL_NAME
        )

    def embed_chunks(self, texts: list[str]) -> list[list[float]]:
        """
        Converts a list of text chunk strings into a list of 384-dim vector arrays.
        """
        if not texts:
            return []
        return self.model.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        """
        Converts a single user question string into a 384-dim vector array.
        """
        return self.model.embed_query(text)
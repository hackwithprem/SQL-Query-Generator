import logging
from typing import List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Embedding service for RAG using sentence-transformers.
    Generates 384-dimensional dense vectors using all-MiniLM-L6-v2.
    """
    _model = None

    @classmethod
    def get_model(cls):
        """Lazy loads the SentenceTransformer model on first invocation."""
        if cls._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                model_name = getattr(settings, "RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
                logger.info(f"Loading sentence-transformers embedding model: {model_name}")
                cls._model = SentenceTransformer(model_name)
            except Exception as e:
                logger.error(f"Failed to load sentence-transformers model: {e}")
                cls._model = None
        return cls._model

    @classmethod
    def get_embedding(cls, text: str) -> Optional[List[float]]:
        """
        Converts a natural language text into a 384-dimensional embedding vector.
        Returns None if embedding generation fails.
        """
        if not text or not text.strip():
            return None

        model = cls.get_model()
        if model is None:
            logger.warning("Embedding model is not available.")
            return None

        try:
            # Generate normalized embedding (cosine similarity becomes dot product)
            embedding = model.encode(text.strip(), normalize_embeddings=True)
            if hasattr(embedding, "tolist"):
                return embedding.tolist()
            return list(embedding)
        except Exception as e:
            logger.error(f"Error generating embedding for text: {e}")
            return None

    @classmethod
    def get_batch_embeddings(cls, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Batch encodes a list of texts into embeddings for efficient seeding.
        """
        if not texts:
            return []

        model = cls.get_model()
        if model is None:
            return [None] * len(texts)

        try:
            cleaned_texts = [t.strip() if t else "" for t in texts]
            embeddings = model.encode(cleaned_texts, normalize_embeddings=True, show_progress_bar=False)
            return [emb.tolist() if hasattr(emb, "tolist") else list(emb) for emb in embeddings]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [None] * len(texts)


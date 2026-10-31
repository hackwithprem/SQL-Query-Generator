import logging
from typing import List, Dict, Any, Optional
import numpy as np
from app.core.config import settings
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.knowledge_base import SQL_EXAMPLES
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

class RAGService:
    """
    Example-Based Retrieval-Augmented Generation (RAG) Service.
    Retrieves the most semantically relevant SQL query examples for a user's question
    to guide the LLM with few-shot syntactic patterns without schema hallucination.
    """
    _local_embeddings_cache: Optional[List[List[float]]] = None

    @classmethod
    def _get_local_embeddings(cls) -> List[List[float]]:
        """
        Lazily computes and caches embeddings for the local knowledge base.
        Enables seamless offline demonstration and fallback when Supabase is unavailable.
        """
        if cls._local_embeddings_cache is None:
            logger.info("Computing embeddings for local SQL knowledge base examples...")
            questions = [ex["question"] for ex in SQL_EXAMPLES]
            embeddings = EmbeddingService.get_batch_embeddings(questions)
            # Replace any failed embeddings with zeros of length 384
            cls._local_embeddings_cache = [
                emb if emb is not None else [0.0] * 384
                for emb in embeddings
            ]
        return cls._local_embeddings_cache

    @classmethod
    def retrieve_relevant_examples(
        cls,
        question: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-k most relevant SQL examples using cosine similarity.
        Tries Supabase pgvector search first; gracefully falls back to local knowledge base.
        Returns empty list if RAG is disabled, on embedding failure, or no examples pass threshold.
        """
        if not getattr(settings, "RAG_ENABLED", True):
            return []

        effective_top_k = top_k or getattr(settings, "RAG_TOP_K", 3)
        effective_threshold = threshold if threshold is not None else getattr(settings, "RAG_SIMILARITY_THRESHOLD", 0.4)

        # Step 1: Generate query embedding
        query_embedding = EmbeddingService.get_embedding(question)
        if query_embedding is None:
            logger.warning("Failed to generate embedding for question; skipping RAG retrieval.")
            return []

        # Step 2: Try Supabase pgvector search via match_sql_examples RPC
        supabase_results = cls._retrieve_from_supabase(query_embedding, effective_top_k, effective_threshold)
        if supabase_results is not None:
            return supabase_results

        # Step 3: Fallback to local vector search (in-memory cosine similarity)
        logger.info("Using local knowledge base for RAG similarity search fallback.")
        return cls._retrieve_from_local(query_embedding, effective_top_k, effective_threshold)

    @classmethod
    def _retrieve_from_supabase(
        cls,
        query_embedding: List[float],
        top_k: int,
        threshold: float
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Queries Supabase PostgreSQL pgvector via RPC 'match_sql_examples'.
        Returns None if Supabase client is unconfigured or call fails.
        """
        client = SupabaseService.get_client()
        if not client:
            return None

        try:
            rpc_res = client.rpc(
                "match_sql_examples",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": threshold,
                    "match_count": top_k
                }
            ).execute()

            if rpc_res and rpc_res.data is not None:
                results = []
                for row in rpc_res.data:
                    results.append({
                        "id": str(row.get("id")),
                        "question": row.get("question"),
                        "sql_query": row.get("sql_query"),
                        "category": row.get("category"),
                        "dialect": row.get("dialect", "general"),
                        "similarity": round(float(row.get("similarity", 0.0)), 4)
                    })
                return results
        except Exception as e:
            logger.warning(f"Supabase pgvector retrieval failed (falling back to local cache): {e}")
            return None

        return None

    @classmethod
    def _retrieve_from_local(
        cls,
        query_embedding: List[float],
        top_k: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Performs in-memory cosine similarity search against pre-curated SQL examples.
        Since embeddings are L2 normalized, cosine similarity equals dot product.
        """
        try:
            local_embs = cls._get_local_embeddings()
            if not local_embs:
                return []

            q_vec = np.array(query_embedding, dtype=np.float32)
            emb_matrix = np.array(local_embs, dtype=np.float32)

            # Dot product of normalized vectors = cosine similarity
            similarities = np.dot(emb_matrix, q_vec)

            scored_examples = []
            for idx, score in enumerate(similarities):
                float_score = float(score)
                if float_score >= threshold:
                    ex = SQL_EXAMPLES[idx]
                    scored_examples.append({
                        "id": ex["id"],
                        "question": ex["question"],
                        "sql_query": ex["sql_query"],
                        "category": ex.get("category"),
                        "dialect": ex.get("dialect", "general"),
                        "similarity": round(float_score, 4)
                    })

            # Sort descending by similarity
            scored_examples.sort(key=lambda x: x["similarity"], reverse=True)
            return scored_examples[:top_k]
        except Exception as e:
            logger.error(f"Local vector similarity search failed: {e}")
            return []

    @classmethod
    def format_examples_for_prompt(cls, examples: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved examples into a concise few-shot reference section
        for injection into the LLM system prompt.
        """
        if not examples:
            return ""

        lines = [
            "RELEVANT REFERENCE SQL PATTERNS (RETRIEVED VIA RAG):",
            "The following verified query patterns demonstrate effective syntax for questions similar to the user's.",
            "CRITICAL SCHEMA RULE: These examples are for structural and syntactic guidance ONLY.",
            "You MUST use table and column names matching the actual target schema (or reasonable conventions if schema-free).",
            "Do NOT blindly copy table or column names from these examples unless they exist in the target schema.",
            ""
        ]

        for i, ex in enumerate(examples, 1):
            category_tag = f" [{ex.get('category')}]" if ex.get("category") else ""
            sim_score = f" (relevance: {ex.get('similarity'):.2f})" if ex.get("similarity") is not None else ""
            lines.append(f"--- Example {i}{category_tag}{sim_score} ---")
            lines.append(f"Similar Question: {ex['question']}")
            lines.append(f"Example SQL: {ex['sql_query']}")
            lines.append("")

        return "\n".join(lines).strip()


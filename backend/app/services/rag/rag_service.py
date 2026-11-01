import logging
import math
import re
from collections import Counter
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.rag.knowledge_base import SQL_EXAMPLES

logger = logging.getLogger(__name__)

# Standard English stop words
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves"
}


def stem_token(word: str) -> str:
    """
    Lightweight rule-based suffix normalization for English vocabulary.
    Normalizes common plurals, verb forms, and noun variations without external NLP packages.
    """
    if len(word) > 4:
        if word.endswith("ies") and len(word) > 5:
            return word[:-3] + "y"
        if word.endswith("ing") and len(word) > 5:
            return word[:-3]
        if word.endswith("ed") and len(word) > 4:
            return word[:-2]
        if word.endswith("es") and len(word) > 4:
            return word[:-2]
        if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
            return word[:-1]
    return word


def tokenize(text: str) -> List[str]:
    """
    Normalizes and tokenizes text:
    - Lowercase normalization
    - Alphanumeric word extraction
    - Stop-word filtering
    - Suffix stemming for vocabulary alignment
    """
    if not text:
        return []
    words = re.findall(r"[a-z0-9]+", text.lower())
    tokens: List[str] = []
    for w in words:
        if w not in STOP_WORDS and len(w) > 1:
            tokens.append(w)
            stemmed = stem_token(w)
            if stemmed != w:
                tokens.append(stemmed)
        elif w.isdigit():
            tokens.append(w)
    return tokens


class BM25Index:
    """
    In-memory BM25 (Okapi) index built from pre-curated SQL examples.
    Zero external ML/PyTorch dependencies, ultra-fast (<1ms) indexing and retrieval.
    """
    def __init__(self, examples: List[Dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.examples = examples
        self.num_docs = len(examples)
        self.doc_tokens: List[List[str]] = []
        self.doc_term_freqs: List[Counter] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freq: Counter = Counter()
        self.idf: Dict[str, float] = {}

        self._build_index()

    def _build_index(self) -> None:
        if not self.examples:
            return

        total_length = 0
        for ex in self.examples:
            # Combine question and category for comprehensive semantic matching
            cat = ex.get("category", "").replace("_", " ")
            text = f"{ex['question']} {cat}"
            tokens = tokenize(text)
            self.doc_tokens.append(tokens)
            length = len(tokens)
            self.doc_lengths.append(length)
            total_length += length

            tf = Counter(tokens)
            self.doc_term_freqs.append(tf)
            for t in tf.keys():
                self.doc_freq[t] += 1

        self.avg_doc_len = total_length / self.num_docs if self.num_docs > 0 else 0.0

        # Precompute Lucene/BM25Okapi IDF: ln((N - n + 0.5) / (n + 0.5) + 1.0)
        # Always >= 0, guaranteeing positive relevance contributions
        for term, freq in self.doc_freq.items():
            self.idf[term] = math.log((self.num_docs - freq + 0.5) / (freq + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 3, min_score: float = 0.1) -> List[Dict[str, Any]]:
        """
        Scores and ranks documents against the query terms using BM25Okapi.
        Returns top-K results exceeding min_score. Returns empty list if no meaningful terms match.
        """
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # Check if any query token exists in index
        matched_any = any(t in self.doc_freq for t in query_tokens)
        if not matched_any:
            return []

        scored_results: List[Dict[str, Any]] = []

        for idx, ex in enumerate(self.examples):
            tf = self.doc_term_freqs[idx]
            dl = self.doc_lengths[idx]
            score = 0.0

            for t in query_tokens:
                if t in tf:
                    term_freq = tf[t]
                    idf_val = self.idf.get(t, 0.0)
                    # BM25Okapi term score
                    numerator = term_freq * (self.k1 + 1.0)
                    denominator = term_freq + self.k1 * (1.0 - self.b + self.b * (dl / self.avg_doc_len)) if self.avg_doc_len > 0 else 1.0
                    score += idf_val * (numerator / denominator)

            if score > 0.0 and score >= min_score:
                round_score = round(score, 4)
                scored_results.append({
                    "id": ex["id"],
                    "question": ex["question"],
                    "sql_query": ex["sql_query"],
                    "category": ex.get("category"),
                    "dialect": ex.get("dialect", "general"),
                    "similarity": round_score,
                    "score": round_score
                })

        # Rank by relevance score descending
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]


class RAGService:
    """
    Lightweight, Pure-Python BM25 Retrieval-Augmented Generation (RAG) Service.
    Retrieves the most semantically relevant SQL query examples for a user's question
    to guide the LLM with few-shot syntactic patterns without downloading heavy ML models.
    """
    _index: Optional[BM25Index] = None

    @classmethod
    def _get_index(cls) -> BM25Index:
        """
        Initializes and caches the BM25 index once on the pre-curated SQL knowledge base.
        Zero network latency, zero heavy PyTorch memory allocation.
        """
        if cls._index is None:
            logger.info("Initializing lightweight BM25 index on SQL knowledge base...")
            cls._index = BM25Index(SQL_EXAMPLES)
        return cls._index

    @classmethod
    def retrieve_relevant_examples(
        cls,
        question: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-k most relevant SQL examples using BM25 relevance scoring.
        Returns empty list if RAG is disabled, query is empty, or no examples meet threshold.
        """
        if not getattr(settings, "RAG_ENABLED", True):
            return []

        if not question or not question.strip():
            return []

        effective_top_k = top_k or getattr(settings, "RAG_TOP_K", 3)
        effective_threshold = (
            threshold
            if threshold is not None
            else getattr(settings, "RAG_MIN_SCORE", getattr(settings, "RAG_SIMILARITY_THRESHOLD", 0.1))
        )

        try:
            index = cls._get_index()
            results = index.search(
                query=question,
                top_k=effective_top_k,
                min_score=effective_threshold
            )
            return results
        except Exception as e:
            logger.error(f"BM25 RAG retrieval failed: {e}")
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

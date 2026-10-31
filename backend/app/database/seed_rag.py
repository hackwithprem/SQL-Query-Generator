"""
Seed script to populate the Supabase `sql_examples` table with verified
natural language questions, SQL queries, and 384-dimensional pgvector embeddings.
"""

import sys
import logging
from app.services.rag.knowledge_base import SQL_EXAMPLES
from app.services.rag.embedding_service import EmbeddingService
from app.services.supabase_service import SupabaseService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def seed_sql_examples() -> int:
    """
    Computes embeddings for all pre-curated examples and inserts them into Supabase.
    Returns the count of seeded examples.
    """
    client = SupabaseService.get_client()
    if not client:
        logger.warning("Supabase client is not configured. Skipping remote database seeding.")
        return 0

    logger.info(f"Preparing to seed {len(SQL_EXAMPLES)} SQL examples into Supabase pgvector...")

    questions = [ex["question"] for ex in SQL_EXAMPLES]
    logger.info("Computing 384-dimensional embeddings using sentence-transformers/all-MiniLM-L6-v2...")
    embeddings = EmbeddingService.get_batch_embeddings(questions)

    records = []
    for ex, emb in zip(SQL_EXAMPLES, embeddings):
        if emb is None:
            logger.warning(f"Failed to generate embedding for: {ex['question']}")
            continue
        records.append({
            "question": ex["question"],
            "sql_query": ex["sql_query"],
            "category": ex.get("category"),
            "dialect": ex.get("dialect", "general"),
            "embedding": emb
        })

    try:
        # Check if table exists or has existing records
        logger.info(f"Upserting {len(records)} records into public.sql_examples...")
        # Batch insert into Supabase
        batch_size = 20
        total_inserted = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            res = client.table("sql_examples").insert(batch).execute()
            count = len(res.data) if res.data else len(batch)
            total_inserted += count
            logger.info(f"Inserted batch {i // batch_size + 1} ({count} items)")

        logger.info(f"Successfully seeded {total_inserted} SQL examples into Supabase pgvector!")
        return total_inserted
    except Exception as e:
        logger.error(f"Failed to seed Supabase sql_examples table: {e}")
        logger.info(
            "Note: Ensure you have executed backend/app/database/rag_migration.sql "
            "in your Supabase SQL Editor first to enable pgvector and create sql_examples."
        )
        return 0

if __name__ == "__main__":
    count = seed_sql_examples()
    sys.exit(0 if count > 0 else 1)


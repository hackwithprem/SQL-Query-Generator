-- ==============================================================================
-- Supabase Migration: Enable pgvector and create sql_examples for RAG
-- ==============================================================================
-- This script enables vector similarity search on Supabase PostgreSQL
-- for the SQL Query Generator Example-Based RAG system.
-- ==============================================================================

-- 1. Enable the pgvector extension to work with embedding vectors
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the sql_examples table to store verified SQL patterns and embeddings
CREATE TABLE IF NOT EXISTS public.sql_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    sql_query TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    category VARCHAR(64),
    dialect VARCHAR(32) DEFAULT 'general',
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Create HNSW index for high-performance cosine distance search
CREATE INDEX IF NOT EXISTS idx_sql_examples_embedding 
ON public.sql_examples 
USING hnsw (embedding vector_cosine_ops);

-- 4. Enable Row Level Security (RLS)
ALTER TABLE public.sql_examples ENABLE ROW LEVEL SECURITY;

-- 5. Read access policy: Public read-only for verified SQL reference patterns
DROP POLICY IF EXISTS "Allow public read access to sql_examples" ON public.sql_examples;
CREATE POLICY "Allow public read access to sql_examples"
    ON public.sql_examples
    FOR SELECT
    USING (true);

-- Write access policy: Service role can manage examples
DROP POLICY IF EXISTS "Allow service role write access to sql_examples" ON public.sql_examples;
CREATE POLICY "Allow service role write access to sql_examples"
    ON public.sql_examples
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- 6. RPC Function for Cosine Similarity Search
CREATE OR REPLACE FUNCTION public.match_sql_examples (
    query_embedding VECTOR(384),
    match_threshold FLOAT DEFAULT 0.4,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    question TEXT,
    sql_query TEXT,
    category VARCHAR,
    dialect VARCHAR,
    similarity FLOAT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        se.id,
        se.question,
        se.sql_query,
        se.category,
        se.dialect,
        (1 - (se.embedding <=> query_embedding))::FLOAT AS similarity
    FROM public.sql_examples se
    WHERE 1 - (se.embedding <=> query_embedding) >= match_threshold
    ORDER BY se.embedding <=> query_embedding ASC
    LIMIT match_count;
END;
$$;


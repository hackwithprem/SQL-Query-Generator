-- ==============================================================================
-- Supabase Schema & Migration Script for SQL Query Generator
-- ==============================================================================
-- This script provisions the application tables with Row Level Security (RLS)
-- integrated with Supabase Auth (auth.users).
-- ==============================================================================

-- 1. Enable UUID Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Public User Profiles Table (Mirrors Supabase Auth Users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS on users table
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Users can view their own profile"
    ON public.users
    FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON public.users
    FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
    ON public.users
    FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Trigger to automatically create a public.users profile on new signup in auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, full_name, created_at, updated_at)
    VALUES (
        new.id,
        new.email,
        COALESCE(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)),
        now(),
        now()
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ==============================================================================
-- 3. Query History Table
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.query_history (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    natural_query TEXT NOT NULL,
    generated_sql TEXT NOT NULL,
    executed BOOLEAN DEFAULT FALSE NOT NULL,
    status VARCHAR(20) DEFAULT 'generated' NOT NULL, -- 'generated', 'executed', 'failed'
    execution_time_ms DOUBLE PRECISION,
    row_count INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_query_history_user_id ON public.query_history(user_id);
CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON public.query_history(created_at DESC);

-- Enable RLS on query_history
ALTER TABLE public.query_history ENABLE ROW LEVEL SECURITY;

-- RLS Policies for query_history
CREATE POLICY "Users can view their own query history"
    ON public.query_history
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own queries into history"
    ON public.query_history
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own query history"
    ON public.query_history
    FOR DELETE
    USING (auth.uid() = user_id);

-- ==============================================================================
-- 4. Uploaded Datasets Table
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.uploaded_datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    file_type VARCHAR(20) NOT NULL, -- 'csv' or 'excel'
    sheet_name VARCHAR(100),
    table_name VARCHAR(64) NOT NULL,
    row_count INTEGER NOT NULL,
    column_count INTEGER NOT NULL,
    columns_json JSONB NOT NULL,
    storage_path TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_uploaded_datasets_user_id ON public.uploaded_datasets(user_id);

-- Enable RLS on uploaded_datasets
ALTER TABLE public.uploaded_datasets ENABLE ROW LEVEL SECURITY;

-- RLS Policies for uploaded_datasets
CREATE POLICY "Users can view their own uploaded datasets"
    ON public.uploaded_datasets
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own datasets"
    ON public.uploaded_datasets
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own datasets"
    ON public.uploaded_datasets
    FOR DELETE
    USING (auth.uid() = user_id);

-- ==============================================================================
-- 5. Supabase Private Storage Policies (Bucket: 'private-datasets')
-- ==============================================================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('private-datasets', 'private-datasets', false)
ON CONFLICT (id) DO NOTHING;

-- Allow users to upload files only into their own user folder (e.g. user_id/filename)
CREATE POLICY "Users can upload files to their own storage folder"
    ON storage.objects
    FOR INSERT
    WITH CHECK (
        bucket_id = 'private-datasets'
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can read their own storage files"
    ON storage.objects
    FOR SELECT
    USING (
        bucket_id = 'private-datasets'
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can delete their own storage files"
    ON storage.objects
    FOR DELETE
    USING (
        bucket_id = 'private-datasets'
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

-- ==============================================================================
-- 6. Example-Based RAG: pgvector & SQL Examples Knowledge Base
-- ==============================================================================
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS public.sql_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    sql_query TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    category VARCHAR(64),
    dialect VARCHAR(32) DEFAULT 'general',
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sql_examples_embedding 
ON public.sql_examples 
USING hnsw (embedding vector_cosine_ops);

ALTER TABLE public.sql_examples ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access to sql_examples" ON public.sql_examples;
CREATE POLICY "Allow public read access to sql_examples"
    ON public.sql_examples
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Allow service role write access to sql_examples" ON public.sql_examples;
CREATE POLICY "Allow service role write access to sql_examples"
    ON public.sql_examples
    FOR ALL
    USING (true)
    WITH CHECK (true);

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

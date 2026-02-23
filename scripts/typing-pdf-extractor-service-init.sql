-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ENUM for extraction status
DO $$ BEGIN
    CREATE TYPE extraction_status_enum AS ENUM ('pending', 'processing', 'success', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create ENUM for embedding status
DO $$ BEGIN
    CREATE TYPE embedding_status_enum AS ENUM ('new', 'in progress', 'done', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Base table for PDFs
CREATE TABLE IF NOT EXISTS pdf (
    pdf_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename TEXT NOT NULL,
    bucket TEXT NOT NULL,
    extraction_status extraction_status_enum DEFAULT 'pending',
    error_message TEXT,
    embedding_status embedding_status_enum DEFAULT 'new',
    embedding_started_at TIMESTAMP WITH TIME ZONE,
    embedding_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(filename, bucket)
);

-- Metadata for PDFs
CREATE TABLE IF NOT EXISTS pdf_metadata (
    pdf_id UUID PRIMARY KEY REFERENCES pdf(pdf_id) ON DELETE CASCADE,
    creator TEXT,
    lineage TEXT,
    document_type TEXT,
    language TEXT,
    tags JSONB,
    extra JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Text chunks from PDFs
CREATE TABLE IF NOT EXISTS chunk_text (
    chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pdf_id UUID REFERENCES pdf(pdf_id) ON DELETE CASCADE,
    page_number INTEGER,
    chunk_index INTEGER,
    text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Registry to track internal state of files seen/processed by Airflow
CREATE TABLE IF NOT EXISTS airflow_file_registry (
    id SERIAL PRIMARY KEY,
    bucket TEXT NOT NULL,
    filename TEXT NOT NULL,
    status TEXT NOT NULL, -- 'pending', 'processed', 'failed'
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    UNIQUE(bucket, filename)
);

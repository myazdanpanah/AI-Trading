-- Initialize TimescaleDB and pgvector extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create indexes for better performance
-- These will be applied after Django migrations

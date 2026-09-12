-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Visual Memory: Stores CLIP embeddings of surveillance/context images
CREATE TABLE visual_memory (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    image_path TEXT,
    caption TEXT,
    embedding vector(512), -- Assuming CLIP ViT-B-32
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Skills Knowledge Base: Stores "How-to" patterns extracted by the LLM
CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    skill_name VARCHAR(255),
    content TEXT,
    embedding vector(384), -- Using sentence-transformers all-MiniLM-L6-v2
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

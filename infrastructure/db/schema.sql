-- 1. Enable the pgvector extension to work with embedding vectors
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Table to store different agent instances/profiles
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID, -- For future multi-tenant platform integration
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'STOPPED',
    vast_instance_id TEXT,
    chromium_profile_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Table to store recorded workflows as DAGs
CREATE TABLE blueprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    state_graph_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Table to store visual anchors for Semantic RAG
CREATE TABLE visual_anchors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blueprint_id UUID REFERENCES blueprints(id) ON DELETE CASCADE,
    semantic_label TEXT NOT NULL, -- e.g., 'Login Button', 'Search Bar'
    embedding vector(512), -- 512 dimensions for CLIP/BGE-M3 models
    bounding_box_relative JSONB, -- {width_pct: float, height_pct: float}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Create an index for faster vector similarity search (Optional but recommended for large datasets)
CREATE INDEX ON visual_anchors USING hnsw (embedding vector_cosine_ops);

-- RLS (Row Level Security) - Optional setup for future
-- ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE blueprints ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE visual_anchors ENABLE ROW LEVEL SECURITY;

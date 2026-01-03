-- RMM PostgreSQL Schema v1.0
-- Requires: PostgreSQL 15+, pgvector extension

-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- NODES TABLE
-- ============================================
CREATE TABLE nodes (
    id UUID PRIMARY KEY,
    vector vector(128) NOT NULL,  -- L2-normalized embedding
    energy DOUBLE PRECISION DEFAULT 0.0,
    last_update BIGINT DEFAULT EXTRACT(EPOCH FROM NOW())::BIGINT,
    significance REAL DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector search index (IVFFlat for Cosine distance)
-- Tune lists based on dataset size: sqrt(num_rows) to num_rows/1000
-- NOTE: IVFFlat requires training phase, good for <1M vectors
CREATE INDEX idx_nodes_vector_cosine ON nodes 
USING ivfflat (vector vector_cosine_ops) 
WITH (lists = 100);

-- ============================================
-- PRODUCTION ALTERNATIVE: HNSW Index
-- ============================================
-- For high-concurrency, low-latency production deployments (>1M vectors)
-- HNSW provides better recall and no training phase, but higher memory usage
-- Recommended for the "NVIDIA Strategy" at scale
--
-- DROP INDEX IF EXISTS idx_nodes_vector_cosine;
-- CREATE INDEX idx_nodes_vector_hnsw ON nodes 
-- USING hnsw (vector vector_cosine_ops) 
-- WITH (m = 16, ef_construction = 64);
--
-- Query-time tuning: SET hnsw.ef_search = 100;

-- Index for batch lookups
CREATE INDEX idx_nodes_last_update ON nodes (last_update DESC);

-- ============================================
-- EDGES TABLE
-- ============================================
CREATE TABLE edges (
    source UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    target UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    weight REAL NOT NULL CHECK (weight >= 0.0 AND weight <= 1.0),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (source, target)
);

-- CRITICAL: Covering index for fetch_neighbors
-- Enables "Index-Only Scan" for Top-N fan-out per hop
CREATE INDEX idx_edges_source_weight ON edges (source, weight DESC) 
INCLUDE (target, metadata);

-- Reverse lookup (for delete cascades and inverse queries)
CREATE INDEX idx_edges_target ON edges (target);

-- ============================================
-- COLD STORAGE TRACKING (Sleep Cycle)
-- ============================================
CREATE TABLE archived_nodes (
    id UUID PRIMARY KEY,
    s3_path TEXT NOT NULL,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    original_significance REAL NOT NULL,
    row_group_index INTEGER NOT NULL  -- Parquet row group for fast revive
);

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Batch upsert nodes (high-efficiency for WriteBackBuffer)
CREATE OR REPLACE FUNCTION upsert_nodes(
    p_nodes JSONB
) RETURNS INTEGER AS $$
DECLARE
    affected INTEGER;
BEGIN
    WITH input AS (
        SELECT 
            (elem->>'id')::UUID AS id,
            (elem->>'vector')::vector AS vector,
            (elem->>'energy')::DOUBLE PRECISION AS energy,
            (elem->>'last_update')::BIGINT AS last_update,
            (elem->>'significance')::REAL AS significance,
            (elem->'metadata') AS metadata
        FROM jsonb_array_elements(p_nodes) AS elem
    )
    INSERT INTO nodes (id, vector, energy, last_update, significance, metadata)
    SELECT id, vector, energy, last_update, significance, COALESCE(metadata, '{}')
    FROM input
    ON CONFLICT (id) DO UPDATE SET
        vector = EXCLUDED.vector,
        energy = EXCLUDED.energy,
        last_update = EXCLUDED.last_update,
        significance = EXCLUDED.significance,
        metadata = EXCLUDED.metadata
    WHERE EXCLUDED.last_update >= nodes.last_update;  -- Last-Write-Wins
    
    GET DIAGNOSTICS affected = ROW_COUNT;
    RETURN affected;
END;
$$ LANGUAGE plpgsql;

-- CTE-based neighbor fetch (single round-trip for batch)
CREATE OR REPLACE FUNCTION fetch_neighbors_batch(
    p_source_ids UUID[],
    p_min_weight REAL DEFAULT 0.05,
    p_max_per_source INTEGER DEFAULT 50
) RETURNS TABLE (
    source UUID,
    target UUID,
    weight REAL,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH sources AS (
        SELECT unnest(p_source_ids) AS source_id
    ),
    ranked AS (
        SELECT 
            e.source,
            e.target,
            e.weight,
            e.metadata,
            ROW_NUMBER() OVER (
                PARTITION BY e.source 
                ORDER BY e.weight DESC, e.target
            ) AS rn
        FROM edges e
        JOIN sources s ON e.source = s.source_id
        WHERE e.weight >= p_min_weight
    )
    SELECT r.source, r.target, r.weight, r.metadata
    FROM ranked r
    WHERE r.rn <= p_max_per_source
    ORDER BY r.source, r.weight DESC;
END;
$$ LANGUAGE plpgsql;

-- Cosine similarity vector search
CREATE OR REPLACE FUNCTION vector_search_cosine(
    p_query vector,
    p_top_k INTEGER DEFAULT 10
) RETURNS TABLE (
    id UUID,
    similarity REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT n.id, (1 - (n.vector <=> p_query))::REAL AS similarity
    FROM nodes n
    ORDER BY n.vector <=> p_query  -- Cosine distance (lower = more similar)
    LIMIT p_top_k;
END;
$$ LANGUAGE plpgsql;

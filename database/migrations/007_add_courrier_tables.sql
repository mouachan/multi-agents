-- Migration 007: Add Courrier & Colis Tables
-- Description: Creates tables for the Courrier & Colis reclamation processing
--              pipeline including tracking events, OCR documents, decisions,
--              processing logs, and a dedicated knowledge base.
-- Requires: pgvector extension, uuid-ossp extension

-- ============================================================================
-- EXTENSIONS
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- ENUM TYPES
-- ============================================================================
CREATE TYPE reclamation_status AS ENUM (
    'pending',
    'processing',
    'completed',
    'rejected',
    'manual_review',
    'escalated'
);

CREATE TYPE reclamation_type AS ENUM (
    'colis_endommage',
    'colis_perdu',
    'non_livre',
    'mauvaise_adresse',
    'vol_point_relais',
    'retard_livraison'
);

CREATE TYPE reclamation_decision_type AS ENUM (
    'rembourser',
    'reexpedier',
    'rejeter',
    'escalader'
);

CREATE TYPE tracking_event_type AS ENUM (
    'prise_en_charge',
    'tri',
    'en_cours_acheminement',
    'arrive_centre',
    'en_livraison',
    'livre',
    'avis_passage',
    'retour_expediteur',
    'incident',
    'point_relais'
);

-- ============================================================================
-- 1. RECLAMATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS reclamations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    numero_suivi VARCHAR(100),
    reclamation_number VARCHAR(100) UNIQUE NOT NULL,
    reclamation_type reclamation_type,
    client_nom VARCHAR(255),
    client_email VARCHAR(255),
    client_telephone VARCHAR(50),
    description TEXT,
    valeur_declaree DECIMAL(10, 2),
    photo_path TEXT,
    document_path TEXT,
    status reclamation_status DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    total_processing_time_ms INTEGER,
    is_archived BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    agent_logs JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reclamations_numero_suivi ON reclamations(numero_suivi);
CREATE INDEX idx_reclamations_reclamation_number ON reclamations(reclamation_number);
CREATE INDEX idx_reclamations_status ON reclamations(status);
CREATE INDEX idx_reclamations_reclamation_type ON reclamations(reclamation_type);
CREATE INDEX idx_reclamations_submitted_at ON reclamations(submitted_at);
CREATE INDEX idx_reclamations_is_archived ON reclamations(is_archived);
CREATE INDEX idx_reclamations_metadata ON reclamations USING GIN(metadata);

-- ============================================================================
-- 2. RECLAMATION DOCUMENTS TABLE (with OCR results and embeddings)
-- ============================================================================
CREATE TABLE IF NOT EXISTS reclamation_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reclamation_id UUID NOT NULL REFERENCES reclamations(id) ON DELETE CASCADE,
    document_type VARCHAR(100),
    file_path TEXT,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),

    -- OCR Results
    raw_ocr_text TEXT,
    raw_ocr_text_redacted TEXT,
    structured_data JSONB,
    ocr_confidence FLOAT,
    ocr_processed_at TIMESTAMP,

    -- Vector embedding for semantic search (768 dimensions for all-mpnet-base-v2)
    embedding vector(768),

    -- Metadata
    page_count INTEGER,
    language VARCHAR(10) DEFAULT 'fra',
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reclamation_documents_reclamation_id ON reclamation_documents(reclamation_id);
CREATE INDEX idx_reclamation_documents_embedding ON reclamation_documents USING hnsw (embedding vector_cosine_ops);

-- ============================================================================
-- 3. RECLAMATION DECISIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS reclamation_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reclamation_id UUID NOT NULL REFERENCES reclamations(id) ON DELETE CASCADE,

    -- Initial System Decision (automated)
    initial_decision reclamation_decision_type,
    initial_confidence FLOAT,
    initial_reasoning TEXT,
    initial_decided_at TIMESTAMP,

    -- Final Reviewer Decision (manual override)
    final_decision reclamation_decision_type,
    final_decision_by VARCHAR(255),
    final_decision_by_name VARCHAR(255),
    final_decision_at TIMESTAMP,
    final_decision_notes TEXT,

    -- Current effective decision
    decision reclamation_decision_type NOT NULL,
    confidence FLOAT,
    reasoning TEXT,

    -- LLM Details
    llm_model VARCHAR(100),

    -- Review
    requires_manual_review BOOLEAN DEFAULT FALSE,

    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reclamation_decisions_reclamation_id ON reclamation_decisions(reclamation_id);
CREATE INDEX idx_reclamation_decisions_decision ON reclamation_decisions(decision);
CREATE INDEX idx_reclamation_decisions_initial_decision ON reclamation_decisions(initial_decision);
CREATE INDEX idx_reclamation_decisions_final_decision ON reclamation_decisions(final_decision);
CREATE INDEX idx_reclamation_decisions_decided_at ON reclamation_decisions(decided_at);

-- ============================================================================
-- 4. RECLAMATION PROCESSING LOGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS reclamation_processing_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reclamation_id UUID NOT NULL REFERENCES reclamations(id) ON DELETE CASCADE,
    step VARCHAR(50),
    agent_name VARCHAR(100),

    -- Execution details
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    status VARCHAR(50),

    -- Input/Output
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,

    -- Metrics
    confidence_score FLOAT,
    tokens_used INTEGER,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reclamation_processing_logs_reclamation_id ON reclamation_processing_logs(reclamation_id);
CREATE INDEX idx_reclamation_processing_logs_step ON reclamation_processing_logs(step);
CREATE INDEX idx_reclamation_processing_logs_started_at ON reclamation_processing_logs(started_at);

-- ============================================================================
-- 5. TRACKING EVENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS tracking_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    numero_suivi VARCHAR(100) NOT NULL,
    event_type tracking_event_type,
    event_date TIMESTAMP NOT NULL,
    location VARCHAR(255),
    detail TEXT,
    code_postal VARCHAR(10),
    is_final BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tracking_events_numero_suivi ON tracking_events(numero_suivi);
CREATE INDEX idx_tracking_events_event_type ON tracking_events(event_type);
CREATE INDEX idx_tracking_events_event_date ON tracking_events(event_date);
CREATE INDEX idx_tracking_events_is_final ON tracking_events(is_final);

-- ============================================================================
-- 6. COURRIER KNOWLEDGE BASE TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS courrier_knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    tags TEXT[],

    -- Vector embedding for semantic search
    embedding vector(768),

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_courrier_knowledge_base_category ON courrier_knowledge_base(category);
CREATE INDEX idx_courrier_knowledge_base_tags ON courrier_knowledge_base USING GIN(tags);
CREATE INDEX idx_courrier_knowledge_base_is_active ON courrier_knowledge_base(is_active);
CREATE INDEX idx_courrier_knowledge_base_embedding ON courrier_knowledge_base USING hnsw (embedding vector_cosine_ops);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================
CREATE TRIGGER update_reclamations_updated_at BEFORE UPDATE ON reclamations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reclamation_documents_updated_at BEFORE UPDATE ON reclamation_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reclamation_decisions_updated_at BEFORE UPDATE ON reclamation_decisions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_courrier_knowledge_base_updated_at BEFORE UPDATE ON courrier_knowledge_base
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to search courrier knowledge base by embedding similarity
CREATE OR REPLACE FUNCTION search_courrier_knowledge(
    query_embedding vector(768),
    max_results INTEGER DEFAULT 5
)
RETURNS TABLE (
    kb_id UUID,
    title VARCHAR,
    content TEXT,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ckb.id,
        ckb.title,
        ckb.content,
        1 - (ckb.embedding <=> query_embedding) AS similarity_score
    FROM courrier_knowledge_base ckb
    WHERE ckb.is_active = TRUE
    ORDER BY ckb.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

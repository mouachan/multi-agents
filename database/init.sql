-- Claims Demo Database Initialization Script
-- PostgreSQL with pgvector extension for RAG capabilities

-- First, enable vector extension in postgres database (required by LlamaStack)
\c postgres
CREATE EXTENSION IF NOT EXISTS vector;

-- Then switch to claims_db and enable extensions
\c claims_db
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE claim_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'manual_review', 'pending_info');
CREATE TYPE processing_step AS ENUM ('ocr', 'guardrails', 'rag_retrieval', 'llm_decision', 'final_review');
CREATE TYPE decision_type AS ENUM ('approve', 'deny', 'manual_review');

-- ============================================================================
-- CLAIMS TABLE
-- ============================================================================
CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    claim_number VARCHAR(100) UNIQUE NOT NULL,
    claim_type VARCHAR(100),
    document_path TEXT NOT NULL,
    status claim_status DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    total_processing_time_ms INTEGER,
    is_archived BOOLEAN DEFAULT FALSE NOT NULL,
    metadata JSONB DEFAULT '{}',
    agent_logs JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_claims_user_id ON claims(user_id);
CREATE INDEX idx_claims_status ON claims(status);
CREATE INDEX idx_claims_submitted_at ON claims(submitted_at);
CREATE INDEX idx_claims_is_archived ON claims(is_archived);
CREATE INDEX idx_claims_metadata ON claims USING GIN(metadata);

-- ============================================================================
-- CLAIM DOCUMENTS TABLE (with OCR results and embeddings)
-- ============================================================================
CREATE TABLE claim_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    document_type VARCHAR(100),
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),

    -- OCR Results
    raw_ocr_text TEXT,
    structured_data JSONB,
    ocr_confidence FLOAT,
    ocr_processed_at TIMESTAMP,

    -- Vector embedding for semantic search (768 dimensions for all-mpnet-base-v2)
    embedding vector(768),

    -- Metadata
    page_count INTEGER,
    language VARCHAR(10) DEFAULT 'eng',
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_claim_documents_claim_id ON claim_documents(claim_id);
CREATE INDEX idx_claim_documents_embedding ON claim_documents USING ivfflat (embedding vector_cosine_ops);
ALTER TABLE claim_documents ADD CONSTRAINT claim_documents_claim_id_unique UNIQUE (claim_id);

-- ============================================================================
-- USER CONTRACTS TABLE (with embeddings for RAG)
-- ============================================================================
CREATE TABLE user_contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    contract_number VARCHAR(100) UNIQUE NOT NULL,
    contract_type VARCHAR(100),

    -- Contract details
    start_date DATE,
    end_date DATE,
    coverage_amount DECIMAL(15, 2),
    premium_amount DECIMAL(15, 2),
    payment_frequency VARCHAR(50),

    -- Contract content
    full_text TEXT,
    key_terms JSONB,
    coverage_details JSONB,
    exclusions JSONB,

    -- Vector embedding for RAG retrieval
    embedding vector(768),

    -- Status
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_contracts_user_id ON user_contracts(user_id);
CREATE INDEX idx_user_contracts_is_active ON user_contracts(is_active);
CREATE INDEX idx_user_contracts_embedding ON user_contracts USING ivfflat (embedding vector_cosine_ops);

-- ============================================================================
-- PROCESSING LOGS TABLE
-- ============================================================================
CREATE TABLE processing_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    step processing_step NOT NULL,
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

CREATE INDEX idx_processing_logs_claim_id ON processing_logs(claim_id);
CREATE INDEX idx_processing_logs_step ON processing_logs(step);
CREATE INDEX idx_processing_logs_started_at ON processing_logs(started_at);

-- ============================================================================
-- GUARDRAILS DETECTIONS TABLE
-- ============================================================================
CREATE TABLE guardrails_detections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    detection_type VARCHAR(100) NOT NULL,  -- ssn, credit_card, email, etc.
    severity VARCHAR(20),  -- low, medium, high

    -- Detection details
    original_text TEXT,  -- DO NOT store actual PII, only for audit
    redacted_text TEXT,
    text_span_start INTEGER,
    text_span_end INTEGER,

    -- Action taken
    action_taken VARCHAR(50),  -- flag, redact, block
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_guardrails_claim_id ON guardrails_detections(claim_id);
CREATE INDEX idx_guardrails_detection_type ON guardrails_detections(detection_type);
CREATE INDEX idx_guardrails_severity ON guardrails_detections(severity);

-- ============================================================================
-- CLAIM DECISIONS TABLE (with system and reviewer decision history)
-- ============================================================================
CREATE TABLE claim_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,

    -- Initial System Decision (automated)
    initial_decision decision_type NOT NULL,
    initial_confidence FLOAT,
    initial_reasoning TEXT,
    initial_decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Final Reviewer Decision (manual override)
    final_decision decision_type,
    final_decision_by VARCHAR(255),
    final_decision_by_name VARCHAR(255),
    final_decision_at TIMESTAMP,
    final_decision_notes TEXT,

    -- Legacy fields for backwards compatibility
    decision decision_type NOT NULL,
    confidence FLOAT,
    reasoning TEXT,

    -- Supporting evidence
    relevant_policies JSONB,
    similar_claims JSONB,
    user_contract_info JSONB,

    -- LLM Details
    llm_model VARCHAR(100),
    llm_prompt TEXT,
    llm_response TEXT,

    -- Review
    requires_manual_review BOOLEAN DEFAULT false,
    manual_review_notes TEXT,
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP,

    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_claim_decisions_claim_id ON claim_decisions(claim_id);
CREATE INDEX idx_claim_decisions_decision ON claim_decisions(decision);
CREATE INDEX idx_claim_decisions_initial_decision ON claim_decisions(initial_decision);
CREATE INDEX idx_claim_decisions_final_decision ON claim_decisions(final_decision);
CREATE INDEX idx_claim_decisions_decided_at ON claim_decisions(decided_at);

-- ============================================================================
-- KNOWLEDGE BASE TABLE (for policies, procedures, FAQs)
-- ============================================================================
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    tags TEXT[],

    -- Vector embedding for semantic search
    embedding vector(768),

    -- Versioning
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    effective_date DATE,
    expiry_date DATE,

    -- Metadata
    source VARCHAR(255),
    author VARCHAR(255),
    last_reviewed DATE,
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_knowledge_base_category ON knowledge_base(category);
CREATE INDEX idx_knowledge_base_tags ON knowledge_base USING GIN(tags);
CREATE INDEX idx_knowledge_base_is_active ON knowledge_base(is_active);
CREATE INDEX idx_knowledge_base_embedding ON knowledge_base USING ivfflat (embedding vector_cosine_ops);

-- ============================================================================
-- USERS TABLE (basic user info)
-- ============================================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    full_name VARCHAR(255),
    date_of_birth DATE,
    phone_number VARCHAR(50),
    address JSONB,

    -- Account status
    is_active BOOLEAN DEFAULT true,
    account_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_claims_updated_at BEFORE UPDATE ON claims
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_claim_documents_updated_at BEFORE UPDATE ON claim_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_contracts_updated_at BEFORE UPDATE ON user_contracts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_claim_decisions_updated_at BEFORE UPDATE ON claim_decisions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_base_updated_at BEFORE UPDATE ON knowledge_base
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to search similar claims by embedding
CREATE OR REPLACE FUNCTION search_similar_claims(
    query_embedding vector(768),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    claim_id UUID,
    claim_number VARCHAR,
    similarity_score FLOAT,
    ocr_text TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.claim_number,
        1 - (cd.embedding <=> query_embedding) AS similarity_score,
        cd.raw_ocr_text
    FROM claim_documents cd
    JOIN claims c ON cd.claim_id = c.id
    WHERE 1 - (cd.embedding <=> query_embedding) >= similarity_threshold
    ORDER BY cd.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Function to search knowledge base
CREATE OR REPLACE FUNCTION search_knowledge_base(
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
        kb.id,
        kb.title,
        kb.content,
        1 - (kb.embedding <=> query_embedding) AS similarity_score
    FROM knowledge_base kb
    WHERE kb.is_active = true
    ORDER BY kb.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- GRANTS (adjust based on your user setup)
-- ============================================================================
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO claims_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO claims_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO claims_user;

-- ============================================================================
-- TENDER (APPELS D'OFFRES) TABLES
-- ============================================================================

-- Tenders main table
CREATE TABLE tenders (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id               VARCHAR(255),
    tender_number           VARCHAR(100) UNIQUE,
    tender_type             VARCHAR(100),
    document_path           TEXT,
    status                  VARCHAR(50) DEFAULT 'pending',
    submitted_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at            TIMESTAMP,
    total_processing_time_ms INTEGER,
    is_archived             BOOLEAN DEFAULT FALSE,
    metadata                JSONB DEFAULT '{}',
    agent_logs              JSONB DEFAULT '[]',
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tenders_entity_id ON tenders(entity_id);
CREATE INDEX idx_tenders_status ON tenders(status);
CREATE INDEX idx_tenders_submitted_at ON tenders(submitted_at);
CREATE INDEX idx_tenders_is_archived ON tenders(is_archived);

-- Tender documents (OCR results + embeddings)
CREATE TABLE tender_documents (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tender_id         UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    document_type     VARCHAR(100),
    file_path         TEXT,
    file_size_bytes   BIGINT,
    mime_type         VARCHAR(100),
    raw_ocr_text      TEXT,
    structured_data   JSONB,
    ocr_confidence    FLOAT,
    ocr_processed_at  TIMESTAMP,
    embedding         vector(768),
    page_count        INTEGER,
    language          VARCHAR(10) DEFAULT 'fra',
    metadata          JSONB DEFAULT '{}',
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tender_documents_tender_id ON tender_documents(tender_id);
CREATE INDEX idx_tender_documents_embedding ON tender_documents USING ivfflat (embedding vector_cosine_ops);

-- Tender decisions (Go/No-Go)
CREATE TABLE tender_decisions (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tender_id               UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    initial_decision        VARCHAR(50),
    initial_confidence      FLOAT,
    initial_reasoning       TEXT,
    initial_decided_at      TIMESTAMP,
    final_decision          VARCHAR(50),
    final_decision_by       VARCHAR(255),
    final_decision_by_name  VARCHAR(255),
    final_decision_at       TIMESTAMP,
    final_decision_notes    TEXT,
    decision                VARCHAR(50),
    confidence              FLOAT,
    reasoning               TEXT,
    risk_analysis           JSONB,
    similar_references      JSONB,
    historical_ao_analysis  JSONB,
    internal_capabilities   JSONB,
    llm_model               VARCHAR(100),
    requires_manual_review  BOOLEAN DEFAULT FALSE,
    decided_at              TIMESTAMP,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tender_decisions_tender_id ON tender_decisions(tender_id);

-- Tender processing logs
CREATE TABLE tender_processing_logs (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tender_id        UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    step             VARCHAR(50),
    agent_name       VARCHAR(100),
    started_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at     TIMESTAMP,
    duration_ms      INTEGER,
    status           VARCHAR(50),
    input_data       JSONB,
    output_data      JSONB,
    error_message    TEXT,
    confidence_score FLOAT,
    tokens_used      INTEGER,
    metadata         JSONB DEFAULT '{}',
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tender_processing_logs_tender_id ON tender_processing_logs(tender_id);

-- Vinci references (past project references)
CREATE TABLE vinci_references (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference_number   VARCHAR(100) UNIQUE,
    project_name       VARCHAR(500),
    maitre_ouvrage     VARCHAR(255),
    nature_travaux     VARCHAR(255),
    montant            DECIMAL(15, 2),
    date_debut         DATE,
    date_fin           DATE,
    region             VARCHAR(100),
    description        TEXT,
    certifications_used JSONB,
    key_metrics        JSONB,
    embedding          vector(768),
    is_active          BOOLEAN DEFAULT TRUE,
    metadata           JSONB DEFAULT '{}',
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vinci_references_embedding ON vinci_references USING ivfflat (embedding vector_cosine_ops);

-- Vinci capabilities (certifications, resources, equipment)
CREATE TABLE vinci_capabilities (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category     VARCHAR(100),
    name         VARCHAR(255),
    description  TEXT,
    valid_until  DATE,
    region       VARCHAR(100),
    availability VARCHAR(50),
    details      JSONB,
    embedding    vector(768),
    is_active    BOOLEAN DEFAULT TRUE,
    metadata     JSONB DEFAULT '{}',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vinci_capabilities_category ON vinci_capabilities(category);

-- Historical tenders (past won/lost AOs)
CREATE TABLE historical_tenders (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ao_number         VARCHAR(100) UNIQUE,
    maitre_ouvrage    VARCHAR(255),
    nature_travaux    VARCHAR(255),
    montant_estime    DECIMAL(15, 2),
    montant_propose   DECIMAL(15, 2),
    resultat          VARCHAR(50),
    raison_resultat   TEXT,
    date_soumission   DATE,
    criteres_attribution JSONB,
    note_technique    FLOAT,
    note_prix         FLOAT,
    region            VARCHAR(100),
    description       TEXT,
    embedding         vector(768),
    is_active         BOOLEAN DEFAULT TRUE,
    metadata          JSONB DEFAULT '{}',
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Triggers for tender tables
CREATE TRIGGER update_tenders_updated_at BEFORE UPDATE ON tenders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tender_documents_updated_at BEFORE UPDATE ON tender_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tender_decisions_updated_at BEFORE UPDATE ON tender_decisions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vinci_references_updated_at BEFORE UPDATE ON vinci_references
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vinci_capabilities_updated_at BEFORE UPDATE ON vinci_capabilities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_historical_tenders_updated_at BEFORE UPDATE ON historical_tenders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Vector similarity search functions for tenders

CREATE OR REPLACE FUNCTION search_similar_references(
    query_embedding vector(768),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    ref_id UUID,
    reference_number VARCHAR,
    project_name VARCHAR,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        vr.id,
        vr.reference_number,
        vr.project_name,
        1 - (vr.embedding <=> query_embedding) AS similarity_score
    FROM vinci_references vr
    WHERE vr.is_active = TRUE
      AND vr.embedding IS NOT NULL
      AND 1 - (vr.embedding <=> query_embedding) >= similarity_threshold
    ORDER BY vr.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION search_historical_tenders(
    query_embedding vector(768),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    ht_id UUID,
    ao_number VARCHAR,
    resultat VARCHAR,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ht.id,
        ht.ao_number,
        ht.resultat,
        1 - (ht.embedding <=> query_embedding) AS similarity_score
    FROM historical_tenders ht
    WHERE ht.is_active = TRUE
      AND ht.embedding IS NOT NULL
      AND 1 - (ht.embedding <=> query_embedding) >= similarity_threshold
    ORDER BY ht.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMPLETION
-- ============================================================================
-- not sure why current_database() shows as a syntax error... looks legit AFAIU
-- no big deal, can do without
-- COMMENT ON DATABASE current_database() IS 'Claims Processing Demo Database with pgvector for RAG';

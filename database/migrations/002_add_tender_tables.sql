-- Migration 002: Add Tender (Appel d'Offres) Tables
-- Description: Creates tables for tender processing pipeline including
--              OCR documents, Go/No-Go decisions, processing logs,
--              Vinci references, capabilities, and historical tenders.
-- Requires: pgvector extension

-- ============================================================
-- Extension
-- ============================================================
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- 1. tenders — main tender entity
-- ============================================================
CREATE TABLE IF NOT EXISTS tenders (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id               VARCHAR(255),
    tender_number           VARCHAR(100) UNIQUE,
    tender_type             VARCHAR(100),
    document_path           TEXT,
    status                  VARCHAR(50) DEFAULT 'pending',
    submitted_at            TIMESTAMPTZ,
    processed_at            TIMESTAMPTZ,
    total_processing_time_ms INT,
    is_archived             BOOLEAN DEFAULT FALSE,
    metadata                JSONB DEFAULT '{}',
    agent_logs              JSONB DEFAULT '[]',
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenders_entity_id    ON tenders (entity_id);
CREATE INDEX IF NOT EXISTS idx_tenders_status       ON tenders (status);
CREATE INDEX IF NOT EXISTS idx_tenders_submitted_at ON tenders (submitted_at);
CREATE INDEX IF NOT EXISTS idx_tenders_is_archived  ON tenders (is_archived);

-- ============================================================
-- 2. tender_documents — OCR results per document
-- ============================================================
CREATE TABLE IF NOT EXISTS tender_documents (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id         UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    document_type     VARCHAR(100),
    file_path         TEXT,
    file_size_bytes   BIGINT,
    mime_type         VARCHAR(100),
    raw_ocr_text      TEXT,
    structured_data   JSONB,
    ocr_confidence    FLOAT,
    ocr_processed_at  TIMESTAMPTZ,
    embedding         vector(768),
    page_count        INT,
    language          VARCHAR(10) DEFAULT 'fra',
    metadata          JSONB DEFAULT '{}',
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tender_documents_tender_id ON tender_documents (tender_id);
CREATE INDEX IF NOT EXISTS idx_tender_documents_embedding ON tender_documents
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================
-- 3. tender_decisions — Go / No-Go decisions
-- ============================================================
CREATE TABLE IF NOT EXISTS tender_decisions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id               UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    initial_decision        VARCHAR(50),
    initial_confidence      FLOAT,
    initial_reasoning       TEXT,
    initial_decided_at      TIMESTAMPTZ,
    final_decision          VARCHAR(50),
    final_decision_by       VARCHAR(255),
    final_decision_by_name  VARCHAR(255),
    final_decision_at       TIMESTAMPTZ,
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
    decided_at              TIMESTAMPTZ,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 4. tender_processing_logs — per-step agent logs
-- ============================================================
CREATE TABLE IF NOT EXISTS tender_processing_logs (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id        UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    step             VARCHAR(50),
    agent_name       VARCHAR(100),
    started_at       TIMESTAMPTZ,
    completed_at     TIMESTAMPTZ,
    duration_ms      INT,
    status           VARCHAR(50),
    input_data       JSONB,
    output_data      JSONB,
    error_message    TEXT,
    confidence_score FLOAT,
    tokens_used      INT,
    metadata         JSONB DEFAULT '{}',
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 5. vinci_references — past project references
-- ============================================================
CREATE TABLE IF NOT EXISTS vinci_references (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_number   VARCHAR(100) UNIQUE,
    project_name       VARCHAR(500),
    maitre_ouvrage     VARCHAR(255),
    nature_travaux     VARCHAR(255),
    montant            NUMERIC(15, 2),
    date_debut         DATE,
    date_fin           DATE,
    region             VARCHAR(100),
    description        TEXT,
    certifications_used JSONB,
    key_metrics        JSONB,
    embedding          vector(768),
    is_active          BOOLEAN DEFAULT TRUE,
    metadata           JSONB DEFAULT '{}',
    created_at         TIMESTAMPTZ DEFAULT NOW(),
    updated_at         TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 6. vinci_capabilities — certifications & resources
-- ============================================================
CREATE TABLE IF NOT EXISTS vinci_capabilities (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vinci_capabilities_category ON vinci_capabilities (category);

-- ============================================================
-- 7. historical_tenders — past won / lost AOs
-- ============================================================
CREATE TABLE IF NOT EXISTS historical_tenders (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ao_number         VARCHAR(100) UNIQUE,
    maitre_ouvrage    VARCHAR(255),
    nature_travaux    VARCHAR(255),
    montant_estime    NUMERIC(15, 2),
    montant_propose   NUMERIC(15, 2),
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
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Vector similarity search functions
-- ============================================================

-- Search similar Vinci references by embedding
CREATE OR REPLACE FUNCTION search_similar_references(
    query_embedding  vector(768),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results      INT DEFAULT 10
)
RETURNS TABLE (
    id               UUID,
    reference_number VARCHAR(100),
    project_name     VARCHAR(500),
    maitre_ouvrage   VARCHAR(255),
    nature_travaux   VARCHAR(255),
    montant          NUMERIC(15, 2),
    date_debut       DATE,
    date_fin         DATE,
    region           VARCHAR(100),
    description      TEXT,
    certifications_used JSONB,
    key_metrics      JSONB,
    similarity       FLOAT
)
LANGUAGE sql STABLE
AS $$
    SELECT
        vr.id,
        vr.reference_number,
        vr.project_name,
        vr.maitre_ouvrage,
        vr.nature_travaux,
        vr.montant,
        vr.date_debut,
        vr.date_fin,
        vr.region,
        vr.description,
        vr.certifications_used,
        vr.key_metrics,
        1 - (vr.embedding <=> query_embedding)::FLOAT AS similarity
    FROM vinci_references vr
    WHERE vr.is_active = TRUE
      AND vr.embedding IS NOT NULL
      AND 1 - (vr.embedding <=> query_embedding) >= similarity_threshold
    ORDER BY vr.embedding <=> query_embedding
    LIMIT max_results;
$$;

-- Search historical tenders by embedding
CREATE OR REPLACE FUNCTION search_historical_tenders(
    query_embedding  vector(768),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results      INT DEFAULT 10
)
RETURNS TABLE (
    id               UUID,
    ao_number        VARCHAR(100),
    maitre_ouvrage   VARCHAR(255),
    nature_travaux   VARCHAR(255),
    montant_estime   NUMERIC(15, 2),
    montant_propose  NUMERIC(15, 2),
    resultat         VARCHAR(50),
    raison_resultat  TEXT,
    date_soumission  DATE,
    criteres_attribution JSONB,
    note_technique   FLOAT,
    note_prix        FLOAT,
    region           VARCHAR(100),
    description      TEXT,
    similarity       FLOAT
)
LANGUAGE sql STABLE
AS $$
    SELECT
        ht.id,
        ht.ao_number,
        ht.maitre_ouvrage,
        ht.nature_travaux,
        ht.montant_estime,
        ht.montant_propose,
        ht.resultat,
        ht.raison_resultat,
        ht.date_soumission,
        ht.criteres_attribution,
        ht.note_technique,
        ht.note_prix,
        ht.region,
        ht.description,
        1 - (ht.embedding <=> query_embedding)::FLOAT AS similarity
    FROM historical_tenders ht
    WHERE ht.is_active = TRUE
      AND ht.embedding IS NOT NULL
      AND 1 - (ht.embedding <=> query_embedding) >= similarity_threshold
    ORDER BY ht.embedding <=> query_embedding
    LIMIT max_results;
$$;

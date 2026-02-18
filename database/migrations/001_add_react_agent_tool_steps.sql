-- Migration: Add ReActAgent tool step names to processing_step ENUM
-- Date: 2025-12-24
-- Description: Adds tool names used by ReActAgent to the processing_step ENUM

-- Add new step values to the processing_step ENUM
ALTER TYPE processing_step ADD VALUE IF NOT EXISTS 'ocr_document';
ALTER TYPE processing_step ADD VALUE IF NOT EXISTS 'retrieve_user_info';
ALTER TYPE processing_step ADD VALUE IF NOT EXISTS 'retrieve_similar_claims';
ALTER TYPE processing_step ADD VALUE IF NOT EXISTS 'make_final_decision';

-- Note: PostgreSQL ENUM values cannot be removed, only added
-- The old values ('ocr', 'guardrails', 'rag_retrieval', 'llm_decision', 'final_review')
-- remain available for backward compatibility

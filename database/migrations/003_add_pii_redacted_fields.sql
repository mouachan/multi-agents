-- Migration 003: Add PII redacted fields for dual-level storage
-- Stores redacted versions alongside originals for safe API responses

-- Users table - redacted PII fields
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_redacted VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name_redacted VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number_redacted VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS date_of_birth_redacted VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS address_redacted JSONB;

-- Claim documents - redacted OCR text
ALTER TABLE claim_documents ADD COLUMN IF NOT EXISTS raw_ocr_text_redacted TEXT;

-- Claim decisions - redacted reasoning
ALTER TABLE claim_decisions ADD COLUMN IF NOT EXISTS reasoning_redacted TEXT;

-- Tender documents - redacted OCR text
ALTER TABLE tender_documents ADD COLUMN IF NOT EXISTS raw_ocr_text_redacted TEXT;

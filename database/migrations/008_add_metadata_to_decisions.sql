-- Add metadata JSONB column to all decision tables for bilingual support
-- (reasoning_en, etc.)

ALTER TABLE claim_decisions ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
ALTER TABLE tender_decisions ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
ALTER TABLE reclamation_decisions ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

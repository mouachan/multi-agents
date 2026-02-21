-- Add token_usage JSONB column to chat_messages for tracking LLM token consumption
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS token_usage JSONB;

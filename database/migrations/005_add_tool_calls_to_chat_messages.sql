-- Add tool_calls JSONB column to chat_messages for persisting tool call metadata
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS tool_calls JSONB;

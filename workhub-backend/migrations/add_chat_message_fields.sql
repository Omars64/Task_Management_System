-- Migration to add edit/delete fields to chat_messages table
-- Run this migration to support message editing and deletion features

-- Add columns for edit/delete functionality
ALTER TABLE chat_messages 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS is_edited BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS deleted_for_sender BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS deleted_for_recipient BOOLEAN DEFAULT FALSE;

-- Update existing records to have default values
UPDATE chat_messages 
SET is_edited = FALSE, 
    is_deleted = FALSE, 
    deleted_for_sender = FALSE, 
    deleted_for_recipient = FALSE 
WHERE is_edited IS NULL OR is_deleted IS NULL OR deleted_for_sender IS NULL OR deleted_for_recipient IS NULL;


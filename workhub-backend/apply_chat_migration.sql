-- Quick SQL migration for chat_messages table
-- Run this directly in your PostgreSQL database or via psql

-- Add new columns for chat message edit/delete features
ALTER TABLE chat_messages 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS is_edited BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS deleted_for_sender BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS deleted_for_recipient BOOLEAN DEFAULT FALSE;

-- Set default values for existing rows
UPDATE chat_messages 
SET 
  is_edited = COALESCE(is_edited, FALSE),
  is_deleted = COALESCE(is_deleted, FALSE),
  deleted_for_sender = COALESCE(deleted_for_sender, FALSE),
  deleted_for_recipient = COALESCE(deleted_for_recipient, FALSE)
WHERE is_edited IS NULL 
   OR is_deleted IS NULL 
   OR deleted_for_sender IS NULL 
   OR deleted_for_recipient IS NULL;

-- Verify the columns were added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'chat_messages'
ORDER BY ordinal_position;


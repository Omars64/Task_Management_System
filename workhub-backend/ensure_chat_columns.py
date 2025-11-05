from app import create_app
from models import db
from sqlalchemy import text


def ensure_chat_columns():
	app = create_app()
	with app.app_context():
		with db.engine.begin() as conn:
			# Add columns if missing (SQL Server compatible)
			conn.execute(text(
				"""
				IF NOT EXISTS (
					SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
					WHERE TABLE_NAME='chat_messages' AND COLUMN_NAME='updated_at'
				)
				BEGIN ALTER TABLE chat_messages ADD updated_at DATETIME NULL; END;
				"""
			))
			conn.execute(text(
				"""
				IF NOT EXISTS (
					SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
					WHERE TABLE_NAME='chat_messages' AND COLUMN_NAME='is_edited'
				)
				BEGIN ALTER TABLE chat_messages ADD is_edited BIT NOT NULL DEFAULT(0); END;
				"""
			))
			conn.execute(text(
				"""
				IF NOT EXISTS (
					SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
					WHERE TABLE_NAME='chat_messages' AND COLUMN_NAME='is_deleted'
				)
				BEGIN ALTER TABLE chat_messages ADD is_deleted BIT NOT NULL DEFAULT(0); END;
				"""
			))
			conn.execute(text(
				"""
				IF NOT EXISTS (
					SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
					WHERE TABLE_NAME='chat_messages' AND COLUMN_NAME='deleted_for_sender'
				)
				BEGIN ALTER TABLE chat_messages ADD deleted_for_sender BIT NOT NULL DEFAULT(0); END;
				"""
			))
			conn.execute(text(
				"""
				IF NOT EXISTS (
					SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
					WHERE TABLE_NAME='chat_messages' AND COLUMN_NAME='deleted_for_recipient'
				)
				BEGIN ALTER TABLE chat_messages ADD deleted_for_recipient BIT NOT NULL DEFAULT(0); END;
				"""
			))
			# Ensure Unicode for emojis
			conn.execute(text(
				"""
				IF EXISTS (
					SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
					WHERE TABLE_NAME='chat_messages' AND COLUMN_NAME='content' AND DATA_TYPE <> 'nvarchar'
				)
				BEGIN ALTER TABLE chat_messages ALTER COLUMN content NVARCHAR(MAX) NOT NULL; END;
				"""
			))
		print("OK: chat_messages columns ensured (emoji-safe)")


if __name__ == "__main__":
	ensure_chat_columns()

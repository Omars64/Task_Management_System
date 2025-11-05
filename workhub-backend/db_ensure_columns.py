from app import create_app
from models import db
from sqlalchemy import text


def main():
    app = create_app()
    with app.app_context():
        with db.engine.begin() as conn:
            conn.execute(text(
                """
                IF NOT EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='tasks' AND COLUMN_NAME='project_id'
                ) AND NOT EXISTS (
                    SELECT 1 FROM sys.columns c
                    JOIN sys.objects o ON o.object_id = c.object_id
                    WHERE o.name = 'tasks' AND c.name = 'project_id'
                )
                BEGIN
                    IF OBJECT_ID('dbo.tasks', 'U') IS NOT NULL
                        ALTER TABLE dbo.tasks ADD project_id INT NULL;
                    ELSE IF OBJECT_ID('tasks', 'U') IS NOT NULL
                        ALTER TABLE tasks ADD project_id INT NULL;
                END
                """
            ))
            conn.execute(text(
                """
                IF NOT EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='tasks' AND COLUMN_NAME='sprint_id'
                ) AND NOT EXISTS (
                    SELECT 1 FROM sys.columns c
                    JOIN sys.objects o ON o.object_id = c.object_id
                    WHERE o.name = 'tasks' AND c.name = 'sprint_id'
                )
                BEGIN
                    IF OBJECT_ID('dbo.tasks', 'U') IS NOT NULL
                        ALTER TABLE dbo.tasks ADD sprint_id INT NULL;
                    ELSE IF OBJECT_ID('tasks', 'U') IS NOT NULL
                        ALTER TABLE tasks ADD sprint_id INT NULL;
                END
                """
            ))
        print("OK: Columns ensured")


if __name__ == "__main__":
    main()



"""Database migration script to add bruteforce_enabled column."""

from pathlib import Path
from src.database import get_db, engine
from src.database.models import Base
import sqlalchemy


def migrate_database():
    """Migrate database to add bruteforce_enabled column if it doesn't exist."""
    print("[*] Checking database schema...")

    # Check if bruteforce_enabled column exists
    inspector = sqlalchemy.inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('scans')]

    if 'bruteforce_enabled' not in columns:
        print("[*] Adding bruteforce_enabled column to scans table...")

        # Add column with ALTER TABLE
        with engine.connect() as conn:
            # SQLite syntax for adding column
            conn.execute(sqlalchemy.text(
                "ALTER TABLE scans ADD COLUMN bruteforce_enabled BOOLEAN DEFAULT 0"
            ))
            conn.commit()

        print("[+] Migration completed: bruteforce_enabled column added")
    else:
        print("[OK] Database schema is up to date")


if __name__ == '__main__':
    print("=" * 60)
    print("Database Migration Script")
    print("=" * 60)

    try:
        migrate_database()
        print("\n[+] Migration successful!")
    except Exception as e:
        print(f"\n[!] Migration failed: {e}")
        import traceback
        traceback.print_exc()

"""Database migration script to add missing columns."""

import sys
sys.path.insert(0, 'C:/Users/LENOVO/Tool/API_Scanner')

from pathlib import Path
from src.database import get_db, engine
from src.database.models import Base
import sqlalchemy


def migrate_database():
    """Migrate database to add missing columns if they don't exist."""
    print("[*] Checking database schema...")
    inspector = sqlalchemy.inspect(engine)

    # Migration 1: Add bruteforce_enabled to scans table
    scans_columns = [col['name'] for col in inspector.get_columns('scans')]
    if 'bruteforce_enabled' not in scans_columns:
        print("[*] Adding bruteforce_enabled column to scans table...")
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text(
                "ALTER TABLE scans ADD COLUMN bruteforce_enabled BOOLEAN DEFAULT 0"
            ))
            conn.commit()
        print("[+] Migration completed: bruteforce_enabled column added")
    else:
        print("[OK] scans.bruteforce_enabled already exists")

    # Migration 2: Add curl_command to endpoints table
    endpoints_columns = [col['name'] for col in inspector.get_columns('endpoints')]
    if 'curl_command' not in endpoints_columns:
        print("[*] Adding curl_command column to endpoints table...")
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text(
                "ALTER TABLE endpoints ADD COLUMN curl_command TEXT"
            ))
            conn.commit()
        print("[+] Migration completed: curl_command column added")
    else:
        print("[OK] endpoints.curl_command already exists")

    print("[OK] All migrations completed")


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

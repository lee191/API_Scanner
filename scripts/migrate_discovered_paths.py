"""
Migration script to add discovered_paths table to existing database.
"""

import sys
from pathlib import Path
from sqlalchemy import inspect

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.connection import get_db, engine
from src.database.models import Base, DiscoveredPath


def check_table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def migrate():
    """Run migration to add discovered_paths table."""
    print("[*] Starting migration for discovered_paths table...")
    
    # Check if table already exists
    if check_table_exists('discovered_paths'):
        print("[!] Table 'discovered_paths' already exists. Migration skipped.")
        return
    
    # Create the table
    print("[*] Creating discovered_paths table...")
    DiscoveredPath.__table__.create(engine)
    
    print("[✓] Migration completed successfully!")
    print("[*] Table 'discovered_paths' has been created.")


if __name__ == '__main__':
    try:
        migrate()
    except Exception as e:
        print(f"[!] Migration failed: {e}")
        sys.exit(1)

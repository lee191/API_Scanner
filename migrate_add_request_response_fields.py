"""
Migration script to add request/response fields to Endpoint table
This script adds detailed HTTP traffic capture fields for AI analysis
"""

import sys
import sqlite3
from pathlib import Path

def migrate_database():
    """Add new columns to endpoint table for detailed request/response storage"""
    
    # Database path - try both possible names
    db_path1 = Path(__file__).parent / 'data' / 'scanner.db'
    db_path2 = Path(__file__).parent / 'data' / 'api_scanner.db'
    
    if db_path1.exists():
        db_path = db_path1
    elif db_path2.exists():
        db_path = db_path2
    else:
        print(f"❌ Database not found at: {db_path1} or {db_path2}")
        print("Please run 'python setup_db.py' first to create the database.")
        return False
    
    print(f"📂 Database found: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(endpoint)")
        columns = [col[1] for col in cursor.fetchall()]
        
        new_columns = [
            ('request_headers', 'JSON'),
            ('request_body', 'TEXT'),
            ('response_headers', 'JSON'),
            ('response_body', 'TEXT'),
            ('response_time', 'INTEGER')
        ]
        
        migrations_needed = []
        for col_name, col_type in new_columns:
            if col_name not in columns:
                migrations_needed.append((col_name, col_type))
        
        if not migrations_needed:
            print("✅ All columns already exist. No migration needed.")
            conn.close()
            return True
        
        print(f"\n🔧 Adding {len(migrations_needed)} new column(s) to endpoint table:")
        
        for col_name, col_type in migrations_needed:
            try:
                sql = f"ALTER TABLE endpoint ADD COLUMN {col_name} {col_type}"
                cursor.execute(sql)
                print(f"  ✅ Added: {col_name} ({col_type})")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    print(f"  ⚠️  Already exists: {col_name}")
                else:
                    raise
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Verify new schema
        cursor.execute("PRAGMA table_info(endpoint)")
        all_columns = cursor.fetchall()
        print(f"\n📋 Endpoint table now has {len(all_columns)} columns:")
        for col in all_columns:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("  Database Migration: Add Request/Response Fields")
    print("=" * 60)
    print("\nThis will add the following columns to endpoint table:")
    print("  - request_headers: Store HTTP request headers")
    print("  - request_body: Store HTTP request body")
    print("  - response_headers: Store HTTP response headers")
    print("  - response_body: Store HTTP response body")
    print("  - response_time: Store response time in milliseconds")
    print("\nThese fields enable AI to analyze actual HTTP traffic data.")
    print("-" * 60)
    
    input("\nPress Enter to start migration...")
    
    success = migrate_database()
    
    if success:
        print("\n" + "=" * 60)
        print("  Migration Complete!")
        print("=" * 60)
        print("\n✨ Next steps:")
        print("  1. Restart API server (api_server.py)")
        print("  2. Run a new scan to collect request/response data")
        print("  3. Use AI Chat to analyze detailed HTTP traffic")
    else:
        print("\n" + "=" * 60)
        print("  Migration Failed")
        print("=" * 60)
        sys.exit(1)

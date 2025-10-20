"""Check database tables."""

import sqlite3
import os

db_path = os.path.join('data', 'scanner.db')

if not os.path.exists(db_path):
    print(f"❌ Database not found: {db_path}")
    exit(1)

print(f"✅ Database found: {db_path}\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("📋 Tables in database:")
for table in tables:
    print(f"  - {table[0]}")
    
    # Get columns for each table
    cursor.execute(f"PRAGMA table_info({table[0]});")
    columns = cursor.fetchall()
    for col in columns:
        print(f"      {col[1]} ({col[2]})")
    print()

conn.close()

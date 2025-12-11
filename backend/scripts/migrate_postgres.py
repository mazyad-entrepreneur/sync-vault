import sys
import os
import sqlite3
import psycopg2
from datetime import datetime

# Configuration
SQLITE_DB = "syncvault.db"
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://syncvault:development_password@localhost:5432/syncvault_db")

def migrate():
    print("🚀 Starting migration from SQLite to PostgreSQL...")
    
    if not os.path.exists(SQLITE_DB):
        print(f"❌ SQLite database {SQLITE_DB} not found.")
        sys.exit(1)
        
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to PostgreSQL
    try:
        pg_conn = psycopg2.connect(POSTGRES_URL)
        pg_cursor = pg_conn.cursor()
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        sys.exit(1)
        
    tables = ["stores", "products", "inventory", "transactions", "alerts", "forecasts"]
    
    for table in tables:
        print(f"\n📦 Migrating table: {table}")
        
        # Get data from SQLite
        try:
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
        except sqlite3.OperationalError:
            print(f"⚠️ Table {table} not found in SQLite. Skipping.")
            continue
            
        if not rows:
            print(f"   No data in {table}.")
            continue
            
        # Insert into Postgres
        # Note: This assumes schemas are identical and created by SQLAlchemy already
        count = 0
        for row in rows:
            data = dict(row)
            columns = list(data.keys())
            values = list(data.values())
            
            placeholders = ",".join(["%s"] * len(values))
            col_names = ",".join(columns)
            
            query = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"
            
            try:
                pg_cursor.execute(query, values)
                count += 1
            except Exception as e:
                print(f"   ❌ Error inserting row {data.get('id')}: {e}")
                pg_conn.rollback()
                continue
                
        pg_conn.commit()
        print(f"   ✅ Migrated {count} rows.")
        
    print("\n✨ Migration complete!")
    sqlite_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    migrate()

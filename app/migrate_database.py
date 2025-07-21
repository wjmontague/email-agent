#!/usr/bin/env python3
"""
Database migration script for Email AI Agent
Adds missing indexes and fixes schema issues
"""

import os
import sys
import sqlite3
from app.secure_db_connection import secure_db
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_db_path():
    """Get the database path"""
    return os.path.join(os.path.dirname(__file__), 'email_agent.db')

def backup_database():
    """Create a backup of the current database"""
    db_path = get_db_path()
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    return None

def run_migrations():
    """Run database migrations"""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print("❌ Database file not found. Please run the app once to create it.")
        return False
    
    with secure_db.get_connection() as conn:
        cursor = conn.cursor()
    
    try:
        print("🔄 Running database migrations...")
        
        # Add missing indexes if they don't exist
        migrations = [
            # Email table indexes
            "CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails(received_at)",
            "CREATE INDEX IF NOT EXISTS idx_emails_sender_email ON emails(sender_email)",
            "CREATE INDEX IF NOT EXISTS idx_emails_is_sent ON emails(is_sent)",
            "CREATE INDEX IF NOT EXISTS idx_emails_thread_id ON emails(thread_id)",
            
            # ClassifiedEmail table indexes
            "CREATE INDEX IF NOT EXISTS idx_classified_category ON classified_emails(category)",
            "CREATE INDEX IF NOT EXISTS idx_classified_priority ON classified_emails(priority)",
            "CREATE INDEX IF NOT EXISTS idx_classified_is_read ON classified_emails(is_read)",
            "CREATE INDEX IF NOT EXISTS idx_classified_is_archived ON classified_emails(is_archived)",
            "CREATE INDEX IF NOT EXISTS idx_classified_requires_action ON classified_emails(requires_action)",
            "CREATE INDEX IF NOT EXISTS idx_classified_property_address ON classified_emails(property_address)",
            
            # Add missing columns if they don't exist
            "ALTER TABLE classified_emails ADD COLUMN is_archived BOOLEAN DEFAULT 0",
            "ALTER TABLE classified_emails ADD COLUMN is_important BOOLEAN DEFAULT 0",
            
            # Update existing NULL values
            "UPDATE classified_emails SET is_archived = 0 WHERE is_archived IS NULL",
            "UPDATE classified_emails SET is_important = 0 WHERE is_important IS NULL",
            "UPDATE classified_emails SET is_read = 0 WHERE is_read IS NULL",
            "UPDATE classified_emails SET requires_action = 0 WHERE requires_action IS NULL",
        ]
        
        for migration in migrations:
            try:
                cursor.execute(migration)
                print(f"✅ Executed: {migration[:50]}...")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e) or "already exists" in str(e):
                    print(f"⏭️  Skipped (already exists): {migration[:50]}...")
                else:
                    print(f"⚠️  Warning: {migration[:50]}... - {e}")
        
        # Verify critical tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['emails', 'classified_emails', 'email_categories', 'processing_logs']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            print("💡 Run 'python app/init_db.py' to create missing tables")
        else:
            print("✅ All required tables exist")
        
        conn.commit()
        conn.close()
        
        print("✅ Database migrations completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        conn.close()
        return False

def verify_database():
    """Verify database integrity"""
    db_path = get_db_path()
    with secure_db.get_connection() as conn:
        cursor = conn.cursor()
    
    try:
        # Check table counts
        print("\n📊 Database Status:")
        
        tables_to_check = ['emails', 'classified_emails', 'email_categories', 'processing_logs']
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} records")
            except sqlite3.OperationalError:
                print(f"  {table}: ❌ Table not found")
        
        # Check for orphaned records
        cursor.execute("""
            SELECT COUNT(*) FROM classified_emails 
            WHERE email_id NOT IN (SELECT id FROM emails)
        """)
        orphaned = cursor.fetchone()[0]
        if orphaned > 0:
            print(f"  ⚠️  Found {orphaned} orphaned classified_emails records")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        conn.close()

if __name__ == "__main__":
    print("🗄️  Email AI Agent Database Migration Tool")
    print("=" * 50)
    
    # Create backup
    backup_path = backup_database()
    
    # Run migrations
    if run_migrations():
        verify_database()
        print("\n🎉 Migration completed successfully!")
        if backup_path:
            print(f"💾 Backup saved at: {backup_path}")
    else:
        print("\n❌ Migration failed!")
        if backup_path:
            print(f"💾 Restore from backup if needed: {backup_path}")
        sys.exit(1)

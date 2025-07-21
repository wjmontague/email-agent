#!/usr/bin/env python3
"""
Database optimization script for Email AI Agent
"""

import os
import sqlite3
from app.secure_db_connection import secure_db
import sys

def optimize_database():
    """Optimize the database"""
    db_path = os.path.join(os.path.dirname(__file__), 'email_agent.db')
    
    if not os.path.exists(db_path):
        print("❌ Database file not found")
        return False
    
    with secure_db.get_connection() as conn:
        cursor = conn.cursor()
    
    try:
        print("🔄 Optimizing database...")
        
        # Vacuum the database to reclaim space
        cursor.execute("VACUUM")
        print("✅ Vacuumed database")
        
        # Analyze tables for better query planning
        cursor.execute("ANALYZE")
        print("✅ Analyzed tables")
        
        # Update statistics
        cursor.execute("PRAGMA optimize")
        print("✅ Updated statistics")
        
        conn.close()
        print("✅ Database optimization completed!")
        return True
        
    except Exception as e:
        print(f"❌ Optimization failed: {e}")
        conn.close()
        return False

if __name__ == "__main__":
    optimize_database()

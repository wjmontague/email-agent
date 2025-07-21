#!/usr/bin/env python3
"""
Database Optimizer
Auto-generated database optimization
"""

import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

def optimize_database():
    """Optimize the database"""
    db_paths = [
        'app/email_agent.db',
        '/home/MikeAubry02025/email_agent/app/email_agent.db'
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        logger.warning("Database not found, skipping optimization")
        return False
    
    try:
        conn = sqlite3.connect(db_path, timeout=30)
        
        # Create essential indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails(received_at)",
            "CREATE INDEX IF NOT EXISTS idx_emails_sender_email ON emails(sender_email)",
            "CREATE INDEX IF NOT EXISTS idx_classified_category ON classified_emails(category)",
            "CREATE INDEX IF NOT EXISTS idx_classified_priority ON classified_emails(priority)",
            "CREATE INDEX IF NOT EXISTS idx_classified_is_read ON classified_emails(is_read)",
        ]
        
        for index_sql in indexes:
            try:
                conn.execute(index_sql)
                logger.debug(f"Created index: {index_sql[:50]}...")
            except Exception as e:
                logger.debug(f"Index creation skipped: {e}")
        
        # Optimize database
        conn.execute("ANALYZE")
        conn.execute("PRAGMA optimize")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Database optimization completed")
        return True
        
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        return False

if __name__ == "__main__":
    optimize_database()

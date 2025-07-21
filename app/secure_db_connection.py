
from app.enhanced_error_handler import safe_execute, handle_database_error
#!/usr/bin/env python3
"""
Secure Database Connection Wrapper
Auto-generated secure database connection manager
"""

import sqlite3
import os
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class SecureDatabaseConnection:
    """Secure database connection manager"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            possible_paths = [
                '/home/MikeAubry02025/email_agent/app/email_agent.db',
                'app/email_agent.db',
                os.path.join(os.path.dirname(__file__), 'email_agent.db'),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    self.db_path = path
                    break
            else:
                self.db_path = '/home/MikeAubry02025/email_agent/app/email_agent.db'
        else:
            self.db_path = db_path
    
    @contextmanager
    def get_connection(self):
        """Get a secure database connection"""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30,
                isolation_level='DEFERRED'
            )
            
            # Security and performance settings
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA temp_store = MEMORY")
            conn.execute("PRAGMA cache_size = -64000")
            
            conn.row_factory = sqlite3.Row
            yield conn
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    @contextmanager
    def transaction(self):
        """Execute operations in a secure transaction"""
        with self.get_connection() as conn:
            try:
                conn.execute("BEGIN TRANSACTION")
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction failed: {e}")
                raise
    
    def execute_query(self, query, params=None):
        """Execute a single query safely"""
        with self.get_connection() as conn:
            if params:
                return conn.execute(query, params)
            else:
                return conn.execute(query)
    
    def get_email_counts(self):
        """Get email counts safely"""
        try:
            with self.get_connection() as conn:
                # Check if tables exist first
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN ('emails', 'classified_emails')
                """)
                existing_tables = {row[0] for row in cursor.fetchall()}
                
                counts = {'emails': 0, 'classified_emails': 0, 'unread': 0}
                
                if 'emails' in existing_tables:
                    cursor = conn.execute("SELECT COUNT(*) FROM emails")
                    result = cursor.fetchone()
                    counts['emails'] = result[0] if result else 0
                
                if 'classified_emails' in existing_tables:
                    cursor = conn.execute("SELECT COUNT(*) FROM classified_emails")
                    result = cursor.fetchone()
                    counts['classified_emails'] = result[0] if result else 0
                    
                    # Get unread count
                    cursor = conn.execute("SELECT COUNT(*) FROM classified_emails WHERE is_read = 0")
                    result = cursor.fetchone()
                    counts['unread'] = result[0] if result else 0
                
                return counts
                
        except Exception as e:
            logger.error(f"Error getting email counts: {e}")
            return {'emails': 0, 'classified_emails': 0, 'unread': 0}

# Global instance for easy importing
secure_db = SecureDatabaseConnection()

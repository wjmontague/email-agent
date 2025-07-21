import sqlite3
from app.secure_db_connection import secure_db
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import contextmanager

class EmailStateManager:
    """Manages email states and urgent counts consistently"""
    
    def __init__(self, db_path: str = None):
        # Handle different deployment environments
        if db_path is None:
            # Auto-detect database path
            possible_paths = [
                '/home/MikeAubry02025/email_agent/app/email_agent.db',
                'app/email_agent.db',
                os.path.join(os.path.dirname(__file__), 'email_agent.db'),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'email_agent.db')
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    self.db_path = path
                    break
            else:
                # Default to the most likely path
                self.db_path = '/home/MikeAubry02025/email_agent/app/email_agent.db'
        else:
            self.db_path = db_path
        
        self.initialized = False
    
    def _lazy_init(self):
        """Initialize only when first used to avoid import-time errors"""
        if not self.initialized:
            try:
                if os.path.exists(self.db_path):
                    self.initialize_state_tracking()
                    self.initialized = True
                else:
                    print(f"Warning: Database not found at {self.db_path}")
            except Exception as e:
                print(f"Warning: Could not initialize EmailStateManager: {e}")
    
    @contextmanager
    def get_db_connection(self):
        """Context manager for database connections"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        with secure_db.get_connection() as conn:
            conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def initialize_state_tracking(self):
        """Initialize state tracking tables and triggers"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Add missing columns if they don't exist
            columns_to_add = [
                ("is_replied", "BOOLEAN DEFAULT 0"),
                ("is_processed", "BOOLEAN DEFAULT 0"),
                ("replied_at", "DATETIME NULL"),
                ("last_action_at", "DATETIME NULL"),
                ("action_type", "VARCHAR(50) NULL")
            ]
            
            for column_name, column_def in columns_to_add:
                try:
                    cursor.execute(f"ALTER TABLE classified_emails ADD COLUMN {column_name} {column_def}")
                except sqlite3.OperationalError:
                    pass  # Column already exists
            
            # Create urgent_counts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS urgent_counts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    count_type VARCHAR(50) NOT NULL UNIQUE,
                    current_count INTEGER NOT NULL DEFAULT 0,
                    last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_by VARCHAR(100)
                )
            """)
            
            # Initialize counts if table is empty
            cursor.execute("SELECT COUNT(*) FROM urgent_counts")
            if cursor.fetchone()[0] == 0:
                self._initialize_counts(cursor)
            
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_classified_is_replied ON classified_emails(is_replied)",
                "CREATE INDEX IF NOT EXISTS idx_classified_is_processed ON classified_emails(is_processed)"
            ]
            
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except sqlite3.OperationalError:
                    pass
            
            conn.commit()
    
    def _initialize_counts(self, cursor):
        """Initialize count tracking with current database state"""
        try:
            counts = {
                'critical': cursor.execute("""
                    SELECT COUNT(*) FROM classified_emails 
                    WHERE priority = 'Critical' AND is_read = 0 AND (is_archived = 0 OR is_archived IS NULL)
                """).fetchone()[0],
                
                'high': cursor.execute("""
                    SELECT COUNT(*) FROM classified_emails 
                    WHERE priority = 'High' AND is_read = 0 AND (is_archived = 0 OR is_archived IS NULL)
                """).fetchone()[0],
                
                'unread': cursor.execute("""
                    SELECT COUNT(*) FROM classified_emails 
                    WHERE is_read = 0 AND (is_archived = 0 OR is_archived IS NULL)
                """).fetchone()[0],
                
                'requires_action': cursor.execute("""
                    SELECT COUNT(*) FROM classified_emails 
                    WHERE requires_action = 1 AND is_read = 0 AND (is_archived = 0 OR is_archived IS NULL)
                """).fetchone()[0]
            }
            
            for count_type, count_value in counts.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO urgent_counts (count_type, current_count, updated_by) 
                    VALUES (?, ?, 'initialization')
                """, (count_type, count_value))
        except Exception as e:
            print(f"Warning: Could not initialize counts: {e}")
    
    def mark_email_as_read(self, email_id: int, priority: str = None) -> bool:
        """Mark email as read and update counts atomically"""
        self._lazy_init()
        
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get current email state
                email_info = cursor.execute("""
                    SELECT priority, is_read, is_archived, requires_action 
                    FROM classified_emails WHERE email_id = ?
                """, (email_id,)).fetchone()
                
                if not email_info or email_info['is_read']:
                    return False  # Already read or doesn't exist
                
                # Mark as read
                cursor.execute("""
                    UPDATE classified_emails 
                    SET is_read = 1, 
                        last_action_at = CURRENT_TIMESTAMP,
                        action_type = 'read'
                    WHERE email_id = ?
                """, (email_id,))
                
                # Update counts
                self._decrement_count(cursor, 'unread', 'mark_read')
                
                if email_info['priority'] in ['Critical', 'High']:
                    self._decrement_count(cursor, email_info['priority'].lower(), 'mark_read')
                
                if email_info['requires_action']:
                    self._decrement_count(cursor, 'requires_action', 'mark_read')
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error marking email as read: {e}")
            return False
    
    def mark_email_as_replied(self, email_id: int) -> bool:
        """Mark email as replied and update counts atomically"""
        self._lazy_init()
        
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get current email state
                email_info = cursor.execute("""
                    SELECT priority, is_read, is_replied, is_archived, requires_action 
                    FROM classified_emails WHERE email_id = ?
                """, (email_id,)).fetchone()
                
                if not email_info or email_info['is_replied']:
                    return False  # Already replied or doesn't exist
                
                # Mark as replied (and read if not already)
                cursor.execute("""
                    UPDATE classified_emails 
                    SET is_replied = 1, 
                        is_read = 1,
                        replied_at = CURRENT_TIMESTAMP,
                        last_action_at = CURRENT_TIMESTAMP,
                        action_type = 'replied'
                    WHERE email_id = ?
                """, (email_id,))
                
                # Update counts only if it wasn't already read
                if not email_info['is_read']:
                    self._decrement_count(cursor, 'unread', 'mark_replied')
                    
                    if email_info['priority'] in ['Critical', 'High']:
                        self._decrement_count(cursor, email_info['priority'].lower(), 'mark_replied')
                    
                    if email_info['requires_action']:
                        self._decrement_count(cursor, 'requires_action', 'mark_replied')
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error marking email as replied: {e}")
            return False
    
    def _decrement_count(self, cursor, count_type: str, updated_by: str):
        """Safely decrement a count, ensuring it doesn't go below 0"""
        cursor.execute("""
            UPDATE urgent_counts 
            SET current_count = MAX(0, current_count - 1),
                last_updated = CURRENT_TIMESTAMP,
                updated_by = ?
            WHERE count_type = ?
        """, (updated_by, count_type))
    
    def get_current_counts(self) -> Dict[str, int]:
        """Get current urgent counts"""
        self._lazy_init()
        
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                counts = cursor.execute("""
                    SELECT count_type, current_count 
                    FROM urgent_counts
                """).fetchall()
                
                return {row['count_type']: row['current_count'] for row in counts}
        except Exception as e:
            print(f"Error getting counts: {e}")
            # Return fallback counts
            return {'critical': 0, 'high': 0, 'unread': 0, 'requires_action': 0}
    
    def recalculate_counts(self) -> Dict[str, int]:
        """Recalculate counts from scratch (for data consistency checks)"""
        self._lazy_init()
        
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Recalculate actual counts
                actual_counts = {
                    'critical': cursor.execute("""
                        SELECT COUNT(*) FROM classified_emails 
                        WHERE priority = 'Critical' AND is_read = 0 AND (is_archived = 0 OR is_archived IS NULL)
                    """).fetchone()[0],
                    
                    'high': cursor.execute("""
                        SELECT COUNT(*) FROM classified_emails 
                        WHERE priority = 'High' AND is_read = 0 AND (is_archived = 0 OR is_archived IS NULL)
                    """).fetchone()[0],
                    
                    'unread': cursor.execute("""
                        SELECT COUNT(*) FROM classified_emails 
                        WHERE is_read = 0 AND (is_archived = 0 OR is_archived IS NULL)
                    """).fetchone()[0],
                    
                    'requires_action': cursor.execute("""
                        SELECT COUNT(*) FROM classified_emails 
                        WHERE requires_action = 1 AND is_read = 0 AND (is_archived = 0 OR is_archived IS NULL)
                    """).fetchone()[0]
                }
                
                # Update stored counts
                for count_type, actual_count in actual_counts.items():
                    cursor.execute("""
                        UPDATE urgent_counts 
                        SET current_count = ?,
                            last_updated = CURRENT_TIMESTAMP,
                            updated_by = 'recalculation'
                        WHERE count_type = ?
                    """, (actual_count, count_type))
                
                conn.commit()
                return actual_counts
                
        except Exception as e:
            print(f"Error recalculating counts: {e}")
            return {'critical': 0, 'high': 0, 'unread': 0, 'requires_action': 0}
    
    def is_available(self) -> bool:
        """Check if the state manager is available and working"""
        try:
            self._lazy_init()
            return self.initialized and os.path.exists(self.db_path)
        except:
            return False


# Global instance - but don't initialize until needed
_state_manager = None

def get_state_manager() -> EmailStateManager:
    """Get the global state manager instance"""
    global _state_manager
    if _state_manager is None:
        _state_manager = secure_db
    return _state_manager
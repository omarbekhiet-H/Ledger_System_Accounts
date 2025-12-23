# database/manager/audit_manager.py

import sqlite3
from datetime import datetime

class AuditManager:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def initialize_audit_tables(self):
        """تهيئة جداول التدقيق في قاعدة البيانات"""
        conn = self.db_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # جدول سجل التدقيق
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_id INTEGER NOT NULL,
                    old_status TEXT NOT NULL,
                    new_status TEXT NOT NULL,
                    audit_notes TEXT,
                    auditor_id INTEGER NOT NULL,
                    audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (entry_id) REFERENCES journal_entries(id)
                )
            """)
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error initializing audit tables: {e}")
            return False
        finally:
            conn.close()

    def log_audit_action(self, entry_id, old_status, new_status, auditor_id, notes=None):
        """تسجيل إجراء تدقيق في السجل"""
        conn = self.db_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs 
                (entry_id, old_status, new_status, audit_notes, auditor_id)
                VALUES (?, ?, ?, ?, ?)
            """, (entry_id, old_status, new_status, notes, auditor_id))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error logging audit action: {e}")
            return False
        finally:
            conn.close()

    def get_audit_history(self, entry_id):
        """الحصول على سجل التدقيق لقيد معين"""
        conn = self.db_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM audit_logs 
                WHERE entry_id = ?
                ORDER BY audit_date DESC
            """, (entry_id,))
            
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error getting audit history: {e}")
            return None
        finally:
            conn.close()

    def get_entries_by_audit_status(self, status):
        """الحصول على القيود حسب حالة التدقيق"""
        conn = self.db_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT je.* FROM journal_entries je
                WHERE je.status = ?
                ORDER BY je.entry_date DESC
            """, (status,))
            
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error getting entries by audit status: {e}")
            return None
        finally:
            conn.close()
import sqlite3
from typing import List, Dict, Optional, Tuple
from database.db_connection import get_users_db_connection, get_db_connection

class NEWAuditManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def get_connection(self):
        """الحصول على اتصال بقاعدة البيانات"""
        if self.db_path:
            return get_db_connection(self.db_path)
        else:
            return get_users_db_connection()

    # ------------------------- إنشاء الجدول -------------------------
    def init_table(self):
        """إنشاء جدول التدقيق إذا لم يكن موجوداً"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    entity TEXT,
                    entity_id INTEGER,
                    details TEXT,
                    ip_address TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating audit_log table: {e}")
        finally:
            if conn:
                conn.close()

    # ------------------------- تسجيل العمليات -------------------------
    def log_action(self, user_id: Optional[int], action: str, entity: str = None,
                   entity_id: int = None, details: str = None, ip_address: str = None) -> Tuple[bool, str]:
        """تسجيل عملية جديدة في السجل"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_log (user_id, action, entity, entity_id, details, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, action, entity, entity_id, details, ip_address))
            conn.commit()
            return True, "تم تسجيل العملية"
        except sqlite3.Error as e:
            return False, f"خطأ أثناء التسجيل: {str(e)}"
        finally:
            if conn:
                conn.close()

    # ------------------------- جلب العمليات -------------------------
    def get_all(self, limit: int = 100, entity: str = None, user_id: int = None) -> List[Dict]:
        """جلب آخر العمليات (مع إمكانية التصفية)"""
        conn = None
        results = []
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            query = "SELECT id, user_id, action, entity, entity_id, details, ip_address, created_at FROM audit_log WHERE 1=1"
            params = []

            if entity:
                query += " AND entity = ?"
                params.append(entity)

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                results.append({
                    "id": row[0],
                    "user_id": row[1],
                    "action": row[2],
                    "entity": row[3],
                    "entity_id": row[4],
                    "details": row[5],
                    "ip_address": row[6],
                    "created_at": row[7],
                })
            return results
        except sqlite3.Error as e:
            print(f"Error fetching audit log: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_by_id(self, log_id: int) -> Optional[Dict]:
        """جلب عملية واحدة"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_id, action, entity, entity_id, details, ip_address, created_at FROM audit_log WHERE id = ?", (log_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "user_id": row[1],
                    "action": row[2],
                    "entity": row[3],
                    "entity_id": row[4],
                    "details": row[5],
                    "ip_address": row[6],
                    "created_at": row[7],
                }
            return None
        except sqlite3.Error as e:
            print(f"Error fetching log by id: {e}")
            return None
        finally:
            if conn:
                conn.close()

import sqlite3
from typing import Dict, Tuple, Optional
from database.db_connection import get_users_db_connection, get_db_connection

class NEWSettingsManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def get_connection(self):
        """الحصول على اتصال بقاعدة البيانات"""
        if self.db_path:
            return get_db_connection(self.db_path)
        else:
            return get_users_db_connection()

    # ------------------------- إنشاء جدول الإعدادات لو مش موجود -------------------------

    def init_table(self):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    description TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating settings table: {e}")
        finally:
            if conn:
                conn.close()

    # ------------------------- جلب الإعداد -------------------------

    def get_setting(self, key: str) -> Optional[str]:
        """جلب قيمة إعداد معين"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else None
        except sqlite3.Error as e:
            print(f"Error getting setting: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_all_settings(self) -> Dict[str, str]:
        """جلب جميع الإعدادات"""
        conn = None
        settings = {}
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM system_settings")
            for row in cursor.fetchall():
                settings[row[0]] = row[1]
            return settings
        except sqlite3.Error as e:
            print(f"Error getting settings: {e}")
            return {}
        finally:
            if conn:
                conn.close()

    # ------------------------- تحديث/إضافة إعداد -------------------------

    def set_setting(self, key: str, value: str, description: str = None) -> Tuple[bool, str]:
        """إضافة أو تحديث إعداد"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO system_settings (key, value, description, updated_at)
                VALUES (?, ?, ?, datetime('now'))
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    description = excluded.description,
                    updated_at = datetime('now')
            """, (key, value, description))

            conn.commit()
            return True, f"تم حفظ الإعداد {key}"
        except sqlite3.Error as e:
            return False, f"خطأ أثناء الحفظ: {str(e)}"
        finally:
            if conn:
                conn.close()

    # ------------------------- مسح إعداد -------------------------

    def delete_setting(self, key: str) -> Tuple[bool, str]:
        """حذف إعداد معين"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM system_settings WHERE key = ?", (key,))
            conn.commit()
            return True, f"تم حذف الإعداد {key}"
        except sqlite3.Error as e:
            return False, f"خطأ أثناء الحذف: {str(e)}"
        finally:
            if conn:
                conn.close()

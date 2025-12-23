# database/base_manager.py
import sys
print(f"DEBUG: Loading base_manager.py from: {__file__}") # DEBUG

import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox

class BaseManager:
    """
    كلاس أساسي لمديري قواعد البيانات يوفر وظائف الاتصال المشتركة.
    """
    def __init__(self, get_connection_func):
        self.get_connection = get_connection_func

    def execute_query(self, query, params=()):
        """ينفذ استعلام SQL (INSERT, UPDATE, DELETE) ويعيد True للنجاح، False للفشل."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ في قاعدة البيانات", f"خطأ في تنفيذ الاستعلام: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def fetch_one(self, query, params=()):
        """يجلب سطر واحد من نتيجة استعلام SQL."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            if row:
                # تحويل الصف إلى قاموس لسهولة الوصول إلى البيانات بالاسم
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ في قاعدة البيانات", f"خطأ في جلب البيانات: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def fetch_all(self, query, params=()):
        """يجلب جميع الأسطر من نتيجة استعلام SQL."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            if rows:
                # تحويل كل صف إلى قاموس
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return []
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ في قاعدة البيانات", f"خطأ في جلب البيانات: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_max_id(self, table_name):
        """يجلب أكبر ID من جدول معين."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return 0
            cursor = conn.cursor()
            cursor.execute(f"SELECT MAX(id) FROM {table_name}")
            max_id = cursor.fetchone()[0]
            return max_id if max_id is not None else 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ في قاعدة البيانات", f"خطأ في جلب أكبر ID من {table_name}: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    def record_exists(self, table_name, column_name, value, exclude_id=None):
        """يتحقق مما إذا كان سجل موجودًا بناءً على عمود وقيمة معينة."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            query = f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} = ?"
            params = [value]
            if exclude_id is not None:
                query += " AND id != ?"
                params.append(exclude_id)
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            return count > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ في قاعدة البيانات", f"خطأ في التحقق من وجود سجل: {e}")
            return False
        finally:
            if conn:
                conn.close()

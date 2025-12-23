# database/manager.py
import sqlite3
from typing import List, Dict, Any, Optional

class DatabaseManager:
    """
    مدير قاعدة البيانات الأساسي للتعامل مع SQLite
    """
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self):
        """إنشاء اتصال بقاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # للحصول على نتائج كـ dictionaries
        return conn

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """تنفيذ استعلام وإرجاع جميع النتائج"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """تنفيذ استعلام وإرجاع نتيجة واحدة"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            return dict(result) if result else None
        finally:
            conn.close()

    def insert(self, query: str, params: tuple = ()) -> int:
        """تنفيذ إدراج وإرجاع ID الصف المضاف"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def execute(self, query: str, params: tuple = ()) -> bool:
        """تنفيذ أمر بدون إرجاع نتائج"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()
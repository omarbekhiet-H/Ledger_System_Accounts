# context_manager.py
import sqlite3
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None
    
    def connect(self):
        """إنشاء اتصال بقاعدة البيانات"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def close(self):
        """إغلاق الاتصال"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    @contextmanager
    def get_cursor(self):
        """مدير سياق للتعامل مع Cursor بأمان"""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
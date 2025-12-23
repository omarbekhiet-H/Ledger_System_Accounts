# database/currency_manager.py

import sqlite3
from database.base_manager import BaseManager

class CurrencyManager(BaseManager):
    """
    مسؤول عن إدارة العملات.
    """
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func)

    def add_currency(self, code, name_ar, name_en=None, symbol=None):
        """يضيف عملة جديدة."""
        query = """
            INSERT INTO currencies (code, name_ar, name_en, symbol)
            VALUES (?, ?, ?, ?)
        """
        params = (code, name_ar, name_en, symbol)
        return self._execute_query(query, params, commit=True, fetch_lastrowid=True)

    def get_all_currencies(self):
        """يجلب جميع العملات النشطة."""
        query = "SELECT id, code, name_ar, name_en, symbol FROM currencies WHERE is_active = 1 ORDER BY code"
        return self._execute_query(query, fetch_all=True)

    def get_currency_by_id(self, currency_id):
        """يجلب تفاصيل عملة بواسطة معرّفها."""
        query = "SELECT id, code, name_ar, name_en, symbol FROM currencies WHERE id = ?"
        return self._execute_query(query, (currency_id,), fetch_one=True)

    def get_currency_by_code(self, code):
        """يجلب تفاصيل عملة بواسطة كودها."""
        query = "SELECT id, code, name_ar, name_en, symbol FROM currencies WHERE code = ?"
        return self._execute_query(query, (code,), fetch_one=True)

    def update_currency(self, currency_id, data):
        """يحدث بيانات عملة موجودة."""
        fields = []
        params = []
        for key, value in data.items():
            fields.append(f"{key} = ?")
            params.append(value)
        
        if not fields:
            return False

        query = f"UPDATE currencies SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        params.append(currency_id)
        return self._execute_query(query, tuple(params), commit=True)

    def delete_currency(self, currency_id):
        """يعطل عملة (يغير حالتها إلى غير نشط)."""
        query = "UPDATE currencies SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        return self._execute_query(query, (currency_id,), commit=True)


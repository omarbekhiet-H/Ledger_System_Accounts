# database/db_connection.py

import sqlite3
import os
from PyQt5.QtWidgets import QMessageBox

# تحديد مسارات ملفات قواعد البيانات المنفصلة
DB_DIR = os.path.dirname(os.path.abspath(__file__))
FINANCIALS_DB_FILE = os.path.join(DB_DIR, 'financials.db')
INVENTORY_DB_FILE = os.path.join(DB_DIR, 'inventory.db')
NEWINVENTORY_DB_FILE = os.path.join(DB_DIR, 'NEWinventory.db')
FIXED_ASSETS_DB_FILE = os.path.join(DB_DIR, 'fixed_assets.db')
USERS_DB_FILE = os.path.join(DB_DIR, 'users.db')
MANUFACTURING_DB_FILE = os.path.join(DB_DIR, 'manufacturing.db')  # ⬅️ الجديد


def _get_connection(db_path):
    """
    دالة مساعدة لإنشاء اتصال بقاعدة بيانات معينة.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        QMessageBox.critical(None, "خطأ في الاتصال", f"لا يمكن الاتصال بقاعدة البيانات '{os.path.basename(db_path)}': {e}")
        return None

def get_db_connection(db_path=None):
    """
    دالة عامة للحصول على اتصال بقاعدة البيانات.
    إذا لم يتم تحديد مسار، يتم استخدام قاعدة بيانات المستخدمين كافتراضي.
    """
    if db_path is None:
        return get_users_db_connection()
    else:
        return _get_connection(db_path)

def get_financials_db_connection():
    """
    يعيد اتصالاً بقاعدة بيانات المالية.
    """
    return _get_connection(FINANCIALS_DB_FILE)

def get_inventory_db_connection():
    """
    يعيد اتصالاً بقاعدة بيانات المخزون.
    """
    return _get_connection(INVENTORY_DB_FILE)

def get_NEWinventory_db_connection():
    """
    يعيد اتصالاً بقاعدة بيانات المخزون.
    """
    return _get_connection(NEWINVENTORY_DB_FILE)

def get_fixed_assets_db_connection():
    """
    يعيد اتصالاً بقاعدة بيانات الأصول الثابتة.
    """
    return _get_connection(FIXED_ASSETS_DB_FILE)

def get_users_db_connection():
    """
    يعيد اتصالاً بقاعدة بيانات المستخدمين.
    """
    return _get_connection(USERS_DB_FILE)
def get_manufacturing_db_connection():
    """
    يعيد اتصالاً بقاعدة بيانات التصنيع.
    """
    return _get_connection(MANUFACTURING_DB_FILE)
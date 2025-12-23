# db_initializer.py (الكود المصحح لمسارات الاستيراد)

# نحذف 'database.' من بداية كل المسارات
from database.db_connection import get_users_db_connection, get_financials_db_connection
from database.schems.users_schema import USERS_SCHEMA_SCRIPT
from database.schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT

def initialize_users_database():
    """
    ينشئ جداول قاعدة بيانات المستخدمين إذا لم تكن موجودة.
    """
    print("... Checking users database schema...")
    conn = get_users_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.executescript(USERS_SCHEMA_SCRIPT)
            conn.commit()
            print("... Users schema check complete.")
        finally:
            conn.close()

def initialize_financials_database():
    """
    ينشئ جداول قاعدة البيانات المالية إذا لم تكن موجودة.
    """
    print("... Checking financials database schema...")
    conn = get_financials_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.executescript(FINANCIALS_SCHEMA_SCRIPT)
            conn.commit()
            print("... Financials schema check complete.")
        finally:
            conn.close()

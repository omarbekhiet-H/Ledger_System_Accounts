import sqlite3
import os

# --- 1. استيراد المخططات ---
from database.schems.users_schema import USERS_SCHEMA_SCRIPT
from database.schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT
from database.schems.inventory_schema import INVENTORY_SCHEMA_SCRIPT
from database.schems.fixed_assets_schema import FIXED_ASSETS_SCHEMA_SCRIPT

# --- 2. تحديد مسار مجلد البيانات داخل المشروع ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# إنشاء مجلد data إذا لم يكن موجوداً
os.makedirs(DATA_DIR, exist_ok=True)

USERS_DB_PATH = os.path.join(DATA_DIR, 'users.db')
FINANCIALS_DB_PATH = os.path.join(DATA_DIR, 'financials.db')
INVENTORY_DB_PATH = os.path.join(DATA_DIR, 'inventory.db')
FIXED_ASSETS_DB_PATH = os.path.join(DATA_DIR, 'fixed_assets.db')

def initialize_users_database():
    """
    ينشئ جداول قاعدة بيانات المستخدمين إذا لم تكن موجودة.
    """
    print("بدء تهيئة قاعدة بيانات المستخدمين...")
    print(f"--> يتم الآن إنشاء/الاتصال بالملف في المسار: {USERS_DB_PATH}")
    
    conn = None
    try:
        conn = sqlite3.connect(USERS_DB_PATH)
        cursor = conn.cursor()
        print("... إنشاء جداول قاعدة بيانات المستخدمين...")
        cursor.executescript(USERS_SCHEMA_SCRIPT)
        conn.commit()
        print("✅ تم إنشاء الجداول بنجاح.")
    except Exception as e:
        print(f"❌ خطأ في تهيئة قاعدة بيانات المستخدمين: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("... تم إغلاق الاتصال بقاعدة بيانات المستخدمين.")

def initialize_financials_database():
    """
    ينشئ جداول قاعدة البيانات المالية إذا لم تكن موجودة.
    """
    print("\nبدء تهيئة قاعدة البيانات المالية...")
    print(f"--> يتم الآن إنشاء/الاتصال بالملف في المسار: {FINANCIALS_DB_PATH}")
    
    conn = None
    try:
        conn = sqlite3.connect(FINANCIALS_DB_PATH)
        cursor = conn.cursor()
        cursor.executescript(FINANCIALS_SCHEMA_SCRIPT)
        conn.commit()
        print("✅ تم إنشاء جداول المالية بنجاح.")
    except Exception as e:
        print(f"❌ خطأ في تهيئة قاعدة البيانات المالية: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("... تم إغلاق الاتصال بقاعدة البيانات المالية.")

def initialize_inventory_db():
    """
    ينشئ جداول قاعدة بيانات المخزون إذا لم تكن موجودة.
    """
    print("\nبدء تهيئة قاعدة بيانات المخزون...")
    print(f"--> يتم الآن إنشاء/الاتصال بالملف في المسار: {INVENTORY_DB_PATH}")
    
    conn = None
    try:
        conn = sqlite3.connect(INVENTORY_DB_PATH)
        cursor = conn.cursor()
        cursor.executescript(INVENTORY_SCHEMA_SCRIPT)
        conn.commit()
        print("✅ تم إنشاء جميع جداول المخزون بنجاح.")
    except Exception as e:
        print(f"❌ خطأ في تهيئة قاعدة بيانات المخزون: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("... تم إغلاق الاتصال بقاعدة بيانات المخزون.")

def initialize_fixed_assets_database():
    """
    ينشئ جداول قاعدة بيانات الأصول الثابتة إذا لم تكن موجودة.
    """
    print("\nبدء تهيئة قاعدة بيانات الأصول الثابتة...")
    print(f"--> يتم الآن إنشاء/الاتصال بالملف في المسار: {FIXED_ASSETS_DB_PATH}")
    
    conn = None
    try:
        conn = sqlite3.connect(FIXED_ASSETS_DB_PATH)
        cursor = conn.cursor()
        cursor.executescript(FIXED_ASSETS_SCHEMA_SCRIPT)
        conn.commit()
        print("✅ تم إنشاء جداول الأصول الثابتة بنجاح.")
    except Exception as e:
        print(f"❌ خطأ في تهيئة قاعدة بيانات الأصول الثابتة: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("... تم إغلاق الاتصال بقاعدة بيانات الأصول الثابتة.")

def initialize_all_databases():
    """
    تهيئة جميع قواعد البيانات في النظام
    """
    print("--- بدء تهيئة جميع قواعد البيانات ---")
    initialize_users_database()
    initialize_financials_database()
    initialize_inventory_db()
    initialize_fixed_assets_database()
    print("\n--- تهيئة جميع قواعد البيانات مكتملة. ---")

# للاستخدام المباشر
if __name__ == "__main__":
    initialize_all_databases()
import sqlite3
import os
import sys

# --- [الأهم] إضافة جذر المشروع إلى مسار بايثون ---
try:
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except NameError:
    project_root = os.path.abspath('.')
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
# -------------------------------------------------

# استيراد سكريبت إنشاء الجداول
try:
    from database.schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT
except ImportError as e:
    print(f"!!! خطأ فادح في الاستيراد: {e}")
    sys.exit(1)

# --- تعريف أسماء المجلدات والملفات ---
DATABASE_FOLDER = "database"
DATABASE_NAME = "financials.db"
# ------------------------------------

def initialize_database():
    try:
        db_folder_path = os.path.join(project_root, DATABASE_FOLDER)
        if not os.path.exists(db_folder_path):
            os.makedirs(db_folder_path)
            print(f"تم إنشاء المجلد: {db_folder_path}")

        db_path = os.path.join(db_folder_path, DATABASE_NAME)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # ✅ تفعيل المفاتيح الأجنبية
        cursor.execute("PRAGMA foreign_keys = ON;")

        print("...جاري إنشاء الجداول...")
        cursor.executescript(FINANCIALS_SCHEMA_SCRIPT)
        conn.commit()

        # --- ✅ عرض أسماء الجداول وعددها ---
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [t[0] for t in cursor.fetchall()]
        print("\n=== الجداول التي تم إنشاؤها ===")
        for t in tables:
            print(f"- {t}")
        print(f"\n📌 عدد الجداول: {len(tables)}")

        conn.close()

    except sqlite3.Error as e:
        print(f"!!! حدث خطأ في قاعدة البيانات: {e}")
    except Exception as e:
        print(f"!!! حدث خطأ غير متوقع: {e}")

if __name__ == "__main__":
    initialize_database()

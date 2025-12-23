# create_database.py
import sqlite3
import os
import sys

# --- [الأهم] إضافة جذر المشروع إلى مسار بايثون ---
# هذا يسمح لنا باستيراد الملفات من المجلدات الأخرى مثل 'database'
try:
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except NameError:
    project_root = os.path.abspath('.')
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
# -------------------------------------------------

# الآن يمكننا الاستيراد من ملفك مباشرة
try:

    from database.schems.inventory_schema import INVENTORY_SCHEMA_SCRIPT

except ImportError as e:
    print(f"!!! خطأ فادح في الاستيراد: {e}")
    print("!!! تأكد من أن بنية المجلدات صحيحة وأن الملف 'financials_schema.py' موجود.")
    sys.exit(1)




# --- إعداد المسارات ---
DATABASE_FOLDER = "database"
DATABASE_NAME = "inventory.db"

def initialize_inventory_database():
    """ينشئ قاعدة بيانات المخازن ويضيف الجداول المطلوبة"""
    try:
        db_folder_path = os.path.join(project_root, DATABASE_FOLDER)

        if not os.path.exists(db_folder_path):
            os.makedirs(db_folder_path)
            print(f"📁 تم إنشاء مجلد قاعدة البيانات: {db_folder_path}")

        db_path = os.path.join(db_folder_path, DATABASE_NAME)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🛠️ جاري تنفيذ سكربت إنشاء الجداول...")
        cursor.executescript(INVENTORY_SCHEMA_SCRIPT)

        conn.commit()
        conn.close()

        print("✅ تم إنشاء قاعدة بيانات المخازن بنجاح:")
        print(f"📦 المسار: {db_path}")
        print("📌 يمكنك الآن إدخال البيانات أو تشغيل الواجهة المرتبطة.")

    except sqlite3.Error as e:
        print(f"❌ خطأ في SQLite: {e}")
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")



if __name__ == "__main__":
    # هذه هي الدالة الوحيدة التي يتم استدعاؤها عند تشغيل الملف

    initialize_inventory_database()

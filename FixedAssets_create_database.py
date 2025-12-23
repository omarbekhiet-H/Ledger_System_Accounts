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
    from database.schems.fixed_assets_schema import FIXED_ASSETS_SCHEMA_SCRIPT
 

except ImportError as e:
    print(f"!!! خطأ فادح في الاستيراد: {e}")
    print("!!! تأكد من أن بنية المجلدات صحيحة وأن الملف 'financials_schema.py' موجود.")
    sys.exit(1)


# --- تعريف أسماء المجلدات والملفات ---
DATABASE_FOLDER = "database"
DATABASE_NAME = "fixed_assets.db"
# ------------------------------------

def initialize_database():
    """
    ينشئ ملف قاعدة البيانات ومجلدها إذا لم يكونا موجودين،
    ثم ينشئ الجداول بداخلها باستخدام السكيما المستوردة.
    """
    try:
        # تحديد مسار مجلد قاعدة البيانات
        db_folder_path = os.path.join(project_root, DATABASE_FOLDER)
        
        # إنشاء المجلد إذا لم يكن موجودًا
        if not os.path.exists(db_folder_path):
            os.makedirs(db_folder_path)
            print(f"تم إنشاء المجلد: {db_folder_path}")

        # تحديد المسار الكامل لقاعدة البيانات
        db_path = os.path.join(db_folder_path, DATABASE_NAME)
        
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("...جاري إنشاء الجداول...")
        # تنفيذ سكريبت إنشاء الجداول من ملفك
        cursor.executescript(FIXED_ASSETS_SCHEMA_SCRIPT)
        
        conn.commit()
        conn.close()
        
        print("*****************************************************")
        print(f"* تم إنشاء الجداول بنجاح في: {db_path} *")
        print("* يمكنك الآن تشغيل الواجهة الرسومية بأمان. *")
        print("*****************************************************")

    except sqlite3.Error as e:
        print(f"!!! حدث خطأ في قاعدة البيانات: {e}")
    except Exception as e:
        print(f"!!! حدث خطأ غير متوقع: {e}")






if __name__ == "__main__":
    # هذه هي الدالة الوحيدة التي يتم استدعاؤها عند تشغيل الملف
    initialize_database()
  

import os
import sys
import sqlite3

# 🟢 إضافة مسار المشروع الجذري
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.schems.manufacturing_schema import MANUFACTURING_SCHEMA_SCRIPT
from database.db_connection import MANUFACTURING_DB_FILE

def init_db():
    with sqlite3.connect(MANUFACTURING_DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.executescript(MANUFACTURING_SCHEMA_SCRIPT)
        conn.commit()
        print("✅ تم إنشاء جميع جداول أوامر التشغيل داخل", MANUFACTURING_DB_FILE)

if __name__ == "__main__":
    init_db()

# init_inventory_db.py
import sqlite3
from database.schems.inventory_schema import INVENTORY_SCHEMA_SCRIPT

db_path = "C:/Users/AU/Videos/accounting/my_erp_projects/database/inventory.db"  # عدّل حسب المسار لو مختلف

def initialize_inventory_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executescript(INVENTORY_SCHEMA_SCRIPT)
    conn.commit()
    conn.close()
    print("✅ تم إنشاء جميع جداول المخزون بنجاح.")

if __name__ == "__main__":
    initialize_inventory_db()
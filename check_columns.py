import sqlite3

# عدل المسار لو قاعدة بياناتك في مكان تاني
DB_PATH = r"J:\Dates\Final Account 23-8-2025\accounting\my_erp_projects\database\fixed_assets.db"

def show_table_info(table_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = cursor.fetchall()
    print(f"\n=== {table_name} ===")
    for col in cols:
        # col = (cid, name, type, notnull, dflt_value, pk)
        print(f" - {col[1]} ({col[2]}){' [PK]' if col[5] else ''}")
    conn.close()

if __name__ == "__main__":
    print("🔎 Checking table columns...")
    for t in ["asset_locations", "measurement_units"]:
        show_table_info(t)

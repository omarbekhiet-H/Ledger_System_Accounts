# -*- coding: utf-8 -*-
"""
Populate default data for Fixed Assets Database
"""

import sqlite3
import os
import sys

# =====================================================
# Database connection
# =====================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
db_path = os.path.join(project_root, "database", "fixed_assets.db")

def get_fixed_assets_db_connection():
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path)


def safe_execute(cursor, sql, params=None, section=""):
    try:
        cursor.execute(sql, params or [])
    except Exception as e:
        print(f"❌ Error in [{section}]")
        print(f"   ↳ SQL: {sql.splitlines()[0]} ...")
        print(f"   ↳ Error: {e}")


def insert_fixed_assets_default_data(conn):
    cursor = conn.cursor()
    print("▶️ Inserting default data for Fixed Assets...")

    # =====================================================
    # 1. Depreciation methods
    # =====================================================
    safe_execute(cursor, """
        INSERT OR IGNORE INTO depreciation_methods 
        (id, code, name_ar, name_en, is_active, description)
        VALUES
        (1, 'SL', 'القسط الثابت', 'Straight Line', 1, 'اهلاك بالقسط الثابت'),
        (2, 'DDB', 'الميزان المتناقص', 'Double Declining Balance', 1, 'اهلاك بالميزان المتناقص');
    """, section="depreciation_methods")

    # =====================================================
    # 2. Measurement Units
    # =====================================================
    safe_execute(cursor, """
        INSERT OR IGNORE INTO measurement_units (code, name_ar, name_en, symbol, is_active)
        VALUES
        ('MTR', 'متر', 'Meter', 'm', 1),
        ('KG', 'كيلوجرام', 'Kilogram', 'kg', 1),
        ('PCS', 'قطعة', 'Piece', 'pcs', 1);
    """, section="measurement_units")

    # =====================================================
    # 3. Location Types
    # =====================================================
    safe_execute(cursor, """
        INSERT OR IGNORE INTO location_types (id, code, name_ar, name_en, is_active)
        VALUES
        (1, 'WH', 'مخزن', 'Warehouse', 1),
        (2, 'BR', 'فرع', 'Branch', 1);
    """, section="location_types")

    # =====================================================
    # 4. Locations
    # =====================================================
    safe_execute(cursor, """
        INSERT OR IGNORE INTO asset_locations
        (loc_code, location_name_ar, location_name_en, location_type_id,
         parent_location_id, is_final, level,
         location_path, description, address, phone, responsible_person,
         capacity, current_usage, is_active, created_at, updated_at)
        VALUES
        ('MAIN', 'المخزن الرئيسي', 'Main Warehouse', 1,
         NULL, 1, 1,
         'MAIN', 'الموقع الرئيسي للشركة', 'المنطقة الصناعية', '0100000000', 'مسؤول التخزين',
         1000, 200, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('CAI', 'فرع القاهرة', 'Cairo Branch', 2,
         NULL, 1, 1,
         'CAI', 'الفرع الرئيسي بالقاهرة', 'وسط البلد - القاهرة', '0101111111', 'مدير الفرع',
         500, 120, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
    """, section="asset_locations")

    main_location = cursor.execute("SELECT id FROM asset_locations WHERE loc_code='MAIN'").fetchone()
    cairo_location = cursor.execute("SELECT id FROM asset_locations WHERE loc_code='CAI'").fetchone()
    print(f"✅ Locations: MAIN={main_location[0] if main_location else None}, CAI={cairo_location[0] if cairo_location else None}")

    # =====================================================
    # 5. Responsibles
    # =====================================================
    safe_execute(cursor, """
        INSERT OR IGNORE INTO asset_responsibles
        (id, code, name_ar, name_en, position, department, phone, email, is_active)
        VALUES
        (1, 'RES-AH', 'أحمد علي', 'Ahmed Ali', 'مدير المخازن', 'المخازن', '0102222222', 'ahmed@example.com', 1),
        (2, 'RES-MN', 'منى حسن', 'Mona Hassan', 'محاسب أصول', 'الحسابات', '0103333333', 'mona@example.com', 1);
    """, section="asset_responsibles")

    ahmed = cursor.execute("SELECT id FROM asset_responsibles WHERE code='RES-AH'").fetchone()
    mona = cursor.execute("SELECT id FROM asset_responsibles WHERE code='RES-MN'").fetchone()
    print(f"✅ Responsibles: Ahmed={ahmed[0] if ahmed else None}, Mona={mona[0] if mona else None}")

    # =====================================================
    # 6. Asset Categories
    # =====================================================
    safe_execute(cursor, """
        INSERT OR IGNORE INTO fixed_asset_categories
        (id, code, name_ar, name_en, depreciation_method_id, useful_life_years, depreciation_rate, is_active)
        VALUES
        (1, 'BLD', 'مبانى', 'Buildings', 1, 20, 5.0, 1),
        (2, 'EQP', 'معدات', 'Equipment', 2, 10, 10.0, 1),
        (3, 'FUR', 'أثاث', 'Furniture', 1, 5, 20.0, 1);
    """, section="fixed_asset_categories")

    # =====================================================
    # 7. Fixed Assets
    # =====================================================
    safe_execute(cursor, """
        INSERT OR IGNORE INTO fixed_assets
        (id, asset_code, asset_name_ar, asset_name_en, category_id,
         acquisition_date, acquisition_cost, salvage_value, current_book_value,
         accumulated_depreciation, status, location_id, quantity, unit_price,
         unit_type, responsible_id, depreciation_method_id, useful_life_years, is_active)
        VALUES
        (1, 'AST-BLD-001', 'مبنى إداري', 'Admin Building', 1,
         '2020-01-01', 1000000, 50000, 950000,
         50000, 'In Use', ?, 1, 1000000,
         'unit', ?, 1, 20, 1),
        (2, 'AST-EQP-001', 'ماكينة إنتاج', 'Production Machine', 2,
         '2021-06-15', 250000, 10000, 240000,
         10000, 'In Use', ?, 1, 250000,
         'unit', ?, 2, 10, 1),
        (3, 'AST-FUR-001', 'مكتب رئيسي', 'Main Office Desk', 3,
         '2022-03-10', 5000, 500, 4500,
         500, 'In Use', ?, 1, 5000,
         'unit', ?, 1, 5, 1);
    """, (main_location[0], ahmed[0], cairo_location[0], mona[0], cairo_location[0], mona[0]), section="fixed_assets")

    # =====================================================
    # 8. Depreciation Entries
    # =====================================================
    safe_execute(cursor, """
        INSERT OR IGNORE INTO depreciation_entries
        (asset_id, entry_date, depreciation_amount, period, is_posted)
        VALUES
        (1, '2023-12-31', 50000, 'FY2023', 1),
        (2, '2023-12-31', 25000, 'FY2023', 1),
        (3, '2023-12-31', 1000, 'FY2023', 1);
    """, section="depreciation_entries")

    # =====================================================
    # 9. Movements
    # =====================================================
    safe_execute(cursor, """
        INSERT OR IGNORE INTO asset_movements
        (asset_id, from_location_id, to_location_id, from_responsible_id, to_responsible_id, movement_date, notes)
        VALUES
        (2, ?, ?, ?, ?, '2023-05-01', 'نقل الماكينة من المخزن الرئيسي إلى فرع القاهرة');
    """, (main_location[0], cairo_location[0], ahmed[0], mona[0]), section="asset_movements")

    # =====================================================
    # 10. Maintenance
    # =====================================================
    safe_execute(cursor, """
        INSERT OR IGNORE INTO asset_maintenance
        (asset_id, maintenance_date, maintenance_type, description, cost, performed_by)
        VALUES
        (2, '2023-07-15', 'دورية', 'صيانة دورية للماكينة', 3000, 'شركة الصيانة المتخصصة');
    """, section="asset_maintenance")

    # =====================================================
    # 11. Disposal
    # =====================================================
    safe_execute(cursor, """
        INSERT OR IGNORE INTO asset_disposals
        (asset_id, disposal_date, disposal_type, proceeds, notes)
        VALUES
        (3, '2024-01-01', 'بيع', 2000, 'بيع الأثاث المستهلك');
    """, section="asset_disposals")

    # =====================================================
    # 12. Warranty
    # =====================================================
    safe_execute(cursor, """
        INSERT OR IGNORE INTO asset_warranties
        (asset_id, provider, start_date, end_date, terms, contact_info)
        VALUES
        (2, 'ضمان المصنع', '2021-06-15', '2024-06-15', 'ضمان 3 سنوات ضد عيوب الصناعة', '0123456789');
    """, section="asset_warranties")

    # =====================================================
    # 13. Insurance
    # =====================================================
    safe_execute(cursor, """
        INSERT OR IGNORE INTO asset_insurance
        (asset_id, policy_number, provider, insurance_company, start_date, end_date, premium, coverage_details)
        VALUES
        (1, 'POL12345', 'شركة التأمين الوطنية', 'National Insurance', '2020-01-01', '2025-01-01', 50000, 'تغطية شاملة للمبنى');
    """, section="asset_insurance")

    conn.commit()
    print("🎉 Default data inserted successfully.")


if __name__ == "__main__":
    conn = get_fixed_assets_db_connection()
    insert_fixed_assets_default_data(conn)
    conn.close()

import sqlite3
import os
import sys
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.db_connection import get_manufacturing_db_connection


def insert_default_data(conn):
    try:
        cursor = conn.cursor()

        sql_script = """
        -- بيانات تجريبية لأوامر التشغيل ونظام التصنيع

        INSERT INTO job_orders (job_number, job_title, job_description, job_type, priority, status, request_date, planned_start_date, planned_end_date, actual_start_date, actual_end_date, created_by_external_id)
        VALUES 
        ('JO-0001', 'تصنيع منتج نهائي A', 'طلب إنتاج 100 وحدة من المنتج A', 'إنتاج', 'high', 'in_progress', '2025-09-01', '2025-09-02', '2025-09-10', '2025-09-02', NULL, 'system'),
        ('JO-0002', 'صيانة خط الإنتاج B', 'صيانة وقائية لخط الإنتاج B', 'صيانة', 'medium', 'planned', '2025-09-05', '2025-09-06', '2025-09-07', NULL, NULL, 'system'),
        ('JO-0003', 'إصلاح ماكينة C', 'إصلاح عطل كهربائي في ماكينة C', 'إصلاح', 'urgent', 'pending', '2025-09-10', '2025-09-11', NULL, NULL, NULL, 'system');

        INSERT INTO job_order_material_requirements (job_order_id, item_id, quantity_required, unit_id, estimated_cost, status)
        VALUES
        (1, 101, 50, 1, 500, 'issued'),
        (1, 102, 30, 1, 300, 'reserved'),
        (1, 103, 20, 1, 200, 'pending');

        INSERT INTO job_order_material_issues (job_order_id, material_requirement_id, item_id, quantity_issued, unit_id, unit_cost, total_cost, issued_by_external_id, issued_from_warehouse_id)
        VALUES
        (1, 1, 101, 50, 1, 10, 500, 'warehouse_user', 1);

        INSERT INTO job_order_material_consumption (job_order_id, material_issue_id, item_id, quantity_consumed, unit_id, consumed_by_external_id)
        VALUES
        (1, 1, 101, 40, 1, 'operator_01');

        INSERT INTO job_order_outputs (job_order_id, item_id, quantity_produced, unit_id, quality_status, production_cost)
        VALUES
        (1, 201, 90, 1, 'passed', 1500),
        (1, 202, 5, 1, 'rework', 100);

        INSERT INTO job_order_progress (job_order_id, progress_percentage, current_stage, status, reported_by_external_id)
        VALUES
        (1, 25, 'المرحلة الأولى', 'in_progress', 'supervisor_01'),
        (1, 50, 'المرحلة الثانية', 'in_progress', 'supervisor_01'),
        (1, 100, 'إنتاج كامل', 'completed', 'supervisor_01');

        INSERT INTO job_order_labor (job_order_id, external_employee_id, role, assigned_hours, actual_hours_worked, hourly_rate, labor_cost)
        VALUES
        (1, 'EMP001', 'مشغل ماكينة', 8, 7, 15, 105),
        (1, 'EMP002', 'فني صيانة', 6, 6, 20, 120);

        INSERT INTO job_order_additional_costs (job_order_id, cost_type, cost_description, amount, currency, vendor_name)
        VALUES
        (1, 'قطع غيار', 'شراء قطع غيار إضافية', 200, 'USD', 'Vendor A'),
        (1, 'نقل', 'تكلفة نقل المواد الخام', 150, 'USD', 'Logistics Co');

        INSERT INTO job_order_comments (job_order_id, comment_text, comment_type, commented_by_external_id)
        VALUES
        (1, 'العمل يسير حسب الخطة', 'general', 'supervisor_01'),
        (1, 'تم اكتشاف عيب في المادة الخام', 'quality', 'quality_team');
        """

        cursor.executescript(sql_script)
        conn.commit()
        print("✅ تم إدخال البيانات الافتراضية بنجاح")

    except Exception as e:
        print(f"❌ خطأ في إدخال البيانات: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()


if __name__ == "__main__":
    conn = get_manufacturing_db_connection()
    insert_default_data(conn)
    conn.close()

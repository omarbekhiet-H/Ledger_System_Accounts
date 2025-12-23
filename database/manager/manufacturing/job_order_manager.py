# database_queries.py
import sqlite3
import os
import sys
from datetime import datetime, timedelta

# إضافة مسار المشروع الجذري
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.db_connection import get_manufacturing_db_connection, get_inventory_db_connection, get_financials_db_connection, get_users_db_connection

class DatabaseManager:
    """مدير قواعد البيانات - يحتوي على جميع الاستعلامات"""
    
    @staticmethod
    def fetch_all(connection_func, query, params=()):
        """تنفيذ استعلام SELECT وإرجاع جميع النتائج"""
        try:
            conn = connection_func()
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(query, params)
            result = cur.fetchall()
            conn.close()
            return result
        except Exception as e:
            print(f"DB Error [{connection_func.__name__}]: {e}")
            return []

    @staticmethod
    def execute_query(connection_func, query, params=()):
        """تنفيذ استعلامات التعديل (INSERT, UPDATE, DELETE)"""
        try:
            conn = connection_func()
            cur = conn.cursor()
            cur.execute(query, params)
            lastrowid = cur.lastrowid
            conn.commit()
            conn.close()
            return lastrowid
        except Exception as e:
            print(f"DB Error [{connection_func.__name__}]: {e}")
            return None

    @staticmethod
    def get_table_columns(connection_func, table_name):
        """الحصول على أسماء أعمدة جدول معين"""
        try:
            conn = connection_func()
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info({table_name})")
            columns = [column[1] for column in cur.fetchall()]
            conn.close()
            return columns
        except Exception as e:
            print(f"Error getting columns for {table_name}: {e}")
            return []

class JobOrderQueries:
    """استعلامات خاصة بأوامر التشغيل"""
    
    @staticmethod
    def get_next_job_number():
        """الحصول على رقم الأمر التالي"""
        rows = DatabaseManager.fetch_all(
            get_manufacturing_db_connection, 
            "SELECT MAX(id) as last_id FROM job_orders"
        )
        last_id = rows[0]["last_id"] if rows and rows[0]["last_id"] else 0
        return f"JO-{last_id+1:04d}"

    @staticmethod
    def search_orders(search_text):
        """البحث عن أوامر التشغيل"""
        query = """
            SELECT jo.id, jo.job_number, c.name_ar as customer, jo.request_date as order_date, 
                   jo.status, jo.estimated_cost as grand_total 
            FROM job_orders jo 
            LEFT JOIN customers c ON jo.customer_id = c.id 
            WHERE jo.job_number LIKE ? OR c.name_ar LIKE ? OR jo.job_description LIKE ?
            ORDER BY jo.request_date DESC
        """
        params = (f'%{search_text}%', f'%{search_text}%', f'%{search_text}%')
        return DatabaseManager.fetch_all(get_manufacturing_db_connection, query, params)

    @staticmethod
    def save_job_order(job_data):
        """حفظ أمر تشغيل جديد"""
        query = """
            INSERT INTO job_orders (
                job_number, job_title, job_description, job_type, priority, status,
                customer_id, request_date, planned_start_date, planned_end_date,
                estimated_cost, external_system
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return DatabaseManager.execute_query(get_manufacturing_db_connection, query, job_data)

    @staticmethod
    def update_job_order(job_data):
        """تحديث أمر تشغيل موجود"""
        query = """
            UPDATE job_orders SET 
                job_title=?, job_description=?, customer_id=?, request_date=?, 
                planned_end_date=?, estimated_cost=?
            WHERE id=?
        """
        return DatabaseManager.execute_query(get_manufacturing_db_connection, query, job_data)

    @staticmethod
    def delete_job_order(job_order_id):
        """حذف أمر تشغيل"""
        # حذف التفاصيل أولاً
        tables = [
            "job_order_material_requirements",
            "job_order_labor", 
            "job_order_additional_costs"
        ]
        
        for table in tables:
            DatabaseManager.execute_query(
                get_manufacturing_db_connection,
                f"DELETE FROM {table} WHERE job_order_id = ?",
                (job_order_id,)
            )
        
        # ثم حذف الأمر الرئيسي
        return DatabaseManager.execute_query(
            get_manufacturing_db_connection,
            "DELETE FROM job_orders WHERE id = ?",
            (job_order_id,)
        )

    @staticmethod
    def load_job_order(order_number):
        """تحميل بيانات أمر التشغيل"""
        query = """
            SELECT jo.*, c.name_ar as customer_name, c.customer_code 
            FROM job_orders jo 
            LEFT JOIN customers c ON jo.customer_id = c.id 
            WHERE jo.job_number = ?
        """
        return DatabaseManager.fetch_all(get_manufacturing_db_connection, query, (order_number,))

    @staticmethod
    def load_order_details(job_order_id):
        """تحميل تفاصيل أمر التشغيل"""
        details = {}
        
        # تحميل المواد
        details['materials'] = DatabaseManager.fetch_all(
            get_manufacturing_db_connection,
            """SELECT jomr.*, i.item_code, i.item_name_ar, u.name_ar as unit_name
            FROM job_order_material_requirements jomr
            LEFT JOIN items i ON jomr.item_id = i.id
            LEFT JOIN units u ON jomr.unit_id = u.id
            WHERE jomr.job_order_id = ?""",
            (job_order_id,)
        )
        
        # تحميل العمالة
        details['labor'] = DatabaseManager.fetch_all(
            get_manufacturing_db_connection,
            "SELECT * FROM job_order_labor WHERE job_order_id = ?",
            (job_order_id,)
        )
        
        # تحميل المصروفات
        details['costs'] = DatabaseManager.fetch_all(
            get_manufacturing_db_connection,
            "SELECT * FROM job_order_additional_costs WHERE job_order_id = ?",
            (job_order_id,)
        )
        
        return details

    @staticmethod
    def save_material_requirements(job_order_id, materials_data):
        """حفظ متطلبات المواد"""
        for material in materials_data:
            DatabaseManager.execute_query(
                get_manufacturing_db_connection,
                """INSERT INTO job_order_material_requirements 
                (job_order_id, item_id, quantity_required, unit_id, estimated_cost, status)
                VALUES (?, ?, ?, ?, ?, ?)""",
                material
            )

    @staticmethod
    def save_labor_requirements(job_order_id, labor_data):
        """حفظ متطلبات العمالة"""
        for labor in labor_data:
            DatabaseManager.execute_query(
                get_manufacturing_db_connection,
                """INSERT INTO job_order_labor 
                (job_order_id, external_employee_id, role, assigned_hours, hourly_rate, labor_cost)
                VALUES (?, ?, ?, ?, ?, ?)""",
                labor
            )

    @staticmethod
    def save_additional_costs(job_order_id, costs_data):
        """حفظ التكاليف الإضافية"""
        for cost in costs_data:
            DatabaseManager.execute_query(
                get_manufacturing_db_connection,
                """INSERT INTO job_order_additional_costs 
                (job_order_id, cost_type, cost_description, amount, currency)
                VALUES (?, ?, ?, ?, ?)""",
                cost
            )

    @staticmethod
    def calculate_end_date(start_date):
        """حساب تاريخ الانتهاء المتوقع"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = start + timedelta(days=7)
        return end.strftime("%Y-%m-%d")

class CustomerQueries:
    """استعلامات خاصة بالعملاء"""
    
    @staticmethod
    def get_customers():
        """الحصول على قائمة العملاء"""
        return DatabaseManager.fetch_all(
            get_inventory_db_connection, 
            "SELECT id, name_ar, customer_code FROM customers WHERE is_active=1"
        )

    @staticmethod
    def extract_customer_id(customer_text):
        """استخراج معرف العميل من النص"""
        if ' - ' in customer_text:
            code_part = customer_text.split(' - ')[0]
            rows = DatabaseManager.fetch_all(
                get_inventory_db_connection,
                "SELECT id FROM customers WHERE customer_code = ? OR name_ar LIKE ?", 
                (code_part, f'%{customer_text}%')
            )
            if rows:
                return rows[0]["id"]
        return None

class ItemQueries:
    """استعلامات خاصة بالأصناف"""
    
    @staticmethod
    def get_items():
        """الحصول على قائمة الأصناف"""
        # فحص أعمدة جدول الأصناف أولاً
        columns = DatabaseManager.get_table_columns(get_inventory_db_connection, "items")
        
        code_column = "item_code" if "item_code" in columns else "code"
        name_column = "item_name_ar" if "item_name_ar" in columns else "item_name"
        unit_column = "unit_name" if "unit_name" in columns else "unit"
        
        query = f"SELECT {code_column}, {name_column}, {unit_column} FROM items WHERE is_active=1"
        return DatabaseManager.fetch_all(get_inventory_db_connection, query)

    @staticmethod
    def get_item_by_code(item_code):
        """الحصول على صنف بواسطة الكود"""
        rows = DatabaseManager.fetch_all(
            get_inventory_db_connection,
            "SELECT id, item_name_ar, unit_name FROM items WHERE item_code = ?",
            (item_code,)
        )
        return rows[0] if rows else None

    @staticmethod
    def get_unit_id(unit_name):
        """الحصول على معرف الوحدة"""
        rows = DatabaseManager.fetch_all(
            get_inventory_db_connection,
            "SELECT id FROM units WHERE name_ar = ? OR name_en = ?", 
            (unit_name, unit_name)
        )
        if rows:
            return rows[0]["id"]
        return 1

class UserQueries:
    """استعلامات خاصة بالمستخدمين"""
    
    @staticmethod
    def get_users():
        """الحصول على قائمة المستخدمين"""
        columns = DatabaseManager.get_table_columns(get_users_db_connection, "users")
        
        code_column = "username" if "username" in columns else "user_code"
        name_column = "name_ar" if "name_ar" in columns else "full_name"
        title_column = "job_title" if "job_title" in columns else "role"
        
        query = f"SELECT {code_column}, {name_column}, {title_column} FROM users WHERE is_active=1"
        return DatabaseManager.fetch_all(get_users_db_connection, query)

class AccountQueries:
    """استعلامات خاصة بالحسابات"""
    
    @staticmethod
    def get_accounts():
        """الحصول على قائمة الحسابات"""
        columns = DatabaseManager.get_table_columns(get_financials_db_connection, "accounts")
        
        code_column = "acc_code" if "acc_code" in columns else "account_code"
        name_column = "account_name_ar" if "account_name_ar" in columns else "account_name"
        
        query = f"SELECT {code_column}, {name_column} FROM accounts WHERE is_active=1"
        return DatabaseManager.fetch_all(get_financials_db_connection, query)
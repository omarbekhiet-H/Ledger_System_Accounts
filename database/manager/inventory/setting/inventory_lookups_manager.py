# database/inventory_lookups_manager.py

import sqlite3
from database.base_manager import BaseManager
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox

class InventoryLookupsManager(BaseManager):
    """
    مسؤول عن إدارة الجداول المرجعية المتعلقة بجزء المخزون:
    الوحدات، فئات الأصناف، المستودعات، الأقسام.
    يتصل بقاعدة بيانات inventory.db
    """
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func)

    def _generate_next_code(self, table_name, prefix):
        """يولد الرمز التالي بناءً على أكبر رمز موجود في الجدول."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            query = f"SELECT MAX(code) FROM {table_name} WHERE code LIKE ? || '%' COLLATE NOCASE"
            cursor.execute(query, (prefix,))
            max_code = cursor.fetchone()[0]

            if max_code:
                if max_code.lower().startswith(prefix.lower()):
                    try:
                        num_part = int(max_code[len(prefix):])
                        next_num = num_part + 1
                    except ValueError:
                        next_num = 1
                else:
                    next_num = 1
            else:
                next_num = 1
            return f"{prefix}{next_num:03d}"
        except sqlite3.Error as e:
            print(f"Error generating next code for {table_name}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    # ======================================================
    # دوال إدارة الوحدات (units)
    # ======================================================

    def add_unit(self, name_ar, name_en=None):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            code = self._generate_next_code('units', 'UNT')
            if not code: return False

            cursor.execute("""
                INSERT INTO units (code, name_ar, name_en)
                VALUES (?, ?, ?)
            """, (code, name_ar, name_en))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"اسم الوحدة '{name_ar}' أو رمزها موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة الوحدة: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_units(self):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM units")
            units = cursor.fetchall()
            
            columns = [column[0] for column in cursor.description]
            result = []
            for unit in units:
                result.append(dict(zip(columns, unit)))
            
            return result
        except Exception as e:
            print(f"Unexpected error in get_all_units: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    def get_unit_by_code(self, unit_code):
    #def get_unit_by_id(self, unit_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, name_ar, name_en, is_active FROM units WHERE id = ?", (unit_code,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting unit by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()
               

    def update_unit(self, unit_id, name_ar, name_en=None, is_active=1):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # التحقق من عدم وجود تكرار للأسماء
            cursor.execute("SELECT id FROM units WHERE name_ar = ? AND id != ?", (name_ar, unit_id))
            if cursor.fetchone():
                QMessageBox.warning(None, "تكرار", f"اسم الوحدة '{name_ar}' موجود بالفعل.")
                return False

            cursor.execute("""
                UPDATE units
                SET name_ar = ?, name_en = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (name_ar, name_en, is_active, unit_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث الوحدة: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_unit(self, unit_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحقق من عدم وجود روابط في جداول أخرى
            tables_to_check = [
                ("items", "unit_id"),
                ("inventory_transactions", "unit_id")
            ]
            
            for table, column in tables_to_check:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} = ?", (unit_id,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.critical(None, "خطأ في الحذف", f"لا يمكن حذف هذه الوحدة لأنها مستخدمة في {table}.")
                    return False

            cursor.execute("DELETE FROM units WHERE id = ?", (unit_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند حذف الوحدة: {e}")
            return False
        finally:
            if conn:
                conn.close()

    # ======================================================
    # دوال إدارة فئات الأصناف (item_categories)
    # ======================================================

    def add_item_category(self, name_ar, name_en=None):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            code = self._generate_next_code('item_categories', 'CAT')
            if not code: return False

            cursor.execute("""
                INSERT INTO item_categories (code, name_ar, name_en)
                VALUES (?, ?, ?)
            """, (code, name_ar, name_en))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"اسم فئة الصنف '{name_ar}' أو رمزها موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة فئة الصنف: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_item_categories(self):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, name_ar, name_en, is_active FROM item_categories ORDER BY name_ar")
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب فئات الأصناف: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_item_category_by_code(self, code):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, name_ar, name_en, is_active FROM item_categories WHERE id = ?", (code,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting item category by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_item_category(self, category_id, name_ar, name_en=None, is_active=1):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # التحقق من عدم وجود تكرار للأسماء
            cursor.execute("SELECT id FROM item_categories WHERE name_ar = ? AND id != ?", (name_ar, category_id))
            if cursor.fetchone():
                QMessageBox.warning(None, "تكرار", f"اسم فئة الصنف '{name_ar}' موجود بالفعل.")
                return False

            cursor.execute("""
                UPDATE item_categories
                SET name_ar = ?, name_en = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (name_ar, name_en, is_active, category_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث فئة الصنف: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_item_category(self, category_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحقق من عدم وجود روابط في جداول أخرى
            tables_to_check = [
                ("items", "category_id"),
                ("inventory_transactions", "category_id")
            ]
            
            for table, column in tables_to_check:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} = ?", (category_id,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.critical(None, "خطأ في الحذف", f"لا يمكن حذف فئة الصنف هذه لأنها مستخدمة في {table}.")
                    return False

            cursor.execute("DELETE FROM item_categories WHERE id = ?", (category_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند حذف فئة الصنف: {e}")
            return False
        finally:
            if conn:
                conn.close()

    # ======================================================
    # دوال إدارة المستودعات (warehouses)
    # ======================================================

    def add_warehouse(self, name_ar, name_en=None, location=None):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            code = self._generate_next_code('warehouses', 'WH')
            if not code: return False

            cursor.execute("""
                INSERT INTO warehouses (code, name_ar, name_en, location)
                VALUES (?, ?, ?, ?)
            """, (code, name_ar, name_en, location))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"اسم المستودع '{name_ar}' أو رمزه موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة المستودع: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_warehouses(self):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, name_ar, name_en, location, is_active FROM warehouses ORDER BY name_ar")
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب المستودعات: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_warehouse_by_id(self, warehouse_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, name_ar, name_en, location, is_active FROM warehouses WHERE id = ?", (warehouse_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting warehouse by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_warehouse(self, id, code, name_ar, name_en=None, location=None, is_active=1):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # التحقق من عدم وجود تكرار للأسماء أو الرموز
            cursor.execute("SELECT id FROM warehouses WHERE (name_ar = ? OR code = ?) AND id != ?", 
                         (name_ar, code, id))
            if cursor.fetchone():
                QMessageBox.warning(None, "تكرار", "اسم المستودع أو رمزه موجود بالفعل.")
                return False

            cursor.execute("""
                UPDATE warehouses
                SET code = ?, name_ar = ?, name_en = ?, location = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (code, name_ar, name_en, location, is_active, id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث المستودع: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_warehouse(self, warehouse_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحقق من عدم وجود روابط في جداول أخرى
            tables_to_check = [
                ("stock_transactions", "warehouse_id"),
                ("inventory_items", "warehouse_id"),
                ("inventory_transactions", "warehouse_id")
            ]
            
            for table, column in tables_to_check:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} = ?", (warehouse_id,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.critical(None, "خطأ في الحذف", f"لا يمكن حذف هذا المستودع لأنه مستخدم في {table}.")
                    return False

            cursor.execute("DELETE FROM warehouses WHERE id = ?", (warehouse_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند حذف المستودع: {e}")
            return False
        finally:
            if conn:
                conn.close()

    # ======================================================
    # دوال إدارة الأقسام (departments)
    # ======================================================

    def add_department(self, name_ar, name_en=None):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            code = self._generate_next_code('departments', 'DEPT')
            if not code: return False

            cursor.execute("""
                INSERT INTO departments (code, name_ar, name_en)
                VALUES (?, ?, ?)
            """, (code, name_ar, name_en))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"اسم القسم '{name_ar}' أو رمزه موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة القسم: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_departments(self):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, name_ar, name_en, is_active FROM departments ORDER BY name_ar")
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب الأقسام: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_department_by_id(self, department_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, name_ar, name_en, is_active FROM departments WHERE id = ?", (department_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting department by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_department(self, department_id, name_ar, name_en=None, is_active=1):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # التحقق من عدم وجود تكرار للأسماء
            cursor.execute("SELECT id FROM departments WHERE name_ar = ? AND id != ?", (name_ar, department_id))
            if cursor.fetchone():
                QMessageBox.warning(None, "تكرار", f"اسم القسم '{name_ar}' موجود بالفعل.")
                return False

            cursor.execute("""
                UPDATE departments
                SET name_ar = ?, name_en = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (name_ar, name_en, is_active, department_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث القسم: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_department(self, department_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحقق من عدم وجود روابط في جداول أخرى
            tables_to_check = [
                ("inventory_transactions", "department_id"),
                ("requisitions", "department_id")
            ]
            
            for table, column in tables_to_check:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} = ?", (department_id,))
                if cursor.fetchone()[0] > 0:
                    QMessageBox.critical(None, "خطأ في الحذف", f"لا يمكن حذف هذا القسم لأنه مستخدم في {table}.")
                    return False

            cursor.execute("DELETE FROM departments WHERE id = ?", (department_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند حذف القسم: {e}")
            return False
        finally:
            if conn:
                conn.close()
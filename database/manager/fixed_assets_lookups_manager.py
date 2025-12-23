# database/fixed_assets_lookups_manager.py

import sqlite3
from ..base_manager import BaseManager
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox

class FixedAssetsLookupsManager(BaseManager):
    """
    مسؤول عن إدارة الجداول المرجعية المتعلقة بجزء الأصول الثابتة:
    فئات الأصول الثابتة.
    يتصل بقاعدة بيانات fixed_assets.db
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
    # دوال إدارة فئات الأصول الثابتة (fixed_asset_categories)
    # ======================================================

    def add_fixed_asset_category(self, name_ar, name_en=None):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            code = self._generate_next_code('fixed_asset_categories', 'FAC')
            if not code: return False

            cursor.execute("""
                INSERT INTO fixed_asset_categories (code, name_ar, name_en)
                VALUES (?, ?, ?)
            """, (code, name_ar, name_en))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"اسم فئة الأصل '{name_ar}' أو رمزها '{code}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة فئة الأصل: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_fixed_asset_categories(self):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, name_ar, name_en, is_active FROM fixed_asset_categories ORDER BY name_ar")
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب فئات الأصول: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_fixed_asset_category_by_id(self, category_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, name_ar, name_en, is_active FROM fixed_asset_categories WHERE id = ?", (category_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting fixed asset category by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_fixed_asset_category(self, category_id, name_ar, name_en=None, is_active=1):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE fixed_asset_categories
                SET name_ar = ?, name_en = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (name_ar, name_en, is_active, category_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"اسم فئة الأصل '{name_ar}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث فئة الأصل: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_fixed_asset_category(self, category_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحقق من عدم وجود روابط (مثال: في جدول fixed_assets)
            cursor.execute("SELECT COUNT(*) FROM fixed_assets WHERE category_id = ?", (category_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف فئة الأصل هذه لأنها مستخدمة في الأصول الثابتة.")
                return False

            query = "DELETE FROM fixed_asset_categories WHERE id = ?"
            cursor.execute(query, (category_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف فئة الأصل هذه لأنها مرتبطة بسجلات أخرى في النظام.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند حذف فئة الأصل: {e}")
            return False
        finally:
            if conn:
                conn.close()
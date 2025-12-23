# database/fixed_asset_manager.py

import sqlite3
from ..base_manager import BaseManager # تأكد من استيراد BaseManager
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox # استيراد QMessageBox

class FixedAssetManager(BaseManager): # يجب أن يرث من BaseManager
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func) # استدعاء __init__ الخاص بـ BaseManager

    def _generate_next_code(self, table_name, prefix):
        """يولد الرمز التالي بناءً على أكبر رمز موجود في الجدول."""
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
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

    def add_fixed_asset(self, asset_code, name_ar, name_en, category_id, acquisition_date,
                        acquisition_cost, useful_life_years, depreciation_method, salvage_value,
                        asset_account_id, accumulated_dep_account_id, depreciation_expense_account_id,
                        country_of_origin=None, serial_number=None, model=None, manufacturer=None, location=None,
                        is_active=1):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            # تحقق من وجود الفئة ورقم الحسابات قبل الإضافة
            # هذه التحققات يجب أن تتم عبر Managers المناسبة
            # (مثال: FixedAssetsLookupsManager و AccountManager)
            # ولكن مبدئياً سنفترض أنها موجودة في هذا النطاق أو ستتم معالجتها في مستوى أعلى.

            cursor.execute("""
                INSERT INTO fixed_assets (
                    code, name_ar, name_en, category_id, acquisition_date,
                    acquisition_cost, useful_life_years, depreciation_method, salvage_value,
                    asset_account_id, accumulated_dep_account_id, depreciation_expense_account_id,
                    country_of_origin, serial_number, model, manufacturer, location, is_active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (asset_code, name_ar, name_en, category_id, acquisition_date,
                  acquisition_cost, useful_life_years, depreciation_method, salvage_value,
                  asset_account_id, accumulated_dep_account_id, depreciation_expense_account_id,
                  country_of_origin, serial_number, model, manufacturer, location, is_active))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"رمز الأصل '{asset_code}' أو الرقم التسلسلي '{serial_number}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة الأصل الثابت: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_fixed_assets(self):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    fa.id, fa.code, fa.name_ar, fa.name_en, fa.category_id,
                    fac.name_ar AS name_ar, # جلب اسم الفئة
                    fa.acquisition_date, fa.acquisition_cost, fa.useful_life_years,
                    fa.depreciation_method, fa.salvage_value, fa.accumulated_depreciation,
                    fa.current_book_value, fa.is_active,
                    fa.asset_account_id, fa.accumulated_dep_account_id, fa.depreciation_expense_account_id,
                    fa.country_of_origin, fa.serial_number, fa.model, fa.manufacturer, fa.location
                FROM fixed_assets fa
                LEFT JOIN fixed_asset_categories fac ON fa.category_id = fac.id
                ORDER BY fa.name_ar
            """)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب الأصول الثابتة: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_fixed_asset_by_id(self, asset_id):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    fa.id, fa.code, fa.name_ar, fa.name_en, fa.category_id,
                    fac.name_ar AS name_ar,
                    fa.acquisition_date, fa.acquisition_cost, fa.useful_life_years,
                    fa.depreciation_method, fa.salvage_value, fa.accumulated_depreciation,
                    fa.current_book_value, fa.is_active,
                    fa.asset_account_id, fa.accumulated_dep_account_id, fa.depreciation_expense_account_id,
                    fa.country_of_origin, fa.serial_number, fa.model, fa.manufacturer, fa.location
                FROM fixed_assets fa
                LEFT JOIN fixed_asset_categories fac ON fa.category_id = fac.id
                WHERE fa.id = ?
            """, (asset_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting fixed asset by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_fixed_asset_by_serial_number(self, serial_number):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id, code, name_ar, name_en, category_id, acquisition_date,
                    acquisition_cost, useful_life_years, depreciation_method, salvage_value,
                    accumulated_depreciation, current_book_value, is_active, asset_account_id, accumulated_dep_account_id,
                    depreciation_expense_account_id, country_of_origin, serial_number, model, manufacturer, location
                FROM fixed_assets
                WHERE serial_number = ? COLLATE NOCASE
            """, (serial_number,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting fixed asset by serial number: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_fixed_asset(self, asset_id, asset_code, name_ar, name_en, category_id, acquisition_date,
                          acquisition_cost, useful_life_years, depreciation_method, salvage_value,
                          asset_account_id, accumulated_dep_account_id, depreciation_expense_account_id,
                          country_of_origin=None, serial_number=None, model=None, manufacturer=None, location=None,
                          is_active=1):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE fixed_assets
                SET
                    code = ?, name_ar = ?, name_en = ?, category_id = ?, acquisition_date = ?,
                    acquisition_cost = ?, useful_life_years = ?, depreciation_method = ?, salvage_value = ?,
                    asset_account_id = ?, accumulated_dep_account_id = ?, depreciation_expense_account_id = ?,
                    country_of_origin = ?, serial_number = ?, model = ?, manufacturer = ?, location = ?,
                    is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (asset_code, name_ar, name_en, category_id, acquisition_date,
                  acquisition_cost, useful_life_years, depreciation_method, salvage_value,
                  asset_account_id, accumulated_dep_account_id, depreciation_expense_account_id,
                  country_of_origin, serial_number, model, manufacturer, location, is_active, asset_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"رمز الأصل '{asset_code}' أو الرقم التسلسلي '{serial_number}' موجود بالفعل لأصل آخر.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث الأصل الثابت: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_fixed_asset(self, asset_id):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # (يمكن إضافة تحقق من الاستخدام في المستقبل إذا كانت هناك جداول تستخدم asset_id)

            query = "DELETE FROM fixed_assets WHERE id = ?"
            cursor.execute(query, (asset_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذا الأصل الثابت لأنه مرتبط بسجلات أخرى في النظام (مثل قيود الإهلاك).")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند حذف الأصل الثابت: {e}")
            return False
        finally:
            if conn:
                conn.close()
                
    def calculate_depreciation_for_period(self, asset_id, start_date, end_date):
        # هذه الدالة تتطلب الوصول إلى بيانات القيد اليومي
        # يجب أن يتم تنفيذها بعناية أو نقلها إلى JournalManager
        # أو يتم التأكد من أن FixedAssetManager لديه وصول إلى JournalManager
        # حالياً، سأفترض أنها تحسب الإهلاك فقط دون إنشاء قيود يومية
        # (الجزء الذي يقوم بإنشاء القيود اليومية يجب أن يكون في JournalManager)
        
        asset = self.get_fixed_asset_by_id(asset_id)
        if not asset:
            QMessageBox.warning(None, "خطأ", "الأصل غير موجود.")
            return 0.0

        acquisition_cost = asset['acquisition_cost']
        salvage_value = asset['salvage_value']
        useful_life_years = asset['useful_life_years']
        depreciation_method = asset['depreciation_method']
        
        # تحويل تواريخ الإهلاك إلى كائنات datetime
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # حساب عدد الأيام في الفترة
        days_in_period = (end_dt - start_dt).days + 1
        
        # حساب الإهلاك اليومي
        if useful_life_years == 0: # تجنب القسمة على صفر
             return 0.0
             
        if depreciation_method == 'Straight-Line':
            total_depreciable_amount = acquisition_cost - salvage_value
            annual_depreciation = total_depreciable_amount / useful_life_years
            daily_depreciation = annual_depreciation / 365.0
            depreciation_for_period = daily_depreciation * days_in_period
        else:
            QMessageBox.warning(None, "خطأ", f"طريقة الإهلاك '{depreciation_method}' غير مدعومة.")
            return 0.0
            
        # التأكد من أن الإهلاك لا يتجاوز القيمة القابلة للإهلاك المتبقية
        max_depreciation_allowed = asset['current_book_value'] - salvage_value
        return min(depreciation_for_period, max_depreciation_allowed)

    def update_asset_depreciation(self, asset_id, depreciation_amount, new_accumulated_dep, new_current_book_value):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE fixed_assets
                SET
                    accumulated_depreciation = ?,
                    current_book_value = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_accumulated_dep, new_current_book_value, asset_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث إهلاك الأصل: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def update_asset_active_status(self, asset_id, is_active):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE fixed_assets
                SET is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (is_active, asset_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث حالة نشاط الأصل: {e}")
            return False
        finally:
            if conn:
                conn.close()
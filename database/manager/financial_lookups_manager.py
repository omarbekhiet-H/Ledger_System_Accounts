# database/financial_lookups_manager.py

import sqlite3
import os
import sys
from PyQt5.QtWidgets import QMessageBox

# =====================================================================
# تصحيح مسار المشروع الجذر لتمكين الاستيراد الصحيح
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.base_manager import BaseManager

class FinancialLookupsManager(BaseManager):
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func)
    
    # في FinancialLookupsManager

        
     # في ملف database/manager/financial_lookups_manager.py
class FinancialLookupsManager(BaseManager):
    # ... الدوال الحالية ...
    
    def get_user_by_id(self, user_id):
        """Retrieves a user by their ID."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: 
                return None
                
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, full_name FROM Users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            
            if result:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, result))
            return None
        except sqlite3.Error as e:
            print(f"Error fetching user by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()
                   
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
                        next_num = 1 # Fallback if numeric part is not valid
                else:
                    next_num = 1 # Fallback if prefix doesn't match
            else:
                next_num = 1
            return f"{prefix}{next_num:03d}" # تنسيق بثلاثة أرقام (مثال: DT001)
        except sqlite3.Error as e:
            print(f"Error generating next code for {table_name}: {e}")
            return None
        finally:
            if conn:
                conn.close()

# ======================================================
    # دوال إدارة أنواع المستندات (document_types)
    # ======================================================

    def add_document_type(self, name_ar, name_en=None):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            code = self._generate_next_code('document_types', 'DT')
            if not code: return False

            cursor.execute("""
                INSERT INTO document_types (code, name_ar, name_en)
                VALUES (?, ?, ?)
            """, (code, name_ar, name_en))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"اسم نوع المستند '{name_ar}' أو رمزه '{code}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة نوع المستند: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_document_types(self):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, name_ar, name_en, is_active FROM document_types ORDER BY name_ar")
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب أنواع المستندات: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_document_type_by_id(self, type_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, name_ar, name_en, is_active FROM document_types WHERE id = ?", (type_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting document type by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_document_type(self, type_id, name_ar, name_en=None, is_active=1):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE document_types
                SET name_ar = ?, name_en = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (name_ar, name_en, is_active, type_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"اسم نوع المستند '{name_ar}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث نوع المستند: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def delete_document_type(self, type_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحقق من عدم وجود روابط قبل الحذف الفعلي
            # مثال: إذا كان نوع المستند مستخدماً في جدول journal_entries
            cursor.execute("SELECT COUNT(*) FROM journal_entries WHERE transaction_type_id = ?", (type_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف نوع المستند هذا لأنه مستخدم في قيود يومية.")
                return False

            query = "DELETE FROM document_types WHERE id = ?"
            cursor.execute(query, (type_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف نوع المستند هذا لأنه مرتبط بسجلات أخرى في النظام.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند حذف نوع المستند: {e}")
            return False
        finally:
            if conn:
                conn.close()


    # ======================================================
    # دوال إدارة العملات (currencies)
    # ======================================================

    def add_currency(self, code, name_ar, name_en=None, symbol=None, exchange_rate=1.0, is_base_currency=0, is_active=1):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # إذا كانت العملة الجديدة هي الأساسية، تأكد من أن لا توجد عملة أساسية أخرى
            if is_base_currency == 1:
                if not self._ensure_single_base_currency(None): # None لأنها إضافة جديدة
                    return False

            # تم إضافة 'is_base_currency' هنا في جملة INSERT
            cursor.execute("""
                INSERT INTO currencies (code, name_ar, name_en, symbol, exchange_rate, is_base_currency, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (code, name_ar, name_en, symbol, exchange_rate, is_base_currency, is_active))
            conn.commit()
            QMessageBox.information(None, "نجاح", "تمت إضافة العملة بنجاح.")
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"رمز العملة '{code}' أو اسمها العربي '{name_ar}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة العملة: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_currencies(self):
        """يجلب جميع العملات."""
        # تم إضافة 'is_base_currency' هنا في جملة SELECT
        query = "SELECT id, code, name_ar, name_en, symbol, exchange_rate, is_base_currency, is_active FROM currencies ORDER BY name_ar"
        return self.fetch_all(query)
    
    # في class FinancialLookupsManager
    def get_all_entry_types(self):
        """
        يجلب جميع أنواع القيود اليومية (transaction_types أو entry_types)
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None:
                return []
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, name_ar, name_en, is_active FROM transaction_types ORDER BY name_ar")
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب أنواع القيود: {e}")
            return []
        finally:
            if conn:
                conn.close()


    def get_currency_by_id(self, currency_id):
        """يجلب عملة بواسطة ID."""
        # تم إضافة 'is_base_currency' هنا في جملة SELECT
        query = "SELECT id, code, name_ar, name_en, symbol, exchange_rate, is_base_currency, is_active FROM currencies WHERE id = ?"
        return self.fetch_one(query, (currency_id,))

    def update_currency(self, id, code, name_ar, name_en=None, symbol=None, exchange_rate=1.0, is_base_currency=0, is_active=1):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            # إذا كانت العملة المحدثة هي الأساسية، تأكد من أن لا توجد عملة أساسية أخرى
            if is_base_currency == 1:
                if not self._ensure_single_base_currency(id):
                    return False

            # تم إضافة 'is_base_currency' هنا في جملة UPDATE
            cursor.execute("""
                UPDATE currencies
                SET code = ?, name_ar = ?, name_en = ?, symbol = ?, exchange_rate = ?, is_base_currency = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (code, name_ar, name_en, symbol, exchange_rate, is_base_currency, is_active, id))
            conn.commit()
            QMessageBox.information(None, "نجاح", "تم تحديث العملة بنجاح.")
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"رمز العملة '{code}' أو اسمها العربي '{name_ar}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث العملة: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_currency(self, currency_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM cash_chests WHERE currency_id = ?", (currency_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذه العملة لأنها مستخدمة في خزائن نقدية.")
                return False
            
            cursor.execute("SELECT COUNT(*) FROM bank_accounts WHERE currency_id = ?", (currency_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذه العملة لأنها مستخدمة في حسابات بنكية/نقدية.")
                return False

            query = "DELETE FROM currencies WHERE id = ?"
            cursor.execute(query, (currency_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذه العملة لأنها مرتبطة بسجلات أخرى في النظام.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند حذف العملة: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_base_currency(self):
        """يجلب العملة الأساسية."""
        # هذه الدالة تستخدم عمود 'is_base_currency'
        query = "SELECT * FROM currencies WHERE is_base_currency = 1"
        return self.fetch_one(query)

    def _ensure_single_base_currency(self, current_currency_id):
        """
        يضمن وجود عملة أساسية واحدة فقط.
        إذا تم تعيين عملة جديدة كعملة أساسية، يتم تغيير حالة العملة الأساسية السابقة إلى غير أساسية.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # جلب العملة الأساسية الحالية (إن وجدت) باستثناء العملة التي يتم تحديثها حالياً
            query = "SELECT id FROM currencies WHERE is_base_currency = 1"
            if current_currency_id is not None:
                query += f" AND id != {current_currency_id}"
            cursor.execute(query)
            existing_base_currency_id = cursor.fetchone()

            if existing_base_currency_id:
                # إذا وجدت عملة أساسية أخرى، قم بتعطيلها
                update_query = "UPDATE currencies SET is_base_currency = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                cursor.execute(update_query, (existing_base_currency_id[0],))
                conn.commit()
                QMessageBox.information(None, "تنبيه", "تم تغيير العملة الأساسية السابقة إلى عملة غير أساسية لتجنب تعدد العملات الأساسية.")
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ في قاعدة البيانات", f"خطأ في ضمان عملة أساسية واحدة: {e}")
            return False
        finally:
           if conn:
                conn.close()


   # ======================================================
    # دوال إدارة مراكز التكلفة (cost_centers)
    # ======================================================

    # تم التعديل هنا: إضافة is_active إلى دالة add_cost_center
    def add_cost_center(self, code, name_ar, name_en=None, description=None, parent_id=None, is_active=1): 
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cost_centers (code, name_ar, name_en, description, parent_cost_center_id, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (code, name_ar, name_en, description, parent_id, is_active)) # تم التعديل هنا: إضافة is_active
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"رمز مركز التكلفة '{code}' أو اسمه العربي '{name_ar}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة مركز التكلفة: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_cost_centers(self):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            # تم التعديل هنا: جلب parent_cost_center_id و is_active
            cursor.execute("SELECT id, code, name_ar, name_en, description, parent_cost_center_id, is_active FROM cost_centers ORDER BY name_ar")
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب مراكز التكلفة: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_cost_center_by_id(self, cost_center_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            # تم التعديل هنا: جلب parent_cost_center_id و is_active
            cursor.execute("SELECT id, code, name_ar, name_en, description, parent_cost_center_id, is_active FROM cost_centers WHERE id = ?", (cost_center_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting cost center by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_cost_center(self, id, data): 
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # استخراج البيانات من القاموس
            code = data.get('code')
            name_ar = data.get('name_ar')
            name_en = data.get('name_en')
            description = data.get('description')
            parent_cost_center_id = data.get('parent_cost_center_id')
            is_active = data.get('is_active', 1) 

            cursor.execute("""
                UPDATE cost_centers
                SET code = ?, name_ar = ?, name_en = ?, description = ?, parent_cost_center_id = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (code, name_ar, name_en, description, parent_cost_center_id, is_active, id)) 
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"رمز مركز التكلفة '{code}' أو اسمه العربي '{name_ar}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث مركز التكلفة: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def deactivate_cost_center(self, cost_center_id):
        """تعطيل مركز تكلفة بدلاً من حذفه فعلياً."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحقق مما إذا كان مركز التكلفة لديه أبناء نشطون
            cursor.execute("SELECT COUNT(*) FROM cost_centers WHERE parent_cost_center_id = ? AND is_active = 1", (cost_center_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في التعطيل", "لا يمكن تعطيل مركز التكلفة هذا لأنه يحتوي على مراكز تكلفة فرعية نشطة. يرجى تعطيل المراكز الفرعية أولاً.")
                return False

            # تحقق مما إذا كان مركز التكلفة مرتبطاً ببنود قيود يومية
            cursor.execute("SELECT COUNT(*) FROM journal_entry_lines WHERE cost_center_id = ?", (cost_center_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في التعطيل", "لا يمكن تعطيل مركز التكلفة هذا لأنه مرتبط ببنود قيود يومية.")
                return False

            cursor.execute("""
                UPDATE cost_centers
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (cost_center_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تعطيل مركز التكلفة: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_cost_center(self, cost_center_id):
        """
        حذف مركز تكلفة فعلياً (يجب أن يتم استدعاؤها بحذر وبعد التأكد من عدم وجود روابط).
        تم تعديلها لاستخدام دالة deactivate_cost_center بدلاً من الحذف الفعلي.
        """
        # بدلاً من الحذف الفعلي، سنقوم بتعطيل مركز التكلفة
        return self.deactivate_cost_center(cost_center_id)

    # ======================================================
    # دوال إدارة أنواع الضرائب (tax_types)
    # ======================================================

    # تم التعديل هنا: إضافة is_active إلى دالة add_tax_type
    def add_tax_type(self, code, name_ar, rate, name_en=None, tax_account_id=None, is_active=1): 
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tax_types (code, name_ar, name_en, rate, tax_account_id, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (code, name_ar, name_en, rate, tax_account_id, is_active)) # تم التعديل هنا: إضافة is_active
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"رمز الضريبة '{code}' أو اسمها العربي '{name_ar}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة نوع الضريبة: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_tax_types(self):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, name_ar, name_en, rate, tax_account_id, is_active FROM tax_types ORDER BY name_ar")
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب أنواع الضرائب: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_tax_type_by_id(self, tax_type_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, name_ar, name_en, rate, tax_account_id, is_active FROM tax_types WHERE id = ?", (tax_type_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting tax type by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_tax_type_by_code(self, code):
        """يجلب نوع الضريبة بواسطة الرمز (code)"""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, name_ar, name_en, rate, tax_account_id, is_active FROM tax_types WHERE code = ?", (code,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting tax type by code: {e}")
            return None
        finally:
            if conn:
                conn.close()

    # تم التعديل هنا: إضافة is_active إلى قاموس data لدالة update_tax_type
    def update_tax_type(self, id, data): 
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            code = data.get('code')
            name_ar = data.get('name_ar')
            name_en = data.get('name_en')
            rate = data.get('rate')
            tax_account_id = data.get('tax_account_id')
            is_active = data.get('is_active', 1) # تم التعديل هنا: جلب is_active من data

            cursor.execute("""
                UPDATE tax_types
                SET code = ?, name_ar = ?, name_en = ?, rate = ?, tax_account_id = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (code, name_ar, name_en, rate, tax_account_id, is_active, id)) # تم التعديل هنا: إضافة is_active
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"رمز الضريبة '{code}' أو اسمها العربي '{name_ar}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث نوع الضريبة: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def deactivate_tax_type(self, tax_type_id):
        """تعطيل نوع ضريبة بدلاً من حذفه فعلياً."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحقق مما إذا كان نوع الضريبة مرتبطاً ببنود قيود يومية
            cursor.execute("SELECT COUNT(*) FROM journal_entry_lines WHERE tax_type_id = ?", (tax_type_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في التعطيل", "لا يمكن تعطيل نوع الضريبة هذا لأنه مستخدم في بنود قيود يومية.")
                return False

            cursor.execute("""
                UPDATE tax_types
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (tax_type_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تعطيل نوع الضريبة: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_tax_type(self, tax_type_id):
        """
        حذف نوع ضريبة فعلياً (يجب أن يتم استدعاؤها بحذر وبعد التأكد من عدم وجود روابط).
        تم تعديلها لاستخدام دالة deactivate_tax_type بدلاً من الحذف الفعلي.
        """
        # بدلاً من الحذف الفعلي، سنقوم بتعطيل نوع الضريبة
        return self.deactivate_tax_type(tax_type_id)

# ======================================================
    # دوال إدارة الصناديق النقدية (cash_chests)
    # ======================================================

    def add_cash_chest(self, name_ar, chest_code, account_id, currency_id, is_active=1):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            # التحقق من أن account_id غير مستخدم بالفعل في أي صندوق أو حساب بنكي آخر
            cursor.execute("SELECT COUNT(*) FROM cash_chests WHERE account_id = ?", (account_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(None, "تكرار", "حساب دليل الحسابات هذا مرتبط بالفعل بصندوق نقدي آخر.")
                return False
            cursor.execute("SELECT COUNT(*) FROM bank_accounts WHERE account_id = ?", (account_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(None, "تكرار", "حساب دليل الحسابات هذا مرتبط بالفعل بحساب بنكي آخر.")
                return False

            cursor.execute("""
                INSERT INTO cash_chests (name_ar, chest_code, account_id, currency_id, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (name_ar, chest_code, account_id, currency_id, is_active))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"اسم الصندوق '{name_ar}' أو رمزه '{chest_code}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة صندوق نقدي: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_cash_chests(self):
        query = "SELECT id, name_ar, chest_code, account_id, currency_id, is_active FROM cash_chests ORDER BY name_ar"
        return self.fetch_all(query)

    def get_cash_chest_by_id(self, chest_id):
        query = "SELECT id, name_ar, chest_code, account_id, currency_id, is_active FROM cash_chests WHERE id = ?"
        return self.fetch_one(query, (chest_id,))

    def update_cash_chest(self, id, data):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            name_ar = data.get('name_ar')
            chest_code = data.get('chest_code')
            account_id = data.get('account_id')
            currency_id = data.get('currency_id')
            is_active = data.get('is_active', 1)

            # التحقق من أن account_id غير مستخدم بالفعل في أي صندوق أو حساب بنكي آخر (باستثناء الصندوق الحالي)
            cursor.execute("SELECT id FROM cash_chests WHERE account_id = ? AND id != ?", (account_id, id))
            if cursor.fetchone():
                QMessageBox.warning(None, "تكرار", "حساب دليل الحسابات هذا مرتبط بالفعل بصندوق نقدي آخر.")
                return False
            cursor.execute("SELECT id FROM bank_accounts WHERE account_id = ?", (account_id,))
            if cursor.fetchone():
                QMessageBox.warning(None, "تكرار", "حساب دليل الحسابات هذا مرتبط بالفعل بصندوق نقدي آخر.") # تم تصحيح الرسالة هنا
                return False

            cursor.execute("""
                UPDATE cash_chests
                SET name_ar = ?, chest_code = ?, account_id = ?, currency_id = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (name_ar, chest_code, account_id, currency_id, is_active, id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"اسم الصندوق '{name_ar}' أو رمزه '{chest_code}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ",f"خطأ عند تحديث صندوق نقدي: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def deactivate_cash_chest(self, chest_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            # تحقق من عدم وجود معاملات مرتبطة بهذا الصندوق
            cursor.execute("SELECT COUNT(*) FROM cash_bank_transactions WHERE cash_chest_id = ?", (chest_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في التعطيل", "لا يمكن تعطيل هذا الصندوق لأنه مرتبط بمعاملات نقدية.")
                return False

            cursor.execute("""
                UPDATE cash_chests
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (chest_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تعطيل صندوق نقدي: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def delete_cash_chest(self, chest_id):
        # نفضل التعطيل على الحذف الفعلي
        return self.deactivate_cash_chest(chest_id)

    # ======================================================
    # دوال إدارة الحسابات البنكية (bank_accounts)
    # ======================================================

    def add_bank_account(self, bank_name_ar, account_number, account_id, currency_id, is_active=1):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            # التحقق من أن account_id غير مستخدم بالفعل في أي صندوق أو حساب بنكي آخر
            cursor.execute("SELECT COUNT(*) FROM bank_accounts WHERE account_id = ?", (account_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(None, "تكرار", "حساب دليل الحسابات هذا مرتبط بالفعل بحساب بنكي آخر.")
                return False
            cursor.execute("SELECT COUNT(*) FROM cash_chests WHERE account_id =极", (account_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(None, "تكرار", "حساب دليل الحسابات هذا مرتبط بالفعل بصندوق نقدي آخر.")
                return False

            cursor.execute("""
                INSERT INTO bank_accounts (bank_name_ar, account_number, account_id, currency_id, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (bank_name_ar, account_number, account_id, currency_id, is_active))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"رقم الحساب '{account_number}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة حساب بنكي: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_bank_accounts(self):
        query = "SELECT id, bank_name_ar, account_number, account_id, currency_id, is_active FROM bank_accounts ORDER BY bank_name_ar"
        return self.fetch_all(query)

    def get_bank_account_by_id(self, bank_id):
        query = "SELECT id, bank_name_ar, account_number, account_id, currency_id, is_active FROM bank_accounts WHERE id = ?"
        return self.fetch_one(query, (bank_id,))

    def update_bank_account(self, id, data):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            bank_name_ar = data.get('bank_name_ar')
            account_number = data.get('account_number')
            account_id = data.get('account_id')
            currency_id = data.get('currency_id')
            is_active = data.get('is_active', 1)

            # التحقق من أن account_id غير مستخدم بالفعل في أي صندوق أو حساب بنكي آخر (باستثناء الحساب البنكي الحالي)
            cursor.execute("SELECT id FROM bank_accounts WHERE account_id = ? AND id != ?", (account_id, id))
            if cursor.fetchone():
                QMessageBox.warning(None, "تكرار", "حساب دليل الحسابات هذا مرتبط بالفعل بحساب بنكي آخر.")
                return False
            cursor.execute("SELECT id FROM cash_chests WHERE account_id = ?", (account_id,))
            if cursor.fetchone():
                QMessageBox.warning(None, "تكرار", "حساب دليل الحسابات هذا مرتبط بالفعل بصندوق نقدي آخر.")
                return False

            cursor.execute("""
                UPDATE bank_accounts
                SET bank_name_ar = ?, account_number = ?, account_id = ?, currency_id = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (bank_name_ar, account_number, account_id, currency_id, is_active, id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"رقم الحساب '{account_number}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث حساب بنكي: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def deactivate_bank_account(self, bank_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            # تحقق من عدم وجود معاملات مرتبطة بهذا الحساب البنكي
            cursor.execute("SELECT COUNT(*) FROM cash_bank_transactions WHERE bank_account_id = ?", (bank_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في التعطيل", "لا يمكن تعطيل هذا الحساب البنكي لأنه مرتبط بمعاملات بنكية.")
                return False

            cursor.execute("""
                UPDATE bank_accounts
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (bank_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تعطيل حساب بنكي: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_bank_account(self, bank_id):
        # نفضل التعطيل على الحذف الفعلي
        return self.deactivate_bank_account(bank_id)
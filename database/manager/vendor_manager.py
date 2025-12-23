# database/vendor_manager.py

import sqlite3
from ..base_manager import BaseManager  # تأكد من استيراد BaseManager
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox # استيراد QMessageBox

class VendorManager(BaseManager): # يجب أن يرث من BaseManager
    """
    مسؤول عن إدارة بيانات الموردين.
    يتصل بقاعدة بيانات financials.db
    """
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

    def add_vendor(self, name_ar, phone, address, linked_account_id,
                   name_en=None, email=None, tax_id=None, contact_person=None, credit_terms=None):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            code = self._generate_next_code('vendors', 'VNDR')
            if not code: return False

            cursor.execute("""
                INSERT INTO vendors (
                    code, name_ar, name_en, phone, email, address, tax_id,
                    contact_person, credit_terms, linked_account_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, name_ar, name_en, phone, email, address, tax_id,
                  contact_person, credit_terms, linked_account_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"المورد '{name_ar}' أو رمزه '{code}' أو رقمه الضريبي '{tax_id}' (إذا كان موجوداً) موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة المورد: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_vendors(self):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    v.id, v.code, v.name_ar, v.name_en, v.phone, v.email, v.address, v.tax_id,
                    v.contact_person, v.credit_terms, v.current_balance, v.is_active,
                    v.linked_account_id, acc.account_name_ar AS linked_account_name_ar # جلب اسم الحساب المرتبط
                FROM vendors v
                LEFT JOIN accounts acc ON v.linked_account_id = acc.id
                ORDER BY v.name_ar
            """)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب الموردين: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_vendor_by_id(self, vendor_id):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    v.id, v.code, v.name_ar, v.name_en, v.phone, v.email, v.address, v.tax_id,
                    v.contact_person, v.credit_terms, v.current_balance, v.is_active,
                    v.linked_account_id, acc.account_name_ar AS linked_account_name_ar
                FROM vendors v
                LEFT JOIN accounts acc ON v.linked_account_id = acc.id
                WHERE v.id = ?
            """, (vendor_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting vendor by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_vendor(self, vendor_id, name_ar, phone, address, linked_account_id,
                      name_en=None, email=None, tax_id=None, contact_person=None, credit_terms=None, is_active=1):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE vendors
                SET
                    name_ar = ?, name_en = ?, phone = ?, email = ?, address = ?, tax_id = ?,
                    contact_person = ?, credit_terms = ?, linked_account_id = ?, is_active = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (name_ar, name_en, phone, email, address, tax_id,
                  contact_person, credit_terms, linked_account_id, is_active, vendor_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"اسم المورد '{name_ar}' أو رقمه الضريبي '{tax_id}' (إذا كان موجوداً) موجود بالفعل لمورد آخر.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث المورد: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_vendor(self, vendor_id):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحقق من عدم وجود روابط (مثال: في فواتير الشراء أو سندات الصرف)
            cursor.execute("SELECT COUNT(*) FROM purchase_invoices WHERE vendor_id = ?", (vendor_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذا المورد لأنه مرتبط بفواتير شراء.")
                return False
            
            cursor.execute("SELECT COUNT(*) FROM payment_vouchers WHERE vendor_id = ?", (vendor_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذا المورد لأنه مرتبط بسندات صرف.")
                return False

            query = "DELETE FROM vendors WHERE id = ?"
            cursor.execute(query, (vendor_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذا المورد لأنه مرتبط بسجلات أخرى في النظام.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند حذف المورد: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def update_vendor_balance(self, vendor_id, amount, is_debit, transaction_type):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحديد كيفية تحديث الرصيد بناءً على نوع المعاملة
            # (مثال: المدين يقلل الرصيد، الدائن يزيد الرصيد للمورد)
            # يجب أن يتوافق هذا مع طبيعة حساب الموردين (التزامات)
            
            # افتراض: حساب الموردين هو حساب التزامات (دائن بطبيعته)
            # زيادة الرصيد عند الشراء الآجل
            # تقليل الرصيد عند السداد للمورد
            
            current_balance = self.get_vendor_by_id(vendor_id)['current_balance']
            
            if is_debit: # إذا كانت المعاملة ستخفض الرصيد الدائن للمورد (مثل سند صرف)
                new_balance = current_balance - amount
            else: # إذا كانت المعاملة ستزيد الرصيد الدائن للمورد (مثل فاتورة شراء)
                new_balance = current_balance + amount
            
            cursor.execute("""
                UPDATE vendors
                SET current_balance = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_balance, vendor_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث رصيد المورد: {e}")
            return False
        finally:
            if conn:
                conn.close()
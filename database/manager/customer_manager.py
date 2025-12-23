# database/customer_manager.py

import sqlite3
from ..base_manager import BaseManager  # تأكد من استيراد BaseManager
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox # استيراد QMessageBox

class CustomerManager(BaseManager): # يجب أن يرث من BaseManager
    """
    مسؤول عن إدارة بيانات العملاء.
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

    def add_customer(self, name_ar, phone, address, linked_account_id,
                     name_en=None, email=None, tax_id=None, contact_person=None, credit_limit=0.0):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            code = self._generate_next_code('customers', 'CUST')
            if not code: return False

            cursor.execute("""
                INSERT INTO customers (
                    code, name_ar, name_en, phone, email, address, tax_id,
                    contact_person, credit_limit, linked_account_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, name_ar, name_en, phone, email, address, tax_id,
                  contact_person, credit_limit, linked_account_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"العميل '{name_ar}' أو رمزه '{code}' أو رقمه الضريبي '{tax_id}' (إذا كان موجوداً) موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة العميل: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_customers(self):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    c.id, c.code, c.name_ar, c.name_en, c.phone, c.email, c.address, c.tax_id,
                    c.contact_person, c.credit_limit, c.current_balance, c.is_active,
                    c.linked_account_id, acc.account_name_ar AS linked_account_name_ar # جلب اسم الحساب المرتبط
                FROM customers c
                LEFT JOIN accounts acc ON c.linked_account_id = acc.id
                ORDER BY c.name_ar
            """)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب العملاء: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_customer_by_id(self, customer_id):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    c.id, c.code, c.name_ar, c.name_en, c.phone, c.email, c.address, c.tax_id,
                    c.contact_person, c.credit_limit, c.current_balance, c.is_active,
                    c.linked_account_id, acc.account_name_ar AS linked_account_name_ar
                FROM customers c
                LEFT JOIN accounts acc ON c.linked_account_id = acc.id
                WHERE c.id = ?
            """, (customer_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting customer by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_customer(self, customer_id, name_ar, phone, address, linked_account_id,
                        name_en=None, email=None, tax_id=None, contact_person=None, credit_limit=0.0, is_active=1):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE customers
                SET
                    name_ar = ?, name_en = ?, phone = ?, email = ?, address = ?, tax_id = ?,
                    contact_person = ?, credit_limit = ?, linked_account_id = ?, is_active = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (name_ar, name_en, phone, email, address, tax_id,
                  contact_person, credit_limit, linked_account_id, is_active, customer_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"اسم العميل '{name_ar}' أو رقمه الضريبي '{tax_id}' (إذا كان موجوداً) موجود بالفعل لعميل آخر.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث العميل: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_customer(self, customer_id):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحقق من عدم وجود روابط (مثال: في الفواتير أو سندات القبض)
            cursor.execute("SELECT COUNT(*) FROM invoices WHERE customer_id = ?", (customer_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذا العميل لأنه مرتبط بفواتير.")
                return False
            
            cursor.execute("SELECT COUNT(*) FROM receipt_vouchers WHERE customer_id = ?", (customer_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذا العميل لأنه مرتبط بسندات قبض.")
                return False

            query = "DELETE FROM customers WHERE id = ?"
            cursor.execute(query, (customer_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذا العميل لأنه مرتبط بسجلات أخرى في النظام.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند حذف العميل: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def update_customer_balance(self, customer_id, amount, is_debit, transaction_type):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحديد كيفية تحديث الرصيد بناءً على نوع المعاملة
            # (مثال: المدين يزيد الرصيد، الدائن يقلل الرصيد للعميل)
            # يجب أن يتوافق هذا مع طبيعة حساب العملاء (أصول أو التزامات)
            
            # افتراض: حساب العملاء هو حساب أصول (مدين بطبيعته)
            # زيادة الرصيد عند البيع الآجل أو الإيداع (قبض)
            # تقليل الرصيد عند السداد من العميل
            
            # هذه الدالة تتطلب فهمًا أعمق لكيفية عمل الحسابات المدينة والدائنة
            # هنا مثال مبسط:
            current_balance = self.get_customer_by_id(customer_id)['current_balance']
            
            if is_debit: # إذا كانت المعاملة ستزيد الرصيد المدين للعميل (مثل فاتورة بيع)
                new_balance = current_balance + amount
            else: # إذا كانت المعاملة ستخفض الرصيد المدين للعميل (مثل سند قبض)
                new_balance = current_balance - amount
            
            cursor.execute("""
                UPDATE customers
                SET current_balance = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_balance, customer_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث رصيد العميل: {e}")
            return False
        finally:
            if conn:
                conn.close()
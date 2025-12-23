# database/cash_bank_manager.py

import sqlite3
from ..base_manager import BaseManager  # تأكد من استيراد BaseManager
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox # استيراد QMessageBox

class CashBankManager(BaseManager): # يجب أن يرث من BaseManager
    """
    مسؤول عن إدارة حسابات البنوك والصناديق (النقدية).
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

    # ======================================================
    # دوال إدارة حسابات البنوك (banks)
    # ======================================================

    def add_bank_account(self, bank_name_ar, account_number, linked_account_id,
                         bank_name_en=None, iban=None, swift_code=None, currency_id=None):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # توليد الكود إذا كان جدول البنوك يستخدم كود
            code = self._generate_next_code('bank_accounts', 'BNK')
            if not code: return False

            cursor.execute("""
                INSERT INTO bank_accounts (
                    code, bank_name_ar, bank_name_en, account_number, iban,
                    swift_code, currency_id, linked_account_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, bank_name_ar, bank_name_en, account_number, iban,
                  swift_code, currency_id, linked_account_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"رقم الحساب '{account_number}' أو IBAN '{iban}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة حساب بنكي: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_bank_accounts(self):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    ba.id, ba.code, ba.bank_name_ar, ba.bank_name_en, ba.account_number,
                    ba.iban, ba.swift_code, ba.currency_id, cur.name_ar AS currency_name_ar, # جلب اسم العملة
                    ba.linked_account_id, acc.account_name_ar AS linked_account_name_ar, # جلب اسم الحساب المرتبط
                    ba.is_active
                FROM bank_accounts ba
                LEFT JOIN currencies cur ON ba.currency_id = cur.id
                LEFT JOIN accounts acc ON ba.linked_account_id = acc.id
                ORDER BY ba.bank_name_ar
            """)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب الحسابات البنكية: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_bank_account_by_id(self, bank_account_id):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    ba.id, ba.code, ba.bank_name_ar, ba.bank_name_en, ba.account_number,
                    ba.iban, ba.swift_code, ba.currency_id, cur.name_ar AS currency_name_ar,
                    ba.linked_account_id, acc.account_name_ar AS linked_account_name_ar,
                    ba.is_active
                FROM bank_accounts ba
                LEFT JOIN currencies cur ON ba.currency_id = cur.id
                LEFT JOIN accounts acc ON ba.linked_account_id = acc.id
                WHERE ba.id = ?
            """, (bank_account_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting bank account by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_bank_account(self, bank_account_id, bank_name_ar, account_number, linked_account_id,
                            bank_name_en=None, iban=None, swift_code=None, currency_id=None, is_active=1):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE bank_accounts
                SET
                    bank_name_ar = ?, bank_name_en = ?, account_number = ?, iban = ?,
                    swift_code = ?, currency_id = ?, linked_account_id = ?, is_active = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (bank_name_ar, bank_name_en, account_number, iban,
                  swift_code, currency_id, linked_account_id, is_active, bank_account_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"رقم الحساب '{account_number}' أو IBAN '{iban}' موجود بالفعل لحساب بنكي آخر.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث حساب بنكي: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_bank_account(self, bank_account_id):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحقق من عدم وجود روابط (مثال: في سجلات الإيصالات/المدفوعات)
            # هذه التحققات يجب أن تتم بحذر لضمان عدم حذف بيانات مرتبطة
            cursor.execute("SELECT COUNT(*) FROM payment_vouchers WHERE cash_bank_account_id = ?", (bank_account_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذا الحساب البنكي لأنه مستخدم في سندات الصرف.")
                return False
            
            cursor.execute("SELECT COUNT(*) FROM receipt_vouchers WHERE cash_bank_account_id = ?", (bank_account_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذا الحساب البنكي لأنه مستخدم في سندات القبض.")
                return False

            query = "DELETE FROM bank_accounts WHERE id = ?"
            cursor.execute(query, (bank_account_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذا الحساب البنكي لأنه مرتبط بسجلات أخرى في النظام.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند حذف حساب بنكي: {e}")
            return False
        finally:
            if conn:
                conn.close()

    # ======================================================
    # دوال إدارة حسابات الصناديق (cashes)
    # ======================================================

    def add_cash_account(self, cash_name_ar, linked_account_id, cash_name_en=None, currency_id=None):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            code = self._generate_next_code('cash_accounts', 'CSH')
            if not code: return False

            cursor.execute("""
                INSERT INTO cash_accounts (
                    code, cash_name_ar, cash_name_en, currency_id, linked_account_id
                )
                VALUES (?, ?, ?, ?, ?)
            """, (code, cash_name_ar, cash_name_en, currency_id, linked_account_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"اسم الصندوق '{cash_name_ar}' أو رمزه '{code}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة حساب صندوق: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_cash_accounts(self):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    ca.id, ca.code, ca.cash_name_ar, ca.cash_name_en, ca.currency_id, cur.name_ar AS currency_name_ar,
                    ca.linked_account_id, acc.account_name_ar AS linked_account_name_ar,
                    ca.is_active
                FROM cash_accounts ca
                LEFT JOIN currencies cur ON ca.currency_id = cur.id
                LEFT JOIN accounts acc ON ca.linked_account_id = acc.id
                ORDER BY ca.cash_name_ar
            """)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب حسابات الصناديق: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_cash_account_by_id(self, cash_account_id):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    ca.id, ca.code, ca.cash_name_ar, ca.cash_name_en, ca.currency_id, cur.name_ar AS currency_name_ar,
                    ca.linked_account_id, acc.account_name_ar AS linked_account_name_ar,
                    ca.is_active
                FROM cash_accounts ca
                LEFT JOIN currencies cur ON ca.currency_id = cur.id
                LEFT JOIN accounts acc ON ca.linked_account_id = acc.id
                WHERE ca.id = ?
            """, (cash_account_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting cash account by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_cash_account(self, cash_account_id, cash_name_ar, linked_account_id,
                            cash_name_en=None, currency_id=None, is_active=1):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE cash_accounts
                SET
                    cash_name_ar = ?, cash_name_en = ?, currency_id = ?,
                    linked_account_id = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (cash_name_ar, cash_name_en, currency_id,
                  linked_account_id, is_active, cash_account_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"اسم الصندوق '{cash_name_ar}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث حساب صندوق: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_cash_account(self, cash_account_id):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحقق من عدم وجود روابط (مثال: في سجلات الإيصالات/المدفوعات)
            cursor.execute("SELECT COUNT(*) FROM payment_vouchers WHERE cash_bank_account_id = ?", (cash_account_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف حساب الصندوق هذا لأنه مستخدم في سندات الصرف.")
                return False
            
            cursor.execute("SELECT COUNT(*) FROM receipt_vouchers WHERE cash_bank_account_id = ?", (cash_account_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف حساب الصندوق هذا لأنه مستخدم في سندات القبض.")
                return False

            query = "DELETE FROM cash_accounts WHERE id = ?"
            cursor.execute(query, (cash_account_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف حساب الصندوق هذا لأنه مرتبط بسجلات أخرى في النظام.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند حذف حساب صندوق: {e}")
            return False
        finally:
            if conn:
                conn.close()
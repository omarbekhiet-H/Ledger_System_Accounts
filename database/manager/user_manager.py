# database/manager/financial/user_manager.py

import sqlite3
import hashlib # لاستخدام التشفير لكلمات المرور
from ..base_manager import BaseManager  # تأكد من استيراد BaseManager
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox # استيراد QMessageBox

class UserManager(BaseManager): # يجب أن يرث من BaseManager
    """
    مسؤول عن إدارة بيانات المستخدمين.
    يتصل بقاعدة بيانات financials.db (أو users.db إذا كان منفصلاً)
    """
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func) # استدعاء __init__ الخاص بـ BaseManager

    def hash_password(self, password):
        """يقوم بتشفير كلمة المرور باستخدام SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def add_user(self, username, password, email=None, is_active=1):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            hashed_password = self.hash_password(password)

            cursor.execute("""
                INSERT INTO users (username, password_hash, email, is_active)
                VALUES (?, ?, ?, ?)
            """, (username, hashed_password, email, is_active))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"اسم المستخدم '{username}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة المستخدم: {e}")
            return False
        finally:
            if conn:
                conn.close()
    # في user_manager.py، ضيف الدالة دي جوة class UserManager

    def get_user_by_id(self, user_id):
        """
        يجلب بيانات مستخدم بواسطة ID.
        يرجع قاموس فيه (id, username, email, is_active, created_at) أو None إذا لم يوجد.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None:
                return None
            cursor = conn.cursor()
            # استخدمنا نفس الاستعلام الموجود في get_all_users لكن مع فلتر بالـ ID
            cursor.execute("SELECT id, username, email, is_active, created_at FROM users WHERE id = ?", (user_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting user by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def authenticate_user(self, username, password):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()

            hashed_password = self.hash_password(password)

            cursor.execute("""
                SELECT id, username, is_active FROM users
                WHERE username = ? AND password_hash = ?
            """, (username, hashed_password))
            user = cursor.fetchone()
            if user and user['is_active']:
                return dict(user) # إرجاع قاموس بمعلومات المستخدم
            return None # لا يوجد مستخدم أو كلمة مرور خاطئة أو غير نشط
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ في عملية المصادقة: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_all_users(self):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email, is_active, created_at FROM users ORDER BY username")
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب المستخدمين: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_user_by_id(self, user_id):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email, is_active, created_at FROM users WHERE id = ?", (user_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting user by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_user(self, user_id, username, email=None, is_active=1, new_password=None):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            params = [username, email, is_active, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
            query = """
                UPDATE users
                SET username = ?, email = ?, is_active = ?, updated_at = ?
            """
            if new_password:
                hashed_password = self.hash_password(new_password)
                query += ", password_hash = ?"
                params.append(hashed_password)
            
            query += " WHERE id = ?"
            params.append(user_id)

            cursor.execute(query, tuple(params))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"اسم المستخدم '{username}' موجود بالفعل لمستخدم آخر.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث المستخدم: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_user(self, user_id):
        conn = None
        try:
            conn = self.get_connection() # استخدام self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحقق من عدم وجود روابط (مثال: إذا كان المستخدم هو مُعد المستندات أو له قيود يومية)
            # هذه الخطوات تعتمد على تصميم قاعدة البيانات، قد تحتاج إلى إضافة المزيد من التحققات
            cursor.execute("SELECT COUNT(*) FROM journal_entries WHERE created_by_user_id = ?", (user_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذا المستخدم لأنه أنشأ قيود يومية.")
                return False
            
            # منع حذف المستخدم إذا كان لديه صلاحيات مرتبطة (يجب أن يتم حذفها أولاً أو إعادة تعيينها)
            cursor.execute("SELECT COUNT(*) FROM user_permissions WHERE user_id = ?", (user_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذا المستخدم لأنه لديه صلاحيات مرتبطة. قم بحذف الصلاحيات أولاً.")
                return False

            query = "DELETE FROM users WHERE id = ?"
            cursor.execute(query, (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذا المستخدم لأنه مرتبط بسجلات أخرى في النظام.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند حذف المستخدم: {e}")
            return False
        finally:
            if conn:
                conn.close()
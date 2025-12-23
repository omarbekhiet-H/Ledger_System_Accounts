# database/permission_manager.py

import sqlite3
from ...base_manager import BaseManager  # تأكد من استيراد BaseManager
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox # استيراد QMessageBox

class PermissionManager(BaseManager): # يجب أن يرث من BaseManager
    """
    مسؤول عن إدارة الصلاحيات والأدوار (Roles) وتعيينها للمستخدمين.
    يتصل بقاعدة بيانات financials.db (أو users.db إذا كان منفصلاً)
    """
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func) # استدعاء __init__ الخاص بـ BaseManager

    # ======================================================
    # دوال إدارة الأدوار (Roles)
    # ======================================================

    def add_role(self, role_name_ar, role_name_en=None, description=None):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO roles (name_ar, name_en, description)
                VALUES (?, ?, ?)
            """, (role_name_ar, role_name_en, description))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"الدور '{role_name_ar}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة الدور: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_roles(self):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("SELECT id, name_ar, name_en, description FROM roles ORDER BY name_ar")
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب الأدوار: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_role_by_id(self, role_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("SELECT id, name_ar, name_en, description FROM roles WHERE id = ?", (role_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting role by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_role(self, role_id, role_name_ar, role_name_en=None, description=None):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE roles
                SET name_ar = ?, name_en = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (role_name_ar, role_name_en, description, role_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"الدور '{role_name_ar}' موجود بالفعل لدور آخر.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث الدور: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_role(self, role_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحقق من عدم وجود مستخدمين مرتبطين بهذا الدور
            cursor.execute("SELECT COUNT(*) FROM user_roles WHERE role_id = ?", (role_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذا الدور لأنه مرتبط بمستخدمين. قم بإلغاء ربط المستخدمين أولاً.")
                return False
            
            # تحقق من عدم وجود صلاحيات مرتبطة بهذا الدور
            cursor.execute("SELECT COUNT(*) FROM role_permissions WHERE role_id = ?", (role_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذا الدور لأنه لديه صلاحيات مرتبطة. قم بحذف الصلاحيات المرتبطة أولاً.")
                return False

            query = "DELETE FROM roles WHERE id = ?"
            cursor.execute(query, (role_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذا الدور لأنه مرتبط بسجلات أخرى في النظام.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند حذف الدور: {e}")
            return False
        finally:
            if conn:
                conn.close()

    # ======================================================
    # دوال إدارة الصلاحيات (Permissions)
    # ======================================================

    def add_permission(self, permission_name_ar, permission_key, permission_name_en=None, description=None):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO permissions (name_ar, name_en, permission_key, description)
                VALUES (?, ?, ?, ?)
            """, (permission_name_ar, permission_name_en, permission_key, description))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"المفتاح '{permission_key}' أو اسم الصلاحية '{permission_name_ar}' موجود بالفعل.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إضافة الصلاحية: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_permissions(self):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("SELECT id, name_ar, name_en, permission_key, description FROM permissions ORDER BY name_ar")
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب الصلاحيات: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_permission_by_id(self, permission_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("SELECT id, name_ar, name_en, permission_key, description FROM permissions WHERE id = ?", (permission_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting permission by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_permission(self, permission_id, permission_name_ar, permission_key, permission_name_en=None, description=None):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE permissions
                SET name_ar = ?, name_en = ?, permission_key = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (permission_name_ar, permission_name_en, permission_key, description, permission_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", f"المفتاح '{permission_key}' أو اسم الصلاحية '{permission_name_ar}' موجود بالفعل لصلاحية أخرى.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تحديث الصلاحية: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_permission(self, permission_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # تحقق من عدم وجود روابط (إذا كانت الصلاحية مرتبطة بأدوار)
            cursor.execute("SELECT COUNT(*) FROM role_permissions WHERE permission_id = ?", (permission_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذه الصلاحية لأنها مرتبطة بأدوار. قم بإلغاء ربطها أولاً.")
                return False

            query = "DELETE FROM permissions WHERE id = ?"
            cursor.execute(query, (permission_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(None, "خطأ في الحذف", "لا يمكن حذف هذه الصلاحية لأنها مرتبطة بسجلات أخرى في النظام.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند حذف الصلاحية: {e}")
            return False
        finally:
            if conn:
                conn.close()

    # ======================================================
    # دوال تعيين الصلاحيات للأدوار (Role-Permission Assignment)
    # ======================================================

    def assign_permission_to_role(self, role_id, permission_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO role_permissions (role_id, permission_id)
                VALUES (?, ?)
            """, (role_id, permission_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", "هذه الصلاحية معينة بالفعل لهذا الدور.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تعيين الصلاحية للدور: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def remove_permission_from_role(self, role_id, permission_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM role_permissions
                WHERE role_id = ? AND permission_id = ?
            """, (role_id, permission_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إزالة الصلاحية من الدور: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_permissions_for_role(self, role_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.name_ar, p.name_en, p.permission_key, p.description
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                WHERE rp.role_id = ?
                ORDER BY p.name_ar
            """, (role_id,))
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب صلاحيات الدور: {e}")
            return []
        finally:
            if conn:
                conn.close()

    # ======================================================
    # دوال تعيين الأدوار للمستخدمين (User-Role Assignment)
    # ======================================================

    def assign_role_to_user(self, user_id, role_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES (?, ?)
            """, (user_id, role_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "تكرار", "هذا الدور معين بالفعل لهذا المستخدم.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند تعيين الدور للمستخدم: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def remove_role_from_user(self, user_id, role_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM user_roles
                WHERE user_id = ? AND role_id = ?
            """, (user_id, role_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند إزالة الدور من المستخدم: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_roles_for_user(self, user_id):
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.id, r.name_ar, r.name_en, r.description
                FROM roles r
                JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = ?
                ORDER BY r.name_ar
            """, (user_id,))
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب أدوار المستخدم: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_all_permissions_for_user(self, user_id):
        """
        يجلب جميع الصلاحيات المباشرة وغير المباشرة (عبر الأدوار) لمستخدم معين.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT p.id, p.name_ar, p.name_en, p.permission_key, p.description
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN user_roles ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = ?
                ORDER BY p.permission_key
            """, (user_id,))
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ عند جلب جميع صلاحيات المستخدم: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def user_has_permission(self, user_id, permission_key):
        """
        يتحقق مما إذا كان المستخدم لديه صلاحية معينة (عبر أدواره).
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*)
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN user_roles ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = ? AND p.permission_key = ? COLLATE NOCASE
            """, (user_id, permission_key))
            count = cursor.fetchone()[0]
            return count > 0
        except sqlite3.Error as e:
            print(f"Error checking user permission: {e}")
            return False
        finally:
            if conn:
                conn.close()
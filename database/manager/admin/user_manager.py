# database/manager/user_manager.py

import sqlite3
import hashlib
import os
import sys

# =====================================================================
# تصحيح مسار المشروع الجذر لضمان عمل الاستيرادات بشكل صحيح
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.base_manager import BaseManager

class UserManager(BaseManager):
    """
    مسؤول عن إدارة المستخدمين، الأدوار، والصلاحيات.
    يتعامل مع جداول: users, roles, role_permissions.
    """
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func)
        print(f"DEBUG: UserManager initialized from {__file__}.")

    def _hash_password(self, password):
        """
        يقوم بتشفير (هاش) كلمة المرور باستخدام خوارزمية SHA-256 الآمنة.
        """
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def verify_user(self, username, password):
        """
        يتحقق من صحة اسم المستخدم وكلمة المرور.
        - يعيد قاموس ببيانات المستخدم إذا كان الدخول صحيحًا والحساب فعالاً.
        - يعيد None إذا كان اسم المستخدم أو كلمة المرور خاطئة، أو إذا كان الحساب معطلاً.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user_data = cursor.fetchone()

            if user_data:
                # قارن الهاش المخزن مع هاش كلمة المرور المدخلة
                if user_data['password_hash'] == self._hash_password(password):
                    if user_data['is_active'] == 1:
                        return dict(user_data) # نجح الدخول
                    else:
                        print(f"Login failed for {username}: Account is disabled.")
                        return None # الحساب معطل
            
            print(f"Login failed for {username}: Invalid username or password.")
            return None # اسم المستخدم أو كلمة المرور خاطئة

        except sqlite3.Error as e:
            print(f"DATABASE ERROR in verify_user: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_user_permissions(self, user_id):
        """
        يجلب كل صلاحيات المستخدم المحدد كقاموس لسهولة الاستخدام.
        مثال للنتيجة: {'reports.view.trial_balance': True, 'journal.delete': False}
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return {}
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # أولاً، نحصل على role_id الخاص بالمستخدم
            cursor.execute("SELECT role_id FROM users WHERE id = ?", (user_id,))
            user_role = cursor.fetchone()
            
            if not user_role:
                return {} # لا يوجد مستخدم بهذا الـ ID

            role_id = user_role['role_id']

            # ثانيًا، نجلب كل الصلاحيات المرتبطة بهذا الـ role_id
            cursor.execute("SELECT permission_key, is_allowed FROM role_permissions WHERE role_id = ?", (role_id,))
            permissions_list = cursor.fetchall()
            
            # تحويل قائمة الصلاحيات إلى قاموس لسهولة الوصول
            # (e.g., permissions_dict['journal.add'])
            permissions_dict = {p['permission_key']: bool(p['is_allowed']) for p in permissions_list}
            return permissions_dict

        except sqlite3.Error as e:
            print(f"DATABASE ERROR in get_user_permissions: {e}")
            return {}
        finally:
            if conn:
                conn.close()

    def get_all_users_with_roles(self):
        """يجلب كل المستخدمين مع اسم الدور الخاص بهم."""
        conn = None
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.full_name, u.is_active, r.role_name_ar
                FROM users u
                JOIN roles r ON u.role_id = r.id
                ORDER BY u.id
            """)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"DATABASE ERROR in get_all_users_with_roles: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_all_roles(self):
        """يجلب كل الأدوار المتاحة."""
        conn = None
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, role_name_ar FROM roles ORDER BY id")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"DATABASE ERROR in get_all_roles: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_user_by_id(self, user_id):
        """يجلب بيانات مستخدم واحد بواسطة الـ ID."""
        conn = None
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            return dict(cursor.fetchone())
        except (sqlite3.Error, TypeError):
            return None
        finally:
            if conn:
                conn.close()

    def add_user(self, username, password, full_name, role_id, is_active):
        """يضيف مستخدمًا جديدًا إلى قاعدة البيانات."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            password_hash = self._hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role_id, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (username, password_hash, full_name, role_id, 1 if is_active else 0))
            conn.commit()
            return True
        except sqlite3.IntegrityError: # يحدث إذا كان اسم المستخدم مكررًا
            return False
        finally:
            if conn:
                conn.close()

    def update_user(self, user_id, full_name, password, role_id, is_active):
        """يحدث بيانات مستخدم موجود."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            if password: # إذا تم توفير كلمة مرور جديدة، قم بتحديثها
                password_hash = self._hash_password(password)
                cursor.execute("""
                    UPDATE users SET full_name = ?, password_hash = ?, role_id = ?, is_active = ?
                    WHERE id = ?
                """, (full_name, password_hash, role_id, 1 if is_active else 0, user_id))
            else: # إذا لم يتم توفير كلمة مرور، لا تقم بتحديثها
                cursor.execute("""
                    UPDATE users SET full_name = ?, role_id = ?, is_active = ?
                    WHERE id = ?
                """, (full_name, role_id, 1 if is_active else 0, user_id))
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            if conn:
                conn.close()

    def delete_user(self, user_id):
        """يحذف مستخدمًا من قاعدة البيانات."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            if conn:
                conn.close()


    def get_all_permissions_matrix(self):
        """
        يجلب كل الصلاحيات وينظمها في قاموس متداخل (مصفوفة).
        'permission_key' -> {role_id: is_allowed, ...}
        """
        conn = None
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT role_id, permission_key, is_allowed FROM role_permissions")
            
            matrix = {}
            for row in cursor.fetchall():
                p_key = row['permission_key']
                if p_key not in matrix:
                    matrix[p_key] = {}
                matrix[p_key][row['role_id']] = bool(row['is_allowed'])
            return matrix
        except sqlite3.Error as e:
            print(f"DATABASE ERROR in get_all_permissions_matrix: {e}")
            return {}
        finally:
            if conn:
                conn.close()

                

    def update_role_permissions(self, permissions_list):
        """
        يحدث كل صلاحيات الأدوار دفعة واحدة.
        permissions_list هو قائمة من Tuples: [(role_id, p_key, is_allowed), ...]
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # حذف كل الصلاحيات القديمة لإعادة كتابتها من جديد
            cursor.execute("DELETE FROM role_permissions")
            # إدراج كل الصلاحيات الجديدة
            cursor.executemany("""
                INSERT INTO role_permissions (role_id, permission_key, is_allowed)
                VALUES (?, ?, ?)
            """, permissions_list)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"DATABASE ERROR in update_role_permissions: {e}")
            conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    def get_all_permissions_matrix(self):
        """
        يجلب كل الصلاحيات وينظمها في قاموس متداخل (مصفوفة).
        'permission_key' -> {role_id: is_allowed, ...}
        """
        conn = None
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # --- استعلام لجلب كل الصلاحيات المسجلة ---
            cursor.execute("SELECT role_id, permission_key, is_allowed FROM role_permissions")
            
            matrix = {}
            all_permissions_keys = self.get_all_possible_permission_keys() # جلب كل المفاتيح الممكنة
            
            # تهيئة المصفوفة بكل المفاتيح لضمان ظهورها حتى لو لم تكن مسجلة
            for p_key in all_permissions_keys:
                matrix[p_key] = {}

            # ملء المصفوفة بالبيانات الموجودة في قاعدة البيانات
            for row in cursor.fetchall():
                p_key = row['permission_key']
                if p_key in matrix: # التأكد من أن الصلاحية لا تزال موجودة
                    matrix[p_key][row['role_id']] = bool(row['is_allowed'])
            
            return matrix
        except sqlite3.Error as e:
            print(f"DATABASE ERROR in get_all_permissions_matrix: {e}")
            return {}
        finally:
            if conn:
                conn.close()

    def update_role_permissions(self, permissions_list):
        """
        يحدث كل صلاحيات الأدوار دفعة واحدة.
        permissions_list هو قائمة من Tuples: [(role_id, p_key, is_allowed), ...]
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # حذف كل الصلاحيات القديمة لإعادة كتابتها من جديد
            cursor.execute("DELETE FROM role_permissions")
            # إدراج كل الصلاحيات الجديدة
            cursor.executemany("""
                INSERT INTO role_permissions (role_id, permission_key, is_allowed)
                VALUES (?, ?, ?)
            """, permissions_list)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"DATABASE ERROR in update_role_permissions: {e}")
            conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def get_all_possible_permission_keys(self):
        """
        دالة مركزية لجلب كل مفاتيح الصلاحيات الممكنة في النظام.
        هذا يضمن أن القائمة موحدة في كل مكان.
        """
        return [
            'reports.view.trial_balance',
            'reports.view.general_ledger',
            'reports.view.subsidiary_ledger',
            'journal.add',
            'journal.edit',
            'journal.delete',
            'journal.post',
            'users.manage',
            'permissions.manage'
        ]

            
            
    

    def get_all_users(self):
        try:
            conn = self.conn_func()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")  # مبدئيًا نجيب كل حاجة
            rows = cursor.fetchall()
            print("[DEBUG] users fetched:", rows)  # نطبعهم في الكونسول
            # حاول نخمن أسماء الأعمدة
            return [{"id": row[0], "full_name": row[1], "username": row[2]} for row in rows]
        except Exception as e:
            print(f"[UserManager] خطأ في get_all_users: {e}")
            return []

    def verify_user_by_id(self, user_id, password):
        """
        التحقق من المستخدم بالـ ID وكلمة المرور
        """
        try:
            conn = self.conn_func()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, full_name, username FROM users WHERE id=%s AND password=%s",
                (user_id, password)
            )
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "full_name": row[1], "username": row[2]}
            return None
        except Exception as e:
            print(f"[UserManager] خطأ في verify_user_by_id: {e}")
            return None


import sqlite3
from typing import List, Dict, Tuple, Set
from database.db_connection import get_users_db_connection, get_db_connection

class NEWRoleManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def get_connection(self):
        """الحصول على اتصال بقاعدة البيانات"""
        if self.db_path:
            return get_db_connection(self.db_path)
        else:
            return get_users_db_connection()

    # ------------------------- CRUD للأدوار -------------------------

    def create_role(self, role_code: str, name_ar: str, name_en: str = None, description: str = None, is_active: bool = True) -> Tuple[bool, str]:
        """إنشاء دور جديد"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM roles WHERE role_code = ?", (role_code,))
            if cursor.fetchone():
                return False, "كود الدور موجود بالفعل"

            cursor.execute("""
                INSERT INTO roles (role_code, name_ar, name_en, description, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (role_code, name_ar, name_en, description, is_active))

            conn.commit()
            return True, "تم إنشاء الدور بنجاح"
        except sqlite3.Error as e:
            return False, f"خطأ أثناء إنشاء الدور: {str(e)}"
        finally:
            if conn:
                conn.close()

                
    def update_role(self, role_id: int, role_code: str, name_ar: str, name_en: str = None, description: str = None, is_active: bool = True) -> Tuple[bool, str]:
        """تحديث بيانات الدور"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM roles WHERE role_code = ? AND id != ?", (role_code, role_id))
            if cursor.fetchone():
                return False, "كود الدور مستخدم من قبل دور آخر"

            cursor.execute("""
                UPDATE roles
                SET role_code = ?, name_ar = ?, name_en = ?, description = ?, is_active = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (role_code, name_ar, name_en, description, is_active, role_id))

            conn.commit()
            return True, "تم تحديث الدور بنجاح"
        except sqlite3.Error as e:
            return False, f"خطأ أثناء تحديث الدور: {str(e)}"
        finally:
            if conn:
                conn.close()

    def delete_role(self, role_id: int) -> Tuple[bool, str]:
        """حذف دور"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM roles WHERE id = ?", (role_id,))
            conn.commit()
            return True, "تم حذف الدور بنجاح"
        except sqlite3.Error as e:
            return False, f"خطأ أثناء حذف الدور: {str(e)}"
        finally:
            if conn:
                conn.close()

    def get_all_roles(self) -> List[Dict]:
        """جلب جميع الأدوار"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id, role_name, description FROM roles ORDER BY role_name")
            roles = []
            for row in cursor.fetchall():
                roles.append({
                    'id': row[0],
                    'role_name': row[1],
                    'description': row[2]
                })
            return roles
        except sqlite3.Error as e:
            print(f"Error getting roles: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_role_by_id(self, role_id: int) -> Dict:
        """جلب بيانات دور باستخدام ID"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id, role_name, description FROM roles WHERE id = ?", (role_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'role_name': row[1],
                    'description': row[2]
                }
            return None
        except sqlite3.Error as e:
            print(f"Error getting role: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def toggle_role_status(self, role_id: int) -> Tuple[bool, str]:
        """تبديل حالة الدور (نشط/غير نشط)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
        
            cursor.execute("SELECT is_active FROM roles WHERE id = ?", (role_id,))
            row = cursor.fetchone()
            if not row:
                return False, "الدور غير موجود"

            new_status = 0 if row[0] else 1
        
            cursor.execute(
                "UPDATE roles SET is_active = ?, updated_at = datetime('now') WHERE id = ?", 
                (new_status, role_id)
            )
            conn.commit()
        
            status_text = "نشط" if new_status else "غير نشط"
            return True, f"تم تغيير حالة الدور إلى: {status_text}"
        
        except sqlite3.Error as e:
            return False, f"خطأ في تحديث الحالة: {str(e)}"
        finally:
            if conn:
                conn.close()            

    # ------------------------- ربط الأدوار بالصلاحيات -------------------------

    def set_role_permissions(self, role_id: int, permission_ids: List[int]) -> Tuple[bool, str]:
        """تعيين صلاحيات للدور (استبدال الكل)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))

            for perm_id in permission_ids:
                cursor.execute("""
                    INSERT INTO role_permissions (role_id, permission_id, granted_at)
                    VALUES (?, ?, datetime('now'))
                """, (role_id, perm_id))

            conn.commit()
            return True, "تم تحديث صلاحيات الدور بنجاح"
        except sqlite3.Error as e:
            return False, f"خطأ أثناء تحديث الصلاحيات: {str(e)}"
        finally:
            if conn:
                conn.close()

    def get_role_permissions(self, role_id: int) -> Set[str]:
        """جلب صلاحيات الدور"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT p.permission_code
                FROM role_permissions rp
                JOIN permissions p ON rp.permission_id = p.id
                WHERE rp.role_id = ?
            """, (role_id,))
            return {row[0] for row in cursor.fetchall()}
        except sqlite3.Error as e:
            print(f"Error getting role permissions: {e}")
            return set()
        finally:
            if conn:
                conn.close()

    # ------------------------- ربط المستخدمين بالأدوار -------------------------

    def assign_role_to_user(self, user_id: int, role_id: int) -> Tuple[bool, str]:
        """إسناد دور لمستخدم"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM user_roles WHERE user_id = ? AND role_id = ?", (user_id, role_id))
            if cursor.fetchone():
                return False, "المستخدم لديه هذا الدور بالفعل"

            cursor.execute("""
                INSERT INTO user_roles (user_id, role_id, assigned_at)
                VALUES (?, ?, datetime('now'))
            """, (user_id, role_id))

            conn.commit()
            return True, "تم إسناد الدور للمستخدم بنجاح"
        except sqlite3.Error as e:
            return False, f"خطأ أثناء إسناد الدور: {str(e)}"
        finally:
            if conn:
                conn.close()

    def get_user_roles(self, user_id: int) -> List[Dict]:
        """جلب أدوار مستخدم معين"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT r.id, r.role_name, r.description
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = ?
            """, (user_id,))
            return [{'id': row[0], 'role_name': row[1], 'description': row[2]} for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error getting user roles: {e}")
            return []
        finally:
            if conn:
                conn.close()

# استبدال الملف الكامل بـ هذا الإصدار المصحح

import sqlite3
from typing import List, Dict, Set, Tuple, Optional
from database.db_connection import get_users_db_connection


class NEWPermissionManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path
    
    def get_connection(self):
        """الحصول على اتصال قاعدة البيانات"""
        if self.db_path:
            from database.db_connection import get_db_connection
            return get_db_connection(self.db_path)
        else:
            return get_users_db_connection()
    
    def get_all_permissions(self) -> List[Dict]:
        """الحصول على جميع الصلاحيات المتاحة"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # استعلام آمن - فقط الأعمدة الأساسية
            cursor.execute("""
                SELECT id, permission_code, name_ar, name_en, module_id, is_active
                FROM permissions 
                ORDER BY name_ar
            """)
            
            permissions = []
            for row in cursor.fetchall():
                permissions.append({
                    'id': row[0],
                    'code': row[1],
                    'name_ar': row[2],
                    'name_en': row[3],
                    'module_id': row[4],
                    'is_active': bool(row[5])
                })
            return permissions
            
        except sqlite3.Error as e:
            print(f"Error getting permissions: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_user_permissions(self, user_id: int) -> Set[str]:
        """الحصول على صلاحيات مستخدم معين"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # استخدام الجدول الصحيح role_permissions بدلاً من user_permissions
            cursor.execute("""
                SELECT p.permission_code 
                FROM role_permissions rp
                JOIN permissions p ON rp.permission_id = p.id
                JOIN user_roles ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = ?
            """, (user_id,))
            
            return {row[0] for row in cursor.fetchall()}
            
        except sqlite3.Error as e:
            print(f"Error getting user permissions: {e}")
            return set()
        finally:
            if conn:
                conn.close()
    
    def has_permission(self, user_id: int, permission_code: str) -> bool:
        """التحقق إذا كان المستخدم لديه صلاحية معينة"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM role_permissions rp
                JOIN permissions p ON rp.permission_id = p.id
                JOIN user_roles ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = ? AND p.permission_code = ?
            """, (user_id, permission_code))
            
            return cursor.fetchone()[0] > 0
            
        except sqlite3.Error as e:
            print(f"Error checking permission: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_permission_by_id(self, permission_id: int) -> Optional[Dict]:
        """الحصول على صلاحية بواسطة ID"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, permission_code, name_ar, name_en, module_id, is_active
                FROM permissions WHERE id = ?
            """, (permission_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'code': row[1],
                    'name_ar': row[2],
                    'name_en': row[3],
                    'module_id': row[4],
                    'is_active': bool(row[5])
                }
            return None
            
        except sqlite3.Error as e:
            print(f"Error getting permission by id: {e}")
            return None
        finally:
            if conn:
                conn.close()

    # إزالة الدوال التي تعتمد على جدول user_permissions غير الموجود
    # واستبدالها بدوال تعمل مع الجداول الموجودة حسب المخطط
    
    def get_permission_categories(self) -> List[str]:
        """الحصول على فئات الصلاحيات (بديل مؤقت)"""
        # منذ لا يوجد عمود category، نستخدم module_id كبديل
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT m.name_ar 
                FROM permissions p
                JOIN modules m ON p.module_id = m.id
                ORDER BY m.name_ar
            """)
            
            return [row[0] for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            print(f"Error getting permission categories: {e}")
            return []
        finally:
            if conn:
                conn.close()
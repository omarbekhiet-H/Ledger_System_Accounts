# database/manager/admin/NEWuser_manager.py

import sqlite3
from typing import List, Dict, Optional, Tuple, Union
from database.db_connection import get_users_db_connection


class NEWUserManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def get_connection(self):
        """الحصول على اتصال قاعدة البيانات"""
        if self.db_path:
            from database.db_connection import get_db_connection
            return get_db_connection(self.db_path)
        else:
            return get_users_db_connection()

    # ------------------- عمليات على المستخدمين -------------------

    def create_user(
        self,
        username: str,
        password: str,
        name_ar: str = None,
        name_en: str = None,
        email: str = None,
        phone: str = None,
        is_active: bool = True,
    ) -> Tuple[bool, str]:
        """إنشاء مستخدم جديد (تخزين كلمة المرور كنص عادي)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # التحقق من عدم وجود اسم مستخدم
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return False, "اسم المستخدم موجود مسبقاً"

            cursor.execute(
                """
                INSERT INTO users (
                    username, password_hash, name_ar, name_en, email, phone, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (username, password, name_ar, name_en, email, phone, is_active),
            )
            conn.commit()
            return True, f"تم إنشاء المستخدم بنجاح (ID: {cursor.lastrowid})"

        except sqlite3.Error as e:
            return False, f"خطأ في إنشاء المستخدم: {str(e)}"
        finally:
            if conn:
                conn.close()

    def save_user(
        self,
        user_id: Optional[int] = None,
        username: str = None,
        password: str = None,
        name_ar: str = None,
        name_en: str = None,
        email: str = None,
        phone: str = None,
        is_active: bool = True,
    ) -> Tuple[bool, str]:
        """
        حفظ مستخدم (إنشاء جديد أو تحديث موجود)
        إذا تم تمرير user_id سيتم التحديث، وإلا سيتم الإنشاء
        """
        if user_id:
            return self.update_user(user_id, username, password, name_ar, name_en, email, phone, is_active)
        else:
            if not username or not password:
                return False, "يجب إدخال اسم المستخدم وكلمة المرور"
            return self.create_user(username, password, name_ar, name_en, email, phone, is_active)

    def update_user(
        self, 
        user_id: int, 
        username: str = None, 
        password: str = None,
        name_ar: str = None, 
        name_en: str = None, 
        email: str = None, 
        phone: str = None, 
        is_active: bool = None
    ) -> Tuple[bool, str]:
        """تحديث بيانات المستخدم"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # التحقق من وجود المستخدم
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return False, "المستخدم غير موجود"

            # بناء استعلام التحديث ديناميكياً
            update_fields = []
            update_values = []
            
            if username is not None:
                # التحقق من عدم تكرار اسم المستخدم
                cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (username, user_id))
                if cursor.fetchone():
                    return False, "اسم المستخدم موجود مسبقاً لمستخدم آخر"
                update_fields.append("username = ?")
                update_values.append(username)
            
            if password is not None:
                update_fields.append("password_hash = ?")
                update_values.append(password)
            
            if name_ar is not None:
                update_fields.append("name_ar = ?")
                update_values.append(name_ar)
            
            if name_en is not None:
                update_fields.append("name_en = ?")
                update_values.append(name_en)
            
            if email is not None:
                update_fields.append("email = ?")
                update_values.append(email)
            
            if phone is not None:
                update_fields.append("phone = ?")
                update_values.append(phone)
            
            if is_active is not None:
                update_fields.append("is_active = ?")
                update_values.append(is_active)
            
            if not update_fields:
                return False, "لم يتم تقديم أي بيانات للتحديث"

            update_fields.append("updated_at = datetime('now')")
            update_values.append(user_id)

            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, update_values)
            conn.commit()
            
            return True, "تم تحديث بيانات المستخدم بنجاح"
            
        except sqlite3.Error as e:
            return False, f"خطأ في تحديث المستخدم: {str(e)}"
        finally:
            if conn:
                conn.close()

    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        """حذف مستخدم بشكل دائم"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # التحقق من وجود المستخدم
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return False, "المستخدم غير موجود"

            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            
            return True, "تم حذف المستخدم بنجاح"
            
        except sqlite3.Error as e:
            return False, f"خطأ في حذف المستخدم: {str(e)}"
        finally:
            if conn:
                conn.close()

    def disable_user(self, user_id: int) -> Tuple[bool, str]:
        """تعطيل المستخدم (جعله غير نشط)"""
        return self.toggle_user_status(user_id, False)

    def enable_user(self, user_id: int) -> Tuple[bool, str]:
        """تفعيل المستخدم (جعله نشط)"""
        return self.toggle_user_status(user_id, True)

    def toggle_user_status(self, user_id: int, status: Optional[bool] = None) -> Tuple[bool, str]:
        """تبديل أو تعيين حالة المستخدم (نشط/غير نشط)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT is_active FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return False, "المستخدم غير موجود"

            if status is None:
                # تبديل الحالة الحالية
                new_status = 0 if row[0] else 1
            else:
                # تعيين الحالة المحددة
                new_status = 1 if status else 0

            cursor.execute(
                "UPDATE users SET is_active = ?, updated_at = datetime('now') WHERE id = ?", 
                (new_status, user_id)
            )
            conn.commit()
            
            status_text = "نشط" if new_status else "غير نشط"
            return True, f"تم تعيين حالة المستخدم إلى: {status_text}"
            
        except sqlite3.Error as e:
            return False, f"خطأ في تحديث الحالة: {str(e)}"
        finally:
            if conn:
                conn.close()

    def search_users(
        self, 
        search_term: str = None, 
        is_active: bool = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[bool, List[Dict], str]:
        """بحث عن المستخدمين بناء على معايير مختلفة"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            conditions = []
            params = []
            
            if search_term:
                conditions.append("""
                    (username LIKE ? OR 
                     name_ar LIKE ? OR 
                     name_en LIKE ? OR 
                     email LIKE ? OR 
                     phone LIKE ?)
                """)
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern] * 5)
            
            if is_active is not None:
                conditions.append("is_active = ?")
                params.append(1 if is_active else 0)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT id, username, name_ar, name_en, email, phone, is_active, created_at
                FROM users 
                {where_clause}
                ORDER BY username ASC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            users = []
            
            for row in cursor.fetchall():
                users.append({
                    "id": row[0],
                    "username": row[1],
                    "name_ar": row[2],
                    "name_en": row[3],
                    "email": row[4],
                    "phone": row[5],
                    "is_active": bool(row[6]),
                    "created_at": row[7],
                })
            
            return True, users, "تم البحث بنجاح"
            
        except sqlite3.Error as e:
            return False, [], f"خطأ في البحث: {str(e)}"
        finally:
            if conn:
                conn.close()


    def get_user_by_id(self, user_id):
        """يجلب بيانات مستخدم بواسطة ID"""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None:
                print("DEBUG: No connection in get_user_by_id")
                return None
            
            cursor = conn.cursor()
            # غير الاستعلام علشان ي match جدولك
            cursor.execute("""
                SELECT id, username, name_ar, name_en, email, is_active 
                FROM users WHERE id = ?
            """, (user_id,))
        
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                user_data = dict(zip(columns, row))
            
                # أضف full_name افتراضي من name_ar أو username
                if user_data.get('name_ar'):
                    user_data['full_name'] = user_data['name_ar']
                elif user_data.get('name_en'):
                    user_data['full_name'] = user_data['name_en']
                else:
                    user_data['full_name'] = user_data['username']
                
                print(f"DEBUG: Found user data: {user_data}")
                return user_data
            else:
                print(f"DEBUG: No user found with ID: {user_id}")
                return None
            
        except sqlite3.Error as e:
            print(f"Error getting user by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()
                
    def get_all_users(self) -> List[Dict]:
        """إرجاع جميع المستخدمين"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
            """
            SELECT id, username, name_ar, name_en, password_hash
            FROM users ORDER BY username ASC
            """
            )

            users = []
            for row in cursor.fetchall():
                full_name = row[2] or row[3] or row[1]
                users.append({
                    "id": row[0],
                    "username": row[1],
                    "full_name": full_name,
                    "password_hash": row[4],   # كلمة السر نص عادي
                })

            return users
        finally:
            if conn:
                conn.close()

    def authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[Dict], str]:
        """مصادقة المستخدم (مقارنة كلمة المرور كنص عادي)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, username, name_ar, name_en, email, phone, is_active, created_at, password_hash
                FROM users 
                WHERE username = ? AND is_active = 1
                """,
                (username,),
            )

            row = cursor.fetchone()
            if not row:
                return False, None, "اسم المستخدم غير موجود أو غير نشط"

            stored_password = row[8]
            if password != stored_password:
                return False, None, "كلمة المرور غير صحيحة"

            user_dict = {
                "id": row[0],
                "username": row[1],
                "full_name": row[2] or row[3] or row[1],
                "email": row[4],
                "phone": row[5],
                "is_active": bool(row[6]),
                "created_at": row[7],
            }
            return True, user_dict, "تمت المصادقة بنجاح"

        except sqlite3.Error as e:
            return False, None, f"خطأ في المصادقة: {str(e)}"
        finally:
            if conn:
                conn.close()

    def change_password(self, user_id: int, new_password: str) -> Tuple[bool, str]:
        """تغيير كلمة المرور (نص عادي)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password_hash = ?, updated_at = datetime('now') WHERE id = ?",
                (new_password, user_id),
            )
            conn.commit()
            return True, "تم تغيير كلمة المرور بنجاح"
        except sqlite3.Error as e:
            return False, f"خطأ في تغيير كلمة المرور: {str(e)}"
        finally:
            if conn:
                conn.close()

    def update_user_password(self, username, new_password):
        """تحديث كلمة المرور (نص عادي)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
        
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (new_password, username)
            )
            conn.commit()
            return True, "Password updated successfully."
        except Exception as e:
            return False, f"Failed to update password: {e}"
        finally:
            if conn:
                conn.close()


if __name__ == "__main__":
    print("⚠️ كلمة المرور تُخزن الآن نص عادي (بدون تشفير) لأغراض مؤقتة.")
    
    # أمثلة على الاستخدام
    manager = NEWUserManager()
    
    # إنشاء مستخدم جديد
    success, message = manager.create_user("test_user", "password123", "اختبار", "Test")
    print(f"Create User: {success} - {message}")
    
    # البحث عن المستخدمين
    success, users, message = manager.search_users("test")
    print(f"Search Users: {success} - {message}")
    for user in users:
        print(f"  - {user['username']} ({user['name_ar']})")
    
    # تعطيل مستخدم
    if users:
        user_id = users[0]['id']
        success, message = manager.disable_user(user_id)
        print(f"Disable User: {success} - {message}")
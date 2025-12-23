import sqlite3
from PyQt5.QtWidgets import QMessageBox

class BranchManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def _connect(self):
        """إنشاء اتصال بقاعدة البيانات"""
        return sqlite3.connect(self.db_path)

    def branch_exists(self, code, exclude_id=None):
        """التحقق من وجود فرع بنفس الكود مع استثناء معرف معين (للتحديث)"""
        conn = self._connect()
        cursor = conn.cursor()
        
        if exclude_id:
            cursor.execute("""
                SELECT COUNT(*) FROM branches 
                WHERE code = ? AND is_active = 1 AND id != ?
            """, (code, exclude_id))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM branches 
                WHERE code = ? AND is_active = 1
            """, (code,))
            
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def get_branch_by_id(self, branch_id):
        """الحصول على بيانات فرع بواسطة المعرف"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.*, l.location_name_ar 
                FROM branches b
                LEFT JOIN store_locations  l ON b.location_id = l.id
                WHERE b.id = ? AND b.is_active = 1
            """, (branch_id,))
            
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            conn.close()
            return dict(zip(columns, row)) if row else None
        except Exception as e:
            QMessageBox.critical(None, "خطأ", f"خطأ في جلب بيانات الفرع: {e}")
            return None

    def list_active_branches(self):
        """قائمة الفعالة مع معلومات الموقع"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    b.id, b.code, b.name_ar, b.name_en,
                    b.location_id, l.location_name_ar AS location_name,
                    b.created_at, b.updated_at
                FROM branches b
                LEFT JOIN store_locations  l ON b.location_id = l.id
                WHERE b.is_active = 1
                ORDER BY b.created_at DESC
            """)
            
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            QMessageBox.critical(None, "خطأ", f"خطأ في جلب قائمة الفروع: {e}")
            return []

    def create_branch(self, code, name_ar, name_en, location_id):
        """إضافة فرع جديد"""
        try:
            # التحقق من البيانات المطلوبة
            if not code.strip():
                QMessageBox.warning(None, "خطأ", "يرجى إدخال كود الفرع")
                return False
            if not name_ar.strip():
                QMessageBox.warning(None, "خطأ", "يرجى إدخال الاسم العربي")
                return False
            
            # التحقق من عدم تكرار الكود
            if self.branch_exists(code):
                QMessageBox.warning(None, "خطأ", "كود الفرع موجود مسبقاً")
                return False
            
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO branches (
                    code, name_ar, name_en, location_id, 
                    is_active, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (code.strip(), name_ar.strip(), name_en.strip(), location_id))
            
            conn.commit()
            branch_id = cursor.lastrowid
            conn.close()
            
            QMessageBox.information(None, "نجاح", "تم إضافة الفرع بنجاح")
            return branch_id
            
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "خطأ", "كود الفرع موجود مسبقاً")
            return False
        except Exception as e:
            QMessageBox.critical(None, "خطأ", f"خطأ في إضافة الفرع: {e}")
            return False

    def update_branch(self, branch_id, code, name_ar, name_en, location_id):
        """تحديث بيانات الفرع"""
        try:
            # التحقق من البيانات المطلوبة
            if not code.strip():
                QMessageBox.warning(None, "خطأ", "يرجى إدخال كود الفرع")
                return False
            if not name_ar.strip():
                QMessageBox.warning(None, "خطأ", "يرجى إدخال الاسم العربي")
                return False
            
            # التحقق من عدم تكرار الكود (مع استثناء الفرع الحالي)
            if self.branch_exists(code, branch_id):
                QMessageBox.warning(None, "خطأ", "كود الفرع موجود مسبقاً في فرع آخر")
                return False
            
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE branches SET
                    code = ?,
                    name_ar = ?,
                    name_en = ?,
                    location_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
            """, (code.strip(), name_ar.strip(), name_en.strip(), location_id, branch_id))
            
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            if affected_rows > 0:
                QMessageBox.information(None, "نجاح", "تم تحديث الفرع بنجاح")
                return True
            else:
                QMessageBox.warning(None, "تحذير", "لم يتم العثور على الفرع للتحديث")
                return False
                
        except sqlite3.IntegrityError:
            QMessageBox.warning(None, "خطأ", "كود الفرع موجود مسبقاً")
            return False
        except Exception as e:
            QMessageBox.critical(None, "خطأ", f"خطأ في تحديث الفرع: {e}")
            return False

    def delete_branch(self, branch_id):
        """حذف فرع (تعطيل)"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE branches SET
                    is_active = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (branch_id,))
            
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            if affected_rows > 0:
                QMessageBox.information(None, "نجاح", "تم حذف الفرع بنجاح")
                return True
            else:
                QMessageBox.warning(None, "تحذير", "لم يتم العثور على الفرع للحذف")
                return False
                
        except Exception as e:
            QMessageBox.critical(None, "خطأ", f"خطأ في حذف الفرع: {e}")
            return False

    def search_branches(self, search_term):
        """بحث الفروع حسب الاسم أو الكود"""
        try:
            if not search_term.strip():
                return self.list_active_branches()
                
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    b.id, b.code, b.name_ar, b.name_en,
                    l.location_name_ar AS location_name
                FROM branches b
                LEFT JOIN store_locations  l ON b.location_id = l.id
                WHERE b.is_active = 1 
                AND (b.name_ar LIKE ? OR b.code LIKE ? OR b.name_en LIKE ?)
                ORDER BY b.name_ar
            """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            QMessageBox.critical(None, "خطأ", f"خطأ في البحث: {e}")
            return []
import sqlite3
from typing import List, Dict, Optional, Union

class ItemCategoryManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        """إنشاء اتصال بقاعدة البيانات"""
        return sqlite3.connect(self.db_path)
    
    def list_active_item_categories(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM item_categories WHERE is_active = 1")
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            print(f"خطأ أثناء جلب الفئات النشطة: {e}")
            return []

    def list_parent_categories(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name_ar
                FROM item_categories
                WHERE parent_id IS NULL AND is_active = 1
                ORDER BY name_ar
            """)
            rows = cursor.fetchall()
            return [dict(zip(["id", "name_ar"], row)) for row in rows]
        except sqlite3.Error as e:
            print(f"خطأ أثناء جلب التصنيفات الرئيسية: {e}")
            return []
        finally:
            conn.close()
            
    def list_subcategories(self, parent_id: int):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name_ar
                FROM item_categories
                WHERE parent_id = ? AND is_active = 1
                ORDER BY name_ar
            """, (parent_id,))
            rows = cursor.fetchall()
            return [dict(zip(["id", "name_ar"], row)) for row in rows]
        except sqlite3.Error as e:
            print(f"خطأ أثناء جلب التصنيفات الفرعية: {e}")
            return []
        finally:
            conn.close()

    


    def list_active_categories(self) -> List[Dict[str, Union[str, int, None]]]:
        """استرجاع جميع الفئات النشطة مع معلومات الفئات الأب"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    c.id, c.code, c.name_ar, c.name_en, c.description,
                    c.parent_id, p.name_ar as parent_name, p.code as parent_code
                FROM item_categories c
                LEFT JOIN item_categories p ON c.parent_id = p.id AND p.is_active = 1
                WHERE c.is_active = 1
                ORDER BY c.name_ar
            """)
            rows = cursor.fetchall()
            return [dict(zip(
                ["id", "code", "name_ar", "name_en", "description", 
                 "parent_id", "parent_name", "parent_code"],
                row
            )) for row in rows]
        except sqlite3.Error as e:
            print(f"خطأ في قاعدة البيانات: {e}")
            return []
        finally:
            conn.close()

    def category_exists(self, code: str, exclude_id: Optional[int] = None) -> bool:
        """التحقق من وجود كود الفئة"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            query = "SELECT 1 FROM item_categories WHERE code = ? AND is_active = 1"
            params = [code]
            
            if exclude_id:
                query += " AND id != ?"
                params.append(exclude_id)
                
            cursor.execute(query, params)
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(f"خطأ في قاعدة البيانات: {e}")
            return False
        finally:
            conn.close()

    def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Union[str, int, None]]]:
        """الحصول على فئة بواسطة المعرف"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, code, name_ar, name_en, description, parent_id
                FROM item_categories
                WHERE id = ? AND is_active = 1
            """, (category_id,))
            row = cursor.fetchone()
            return dict(zip(
                ["id", "code", "name_ar", "name_en", "description", "parent_id"],
                row
            )) if row else None
        except sqlite3.Error as e:
            print(f"خطأ في قاعدة البيانات: {e}")
            return None
        finally:
            conn.close()

    def create_category(self, code: str, name_ar: str, name_en: str, 
                       parent_id: Optional[int], description: str) -> bool:
        """إنشاء فئة جديدة"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO item_categories (code, name_ar, name_en, parent_id, description)
                VALUES (?, ?, ?, ?, ?)
            """, (code, name_ar, name_en, parent_id, description))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"خطأ في قاعدة البيانات: {e}")
            return False
        finally:
            conn.close()

    def update_category(self, category_id: int, code: str, name_ar: str, 
                       name_en: str, parent_id: Optional[int], description: str) -> bool:
        """تحديث بيانات الفئة"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE item_categories
                SET code = ?, name_ar = ?, name_en = ?, parent_id = ?, 
                    description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (code, name_ar, name_en, parent_id, description, category_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"خطأ في قاعدة البيانات: {e}")
            return False
        finally:
            conn.close()

    def delete_category(self, category_id: int) -> bool:
        """حذف فئة (تعطيلها)"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE item_categories
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (category_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"خطأ في قاعدة البيانات: {e}")
            return False
        finally:
            conn.close()
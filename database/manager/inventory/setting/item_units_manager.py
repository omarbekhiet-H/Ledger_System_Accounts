import sqlite3
from typing import List, Dict, Optional

class ItemUnitManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        """إنشاء اتصال بقاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # للوصول إلى الأعمدة بأسمائها
        return conn

    def list_active_units(self) -> List[Dict[str, str]]:
        """استرجاع جميع الوحدات النشطة"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, code, name_ar, name_en
                FROM units
                WHERE is_active = 1
                ORDER BY name_ar
            """)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"خطأ في قاعدة البيانات: {e}")
            return []
        finally:
            conn.close()

    def search_units(self, search_term: str) -> List[Dict[str, str]]:
        """بحث الوحدات حسب الاسم أو الكود"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, code, name_ar, name_en
                FROM units
                WHERE is_active = 1 
                AND (name_ar LIKE ? OR name_en LIKE ? OR code LIKE ?)
                ORDER BY name_ar
            """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"خطأ في قاعدة البيانات: {e}")
            return []
        finally:
            conn.close()

    def unit_exists(self, code: str, exclude_id: Optional[int] = None) -> bool:
        """التحقق من وجود كود الوحدة"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            query = "SELECT 1 FROM units WHERE code = ? AND is_active = 1"
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

    def create_unit(self, code: str, name_ar: str, name_en: str = "") -> bool:
        """إنشاء وحدة جديدة"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO units (code, name_ar, name_en)
                VALUES (?, ?, ?)
            """, (code, name_ar, name_en))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            print(f"خطأ تكامل البيانات: {e}")
            return False
        except sqlite3.Error as e:
            print(f"خطأ في قاعدة البيانات: {e}")
            return False
        finally:
            conn.close()

    def update_unit(self, unit_id: int, code: str, name_ar: str, name_en: str = "") -> bool:
        """تحديث بيانات الوحدة"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE units
                SET code = ?, name_ar = ?, name_en = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
            """, (code, name_ar, name_en, unit_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            print(f"خطأ تكامل البيانات: {e}")
            return False
        except sqlite3.Error as e:
            print(f"خطأ في قاعدة البيانات: {e}")
            return False
        finally:
            conn.close()

    def delete_unit(self, unit_id: int) -> bool:
        """حذف وحدة (تعطيلها)"""
        conn = self._connect()
        try:
            # التحقق أولاً إذا كانت الوحدة مستخدمة في أصناف
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM items WHERE base_unit_id = ? AND is_active = 1
            """, (unit_id,))
            count = cursor.fetchone()[0]
            
            if count > 0:
                print("لا يمكن حذف وحدة مستخدمة في أصناف")
                return False
                
            # إذا لم تكن مستخدمة، يتم التعطيل
            cursor.execute("""
                UPDATE units
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (unit_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"خطأ في قاعدة البيانات: {e}")
            return False
        finally:
            conn.close()
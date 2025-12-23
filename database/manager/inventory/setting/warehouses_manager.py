import sqlite3
from typing import List, Dict, Optional

class WarehouseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row # لتسهيل الوصول للبيانات
        return conn

    def list_active_warehouses(self) -> List[Dict]:
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    w.id, w.code, w.name_ar, w.name_en,
                    b.name_ar AS branch_name,
                    w.branch_id
                FROM warehouses w
                LEFT JOIN branches b ON w.branch_id = b.id
                WHERE w.is_active = 1 AND b.is_active = 1
                ORDER BY w.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error in list_active_warehouses: {e}")
            return []
        finally:
            conn.close()

    def create_warehouse(self, code: str, name_ar: str, name_en: str, branch_id: int) -> bool:
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO warehouses (code, name_ar, name_en, branch_id)
                VALUES (?, ?, ?, ?)
            """, (code, name_ar, name_en, branch_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError: # أكثر تحديداً للخطأ
            print(f"Database integrity error: Warehouse code '{code}' may already exist.")
            return False
        except sqlite3.Error as e:
            print(f"Database error in create_warehouse: {e}")
            return False
        finally:
            conn.close()

    # **تصحيح: تعديل دالة التحديث بالكامل**
    def update_warehouse(self, warehouse_id: int, code: str, name_ar: str, 
                        name_en: str, branch_id: int) -> bool:
        """Update an existing warehouse without location."""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE warehouses
                SET code = ?, name_ar = ?, name_en = ?, 
                    branch_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (code, name_ar, name_en, branch_id, warehouse_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Database error in update_warehouse: {e}")
            return False
        finally:
            conn.close()

    def delete_warehouse(self, warehouse_id: int) -> bool:
        """Soft delete a warehouse."""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE warehouses SET is_active = 0 WHERE id = ?", (warehouse_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Database error in delete_warehouse: {e}")
            return False
        finally:
            conn.close()
            
    # **إضافة: دالة للتحقق من تكرار الكود**
    def warehouse_exists(self, code: str, exclude_id: Optional[int] = None) -> bool:
        """Check if a warehouse with the given code already exists."""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            query = "SELECT 1 FROM warehouses WHERE code = ? AND is_active = 1"
            params = [code]
            if exclude_id:
                query += " AND id != ?"
                params.append(exclude_id)
            
            cursor.execute(query, params)
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(f"Database error in warehouse_exists: {e}")
            return False
        finally:
            conn.close()
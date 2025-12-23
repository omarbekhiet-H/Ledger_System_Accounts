import sqlite3
from typing import List, Dict, Any, Optional
#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#
class ItemsManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        """إنشاء اتصال بقاعدة البيانات مع تفعيل الوصول للحقول بالأسماء"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#
    def get_last_item_code(self, parent_category_id: int) -> Optional[str]:
        """استرجاع آخر كود صنف لتصنيف أب معين"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT item_code 
                FROM items 
                WHERE parent_category_id = ? 
                ORDER BY item_code DESC 
                LIMIT 1
            """, (parent_category_id,))
            result = cursor.fetchone()
            return result['item_code'] if result else None
        except sqlite3.Error as e:
            print(f"خطأ في get_last_item_code: {e}")
            return None
        finally:
            conn.close()
#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#
    def list_items_with_movements(self) -> List[Dict[str, Any]]:
        """استرجاع الأصناف مع عدد حركاتها (النسخة المصححة)"""
        # تأكد من أن كل الأسطر التالية تبدأ بمسافة بادئة واحدة
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    i.id,
                    i.item_code,
                    i.item_name_ar,
                    i.item_type,
                    i.purchase_price AS cost_price,
                    i.sale_price,
                    i.min_stock_limit,
                    i.max_stock_limit,
                    i.reorder_point,
                     i.expiry_date,
                    i.has_expiry_date AS has_expiry,
                    ic.name_ar AS category_name,
                    u.name_ar AS unit_name,
                    (SELECT COUNT(*) FROM item_movements WHERE item_id = i.id) AS movement_count
                FROM
                    items AS i
                LEFT JOIN
                    item_categories AS ic ON i.item_category_id = ic.id
                LEFT JOIN
                    units AS u ON i.base_unit_id = u.id
                WHERE
                    i.is_active = 1
                ORDER BY
                    i.item_name_ar
            """)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"خطأ في list_items_with_movements: {e}")
            return []
        finally:
            conn.close()
#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#


    def check_items_table_structure(self):
        """التحقق من هيكل جدول items"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(items)")
            columns = cursor.fetchall()
            print("أعمدة جدول items:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            return columns
        finally:
            conn.close()        
#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#
    def create_item(self, item_data: Dict[str, Any], units: List[Dict[str, Any]]) -> bool:
        """إضافة صنف جديد مع وحداته"""
        conn = self._connect()
        cursor = conn.cursor()
        try:
            # إضافة الصنف الرئيسي
            cursor.execute("""
                INSERT INTO items (
                    item_code, item_name_ar, item_type,
                    parent_category_id, category_id,
                    cost_price, sale_price, 
                    min_stock_limit, max_stock_limit, reorder_point,
                    has_expiry, expiry_date,
                    base_unit_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_data['item_code'],
                item_data['item_name_ar'],
                item_data['item_type'],
                item_data['parent_category_id'],
                item_data['category_id'],
                item_data['cost_price'],
                item_data['sale_price'],
                item_data['min_stock_limit'],
                item_data['max_stock_limit'],
                item_data['reorder_point'],
                item_data['has_expiry'],
                item_data['expiry_date'],
                units[0]['unit_id'] if units else None
            ))
            
            item_id = cursor.lastrowid
            
            # إضافة الوحدات
            for unit in units:
                cursor.execute("""
                    INSERT INTO item_units (
                        item_id, unit_id, is_main, is_medium, is_small,
                        conversion_factor
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    item_id,
                    unit['unit_id'],
                    unit.get('is_main', False),
                    unit.get('is_medium', False),
                    unit.get('is_small', False),
                    unit.get('conversion_factor', 1.0)
                ))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"خطأ في create_item: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#
    def get_item_details(self, item_id: int) -> Optional[Dict[str, Any]]:
        """استرجاع تفاصيل صنف مع وحداته"""
        conn = self._connect()
        try:
            # بيانات الصنف الأساسية
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    i.*,
                    ic.name_ar AS category_name,
                    pc.name_ar AS parent_category_name,
                    ic.id AS category_id,
                    pc.id AS parent_category_id
                FROM items i
                LEFT JOIN item_categories ic ON i.item_category_id = ic.id
                LEFT JOIN item_categories pc ON ic.parent_id = pc.id
                WHERE i.id = ?
            """, (item_id,))
            item = cursor.fetchone()
        
            if not item:
                return None
            
            item_data = dict(item)
        
            # وحدات الصنف
            cursor.execute("""
                SELECT 
                    iu.*,
                    u.name_ar AS unit_name
                FROM item_units iu
                JOIN units u ON iu.unit_id = u.id
                WHERE iu.item_id = ?
            """, (item_id,))
        
            item_data['units'] = [dict(row) for row in cursor.fetchall()]
        
            return item_data
        except sqlite3.Error as e:
            print(f"خطأ في get_item_details: {e}")
            return None
        finally:
            conn.close()
#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#
    def update_item(self, item_id: int, item_data: Dict[str, Any], units: List[Dict[str, Any]]) -> bool:
        """تحديث بيانات صنف"""
        conn = self._connect()
        cursor = conn.cursor()
        try:
            # تحديث بيانات الصنف
            cursor.execute("""
                UPDATE items SET
                    item_name_ar = ?,
                    item_type = ?,
                    parent_category_id = ?,
                    category_id = ?,
                    cost_price = ?,
                    sale_price = ?,
                    min_stock_limit = ?,
                    max_stock_limit = ?,
                    reorder_point = ?,
                    has_expiry = ?,
                    expiry_date = ?,
                    base_unit_id = ?
                WHERE id = ?
            """, (
                item_data['item_name_ar'],
                item_data['item_type'],
                item_data['parent_category_id'],
                item_data['category_id'],
                item_data['cost_price'],
                item_data['sale_price'],
                item_data['min_stock_limit'],
                item_data['max_stock_limit'],
                item_data['reorder_point'],
                item_data['has_expiry'],
                item_data['expiry_date'],
                units[0]['unit_id'] if units else None,
                item_id
            ))
            
            # حذف الوحدات القديمة
            cursor.execute("DELETE FROM item_units WHERE item_id = ?", (item_id,))
            
            # إضافة الوحدات الجديدة
            for unit in units:
                cursor.execute("""
                    INSERT INTO item_units (
                        item_id, unit_id, is_main, is_medium, is_small,
                        conversion_factor
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    item_id,
                    unit['unit_id'],
                    unit.get('is_main', False),
                    unit.get('is_medium', False),
                    unit.get('is_small', False),
                    unit.get('conversion_factor', 1.0)
                ))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"خطأ في update_item: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#
    def delete_item(self, item_id: int) -> bool:
        """حذف صنف (حذف منطقي)"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE items SET is_active = 0 WHERE id = ?", (item_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"خطأ في delete_item: {e}")
            return False
        finally:
            conn.close()
#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#
    def get_item_base_unit(self, item_id: int) -> Optional[int]:
        """استرجاع الـ unit_id للوحدة الأساسية للصنف"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT base_unit_id 
                FROM items 
                WHERE id = ?
            """, (item_id,))
            result = cursor.fetchone()
            return result['base_unit_id'] if result else None
        except sqlite3.Error as e:
            print(f"خطأ في get_item_base_unit: {e}")
            return None
        finally:
            conn.close()
#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#
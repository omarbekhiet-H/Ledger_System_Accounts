
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime

class InventoryCycleManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        """إنشاء اتصال بقاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_items_below_reorder_point(self, warehouse_id: int = None) -> List[Dict[str, Any]]:
        """
        استرجاع الأصناف التي وصلت إلى نقطة إعادة الطلب
        """
        conn = self._connect()
        try:
            query = """
                SELECT 
                    i.id, i.item_code, i.item_name_ar, 
                    i.reorder_point, i.min_stock_limit, i.max_stock_limit,
                    u.name_ar AS unit_name,
                    COALESCE(SUM(CASE WHEN st.transaction_type = 'In' THEN st.quantity ELSE -st.quantity END), 0) AS current_stock
                FROM items i
                JOIN units u ON i.base_unit_id = u.id
                LEFT JOIN stock_transactions st ON i.id = st.item_id 
                    AND (? IS NULL OR st.warehouse_id = ?)
                WHERE i.is_active = 1
                GROUP BY i.id
                HAVING current_stock <= i.reorder_point
                ORDER BY i.item_name_ar
            """
            cursor = conn.cursor()
            cursor.execute(query, (warehouse_id, warehouse_id))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"خطأ في get_items_below_reorder_point: {e}")
            return []
        finally:
            conn.close()

#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#
    def create_purchase_request(self, requester_id: int, items: List[Dict[str, Any]]) -> Optional[int]:
        """
        إنشاء طلب شراء جديد برقم تسلسلي يومي
        """
        conn = self._connect()
        cursor = conn.cursor()
        try:
            # تاريخ اليوم
            request_date = datetime.now().strftime("%Y-%m-%d")
            date_code = datetime.now().strftime("%Y%m%d")

            # جلب آخر رقم تسلسلي لليوم الحالي
            cursor.execute("""
                SELECT request_number
                FROM purchase_requests
                WHERE request_number LIKE ?
                ORDER BY request_number DESC
                LIMIT 1
            """, (f"PR-{date_code}-%",))
            last_request = cursor.fetchone()

            if last_request:
                # استخراج الرقم وزيادته
                last_number = int(last_request[0].split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            # توليد رقم الطلب
            request_number = f"PR-{date_code}-{new_number:04d}"

            # إنشاء طلب الشراء الرئيسي
            cursor.execute("""
                INSERT INTO purchase_requests (request_number, request_date, requester_id, status)
                VALUES (?, ?, ?, 'pending')
            """, (request_number, request_date, requester_id))
        
            request_id = cursor.lastrowid
        
            # إضافة الأصناف إلى طلب الشراء
            for item in items:
                cursor.execute("""
                    INSERT INTO request_items (
                        request_id, item_id, quantity, unit_id, notes
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    request_id,
                    item['item_id'],
                    item['quantity'],
                    item['unit_id'],
                    item.get('notes', '')
                ))
        
            conn.commit()
            return request_id
        except sqlite3.Error as e:
            print(f"خطأ في create_purchase_request: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def generate_purchase_order(self, request_id: int, supplier_id: int) -> Optional[int]:
            """
            إنشاء أمر شراء من طلب الشراء
            """
            conn = self._connect()
            cursor = conn.cursor()
            try:
                # الحصول على تفاصيل طلب الشراء
                cursor.execute("SELECT * FROM purchase_requests WHERE id = ?", (request_id,))
                request = cursor.fetchone()
            
                if not request:
                    return None
                
                # إنشاء أمر الشراء
                order_date = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("""
                    INSERT INTO purchase_orders (
                        supplier_id, order_date, status
                    ) VALUES (?, ?, 'pending')
                """, (supplier_id, order_date))
            
                order_id = cursor.lastrowid
            
                # نقل الأصناف من طلب الشراء إلى أمر الشراء
                cursor.execute("""
                    INSERT INTO order_items (
                        order_id, item_id, quantity, unit_id, unit_price, notes
                    )
                    SELECT 
                        ?, item_id, quantity, unit_id, 
                        (SELECT purchase_price FROM items WHERE id = item_id),
                        notes
                    FROM request_items 
                    WHERE request_id = ?
                """, (order_id, request_id))
            
                # تحديث حالة طلب الشراء إلى "مكتمل"
                cursor.execute("""
                    UPDATE purchase_requests 
                    SET status = 'completed'
                    WHERE id = ?
                """, (request_id,))
            
                conn.commit()
                return order_id
            except sqlite3.Error as e:
                print(f"خطأ في generate_purchase_order: {e}")
                conn.rollback()
                return None
            finally:
                conn.close()

    def get_purchase_request_details(self, request_id: int) -> Optional[Dict[str, Any]]:
            """
            استرجاع تفاصيل طلب شراء مع الأصناف
            """
            conn = self._connect()
            try:
                cursor = conn.cursor()
            
                # بيانات الطلب الأساسية
                cursor.execute("""
                    SELECT * FROM purchase_requests WHERE id = ?
                """, (request_id,))
                request = cursor.fetchone()
            
                if not request:
                    return None
                
                request_data = dict(request)
            
                # الأصناف المطلوبة
                cursor.execute("""
                    SELECT 
                        ri.*,
                        i.item_code, i.item_name_ar,
                        u.name_ar AS unit_name
                    FROM request_items ri
                    JOIN items i ON ri.item_id = i.id
                    JOIN units u ON ri.unit_id = u.id
                    WHERE ri.request_id = ?
                """, (request_id,))
            
                request_data['items'] = [dict(row) for row in cursor.fetchall()]
            
                return request_data
            except sqlite3.Error as e:
                print(f"خطأ في get_purchase_request_details: {e}")
                return None
            finally:
                conn.close()

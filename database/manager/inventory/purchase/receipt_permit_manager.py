import os
import sys
from datetime import datetime
from database.db_connection import get_inventory_db_connection

class ReceiptPermit:
    """إدارة إذونات الاستلام والتعامل مع قاعدة البيانات"""

    def __init__(self):
        self.conn = get_inventory_db_connection()
        if self.conn is None:
            raise Exception("فشل الاتصال بقاعدة بيانات المخزون")
        self.cursor = self.conn.cursor()

    def create_receipt_permit(self, supply_order_id, warehouse_id):
        """إنشاء إذن استلام جديد"""
        try:
            permit_number = f"RP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            permit_date = datetime.now().strftime('%Y-%m-%d')

            self.cursor.execute("""
                INSERT INTO receipt_permits 
                (permit_number, permit_date, supply_order_id, warehouse_id, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (permit_number, permit_date, supply_order_id, warehouse_id))

            permit_id = self.cursor.lastrowid
            self.conn.commit()
            return permit_id
        except Exception as e:
            self.conn.rollback()
            raise e

    def update_received_quantity(self, permit_id, item_id, received_quantity, unit_id, notes):
        """تحديث الكمية المستلمة للصنف"""
        try:
            # الحصول على الكمية المطلوبة من أمر التوريد
            self.cursor.execute("""
                SELECT soi.quantity 
                FROM supply_order_items soi
                JOIN receipt_permits rp ON soi.order_id = rp.supply_order_id
                WHERE rp.id = ? AND soi.item_id = ?
            """, (permit_id, item_id))
            
            result = self.cursor.fetchone()
            if result:
                quantity_required = result[0]
                
                # إدخال أو تحديث سجل في receipt_permit_items
                self.cursor.execute("""
                    INSERT OR REPLACE INTO receipt_permit_items 
                    (receipt_permit_id, item_id, quantity, received_quantity, unit_id, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (permit_id, item_id, quantity_required, received_quantity, unit_id, notes))
                
                self.conn.commit()
            else:
                raise Exception("لم يتم العثور على الصنف في أمر التوريد")
        except Exception as e:
            self.conn.rollback()
            raise e

    def complete_receipt(self, permit_id):
        """إكمال عملية الاستلام"""
        try:
            # تحديث حالة إذن الاستلام
            self.cursor.execute("""
                UPDATE receipt_permits 
                SET status = 'completed', receipt_date = date('now')
                WHERE id = ?
            """, (permit_id,))
            
            # الحصول على supply_order_id
            self.cursor.execute("""
                SELECT supply_order_id FROM receipt_permits WHERE id = ?
            """, (permit_id,))
            
            supply_order_id = self.cursor.fetchone()[0]
            
            # تحديث الكميات المستلمة في supply_order_items
            self.cursor.execute("""
                UPDATE supply_order_items 
                SET received_quantity = received_quantity + (
                    SELECT received_quantity 
                    FROM receipt_permit_items 
                    WHERE receipt_permit_id = ? 
                    AND item_id = supply_order_items.item_id
                )
                WHERE order_id = ?
            """, (permit_id, supply_order_id))
            
            # التحقق إذا كان أمر التوريد مكتملاً بالكامل
            self.cursor.execute("""
                SELECT COUNT(*) 
                FROM supply_order_items 
                WHERE order_id = ? AND quantity > COALESCE(received_quantity, 0)
            """, (supply_order_id,))
            
            pending_items = self.cursor.fetchone()[0]
            
            if pending_items == 0:
                # تحديث حالة أمر التوريد إلى مكتمل
                self.cursor.execute("""
                    UPDATE supply_orders 
                    SET status = 'completed'
                    WHERE id = ?
                """, (supply_order_id,))
            else:
                # تحديث حالة أمر التوريد إلى مستلم جزئياً
                self.cursor.execute("""
                    UPDATE supply_orders 
                    SET status = 'partially_received'
                    WHERE id = ?
                """, (supply_order_id,))
            
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def close(self):
        """إغلاق الاتصال"""
        if self.conn:
            self.conn.close()
import os
import sys
from datetime import datetime
import logging
from database.db_connection import get_inventory_db_connection

class AdditionPermit:
    def __init__(self):
        self.conn = get_inventory_db_connection()
        if self.conn is None:
            raise Exception("فشل الاتصال بقاعدة بيانات المخزون")
        self.cursor = self.conn.cursor()

    def create_addition_permit(self, receipt_id):
        """إنشاء إذن إضافة بناء على إذن الاستلام"""
        try:
            self.cursor.execute("SELECT * FROM receipt_permits WHERE id = ?", (receipt_id,))
            receipt = self.cursor.fetchone()
            if not receipt:
                raise ValueError("إذن الاستلام غير موجود")

            self.cursor.execute("""
                INSERT INTO addition_permits 
                (receipt_id, addition_date, status)
                VALUES (?, ?, 'pending')
            """, (receipt_id, datetime.now().strftime('%Y-%m-%d')))

            addition_id = self.cursor.lastrowid

            # نسخ الأصناف
            self.copy_receipt_items_to_addition(receipt_id, addition_id)

            self.conn.commit()
            logging.info(f"تم إنشاء إذن الإضافة برقم: {addition_id}")
            return addition_id
        except Exception as e:
            self.conn.rollback()
            logging.error(f"خطأ في إنشاء إذن الإضافة: {e}")
            raise e

    def copy_receipt_items_to_addition(self, receipt_id, addition_id):
        """نسخ الأصناف من إذن الاستلام إلى إذن الإضافة"""
        self.cursor.execute("""
            SELECT item_id, received_quantity, unit_id 
            FROM receipt_items 
            WHERE permit_id = ? AND received_quantity > 0
        """, (receipt_id,))

        items = self.cursor.fetchall()
        if not items:
            logging.warning("لم يتم العثور على أصناف في إذن الاستلام")

        for item_id, quantity, unit_id in items:
            self.cursor.execute("""
                INSERT INTO addition_items 
                (permit_id, item_id, quantity, unit_id)
                VALUES (?, ?, ?, ?)
            """, (addition_id, item_id, quantity, unit_id))

        logging.info(f"تم نسخ {len(items)} صنف إلى إذن الإضافة")

    def complete_addition(self, addition_id):
        """إكمال عملية الإضافة"""
        try:
            self.cursor.execute("""
                UPDATE addition_permits 
                SET status = 'completed'
                WHERE id = ?
            """, (addition_id,))

            self.conn.commit()
            logging.info(f"تم إكمال إذن الإضافة رقم: {addition_id}")
            return True
        except Exception as e:
            self.conn.rollback()
            logging.error(f"خطأ في إكمال إذن الإضافة: {e}")
            raise e

    def get_addition_details(self, addition_id):
        """الحصول على تفاصيل إذن الإضافة"""
        try:
            self.cursor.execute("""
                SELECT ap.*, rp.id as receipt_id, so.order_number
                FROM addition_permits ap
                LEFT JOIN receipt_permits rp ON ap.receipt_id = rp.id
                LEFT JOIN supply_orders so ON rp.order_id = so.id
                WHERE ap.id = ?
            """, (addition_id,))
            addition = self.cursor.fetchone()

            self.cursor.execute("""
                SELECT ai.*, i.item_name_ar, i.item_code, u.name_ar as unit_name
                FROM addition_items ai
                LEFT JOIN items i ON ai.item_id = i.id
                LEFT JOIN units u ON ai.unit_id = u.id
                WHERE ai.permit_id = ?
            """, (addition_id,))
            items = self.cursor.fetchall()

            return addition, items
        except Exception as e:
            logging.error(f"خطأ في الحصول على تفاصيل إذن الإضافة: {e}")
            return None, None

    def close(self):
        """إغلاق الاتصال"""
        if self.conn:
            self.conn.close()
            logging.info("تم إغلاق الاتصال بقاعدة البيانات")
import os
import sys
from datetime import datetime
from database.db_connection import get_inventory_db_connection


class SupplyOrder:
    """إدارة أوامر التوريد والتعامل مع قاعدة البيانات"""

    def __init__(self):
        self.conn = get_inventory_db_connection()
        if self.conn is None:
            raise Exception("فشل الاتصال بقاعدة بيانات المخزون")
        self.cursor = self.conn.cursor()

    def create_supply_order(self, request_id, supplier_id, notes=None, delivery_days=7):
        """إنشاء أمر توريد جديد"""
        try:
            order_number = f"SO-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            order_date = datetime.now().strftime('%Y-%m-%d')

            self.cursor.execute("""
                INSERT INTO supply_orders 
                (order_number, order_date, request_id, supplier_id, notes, delivery_days, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """, (order_number, order_date, request_id, supplier_id, notes, delivery_days))

            order_id = self.cursor.lastrowid

            # نسخ الأصناف من طلب الشراء إلى أمر التوريد
            self.copy_request_items_to_order(request_id, order_id)

            self.conn.commit()
            return order_id
        except Exception as e:
            self.conn.rollback()
            raise e

    def copy_request_items_to_order(self, request_id, order_id):
        """نسخ أصناف طلب الشراء إلى أمر التوريد"""
        self.cursor.execute("""
            SELECT item_id, quantity, unit_price
            FROM purchase_request_items
            WHERE request_id = ?
        """, (request_id,))
        items = self.cursor.fetchall()

        for item_id, quantity, price in items:
            self.cursor.execute("""
                INSERT INTO supply_order_items (order_id, item_id, quantity, price)
                VALUES (?, ?, ?, ?)
            """, (order_id, item_id, quantity, price))

    def add_order_item(self, order_id, item_id, quantity, price):
        """إضافة صنف يدويًا إلى أمر التوريد"""
        try:
            self.cursor.execute("""
                INSERT INTO supply_order_items (order_id, item_id, quantity, price)
                VALUES (?, ?, ?, ?)
            """, (order_id, item_id, quantity, price))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def update_order_item_price(self, order_id, item_id, new_price):
        """تحديث سعر الصنف في أمر التوريد"""
        try:
            self.cursor.execute("""
                UPDATE supply_order_items 
                SET price = ?
                WHERE order_id = ? AND item_id = ?
            """, (new_price, order_id, item_id))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def complete_order(self, order_id):
        """إكمال أمر التوريد"""
        self.cursor.execute("""
            UPDATE supply_orders 
            SET status = 'completed'
            WHERE id = ?
        """, (order_id,))
        self.conn.commit()

    def get_orders_by_status(self, status):
        """الحصول على أوامر التوريد حسب الحالة"""
        self.cursor.execute("""
            SELECT so.*, s.name_ar as supplier_name, pr.request_number
            FROM supply_orders so
            LEFT JOIN suppliers s ON so.supplier_id = s.id
            LEFT JOIN purchase_requests pr ON so.request_id = pr.id
            WHERE so.status = ?
        """, (status,))
        return self.cursor.fetchall()

    def get_order_details(self, order_id):
        """الحصول على تفاصيل أمر التوريد مع الأصناف"""
        self.cursor.execute("""
            SELECT so.*, s.name_ar as supplier_name, pr.request_number
            FROM supply_orders so
            LEFT JOIN suppliers s ON so.supplier_id = s.id
            LEFT JOIN purchase_requests pr ON so.request_id = pr.id
            WHERE so.id = ?
        """, (order_id,))
        order = self.cursor.fetchone()

        self.cursor.execute("""
            SELECT soi.*, i.item_name_ar, i.item_code
            FROM supply_order_items soi
            LEFT JOIN items i ON soi.item_id = i.id
            WHERE soi.order_id = ?
        """, (order_id,))
        items = self.cursor.fetchall()

        return order, items

    def close(self):
        """إغلاق الاتصال"""
        if self.conn:
            self.conn.close()

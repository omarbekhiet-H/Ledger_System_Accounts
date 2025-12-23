import os
import sys
import sqlite3
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.db_connection import get_inventory_db_connection


class InventoryInvoice:
    def __init__(self):
        self.conn = get_inventory_db_connection()
        if self.conn is None:
            raise Exception("فشل الاتصال بقاعدة بيانات المخزون")
        self.cursor = self.conn.cursor()

    def create_inventory_invoice(self, addition_id, supplier_id, notes=None):
        """إنشاء فاتورة مخزنية جديدة"""
        try:
            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            invoice_date = datetime.now().strftime('%Y-%m-%d')
            total_amount = self.calculate_total_amount(addition_id)

            self.cursor.execute("""
                INSERT INTO inventory_invoices 
                (invoice_number, invoice_date, addition_id, supplier_id, notes, total_amount, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """, (invoice_number, invoice_date, addition_id, supplier_id, notes, total_amount))

            invoice_id = self.cursor.lastrowid
            self.conn.commit()
            return invoice_id
        except Exception as e:
            self.conn.rollback()
            raise e

    def calculate_total_amount(self, addition_id):
        """حساب المبلغ الإجمالي للفاتورة"""
        try:
            self.cursor.execute("""
                SELECT SUM(ai.quantity * soi.price)
                FROM addition_items ai
                JOIN addition_permits ap ON ai.permit_id = ap.id
                JOIN receipt_permits rp ON ap.receipt_id = rp.id
                JOIN supply_orders so ON rp.order_id = so.id
                JOIN supply_order_items soi ON so.id = soi.order_id AND soi.item_id = ai.item_id
                WHERE ai.permit_id = ?
            """, (addition_id,))
            result = self.cursor.fetchone()
            return result[0] if result and result[0] else 0
        except Exception as e:
            logging.error(f"خطأ في حساب المبلغ الإجمالي: {e}")
            return 0

    def copy_addition_items_to_invoice(self, addition_id, invoice_id):
        """نسخ الأصناف من إذن الإضافة إلى الفاتورة"""
        try:
            self.cursor.execute("""
                SELECT ai.item_id, ai.quantity, ai.unit_id
                FROM addition_items ai
                WHERE ai.permit_id = ?
            """, (addition_id,))
            items = self.cursor.fetchall()

            for item_id, quantity, unit_id in items:
                self.cursor.execute("""
                    SELECT soi.price 
                    FROM addition_permits ap
                    JOIN receipt_permits rp ON ap.receipt_id = rp.id
                    JOIN supply_orders so ON rp.order_id = so.id
                    JOIN supply_order_items soi ON so.id = soi.order_id AND soi.item_id = ?
                    WHERE ap.id = ?
                """, (item_id, addition_id))

                price_result = self.cursor.fetchone()
                unit_price = price_result[0] if price_result else 0
                total_price = quantity * unit_price

                self.cursor.execute("""
                    INSERT INTO invoice_items 
                    (invoice_id, item_id, quantity, unit_id, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (invoice_id, item_id, quantity, unit_id, unit_price, total_price))

            self.conn.commit()
            logging.info(f"تم نسخ {len(items)} صنف إلى الفاتورة المخزنية")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"خطأ في نسخ الأصناف: {e}")
            raise e

    def complete_invoice(self, invoice_id):
        """إكمال الفاتورة"""
        try:
            self.cursor.execute("""
                UPDATE inventory_invoices 
                SET status = 'completed'
                WHERE id = ?
            """, (invoice_id,))
            self.conn.commit()
            logging.info(f"تم إكمال الفاتورة المخزنية رقم: {invoice_id}")
            return True
        except Exception as e:
            self.conn.rollback()
            logging.error(f"خطأ في إكمال الفاتورة: {e}")
            raise e

    def get_invoice_details(self, invoice_id):
        """الحصول على تفاصيل الفاتورة"""
        try:
            self.cursor.execute("""
                SELECT ii.*, s.name_ar as supplier_name
                FROM inventory_invoices ii
                LEFT JOIN suppliers s ON ii.supplier_id = s.id
                WHERE ii.id = ?
            """, (invoice_id,))
            invoice = self.cursor.fetchone()

            self.cursor.execute("""
                SELECT ii.*, i.item_name_ar, i.item_code, u.name_ar as unit_name
                FROM invoice_items ii
                LEFT JOIN items i ON ii.item_id = i.id
                LEFT JOIN units u ON ii.unit_id = u.id
                WHERE ii.invoice_id = ?
            """, (invoice_id,))
            items = self.cursor.fetchall()

            return invoice, items
        except Exception as e:
            logging.error(f"خطأ في الحصول على تفاصيل الفاتورة: {e}")
        return None, None

    def close(self):
        if self.conn:
            self.conn.close()
            logging.info("تم إغلاق الاتصال بقاعدة البيانات")
    
    def create_invoice(self, addition_id, supplier_id, invoice_number, invoice_date, invoice_type, total_amount, notes):
        try:
            self.cursor.execute("""
                INSERT INTO inventory_invoices (
                    addition_id,
                    supplier_id,
                    invoice_number,
                    invoice_date,
                    invoice_type,
                    total_amount,
                    notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                addition_id,
                supplier_id,
                invoice_number,
                invoice_date,
                invoice_type,
                total_amount,
                notes
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"خطأ أثناء إنشاء الفاتورة: {e}")
        self.conn.rollback()
        return None
        
    def add_invoice_item(self, invoice_id, item_id, quantity, unit_id, unit_price, discount_percent, discount_amount, bonus, tax_percent, total_price):
        try:
            self.cursor.execute("""
                INSERT INTO invoice_items (
                    invoice_id, item_id, quantity, unit_id, unit_price,
                    discount_percent, discount_amount, bonus, tax_percent, total_price
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id, item_id, quantity, unit_id, unit_price,
                discount_percent, discount_amount, bonus, tax_percent, total_price
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"خطأ أثناء إضافة الصنف: {e}")
        return False
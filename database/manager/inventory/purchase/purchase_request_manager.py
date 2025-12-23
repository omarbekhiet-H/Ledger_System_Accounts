import os
import sys
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.db_connection import get_inventory_db_connection

class PurchaseRequest:
    """مدير طلبات الشراء للتعامل مع قاعدة البيانات"""
    
    def __init__(self):
        self.conn = get_inventory_db_connection()
        if self.conn is None:
            raise Exception("فشل الاتصال بقاعدة بيانات المخزون")
        self.cursor = self.conn.cursor()

    def create_request(self, requester_id, department_id, notes=None):
        """إنشاء طلب شراء جديد"""
        try:
            request_number = f"PR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            request_date = datetime.now().strftime('%Y-%m-%d')
            
            self.cursor.execute("""
                INSERT INTO purchase_requests 
                (request_number, request_date, requester_id, department_id, notes, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            """, (request_number, request_date, requester_id, department_id, notes))
            
            request_id = self.cursor.lastrowid
            self.conn.commit()
            return request_id
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_request_item(self, request_id, item_id, quantity, price):
        """إضافة صنف إلى طلب الشراء"""
        try:
            total = quantity * price
            self.cursor.execute("""
                INSERT INTO purchase_request_items 
                (request_id, item_id, quantity, price, total)
                VALUES (?, ?, ?, ?, ?)
            """, (request_id, item_id, quantity, price, total))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def update_status(self, request_id, status):
        """تحديث حالة طلب الشراء"""
        try:
            self.cursor.execute("""
                UPDATE purchase_requests 
                SET status = ?
                WHERE id = ?
            """, (status, request_id))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_request_details(self, request_id):
        """الحصول على تفاصيل طلب الشراء"""
        try:
            self.cursor.execute("""
                SELECT pr.*, r.name_ar as requester_name, d.name_ar as department_name
                FROM purchase_requests pr
                LEFT JOIN requesters r ON pr.requester_id = r.id
                LEFT JOIN departments d ON pr.department_id = d.id
                WHERE pr.id = ?
            """, (request_id,))
            request = self.cursor.fetchone()

            self.cursor.execute("""
                SELECT pri.*, i.item_name_ar, i.item_code
                FROM purchase_request_items pri
                LEFT JOIN items i ON pri.item_id = i.id
                WHERE pri.request_id = ?
            """, (request_id,))
            items = self.cursor.fetchall()

            return request, items
        except Exception as e:
            raise e

    def get_requests_by_status(self, status):
        """الحصول على طلبات الشراء حسب الحالة"""
        try:
            self.cursor.execute("""
                SELECT pr.*, r.name_ar as requester_name, d.name_ar as department_name
                FROM purchase_requests pr
                LEFT JOIN requesters r ON pr.requester_id = r.id
                LEFT JOIN departments d ON pr.department_id = d.id
                WHERE pr.status = ?
            """, (status,))
            return self.cursor.fetchall()
        except Exception as e:
            raise e

    def close(self):
        """إغلاق الاتصال"""
        if self.conn:
            self.conn.close()
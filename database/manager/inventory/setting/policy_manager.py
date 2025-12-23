import os
import sqlite3

class DBManager:
    def __init__(self, db_path=None):
        # تحديد مسار قاعدة البيانات
        if db_path is None:
            # الحصول على المسار الحالي للبرنامج
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # الانتقال إلى مجلد المشروع الرئيسي (4 مستويات للأعلى)
            project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
            # تحديد مسار قاعدة البيانات في مجلد schema
            db_path = os.path.join(project_root, 'database', 'schema', 'inventory.db')
        
        # إنشاء مجلد قاعدة البيانات إذا لم يكن موجوداً
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # الاتصال بقاعدة البيانات
        self.conn = sqlite3.connect(db_path)
        self.create_tables()


    def __init__(self, db_path="inventory.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def get_all_policies(self):
        query = "SELECT * FROM policy_master WHERE is_active = 1 ORDER BY display_order"
        return self.conn.execute(query).fetchall()

    def get_policy_details(self, policy_id):
        query = "SELECT * FROM policy_details WHERE policy_id = ? AND is_active = 1"
        return self.conn.execute(query, (policy_id,)).fetchall()
    def update_policy_detail(self, detail_id, new_value):
        query = "UPDATE policy_details SET setting_value = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        self.conn.execute(query, (new_value, detail_id))
        self.conn.commit()

    def delete_policy(self, policy_id):
        query = "DELETE FROM policy_master WHERE id = ?"
        self.conn.execute(query, (policy_id,))
        self.conn.commit()
    def get_all_policies(self):
        query = "SELECT * FROM policy_master WHERE is_active = 1 ORDER BY display_order"
        return self.conn.execute(query).fetchall()
    
    def get_policies_by_category(self, category):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, key, name, category, description, editable, requires_approval,
                   default_scope, version
            FROM policy_master
            WHERE category = ?
        """, (category,))
        rows = cursor.fetchall()
        policies = []
        for row in rows:
            policies.append({
                "id": row[0],
                "key": row[1],
                "name": row[2],
                "category": row[3],
                "description": row[4],
                "editable": row[5],
                "requires_approval": row[6],
                "default_scope": row[7],
                "version": row[8]
            })
        return policies
    def get_policies_by_category(self, category):
        """جلب جميع السياسات حسب التصنيف."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, key, name, category, description, editable, requires_approval,
                   default_scope, version
            FROM policy_master
            WHERE category = ?
        """, (category,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_inventory_account_types(self):
        """جلب أنواع حساب المخزون من جدول خاص أو إرجاع قائمة ثابتة إذا لم يوجد."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM inventory_account_types")
            rows = cursor.fetchall()
            if rows:
                return [row["name"] for row in rows]
        except sqlite3.OperationalError:
            # إذا لم يوجد جدول، نرجع قائمة افتراضية
            return ["متوسط التكلفة", "FIFO", "LIFO", "مرجح"]
        return ["متوسط التكلفة", "FIFO", "LIFO", "مرجح"]
    def get_policies_by_category(self, category):
        """جلب جميع السياسات حسب التصنيف"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, key, name, category, description, editable, requires_approval,
                   default_scope, version, updated_at
            FROM policy_master
            WHERE category = ? AND is_active = 1
            ORDER BY name
        """, (category,))
        return [dict(row) for row in cursor.fetchall()]

    def get_policy_details(self, policy_id):
        """جلب جميع الإعدادات التفصيلية لسياسة معينة"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, setting_key, setting_value, data_type
            FROM policy_details
            WHERE policy_id = ? AND is_active = 1
            ORDER BY id
        """, (policy_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_inventory_account_types(self):
        """جلب أنواع حساب المخزون"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name FROM inventory_account_types 
            WHERE is_active = 1
            ORDER BY name
        """)
        return [row["name"] for row in cursor.fetchall()]

    def delete_policy(self, policy_id):
        """حذف سياسة معينة"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE policy_master 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (policy_id,))
        self.conn.commit()
    

    def close(self):
        self.conn.close()

    

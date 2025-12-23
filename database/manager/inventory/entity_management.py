import sqlite3
from datetime import datetime

class EntityManagement:
    def __init__(self, db_path):
        self.db_path = db_path
    
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_entities_table(self):
        """إنشاء جدول الكيانات إذا لم يكن موجوداً"""
        query = """
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name_ar TEXT NOT NULL,
            name_en TEXT,
            entity_type TEXT NOT NULL CHECK(entity_type IN (
                'supplier', 'customer', 'branch', 'department', 
                'location', 'warehouse'
            )),
            parent_id INTEGER,
            contact_person TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            tax_number TEXT,
            is_active INTEGER DEFAULT 1,
            credit_limit DECIMAL(10, 2),
            capacity REAL DEFAULT 0,
            current_capacity REAL DEFAULT 0,
            manager_external_id TEXT,
            external_id TEXT,
            external_system TEXT DEFAULT 'accounting',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES entities(id)
        )
        """
        
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating table: {e}")
            return False
    
    def add_entity(self, entity_data):
        """إضافة كيان جديد"""
        query = """
        INSERT INTO entities (
            code, name_ar, name_en, entity_type, parent_id,
            contact_person, phone, email, address, tax_number,
            is_active, credit_limit, capacity, current_capacity,
            manager_external_id, external_id, external_system
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(query, (
                entity_data['code'],
                entity_data['name_ar'],
                entity_data.get('name_en'),
                entity_data['entity_type'],
                entity_data.get('parent_id'),
                entity_data.get('contact_person'),
                entity_data.get('phone'),
                entity_data.get('email'),
                entity_data.get('address'),
                entity_data.get('tax_number'),
                entity_data.get('is_active', 1),
                entity_data.get('credit_limit', 0),
                entity_data.get('capacity', 0),
                entity_data.get('current_capacity', 0),
                entity_data.get('manager_external_id'),
                entity_data.get('external_id'),
                entity_data.get('external_system', 'accounting')
            ))
            conn.commit()
            entity_id = cursor.lastrowid
            conn.close()
            return entity_id
        except sqlite3.IntegrityError:
            raise Exception("الكود موجود مسبقاً")
        except Exception as e:
            raise Exception(f"خطأ في الإضافة: {str(e)}")
    
    def update_entity(self, entity_id, entity_data):
        """تحديث بيانات كيان"""
        query = """
        UPDATE entities SET
            code = ?, name_ar = ?, name_en = ?, entity_type = ?, parent_id = ?,
            contact_person = ?, phone = ?, email = ?, address = ?, tax_number = ?,
            is_active = ?, credit_limit = ?, capacity = ?, current_capacity = ?,
            manager_external_id = ?, external_id = ?, external_system = ?,
            updated_at = ?
        WHERE id = ?
        """
        
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(query, (
                entity_data['code'],
                entity_data['name_ar'],
                entity_data.get('name_en'),
                entity_data['entity_type'],
                entity_data.get('parent_id'),
                entity_data.get('contact_person'),
                entity_data.get('phone'),
                entity_data.get('email'),
                entity_data.get('address'),
                entity_data.get('tax_number'),
                entity_data.get('is_active', 1),
                entity_data.get('credit_limit', 0),
                entity_data.get('capacity', 0),
                entity_data.get('current_capacity', 0),
                entity_data.get('manager_external_id'),
                entity_data.get('external_id'),
                entity_data.get('external_system', 'accounting'),
                datetime.now(),
                entity_id
            ))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            raise Exception("الكود موجود مسبقاً")
        except Exception as e:
            raise Exception(f"خطأ في التحديث: {str(e)}")
    
    def delete_entity(self, entity_id):
        """حذف كيان"""
        query = "DELETE FROM entities WHERE id = ?"
        
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(query, (entity_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            raise Exception(f"خطأ في الحذف: {str(e)}")
    
    def toggle_entity_status(self, entity_id):
        """تبديل حالة الكيان (تفعيل/تعطيل)"""
        query = "UPDATE entities SET is_active = NOT is_active, updated_at = ? WHERE id = ?"
        
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(query, (datetime.now(), entity_id))
            conn.commit()
            
            # الحصول على الحالة الجديدة
            cursor.execute("SELECT is_active FROM entities WHERE id = ?", (entity_id,))
            new_status = cursor.fetchone()['is_active']
            conn.close()
            
            return new_status
        except Exception as e:
            raise Exception(f"خطأ في تغيير الحالة: {str(e)}")
    
    def get_entity(self, entity_id):
        """الحصول على بيانات كيان محدد"""
        query = "SELECT * FROM entities WHERE id = ?"
        
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(query, (entity_id,))
            entity = cursor.fetchone()
            conn.close()
            
            if entity:
                return dict(entity)
            return None
        except Exception as e:
            raise Exception(f"خطأ في استرجاع البيانات: {str(e)}")
    
    def search_entities(self, entity_type=None, search_text="", active_only=True):
        """بحث في الكيانات"""
        query = """
        SELECT * FROM entities 
        WHERE 1=1
        """
        params = []
        
        if entity_type and entity_type != "الكل":
            query += " AND entity_type = ?"
            params.append(entity_type)
        
        if search_text:
            query += " AND (code LIKE ? OR name_ar LIKE ? OR name_en LIKE ?)"
            params.extend([f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"])
        
        if active_only:
            query += " AND is_active = 1"
        
        query += " ORDER BY name_ar"
        
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(query, params)
            entities = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return entities
        except Exception as e:
            raise Exception(f"خطأ في البحث: {str(e)}")
    
    def get_entities_by_type(self, entity_type):
        """الحصول على جميع الكيانات من نوع معين"""
        return self.search_entities(entity_type=entity_type, active_only=False)
    
    def validate_entity_data(self, entity_data, is_update=False):
        """التحقق من صحة بيانات الكيان"""
        errors = []
        
        if not entity_data.get('code'):
            errors.append("الكود مطلوب")
        
        if not entity_data.get('name_ar'):
            errors.append("الاسم العربي مطلوب")
        
        if not entity_data.get('entity_type'):
            errors.append("نوع الكيان مطلوب")
        
        # التحقق من عدم تكرار الكود
        if not is_update:
            try:
                conn = self._connect()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM entities WHERE code = ?", 
                              (entity_data['code'],))
                count = cursor.fetchone()['count']
                conn.close()
                
                if count > 0:
                    errors.append("الكود موجود مسبقاً")
            except:
                pass
        
        return errors

# مثال للاستخدام
if __name__ == "__main__":
    manager = EntityManagement("database/inventory.db")
    manager.create_entities_table()
    
    # إضافة مورد جديد
    supplier_data = {
        'code': 'SUP001',
        'name_ar': 'مورد الاختبار',
        'name_en': 'Test Supplier',
        'entity_type': 'supplier',
        'contact_person': 'أحمد محمد',
        'phone': '0123456789',
        'email': 'test@supplier.com',
        'address': 'القاهرة',
        'credit_limit': 10000.00,
        'is_active': 1
    }
    
    try:
        supplier_id = manager.add_entity(supplier_data)
        print(f"تم إضافة المورد برقم: {supplier_id}")
    except Exception as e:
        print(f"خطأ: {e}")
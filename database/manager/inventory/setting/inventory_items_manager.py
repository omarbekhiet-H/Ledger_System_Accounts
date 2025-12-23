# database/inventory_manager.py

import sqlite3
from database.base_manager import BaseManager
from PyQt5.QtWidgets import QMessageBox
from datetime import datetime

class InventoryManager(BaseManager):
    """يدير عمليات المخزون والأصناف ومجموعاتها"""
    
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func)
    
    def add_item(self, item_data):
        """
        إضافة صنف جديد مع الوحدات المتعددة
        item_data يجب أن يحتوي على:
        - item_code, item_name_ar, item_type, unit_id (الوحدة الأساسية)
        - main_unit_id, medium_unit_id, small_unit_id (الوحدات)
        - main_to_medium_factor, medium_to_small_factor (معاملات التحويل)
        - باقي الحقول الاختيارية
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # التحقق من وجود الوحدات المحددة
            if not self._validate_units(item_data):
                QMessageBox.warning(None, "خطأ", "الوحدات المحددة غير صالحة")
                return False
            
            cursor.execute("""
                INSERT INTO items (
                    item_code, item_name_ar, item_name_en, item_type,
                    unit_id, main_unit_id, medium_unit_id, small_unit_id,
                    main_to_medium_factor, medium_to_small_factor,
                    item_category_id, purchase_price, sale_price,
                    inventory_account_id, cogs_account_id, sales_account_id, is_active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_data['item_code'],
                item_data['item_name_ar'],
                item_data.get('item_name_en'),
                item_data['item_type'],
                item_data['unit_id'],
                item_data.get('main_unit_id'),
                item_data.get('medium_unit_id'),
                item_data.get('small_unit_id'),
                item_data.get('main_to_medium_factor', 1.0),
                item_data.get('medium_to_small_factor', 1.0),
                item_data.get('item_category_id'),
                item_data.get('purchase_price', 0.0),
                item_data.get('sale_price', 0.0),
                item_data.get('inventory_account_id'),
                item_data.get('cogs_account_id'),
                item_data.get('sales_account_id'),
                item_data.get('is_active', 1)
            ))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            QMessageBox.warning(None, "خطأ", "رمز الصنف أو الاسم موجود مسبقاً")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ في إضافة الصنف: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def _validate_units(self, item_data):
        """التحقق من صحة الوحدات المحددة"""
        try:
            # الوحدة الأساسية مطلوبة
            if not item_data.get('unit_id'):
                return False
                
            # إذا حددت وحدة كبرى يجب تحديد معامل التحويل
            if item_data.get('main_unit_id') and not item_data.get('main_to_medium_factor'):
                return False
                
            # إذا حددت وحدة متوسطة يجب تحديد معامل التحويل
            if item_data.get('medium_unit_id') and not item_data.get('medium_to_small_factor'):
                return False
                
            return True
        except:
            return False

    def update_item(self, item_id, item_data):
        """تحديث بيانات الصنف"""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # التحقق من صحة الوحدات
            if not self._validate_units(item_data):
                QMessageBox.warning(None, "خطأ", "الوحدات المحددة غير صالحة")
                return False
            
            cursor.execute("""
                UPDATE items SET
                    item_name_ar = ?,
                    item_name_en = ?,
                    item_type = ?,
                    unit_id = ?,
                    main_unit_id = ?,
                    medium_unit_id = ?,
                    small_unit_id = ?,
                    main_to_medium_factor = ?,
                    medium_to_small_factor = ?,
                    item_category_id = ?,
                    purchase_price = ?,
                    sale_price = ?,
                    inventory_account_id = ?,
                    cogs_account_id = ?,
                    sales_account_id = ?,
                    is_active = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                item_data['item_name_ar'],
                item_data.get('item_name_en'),
                item_data['item_type'],
                item_data['unit_id'],
                item_data.get('main_unit_id'),
                item_data.get('medium_unit_id'),
                item_data.get('small_unit_id'),
                item_data.get('main_to_medium_factor', 1.0),
                item_data.get('medium_to_small_factor', 1.0),
                item_data.get('item_category_id'),
                item_data.get('purchase_price', 0.0),
                item_data.get('sale_price', 0.0),
                item_data.get('inventory_account_id'),
                item_data.get('cogs_account_id'),
                item_data.get('sales_account_id'),
                item_data.get('is_active', 1),
                item_id
            ))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ في تحديث الصنف: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_item_by_id(self, item_id):
        """الحصول على بيانات صنف بواسطة المعرف"""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    i.*,
                    u1.name_ar AS unit_name,
                    u2.name_ar AS main_unit_name,
                    u3.name_ar AS medium_unit_name,
                    u4.name_ar AS small_unit_name,
                    cat.name_ar AS category_name,
                    cat.id AS category_id
                FROM items i
                LEFT JOIN units u1 ON i.unit_id = u1.id
                LEFT JOIN units u2 ON i.main_unit_id = u2.id
                LEFT JOIN units u3 ON i.medium_unit_id = u3.id
                LEFT JOIN units u4 ON i.small_unit_id = u4.id
                LEFT JOIN item_categories cat ON i.item_category_id = cat.id
                WHERE i.id = ?
            """, (item_id,))
            
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting item by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def convert_units(self, item_id, from_unit_type, to_unit_type, quantity):
        """
        تحويل الكمية بين الوحدات المختلفة للصنف
        from_unit_type: 'main', 'medium', 'small', 'base'
        to_unit_type: 'main', 'medium', 'small', 'base'
        """
        item = self.get_item_by_id(item_id)
        if not item:
            return None
            
        # تحويل الكمية إلى الوحدة الأساسية أولاً
        if from_unit_type == 'main':
            if not item['main_unit_id']:
                return None
            base_quantity = quantity * item['main_to_medium_factor'] * item['medium_to_small_factor']
        elif from_unit_type == 'medium':
            if not item['medium_unit_id']:
                return None
            base_quantity = quantity * item['medium_to_small_factor']
        elif from_unit_type == 'small':
            if not item['small_unit_id']:
                return None
            base_quantity = quantity
        else:  # 'base'
            base_quantity = quantity
            
        # التحويل من الوحدة الأساسية إلى الوحدة المطلوبة
        if to_unit_type == 'main':
            if not item['main_unit_id']:
                return None
            return base_quantity / (item['main_to_medium_factor'] * item['medium_to_small_factor'])
        elif to_unit_type == 'medium':
            if not item['medium_unit_id']:
                return None
            return base_quantity / item['medium_to_small_factor']
        elif to_unit_type == 'small':
            if not item['small_unit_id']:
                return None
            return base_quantity
        else:  # 'base'
            return base_quantity

    def get_all_items(self, category_id=None, include_subcategories=True):
        """الحصول على جميع الأصناف مع معلومات الوحدات"""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    i.*,
                    u1.name_ar AS unit_name,
                    u2.name_ar AS main_unit_name,
                    u3.name_ar AS medium_unit_name,
                    u4.name_ar AS small_unit_name,
                    cat.name_ar AS category_name
                FROM items i
                LEFT JOIN units u1 ON i.unit_id = u1.id
                LEFT JOIN units u2 ON i.main_unit_id = u2.id
                LEFT JOIN units u3 ON i.medium_unit_id = u3.id
                LEFT JOIN units u4 ON i.small_unit_id = u4.id
                LEFT JOIN item_categories cat ON i.item_category_id = cat.id
            """
            
            params = []
            
            if category_id is not None:
                if include_subcategories:
                    category_ids = [category_id]
                    subcategories = self._get_all_subcategories(category_id)
                    category_ids.extend([c['id'] for c in subcategories])
                    query += " WHERE i.item_category_id IN ({})".format(','.join(['?']*len(category_ids)))
                    params.extend(category_ids)
                else:
                    query += " WHERE i.item_category_id = ?"
                    params.append(category_id)
            
            query += " ORDER BY i.item_name_ar"
            
            cursor.execute(query, params)
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ في جلب الأصناف: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def add_stock_transaction(self, transaction_data):
        """
        إضافة حركة مخزون مع التحقق من الوحدات
        transaction_data يجب أن يحتوي على:
        - transaction_number, transaction_date, item_id, warehouse_id
        - transaction_type ('In' أو 'Out'), quantity, unit_type
        - unit_cost, unit_sale_price (اختياري), description (اختياري)
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            item = self.get_item_by_id(transaction_data['item_id'])
            if not item:
                QMessageBox.warning(None, "خطأ", "الصنف غير موجود")
                return False
                
            # تحويل الكمية إلى الوحدة الأساسية
            quantity_in_base = self.convert_units(
                transaction_data['item_id'],
                transaction_data['unit_type'],
                'base',
                transaction_data['quantity']
            )
            
            if quantity_in_base is None:
                QMessageBox.warning(None, "خطأ", "نوع الوحدة المحدد غير صالح لهذا الصنف")
                return False
                
            cursor.execute("""
                INSERT INTO stock_transactions (
                    transaction_number, transaction_date, item_id, warehouse_id,
                    transaction_type, quantity, unit_cost, unit_sale_price, description
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction_data['transaction_number'],
                transaction_data['transaction_date'],
                transaction_data['item_id'],
                transaction_data['warehouse_id'],
                transaction_data['transaction_type'],
                quantity_in_base,  # تخزين الكمية بالوحدة الأساسية
                transaction_data.get('unit_cost'),
                transaction_data.get('unit_sale_price'),
                transaction_data.get('description')
            ))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ في إضافة حركة المخزون: {e}")
            return False
        finally:
            if conn:
                conn.close()

    # ========== إدارة مجموعات الأصناف ==========
    
    def add_item_category(self, category_data):
        """إضافة مجموعة أصناف جديدة"""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO item_categories (
                    code, name_ar, name_en, parent_id, description, is_active
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                category_data['code'],
                category_data['name_ar'],
                category_data.get('name_en'),
                category_data.get('parent_id'),
                category_data.get('description'),
                category_data.get('is_active', 1)
            ))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            QMessageBox.warning(None, "خطأ", "رمز المجموعة أو الاسم موجود مسبقاً")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ في إضافة مجموعة الأصناف: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def update_item_category(self, category_id, category_data):
        """تحديث بيانات مجموعة الأصناف"""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE item_categories SET
                    name_ar = ?,
                    name_en = ?,
                    parent_id = ?,
                    description = ?,
                    is_active = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                category_data['name_ar'],
                category_data.get('name_en'),
                category_data.get('parent_id'),
                category_data.get('description'),
                category_data.get('is_active', 1),
                category_id
            ))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            QMessageBox.warning(None, "خطأ", "رمز المجموعة أو الاسم موجود مسبقاً")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ في تحديث مجموعة الأصناف: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_item_category_by_id(self, category_id):
        """الحصول على بيانات مجموعة أصناف بواسطة المعرف"""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    c.*,
                    p.name_ar AS parent_name,
                    p.code AS parent_code
                FROM item_categories c
                LEFT JOIN item_categories p ON c.parent_id = p.id
                WHERE c.id = ?
            """, (category_id,))
            
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        except sqlite3.Error as e:
            print(f"Error getting category by ID: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_all_item_categories(self, include_inactive=False):
        """الحصول على جميع مجموعات الأصناف مع معلومات المجموعات الأم"""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    c.*,
                    p.name_ar AS parent_name,
                    p.code AS parent_code
                FROM item_categories c
                LEFT JOIN item_categories p ON c.parent_id = p.id
            """
            
            if not include_inactive:
                query += " WHERE c.is_active = 1"
                
            query += " ORDER BY c.name_ar"
            
            cursor.execute(query)
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ في جلب مجموعات الأصناف: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_categories_tree(self, parent_id=None):
        """الحصول على هيكل شجري لمجموعات الأصناف"""
        categories = self.get_all_item_categories(include_inactive=True)
        tree = []
        
        for category in categories:
            if category['parent_id'] == parent_id:
                children = self.get_categories_tree(category['id'])
                if children:
                    category['children'] = children
                tree.append(category)
                
        return tree

    def delete_item_category(self, category_id):
        """حذف مجموعة أصناف (إذا لم يكن لها أصناف تابعة)"""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            
            # التحقق من وجود أصناف تابعة للمجموعة
            cursor.execute("SELECT COUNT(*) FROM items WHERE item_category_id = ?", (category_id,))
            item_count = cursor.fetchone()[0]
            
            if item_count > 0:
                QMessageBox.warning(None, "خطأ", "لا يمكن حذف المجموعة لأنها تحتوي على أصناف")
                return False
                
            # التحقق من وجود مجموعات فرعية
            cursor.execute("SELECT COUNT(*) FROM item_categories WHERE parent_id = ?", (category_id,))
            child_count = cursor.fetchone()[0]
            
            if child_count > 0:
                QMessageBox.warning(None, "خطأ", "لا يمكن حذف المجموعة لأنها تحتوي على مجموعات فرعية")
                return False
                
            # حذف المجموعة
            cursor.execute("DELETE FROM item_categories WHERE id = ?", (category_id,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ في حذف مجموعة الأصناف: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_items_by_category(self, category_id, include_subcategories=True):
        """الحصول على الأصناف حسب المجموعة (مع أو بدون المجموعات الفرعية)"""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            
            if include_subcategories:
                # الحصول على جميع المعرفات للمجموعات الفرعية
                category_ids = [category_id]
                subcategories = self._get_all_subcategories(category_id)
                category_ids.extend([c['id'] for c in subcategories])
                
                query = """
                    SELECT 
                        i.*,
                        u1.name_ar AS unit_name,
                        cat.name_ar AS category_name
                    FROM items i
                    LEFT JOIN units u1 ON i.unit_id = u1.id
                    LEFT JOIN item_categories cat ON i.item_category_id = cat.id
                    WHERE i.item_category_id IN ({})
                    ORDER BY i.item_name_ar
                """.format(','.join(['?'] * len(category_ids)))
                
                cursor.execute(query, category_ids)
            else:
                cursor.execute("""
                    SELECT 
                        i.*,
                        u1.name_ar AS unit_name,
                        cat.name_ar AS category_name
                    FROM items i
                    LEFT JOIN units u1 ON i.unit_id = u1.id
                    LEFT JOIN item_categories cat ON i.item_category_id = cat.id
                    WHERE i.item_category_id = ?
                    ORDER BY i.item_name_ar
                """, (category_id,))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ", f"خطأ في جلب الأصناف حسب المجموعة: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def _get_all_subcategories(self, parent_id):
        """دالة مساعدة للحصول على جميع المجموعات الفرعية"""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            
            cursor.execute("""
                WITH RECURSIVE subcategories(id) AS (
                    SELECT id FROM item_categories WHERE parent_id = ?
                    UNION ALL
                    SELECT c.id FROM item_categories c
                    JOIN subcategories s ON c.parent_id = s.id
                )
                SELECT * FROM item_categories WHERE id IN subcategories
            """, (parent_id,))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error getting subcategories: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_category_full_path(self, category_id):
        """الحصول على المسار الكامل للمجموعة (من الجذر إلى المجموعة الحالية)"""
        path = []
        current_id = category_id
        
        while current_id is not None:
            category = self.get_item_category_by_id(current_id)
            if not category:
                break
            path.insert(0, f"{category['name_ar']} ({category['code']})")
            current_id = category['parent_id']
        
        return ' / '.join(path) if path else ""

    def get_category_statistics(self, category_id):
        """الحصول على إحصائيات المجموعة (عدد الأصناف، القيمة الإجمالية)"""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return {}
            cursor = conn.cursor()
            
            # الحصول على جميع الأصناف في المجموعة والمجموعات الفرعية
            category_ids = [category_id]
            subcategories = self._get_all_subcategories(category_id)
            category_ids.extend([c['id'] for c in subcategories])
            
            # حساب عدد الأصناف
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM items 
                WHERE item_category_id IN ({','.join(['?']*len(category_ids))})
            """, category_ids)
            items_count = cursor.fetchone()[0]
            
            # حساب القيمة الإجمالية للمخزون
            cursor.execute(f"""
                SELECT SUM(i.purchase_price * COALESCE(inv.quantity, 0))
                FROM items i
                LEFT JOIN inventory inv ON i.id = inv.item_id
                WHERE i.item_category_id IN ({','.join(['?']*len(category_ids))})
            """, category_ids)
            total_value = cursor.fetchone()[0] or 0
            
            return {
                'items_count': items_count,
                'total_value': total_value,
                'subcategories_count': len(subcategories)
            }
        except sqlite3.Error as e:
            print(f"Error getting category statistics: {e}")
            return {}
        finally:
            if conn:
                conn.close()

    def validate_category_hierarchy(self, category_id, new_parent_id):
        """التحقق من عدم وجود تكرار دوري في التصنيفات"""
        if category_id == new_parent_id:
            return False
            
        current = new_parent_id
        while current is not None:
            if current == category_id:
                return False
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT parent_id FROM item_categories WHERE id = ?", (current,))
            current = cursor.fetchone()[0] if cursor.fetchone() else None
            conn.close()
        return True
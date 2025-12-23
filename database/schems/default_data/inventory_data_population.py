import sqlite3
import os
import sys
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.admin.user_manager import UserManager
from database.db_connection import get_inventory_db_connection


def insert_default_data(conn):
    cursor = conn.cursor()
    
    # 1. المواقع
    store_locations  = [
        ('LOC1', 'الموقع الرئيسي', 'Main Location', 'المقر الرئيسي للشركة', 1),
        ('LOC2', 'فرع الرياض', 'Riyadh Branch', 'فرع منطقة الرياض', 1),
        ('LOC3', 'فرع جدة', 'Jeddah Branch', 'فرع منطقة جدة', 1)
    ]
    cursor.executemany("""
        INSERT INTO store_locations  (code, location_name_ar, location_name_en, description, is_active)
        VALUES (?, ?, ?, ?, ?)
    """, store_locations )
    
    # 2. الفروع
    branches = [
        ('BR1', 'الفرع الرئيسي', 'Main Branch', 1, 'الفرع الرئيسي بالموقع الرئيسي', 1),
        ('BR2', 'فرع الرياض الشمالي', 'Riyadh North Branch', 2, 'فرع شمال الرياض', 1),
        ('BR3', 'فرع جدة الغربي', 'Jeddah West Branch', 3, 'فرع غرب جدة', 1)
    ]
    cursor.executemany("""
        INSERT INTO branches (code, name_ar, name_en, location_id, description, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    """, branches)
    
    # 3. المستودعات
    warehouses = [
        ('WH1', 'المستودع الرئيسي', 'Main Warehouse', 1, 1, 'المستودع الرئيسي بالفرع الرئيسي', 1, 10000.0, 0.0, 'user123', 'الرياض - حي العليا', '0501234567'),
        ('WH2', 'مستودع الرياض 1', 'Riyadh Warehouse 1', 2, 2, 'المستودع الأول بفرع الرياض', 1, 5000.0, 0.0, 'user456', 'الرياض - حي النخيل', '0501111111'),
        ('WH3', 'مستودع جدة 1', 'Jeddah Warehouse 1', 3, 3, 'المستودع الأول بفرع جدة', 1, 8000.0, 0.0, 'user789', 'جدة - حي الصفا', '0502222222')
    ]
    cursor.executemany("""
        INSERT INTO warehouses (code, name_ar, name_en, branch_id, location_id, description, is_active, capacity, current_capacity, manager_external_id, address, contact_phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, warehouses)
    
    # 4. الوحدات
    units = [
        ('UNIT1', 'قطعة', 'Piece', 1),
        ('UNIT2', 'كيلوغرام', 'Kilogram', 1),
        ('UNIT3', 'لتر', 'Liter', 1),
        ('UNIT4', 'علبة', 'Box', 1),
        ('UNIT5', 'كرتون', 'Carton', 1)
    ]
    cursor.executemany("""
        INSERT INTO units (code, name_ar, name_en, is_active)
        VALUES (?, ?, ?, ?)
    """, units)
    
    # 5. الأقسام
    departments = [
        ('DEPT1', 'المشتريات', 'Purchasing', 1, 'acc_dept1', 'accounting'),
        ('DEPT2', 'المبيعات', 'Sales', 1, 'acc_dept2', 'accounting'),
        ('DEPT3', 'المخازن', 'Warehouse', 1, 'acc_dept3', 'accounting'),
        ('DEPT4', 'المالية', 'Finance', 1, 'acc_dept4', 'accounting'),
        ('DEPT5', 'التسويق', 'Marketing', 1, 'acc_dept5', 'accounting')
    ]
    cursor.executemany("""
        INSERT INTO departments (code, name_ar, name_en, is_active, external_department_id, external_system)
        VALUES (?, ?, ?, ?, ?, ?)
    """, departments)
    
    # 6. فئات الأصناف
    item_categories = [
        ('CAT1', 'مواد خام', 'Raw Materials', None, 'المواد الخام الأساسية', 1),
        ('CAT2', 'منتجات نهائية', 'Finished Products', None, 'المنتجات النهائية للبيع', 1),
        ('CAT3', 'مواد تغليف', 'Packaging', None, 'مواد التغليف والتعبئة', 1),
        ('CAT1-1', 'مواد خام غذائية', 'Food Raw Materials', 1, 'المواد الخام الغذائية', 1),
        ('CAT1-2', 'مواد خام كيميائية', 'Chemical Raw Materials', 1, 'المواد الخام الكيميائية', 1)
    ]
    cursor.executemany("""
        INSERT INTO item_categories (code, name_ar, name_en, parent_id, description, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    """, item_categories)
    
    # 7. مجموعات الأصناف
    item_groups = [
        ('GRP1', 'مجموعة المواد الغذائية', 'Food Materials Group', 4, 'مجموعة المواد الغذائية الخام', 1),
        ('GRP2', 'مجموعة المنظفات', 'Detergents Group', 5, 'مجموعة المواد الكيميائية للمنظفات', 1),
        ('GRP3', 'مجموعة المشروبات', 'Beverages Group', 2, 'مجموعة المشروبات الجاهزة', 1)
    ]
    cursor.executemany("""
        INSERT INTO item_groups (code, name_ar, name_en, category_id, description, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    """, item_groups)
    
    suppliers = [
        ('SUP001', 'مورد المواد الغذائية', 'Food Supplier', '123456789', 'أحمد محمد', '0501234567', 'supplier1@example.com', 
        'الرياض - حي العليا', 'السعودية', 'الرياض', '12345', 'www.foodsupplier.com', 'Food', 'net_30', 'تحويل بنكي', 
        100000.0, 4, 'ar', '2022-01-01', '2024-12-31', 1, 'email',
        'مورد رئيسي للمواد الغذائية', 1, 'acc_supplier1', 'accounting'),

        ('SUP002', 'مورد المواد الكيميائية', 'Chemical Supplier', '987654321', 'خالد علي', '0507654321', 'supplier2@example.com', 
        'جدة - حي الصفا', 'السعودية', 'جدة', '54321', 'www.chemsupplier.com', 'Chemical', 'net_15', 'شيك', 
        50000.0, 3, 'ar', '2022-01-01', '2024-12-31', 1, 'phone',
        'مورد للمواد الكيميائية', 1, 'acc_supplier2', 'accounting')
    ]

    cursor.executemany("""
        INSERT INTO suppliers (
            supplier_code, name_ar, name_en, tax_number, contact_person, phone, email, 
            address, country, city, postal_code, website, supply_category, payment_terms, 
            payment_method, credit_limit, rating, language, contract_start_date, contract_end_date, 
            is_verified, preferred_contact_method, notes, is_active,
            external_account_id, external_system
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, suppliers)

    # 9. الأصناف
    items = [
        ('ITEM1', 'سكر', 'Sugar', 'سكر أبيض ناعم', 'Inventory', 4, 1, 2, 0, 100.0, 1000.0, 200.0, 5.0, 7.0, None, None, None, None, None, 1, 1.0, '1kg', 365, 'Food', 'جاف وبارد', 'مصنع السكر', 1, 7, 'acc_item1', 'accounting'),
        ('ITEM2', 'زيت نباتي', 'Vegetable Oil', 'زيت نباتي للطهي', 'Inventory', 4, 2, 3, 1, 50.0, 500.0, 100.0, 15.0, 20.0, None, None, None, '2024-12-31', None, 1, 0.9, '1L', 180, 'Food', 'بارد وجاف', 'مصنع الزيوت', 1, 14, 'acc_item2', 'accounting'),
        ('ITEM3', 'منظف أرضيات', 'Floor Cleaner', 'منظف أرضيات لجميع الأسطح', 'Inventory', 5, 2, 3, 1, 20.0, 200.0, 50.0, 10.0, 15.0, None, None, None, '2025-06-30', None, 1, 1.2, '1L', 365, 'Chemical', 'درجة حرارة الغرفة', 'مصنع المنظفات', 2, 10, 'acc_item3', 'accounting'),
        ('ITEM4', 'مشروب غازي', 'Soft Drink', 'مشروب غازي 330 مل', 'Inventory', 2, 3, 1, 1, 500.0, 5000.0, 1000.0, 2.0, 3.5, None, None, None, '2024-09-30', None, 1, 0.33, '330ml', 180, 'Beverage', 'بارد', 'مصنع المشروبات', 1, 5, 'acc_item4', 'accounting'),
        ('ITEM5', 'كرتون تغليف', 'Packaging Carton', 'كرتون تغليف مقاس 30×30×30', 'Inventory', 3, 3, 5, 0, 100.0, 1000.0, 200.0, 3.0, 4.0, None, None, None, None, None, 1, 0.5, '30x30x30cm', None, 'Packaging', 'جاف', 'مصنع الكراتين', 2, 3, 'acc_item5', 'accounting')
    ]
    cursor.executemany("""
        INSERT INTO items (
            item_code, item_name_ar, item_name_en, item_description, item_type, 
            item_category_id, item_group_id, base_unit_id, has_expiry_date, min_stock_limit, 
            max_stock_limit, reorder_point, purchase_price, sale_price, 
            inventory_account_id, cogs_account_id, sales_account_id, 
            expiry_date, image_path, is_active, weight, dimensions, shelf_life_days,
            hazard_classification, storage_conditions, manufacturer, supplier_id, lead_time_days,
            external_item_id, external_system
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, items)
    
    # 10. وحدات الأصناف
    item_units_data = [
        (1, 1, 0, 0, 1, 1.0),   # سكر - قطعة (غير رئيسي)
        (1, 2, 1, 0, 0, 1.0),   # سكر - كيلوغرام (رئيسي)
        (2, 3, 1, 0, 0, 1.0),   # زيت - لتر (رئيسي)
        (3, 3, 1, 0, 0, 1.0),   # منظف - لتر (رئيسي)
        (4, 1, 1, 0, 0, 1.0),   # مشروب - قطعة (رئيسي)
        (4, 4, 0, 1, 0, 24.0),  # مشروب - علبة (24 قطعة)
        (4, 5, 0, 0, 1, 12.0),  # مشروب - كرتون (12 علبة)
        (5, 5, 1, 0, 0, 1.0)    # كرتون - كرتون (رئيسي)
    ]
    cursor.executemany("""
        INSERT INTO item_units (item_id, unit_id, is_main, is_medium, is_small, conversion_factor)
        VALUES (?, ?, ?, ?, ?, ?)
    """, item_units_data)
    
    # 11. العملاء
    customers = [
        ('عميل التجزئة', 'محمد سعيد', '0501111111', 'customer1@example.com', 'الرياض - حي النخيل', 1, 'عميل رئيسي', 'www.retailer.com', 'شروط الدفع: 15 يوم', 'السعودية', 'الرياض', '11111', None,  None, None, 50000.0, 4, 'email', 'الرياض - حي النخيل', 'acc_customer1', 'accounting'),
        ('عميل الجملة', 'علي عبدالله', '0502222222', 'customer2@example.com', 'جدة - حي الروضة', 1, 'عميل جملة', 'www.wholesaler.com', 'شروط الدفع: 30 يوم', 'السعودية', 'جدة', '22222', None, None, None, 100000.0, 5, 'phone', 'جدة - حي الروضة', 'acc_customer2', 'accounting')
    ]
    cursor.executemany("""
        INSERT INTO customers (
            name_ar, contact_person, phone, email, address, is_active, notes, website, 
            payment_terms, country, city, postal_code, account_id,
            financial_policy_id, inventory_policy_id, credit_limit, rating, 
            preferred_contact_method, delivery_address, external_account_id, external_system
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, customers)
    
    # 12. سياسات الائتمان
    credit_policies = [
        ('سياسة الموردين الأساسية', 'supplier', 100000.0, 'net_30', 5, 1.5, 1000.0, 60, 1),
        ('سياسة العملاء المميزين', 'customer', 50000.0, '2/10 net_30', 0, 2.0, 500.0, 45, 1),
        ('سياسة العملاء العاديين', 'customer', 20000.0, 'net_15', 0, 3.0, 200.0, 30, 1)
    ]
    cursor.executemany("""
        INSERT INTO credit_policies (
            policy_name, policy_type, credit_limit, payment_terms, grace_period, 
            interest_rate, min_order_value, max_credit_period, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, credit_policies)
    
    # 13. سياسات البونص
    bonus_policies = [
        ('خصم الكمية على المواد الغذائية', 'quantity', 100.0, 10.0, '2023-01-01', '2023-12-31', 1),
        ('خصم النسبة على المنظفات', 'percentage', 50.0, 5.0, '2023-01-01', '2023-12-31', 1),
        ('بونص العروض الخاصة', 'quantity', 10.0, 1.0, '2023-06-01', '2023-06-30', 1)
    ]
    cursor.executemany("""
        INSERT INTO bonus_policies (
            policy_name, bonus_type, min_quantity, bonus_value, applicable_from, 
            applicable_to, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, bonus_policies)
    
    # 14. تفعيل سياسات البونص على الأصناف
    item_bonus_policies = [
        (1, 1, 1),  # صنف السكر عليه سياسة خصم الكمية
        (3, 2, 1),  # صنف المنظف عليه سياسة خصم النسبة
        (4, 3, 1)   # صنف المشروب عليه سياسة العروض الخاصة
    ]
    cursor.executemany("""
        INSERT INTO item_bonus_policies (item_id, bonus_policy_id, is_active)
        VALUES (?, ?, ?)
    """, item_bonus_policies)
    
    # 15. طلبات الشراء
    purchase_requests = [
        ('PR-2023-001', '2023-01-15', 'user123', 1, 'approved', 'طلب مواد خام لشهر يناير', 'user456', '2023-01-16', 'cost_center1'),
        ('PR-2023-002', '2023-01-20', 'user456', 2, 'approved', 'طلب مواد تغليف لشهر يناير', 'user789', '2023-01-21', 'cost_center2'),
        ('PR-2023-003', '2023-02-01', 'user789', 3, 'pending', 'طلب مواد تنظيف لشهر فبراير', None, None, 'cost_center3')
    ]
    cursor.executemany("""
        INSERT INTO purchase_requests (
            request_number, request_date, requester_external_id, department_id, status, notes,
            approved_by_external_id, approved_at, cost_center_external_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, purchase_requests)
    
    # 16. أصناف طلبات الشراء
    purchase_request_items = [
        (1, 1, 500.0, 2, 5.0, 2500.0, 4, 1),
        (1, 2, 200.0, 3, 15.0, 3000.0, 4, 1),
        (2, 5, 300.0, 5, 3.0, 900.0, 3, 1),
        (3, 3, 100.0, 3, 10.0, 1000.0, 5, 0)
    ]
    cursor.executemany("""
        INSERT INTO purchase_request_items (
            request_id, item_id, quantity, unit_id, unit_price, total_price, category_id, is_selected
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, purchase_request_items)
    
    # 17. أوامر التوريد
    supply_orders = [
        ('SO-2023-001', 1, 1, '2023-01-16', '2023-01-25', 'delivered', 9, 'أمر توريد مواد غذائية'),
        ('SO-2023-002', 2, 2, '2023-01-21', '2023-01-30', 'approved', 9, 'أمر توريد مواد تغليف'),
        ('SO-2023-003', 3, 1, '2023-02-02', '2023-02-15', 'pending', 13, 'أمر توريد مواد تنظيف')
    ]
    cursor.executemany("""
        INSERT INTO supply_orders (
            order_number, request_id, supplier_id, order_date, expected_delivery_date, status, delivery_days, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, supply_orders)
    
    # 18. أصناف أوامر التوريد
    supply_order_items = [
        (1, 1, 500.0, 2, 5.0),
        (1, 2, 200.0, 3, 15.0),
        (2, 5, 300.0, 5, 3.0),
        (3, 3, 100.0, 3, 10.0)
    ]
    cursor.executemany("""
        INSERT INTO supply_order_items (
            order_id, item_id, quantity, unit_id, price
        ) VALUES (?, ?, ?, ?, ?)
    """, supply_order_items)
    
    # 19. إذونات الاستلام
    receipt_permits = [
        ('RP-2023-001', '2023-01-25', 1, 1, '2023-01-25', 'completed', 'user123', 'user456'),
        ('RP-2023-002', '2023-01-30', 2, 1, '2023-01-30', 'completed', 'user456', 'user789'),
        ('RP-2023-003', '2023-02-15', 3, 2, None, 'pending', None, None)
    ]
    cursor.executemany("""
        INSERT INTO receipt_permits (
            permit_number, permit_date, supply_order_id, warehouse_id, receipt_date, status,
            received_by_external_id, approved_by_external_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, receipt_permits)
    
    # 20. أصناف إذونات الاستلام
    receipt_items = [
        (1, 1, 500.0, 2, 500.0, 'تم الاستلام بالكامل'),
        (1, 2, 200.0, 3, 200.0, 'تم الاستلام بالكامل'),
        (2, 5, 300.0, 5, 300.0, 'تم الاستلام بالكامل')
    ]
    cursor.executemany("""
        INSERT INTO receipt_items (
            permit_id, item_id, quantity, unit_id, received_quantity, notes
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, receipt_items)
    
    # 21. إذونات الإضافة
    addition_permits = [
        (1, '2023-01-25', 'completed'),
        (2, '2023-01-30', 'completed')
    ]
    cursor.executemany("""
        INSERT INTO addition_permits (
            receipt_id, addition_date, status
        ) VALUES (?, ?, ?)
    """, addition_permits)
    
    # 22. أصناف إذونات الإضافة
    addition_items = [
        (1, 1, 500.0, 2),
        (1, 2, 200.0, 3),
        (2, 5, 300.0, 5)
    ]
    cursor.executemany("""
        INSERT INTO addition_items (
            permit_id, item_id, quantity, unit_id
        ) VALUES (?, ?, ?, ?)
    """, addition_items)
    
    # 23. أوامر الشراء
    purchase_orders = [
        (1, '2023-01-16', '2023-01-25', 'completed', 'user123', 'user456', '2023-01-17'),
        (2, '2023-01-21', '2023-01-30', 'completed', 'user456', 'user789', '2023-01-22'),
        (1, '2023-02-02', '2023-02-15', 'pending', 'user789', None, None)
    ]
    cursor.executemany("""
        INSERT INTO purchase_orders (
            supplier_id, order_date, expected_delivery_date, status,
            created_by_external_id, approved_by_external_id, approved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, purchase_orders)
    
    # 24. فواتير الشراء
    purchase_invoices = [
        (1, 'INV-2023-001', '2023-01-25', 1, 5500.0, None, 'paid', 'net_30', 250.0, '2023-02-24', 2.0),
        (2, 'INV-2023-002', '2023-01-30', 2, 900.0, None, 'paid', 'net_30', 0.0, '2023-03-01', 0.0)
    ]
    cursor.executemany("""
        INSERT INTO purchase_invoices (
            supplier_id, invoice_number, invoice_date, order_id, total_amount, 
            accounting_entry_id, status, payment_terms, discount_amount, due_date, early_payment_discount
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, purchase_invoices)
    
    # 25. أصناف فواتير الشراء
    purchase_invoice_items = [
        (1, 1, 500.0, 2, 5.0, 2500.0, 0, 5.0, None, None, 'cost_acc1', 'inv_acc1'),
        (1, 2, 200.0, 3, 15.0, 3000.0, 0, 15.0, None, None, 'cost_acc2', 'inv_acc2'),
        (2, 5, 300.0, 5, 3.0, 900.0, 0, 3.0, None, None, 'cost_acc3', 'inv_acc3')
    ]
    cursor.executemany("""
        INSERT INTO purchase_invoice_items (
            invoice_id, item_id, quantity, unit_id, unit_price, total_price, 
            is_bonus, original_purchase_price, cost_account_id, inventory_account_id,
            cost_account_external_id, inventory_account_external_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, purchase_invoice_items)
    
    # 26. الفواتير المخزنية
    inventory_invoices = [
        (1, 1, '2023-01-25', 5500.0, 'paid', 'purchase', None),
        (2, 2, '2023-01-30', 900.0, 'paid', 'purchase', None)
    ]
    cursor.executemany("""
        INSERT INTO inventory_invoices (
            addition_id, supplier_id, invoice_date, total_amount, status, invoice_type, accounting_entry_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, inventory_invoices)
    
    # 27. أصناف الفواتير المخزنية
    invoice_items = [
        (1, 1, 500.0, 2, 5.0, 2500.0, 0, 5.0, None, None, None, 'cost_acc1', 'inv_acc1'),
        (1, 2, 200.0, 3, 15.0, 3000.0, 0, 15.0, None, None, None, 'cost_acc2', 'inv_acc2'),
        (2, 5, 300.0, 5, 3.0, 900.0, 0, 3.0, None, None, None, 'cost_acc3', 'inv_acc3')
    ]
    cursor.executemany("""
        INSERT INTO invoice_items (
            invoice_id, item_id, quantity, unit_id, unit_price, total_price, 
            is_bonus, original_purchase_price, base_invoice_id, cost_account_id, inventory_account_id,
            cost_account_external_id, inventory_account_external_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, invoice_items)
    
    # 28. الحركات المخزنية
    stock_transactions = [
        ('TRN-001', '2023-01-25', 1, 1, 'In', 500.0, 5.0, 7.0, '2024-12-31', 'إضافة مخزون سكر', None, 'BATCH001', None, 'PO-001', 1, 'cost_center1', 'user123'),
        ('TRN-002', '2023-01-25', 2, 1, 'In', 200.0, 15.0, 20.0, '2024-12-31', 'إضافة مخزون زيت', None, 'BATCH002', None, 'PO-001', 1, 'cost_center1', 'user123'),
        ('TRN-003', '2023-01-30', 5, 1, 'In', 300.0, 3.0, 4.0, None, 'إضافة مخزون كرتون', None, None, None, 'PO-002', 2, 'cost_center2', 'user456'),
        ('TRN-004', '2023-02-05', 1, 1, 'Out', 50.0, 5.0, 7.0, None, 'صرف مخزون سكر', None, 'BATCH001', None, 'SO-001', 3, 'cost_center3', 'user789'),
        ('TRN-005', '2023-02-05', 2, 1, 'Out', 20.0, 15.0, 20.0, None, 'صرف مخزون زيت', None, 'BATCH002', None, 'SO-001', 3, 'cost_center3', 'user789')
    ]
    cursor.executemany("""
        INSERT INTO stock_transactions (
            transaction_number, transaction_date, item_id, warehouse_id, transaction_type, 
            quantity, unit_cost, unit_sale_price, expiry_date, description, journal_entry_id,
            batch_number, serial_number, reference_document, reference_id, cost_center_external_id, created_by_external_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, stock_transactions)
    
    # 29. حركات الأصناف
    item_movements = [
        (1, 'in', 500.0, 2, '2023-01-25', 'TRN-001', 'إضافة مخزون سكر'),
        (2, 'in', 200.0, 3, '2023-01-25', 'TRN-002', 'إضافة مخزون زيت'),
        (5, 'in', 300.0, 5, '2023-01-30', 'TRN-003', 'إضافة مخزون كرتون'),
        (1, 'out', 50.0, 2, '2023-02-05', 'TRN-004', 'صرف مخزون سكر'),
        (2, 'out', 20.0, 3, '2023-02-05', 'TRN-005', 'صرف مخزون زيت')
    ]
    cursor.executemany("""
        INSERT INTO item_movements (
            item_id, movement_type, quantity, unit_id, date, reference, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, item_movements)
    
    # 30. المعاملات الائتمانية
    credit_transactions = [
        (1, 'supplier', '2023-01-25', 'invoice', 5500.0, 5500.0, 1, 'purchase_invoice', 'فاتورة شراء مواد غذائية'),
        (1, 'supplier', '2023-02-10', 'payment', -5500.0, 0.0, None, 'payment', 'سداد فاتورة شراء'),
        (2, 'supplier', '2023-01-30', 'invoice', 900.0, 900.0, 2, 'purchase_invoice', 'فاتورة شراء مواد تغليف'),
        (1, 'customer', '2023-02-15', 'invoice', 3500.0, 3500.0, None, 'sales_invoice', 'فاتورة مبيعات للعميل')
    ]
    cursor.executemany("""
        INSERT INTO credit_transactions (
            entity_id, entity_type, transaction_date, transaction_type, 
            amount, balance, reference_id, reference_type, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, credit_transactions)
    
    # 31. السياسات الرئيسية
    policy_master = [
        ('inventory_evaluation', 'تقييم المخزون', 'inventory', 'سياسة تقييم المخزون', 1, 1, 0, 'عام', '1.0', 1, 'admin', 'admin'),
        ('purchase_approval', 'موافقة المشتريات', 'purchasing', 'سياسة موافقات المشتريات', 2, 1, 1, 'عام', '1.0', 1, 'admin', 'admin'),
        ('stock_reorder', 'إعادة طلب المخزون', 'inventory', 'سياسة إعادة طلب المخزون', 3, 1, 0, 'عام', '1.0', 1, 'admin', 'admin'),
        ('credit_policy', 'سياسة الائتمان', 'financial', 'سياسات منح الائتمان للموردين والعملاء', 4, 1, 1, 'عام', '1.0', 1, 'admin', 'admin'),
        ('discount_policy', 'سياسة الخصومات', 'sales', 'سياسات الخصومات والعروض (البونص)', 5, 1, 0, 'عام', '1.0', 1, 'admin', 'admin'),
        ('payment_terms', 'شروط الدفع', 'financial', 'سياسات تحديد شروط الدفع', 6, 1, 0, 'عام', '1.0', 1, 'admin', 'admin')
    ]
    cursor.executemany("""
        INSERT INTO policy_master (
            key, name, category, description, display_order, editable, requires_approval, 
            default_scope, version, is_active, created_by, updated_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, policy_master)
    
    # 32. تفاصيل السياسات
    policy_details = [
        (1, 'method', 'FIFO', 'text', 'dropdown', 1, None, 'عام', '2023-01-01', None, 'طريقة تقييم المخزون', 1, 'admin', 'admin'),
        (1, 'frequency', 'monthly', 'text', 'dropdown', 1, None, 'عام', '2023-01-01', None, 'تكرار التقييم', 1, 'admin', 'admin'),
        (2, 'approval_levels', '2', 'number', 'textbox', 1, '>0', 'عام', '2023-01-01', None, 'عدد مستويات الموافقة', 1, 'admin', 'admin'),
        (2, 'threshold', '10000', 'number', 'textbox', 1, '>0', 'عام', '2023-01-01', None, 'حد الموافقة بالريال', 1, 'admin', 'admin'),
        (3, 'reorder_point', '0.8', 'number', 'textbox', 1, '>0', 'عام', '2023-01-01', None, 'نسبة إعادة الطلب من الحد الأقصى', 1, 'admin', 'admin'),
        (4, 'max_credit_limit', '1000000', 'number', 'textbox', 1, '>0', 'عام', '2023-01-01', None, 'الحد الأقصى للائتمان', 1, 'admin', 'admin'),
        (4, 'default_terms', 'net_30', 'text', 'dropdown', 1, None, 'عام', '2023-01-01', None, 'شروط الدفع الافتراضية', 1, 'admin', 'admin'),
        (5, 'max_discount', '20', 'number', 'textbox', 1, '<=100', 'عام', '2023-01-01', None, 'أقصى خصم مسموح به %', 1, 'admin', 'admin'),
        (6, 'early_payment_discount', '2/10 net_30', 'text', 'dropdown', 0, None, 'عام', '2023-01-01', None, 'خصم الدفع المبكر', 1, 'admin', 'admin')
    ]
    cursor.executemany("""
        INSERT INTO policy_details (
            policy_id, setting_key, setting_value, data_type, input_type, is_required, 
            validation_rule, scope, effective_date, expiry_date, notes, is_active, 
            created_by, updated_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, policy_details)
    
    # 33. وصف السياسات
    policy_descriptions = [
        ('inventory_evaluation', 'سياسة تقييم المخزون تحدد طريقة تقييم المخزون وتكرار التقييم'),
        ('purchase_approval', 'سياسة موافقات المشتريات تحدد مستويات الموافقة وحدود الموافقة'),
        ('stock_reorder', 'سياسة إعادة طلب المخزون تحدد متى يتم إعادة طلب المخزون'),
        ('credit_policy', 'سياسة الائتمان تحدد شروط منح الائتمان للموردين والعملاء'),
        ('discount_policy', 'سياسة الخصومات تحدد قواعد منح الخصومات والعروض الخاصة'),
        ('payment_terms', 'سياسة شروط الدفع تحدد خيارات الدفع المتاحة وفترات السماح')
    ]
    cursor.executemany("""
        INSERT INTO policy_descriptions (policy_key, description)
        VALUES (?, ?)
    """, policy_descriptions)
    
    # 34. طلبات الصرف
    issue_requests = [
        ('IR-2023-001', '2023-02-10', 'user123', 3, 'صرف مواد للإنتاج', 'approved', 'user456', '2023-02-11', 'cost_center4'),
        ('IR-2023-002', '2023-02-15', 'user456', 2, 'صرف مواد للتسويق', 'pending', None, None, 'cost_center5')
    ]
    cursor.executemany("""
        INSERT INTO issue_requests (
            request_number, request_date, requester_external_id, department_id, purpose, status,
            approved_by_external_id, approved_at, cost_center_external_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, issue_requests)
    
    # 35. أصناف طلبات الصرف
    issue_request_items = [
        (1, 1, 100.0, 2, 'لإنتاج الدفعة الجديدة', 100.0, 0.0, 5.0, 0.0, 'pending', 'normal', '2023-02-20'),
        (1, 2, 50.0, 3, 'لإنتاج الدفعة الجديدة', 50.0, 0.0, 15.0, 0.0, 'pending', 'normal', '2023-02-20'),
        (2, 4, 200.0, 1, 'لعروض التسويق', 200.0, 0.0, 3.0, 0.0, 'pending', 'urgent', '2023-02-25')
]
    cursor.executemany("""
        INSERT INTO issue_request_items (
            request_id, item_id, quantity, unit_id, notes,
            approved_quantity, issued_quantity, estimated_cost, actual_cost,
            status, priority, required_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, issue_request_items)

    
    # 36. الجرد الفعلي
    physical_inventory = [
        ('PI-2023-001', '2023-01-31', 1, 'completed', 'user123', 'user456', 'جرد نهاية يناير'),
        ('PI-2023-002', '2023-02-28', 2, 'pending', 'user456', None, 'جرد نهاية فبراير')
    ]
    cursor.executemany("""
        INSERT INTO physical_inventory (
            inventory_number, inventory_date, warehouse_id, status,
            counted_by_external_id, verified_by_external_id, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, physical_inventory)
    
    # 37. أصناف الجرد الفعلي
    physical_inventory_items = [
        (1, 1, 450.0, 450.0, 0.0, 2, 'مطابق'),
        (1, 2, 180.0, 180.0, 0.0, 3, 'مطابق'),
        (1, 5, 300.0, 300.0, 0.0, 5, 'مطابق')
    ]
    cursor.executemany("""
        INSERT INTO physical_inventory_items (
            inventory_id, item_id, system_quantity, actual_quantity, variance, unit_id, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, physical_inventory_items)
    
# 38. إعدادات التكامل
    integration_config = [
        ('accounting_system_url', 'https://accounting.example.com/api', 'رابط نظام المحاسبة'),
        ('accounting_api_key', 'secret_key_123', 'مفتاح API لنظام المحاسبة'),
        ('user_system_url', 'https://users.example.com/api', 'رابط نظام المستخدمين'),
        ('sync_interval_minutes', '30', 'فترة المزامنة بالدقائق'),
        ('last_sync_timestamp', '2023-02-20 10:00:00', 'آخر وقت مزامنة')
]

    # ========== التعديل هنا ==========
    # التحقق من وجود المفتاح قبل الإدخال
    for config_key, config_value, description in integration_config:
        cursor.execute("SELECT COUNT(*) FROM integration_config WHERE config_key = ?", (config_key,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO integration_config (config_key, config_value, description)
                VALUES (?, ?, ?)
                """, (config_key, config_value, description))
        else:
                print(f"⚠️  المفتاح '{config_key}' موجود مسبقاً، تم تخطيه")
# ========== نهاية التعديل ==========

    
    # 39. تعيين مراكز التكلفة
    cost_center_mapping = [
        ('DEPT1', 'cost_center1', 'accounting', 1),
        ('DEPT2', 'cost_center2', 'accounting', 1),
        ('DEPT3', 'cost_center3', 'accounting', 1),
        ('DEPT4', 'cost_center4', 'accounting', 1),
        ('DEPT5', 'cost_center5', 'accounting', 1)
    ]
    cursor.executemany("""
        INSERT INTO cost_center_mapping (internal_reference, external_cost_center_id, external_system, is_active)
        VALUES (?, ?, ?, ?)
    """, cost_center_mapping)
    
    conn.commit()
    print("✅ تم إدخال جميع البيانات الافتراضية بنجاح")

def insert_comprehensive_stock_movements(cursor, conn):
    """
    إدخال حركات مخزنية شاملة تغطي جميع أنواع المعاملات
    """
    print("📦 إدخال حركات مخزنية شاملة...")
    
    try:
        # الحصول على معرفات المستودعات
        cursor.execute("SELECT id, code FROM warehouses")
        warehouses = {row[1]: row[0] for row in cursor.fetchall()}
        
        # الحصول على معرفات الأصناف
        cursor.execute("SELECT id, item_code FROM items")
        items = {row[1]: row[0] for row in cursor.fetchall()}
        
        # الحصول على معرفات الوحدات
        cursor.execute("SELECT id, code FROM units")
        units = {row[1]: row[0] for row in cursor.fetchall()}
        
        # حركات مخزنية شاملة
        stock_movements = [
            # حركات إدخال (In)
            {
                "transaction_number": "TRN-2023-001",
                "date": "2023-01-10",
                "item_code": "ITEM1",
                "warehouse_code": "WH1",
                "type": "In",
                "quantity": 1000.0,
                "unit_code": "UNIT2",
                "unit_cost": 4.5,
                "unit_sale_price": 6.0,
                "description": "شراء مباشر - سكر"
            },
            {
                "transaction_number": "TRN-2023-002",
                "date": "2023-01-15",
                "item_code": "ITEM2",
                "warehouse_code": "WH1",
                "type": "In",
                "quantity": 500.0,
                "unit_code": "UNIT3",
                "unit_cost": 14.0,
                "unit_sale_price": 18.0,
                "description": "شراء مباشر - زيت نباتي"
            },
            {
                "transaction_number": "TRN-2023-003",
                "date": "2023-01-20",
                "item_code": "ITEM3",
                "warehouse_code": "WH2",
                "type": "In",
                "quantity": 200.0,
                "unit_code": "UNIT3",
                "unit_cost": 9.5,
                "unit_sale_price": 14.0,
                "description": "شراء مباشر - منظف أرضيات"
            },
            
            # حركات إخراج (Out) - مبيعات
            {
                "transaction_number": "TRN-2023-004",
                "date": "2023-01-25",
                "item_code": "ITEM1",
                "warehouse_code": "WH1",
                "type": "Out",
                "quantity": 200.0,
                "unit_code": "UNIT2",
                "unit_cost": 4.5,
                "unit_sale_price": 6.0,
                "description": "مبيعات - عميل التجزئة"
            },
            {
                "transaction_number": "TRN-2023-005",
                "date": "2023-01-26",
                "item_code": "ITEM2",
                "warehouse_code": "WH1",
                "type": "Out",
                "quantity": 100.0,
                "unit_code": "UNIT3",
                "unit_cost": 14.0,
                "unit_sale_price": 18.0,
                "description": "مبيعات - عميل الجملة"
            },
            
            # حركات تحويل بين المستودعات
            {
                "transaction_number": "TRN-2023-006",
                "date": "2023-01-28",
                "item_code": "ITEM1",
                "warehouse_code": "WH1",
                "type": "Out",
                "quantity": 300.0,
                "unit_code": "UNIT2",
                "unit_cost": 4.5,
                "unit_sale_price": 6.0,
                "description": "تحويل إلى فرع الرياض"
            },
            {
                "transaction_number": "TRN-2023-007",
                "date": "2023-01-28",
                "item_code": "ITEM1",
                "warehouse_code": "WH2",
                "type": "In",
                "quantity": 300.0,
                "unit_code": "UNIT2",
                "unit_cost": 4.5,
                "unit_sale_price": 6.0,
                "description": "استلام من الفرع الرئيسي"
            },
            
            # حركات شهر فبراير
            {
                "transaction_number": "TRN-2023-008",
                "date": "2023-02-05",
                "item_code": "ITEM4",
                "warehouse_code": "WH1",
                "type": "In",
                "quantity": 1000.0,
                "unit_code": "UNIT1",
                "unit_cost": 1.8,
                "unit_sale_price": 3.0,
                "description": "شراء مباشر - مشروبات غازية"
            },
            {
                "transaction_number": "TRN-2023-009",
                "date": "2023-02-10",
                "item_code": "ITEM5",
                "warehouse_code": "WH1",
                "type": "In",
                "quantity": 500.0,
                "unit_code": "UNIT5",
                "unit_cost": 2.8,
                "unit_sale_price": 3.8,
                "description": "شراء مباشر - كراتين تغليف"
            }
        ]
        
        for movement in stock_movements:
            # التحقق من وجود البيانات
            if (movement["item_code"] not in items or 
                movement["warehouse_code"] not in warehouses or 
                movement["unit_code"] not in units):
                print(f"⚠️  بيانات غير موجودة للحركة: {movement['transaction_number']}")
                continue
            
            cursor.execute("""
                INSERT INTO stock_transactions (
                    transaction_number, transaction_date, item_id, warehouse_id, 
                    transaction_type, quantity, unit_cost, unit_sale_price, description,
                    cost_center_external_id, created_by_external_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                movement["transaction_number"],
                movement["date"],
                items[movement["item_code"]],
                warehouses[movement["warehouse_code"]],
                movement["type"],
                movement["quantity"],
                movement["unit_cost"],
                movement["unit_sale_price"],
                movement["description"],
                "cost_center1",
                "user123"
            ))
            
            # إدخال في جدول حركات الأصناف
            cursor.execute("""
                INSERT INTO item_movements (
                    item_id, movement_type, quantity, unit_id, date, reference, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                items[movement["item_code"]],
                movement["type"].lower(),
                movement["quantity"],
                units[movement["unit_code"]],
                movement["date"],
                movement["transaction_number"],
                movement["description"]
            ))
            
            print(f"✅ تم إدخال الحركة: {movement['transaction_number']}")
        
        conn.commit()
        print(f"✅ تم إدخال {len(stock_movements)} حركة مخزنية بنجاح")
        
    except Exception as e:
        print(f"❌ خطأ في إدخال الحركات المخزنية: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()

def insert_inventory_valuation_data(cursor, conn):
    """
    إدخال بيانات تقييم المخزون والأرصدة الافتتاحية
    """
    print("💰 إدخال بيانات تقييم المخزون...")
    
    try:
        # أرصدة افتتاحية للأصناف
        opening_balances = [
            ('ITEM1', 'WH1', 500.0, 'UNIT2', 4.0, 6.0, '2023-01-01'),
            ('ITEM2', 'WH1', 200.0, 'UNIT3', 13.0, 17.0, '2023-01-01'),
            ('ITEM3', 'WH2', 100.0, 'UNIT3', 9.0, 13.0, '2023-01-01'),
            ('ITEM4', 'WH1', 800.0, 'UNIT1', 1.7, 2.8, '2023-01-01'),
            ('ITEM5', 'WH1', 300.0, 'UNIT5', 2.5, 3.5, '2023-01-01')
        ]
        
        for balance in opening_balances:
            item_code, wh_code, qty, unit_code, cost, sale_price, date = balance
            
            # ========== التصحيح هنا ==========
            cursor.execute("SELECT id FROM items WHERE item_code = ?", (item_code,))
            item_result = cursor.fetchone()
            item_id = item_result[0] if item_result else None
            
            cursor.execute("SELECT id FROM warehouses WHERE code = ?", (wh_code,))
            wh_result = cursor.fetchone()
            wh_id = wh_result[0] if wh_result else None
            
            cursor.execute("SELECT id FROM units WHERE code = ?", (unit_code,))
            unit_result = cursor.fetchone()
            unit_id = unit_result[0] if unit_result else None
            # ========== نهاية التصحيح ==========
            
            if item_id and wh_id and unit_id:
                # إدخال حركة افتتاحية
                cursor.execute("""
                    INSERT INTO stock_transactions (
                        transaction_number, transaction_date, item_id, warehouse_id, 
                        transaction_type, quantity, unit_cost, unit_sale_price, description,
                        cost_center_external_id, created_by_external_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"OPEN-{item_code}-{wh_code}",
                    date,
                    item_id,
                    wh_id,
                    'In',
                    qty,
                    cost,
                    sale_price,
                    'رصيد افتتاحي',
                    "cost_center1",
                    "system"
                ))
                print(f"✅ تم إدخال الرصيد الافتتاحي لـ {item_code} في {wh_code}")
            else:
                print(f"⚠️  بيانات غير موجودة للرصيد الافتتاحي: {item_code} في {wh_code}")
        
        conn.commit()
        print("✅ تم إدخال الأرصدة الافتتاحية بنجاح")
        
    except Exception as e:
        print(f"❌ خطأ في إدخال بيانات التقييم: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()


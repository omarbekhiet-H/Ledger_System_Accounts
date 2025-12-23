# database/schems/default_data/financials_data_population.py

import sqlite3
import os
import sys
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.admin.user_manager import UserManager
from database.db_connection import get_financials_db_connection

def populate_users_and_permissions(cursor, conn):
    """
    يضيف الأدوار والمستخدمين والصلاحيات الافتراضية للنظام.
    """
    print("Populating default users, roles, and permissions...")

    temp_user_manager = UserManager(get_financials_db_connection)

    try:
        roles = [
            (1, 'Admin', 'مدير النظام', 'يملك كل الصلاحيات على النظام.'),
            (2, 'Accountant', 'محاسب', 'يملك صلاحيات الإدخال والتعديل والتقارير المحاسبية.'),
            (3, 'DataEntry', 'مدخل بيانات', 'يملك صلاحيات إدخال محدودة فقط (مثل الفواتير).'),
            (4, 'Auditor', 'مراجع', 'يملك صلاحيات عرض التقارير فقط بدون تعديل.')
        ]
        cursor.executemany("INSERT OR IGNORE INTO roles (id, role_name, role_name_ar, description) VALUES (?, ?, ?, ?)", roles)

        users = [
            ('admin', temp_user_manager._hash_password('123'), 'المدير العام', 1),
            ('accountant', temp_user_manager._hash_password('123'), 'المحاسب الرئيسي', 2),
            ('user1', temp_user_manager._hash_password('123'), 'موظف إدخال فواتير', 3)
        ]
        cursor.executemany("INSERT OR IGNORE INTO users (username, password_hash, full_name, role_id) VALUES (?, ?, ?, ?)", users)

        all_possible_permissions = [
            'reports.view.trial_balance', 'reports.view.general_ledger', 'reports.view.subsidiary_ledger',
            'journal.add', 'journal.edit', 'journal.delete', 'journal.post',
            'users.manage', 'permissions.manage'
        ]
        admin_permissions = [(1, perm_key, 1) for perm_key in all_possible_permissions]
        cursor.executemany("INSERT OR IGNORE INTO role_permissions (role_id, permission_key, is_allowed) VALUES (?, ?, ?)", admin_permissions)
        
        conn.commit()
        print("Default Admin user, role, and permissions have been populated.")

    except sqlite3.Error as e:
        print(f"ERROR populating users and permissions: {e}")
        conn.rollback()

def populate_accounts(cursor, conn):
    """
    Populates the accounts table with a structured and ideal chart of accounts.
    """
    print("Populating default Chart of Accounts...")

    try:
        type_ids = {
            'ASSET': cursor.execute("SELECT id FROM account_types WHERE code='ASSET'").fetchone()[0],
            'LIABILITY': cursor.execute("SELECT id FROM account_types WHERE code='LIABILITY'").fetchone()[0],
            'EQUITY': cursor.execute("SELECT id FROM account_types WHERE code='EQUITY'").fetchone()[0],
            'REVENUE': cursor.execute("SELECT id FROM account_types WHERE code='REVENUE'").fetchone()[0],
            'EXPENSE': cursor.execute("SELECT id FROM account_types WHERE code='EXPENSE'").fetchone()[0]
        }
    except (TypeError, IndexError):
        print("CRITICAL: Could not fetch essential account type IDs. Aborting account population.")
        return

    # حسابات محسنة ومتنوعة
    accounts_structure = [
        ('1', 'الأصول', 'Assets', 'ASSET', 1, 1, 0, None),
        ('11', 'الأصول المتداولة', 'Current Assets', 'ASSET', 1, 2, 0, '1'),
        ('111', 'النقدية وما في حكمها', 'Cash & Cash Equivalents', 'ASSET', 1, 3, 0, '11'),
        ('1111', 'الخزينة الرئيسية', 'Main Safe', 'ASSET', 1, 4, 1, '111'),
        ('1112', 'صندوق المبيعات', 'Sales Cash', 'ASSET', 1, 4, 1, '111'),
        ('112', 'البنوك', 'Banks', 'ASSET', 1, 3, 0, '11'),
        ('1121', 'البنك الأهلي - حساب جاري', 'Al Ahli Bank - Current', 'ASSET', 1, 4, 1, '112'),
        ('1122', 'البنك الرياض - توفير', 'Al Rajhi Bank - Savings', 'ASSET', 1, 4, 1, '112'),
        ('113', 'العملاء', 'Accounts Receivable', 'ASSET', 1, 3, 0, '11'),
        ('1131', 'عملاء نقديين', 'Cash Customers', 'ASSET', 1, 4, 1, '113'),
        ('1132', 'عملاء آجلين', 'Credit Customers', 'ASSET', 1, 4, 1, '113'),
        ('114', 'المخزون', 'Inventory', 'ASSET', 1, 3, 0, '11'),
        ('1141', 'مخزون بضاعة تامة', 'Finished Goods', 'ASSET', 1, 4, 1, '114'),
        ('1142', 'مخزون مواد خام', 'Raw Materials', 'ASSET', 1, 4, 1, '114'),
        ('115', 'مصروفات مقدمة', 'Prepaid Expenses', 'ASSET', 1, 3, 1, '11'),
        ('116', 'إيرادات مستحقة', 'Accrued Revenues', 'ASSET', 1, 3, 1, '11'),
        
        ('12', 'الأصول غير المتداولة', 'Non-Current Assets', 'ASSET', 1, 2, 0, '1'),
        ('121', 'الأصول الثابتة', 'Fixed Assets', 'ASSET', 1, 3, 0, '12'),
        ('1211', 'الأراضي', 'Land', 'ASSET', 1, 4, 1, '121'),
        ('1212', 'المباني', 'Buildings', 'ASSET', 1, 4, 1, '121'),
        ('1213', 'السيارات', 'Vehicles', 'ASSET', 1, 4, 1, '121'),
        ('1214', 'الأثاث والمعدات', 'Furniture & Equipment', 'ASSET', 1, 4, 1, '121'),
        ('122', 'مجمع الإهلاك', 'Accumulated Depreciation', 'ASSET', 1, 3, 0, '12'),
        ('1221', 'مجمع إهلاك المباني', 'Buildings Acc. Depreciation', 'ASSET', 1, 4, 1, '122'),
        ('1222', 'مجمع إهلاك السيارات', 'Vehicles Acc. Depreciation', 'ASSET', 1, 4, 1, '122'),
        ('1223', 'مجمع إهلاك الأثاث', 'Furniture Acc. Depreciation', 'ASSET', 1, 4, 1, '122'),

        ('2', 'الخصوم', 'Liabilities', 'LIABILITY', 1, 1, 0, None),
        ('21', 'الخصوم المتداولة', 'Current Liabilities', 'LIABILITY', 1, 2, 0, '2'),
        ('211', 'الموردون', 'Accounts Payable', 'LIABILITY', 1, 3, 0, '21'),
        ('2111', 'موردون محليون', 'Local Suppliers', 'LIABILITY', 1, 4, 1, '211'),
        ('2112', 'موردون دوليون', 'International Suppliers', 'LIABILITY', 1, 4, 1, '211'),
        ('212', 'الضرائب', 'Taxes', 'LIABILITY', 1, 3, 0, '21'),
        ('2121', 'ضريبة القيمة المضافة', 'Value Added Tax (VAT)', 'LIABILITY', 1, 4, 1, '212'),
        ('2122', 'ضريبة الدخل', 'Income Tax', 'LIABILITY', 1, 4, 1, '212'),
        ('213', 'قروض قصيرة الأجل', 'Short-term Loans', 'LIABILITY', 1, 3, 1, '21'),
        ('214', 'أوراق دفع', 'Notes Payable', 'LIABILITY', 1, 3, 1, '21'),
        
        ('22', 'الخصوم طويلة الأجل', 'Long-term Liabilities', 'LIABILITY', 1, 2, 0, '2'),
        ('221', 'قروض طويلة الأجل', 'Long-term Loans', 'LIABILITY', 1, 3, 1, '22'),
        ('222', 'سندات دفع', 'Bonds Payable', 'LIABILITY', 1, 3, 1, '22'),

        ('3', 'حقوق الملكية', 'Equity', 'EQUITY', 1, 1, 0, None),
        ('31', 'رأس المال', 'Capital', 'EQUITY', 1, 2, 0, '3'),
        ('311', 'رأس المال المدفوع', 'Paid-in Capital', 'EQUITY', 1, 3, 1, '31'),
        ('312', 'رأس المال الاحتياطي', 'Reserve Capital', 'EQUITY', 1, 3, 1, '31'),
        ('32', 'الأرباح المحتجزة', 'Retained Earnings', 'EQUITY', 1, 2, 1, '3'),
        ('33', 'أرباح العام الحالي', 'Current Year Earnings', 'EQUITY', 1, 2, 1, '3'),
        ('34', 'احتياطي قانوني', 'Legal Reserve', 'EQUITY', 1, 2, 1, '3'),

        ('4', 'الإيرادات', 'Revenues', 'REVENUE', 0, 1, 0, None),
        ('41', 'إيرادات النشاط الرئيسي', 'Operating Revenues', 'REVENUE', 0, 2, 0, '4'),
        ('411', 'إيرادات مبيعات', 'Sales Revenue', 'REVENUE', 0, 3, 1, '41'),
        ('412', 'إيرادات خدمات', 'Service Revenue', 'REVENUE', 0, 3, 1, '41'),
        ('42', 'إيرادات أخرى', 'Other Revenues', 'REVENUE', 0, 2, 0, '4'),
        ('421', 'إيرادات استثمارية', 'Investment Revenue', 'REVENUE', 0, 3, 1, '42'),
        ('422', 'إيرادات فوائد', 'Interest Revenue', 'REVENUE', 0, 3, 1, '42'),

        ('5', 'المصروفات', 'Expenses', 'EXPENSE', 0, 1, 0, None),
        ('51', 'تكلفة المبيعات', 'Cost of Sales', 'EXPENSE', 0, 2, 1, '5'),
        ('52', 'مصروفات تشغيلية', 'Operating Expenses', 'EXPENSE', 0, 2, 0, '5'),
        ('521', 'مصروفات إدارية', 'Admin Expenses', 'EXPENSE', 0, 3, 0, '52'),
        ('5211', 'مصروف رواتب', 'Salaries Expense', 'EXPENSE', 0, 4, 1, '521'),
        ('5212', 'مصروف إيجار', 'Rent Expense', 'EXPENSE', 0, 4, 1, '521'),
        ('5213', 'مصروف كهرباء وماء', 'Utilities Expense', 'EXPENSE', 0, 4, 1, '521'),
        ('5214', 'مصروف اتصالات', 'Communication Expense', 'EXPENSE', 0, 4, 1, '521'),
        ('522', 'مصروفات تسويقية', 'Marketing Expenses', 'EXPENSE', 0, 3, 0, '52'),
        ('5221', 'مصروف إعلانات', 'Advertising Expense', 'EXPENSE', 0, 4, 1, '522'),
        ('5222', 'مصروف علاقات عامة', 'Public Relations Expense', 'EXPENSE', 0, 4, 1, '522'),
        ('53', 'مصروفات مالية', 'Financial Expenses', 'EXPENSE', 0, 2, 0, '5'),
        ('531', 'مصروف فوائد', 'Interest Expense', 'EXPENSE', 0, 3, 1, '53'),
        ('532', 'مصروف عمولات بنكية', 'Bank Commission Expense', 'EXPENSE', 0, 3, 1, '53'),

        ('6', 'حسابات وسيطة للإقفال', 'Closing Accounts', 'EQUITY', 1, 1, 0, None),
        ('61', 'ملخص الدخل', 'Income Summary', 'EQUITY', 1, 2, 1, '6'),
        ('62', 'تسويات الجرد', 'Adjustment Accounts', 'EQUITY', 1, 2, 1, '6')
    ]

    created_accounts = {}
    for acc_code, name_ar, name_en, type_code, is_bs, level, is_final, parent_code in accounts_structure:
        parent_id = created_accounts.get(parent_code)
        type_id = type_ids.get(type_code)
        
        cursor.execute("SELECT id FROM accounts WHERE acc_code = ?", (acc_code,))
        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO accounts (acc_code, account_name_ar, account_name_en, account_type_id, parent_account_id, is_balance_sheet, level, is_final, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (acc_code, name_ar, name_en, type_id, parent_id, is_bs, level, is_final, 1))
            created_accounts[acc_code] = cursor.lastrowid

def insert_demo_journal_entries(cursor, conn):
    """
    إدخال قيود يومية تجريبية باستخدام الحسابات الحقيقية الموجودة
    """
    print("DEBUG: Starting demo journal entry population...")

    try:
        # استرجاع السنة المالية
        cursor.execute("SELECT id, year_name FROM financial_years WHERE is_active = 1 LIMIT 1")
        fy_result = cursor.fetchone()
        if fy_result is None:
            print("INFO: لا توجد سنة مالية نشطة، تخطي البيانات التجريبية.")
            return
        financial_year_id, year_name = fy_result

        # استرجاع بعض الحسابات للاستخدام في القيود
        cursor.execute("SELECT id, acc_code, account_name_ar FROM accounts WHERE is_final = 1 LIMIT 10")
        accounts = cursor.fetchall()
        
        if not accounts:
            print("INFO: لا توجد حسابات نهائية، تخطي البيانات التجريبية.")
            return

        # إنشاء قيود تجريبية متنوعة
        demo_entries = [
            {
                "desc": "قيد افتتاحي للمبيعات",
                "date": "2025-01-01",
                "lines": [
                    {"account": "1111", "debit": 50000, "credit": 0},
                    {"account": "311", "debit": 0, "credit": 50000}
                ]
            },
            {
                "desc": "قيد شراء بضاعة",
                "date": "2025-01-15",
                "lines": [
                    {"account": "1141", "debit": 20000, "credit": 0},
                    {"account": "1121", "debit": 0, "credit": 20000}
                ]
            },
            {
                "desc": "قيد مبيعات نقدية",
                "date": "2025-01-20",
                "lines": [
                    {"account": "1111", "debit": 15000, "credit": 0},
                    {"account": "411", "debit": 0, "credit": 15000}
                ]
            },
            {
                "desc": "قيد مصروفات رواتب",
                "date": "2025-01-30",
                "lines": [
                    {"account": "5211", "debit": 8000, "credit": 0},
                    {"account": "1121", "debit": 0, "credit": 8000}
                ]
            }
        ]

        entry_counter = 1
        for entry in demo_entries:
            entry_number = f"DEMO{entry_counter:03d}"
            total_debit = sum(line["debit"] for line in entry["lines"])
            total_credit = sum(line["credit"] for line in entry["lines"])
            
            if abs(total_debit - total_credit) > 0.01:
                print(f"Warning: قيد غير متوازن - {entry['desc']}")
                continue

            # إدخال رأس القيد
            cursor.execute("""
                INSERT INTO journal_entries (
                    entry_number, entry_date, description, financial_year_id,
                    total_debit, total_credit, status, system_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (entry_number, entry["date"], entry["desc"], financial_year_id,
                 total_debit, total_credit, 'Posted', entry["date"]))
            
            entry_id = cursor.lastrowid
            
            # إدخال بنود القيد
            for line in entry["lines"]:
                cursor.execute("SELECT id FROM accounts WHERE acc_code = ?", (line["account"],))
                account_result = cursor.fetchone()
                if account_result:
                    account_id = account_result[0]
                    cursor.execute("""
                        INSERT INTO journal_entry_lines (
                            journal_entry_id, account_id, debit, credit
                        ) VALUES (?, ?, ?, ?)
                    """, (entry_id, account_id, line["debit"], line["credit"]))
            
            print(f"تم إدخال القيد: {entry_number} - {entry['desc']}")
            entry_counter += 1

        conn.commit()
        print("✅ تم إدخال القيود التجريبية بنجاح.")

    except Exception as e:
        print(f"ERROR during demo journal entry insertion: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()

def insert_default_data(conn):
    """
    Inserts all default data into the financials database
    """
    cursor = conn.cursor()
    print("Inserting default data for Financials...")

    # 1. العملات
    cursor.execute("""
        INSERT OR IGNORE INTO currencies (code, name_ar, name_en, symbol, exchange_rate, is_base_currency, is_active) VALUES
        ('SAR', 'ريال سعودي', 'Saudi Riyal', '﷼', 1.0, 1, 1),
        ('USD', 'دولار أمريكي', 'US Dollar', '$', 3.75, 0, 1),
        ('EUR', 'يورو', 'Euro', '€', 4.0, 0, 1)
    """)

    # 2. أنواع الحسابات
    cursor.execute("""
        INSERT OR IGNORE INTO account_types (code, name_ar, name_en, account_side, is_active) VALUES
        ('ASSET', 'الأصول', 'Assets', 'Debit', 1),
        ('LIABILITY', 'الخصوم', 'Liabilities', 'Credit', 1),
        ('EQUITY', 'حقوق الملكية', 'Equity', 'Credit', 1),
        ('REVENUE', 'الإيرادات', 'Revenues', 'Credit', 1),
        ('EXPENSE', 'المصروفات', 'Expenses', 'Debit', 1)
    """)

    # 3. الحسابات
    populate_accounts(cursor, conn)
    
    # 4. أنواع المستندات
    cursor.execute("""
        INSERT OR IGNORE INTO document_types (code, name_ar, name_en, is_active) VALUES
        ('INV', 'فاتورة مبيعات', 'Sales Invoice', 1),
        ('PUR', 'فاتورة مشتريات', 'Purchase Invoice', 1),
        ('REC', 'سند قبض', 'Receipt Voucher', 1),
        ('PAY', 'سند صرف', 'Payment Voucher', 1),
        ('JE', 'قيد يومية', 'Journal Entry', 1),
        ('OPENING_BALANCE', 'رصيد افتتاحي', 'Opening Balance', 1)
    """)

    # 5. الخزائن النقدية
    cursor.execute("""
        INSERT OR IGNORE INTO cash_chests (name_ar, chest_code, account_id) VALUES
        ('الصندوق الرئيسي', 'MAIN_CASH', (SELECT id FROM accounts WHERE acc_code='1111')),
        ('صندوق المبيعات', 'SALES_CASH', (SELECT id FROM accounts WHERE acc_code='1112'))
    """)

    # 6. أنواع المعاملات
    cursor.execute("""
    INSERT OR IGNORE INTO transaction_types (code, name_ar, name_en, description, is_active) VALUES
    ('OP_ENTRY', 'قيد افتتاحي', 'Opening Entry', 'قيد يستخدم لتسجيل الأرصدة الافتتاحية', 1),
    ('SALES_INV', 'فاتورة مبيعات', 'Sales Invoice', 'معاملة بيع السلع أو الخدمات', 1),
    ('PURCH_INV', 'فاتورة مشتريات', 'Purchase Invoice', 'معاملة شراء السلع أو الخدمات', 1),
    ('CASH_RECEIPT', 'سند قبض نقدي', 'Cash Receipt Voucher', 'إثبات استلام مبلغ نقدي', 1),
    ('CASH_PAYMENT', 'سند صرف نقدي', 'Cash Payment Voucher', 'إثبات صرف مبلغ نقدي', 1)
    """)

    # 7. مراكز التكلفة
    cursor.execute("SELECT COUNT(*) FROM cost_centers")
    if cursor.fetchone()[0] == 0:
        cost_centers_data = [
            ('CC001', 'الإدارة العامة', 'General Management', 'مركز تكلفة الإدارة العامة', None),
            ('CC002', 'قسم المبيعات', 'Sales Department', 'مركز تكلفة قسم المبيعات', None),
            ('CC003', 'قسم المشتريات', 'Purchasing Department', 'مركز تكلفة قسم المشتريات', None),
            ('CC004', 'قسم التسويق', 'Marketing Department', 'مركز تكلفة قسم التسويق', None)
        ]
        cursor.executemany(
            "INSERT INTO cost_centers (code, name_ar, name_en, description, parent_cost_center_id) VALUES (?, ?, ?, ?, ?)",
            cost_centers_data
        )

    # 8. حسابات البنوك
    cursor.execute("""
        INSERT OR IGNORE INTO bank_accounts (bank_name_ar, account_number, account_id) VALUES
        ('بنك الرياض', '123456789', (SELECT id FROM accounts WHERE acc_code='1121')),
        ('بنك الأهلي', '987654321', (SELECT id FROM accounts WHERE acc_code='1122'))
    """)

    # 9. أنواع الضرائب
    cursor.execute("""
        INSERT OR IGNORE INTO tax_types (code, name_ar, name_en, rate, tax_account_id, is_active) VALUES
        ('VAT15', 'ضريبة القيمة المضافة 15%', 'VAT 15%', 0.15, (SELECT id FROM accounts WHERE acc_code='2121'), 1)
    """)

    # 10. السنوات المالية
    cursor.execute("SELECT COUNT(*) FROM financial_years")
    if cursor.fetchone()[0] == 0:
        current_year = datetime.now().year
        start_date = f"{current_year}-01-01"
        end_date = f"{current_year}-12-31"
        year_name = f"FY{current_year}"

        cursor.execute("""
            INSERT INTO financial_years (year_name, start_date, end_date, is_active, is_closed)
            VALUES (?, ?, ?, 1, 0)
        """, (year_name, start_date, end_date))

    conn.commit()

    # 11. القيود التجريبية
    insert_demo_journal_entries(cursor, conn)
    
    # 12. المستخدمين والصلاحيات
    populate_users_and_permissions(cursor, conn)

    print("Default data for Financials inserted successfully.")
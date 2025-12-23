# database/schems/financials_schema.py

FINANCIALS_SCHEMA_SCRIPT = """
-- =====================================================================
-- 1. جدول الأدوار
-- =====================================================================
CREATE TABLE IF NOT EXISTS roles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name       TEXT NOT NULL UNIQUE,
    role_name_ar    TEXT,
    description     TEXT
);

-- =====================================================================
-- 2. جدول المستخدمين
-- =====================================================================
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    full_name       TEXT,
    role_id         INTEGER NOT NULL,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT
);

-- =====================================================================
-- 3. صلاحيات الأدوار
-- =====================================================================
CREATE TABLE IF NOT EXISTS role_permissions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id         INTEGER NOT NULL,
    permission_key  TEXT NOT NULL,
    is_allowed      INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE(role_id, permission_key)
);

-- =====================================================================
-- 4. العملات
-- =====================================================================
CREATE TABLE IF NOT EXISTS currencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name_ar TEXT NOT NULL UNIQUE,
    name_en TEXT UNIQUE,
    symbol TEXT,
    exchange_rate REAL DEFAULT 1.0, 
    is_base_currency INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1, 
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL);

-- =====================================================================
-- 5. أنواع الحسابات
-- =====================================================================
CREATE TABLE IF NOT EXISTS account_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name_ar TEXT NOT NULL UNIQUE,
    name_en TEXT UNIQUE,
    account_side TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL
);

-- =====================================================================
-- 6. الحسابات مع ربط بالشجرة والسنة المالية
-- =====================================================================
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acc_code TEXT NOT NULL UNIQUE COLLATE NOCASE, 
    account_name_ar TEXT NOT NULL,
    account_name_en TEXT,
    account_type_id INTEGER NOT NULL,
    parent_account_id INTEGER,
    is_final INTEGER NOT NULL DEFAULT 0,
    is_balance_sheet INTEGER NOT NULL DEFAULT 0, 
    level INTEGER NOT NULL DEFAULT 1, 
    account_path TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL,
    FOREIGN KEY (account_type_id) REFERENCES account_types(id),
    FOREIGN KEY (parent_account_id) REFERENCES accounts(id)
   
);

-- جدول ربط الحسابات بالمجموعات
CREATE TABLE IF NOT EXISTS category_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    account_type TEXT NOT NULL,  -- نوع الحساب (مخزون، مبيعات، إلخ)
    account_id INTEGER NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    UNIQUE(category_id, account_type),
    FOREIGN KEY (category_id) REFERENCES item_categories(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS inventory_accounts_mapping (
    action_id TEXT PRIMARY KEY,
    debit_account_id INTEGER,
    credit_account_id INTEGER,
    FOREIGN KEY (debit_account_id) REFERENCES accounts (id),
    FOREIGN KEY (credit_account_id) REFERENCES accounts (id)
);
-- جدول أنواع الحسابات المطلوبة
CREATE TABLE IF NOT EXISTS account_types_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_key TEXT NOT NULL UNIQUE,  -- مفتاح النوع (inventory, sales, etc.)
    name_ar TEXT NOT NULL,          -- الاسم العربي
    name_en TEXT,                   -- الاسم الإنجليزي
    description TEXT,               -- الوصف
    is_required INTEGER DEFAULT 0,  -- إذا كان الحساب إلزامي
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS voucher_deductions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cash_bank_transaction_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    FOREIGN KEY (cash_bank_transaction_id) REFERENCES cash_bank_transactions (id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts (id)
);
-- =====================================================================
-- 7. أنواع المستندات
-- =====================================================================
CREATE TABLE IF NOT EXISTS document_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name_ar TEXT NOT NULL UNIQUE,
    name_en TEXT UNIQUE,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL
);

-- =====================================================================
-- 8. أنواع العمليات
-- =====================================================================
CREATE TABLE IF NOT EXISTS transaction_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name_ar TEXT NOT NULL UNIQUE,
    name_en TEXT UNIQUE,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL
);

-- =====================================================================
-- 9. أنواع الضرائب
-- =====================================================================
CREATE TABLE IF NOT EXISTS tax_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name_ar TEXT NOT NULL UNIQUE,
    name_en TEXT UNIQUE,
    rate REAL NOT NULL,
    tax_account_id INTEGER, 
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL,
    FOREIGN KEY (tax_account_id) REFERENCES accounts(id)
);

-- =====================================================================
-- 10. السنة المالية
-- =====================================================================
CREATE TABLE IF NOT EXISTS financial_years (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year_name TEXT NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_closed INTEGER NOT NULL DEFAULT 0,
    closing_entry_id INTEGER,
    revenues_account_id INTEGER,
    expenses_account_id INTEGER,
    retained_earnings_account_id INTEGER,
    legal_reserve_account_id INTEGER,
    legal_reserve_percent REAL DEFAULT 0.0,
    income_tax_account_id INTEGER,
    solidarity_tax_account_id INTEGER,
    income_tax_percent REAL DEFAULT 0.0,
    solidarity_tax_percent REAL DEFAULT 0.0,
    closed_at TIMESTAMP,
    closed_by_user_id INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (closing_entry_id) REFERENCES journal_entries(id) ON DELETE SET NULL,
    FOREIGN KEY (revenues_account_id) REFERENCES accounts(id),
    FOREIGN KEY (expenses_account_id) REFERENCES accounts(id),
    FOREIGN KEY (retained_earnings_account_id) REFERENCES accounts(id),
    FOREIGN KEY (legal_reserve_account_id) REFERENCES accounts(id),
    FOREIGN KEY (income_tax_account_id) REFERENCES accounts(id),
    FOREIGN KEY (solidarity_tax_account_id) REFERENCES accounts(id)
);

-- =====================================================================
-- 11. قيود اليومية
-- =====================================================================
CREATE TABLE IF NOT EXISTS journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_number TEXT NOT NULL UNIQUE COLLATE NOCASE,
    entry_date TEXT NOT NULL,
    system_date DATE NOT NULL DEFAULT (DATE('now')),
    financial_year_id INTEGER NOT NULL,
    description TEXT,
    transaction_type_id INTEGER, 
    total_debit REAL NOT NULL CHECK(total_debit >= 0),
    total_credit REAL NOT NULL CHECK(total_credit >= 0),
    status TEXT DEFAULT 'Under Review',
    created_by INTEGER,
    updated_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL,
    FOREIGN KEY (transaction_type_id) REFERENCES transaction_types(id),
    FOREIGN KEY (financial_year_id) REFERENCES financial_years(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id)
);

-- =====================================================================
-- 12. بنود القيود
-- =====================================================================
CREATE TABLE IF NOT EXISTS journal_entry_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal_entry_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    document_type_id INTEGER, 
    tax_type_id INTEGER, 
    cost_center_id INTEGER, 
    exchange_rate REAL DEFAULT 1.0,
    notes TEXT,
    contra_account_id INTEGER,
    document_number TEXT,
    debit REAL DEFAULT 0.0 CHECK(debit >= 0),
    credit REAL DEFAULT 0.0 CHECK(credit >= 0),
    created_by INTEGER,
    updated_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL,
    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (contra_account_id) REFERENCES accounts(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id),
    FOREIGN KEY (tax_type_id) REFERENCES tax_types(id), 
    FOREIGN KEY (cost_center_id) REFERENCES cost_centers(id),
    FOREIGN KEY (document_type_id) REFERENCES document_types(id)
);

-- =====================================================================
-- 13. صناديق النقد والبنوك والجداول المساعدة
-- =====================================================================
CREATE TABLE IF NOT EXISTS cash_chests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar TEXT NOT NULL UNIQUE,
    chest_code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    account_id INTEGER NOT NULL UNIQUE, 
    currency_id INTEGER NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
   
);

CREATE TABLE IF NOT EXISTS bank_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_name_ar TEXT NOT NULL,
    account_number TEXT NOT NULL UNIQUE COLLATE NOCASE,
    account_id INTEGER NOT NULL UNIQUE, 
    currency_id INTEGER NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(id)

);

CREATE TABLE IF NOT EXISTS cost_centers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL,
    name_en TEXT,
    description TEXT,
    parent_cost_center_id INTEGER,
    is_final INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL,
    FOREIGN KEY (parent_cost_center_id) REFERENCES cost_centers(id)
);

CREATE TABLE IF NOT EXISTS cash_bank_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_number TEXT NOT NULL UNIQUE COLLATE NOCASE,
    transaction_date TEXT NOT NULL,
    cash_chest_id INTEGER,
    bank_account_id INTEGER,
    transaction_type TEXT NOT NULL,
    transaction_type_id INTEGER,
    cost_center_id INTEGER,
    description TEXT,
    amount REAL NOT NULL,
    exchange_rate REAL DEFAULT 1.0,
    journal_entry_id INTEGER UNIQUE, 
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL,
    FOREIGN KEY (cash_chest_id) REFERENCES cash_chests(id),
    FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id),
    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id),
    CHECK ((cash_chest_id IS NOT NULL AND bank_account_id IS NULL) OR (cash_chest_id IS NULL AND bank_account_id IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS account_linking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_type TEXT UNIQUE NOT NULL,
    account_id INTEGER NOT NULL,
    description TEXT,
    FOREIGN KEY(account_id) REFERENCES chart_of_accounts(id)
);

-- =====================================================================
-- 14. إغلاق السنة المالية
-- =====================================================================
CREATE TABLE IF NOT EXISTS financial_closures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    financial_year_id INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    updated_at DATETIME,
    executed_at TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER,
    updated_by_user_id INTEGER,
    FOREIGN KEY (financial_year_id) REFERENCES financial_years(id)
);

CREATE TRIGGER IF NOT EXISTS trg_financial_closures_updated
AFTER UPDATE ON financial_closures
FOR EACH ROW
BEGIN
    UPDATE financial_closures
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;
END;


"""

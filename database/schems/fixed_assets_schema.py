# -*- coding: utf-8 -*-

FIXED_ASSETS_SCHEMA_SCRIPT = """

-- 🔹 أنواع المواقع
CREATE TABLE IF NOT EXISTS location_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name_ar TEXT NOT NULL UNIQUE,
    name_en TEXT UNIQUE,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL
);

-- 🔹 المواقع مع ربط بالشجرة
CREATE TABLE IF NOT EXISTS asset_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loc_code TEXT NOT NULL UNIQUE COLLATE NOCASE, 
    location_name_ar TEXT NOT NULL,
    location_name_en TEXT,
    location_type_id INTEGER NOT NULL,
    parent_location_id INTEGER,
    is_final INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1, 
    location_path TEXT,
    description TEXT,
    
    -- معلومات إضافية للموقع
    address TEXT,
    phone TEXT,
    responsible_person TEXT,
    capacity INTEGER,
    current_usage INTEGER DEFAULT 0,
    
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL,
    
    FOREIGN KEY (location_type_id) REFERENCES location_types(id),
    FOREIGN KEY (parent_location_id) REFERENCES asset_locations(id)
);

-- 🔹 فهارس لأداء أفضل
CREATE INDEX IF NOT EXISTS idx_location_code ON asset_locations(loc_code);
CREATE INDEX IF NOT EXISTS idx_location_parent ON asset_locations(parent_location_id);
CREATE INDEX IF NOT EXISTS idx_location_path ON asset_locations(location_path);
CREATE INDEX IF NOT EXISTS idx_location_type ON asset_locations(location_type_id);

-- 🔹 طرق الإهلاك
CREATE TABLE IF NOT EXISTS depreciation_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name_ar TEXT NOT NULL UNIQUE,
    name_en TEXT UNIQUE,
    is_active INTEGER DEFAULT 1,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 تصنيفات الأصول
CREATE TABLE IF NOT EXISTS fixed_asset_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name_ar TEXT NOT NULL UNIQUE,
    name_en TEXT UNIQUE,
    category_type TEXT NOT NULL DEFAULT 'fixed_asset',
    parent_id INTEGER DEFAULT NULL,
    level INTEGER DEFAULT 1,
    depreciation_method_id INTEGER,
    useful_life_years INTEGER,
    depreciation_rate REAL,
    asset_account_id INTEGER,
    depreciation_account_id INTEGER,
    accumulated_dep_account_id INTEGER,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (depreciation_method_id) REFERENCES depreciation_methods(id),
    FOREIGN KEY (parent_id) REFERENCES fixed_asset_categories(id)
);

-- 🔹 المخازن (من inventory)
CREATE TABLE IF NOT EXISTS warehouses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name_ar TEXT NOT NULL,
    name_en TEXT,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 المباني
CREATE TABLE IF NOT EXISTS buildings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id INTEGER NOT NULL,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name_ar TEXT NOT NULL,
    name_en TEXT,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE CASCADE
);

-- 🔹 الأدوار
CREATE TABLE IF NOT EXISTS floors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id INTEGER NOT NULL,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name_ar TEXT NOT NULL,
    name_en TEXT,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
);

-- 🔹 الغرف
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    floor_id INTEGER NOT NULL,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name_ar TEXT NOT NULL,
    name_en TEXT,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (floor_id) REFERENCES floors(id) ON DELETE CASCADE
);

-- 🔹 المسؤولين
CREATE TABLE IF NOT EXISTS asset_responsibles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL,
    name_en TEXT,
    position TEXT,
    department TEXT,
    phone TEXT,
    email TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 الأصول الثابتة
CREATE TABLE IF NOT EXISTS fixed_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    asset_name_ar TEXT NOT NULL,
    asset_name_en TEXT,
    category_id INTEGER NOT NULL,
    acquisition_date TEXT NOT NULL,
    acquisition_cost REAL NOT NULL,
    salvage_value REAL DEFAULT 0.0,
    current_book_value REAL NOT NULL,
    accumulated_depreciation REAL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'In Use',
    location_id INTEGER,
    quantity REAL DEFAULT 1.0,
    unit_price REAL DEFAULT 0.0,
    unit_type TEXT,
    description TEXT,
    specifications TEXT,
    responsible_id INTEGER,
    journal_entry_id INTEGER,
    created_by_user_id INTEGER,
    depreciation_method_id INTEGER,

    -- بيانات فنية
    serial_number TEXT,
    model TEXT,
    brand TEXT,
    supplier_id INTEGER,
    purchase_document_ref TEXT,
    warranty_end_date TEXT,

    -- معلومات إضافية
    commissioning_date DATE,
    useful_life_years INTEGER,
    last_maintenance_date DATE,
    maintenance_cycle TEXT,

    -- بيانات الملكية والتأمين
    owner_entity TEXT,
    insurance_status TEXT,
    insurance_policy_no TEXT,

    -- تتبع
    barcode_value TEXT,
    asset_image_path TEXT,

    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (category_id) REFERENCES fixed_asset_categories(id),
    FOREIGN KEY (location_id) REFERENCES asset_locations(id),
    FOREIGN KEY (responsible_id) REFERENCES asset_responsibles(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id),
    FOREIGN KEY (depreciation_method_id) REFERENCES depreciation_methods(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

-- 🔹 ربط الأصول بالحسابات
CREATE TABLE IF NOT EXISTS asset_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    relation_type TEXT DEFAULT 'extra' CHECK(relation_type IN ('main','depreciation','accumulated','gain_loss','other')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(asset_id, account_id),
    FOREIGN KEY (asset_id) REFERENCES fixed_assets(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

-- 🔹 قيود الإهلاك
CREATE TABLE IF NOT EXISTS depreciation_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    entry_date TEXT NOT NULL,
    depreciation_amount REAL NOT NULL,
    journal_entry_id INTEGER,
    period TEXT,
    is_posted INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES fixed_assets(id) ON DELETE CASCADE,
    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id)
);

-- 🔹 عمليات نقل الأصول
CREATE TABLE IF NOT EXISTS asset_transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    from_location_id INTEGER,
    to_location_id INTEGER,
    transfer_date TEXT NOT NULL,
    from_responsible_id INTEGER,
    to_responsible_id INTEGER,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES fixed_assets(id),
    FOREIGN KEY (from_location_id) REFERENCES asset_locations(id),
    FOREIGN KEY (to_location_id) REFERENCES asset_locations(id),
    FOREIGN KEY (from_responsible_id) REFERENCES asset_responsibles(id),
    FOREIGN KEY (to_responsible_id) REFERENCES asset_responsibles(id)
);

-- 🔹 تأمين الأصول
CREATE TABLE IF NOT EXISTS asset_insurance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    policy_number TEXT NOT NULL,
    provider TEXT,
    insurance_company TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    premium REAL DEFAULT 0.0,
    coverage_details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES fixed_assets(id) ON DELETE CASCADE
);

-- 🔹 إعادة تقييم الأصول
CREATE TABLE IF NOT EXISTS asset_revaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    revaluation_date TEXT NOT NULL,
    old_value REAL NOT NULL,
    new_value REAL NOT NULL,
    reason TEXT,
    journal_entry_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES fixed_assets(id),
    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id)
);

-- الحركات (نقل الأصل بين مواقع/مسؤولين)
CREATE TABLE IF NOT EXISTS asset_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    from_location_id INTEGER,
    to_location_id INTEGER,
    from_responsible_id INTEGER,
    to_responsible_id INTEGER,
    movement_date TEXT NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES fixed_assets(id) ON DELETE CASCADE,
    FOREIGN KEY (from_location_id) REFERENCES asset_locations(id),
    FOREIGN KEY (to_location_id) REFERENCES asset_locations(id),
    FOREIGN KEY (from_responsible_id) REFERENCES asset_responsibles(id),
    FOREIGN KEY (to_responsible_id) REFERENCES asset_responsibles(id)
);

-- الصيانة
CREATE TABLE IF NOT EXISTS asset_maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    maintenance_date TEXT NOT NULL,
    maintenance_type TEXT NOT NULL,
    description TEXT,
    cost REAL DEFAULT 0.0,
    performed_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES fixed_assets(id) ON DELETE CASCADE
);

-- التصرف في الأصول
CREATE TABLE IF NOT EXISTS asset_disposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    disposal_date TEXT NOT NULL,
    disposal_type TEXT NOT NULL,
    proceeds REAL DEFAULT 0.0,
    journal_entry_id INTEGER,
    disposed_by_user_id INTEGER,
    approval_status TEXT DEFAULT 'pending',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES fixed_assets(id) ON DELETE CASCADE,
    FOREIGN KEY (disposed_by_user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS measurement_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL,
    name_en TEXT,
    symbol TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- الضمانات
CREATE TABLE IF NOT EXISTS asset_warranties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    provider TEXT,
    start_date TEXT,
    end_date TEXT,
    terms TEXT,
    contact_info TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES fixed_assets(id) ON DELETE CASCADE
);

-- 🔹 فهارس للأداء
CREATE INDEX IF NOT EXISTS idx_assets_category ON fixed_assets(category_id);
CREATE INDEX IF NOT EXISTS idx_assets_status ON fixed_assets(status);
CREATE INDEX IF NOT EXISTS idx_depreciation_asset ON depreciation_entries(asset_id);
CREATE INDEX IF NOT EXISTS idx_assets_serial ON fixed_assets(serial_number);
CREATE INDEX IF NOT EXISTS idx_assets_supplier ON fixed_assets(supplier_id);
"""

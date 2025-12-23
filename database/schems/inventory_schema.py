INVENTORY_SCHEMA_SCRIPT = """
-- جدول المواقع
CREATE TABLE IF NOT EXISTS store_locations  (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    location_name_ar TEXT NOT NULL,
    location_name_en TEXT,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

-- جدول الفروع
CREATE TABLE IF NOT EXISTS branches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL,
    name_en TEXT,
    location_id INTEGER NOT NULL,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (location_id) REFERENCES store_locations (id)
);

-- جدول المستودعات
CREATE TABLE IF NOT EXISTS warehouses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL,
    name_en TEXT,
    branch_id INTEGER NOT NULL,
    location_id INTEGER,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    capacity REAL DEFAULT 0,
    current_capacity REAL DEFAULT 0,
    manager_external_id TEXT,
    address TEXT,
    contact_phone TEXT,
    CHECK (capacity >= 0),
    CHECK (current_capacity >= 0 AND current_capacity <= capacity),
    FOREIGN KEY (branch_id) REFERENCES branches(id),
    FOREIGN KEY (location_id) REFERENCES store_locations (id)
);

-- جدول الوحدات
CREATE TABLE IF NOT EXISTS units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name_ar TEXT NOT NULL,
    name_en TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول وحدات الأصناف
CREATE TABLE IF NOT EXISTS item_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    unit_id INTEGER NOT NULL,
    is_main INTEGER DEFAULT 0,
    is_medium INTEGER DEFAULT 0,
    is_small INTEGER DEFAULT 0,
    conversion_factor REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id),
    UNIQUE(item_id, unit_id)
);

-- جدول الأقسام
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL UNIQUE,
    name_en TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- إضافة حقول التكامل
    external_department_id TEXT,
    external_system TEXT DEFAULT 'accounting'
);

-- جدول فئات الأصناف
CREATE TABLE IF NOT EXISTS item_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL,
    name_en TEXT,
    parent_id INTEGER,
    description TEXT,
    account_id INTEGER, -- الحساب المرتبط بالمجموعة
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (parent_id) REFERENCES item_categories(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

-- جدول مجموعات الأصناف
CREATE TABLE IF NOT EXISTS item_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name_ar TEXT NOT NULL,
    name_en TEXT,
    category_id INTEGER NOT NULL,
    account_id INTEGER, -- الحساب المرتبط بالمجموعة
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (category_id) REFERENCES item_categories(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);


-- جدول ربط مجموعات الأصناف بالحسابات
CREATE TABLE IF NOT EXISTS group_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    account_type TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (group_id) REFERENCES item_groups(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    UNIQUE(group_id, account_type)
);

-- جدول ربط فئات الأصناف بالحسابات
CREATE TABLE IF NOT EXISTS category_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    account_type TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (category_id) REFERENCES item_categories(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    UNIQUE(category_id, account_type)
);


-- جدول الأصناف
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    item_name_ar TEXT NOT NULL UNIQUE,
    item_name_en TEXT UNIQUE,
    item_description TEXT,
    item_type TEXT NOT NULL,
    item_category_id INTEGER,
    item_group_id INTEGER,
    base_unit_id INTEGER NOT NULL,
    has_expiry_date INTEGER DEFAULT 0,
    min_stock_limit REAL DEFAULT 0 CHECK(min_stock_limit >= 0),
    max_stock_limit REAL DEFAULT 0 CHECK(max_stock_limit >= 0),
    reorder_point REAL DEFAULT 0.0,
    purchase_price REAL DEFAULT 0 CHECK(purchase_price >= 0),
    sale_price REAL DEFAULT 0 CHECK(sale_price >= 0),
    inventory_account_id INTEGER,
    cogs_account_id INTEGER,
    sales_account_id INTEGER,
    expiry_date TEXT,
    image_path TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- إضافة حقول جديدة
    weight REAL DEFAULT 0,
    dimensions TEXT,
    shelf_life_days INTEGER,
    hazard_classification TEXT,
    storage_conditions TEXT,
    manufacturer TEXT,
    supplier_id INTEGER,
    lead_time_days INTEGER,
    -- حقول التكامل مع الأنظمة الخارجية
    external_item_id TEXT,
    external_system TEXT DEFAULT 'accounting',
    FOREIGN KEY (base_unit_id) REFERENCES units(id),
    FOREIGN KEY (item_category_id) REFERENCES item_categories(id),
    FOREIGN KEY (item_group_id) REFERENCES item_groups(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);
-- جدول الموردين
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_code TEXT NOT NULL UNIQUE, -- رمز المورد
    name_ar TEXT NOT NULL,
    name_en TEXT,
    tax_number TEXT,
    contact_person TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    country TEXT,
    city TEXT,
    postal_code TEXT,
    website TEXT,
    supply_category TEXT,
    payment_terms TEXT,
    payment_method TEXT,
    credit_limit DECIMAL(10, 2),
    rating INTEGER,
    language TEXT,
    contract_start_date DATE,
    contract_end_date DATE,
    is_verified INTEGER DEFAULT 0,
    preferred_contact_method TEXT,
    account_id INTEGER,                 -- الحساب الرئيسي للمورد
    relation_type TEXT DEFAULT 'main',
    financial_policy_id INTEGER,
    inventory_policy_id INTEGER,
    minimum_stock_level INTEGER,
    lead_time INTEGER,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- حقول التكامل مع نظام المحاسبة
    external_account_id TEXT,
    external_system TEXT DEFAULT 'accounting',
    FOREIGN KEY (account_id) REFERENCES accounts(id)
  
);

-- جدول حسابات الموردين (لحسابات إضافية)
CREATE TABLE IF NOT EXISTS supplier_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    relation_type TEXT DEFAULT 'extra' CHECK(relation_type IN ('main','extra','other')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(supplier_id, account_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

-- جدول حسابات العملاء (لحسابات إضافية)
CREATE TABLE IF NOT EXISTS customer_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    relation_type TEXT DEFAULT 'extra' CHECK(relation_type IN ('main','extra','other')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, account_id),
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- جدول سياسات الائتمان
CREATE TABLE IF NOT EXISTS credit_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_name TEXT NOT NULL,
    policy_type TEXT NOT NULL,
    credit_limit DECIMAL(15,2) NOT NULL,
    payment_terms TEXT NOT NULL,
    grace_period INTEGER DEFAULT 0,
    interest_rate DECIMAL(5,2) DEFAULT 0.0,
    min_order_value DECIMAL(15,2) DEFAULT 0.0,
    max_credit_period INTEGER,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- جدول سياسات البونص
CREATE TABLE IF NOT EXISTS bonus_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_name TEXT NOT NULL,
    bonus_type TEXT NOT NULL,
    min_quantity DECIMAL(15,3) DEFAULT 0.0,
    bonus_value DECIMAL(15,3) NOT NULL,
    applicable_from DATE NOT NULL,
    applicable_to DATE,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- جدول تفعيل سياسات البونص على الأصناف
CREATE TABLE IF NOT EXISTS item_bonus_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    bonus_policy_id INTEGER NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (bonus_policy_id) REFERENCES bonus_policies(id),
    UNIQUE(item_id, bonus_policy_id)
);

-- جدول المعاملات الائتمانية
CREATE TABLE IF NOT EXISTS credit_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_type TEXT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    balance DECIMAL(15,2) NOT NULL,
    reference_id INTEGER,
    reference_type TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- جدول طلبات الشراء
CREATE TABLE IF NOT EXISTS purchase_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_number TEXT NOT NULL UNIQUE,
    request_date TEXT NOT NULL,
    requester_external_id TEXT,
    department_id INTEGER,
    status TEXT DEFAULT 'pending',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- حقول الموافقة والتكامل
    approved_by_external_id TEXT,
    approved_at DATETIME,
    cost_center_external_id TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- جدول أصناف طلبات الشراء
CREATE TABLE IF NOT EXISTS purchase_request_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    unit_price REAL,
    total_price REAL,
    category_id INTEGER,
    is_selected INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES purchase_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id),
    FOREIGN KEY (category_id) REFERENCES item_categories(id)
);

-- جدول أوامر الشراء
CREATE TABLE IF NOT EXISTS purchase_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    expected_delivery_date TEXT,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- حقول الموافقة والتكامل
    approved_by_external_id TEXT,
    approved_at DATETIME,
    created_by_external_id TEXT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

-- جدول فواتير الشراء
CREATE TABLE IF NOT EXISTS purchase_invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    invoice_number TEXT UNIQUE,
    invoice_date TEXT NOT NULL,
    order_id INTEGER,
    total_amount REAL NOT NULL,
    accounting_entry_id INTEGER,
    status TEXT DEFAULT 'pending',
    payment_terms TEXT DEFAULT 'net_30',
    discount_amount DECIMAL(15,2) DEFAULT 0.0,
    due_date DATE,
    early_payment_discount DECIMAL(5,2) DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (order_id) REFERENCES purchase_orders(id)
);

-- جدول أصناف فواتير الشراء
CREATE TABLE IF NOT EXISTS purchase_invoice_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    total_price REAL NOT NULL,
    is_bonus INTEGER DEFAULT 0,
    original_purchase_price REAL,
    cost_account_id INTEGER,
    inventory_account_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- حقول التكامل مع نظام المحاسبة
    cost_account_external_id TEXT,
    inventory_account_external_id TEXT,
    FOREIGN KEY (invoice_id) REFERENCES purchase_invoices(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);

-- جدول أوامر التوريد
CREATE TABLE IF NOT EXISTS supply_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT NOT NULL UNIQUE,
    request_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    expected_delivery_date TEXT,
    status TEXT DEFAULT 'pending',
    delivery_days INTEGER,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES purchase_requests(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);


-- جدول أصناف أوامر التوريد
CREATE TABLE IF NOT EXISTS supply_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    received_quantity REAL DEFAULT 0,  -- تمت إضافة هذا الحقل
    unit_id INTEGER NOT NULL,
    price REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES supply_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);

-- جدول إذونات الاستلام
CREATE TABLE IF NOT EXISTS receipt_permits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    permit_number TEXT NOT NULL UNIQUE,
    permit_date DATE DEFAULT CURRENT_DATE,
    supply_order_id INTEGER NOT NULL,
    warehouse_id INTEGER NOT NULL,
    receipt_date TEXT,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- حقول الموافقة والتكامل
    received_by_external_id TEXT,
    approved_by_external_id TEXT,
    FOREIGN KEY (supply_order_id) REFERENCES supply_orders(id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
);

CREATE TABLE IF NOT EXISTS receipt_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    permit_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    received_quantity REAL DEFAULT 0,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (permit_id) REFERENCES receipt_permits(id),
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);

CREATE TABLE IF NOT EXISTS item_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    movement_type TEXT NOT NULL CHECK(movement_type IN ('in', 'out', 'adjustment', 'transfer')),
    quantity REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    date DATE NOT NULL,
    reference TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);

-- إنشاء فهارس لتحسين الأداء
CREATE INDEX IF NOT EXISTS idx_item_movements_item ON item_movements(item_id);
CREATE INDEX IF NOT EXISTS idx_item_movements_date ON item_movements(date);
CREATE INDEX IF NOT EXISTS idx_item_movements_type ON item_movements(movement_type);

-- جدول تفاصيل إذونات الاستلام
CREATE TABLE IF NOT EXISTS receipt_permit_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_permit_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    received_quantity REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (receipt_permit_id) REFERENCES receipt_permits(id),
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);
-- جدول إذونات الإضافة
CREATE TABLE IF NOT EXISTS addition_permits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,
    addition_date TEXT NOT NULL,
     notes TEXT,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (receipt_id) REFERENCES receipt_permits(id)
);

-- جدول أصناف إذونات الإضافة
CREATE TABLE IF NOT EXISTS addition_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    permit_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (permit_id) REFERENCES addition_permits(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);

-- جدول الفواتير المخزنية
CREATE TABLE IF NOT EXISTS inventory_invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    addition_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    invoice_number TEXT,
    invoice_date TEXT NOT NULL,
    total_amount REAL NOT NULL,
    status TEXT DEFAULT 'pending',
    invoice_type TEXT NOT NULL DEFAULT 'purchase',
    accounting_entry_id INTEGER,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (addition_id) REFERENCES addition_permits(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

-- جدول أصناف الفواتير المخزنية
CREATE TABLE IF NOT EXISTS invoice_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    total_price REAL NOT NULL,
    is_bonus INTEGER DEFAULT 0,
    original_purchase_price REAL,
    base_invoice_id INTEGER,
    cost_account_id INTEGER,
    inventory_account_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- حقول التكامل مع نظام المحاسبة
    cost_account_external_id TEXT,
    inventory_account_external_id TEXT,
    FOREIGN KEY (invoice_id) REFERENCES inventory_invoices(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);

-- جدول الحركات المخزنية
CREATE TABLE IF NOT EXISTS stock_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_number TEXT NOT NULL UNIQUE COLLATE NOCASE,
    transaction_date TEXT NOT NULL,
    item_id INTEGER NOT NULL,
    warehouse_id INTEGER NOT NULL,
    transaction_type TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit_cost REAL,
    unit_sale_price REAL,
    expiry_date TEXT,
    description TEXT,
    journal_entry_id INTEGER UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- حقول إضافية للتكامل
    batch_number TEXT,
    serial_number TEXT,
    reference_document TEXT,
    reference_id INTEGER,
    cost_center_external_id TEXT,
    created_by_external_id TEXT,
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
);


-- جدول السياسات الرئيسية
CREATE TABLE IF NOT EXISTS policy_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    editable BOOLEAN DEFAULT 1,
    requires_approval BOOLEAN DEFAULT 0,
    default_scope TEXT DEFAULT 'عام',
    version TEXT DEFAULT '1.0',
    is_active BOOLEAN DEFAULT 1,
    created_by TEXT,
    updated_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- جدول تفاصيل السياسات
CREATE TABLE IF NOT EXISTS policy_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id INTEGER NOT NULL,
    setting_key TEXT NOT NULL,
    setting_value TEXT NOT NULL,
    data_type TEXT DEFAULT 'text',
    input_type TEXT DEFAULT 'textbox',
    is_required BOOLEAN DEFAULT 0,
    validation_rule TEXT,
    scope TEXT DEFAULT 'عام',
    effective_date DATE,
    expiry_date DATE,
    notes TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_by TEXT,
    updated_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(policy_id) REFERENCES policy_master(id) ON DELETE CASCADE
);

-- جدول وصف السياسات
CREATE TABLE IF NOT EXISTS policy_descriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_key TEXT NOT NULL,
    description TEXT NOT NULL
);

-- جدول أنواع الحسابات المخزنية
CREATE TABLE IF NOT EXISTS inventory_account_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);


-- جدول العملاء (مصحح)
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar TEXT NOT NULL,
    contact_person TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    is_active INTEGER DEFAULT 1,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    website TEXT,
    payment_terms TEXT,
    country TEXT,
    city TEXT,
    postal_code TEXT,
    account_id INTEGER,
    financial_policy_id INTEGER,
    inventory_policy_id INTEGER,
    credit_limit DECIMAL(10, 2),
    rating INTEGER,
    preferred_contact_method TEXT,
    delivery_address TEXT,
    external_account_id TEXT,
    external_system TEXT DEFAULT 'accounting',
    relation_type TEXT,
    extra_account_id INTEGER,
    tax_number TEXT,
    customer_category TEXT,
    payment_method TEXT,
    language TEXT DEFAULT 'ar',
    discount_policy TEXT,
    discount_percentage DECIMAL(5, 2),
    contract_start_date DATE,
    last_purchase_date DATE,
    is_verified INTEGER DEFAULT 0,
    customer_code TEXT
);

-- جدول طلبات الصرف
CREATE TABLE IF NOT EXISTS issue_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_number TEXT NOT NULL UNIQUE,
    request_date DATE NOT NULL,
    requester_external_id TEXT NOT NULL,
    department_id INTEGER NOT NULL,
    purpose TEXT,
    store_id INTEGER,
    priority TEXT DEFAULT 'normal' CHECK(priority IN ('low', 'normal', 'high', 'urgent')),
    required_date DATE,
    project_code TEXT,
    budget_code TEXT,
    cost_center_id INTEGER,
    total_estimated_cost REAL DEFAULT 0,
    total_actual_cost REAL DEFAULT 0,
    status TEXT DEFAULT 'pending',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- حقول الموافقة والتكامل
    approved_by_external_id TEXT,
    approved_at DATETIME,
    cost_center_external_id TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);


-- جدول أصناف طلبات الصرف
CREATE TABLE IF NOT EXISTS issue_request_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    notes TEXT,
    approved_quantity REAL DEFAULT 0,
    issued_quantity REAL DEFAULT 0,
    estimated_cost REAL DEFAULT 0,
    actual_cost REAL DEFAULT 0,
    status TEXT DEFAULT 'pending',
    priority TEXT DEFAULT 'normal',
    required_date TEXT,
    FOREIGN KEY (request_id) REFERENCES issue_requests(id),
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);


    -- إضافة الأعمدة المطلوبة لجدول أصناف طلبات الصرف
    priority TEXT DEFAULT 'normal',
    required_date DATE,
    estimated_cost REAL DEFAULT 0,
    actual_cost REAL DEFAULT 0,
    approved_quantity REAL DEFAULT 0,
    issued_quantity REAL DEFAULT 0,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'partially_issued', 'completed')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES issue_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);

-- جدول الجرد الفعلي
CREATE TABLE IF NOT EXISTS physical_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_number TEXT NOT NULL UNIQUE,
    inventory_date DATE NOT NULL,
    warehouse_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    counted_by_external_id INTEGER,
    verified_by_external_id INTEGER,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
);

-- جدول أصناف الجرد الفعلي
CREATE TABLE IF NOT EXISTS physical_inventory_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    system_quantity REAL NOT NULL,
    actual_quantity REAL NOT NULL,
    variance REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (inventory_id) REFERENCES physical_inventory(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);

-- جدول مزامنة البيانات
CREATE TABLE IF NOT EXISTS data_sync_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    external_system TEXT NOT NULL,
    external_id TEXT NOT NULL,
    sync_direction TEXT NOT NULL,
    sync_status TEXT DEFAULT 'pending',
    sync_date DATETIME,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(table_name, record_id, external_system)
);

-- جدول تعيين المراكز والتكاليف
CREATE TABLE IF NOT EXISTS cost_center_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    internal_reference TEXT NOT NULL,
    external_cost_center_id TEXT NOT NULL,
    external_system TEXT DEFAULT 'accounting',
    is_active INTEGER DEFAULT 1,
    mapping_date DATE DEFAULT CURRENT_DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(internal_reference, external_system)
);

-- جدول إعدادات التكامل
CREATE TABLE IF NOT EXISTS integration_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description TEXT,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- إنشاء الفهارس لتحسين الأداء
CREATE INDEX IF NOT EXISTS idx_items_category ON items(item_category_id);
CREATE INDEX IF NOT EXISTS idx_items_group ON items(item_group_id);
CREATE INDEX IF NOT EXISTS idx_items_base_unit ON items(base_unit_id);
CREATE INDEX IF NOT EXISTS idx_items_external ON items(external_item_id);
CREATE INDEX IF NOT EXISTS idx_item_units_item ON item_units(item_id);
CREATE INDEX IF NOT EXISTS idx_item_units_unit ON item_units(unit_id);
CREATE INDEX IF NOT EXISTS idx_purchase_requests_external ON purchase_requests(requester_external_id, cost_center_external_id);
CREATE INDEX IF NOT EXISTS idx_suppliers_external ON suppliers(external_account_id);
CREATE INDEX IF NOT EXISTS idx_customers_external ON customers(external_account_id);
CREATE INDEX IF NOT EXISTS idx_departments_external ON departments(external_department_id);
CREATE INDEX IF NOT EXISTS idx_stock_transactions_external ON stock_transactions(cost_center_external_id);
CREATE INDEX IF NOT EXISTS idx_stock_transactions_item ON stock_transactions(item_id);
CREATE INDEX IF NOT EXISTS idx_stock_transactions_warehouse ON stock_transactions(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_stock_transactions_date ON stock_transactions(transaction_date);

-- إدخال إعدادات التكامل الأساسية
INSERT OR IGNORE INTO integration_config (config_key, config_value, description) VALUES
('accounting_system_url', 'https://accounting.example.com/api', 'رابط نظام المحاسبة'),
('accounting_api_key', '', 'مفتاح API لنظام المحاسبة'),
('user_system_url', 'https://users.example.com/api', 'رابط نظام المستخدمين'),
('sync_interval_minutes', '30', 'فترة المزامنة بالدقائق'),
('last_sync_timestamp', '', 'آخر وقت مزامنة');

-- جدول إذونات الصرف
CREATE TABLE IF NOT EXISTS issue_permits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    permit_number TEXT NOT NULL UNIQUE,
    permit_date DATE DEFAULT CURRENT_DATE,
    request_id INTEGER NOT NULL,
    warehouse_id INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    issued_by_external_id TEXT NOT NULL,
    approved_by_external_id TEXT,
    issue_date TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'issued', 'completed', 'cancelled')),
    total_items INTEGER DEFAULT 0,
    total_quantity REAL DEFAULT 0,
    total_cost REAL DEFAULT 0,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES issue_requests(id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- جدول أصناف إذونات الصرف
CREATE TABLE IF NOT EXISTS issue_permit_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    permit_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    request_item_id INTEGER NOT NULL,
    requested_quantity REAL NOT NULL,
    issued_quantity REAL NOT NULL DEFAULT 0,
    unit_id INTEGER NOT NULL,
    unit_cost REAL DEFAULT 0,
    total_cost REAL DEFAULT 0,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'issued', 'partially_issued', 'completed', 'cancelled')),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (permit_id) REFERENCES issue_permits(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (request_item_id) REFERENCES issue_request_items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);

-- جدول موافقات طلبات الصرف
CREATE TABLE IF NOT EXISTS issue_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    approver_external_id TEXT NOT NULL,
    approval_level INTEGER DEFAULT 1,
    approval_status TEXT NOT NULL CHECK(approval_status IN ('pending', 'approved', 'rejected', 'cancelled')),
    approval_date DATETIME,
    comments TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES issue_requests(id) ON DELETE CASCADE
);

-- جدول تعقب حالة إذونات الصرف
CREATE TABLE IF NOT EXISTS permit_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    permit_id INTEGER NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_by_external_id TEXT NOT NULL,
    change_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (permit_id) REFERENCES issue_permits(id) ON DELETE CASCADE
);

-- ================================================================
-- جداول التحويلات والارتجاع الجديدة
-- ================================================================

-- جدول أذونات التحويل بين الأقسام
CREATE TABLE IF NOT EXISTS department_transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_number TEXT NOT NULL UNIQUE,
    transfer_date DATE NOT NULL,
    from_department_id INTEGER NOT NULL,
    to_department_id INTEGER NOT NULL,
    warehouse_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending', -- (pending, completed, cancelled)
    notes TEXT,
    created_by_external_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_department_id) REFERENCES departments(id),
    FOREIGN KEY (to_department_id) REFERENCES departments(id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
);

CREATE TABLE IF NOT EXISTS department_transfer_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    notes TEXT,
    FOREIGN KEY (transfer_id) REFERENCES department_transfers(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);

-- جدول أذونات الارتجاع من الأقسام
CREATE TABLE IF NOT EXISTS department_returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_number TEXT NOT NULL UNIQUE,
    return_date DATE NOT NULL,
    from_department_id INTEGER NOT NULL,
    to_warehouse_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    reason TEXT,
    created_by_external_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_department_id) REFERENCES departments(id),
    FOREIGN KEY (to_warehouse_id) REFERENCES warehouses(id)
);

CREATE TABLE IF NOT EXISTS department_return_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    notes TEXT,
    FOREIGN KEY (return_id) REFERENCES department_returns(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);

-- جدول أذونات الارتجاع للمورد
CREATE TABLE IF NOT EXISTS supplier_returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_number TEXT NOT NULL UNIQUE,
    return_date DATE NOT NULL,
    supplier_id INTEGER NOT NULL,
    from_warehouse_id INTEGER NOT NULL,
    purchase_invoice_ref TEXT, -- رقم فاتورة الشراء المرجعية
    status TEXT DEFAULT 'pending',
    reason TEXT,
    created_by_external_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (from_warehouse_id) REFERENCES warehouses(id)
);

CREATE TABLE IF NOT EXISTS supplier_return_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    purchase_price REAL, -- سعر الشراء وقت الإرجاع
    notes TEXT,
    FOREIGN KEY (return_id) REFERENCES supplier_returns(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);

-- جدول حركات الصرف الفعلية
CREATE TABLE IF NOT EXISTS issue_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    permit_id INTEGER NOT NULL,
    permit_item_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    unit_cost REAL DEFAULT 0,
    total_cost REAL DEFAULT 0,
    issued_by_external_id TEXT NOT NULL,
    issued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    received_by_external_id TEXT,
    received_at DATETIME,
    status TEXT DEFAULT 'issued' CHECK(status IN ('issued', 'received', 'cancelled')),
    notes TEXT,
    FOREIGN KEY (permit_id) REFERENCES issue_permits(id),
    FOREIGN KEY (permit_item_id) REFERENCES issue_permit_items(id),
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);

-- إنشاء الفهارس لتحسين الأداء
CREATE INDEX IF NOT EXISTS idx_issue_requests_status ON issue_requests(status);
CREATE INDEX IF NOT EXISTS idx_issue_requests_department ON issue_requests(department_id);
CREATE INDEX IF NOT EXISTS idx_issue_requests_priority ON issue_requests(priority);
CREATE INDEX IF NOT EXISTS idx_issue_request_items_status ON issue_request_items(status);
CREATE INDEX IF NOT EXISTS idx_issue_permits_request ON issue_permits(request_id);
CREATE INDEX IF NOT EXISTS idx_issue_permits_warehouse ON issue_permits(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_issue_permits_status ON issue_permits(status);
CREATE INDEX IF NOT EXISTS idx_issue_approvals_request ON issue_approvals(request_id);
CREATE INDEX IF NOT EXISTS idx_issue_transactions_permit ON issue_transactions(permit_id);

"""
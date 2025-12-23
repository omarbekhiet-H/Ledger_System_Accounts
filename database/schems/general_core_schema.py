# database/schems/general_core_schema.py

GENERAL_CORE_SCHEMA_SCRIPT = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    customer_name_ar TEXT NOT NULL UNIQUE,
    customer_name_en TEXT,
    contact_person TEXT,
    phone TEXT,
    email TEXT UNIQUE COLLATE NOCASE,
    address TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    vendor_name_ar TEXT NOT NULL UNIQUE,
    vendor_name_en TEXT,
    contact_person TEXT,
    phone TEXT,
    email TEXT UNIQUE COLLATE NOCASE,
    address TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT NOT NULL UNIQUE COLLATE NOCASE,
    setting_value TEXT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""
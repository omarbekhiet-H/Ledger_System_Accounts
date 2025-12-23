# database/schemas/users_schema.py

USERS_SCHEMA_SCRIPT = """
-- جدول أنواع البيانات المرجعية
CREATE TABLE IF NOT EXISTS lookup_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name_ar TEXT NOT NULL UNIQUE,
    type_name_en TEXT UNIQUE,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- جدول القيم المرجعية (مكمل للـ lookup_types)
CREATE TABLE IF NOT EXISTS lookup_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lookup_type_id INTEGER NOT NULL,
    code TEXT NOT NULL COLLATE NOCASE,
    value_ar TEXT NOT NULL,
    value_en TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lookup_type_id) REFERENCES lookup_types(id) ON DELETE CASCADE,
    UNIQUE (lookup_type_id, code)
);

-- جدول الأقسام
CREATE TABLE IF NOT EXISTS department_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name_ar TEXT NOT NULL UNIQUE,
    name_en TEXT UNIQUE,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- جدول الأدوار
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name_ar TEXT NOT NULL UNIQUE,
    name_en TEXT UNIQUE,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- جدول المستخدمين
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    name_ar TEXT,
    name_en TEXT,
    email TEXT UNIQUE COLLATE NOCASE,
    phone TEXT,
    department_type_id INTEGER,
    profile_image_url TEXT,
    address TEXT,
    gender_id INTEGER, -- من lookup_values
    preferred_language_id INTEGER, -- من lookup_values
    default_role_id INTEGER, -- من جدول roles
    last_login DATETIME,
    failed_login_attempts INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    updated_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_type_id) REFERENCES department_types(id),
    FOREIGN KEY (gender_id) REFERENCES lookup_values(id),
    FOREIGN KEY (preferred_language_id) REFERENCES lookup_values(id),
    FOREIGN KEY (default_role_id) REFERENCES roles(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id)
);



-- جدول الوحدات/الموديولات
CREATE TABLE IF NOT EXISTS modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name_ar TEXT NOT NULL,
    name_en TEXT,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- جدول الصلاحيات
CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    permission_code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name_ar TEXT NOT NULL UNIQUE,
    name_en TEXT UNIQUE,
    description TEXT,
    module_id INTEGER,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(id)
);

-- جدول ربط المستخدمين بالأدوار
CREATE TABLE IF NOT EXISTS user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE (user_id, role_id)
);

-- جدول ربط الأدوار بالصلاحيات
CREATE TABLE IF NOT EXISTS role_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE (role_id, permission_id)
);

-- جدول تعيينات واجهة المستخدم
CREATE TABLE IF NOT EXISTS ui_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    form_name TEXT NOT NULL,
    ui_element_id TEXT NOT NULL,
    db_table TEXT,
    db_column TEXT,
    display_label_ar TEXT,
    control_type TEXT,
    lookup_type_id INTEGER,
    required_permission_id INTEGER,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lookup_type_id) REFERENCES lookup_types(id),
    FOREIGN KEY (required_permission_id) REFERENCES permissions(id)
);

-- جدول سجلات الدخول
CREATE TABLE IF NOT EXISTS login_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,
    success INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- جدول النشاطات العامة
CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT,
    target_table TEXT,
    target_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- جدول جلسات المستخدم
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    session_token TEXT UNIQUE,
    login_time DATETIME,
    logout_time DATETIME,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

"""
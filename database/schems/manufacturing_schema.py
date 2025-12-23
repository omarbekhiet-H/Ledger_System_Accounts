MANUFACTURING_SCHEMA_SCRIPT = """
-- ================================================================
-- جداول أوامر التشغيل (Job Orders)
-- ================================================================

-- جدول أوامر التشغيل الرئيسي
CREATE TABLE IF NOT EXISTS job_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_number TEXT NOT NULL UNIQUE,
    job_title TEXT NOT NULL,
    job_description TEXT,
    job_type TEXT NOT NULL,
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'urgent')),
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'planned', 'in_progress', 'on_hold', 'completed', 'cancelled')),
    
    -- معلومات العميل/القسم الطالب
    requested_by_department_id INTEGER,
    requested_by_external_id TEXT,
    customer_id INTEGER,
    
    -- معلومات التنفيذ
    assigned_to_department_id INTEGER,
    assigned_to_external_id TEXT,
    supervisor_external_id TEXT,
    
    -- التواريخ
    request_date DATE NOT NULL,
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    due_date DATE,
    
    -- التكاليف
    estimated_cost REAL DEFAULT 0,
    actual_cost REAL DEFAULT 0,
    budget REAL DEFAULT 0,
    
    -- الموقع والمستودع
    location_id INTEGER,
    warehouse_id INTEGER,
    
    -- معلومات إضافية
    project_code TEXT,
    work_order_ref TEXT,
    required_skills TEXT,
    actual_quantity_used REAL DEFAULT 0,
    stock_status TEXT DEFAULT 'pending',
    safety_requirements TEXT,
    quality_standards TEXT,
    
    -- التكامل مع الأنظمة
    external_job_id TEXT,
    external_system TEXT DEFAULT 'production',
    
    is_active INTEGER DEFAULT 1,
    created_by_external_id TEXT,
    updated_by_external_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- جدول متطلبات المواد لأوامر التشغيل
CREATE TABLE IF NOT EXISTS job_order_material_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_order_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity_required REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    estimated_cost REAL DEFAULT 0,
    actual_cost REAL DEFAULT 0,
    
    -- حالة التوريد
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'reserved', 'issued', 'consumed', 'cancelled', 'correction')),
    issued_quantity REAL DEFAULT 0,
    consumed_quantity REAL DEFAULT 0,
    
    -- معلومات التوقيت
    required_date DATE,
    issued_date DATE,
    consumed_date DATE,
    approved_date DATE,
    
    -- معلومات إضافية
    notes TEXT,
    priority TEXT DEFAULT 'medium',
    is_critical INTEGER DEFAULT 0,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (job_order_id) REFERENCES job_orders(id) ON DELETE CASCADE
);

-- جدول إصدار المواد لأوامر التشغيل
CREATE TABLE IF NOT EXISTS job_order_material_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_order_id INTEGER NOT NULL,
    material_requirement_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity_issued REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    unit_cost REAL DEFAULT 0,
    total_cost REAL DEFAULT 0,
    
    -- معلومات الإصدار
    issued_by_external_id TEXT NOT NULL,
    issued_from_warehouse_id INTEGER NOT NULL,
    issued_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    batch_number TEXT,
    serial_number TEXT,
    
    -- حالة الاستهلاك
    consumption_status TEXT DEFAULT 'issued' CHECK(consumption_status IN ('issued', 'partially_consumed', 'fully_consumed', 'returned')),
    consumed_quantity REAL DEFAULT 0,
    returned_quantity REAL DEFAULT 0,
    
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (job_order_id) REFERENCES job_orders(id),
    FOREIGN KEY (material_requirement_id) REFERENCES job_order_material_requirements(id)
);

-- جدول استهلاك المواد في أوامر التشغيل
CREATE TABLE IF NOT EXISTS job_order_material_consumption (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_order_id INTEGER NOT NULL,
    material_issue_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity_consumed REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    consumption_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- معلومات الاستهلاك
    consumed_by_external_id TEXT,
    work_center TEXT,
    operation_number TEXT,
    step_number INTEGER,
    
    -- الجودة والتحكم
    quality_check_passed INTEGER DEFAULT 1,
    quality_notes TEXT,
    waste_quantity REAL DEFAULT 0,
    waste_reason TEXT,
    
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (job_order_id) REFERENCES job_orders(id),
    FOREIGN KEY (material_issue_id) REFERENCES job_order_material_issues(id)
);

-- جدول إرجاع المواد من أوامر التشغيل
CREATE TABLE IF NOT EXISTS job_order_material_returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_order_id INTEGER NOT NULL,
    material_issue_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity_returned REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    return_reason TEXT,
    
    -- معلومات الإرجاع
    returned_to_warehouse_id INTEGER,
    returned_by_external_id TEXT,
    return_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    condition TEXT CHECK(condition IN ('good', 'damaged', 'expired', 'defective')),
    
    -- التكاليف
    estimated_value REAL DEFAULT 0,
    actual_value REAL DEFAULT 0,
    
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (job_order_id) REFERENCES job_orders(id),
    FOREIGN KEY (material_issue_id) REFERENCES job_order_material_issues(id)
);

-- جدول المخرجات والمنتجات لأوامر التشغيل
CREATE TABLE IF NOT EXISTS job_order_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_order_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity_produced REAL NOT NULL,
    unit_id INTEGER NOT NULL,
    
    -- جودة المخرجات
    quality_status TEXT DEFAULT 'pending' CHECK(quality_status IN ('pending', 'passed', 'failed', 'rework')),
    quality_inspector_external_id TEXT,
    quality_inspection_date DATETIME,
    quality_notes TEXT,
    
    -- التخزين
    stored_quantity REAL DEFAULT 0,
    stored_in_warehouse_id INTEGER,
    storage_date DATETIME,
    
    -- التكاليف
    production_cost REAL DEFAULT 0,
    unit_production_cost REAL DEFAULT 0,
    
    production_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_by_external_id TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (job_order_id) REFERENCES job_orders(id) ON DELETE CASCADE
);

-- جدول مراحل وتقدم أوامر التشغيل
CREATE TABLE IF NOT EXISTS job_order_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_order_id INTEGER NOT NULL,
    progress_percentage INTEGER NOT NULL CHECK(progress_percentage >= 0 AND progress_percentage <= 100),
    current_stage TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('not_started', 'in_progress', 'completed', 'on_hold')),
    
    -- معلومات المرحلة
    stage_start_date DATETIME,
    stage_end_date DATETIME,
    stage_duration_hours REAL,
    estimated_stage_hours REAL,
    
    -- الموارد
    manpower_count INTEGER DEFAULT 0,
    equipment_used TEXT,
    issues_encountered TEXT,
    solutions_applied TEXT,
    
    reported_by_external_id TEXT NOT NULL,
    report_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (job_order_id) REFERENCES job_orders(id) ON DELETE CASCADE
);

-- جدول الموارد البشرية لأوامر التشغيل
CREATE TABLE IF NOT EXISTS job_order_labor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_order_id INTEGER NOT NULL,
    external_employee_id TEXT NOT NULL,
    
    -- معلومات العامل
    role TEXT NOT NULL,
    assigned_hours REAL DEFAULT 0,
    actual_hours_worked REAL DEFAULT 0,
    hourly_rate REAL DEFAULT 0,
    labor_cost REAL DEFAULT 0,
    
    -- التوقيت
    assignment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    start_time DATETIME,
    end_time DATETIME,
    
    -- الأداء
    productivity_rating INTEGER CHECK(productivity_rating >= 1 AND productivity_rating <= 5),
    notes TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (job_order_id) REFERENCES job_orders(id) ON DELETE CASCADE
);

-- جدول معدات وأدوات أوامر التشغيل
CREATE TABLE IF NOT EXISTS job_order_equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_order_id INTEGER NOT NULL,
    equipment_id TEXT NOT NULL,
    equipment_name TEXT NOT NULL,
    
    -- معلومات الاستخدام
    planned_usage_hours REAL DEFAULT 0,
    actual_usage_hours REAL DEFAULT 0,
    hourly_cost_rate REAL DEFAULT 0,
    total_equipment_cost REAL DEFAULT 0,
    
    -- التوقيت
    assignment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    start_time DATETIME,
    end_time DATETIME,
    
    -- الصيانة والحالة
    maintenance_required INTEGER DEFAULT 0,
    condition_notes TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (job_order_id) REFERENCES job_orders(id) ON DELETE CASCADE
);

-- جدول التكاليف الإضافية لأوامر التشغيل
CREATE TABLE IF NOT EXISTS job_order_additional_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_order_id INTEGER NOT NULL,
    cost_type TEXT NOT NULL,
    cost_description TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    exchange_rate REAL DEFAULT 1.0,
    
    cost_date DATE,
    vendor_name TEXT,
    reference_number TEXT,
    is_billable INTEGER DEFAULT 1,
    
    created_by_external_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (job_order_id) REFERENCES job_orders(id) ON DELETE CASCADE
);

-- جدول المرفقات والوثائق لأوامر التشغيل
CREATE TABLE IF NOT EXISTS job_order_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_order_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER,
    description TEXT,
    
    uploaded_by_external_id TEXT NOT NULL,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (job_order_id) REFERENCES job_orders(id) ON DELETE CASCADE
);

-- جدول تعليقات وملاحظات أوامر التشغيل
CREATE TABLE IF NOT EXISTS job_order_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_order_id INTEGER NOT NULL,
    comment_text TEXT NOT NULL,
    comment_type TEXT DEFAULT 'general' CHECK(comment_type IN ('general', 'technical', 'quality', 'safety')),
    
    commented_by_external_id TEXT NOT NULL,
    comment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    is_internal INTEGER DEFAULT 0,
    requires_action INTEGER DEFAULT 0,
    action_taken INTEGER DEFAULT 0,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (job_order_id) REFERENCES job_orders(id) ON DELETE CASCADE
);

-- إنشاء الفهارس لتحسين أداء أوامر التشغيل
CREATE INDEX IF NOT EXISTS idx_job_orders_number ON job_orders(job_number);
CREATE INDEX IF NOT EXISTS idx_job_orders_status ON job_orders(status);
CREATE INDEX IF NOT EXISTS idx_job_orders_type ON job_orders(job_type);
CREATE INDEX IF NOT EXISTS idx_job_orders_dates ON job_orders(planned_start_date, planned_end_date, actual_start_date, actual_end_date);

CREATE INDEX IF NOT EXISTS idx_job_materials_job ON job_order_material_requirements(job_order_id);
CREATE INDEX IF NOT EXISTS idx_job_materials_item ON job_order_material_requirements(item_id);
CREATE INDEX IF NOT EXISTS idx_job_materials_status ON job_order_material_requirements(status);

CREATE INDEX IF NOT EXISTS idx_job_issues_job ON job_order_material_issues(job_order_id);
CREATE INDEX IF NOT EXISTS idx_job_issues_material ON job_order_material_issues(material_requirement_id);

CREATE INDEX IF NOT EXISTS idx_job_consumption_job ON job_order_material_consumption(job_order_id);
CREATE INDEX IF NOT EXISTS idx_job_consumption_issue ON job_order_material_consumption(material_issue_id);

CREATE INDEX IF NOT EXISTS idx_job_outputs_job ON job_order_outputs(job_order_id);
CREATE INDEX IF NOT EXISTS idx_job_outputs_item ON job_order_outputs(item_id);

CREATE INDEX IF NOT EXISTS idx_job_progress_job ON job_order_progress(job_order_id);
CREATE INDEX IF NOT EXISTS idx_job_progress_status ON job_order_progress(status);

CREATE INDEX IF NOT EXISTS idx_job_labor_job ON job_order_labor(job_order_id);
CREATE INDEX IF NOT EXISTS idx_job_equipment_job ON job_order_equipment(job_order_id);
CREATE INDEX IF NOT EXISTS idx_job_costs_job ON job_order_additional_costs(job_order_id);
CREATE INDEX IF NOT EXISTS idx_job_attachments_job ON job_order_attachments(job_order_id);
CREATE INDEX IF NOT EXISTS idx_job_comments_job ON job_order_comments(job_order_id);
"""
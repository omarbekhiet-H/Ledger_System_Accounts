import sqlite3

def insert_sample_policies(db_path="inventory.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # إنشاء جدول المقترحات إن لم يكن موجود
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS policy_descriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_key TEXT NOT NULL,
        description TEXT NOT NULL
    )
    """)

    sample_policies = [
        ("sale_issue_evaluation", "تقييم المنصرف للبيع", "مخزنية", "يتم التقييم باستخدام متوسط التكلفة"),
        ("internal_issue_evaluation", "تقييم المنصرف للأقسام", "مخزنية", "يتم التقييم حسب التكلفة الفعلية"),
        ("stock_evaluation", "تقييم المخزون", "مخزنية", "يتم التقييم باستخدام FIFO"),
    ]

    policy_descriptions = {
        "sale_issue_evaluation": [
            "متوسط التكلفة", "آخر سعر شراء", "سعر البيع المتوقع"
        ],
        "internal_issue_evaluation": [
            "التكلفة الفعلية", "تكلفة القسم", "تكلفة التشغيل"
        ],
        "stock_evaluation": [
            "FIFO", "LIFO", "متوسط مرجح", "التكلفة التاريخية"
        ]
    }

    for key, name, category, desc in sample_policies:
        cursor.execute("""
        INSERT OR IGNORE INTO policy_master (key, name, category, description, is_active)
        VALUES (?, ?, ?, ?, 1)
        """, (key, name, category, desc))

        # إدخال المقترحات الخاصة بالوصف
        for suggestion in policy_descriptions.get(key, []):
            cursor.execute("""
            INSERT INTO policy_descriptions (policy_key, description)
            VALUES (?, ?)
            """, (key, suggestion))

    conn.commit()
    conn.close()
    print("✅ تم إدخال السياسات والمقترحات بنجاح")

if __name__ == "__main__":
    insert_sample_policies()
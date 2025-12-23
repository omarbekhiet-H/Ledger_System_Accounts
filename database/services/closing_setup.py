# database/services/closing_setup.py

import sqlite3

class ClosingSetupService:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def setup_default_closure_steps(self):
        """إعداد إجراءات الإقفال الافتراضية"""
        steps = [
            ('جرد المخزون', 'inventory_count'),
            ('المطابقة البنكية', 'bank_reconciliation'),
            ('تأكيد المدينون', 'receivables_confirmation'),
            ('تأكيد الدائنون', 'payables_confirmation'),
            ('جرد الأصول الثابتة', 'fixed_assets_count'),
            ('مراجعة المصروفات المستحقة', 'accrued_expenses_review'),
            ('مراجعة الإيرادات المستحقة', 'accrued_revenues_review')
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # الحصول على جميع السنوات المالية
        cursor.execute("SELECT id FROM financial_years WHERE is_closed = 0")
        open_years = cursor.fetchall()
        
        for year_id, in open_years:
            for step_name_ar, step_name_en in steps:
                cursor.execute("""
                    INSERT OR IGNORE INTO financial_closures 
                    (financial_year_id, step_name, status)
                    VALUES (?, ?, 'pending')
                """, (year_id, step_name_ar))
        
        conn.commit()
        conn.close()
    
    def initialize_financial_year(self, year_name: str, start_date: str, end_date: str,
                                revenues_account_id: int, expenses_account_id: int,
                                retained_earnings_account_id: int, legal_reserve_account_id: int,
                                income_tax_account_id: int, solidarity_tax_account_id: int,
                                income_tax_percent: float = 22.5, 
                                solidarity_tax_percent: float = 2.5,
                                legal_reserve_percent: float = 10.0) -> int:
        """تهيئة سنة مالية جديدة"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO financial_years (
                year_name, start_date, end_date,
                revenues_account_id, expenses_account_id,
                retained_earnings_account_id, legal_reserve_account_id,
                income_tax_account_id, solidarity_tax_account_id,
                income_tax_percent, solidarity_tax_percent, legal_reserve_percent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            year_name, start_date, end_date,
            revenues_account_id, expenses_account_id,
            retained_earnings_account_id, legal_reserve_account_id,
            income_tax_account_id, solidarity_tax_account_id,
            income_tax_percent, solidarity_tax_percent, legal_reserve_percent
        ))
        
        year_id = cursor.lastrowid
        
        # إعداد إجراءات الإقفال
        self.setup_default_closure_steps()
        
        conn.commit()
        conn.close()
        
        return year_id

# نموذج للاستخدام
if __name__ == "__main__":
    setup_service = ClosingSetupService('financial_database.db')
    
    # تهيئة سنة مالية جديدة
    year_id = setup_service.initialize_financial_year(
        year_name="2024",
        start_date="2024-01-01",
        end_date="2024-12-31",
        revenues_account_id=4001,
        expenses_account_id=5001,
        retained_earnings_account_id=3001,
        legal_reserve_account_id=3002,
        income_tax_account_id=2001,
        solidarity_tax_account_id=2002
    )
    
    print(f"تم إنشاء السنة المالية برقم: {year_id}")
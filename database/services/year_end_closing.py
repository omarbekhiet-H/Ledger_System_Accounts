# database/services/year_end_closing.py

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class YearEndClosingService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def create_connection(self):
        """إنشاء اتصال بقاعدة البيانات"""
        return sqlite3.connect(self.db_path)
    
    def get_financial_year(self, year_id: int) -> Optional[Dict]:
        """الحصول على بيانات السنة المالية"""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM financial_years 
            WHERE id = ?
        """, (year_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    def validate_year_for_closing(self, year_id: int) -> Tuple[bool, List[str]]:
        """التحقق من إمكانية إقفال السنة المالية"""
        errors = []
        conn = self.create_connection()
        cursor = conn.cursor()
        
        # التحقق من وجود قيود غير معتمدة
        cursor.execute("""
            SELECT COUNT(*) as pending_count
            FROM journal_entries 
            WHERE entry_date BETWEEN 
                (SELECT start_date FROM financial_years WHERE id = ?)
                AND 
                (SELECT end_date FROM financial_years WHERE id = ?)
            AND status != 'Approved'
        """, (year_id, year_id))
        
        pending_count = cursor.fetchone()['pending_count']
        if pending_count > 0:
            errors.append(f"يوجد {pending_count} قيود غير معتمدة")
        
        # التحقق من اكتمال إجراءات الإقفال
        cursor.execute("""
            SELECT COUNT(*) as incomplete_count
            FROM financial_closures 
            WHERE financial_year_id = ? AND status != 'completed'
        """, (year_id,))
        
        incomplete_count = cursor.fetchone()['incomplete_count']
        if incomplete_count > 0:
            errors.append(f"يوجد {incomplete_count} إجراءات إقفال غير مكتملة")
        
        conn.close()
        return len(errors) == 0, errors
    
    def calculate_net_profit(self, year_id: int) -> float:
        """حساب صافي الربح أو الخسارة"""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        # حساب إجمالي الإيرادات (حسابات 4xxxx)
        cursor.execute("""
            SELECT COALESCE(SUM(jel.credit - jel.debit), 0) as total_revenues
            FROM journal_entry_lines jel
            JOIN accounts a ON jel.account_id = a.id
            JOIN journal_entries je ON jel.journal_entry_id = je.id
            WHERE je.entry_date BETWEEN 
                (SELECT start_date FROM financial_years WHERE id = ?)
                AND 
                (SELECT end_date FROM financial_years WHERE id = ?)
            AND a.acc_code LIKE '4%'
            AND je.status = 'Approved'
        """, (year_id, year_id))
        
        total_revenues = cursor.fetchone()['total_revenues'] or 0
        
        # حساب إجمالي المصروفات (حسابات 5xxxx)
        cursor.execute("""
            SELECT COALESCE(SUM(jel.debit - jel.credit), 0) as total_expenses
            FROM journal_entry_lines jel
            JOIN accounts a ON jel.account_id = a.id
            JOIN journal_entries je ON jel.journal_entry_id = je.id
            WHERE je.entry_date BETWEEN 
                (SELECT start_date FROM financial_years WHERE id = ?)
                AND 
                (SELECT end_date FROM financial_years WHERE id = ?)
            AND a.acc_code LIKE '5%'
            AND je.status = 'Approved'
        """, (year_id, year_id))
        
        total_expenses = cursor.fetchone()['total_expenses'] or 0
        
        conn.close()
        return total_revenues - total_expenses
    
    def calculate_taxes(self, year_id: int, net_profit: float) -> Dict[str, float]:
        """حساب الضرائب المستحقة"""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT income_tax_percent, solidarity_tax_percent,
                   income_tax_account_id, solidarity_tax_account_id
            FROM financial_years 
            WHERE id = ?
        """, (year_id,))
        
        tax_info = cursor.fetchone()
        conn.close()
        
        income_tax = net_profit * (tax_info['income_tax_percent'] / 100) if tax_info['income_tax_percent'] else 0
        solidarity_tax = net_profit * (tax_info['solidarity_tax_percent'] / 100) if tax_info['solidarity_tax_percent'] else 0
        
        return {
            'income_tax': income_tax,
            'solidarity_tax': solidarity_tax,
            'total_tax': income_tax + solidarity_tax,
            'income_tax_account_id': tax_info['income_tax_account_id'],
            'solidarity_tax_account_id': tax_info['solidarity_tax_account_id']
        }
    
    def calculate_legal_reserve(self, year_id: int, profit_after_tax: float) -> float:
        """حساب الاحتياطي القانوني"""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT legal_reserve_percent, legal_reserve_account_id
            FROM financial_years 
            WHERE id = ?
        """, (year_id,))
        
        reserve_info = cursor.fetchone()
        conn.close()
        
        legal_reserve = profit_after_tax * (reserve_info['legal_reserve_percent'] / 100) if reserve_info['legal_reserve_percent'] else 0
        return legal_reserve
    
    def create_closing_journal_entry(self, year_id: int, user_id: int) -> int:
        """إنشاء قيد إقفال السنة المالية"""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        # الحصول على بيانات السنة
        year_data = self.get_financial_year(year_id)
        net_profit = self.calculate_net_profit(year_id)
        taxes = self.calculate_taxes(year_id, net_profit)
        profit_after_tax = net_profit - taxes['total_tax']
        legal_reserve = self.calculate_legal_reserve(year_id, profit_after_tax)
        final_profit = profit_after_tax - legal_reserve
        
        # إنشاء رقم قيد فريد
        entry_number = f"CLS-{year_data['year_name']}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # إدخال قيد الإقفال الرئيسي
        cursor.execute("""
            INSERT INTO journal_entries (
                entry_number, entry_date, description,
                currency_id, exchange_rate, total_debit, total_credit, status
            ) VALUES (?, ?, ?, 1, 1.0, ?, ?, 'Approved')
        """, (
            entry_number,
            year_data['end_date'],
            f"قيد إقفال السنة المالية {year_data['year_name']}",
            net_profit,
            net_profit
        ))
        
        journal_entry_id = cursor.lastrowid
        
        # إدخال بنود قيد الإقفال
        self._create_closing_entries(cursor, journal_entry_id, year_data, net_profit, taxes, legal_reserve, final_profit)
        
        # تحديث السنة المالية بقيد الإقفال
        cursor.execute("""
            UPDATE financial_years 
            SET closing_entry_id = ?, is_closed = 1,
                closed_at = CURRENT_TIMESTAMP, closed_by_user_id = ?
            WHERE id = ?
        """, (journal_entry_id, user_id, year_id))
        
        conn.commit()
        conn.close()
        
        return journal_entry_id
    
    def _create_closing_entries(self, cursor, journal_entry_id: int, year_data: Dict, 
                               net_profit: float, taxes: Dict, legal_reserve: float, final_profit: float):
        """إنشاء البنود التفصيلية لقيد الإقفال"""
        
        # 1. إقفال حسابات الإيرادات
        cursor.execute("""
            INSERT INTO journal_entry_lines (
                journal_entry_id, account_id, debit, credit, notes
            ) VALUES (?, ?, 0, ?, 'إقفال حساب الإيرادات')
        """, (journal_entry_id, year_data['revenues_account_id'], net_profit + taxes['total_tax']))
        
        # 2. إقفال حسابات المصروفات
        cursor.execute("""
            INSERT INTO journal_entry_lines (
                journal_entry_id, account_id, debit, credit, notes
            ) VALUES (?, ?, ?, 0, 'إقفال حساب المصروفات')
        """, (journal_entry_id, year_data['expenses_account_id'], net_profit + taxes['total_tax']))
        
        # 3. تسجيل ضريبة الدخل
        if taxes['income_tax'] > 0:
            cursor.execute("""
                INSERT INTO journal_entry_lines (
                    journal_entry_id, account_id, debit, credit, notes
                ) VALUES (?, ?, ?, 0, 'ضريبة دخل')
            """, (journal_entry_id, year_data['income_tax_account_id'], taxes['income_tax']))
        
        # 4. تسجيل الضريبة التضامنية
        if taxes['solidarity_tax'] > 0:
            cursor.execute("""
                INSERT INTO journal_entry_lines (
                    journal_entry_id, account_id, debit, credit, notes
                ) VALUES (?, ?, ?, 0, 'ضريبة تضامنية')
            """, (journal_entry_id, year_data['solidarity_tax_account_id'], taxes['solidarity_tax']))
        
        # 5. تسجيل الاحتياطي القانوني
        if legal_reserve > 0:
            cursor.execute("""
                INSERT INTO journal_entry_lines (
                    journal_entry_id, account_id, debit, credit, notes
                ) VALUES (?, ?, ?, 0, 'الاحتياطي القانوني')
            """, (journal_entry_id, year_data['legal_reserve_account_id'], legal_reserve))
        
        # 6. تحويل الأرباح إلى الأرباح المرحلة
        if final_profit > 0:
            cursor.execute("""
                INSERT INTO journal_entry_lines (
                    journal_entry_id, account_id, debit, credit, notes
                ) VALUES (?, ?, ?, 0, 'تحويل الأرباح إلى الأرباح المرحلة')
            """, (journal_entry_id, year_data['retained_earnings_account_id'], final_profit))
    
    def execute_year_closing(self, year_id: int, user_id: int) -> Dict:
        """تنفيذ عملية الإقفال السنوي الكاملة"""
        try:
            # التحقق من إمكانية الإقفال
            can_close, errors = self.validate_year_for_closing(year_id)
            if not can_close:
                return {
                    'success': False,
                    'message': 'لا يمكن إقفال السنة المالية',
                    'errors': errors
                }
            
            # إنشاء قيد الإقفال
            journal_entry_id = self.create_closing_journal_entry(year_id, user_id)
            
            # تحديث حالة الإجراءات كمنتهية
            self._mark_closure_steps_completed(year_id)
            
            return {
                'success': True,
                'message': 'تم إقفال السنة المالية بنجاح',
                'journal_entry_id': journal_entry_id,
                'year_id': year_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'فشل في إقفال السنة المالية: {str(e)}',
                'errors': [str(e)]
            }
    
    def _mark_closure_steps_completed(self, year_id: int):
        """تحديث جميع إجراءات الإقفال كمكتملة"""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE financial_closures 
            SET status = 'completed', executed_at = CURRENT_TIMESTAMP
            WHERE financial_year_id = ?
        """, (year_id,))
        
        conn.commit()
        conn.close()
    
    def get_closing_summary(self, year_id: int) -> Dict:
        """الحصول على ملخص عملية الإقفال"""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        # حساب الأرقام
        net_profit = self.calculate_net_profit(year_id)
        taxes = self.calculate_taxes(year_id, net_profit)
        profit_after_tax = net_profit - taxes['total_tax']
        legal_reserve = self.calculate_legal_reserve(year_id, profit_after_tax)
        final_profit = profit_after_tax - legal_reserve
        
        # الحصول على معلومات السنة
        cursor.execute("""
            SELECT year_name, start_date, end_date, is_closed,
                   closed_at, u.full_name as closed_by
            FROM financial_years fy
            LEFT JOIN users u ON fy.closed_by_user_id = u.id
            WHERE fy.id = ?
        """, (year_id,))
        
        year_info = cursor.fetchone()
        
        # الحصول على إجراءات الإقفال
        cursor.execute("""
            SELECT step_name, status, executed_at
            FROM financial_closures 
            WHERE financial_year_id = ?
            ORDER BY id
        """, (year_id,))
        
        closure_steps = cursor.fetchall()
        
        conn.close()
        
        return {
            'year_info': dict(year_info) if year_info else {},
            'financial_results': {
                'net_profit': net_profit,
                'income_tax': taxes['income_tax'],
                'solidarity_tax': taxes['solidarity_tax'],
                'total_tax': taxes['total_tax'],
                'profit_after_tax': profit_after_tax,
                'legal_reserve': legal_reserve,
                'final_profit': final_profit
            },
            'closure_steps': [dict(step) for step in closure_steps]
        }
    
    def reopen_financial_year(self, year_id: int, user_id: int) -> bool:
        """إعادة فتح سنة مالية مغلقة"""
        try:
            conn = self.create_connection()
            cursor = conn.cursor()
            
            # التحقق من وجود قيد إقفال
            cursor.execute("""
                SELECT closing_entry_id FROM financial_years WHERE id = ?
            """, (year_id,))
            
            closing_entry_id = cursor.fetchone()['closing_entry_id']
            
            if closing_entry_id:
                # حذف قيد الإقفال
                cursor.execute("""
                    DELETE FROM journal_entries WHERE id = ?
                """, (closing_entry_id,))
            
            # إعادة فتح السنة
            cursor.execute("""
                UPDATE financial_years 
                SET is_closed = 0, closing_entry_id = NULL,
                    closed_at = NULL, closed_by_user_id = NULL
                WHERE id = ?
            """, (year_id,))
            
            # إعادة تعيين إجراءات الإقفال
            cursor.execute("""
                UPDATE financial_closures 
                SET status = 'pending', executed_at = NULL
                WHERE financial_year_id = ?
            """, (year_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error reopening year: {e}")
            return False

# نموذج للاستخدام
if __name__ == "__main__":
    # مثال لاستخدام الخدمة
    closing_service = YearEndClosingService('financial_database.db')
    
    # الحصول على ملخص الإقفال
    summary = closing_service.get_closing_summary(1)
    print("ملخص الإقفال:", summary)
    
    # تنفيذ الإقفال
    result = closing_service.execute_year_closing(1, 1)
    print("نتيجة الإقفال:", result)
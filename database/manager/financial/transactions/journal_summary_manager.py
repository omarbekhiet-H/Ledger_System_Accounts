# database/manager/journal_summary_manager.py
import sqlite3
import os
import sys
# =====================================================================
# تصحيح مسار المشروع الجذر لتمكين الاستيراد الصحيح
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
# اضبط عدد '..' حسب مكان الملف. إذا كان في database/manager/، فخطوتين للخلف كافية.
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.base_manager import BaseManager

# =====================================================================
# كلاس جديد ومستقل ومسؤول فقط عن تقرير الإجماليات
# =====================================================================
class JournalSummaryManager(BaseManager):
    """
    كلاس مستقل ومسؤول فقط عن جلب بيانات تقرير قيود اليومية الإجمالي.
    """
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func)
        print(f"DEBUG: JournalSummaryManager (Independent Class) initialized from {__file__}.")

    def get_summary_entries_in_range(self, start_date, end_date):
        """
        يجلب بيانات رأس القيد فقط مع إجمالي المدين والدائن لكل قيد.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None:
                print("ERROR: Could not get database connection for Summary Manager.")
                return []

            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
                SELECT
                    je.id,
                    je.entry_number,
                    je.entry_date,
                    je.description,
                    je.total_debit,
                    je.total_credit,
                    je.status,
                    tt.name_ar AS transaction_type_name
                
                FROM
                    journal_entries je
                LEFT JOIN
                    transaction_types tt ON je.transaction_type_id = tt.id
                
                WHERE
                    je.entry_date BETWEEN ? AND ?
                ORDER BY
                    je.entry_date ASC, je.entry_number ASC;
            """
            
            cursor.execute(query, (start_date, end_date))
            results = [dict(row) for row in cursor.fetchall()]
            return results

        except sqlite3.Error as e:
            print(f"DATABASE ERROR in JournalSummaryManager: {e}")
            return []
        finally:
            if conn:
                conn.close()
        # في journal_summary_manager.py أضف هذه الدوال:

    def get_revenue_total(self, start_date, end_date):
        """جلب إجمالي الإيرادات لفترة محددة"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(jel.debit), 0) 
                FROM journal_entry_lines jel
                JOIN accounts a ON jel.account_id = a.id
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE a.account_type = 'revenue' 
                AND je.entry_date BETWEEN ? AND ?
            """, (start_date, end_date))
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_expense_total(self, start_date, end_date):
        """جلب إجمالي المصروفات لفترة محددة"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(jel.debit), 0) 
                FROM journal_entry_lines jel
                JOIN accounts a ON jel.account_id = a.id
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE a.account_type = 'expense' 
                AND je.entry_date BETWEEN ? AND ?
            """, (start_date, end_date))
            return cursor.fetchone()[0]
        finally:
            conn.close()

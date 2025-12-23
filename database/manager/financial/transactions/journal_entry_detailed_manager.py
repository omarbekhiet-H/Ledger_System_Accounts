# database/manager/financial/transactions/journal_entry_detailed_manager.py

import sqlite3
import os
import sys

# =====================================================================
# تصحيح مسار المشروع الجذر لتمكين الاستيراد الصحيح
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
# تم تصحيح المسار ليكون 4 خطوات للخلف بناءً على بنية المجلدات
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.base_manager import BaseManager

class JournalEntryDetailedManager(BaseManager):
    """
    مدير متخصص لجلب بيانات تقرير قيود اليومية التفصيلي.
    """
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func)
        print(f"DEBUG: JournalEntryDetailedManager initialized from {__file__}.")

    def get_detailed_entries_in_range(self, start_date, end_date):
        """
        يجلب كل قيود اليومية وتفاصيلها الكاملة ضمن نطاق زمني محدد.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None:
                print("ERROR: Could not get database connection.")
                return []

            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
                SELECT
                    je.id AS entry_id, je.entry_number, je.entry_date,
                    je.description AS entry_description, je.status,
                    tt.name_ar AS transaction_type_name,
                    jel.id AS line_id, jel.debit, jel.credit,
                    jel.notes AS line_notes, jel.document_number AS line_document_number,
                    a.acc_code, a.account_name_ar,
                    cost.name_ar AS cost_center_name,
                    tax.name_ar AS tax_type_name,
                    doc.name_ar AS document_type_name
                FROM
                    journal_entries je
                JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
                LEFT JOIN accounts a ON jel.account_id = a.id
                LEFT JOIN transaction_types tt ON je.transaction_type_id = tt.id
                LEFT JOIN cost_centers cost ON jel.cost_center_id = cost.id
                LEFT JOIN tax_types tax ON jel.tax_type_id = tax.id
                LEFT JOIN document_types doc ON jel.document_type_id = doc.id
                WHERE je.entry_date BETWEEN ? AND ?
                ORDER BY je.entry_date ASC, je.entry_number ASC, jel.id ASC;
            """
            
            cursor.execute(query, (start_date, end_date))
            results = [dict(row) for row in cursor.fetchall()]
            return results

        except sqlite3.Error as e:
            print(f"DATABASE ERROR in get_detailed_entries_in_range: {e}")
            return []
        finally:
            if conn:
                conn.close()

    # =====================================================================
    # الدالة التي كانت مفقودة، الآن في مكانها الصحيح مع مسافة بادئة
    # =====================================================================
    def get_one_entry_details(self, entry_id):
        """
        يجلب التفاصيل الكاملة لقيد واحد محدد بواسطة الـ ID الخاص به.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []

            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
                SELECT
                    je.id AS entry_id, je.entry_number, je.entry_date,
                    je.description AS entry_description, je.status,
                    tt.name_ar AS transaction_type_name,
                    jel.id AS line_id, jel.debit, jel.credit,
                    jel.notes AS line_notes, jel.document_number AS line_document_number,
                    a.acc_code, a.account_name_ar,
                    cost.name_ar AS cost_center_name,
                    tax.name_ar AS tax_type_name,
                    doc.name_ar AS document_type_name
                FROM
                    journal_entries je
                JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
                LEFT JOIN accounts a ON jel.account_id = a.id
                LEFT JOIN transaction_types tt ON je.transaction_type_id = tt.id
                LEFT JOIN cost_centers cost ON jel.cost_center_id = cost.id
                LEFT JOIN tax_types tax ON jel.tax_type_id = tax.id
                LEFT JOIN document_types doc ON jel.document_type_id = doc.id
                WHERE
                    je.id = ?
                ORDER BY
                    jel.id ASC;
            """
            
            cursor.execute(query, (entry_id,))
            results = [dict(row) for row in cursor.fetchall()]
            return results

        except sqlite3.Error as e:
            print(f"DATABASE ERROR in get_one_entry_details: {e}")
            return []
        finally:
            if conn:
                conn.close()

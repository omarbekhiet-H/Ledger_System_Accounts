# database/manager/financial/financial_report_manager.py

import sqlite3
import os
import sys
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QMessageBox

# --- تصحيح مسار المشروع الجذر ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.base_manager import BaseManager
from database.manager.account_manager import AccountManager

class FinancialReportManager(BaseManager):
    """
    مسؤول عن تجهيز البيانات للتقارير المالية (أستاذ عام، ميزان مراجعة، إلخ).
    """
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func)
        self.account_manager = AccountManager(get_connection_func)
        print(f"DEBUG: FinancialReportManager initialized from {__file__}.")

    def get_journal_entries_for_account_in_range(self, account_id, start_date, end_date):
        """
        يجلب كل قيود اليومية لحساب معين ضمن نطاق زمني محدد
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: 
                return []
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = """
                SELECT
                    JE.id AS entry_id, JE.entry_number, JE.entry_date, JE.description AS entry_description,
                    JE.total_debit, JE.total_credit, JE.status, DT.name_ar AS transaction_type_name,
                    JEL.id AS line_id, JEL.account_id, ACC.acc_code,
                    ACC.account_name_ar, JEL.debit, JEL.credit, JEL.notes AS line_notes,
                    JEL.document_number AS line_document_number, JDT.name_ar AS line_document_type_name,
                    TT.name_ar AS line_tax_type_name, CC.name_ar AS line_cost_center_name
                FROM journal_entries JE
                JOIN journal_entry_lines JEL ON JE.id = JEL.journal_entry_id
                LEFT JOIN document_types DT ON JE.transaction_type_id = DT.id
                LEFT JOIN accounts ACC ON JEL.account_id = ACC.id
                LEFT JOIN document_types JDT ON JEL.document_type_id = JDT.id
                LEFT JOIN tax_types TT ON JEL.tax_type_id = TT.id
                LEFT JOIN cost_centers CC ON JEL.cost_center_id = CC.id
                WHERE JEL.account_id = ? AND JE.entry_date BETWEEN ? AND ?
                ORDER BY JE.entry_date ASC, JE.entry_number ASC, JEL.id ASC;
            """
            cursor.execute(query, (account_id, start_date, end_date))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching journal entries for account: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_one_entry_details(self, entry_id):
        """
        يجلب التفاصيل الكاملة لقيد واحد محدد بواسطة الـ ID الخاص به.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: 
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
                FROM journal_entries je
                JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
                LEFT JOIN accounts a ON jel.account_id = a.id
                LEFT JOIN transaction_types tt ON je.transaction_type_id = tt.id
                LEFT JOIN cost_centers cost ON jel.cost_center_id = cost.id
                LEFT JOIN tax_types tax ON jel.tax_type_id = tax.id
                LEFT JOIN document_types doc ON jel.document_type_id = doc.id
                WHERE je.id = ?
                ORDER BY jel.id ASC;
            """
            cursor.execute(query, (entry_id,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"DATABASE ERROR in get_one_entry_details: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_journal_entries_in_range(self, start_date, end_date):
        """
        يجلب كل قيود اليومية وتفاصيلها الكاملة ضمن نطاق زمني محدد للتقارير.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: 
                return []
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = """
                SELECT
                    JE.id AS entry_id, JE.entry_number, JE.entry_date, JE.description AS entry_description,
                    JE.total_debit, JE.total_credit, JE.status, DT.name_ar AS transaction_type_name,
                    JEL.id AS line_id, JEL.account_id, ACC.acc_code,
                    ACC.account_name_ar, JEL.debit, JEL.credit, JEL.notes AS line_notes,
                    JEL.document_number AS line_document_number, JDT.name_ar AS line_document_type_name,
                    TT.name_ar AS line_tax_type_name, CC.name_ar AS line_cost_center_name
                FROM journal_entries JE
                JOIN journal_entry_lines JEL ON JE.id = JEL.journal_entry_id
                LEFT JOIN document_types DT ON JE.transaction_type_id = DT.id
                LEFT JOIN accounts ACC ON JEL.account_id = ACC.id
                LEFT JOIN document_types JDT ON JEL.document_type_id = JDT.id
                LEFT JOIN tax_types TT ON JEL.tax_type_id = TT.id
                LEFT JOIN cost_centers CC ON JEL.cost_center_id = CC.id
                WHERE JE.entry_date BETWEEN ? AND ?
                ORDER BY JE.entry_date ASC, JE.entry_number ASC, JEL.id ASC;
            """
            cursor.execute(query, (start_date, end_date))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching detailed journal entries: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_general_ledger_data(self, start_date, end_date, account_id=None):
        """
        يجلب بيانات الأستاذ العام للحسابات النهائية.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: 
                return []
            cursor = conn.cursor()

            accounts_to_process = []
            if account_id:
                descendant_ids = self.account_manager._get_descendant_account_ids(account_id)
                all_accounts = self.account_manager.get_all_accounts()
                accounts_to_process = [acc for acc in all_accounts if acc['id'] in descendant_ids and acc['is_final'] == 1]
            else:
                all_accounts = self.account_manager.get_all_accounts()
                accounts_to_process = [acc for acc in all_accounts if acc['is_final'] == 1]

            if not accounts_to_process:
                return []

            general_ledger_report_data = []
            for account in accounts_to_process:
                current_account_id = account['id']
                account_type_data = self.account_manager.get_account_type_by_id(account['account_type_id'])
                account_side = account_type_data['account_side'] if account_type_data else 'Debit'

                opening_balance_date = datetime.strptime(start_date, "%Y-%m-%d").date() - timedelta(days=1)
                op_final_balance = self.account_manager.get_account_balance_cumulative([current_account_id], opening_balance_date.strftime("%Y-%m-%d"))

                opening_debit = op_final_balance if account_side == 'Debit' and op_final_balance >= 0 else abs(op_final_balance) if account_side == 'Credit' and op_final_balance < 0 else 0.0
                opening_credit = op_final_balance if account_side == 'Credit' and op_final_balance >= 0 else abs(op_final_balance) if account_side == 'Debit' and op_final_balance < 0 else 0.0

                query_movements = """
                    SELECT SUM(debit), SUM(credit) 
                    FROM journal_entry_lines JEL 
                    JOIN journal_entries JE ON JEL.journal_entry_id = JE.id 
                    WHERE JEL.account_id = ? AND JE.entry_date BETWEEN ? AND ?
                """
                cursor.execute(query_movements, (current_account_id, start_date, end_date))
                movement_result = cursor.fetchone()
                period_debit = movement_result[0] or 0.0
                period_credit = movement_result[1] or 0.0

                final_balance = opening_debit - opening_credit + period_debit - period_credit
                final_debit = final_balance if final_balance >= 0 else 0.0
                final_credit = abs(final_balance) if final_balance < 0 else 0.0
                
                if any([opening_debit, opening_credit, period_debit, period_credit]):
                    general_ledger_report_data.append({
                        'account_id': current_account_id,
                        'acc_code': account['acc_code'],
                        'account_name_ar': account['account_name_ar'],
                        'opening_debit_balance': opening_debit,
                        'opening_credit_balance': opening_credit,
                        'period_debit': period_debit,
                        'period_credit': period_credit,
                        'final_debit_balance': final_debit,
                        'final_credit_balance': final_credit
                    })
            
            general_ledger_report_data.sort(key=lambda x: x['acc_code'])
            return general_ledger_report_data
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching General Ledger data: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_trial_balance_data(self, start_date, end_date):
        """
        يجلب بيانات ميزان المراجعة لكل الحسابات (رئيسية وفرعية).
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: 
                return []
            cursor = conn.cursor()
            all_accounts = self.account_manager.get_all_accounts()
            trial_balance_report_data = []

            for account in all_accounts:
                account_id = account['id']
                account_type_data = self.account_manager.get_account_type_by_id(account['account_type_id'])
                account_side = account_type_data['account_side'] if account_type_data else 'Debit'
                
                ids_to_sum = self.account_manager._get_descendant_account_ids(account_id)
                if not ids_to_sum: 
                    continue

                opening_balance_date = datetime.strptime(start_date, "%Y-%m-%d").date() - timedelta(days=1)
                op_final_balance = self.account_manager.get_account_balance_cumulative(ids_to_sum, opening_balance_date.strftime("%Y-%m-%d"))

                opening_debit = op_final_balance if account_side == 'Debit' and op_final_balance >= 0 else abs(op_final_balance) if account_side == 'Credit' and op_final_balance < 0 else 0.0
                opening_credit = op_final_balance if account_side == 'Credit' and op_final_balance >= 0 else abs(op_final_balance) if account_side == 'Debit' and op_final_balance < 0 else 0.0

                id_placeholders = ','.join('?' * len(ids_to_sum))
                query_movements = f"""
                    SELECT SUM(debit), SUM(credit) 
                    FROM journal_entry_lines JEL 
                    JOIN journal_entries JE ON JEL.journal_entry_id = JE.id 
                    WHERE JEL.account_id IN ({id_placeholders}) AND JE.entry_date BETWEEN ? AND ?
                """
                cursor.execute(query_movements, list(ids_to_sum) + [start_date, end_date])
                movement_result = cursor.fetchone()
                period_debit = movement_result[0] or 0.0
                period_credit = movement_result[1] or 0.0

                final_balance = opening_debit - opening_credit + period_debit - period_credit
                final_debit = final_balance if final_balance >= 0 else 0.0
                final_credit = abs(final_balance) if final_balance < 0 else 0.0

                if any([opening_debit, opening_credit, period_debit, period_credit]):
                    trial_balance_report_data.append({
                        'account_id': account_id,
                        'acc_code': account['acc_code'], 
                        'account_name_ar': account['account_name_ar'],
                        'level': account['level'],
                        'opening_debit_balance': opening_debit, 
                        'opening_credit_balance': opening_credit,
                        'period_debit': period_debit, 
                        'period_credit': period_credit,
                        'final_debit_balance': final_debit, 
                        'final_credit_balance': final_credit
                    })
            
            trial_balance_report_data.sort(key=lambda x: x['acc_code'])
            return trial_balance_report_data
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching trial balance data: {e}")
            return []
        finally:
            if conn:
                conn.close()

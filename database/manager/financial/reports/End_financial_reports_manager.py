# database/manager/financial_reports_manager.py

import sqlite3
import os
import sys
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox

# =====================================================================
# Correct project root path to enable correct imports
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.base_manager import BaseManager
from database.db_connection import get_financials_db_connection
from database.manager.account_manager import AccountManager # Needed for account details


class EndFinancialReportsManager(BaseManager):
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func)
        self.account_manager = AccountManager(get_connection_func) # Re-use connection func
        print(f"DEBUG: FinancialReportsManager initialized from {__file__}.")

    def get_trial_balance(self, end_date_str):
        """
        Generates a trial balance report up to a specified date.
        Returns a list of dictionaries for each final account with its total debit, total credit, and final balance.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()

            # Get all final accounts
            final_accounts = self.account_manager.get_all_final_accounts()
            
            report_data = []
            for account in final_accounts:
                account_id = account['id']
                account_code = account['acc_code']
                account_name_ar = account['account_name_ar']
                account_side = account['account_type_name_ar'] # This is actually account_type.name_ar, not account_side
                
                # Correctly get account_side from account_type_id
                account_type_details = self.account_manager.get_account_type_by_id(account['account_type_id'])
                natural_side = account_type_details['account_side'] if account_type_details else 'Debit' # Default to Debit if not found

                # Calculate total debit and credit for the account up to the end_date
                # Use the aggregated balance function for safety, though for final accounts it's the same
                total_debit, total_credit, final_balance = self.account_manager.get_account_balance_up_to_date(account_id, end_date_str)

                report_data.append({
                    'account_id': account_id,
                    'account_code': account_code,
                    'account_name_ar': account_name_ar,
                    'natural_side': natural_side,
                    'total_debit': total_debit,
                    'total_credit': total_credit,
                    'final_balance': final_balance # This is the balance on its natural side
                })
            return report_data
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error generating trial balance: {e}")
            print(f"Error in get_trial_balance: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_income_statement_data(self, start_date_str, end_date_str, level=None):
        """
        Generates data for an Income Statement (Profit and Loss) report.
        Supports showing accounts on specific chart levels (e.g., 2 or 3),
        aggregating their descendants.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None:
                return []

            cursor = conn.cursor()
            results = []

            # Get all accounts
            all_accounts = self.account_manager.get_all_accounts()
            if not all_accounts:
                return []

            for account in all_accounts:
                acc_level = account.get("level", 0)

                # Skip accounts not matching the requested level (if specified)
                if level is not None and acc_level != level:
                    continue

                acc_type = self.account_manager.get_account_type_by_id(account['account_type_id'])
                if not acc_type:
                    continue

                if acc_type['name_ar'] not in ("الإيرادات", "المصروفات"):
                    continue

                # Get all descendant ids (including itself)
                ids_to_sum = self.account_manager._get_descendant_account_ids(account['id'])
                if not ids_to_sum:
                    ids_to_sum = [account['id']]

                placeholders = ",".join("?" * len(ids_to_sum))
                query = f"""
                    SELECT 
                        SUM(jel.debit) AS sum_debit, 
                        SUM(jel.credit) AS sum_credit
                    FROM journal_entry_lines jel
                    JOIN journal_entries je ON jel.journal_entry_id = je.id
                    WHERE jel.account_id IN ({placeholders})
                      AND je.entry_date BETWEEN ? AND ?
                """
                cursor.execute(query, ids_to_sum + [start_date_str, end_date_str])
                row = cursor.fetchone()
                sum_debit = row[0] or 0.0
                sum_credit = row[1] or 0.0

                # For revenues → (credit - debit), for expenses → (debit - credit)
                if acc_type['name_ar'] == "الإيرادات":
                    final_balance = sum_credit - sum_debit
                else:
                    final_balance = sum_debit - sum_credit

                if abs(final_balance) > 0.0001:
                    results.append({
                        "acc_code": account["acc_code"],
                        "account_name_ar": account["account_name_ar"],
                        "account_type_name": acc_type["name_ar"],
                        "debit": sum_debit,
                        "credit": sum_credit,
                        "final_balance": final_balance,
                        "level": acc_level
                    })

            results.sort(key=lambda x: x["acc_code"])
            return results

        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error generating income statement: {e}")
            print(f"Error in get_income_statement_data: {e}")
            return []
        finally:
            if conn:
                conn.close()


    def get_balance_sheet_data(self, end_date_str, level=3):
        """
        Generates hierarchical Balance Sheet data up to a specified level.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None:
                return {"assets": [], "liabilities": [], "equity": []}
            cursor = conn.cursor()

            # Get account types
            account_types = {
                "ASSET": "الأصول",
                "LIABILITY": "الخصوم",
                "EQUITY": "حقوق الملكية"
            }

            result = {"assets": [], "liabilities": [], "equity": []}

            for acc_type_code, acc_type_name in account_types.items():
                # كل الحسابات من النوع ده حتى المستوى المطلوب
                accounts = cursor.execute("""
                    SELECT a.id, a.acc_code, a.account_name_ar, a.parent_account_id, a.level,
                       at.account_side
                    FROM accounts a
                    JOIN account_types at ON a.account_type_id = at.id
                    WHERE at.code = ? AND a.level <= ?
                    ORDER BY a.acc_code ASC
                """, (acc_type_code, level)).fetchall()

                for acc_id, acc_code, acc_name_ar, parent_id, acc_level, side in accounts:
                    # اجمع الرصيد لغاية التاريخ
                    total_debit, total_credit, final_balance = self.account_manager.get_account_balance_up_to_date(acc_id, end_date_str)

                    result_key = "assets" if acc_type_code == "ASSET" else "liabilities" if acc_type_code == "LIABILITY" else "equity"
                    result[result_key].append({
                        "account_id": acc_id,
                        "account_code": acc_code,
                        "account_name_ar": acc_name_ar,
                        "account_type_name": acc_type_name,
                        "parent_account_id": parent_id,
                        "level": acc_level,
                        "balance": final_balance
                    })

            return result

        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error generating balance sheet: {e}")
            return {"assets": [], "liabilities": [], "equity": []}
        finally:
            if conn:
                conn.close()

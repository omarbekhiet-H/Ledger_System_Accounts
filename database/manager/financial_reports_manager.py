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


class FinancialReportsManager(BaseManager):
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

    def get_income_statement_data(self, start_date_str, end_date_str):
        """
        Generates data for an Income Statement (Profit and Loss) report.
        Sums up revenues and expenses for a given period.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return {'revenues': [], 'expenses': [], 'net_income': 0.0}
            cursor = conn.cursor()

            # Get IDs for Revenue and Expense account types
            revenue_type_id = cursor.execute("SELECT id FROM account_types WHERE code='REVENUE'").fetchone()
            expense_type_id = cursor.execute("SELECT id FROM account_types WHERE code='EXPENSE'").fetchone()

            revenue_type_id = revenue_type_id[0] if revenue_type_id else None
            expense_type_id = expense_type_id[0] if expense_type_id else None

            revenues_data = []
            expenses_data = []
            
            total_revenues = 0.0
            total_expenses = 0.0

            # Fetch all final revenue accounts and their balances
            if revenue_type_id:
                revenue_accounts = cursor.execute("""
                    SELECT a.id, a.acc_code, a.account_name_ar, at.account_side
                    FROM accounts a
                    JOIN account_types at ON a.account_type_id = at.id
                    WHERE a.account_type_id = ? AND a.id NOT IN (SELECT DISTINCT parent_account_id FROM accounts WHERE parent_account_id IS NOT NULL)
                    ORDER BY a.acc_code ASC
                """, (revenue_type_id,)).fetchall()

                for acc_id, acc_code, acc_name_ar, acc_side in revenue_accounts:
                    # For income statement, we need the balance *within* the period
                    # This means sum of (credit - debit) for revenue accounts within the range
                    cursor.execute("""
                        SELECT 
                            SUM(CASE WHEN JEL.credit IS NOT NULL THEN JEL.credit ELSE 0 END) - 
                            SUM(CASE WHEN JEL.debit IS NOT NULL THEN JEL.debit ELSE 0 END)
                        FROM journal_entry_lines JEL
                        JOIN journal_entries JE ON JEL.journal_entry_id = JE.id
                        WHERE JEL.account_id = ? AND JE.entry_date BETWEEN ? AND ?
                    """, (acc_id, start_date_str, end_date_str))
                    balance = cursor.fetchone()[0]
                    balance = balance if balance is not None else 0.0
                    
                    revenues_data.append({
                        'account_code': acc_code,
                        'account_name_ar': acc_name_ar,
                        'balance': balance
                    })
                    total_revenues += balance

            # Fetch all final expense accounts and their balances
            if expense_type_id:
                expense_accounts = cursor.execute("""
                    SELECT a.id, a.acc_code, a.account_name_ar, at.account_side
                    FROM accounts a
                    JOIN account_types at ON a.account_type_id = at.id
                    WHERE a.account_type_id = ? AND a.id NOT IN (SELECT DISTINCT parent_account_id FROM accounts WHERE parent_account_id IS NOT NULL)
                    ORDER BY a.acc_code ASC
                """, (expense_type_id,)).fetchall()
                
                for acc_id, acc_code, acc_name_ar, acc_side in expense_accounts:
                    # For income statement, we need the balance *within* the period
                    # This means sum of (debit - credit) for expense accounts within the range
                    cursor.execute("""
                        SELECT 
                            SUM(CASE WHEN JEL.debit IS NOT NULL THEN JEL.debit ELSE 0 END) - 
                            SUM(CASE WHEN JEL.credit IS NOT NULL THEN JEL.credit ELSE 0 END)
                        FROM journal_entry_lines JEL
                        JOIN journal_entries JE ON JEL.journal_entry_id = JE.id
                        WHERE JEL.account_id = ? AND JE.entry_date BETWEEN ? AND ?
                    """, (acc_id, start_date_str, end_date_str))
                    balance = cursor.fetchone()[0]
                    balance = balance if balance is not None else 0.0
                    
                    expenses_data.append({
                        'account_code': acc_code,
                        'account_name_ar': acc_name_ar,
                        'balance': balance
                    })
                    total_expenses += balance
            
            net_income = total_revenues - total_expenses

            return {
                'revenues': revenues_data,
                'expenses': expenses_data,
                'total_revenues': total_revenues,
                'total_expenses': total_expenses,
                'net_income': net_income
            }

        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error generating income statement: {e}")
            print(f"Error in get_income_statement_data: {e}")
            return {'revenues': [], 'expenses': [], 'net_income': 0.0, 'total_revenues': 0.0, 'total_expenses': 0.0}
        finally:
            if conn:
                conn.close()

    def get_balance_sheet_data(self, end_date_str):
        """
        Generates data for a Balance Sheet report up to a specified date.
        Sums up assets, liabilities, and equity.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return {'assets': [], 'liabilities': [], 'equity': [], 'total_assets': 0.0, 'total_liabilities_equity': 0.0}
            cursor = conn.cursor()

            # Get IDs for Asset, Liability, and Equity account types
            asset_type_id = cursor.execute("SELECT id FROM account_types WHERE code='ASSET'").fetchone()
            liability_type_id = cursor.execute("SELECT id FROM account_types WHERE code='LIABILITY'").fetchone()
            equity_type_id = cursor.execute("SELECT id FROM account_types WHERE code='EQUITY'").fetchone()

            asset_type_id = asset_type_id[0] if asset_type_id else None
            liability_type_id = liability_type_id[0] if liability_type_id else None
            equity_type_id = equity_type_id[0] if equity_type_id else None

            assets_data = []
            liabilities_data = []
            equity_data = []

            total_assets = 0.0
            total_liabilities = 0.0
            total_equity = 0.0

            # Fetch all final Asset accounts and their balances
            if asset_type_id:
                asset_accounts = cursor.execute("""
                    SELECT a.id, a.acc_code, a.account_name_ar, at.account_side
                    FROM accounts a
                    JOIN account_types at ON a.account_type_id = at.id
                    WHERE a.account_type_id = ? AND a.id NOT IN (SELECT DISTINCT parent_account_id FROM accounts WHERE parent_account_id IS NOT NULL)
                    ORDER BY a.acc_code ASC
                """, (asset_type_id,)).fetchall()

                for acc_id, acc_code, acc_name_ar, acc_side in asset_accounts:
                    total_debit, total_credit, final_balance = self.account_manager.get_account_balance_up_to_date(acc_id, end_date_str)
                    assets_data.append({
                        'account_code': acc_code,
                        'account_name_ar': acc_name_ar,
                        'balance': final_balance # Balance on its natural side (Debit for Assets)
                    })
                    total_assets += final_balance

            # Fetch all final Liability accounts and their balances
            if liability_type_id:
                liability_accounts = cursor.execute("""
                    SELECT a.id, a.acc_code, a.account_name_ar, at.account_side
                    FROM accounts a
                    JOIN account_types at ON a.account_type_id = at.id
                    WHERE a.account_type_id = ? AND a.id NOT IN (SELECT DISTINCT parent_account_id FROM accounts WHERE parent_account_id IS NOT NULL)
                    ORDER BY a.acc_code ASC
                """, (liability_type_id,)).fetchall()
                
                for acc_id, acc_code, acc_name_ar, acc_side in liability_accounts:
                    total_debit, total_credit, final_balance = self.account_manager.get_account_balance_up_to_date(acc_id, end_date_str)
                    liabilities_data.append({
                        'account_code': acc_code,
                        'account_name_ar': acc_name_ar,
                        'balance': final_balance # Balance on its natural side (Credit for Liabilities)
                    })
                    total_liabilities += final_balance

            # Fetch all final Equity accounts and their balances
            if equity_type_id:
                equity_accounts = cursor.execute("""
                    SELECT a.id, a.acc_code, a.account_name_ar, at.account_side
                    FROM accounts a
                    JOIN account_types at ON a.account_type_id = at.id
                    WHERE a.account_type_id = ? AND a.id NOT IN (SELECT DISTINCT parent_account_id FROM accounts WHERE parent_account_id IS NOT NULL)
                    ORDER BY a.acc_code ASC
                """, (equity_type_id,)).fetchall()
                
                for acc_id, acc_code, acc_name_ar, acc_side in equity_accounts:
                    total_debit, total_credit, final_balance = self.account_manager.get_account_balance_up_to_date(acc_id, end_date_str)
                    equity_data.append({
                        'account_code': acc_code,
                        'account_name_ar': acc_name_ar,
                        'balance': final_balance # Balance on its natural side (Credit for Equity)
                    })
                    total_equity += final_balance
            
            total_liabilities_equity = total_liabilities + total_equity

            return {
                'assets': assets_data,
                'liabilities': liabilities_data,
                'equity': equity_data,
                'total_assets': total_assets,
                'total_liabilities_equity': total_liabilities_equity
            }

        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error generating balance sheet: {e}")
            print(f"Error in get_balance_sheet_data: {e}")
            return {'assets': [], 'liabilities': [], 'equity': [], 'total_assets': 0.0, 'total_liabilities_equity': 0.0}
        finally:
            if conn:
                conn.close()


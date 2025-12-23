# database/manager/account_manager.py

import sqlite3
import os
import sys
from PyQt5.QtWidgets import QMessageBox # Keep for error messages

# =====================================================================
# Correct project root path to enable correct imports
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.base_manager import BaseManager
# Import connection function here instead of defining or passing it indirectly
from database.db_connection import get_financials_db_connection 

class AccountManager(BaseManager):
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func)
        self.table_name = "accounts" # Table name in the database
        print(f"DEBUG: AccountManager initialized from {__file__}.") # DEBUG
        

    def create_table(self):
        # This is now managed by financials_schema.py
        pass

    def add_account(self, acc_code, account_name_ar, account_name_en, account_type_id, is_balance_sheet, level, is_active=1, parent_account_id=None):
        """Function to add a new account."""
        if self.record_exists(self.table_name, 'acc_code', acc_code):
            QMessageBox.warning(None, "Input Error", "Account code already exists.")
            return False
        if self.record_exists(self.table_name, 'account_name_ar', account_name_ar):
            QMessageBox.warning(None, "Input Error", "Arabic account name already exists.")
            return False
        if account_name_en and self.record_exists(self.table_name, 'account_name_en', account_name_en):
            QMessageBox.warning(None, "Input Error", "English account name already exists.")
            return False

        query = """
            INSERT INTO accounts (acc_code, account_name_ar, account_name_en, account_type_id, is_balance_sheet, level, is_active, parent_account_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (acc_code, account_name_ar, account_name_en, account_type_id, is_balance_sheet, level, is_active, parent_account_id)
        return self.execute_query(query, params)

    def update_account(self, account_id, acc_code, account_name_ar, account_name_en, account_type_id, is_balance_sheet, level, is_active, parent_account_id=None):
        """Function to update an existing account."""
        # Check for duplicate account code or Arabic/English name, excluding the current account
        if self.record_exists(self.table_name, 'acc_code', acc_code, exclude_id=account_id):
            QMessageBox.warning(None, "Input Error", "Account code already exists for another account.")
            return False
        if self.record_exists(self.table_name, 'account_name_ar', account_name_ar, exclude_id=account_id):
            QMessageBox.warning(None, "Input Error", "Arabic account name already exists for another account.")
            return False
        if account_name_en and self.record_exists(self.table_name, 'account_name_en', account_name_en, exclude_id=account_id):
            QMessageBox.warning(None, "Input Error", "English account name already exists for another account.")
            return False

        query = """
            UPDATE accounts
            SET acc_code = ?, account_name_ar = ?, account_name_en = ?, account_type_id = ?, 
                is_balance_sheet = ?, level = ?, is_active = ?, parent_account_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        params = (acc_code, account_name_ar, account_name_en, account_type_id, is_balance_sheet, level, is_active, parent_account_id, account_id)
        return self.execute_query(query, params)

    def deactivate_account(self, account_id):
        """Function to deactivate an account (make it inactive)."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            # Check for active child accounts
            cursor.execute("SELECT COUNT(*) FROM accounts WHERE parent_account_id = ? AND is_active = 1", (account_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "Deactivation Error", "Cannot deactivate this account because it has active child accounts.")
                return False

            # Check for associated journal entries
            cursor.execute("SELECT COUNT(*) FROM journal_entry_lines WHERE account_id = ?", (account_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "Deactivation Error", "Cannot deactivate this account because it is linked to journal entries.")
                return False

            cursor.execute("UPDATE accounts SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (account_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error deactivating account: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def activate_account(self, account_id):
        """Function to activate an account."""
        query = "UPDATE accounts SET is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        return self.execute_query(query, (account_id,))

    def delete_account(self, account_id):
        """Function to delete an account. Requires checking for dependencies."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            # Check for child accounts
            cursor.execute("SELECT COUNT(*) FROM accounts WHERE parent_account_id = ?", (account_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "Deletion Error", "Cannot delete this account because it has child accounts.")
                return False

            # Check for associated journal entries
            cursor.execute("SELECT COUNT(*) FROM journal_entry_lines WHERE account_id = ?", (account_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "Deletion Error", "Cannot delete this account because it is linked to journal entries.")
                return False

            # Check if linked as an account in cash_chests or bank_accounts
            cursor.execute("SELECT COUNT(*) FROM cash_chests WHERE account_id = ?", (account_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "Deletion Error", "Cannot delete this account because it is linked to a cash chest.")
                return False

            cursor.execute("SELECT COUNT(*) FROM bank_accounts WHERE account_id = ?", (account_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "Deletion Error", "Cannot delete this account because it is linked to a bank account.")
                return False
            
            # Check if linked as a tax account in tax_types
            cursor.execute("SELECT COUNT(*) FROM tax_types WHERE tax_account_id = ?", (account_id,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.critical(None, "Deletion Error", "Cannot delete this account because it is linked to a tax type.")
                return False

            # If no dependencies, proceed with deletion
            query = "DELETE FROM accounts WHERE id = ?"
            return self.execute_query(query, (account_id,))
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error deleting account: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_account_by_id(self, account_id):
        """Fetches an account by ID."""
        query = "SELECT * FROM accounts WHERE id = ?"
        return self.fetch_one(query, (account_id,))

    def get_account_by_code(self, acc_code):
        """Fetches an account by its code."""
        query = "SELECT * FROM accounts WHERE acc_code = ?"
        return self.fetch_one(query, (acc_code,))

    def get_all_accounts(self):
        """Fetches all accounts."""
        query = "SELECT * FROM accounts ORDER BY acc_code"
        return self.fetch_all(query)
    
    # =================================================================================
# ==> أضف هذه الدالة هنا <==
# =================================================================================
    def get_all_accounts_with_details(self):
        """
        يجلب جميع الحسابات مع تفاصيل إضافية مثل طبيعة الحساب (مدين/دائن)
        من جدول أنواع الحسابات باستخدام JOIN.
        """
        query = """
            SELECT
                a.id,
                a.acc_code,
                a.account_name_ar,
                a.account_name_en,
                a.account_type_id,
                a.parent_account_id,
                a.is_final,
                a.is_balance_sheet,
                a.level,
                a.is_active,
                at.account_side
            FROM
                accounts a
            JOIN
                account_types at ON a.account_type_id = at.id
            ORDER BY
                a.acc_code;
        """
        # تفترض هذه الدالة وجود دالة fetch_all في BaseManager
        return self.fetch_all(query)
# =================================================================================


    def get_all_active_accounts(self):
        """Fetches all active accounts."""
        query = "SELECT * FROM accounts WHERE is_active = 1 ORDER BY acc_code"
        return self.fetch_all(query)

    def get_all_final_accounts(self):
        """
        Fetches all final accounts (those that have no child accounts).
        These are the accounts on which journal entries can be posted.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            query = """
                SELECT a.id, a.acc_code, a.account_name_ar, a.account_name_en, a.account_type_id, at.account_side
                FROM accounts a
                JOIN account_types at ON a.account_type_id = at.id
                WHERE a.id NOT IN (SELECT parent_account_id FROM accounts WHERE parent_account_id IS NOT NULL)
                ORDER BY a.acc_code;
            """
            cursor.execute(query)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching final accounts: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_final_account_by_code(self, acc_code):
        """
        Fetches a final account (one with no children) by its code.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None:
                return None
            cursor = conn.cursor()
            # A final account is one that does not appear as a parent_account_id for any other account
            query = """
                SELECT a.*, at.account_side
                FROM accounts a
                JOIN account_types at ON a.account_type_id = at.id
                WHERE a.acc_code = ? 
                AND a.is_active = 1
                AND a.id NOT IN (SELECT parent_account_id FROM accounts WHERE parent_account_id IS NOT NULL)
            """
            cursor.execute(query, (acc_code,))
            
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None # Account not found or not a final account
            
        except sqlite3.Error as e:
            print(f"Database error in get_final_account_by_code: {e}")
            QMessageBox.critical(None, "Database Error", f"Error fetching final account by code: {e}")
            return None
        finally:
            if conn:
                conn.close()            

    def get_account_type_by_id(self, type_id):
        """Fetches an account type by ID."""
        query = "SELECT * FROM account_types WHERE id = ?"
        return self.fetch_one(query, (type_id,))

    def get_account_types(self):
        """Fetches all account types."""
        query = "SELECT id, name_ar, account_side FROM account_types WHERE is_active = 1 ORDER BY name_ar"
        return self.fetch_all(query)

    def get_max_child_acc_code(self, parent_account_id):
        """
        Fetches the highest direct child account code for a given parent account.
        If parent_account_id is None, it looks for the highest top-level account code.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()

            if parent_account_id is None:
                query = "SELECT MAX(acc_code) FROM accounts WHERE parent_account_id IS NULL"
                cursor.execute(query)
            else:
                query = "SELECT MAX(acc_code) FROM accounts WHERE parent_account_id = ?"
                cursor.execute(query, (parent_account_id,))
            
            result = cursor.fetchone()[0]
            return result if result else None
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching max child account code: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def _get_descendant_account_ids(self, account_id):
        """
        Recursively fetches all descendant account IDs (children, grandchildren, etc.)
        for a given account, including the account's own ID.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []

            descendant_ids = {account_id} # Start with the account's own ID
            queue = [account_id]

            while queue:
                current_id = queue.pop(0)
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM accounts WHERE parent_account_id = ?", (current_id,))
                children = cursor.fetchall()
                for child_row in children:
                    child_id = child_row[0]
                    if child_id not in descendant_ids:
                        descendant_ids.add(child_id)
                        queue.append(child_id)
            return list(descendant_ids)
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching hierarchical descendant accounts: {e}")
            # In case of error, return only the account itself to avoid larger issues
            return [account_id] 
        finally:
            if conn:
                conn.close()

    def get_account_balance(self, account_id, up_to_date=None):
        """
        Calculates the balance of a specific account up to a given date, including movements of all its descendant accounts.
        If no date is specified, it calculates the balance up to today's date.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return 0.0

            # Fetch all descendant account IDs, including the account itself
            account_ids_to_sum = self._get_descendant_account_ids(account_id)
            if not account_ids_to_sum: 
                return 0.0

            # Convert the list of IDs to a string for the SQL IN clause
            id_placeholders = ','.join('?' * len(account_ids_to_sum))

            # Fetch the account's normal balance side (for the main account, not the child)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT at.account_side
                FROM accounts a
                JOIN account_types at ON a.account_type_id = at.id
                WHERE a.id = ?
            """, (account_id,))
            account_side = cursor.fetchone()
            if not account_side:
                QMessageBox.warning(None, "Account Error", "Account type not found.")
                return 0.0
            account_side = account_side[0] # 'Debit' or 'Credit'

            # Query to fetch total debits and credits for all specified descendant accounts up to the date
            query = f"""
                SELECT SUM(JEL.debit) AS total_debit, SUM(JEL.credit) AS total_credit
                FROM journal_entry_lines JEL 
                JOIN journal_entries JE ON JEL.journal_entry_id = JE.id 
                WHERE JEL.account_id IN ({id_placeholders})
            """
            params = list(account_ids_to_sum) # Convert set to list for parameters

            if up_to_date:
                query += " AND JE.entry_date <= ?"
                params.append(up_to_date)
            
            cursor.execute(query, tuple(params))
            result = cursor.fetchone()

            total_debit = result[0] if result and result[0] is not None else 0.0
            total_credit = result[1] if result and result[1] is not None else 0.0

            # Calculate balance based on account type
            if account_side == 'Debit': # Assets and Expenses
                balance = total_debit - total_credit
            elif account_side == 'Credit': # Liabilities, Equity, and Revenues
                balance = total_credit - total_debit
            else:
                balance = 0.0 # Unexpected case

            return balance
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching hierarchical account balance: {e}")
            print(f"Error getting hierarchical account balance: {e}") # Print error to console
            return 0.0
        finally:
            if conn:
                conn.close()

    def get_account_balance_up_to_date(self, account_id, up_to_date_str):
        """
        Calculates the balance of a specific account up to a given date, including movements of all its descendant accounts.
        This function is crucial for calculating opening balances for reports.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return 0.0, 0.0, 0.0 # Return debit, credit, and final balance

            # Fetch all descendant account IDs, including the account itself
            account_ids_to_sum = self._get_descendant_account_ids(account_id)
            if not account_ids_to_sum:
                return 0.0, 0.0, 0.0

            id_placeholders = ','.join('?' * len(account_ids_to_sum))

            cursor = conn.cursor()
            cursor.execute("""
                SELECT at.account_side
                FROM accounts a
                JOIN account_types at ON a.account_type_id = at.id
                WHERE a.id = ?
            """, (account_id,))
            account_side_row = cursor.fetchone()
            if not account_side_row:
                return 0.0, 0.0, 0.0

            account_side = account_side_row[0]

            query = f"""
                SELECT 
                    SUM(CASE WHEN JEL.debit IS NOT NULL THEN JEL.debit ELSE 0 END) AS total_debit,
                    SUM(CASE WHEN JEL.credit IS NOT NULL THEN JEL.credit ELSE 0 END) AS total_credit
                FROM journal_entry_lines JEL
                JOIN journal_entries JE ON JEL.journal_entry_id = JE.id
                WHERE JEL.account_id IN ({id_placeholders}) AND JE.entry_date <= ?
            """
            params = list(account_ids_to_sum)
            params.append(up_to_date_str)

            cursor.execute(query, tuple(params))
            result = cursor.fetchone()

            total_debit = result[0] if result and result[0] is not None else 0.0
            total_credit = result[1] if result and result[1] is not None else 0.0

            final_balance = 0.0
            if account_side == 'Debit':
                final_balance = total_debit - total_credit
            elif account_side == 'Credit':
                final_balance = total_credit - total_debit
            
            return total_debit, total_credit, final_balance

        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error calculating hierarchical account balance up to date: {e}")
            print(f"Error calculating hierarchical account balance up to date: {e}")
            return 0.0, 0.0, 0.0
        finally:
            if conn:
                conn.close()
# =====================================================================
    # الدالة المساعدة التي كانت مفقودة - أضفها هنا
    # =====================================================================
    def get_account_balance_cumulative(self, account_ids, up_to_date):
        """
        يحسب الرصيد التراكمي لمجموعة من الحسابات (IDs) حتى تاريخ معين.
        هذه دالة مساعدة أساسية للتقارير المالية.
        """
        if not account_ids:
            return 0.0

        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return 0.0
            cursor = conn.cursor()

            id_placeholders = ','.join('?' * len(account_ids))
            
            query = f"""
                SELECT
                    SUM(JEL.debit) AS total_debit,
                    SUM(JEL.credit) AS total_credit
                FROM journal_entry_lines JEL
                JOIN journal_entries JE ON JEL.journal_entry_id = JE.id
                WHERE JEL.account_id IN ({id_placeholders})
                AND JE.entry_date <= ?
            """
            
            params = list(account_ids)
            params.append(up_to_date)
            
            cursor.execute(query, tuple(params))
            result = cursor.fetchone()

            total_debit = result[0] if result and result[0] is not None else 0.0
            total_credit = result[1] if result and result[1] is not None else 0.0
            
            # ملاحظة: هذه الدالة تعيد الرصيد الصافي (مدين موجب، دائن سالب)
            # وسيتم التعامل مع طبيعة الحساب في مدير التقارير
            return total_debit - total_credit

        except sqlite3.Error as e:
            print(f"Database error in get_account_balance_cumulative: {e}")
            return 0.0
        finally:
            if conn:
                conn.close()
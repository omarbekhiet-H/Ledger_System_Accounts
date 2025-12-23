# database/manager/journal_manager.py
import sys
# DEBUG: Loading journal_manager.py from: C:\Users\AU\Videos\my_erp_projects\database\manager\journal_manager.py # DEBUG

import sqlite3
import os
from PyQt5.QtWidgets import QMessageBox
from datetime import datetime, timedelta

# =====================================================================
# Correcting the root project path to enable proper imports
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import necessary managers
from database.base_manager import BaseManager
from database.manager.account_manager import AccountManager # Import AccountManager

class JournalManager(BaseManager):
    """
    Responsible for managing journal entries and their lines, as well as financial years.
    Connects to the financials.db database.
    """
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func)
        # DEBUG: Add this line to check that this version of the class is loaded
        print(f"DEBUG: JournalManager initialized from {__file__} (Version for General Ledger Non-Final Accounts).")
        self.account_manager = AccountManager(get_connection_func) # Initialize AccountManager

    def _generate_next_entry_number(self):
        """Generates the next entry number based on the largest existing number."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return None
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(entry_number) FROM journal_entries")
            max_entry_number = cursor.fetchone()[0]

            if max_entry_number:
                num_part_str = ''.join(filter(str.isdigit, max_entry_number))
                if num_part_str:
                    num_part = int(num_part_str)
                    next_num = num_part + 1
                    prefix = ''.join(filter(str.isalpha, max_entry_number))
                    if prefix:
                        padding = len(num_part_str)
                        return f"{prefix}{next_num:0{padding}d}"
                    else:
                        return str(next_num)
                else:
                    return "1"
            return "1"
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error generating next entry number: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def add_journal_entry(self, entry_date, system_date, description, transaction_type_id, total_debit, total_credit, lines, status='Under Review', created_by=None):
        """
        Adds a new journal entry with its lines.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            entry_number = self._generate_next_entry_number()
            if entry_number is None:
                return False

            cursor.execute("""
                INSERT INTO journal_entries (entry_number, entry_date, description, transaction_type_id,  total_debit, total_credit, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (entry_number, entry_date, description, transaction_type_id, total_debit, total_credit, status, created_by))

            journal_entry_id = cursor.lastrowid

            for line in lines:
                cursor.execute("""
                    INSERT INTO journal_entry_lines (journal_entry_id, account_id, document_type_id, tax_type_id, cost_center_id, notes, document_number, debit, credit)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (journal_entry_id, line['account_id'], line.get('document_type_id'), line.get('tax_type_id'),
                      line.get('cost_center_id'), line.get('notes'), line.get('document_number'), line['debit'], line['credit']))

            conn.commit()
            QMessageBox.information(None, "Success", "Entry saved successfully.")
            return True
        except sqlite3.Error as e:
            conn.rollback()
            QMessageBox.critical(None, "Database Error", f"Error adding journal entry: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def update_journal_entry(self, entry_id, entry_date, description, transaction_type_id, total_debit, total_credit, lines, status=None):
        """
        Updates an existing journal entry with its lines.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            update_query = """
                UPDATE journal_entries
                SET entry_date = ?, description = ?, transaction_type_id = ?,
                     total_debit = ?, total_credit = ?, updated_at = CURRENT_TIMESTAMP
            """
            params = [entry_date, description, transaction_type_id, total_debit, total_credit]

            if status is not None:
                update_query += ", status = ?"
                params.append(status)

            update_query += " WHERE id = ?"
            params.append(entry_id)

            cursor.execute(update_query, tuple(params))

            cursor.execute("DELETE FROM journal_entry_lines WHERE journal_entry_id = ?", (entry_id,))
            for line in lines:
                cursor.execute("""
                    INSERT INTO journal_entry_lines (journal_entry_id, account_id, document_type_id, tax_type_id, cost_center_id, notes, document_number, debit, credit)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (entry_id, line['account_id'], line.get('document_type_id'), line.get('tax_type_id'),
                      line.get('cost_center_id'), line.get('notes'), line.get('document_number'), line['debit'], line['credit']))

            conn.commit()
            QMessageBox.information(None, "Success", "Entry updated successfully.")
            return True
        except sqlite3.Error as e:
            conn.rollback()
            QMessageBox.critical(None, "Database Error", f"Error updating journal entry: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_journal_entry(self, entry_id):
        """
        Deletes a journal entry and its associated lines.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))
            conn.commit()
            QMessageBox.information(None, "Success", "Entry deleted successfully.")
            return True
        except sqlite3.Error as e:
            conn.rollback()
            QMessageBox.critical(None, "Database Error", f"Error deleting journal entry: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_journal_entry_by_id(self, entry_id):
        """Fetches a journal entry by ID."""
        conn = self.get_connection()
        try:
            query = "SELECT * FROM journal_entries WHERE id = ?"
            result = self.fetch_one(query, (entry_id,))
            return dict(result) if result else None
        finally:
            if conn:
                conn.close()

    def get_journal_entry_lines(self, journal_entry_id):
        """Fetches lines for a specific journal entry."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM journal_entry_lines WHERE journal_entry_id = ?", (journal_entry_id,))
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching journal entry lines: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_all_journal_entries(self):
        """Fetches all journal entries."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    JE.id, JE.entry_number, JE.entry_date, JE.description,
                    JE.total_debit, JE.total_credit, JE.status,
                    DT.name_ar AS transaction_type_name,
                FROM journal_entries JE
                LEFT JOIN Document_Types DT ON JE.transaction_type_id = DT.id
                ORDER BY JE.entry_date DESC, JE.entry_number DESC
            """)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching all journal entries: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_journal_entries_by_status(self, status):
        """Fetches journal entries by status."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    JE.id, JE.entry_number, JE.entry_date, JE.description,
                    JE.total_debit, JE.total_credit, JE.status,
                    DT.name_ar AS transaction_type_name,
                FROM journal_entries JE
                LEFT JOIN Document_Types DT ON JE.transaction_type_id = DT.id
                WHERE JE.status = ?
                ORDER BY JE.entry_date DESC, JE.entry_number DESC
            """, (status,))
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching journal entries by status: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def search_journal_entries(self, search_term):
        """
        Searches for journal entries by entry number or description.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            query = """
                SELECT
                    JE.id, JE.entry_number, JE.entry_date, JE.description,
                    JE.total_debit, JE.total_credit, JE.status,
                    DT.name_ar AS transaction_type_name,
                FROM journal_entries JE
                LEFT JOIN Document_Types DT ON JE.transaction_type_id = DT.id
                WHERE JE.entry_number LIKE ? COLLATE NOCASE OR JE.description LIKE ? COLLATE NOCASE
                ORDER BY JE.entry_date DESC, JE.entry_number DESC
            """
            params = (f'%{search_term}%', f'%{search_term}%')
            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error searching journal entries: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_journal_entries_for_account_in_range(self, account_id, start_date, end_date):
        """
        Fetches all movements (debit and credit) for a specific account within a date range
        from the journal_entry_lines table, with associated entry details.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            query = """
                SELECT
                    JE.entry_number,
                    JE.entry_date,
                    JE.description AS entry_description,
                    JEL.account_id,
                    JEL.debit,
                    JEL.credit,
                    JEL.notes AS line_notes,
                    JEL.document_number,
                    JEL.document_type_id, -- Add document_type_id here
                    DT.name_ar AS document_type_name_ar, -- Fetch document type name directly
                    -- Fetch the contra account (the other account in the same entry)
                    (SELECT account_id FROM journal_entry_lines
                     WHERE journal_entry_id = JEL.journal_entry_id AND account_id != JEL.account_id LIMIT 1) AS contra_account_id
                FROM
                    journal_entry_lines JEL
                JOIN
                    journal_entries JE ON JEL.journal_entry_id = JE.id
                LEFT JOIN -- Use LEFT JOIN in case document_type_id is null
                    document_types DT ON JEL.document_type_id = DT.id
                WHERE
                    JEL.account_id = ?
                    AND JE.entry_date BETWEEN ? AND ?
                ORDER BY
                    JE.entry_date ASC, JE.entry_number ASC;
            """
            params = (account_id, start_date, end_date)
            cursor.execute(query, params)

            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching subsidiary ledger entries: {e}")
            print(f"Error in get_journal_entries_for_account_in_range: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_journal_entries_in_range(self, start_date, end_date):
        """
        Fetches all journal entries with their lines within a specific date range.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()
            query = """
                SELECT
                    JE.id AS entry_id,
                    JE.entry_number,
                    JE.entry_date,
                    JE.description AS entry_description,
                    JE.total_debit,
                    JE.total_credit,
                    JE.status,
                    DT.name_ar AS transaction_type_name,
                    JEL.id AS line_id,
                    JEL.account_id,
                    ACC.acc_code,
                    ACC.account_name_ar,
                    JEL.debit,
                    JEL.credit,
                    JEL.notes AS line_notes,
                    JEL.document_number AS line_document_number,
                    JDT.name_ar AS line_document_type_name,
                    TT.name_ar AS line_tax_type_name,
                    CC.name_ar AS line_cost_center_name
                FROM journal_entries JE
                JOIN journal_entry_lines JEL ON JE.id = JEL.journal_entry_id
                LEFT JOIN Document_Types DT ON JE.transaction_type_id = DT.id
                LEFT JOIN Accounts ACC ON JEL.account_id = ACC.id
                LEFT JOIN Document_Types JDT ON JEL.document_type_id = JDT.id
                LEFT JOIN Tax_Types TT ON JEL.tax_type_id = TT.id
                LEFT JOIN Cost_Centers CC ON JEL.cost_center_id = CC.id
                WHERE JE.entry_date BETWEEN ? AND ?
                ORDER BY JE.entry_date ASC, JE.entry_number ASC, JEL.id ASC;
            """
            params = (start_date, end_date)
            cursor.execute(query, params)

            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching journal entries for the period: {e}")
            print(f"Error in get_journal_entries_in_range: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_general_ledger_data(self, start_date, end_date, account_id=None):
        """
        Fetches General Ledger data (opening balance, period movements, final balance)
        for individual accounts within a specified period.
        Only accounts with is_final = 0 are included.
        If an account_id is provided (and it's a non-final account), it will fetch data
        for that specific account AND all its direct and indirect descendants that are also non-final,
        each displayed on a separate line.
        If no account_id is provided, it will fetch data for ALL non-final accounts, each
        displayed on a separate line.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()

            # Determine which accounts to process
            target_account_ids = []
            if account_id:
                # Get the provided account
                selected_account = self.account_manager.get_account_by_id(account_id)
                if not selected_account or selected_account['is_final'] == 1:
                    # If account not found or is final, return empty. UI will warn.
                    return []
                
                # Get all its descendants (including itself) that are NOT final
                all_descendants = self.account_manager._get_descendant_account_ids(account_id)
                target_account_ids = [
                    acc_id for acc_id in all_descendants 
                    if self.account_manager.get_account_by_id(acc_id)['is_final'] == 0
                ]
                
                if not target_account_ids:
                    return []
            else:
                # If no specific account is provided, get all non-final accounts
                all_accounts_data = self.account_manager.get_all_accounts()
                target_account_ids = [acc['id'] for acc in all_accounts_data if acc['is_final'] == 0]
                if not target_account_ids:
                    return []

            general_ledger_report_data = []

            # Iterate through each individual non-final account ID to get its data
            for individual_account_id in target_account_ids:
                account = self.account_manager.get_account_by_id(individual_account_id)
                if not account:
                    continue # Should not happen if IDs are valid

                account_code = account['acc_code']
                account_name = account['account_name_ar']
                account_level = account['level']
                
                # Get account_side from account_type_data for the individual account
                account_type_data = self.account_manager.get_account_type_by_id(account['account_type_id'])
                account_side = account_type_data['account_side'] if account_type_data else 'Debit'

                # Opening Balance for the individual account
                opening_balance_date = datetime.strptime(start_date, "%Y-%m-%d").date() - timedelta(days=1)
                opening_balance_date_str = opening_balance_date.strftime("%Y-%m-%d")

                op_debit_total, op_credit_total, op_final_balance = self.account_manager.get_account_balance_up_to_date(individual_account_id, opening_balance_date_str)

                opening_debit_balance = 0.0
                opening_credit_balance = 0.0
                if account_side == 'Debit':
                    if op_final_balance > 0:
                        opening_debit_balance = op_final_balance
                    else:
                        opening_credit_balance = abs(op_final_balance)
                elif account_side == 'Credit':
                    if op_final_balance > 0:
                        opening_credit_balance = op_final_balance
                    else:
                        opening_debit_balance = abs(op_final_balance)

                # Period Movements for the individual account
                query_movements = """
                    SELECT
                        SUM(CASE WHEN JEL.debit IS NOT NULL THEN JEL.debit ELSE 0 END) AS period_debit,
                        SUM(CASE WHEN JEL.credit IS NOT NULL THEN JEL.credit ELSE 0 END) AS period_credit
                    FROM journal_entry_lines JEL
                    JOIN journal_entries JE ON JEL.journal_entry_id = JE.id
                    WHERE JEL.account_id = ? AND JE.entry_date BETWEEN ? AND ?
                """
                params_movements = (individual_account_id, start_date, end_date)
                cursor.execute(query_movements, params_movements)
                movement_result = cursor.fetchone()

                period_debit = movement_result[0] if movement_result and movement_result[0] is not None else 0.0
                period_credit = movement_result[1] if movement_result and movement_result[1] is not None else 0.0

                # Final Balance for the individual account
                final_balance_at_end_date = self.account_manager.get_account_balance_up_to_date(individual_account_id, end_date)[2] # Get only final balance

                final_debit_balance = 0.0
                final_credit_balance = 0.0
                if account_side == 'Debit':
                    if final_balance_at_end_date > 0:
                        final_debit_balance = final_balance_at_end_date
                    else:
                        final_credit_balance = abs(final_balance_at_end_date)
                elif account_side == 'Credit':
                    if final_balance_at_end_date > 0:
                        final_credit_balance = final_balance_at_end_date
                    else:
                        final_debit_balance = abs(final_balance_at_end_date)

                # Add the account only if it has any balances or movements
                if any([opening_debit_balance, opening_credit_balance, period_debit, period_credit, final_debit_balance, final_credit_balance]):
                    general_ledger_report_data.append({
                        'account_id': individual_account_id,
                        'acc_code': account_code,
                        'account_name_ar': account_name,
                        'account_side': account_side,
                        'level': account_level,
                        'opening_debit_balance': opening_debit_balance,
                        'opening_credit_balance': opening_credit_balance,
                        'period_debit': period_debit,
                        'period_credit': period_credit,
                        'final_debit_balance': final_debit_balance,
                        'final_credit_balance': final_credit_balance
                    })
            
            # Sort the data by account code for better readability
            general_ledger_report_data.sort(key=lambda x: x['acc_code'])

            return general_ledger_report_data

        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching General Ledger data: {e}")
            print(f"Error in get_general_ledger_data: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_trial_balance_data(self, start_date, end_date):
        """
        Fetches Trial Balance data (opening balance, period movements, final balance)
        for all accounts up to a specified date.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()

            all_accounts = self.account_manager.get_all_accounts()

            trial_balance_report_data = []

            for account in all_accounts:
                account_id = account['id']
                account_code = account['acc_code']
                account_name_ar = account['account_name_ar']
                is_balance_sheet = account['is_balance_sheet']
                account_level = account['level']

                account_type_data = self.account_manager.get_account_type_by_id(account['account_type_id'])
                account_side = account_type_data['account_side'] if account_type_data else 'Debit'

                opening_balance_date = datetime.strptime(start_date, "%Y-%m-%d").date() - timedelta(days=1)
                opening_balance_date_str = opening_balance_date.strftime("%Y-%m-%d")

                op_debit_total, op_credit_total, op_final_balance = self.account_manager.get_account_balance_up_to_date(account_id, opening_balance_date_str)

                opening_debit_balance = 0.0
                opening_credit_balance = 0.0
                if account_side == 'Debit':
                    if op_final_balance > 0:
                        opening_debit_balance = op_final_balance
                    else:
                        opening_credit_balance = abs(op_final_balance)
                elif account_side == 'Credit':
                    if op_final_balance > 0:
                        opening_credit_balance = op_final_balance
                    else:
                        opening_debit_balance = abs(op_final_balance)

                account_ids_for_movements = self.account_manager._get_descendant_account_ids(account_id)
                if not account_ids_for_movements:
                    period_debit = 0.0
                    period_credit = 0.0
                else:
                    id_placeholders = ','.join('?' * len(account_ids_for_movements))
                    query_movements = f"""
                        SELECT
                            SUM(CASE WHEN JEL.debit IS NOT NULL THEN JEL.debit ELSE 0 END) AS period_debit,
                            SUM(CASE WHEN JEL.credit IS NOT NULL THEN JEL.credit ELSE 0 END) AS period_credit
                        FROM journal_entry_lines JEL
                        JOIN journal_entries JE ON JEL.journal_entry_id = JE.id
                        WHERE JEL.account_id IN ({id_placeholders}) AND JE.entry_date BETWEEN ? AND ?
                    """
                    params_movements = list(account_ids_for_movements)
                    params_movements.extend([start_date, end_date])
                    cursor.execute(query_movements, tuple(params_movements))
                    movement_result = cursor.fetchone()

                    period_debit = movement_result[0] if movement_result and movement_result[0] is not None else 0.0
                    period_credit = movement_result[1] if movement_result and movement_result[1] is not None else 0.0

                final_balance_at_end_date = self.account_manager.get_account_balance_cumulative(account_ids_for_movements, end_date)

                final_debit_balance = 0.0
                final_credit_balance = 0.0
                if account_side == 'Debit':
                    if final_balance_at_end_date > 0:
                        final_debit_balance = final_balance_at_end_date
                    else:
                        final_credit_balance = abs(final_balance_at_end_date)
                elif account_side == 'Credit':
                    if final_balance_at_end_date > 0:
                        final_credit_balance = final_balance_at_end_date
                    else:
                        final_debit_balance = abs(final_balance_at_end_date)

                trial_balance_report_data.append({
                    'account_id': account_id,
                    'acc_code': account_code,
                    'account_name_ar': account_name_ar,
                    'account_side': account_side,
                    'is_balance_sheet': is_balance_sheet,
                    'level': account_level,
                    'opening_debit_balance': opening_debit_balance,
                    'opening_credit_balance': opening_credit_balance,
                    'period_debit': period_debit,
                    'period_credit': period_credit,
                    'final_debit_balance': final_debit_balance,
                    'final_credit_balance': final_credit_balance
                })

            return trial_balance_report_data

        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching trial balance data: {e}")
            print(f"Error in get_trial_balance_data: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_income_statement_data(self, start_date, end_date, level):
        """
        Fetches Income Statement data (revenues and expenses) at a specific level
        within a specified period, with hierarchical aggregation of balances.
        """
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            cursor = conn.cursor()

            all_accounts = self.account_manager.get_all_accounts()

            income_statement_data = []

            for account in all_accounts:
                account_type_data = self.account_manager.get_account_type_by_id(account['account_type_id'])
                if not account_type_data or account_type_data['code'] not in ('REVENUE', 'EXPENSE'):
                    continue

                if account['level'] != level:
                    continue

                account_id = account['id']
                account_code = account['acc_code']
                account_name_ar = account['account_name_ar']
                account_name_en = account['account_name_en']
                account_side = account_type_data['account_side']

                account_ids_to_sum = self.account_manager._get_descendant_account_ids(account_id)

                if not account_ids_to_sum:
                    continue

                id_placeholders = ','.join('?' * len(account_ids_to_sum))

                query_sum = f"""
                    SELECT
                        SUM(CASE WHEN JEL.debit IS NOT NULL THEN JEL.debit ELSE 0 END) AS total_debit,
                        SUM(CASE WHEN JEL.credit IS NOT NULL THEN JEL.credit ELSE 0 END) AS total_credit
                    FROM journal_entry_lines JEL
                    JOIN journal_entries JE ON JEL.journal_entry_id = JE.id
                    WHERE JEL.account_id IN ({id_placeholders})
                    AND JE.entry_date BETWEEN ? AND ?
                """
                params_sum = list(account_ids_to_sum)
                params_sum.extend([start_date, end_date])

                cursor.execute(query_sum, tuple(params_sum))
                result = cursor.fetchone()

                total_debit = result[0] if result and result[0] is not None else 0.0
                total_credit = result[1] if result and result[1] is not None else 0.0

                net_movement = 0.0
                if account_side == 'Debit':
                    net_movement = total_debit - total_credit
                else:
                    net_movement = total_credit - total_debit

                income_statement_data.append({
                    'account_id': account_id,
                    'acc_code': account_code,
                    'account_name_ar': account_name_ar,
                    'account_name_en': account_name_en,
                    'account_side': account_side,
                    'level': account['level'],
                    'total_debit': total_debit,
                    'total_credit': total_credit,
                    'net_movement': net_movement
                })

            return income_statement_data

        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching income statement data: {e}")
            print(f"Error in get_income_statement_data: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def create_year_end_closing_entry(self, year_id, end_date, net_income):
        """
        Creates the actual year-end closing entry.
        (This is a simplified version and needs more detailed logic)
        """
        conn = self.get_connection()
        try:
            print(f"Simulation: Creating closing entry for year {year_id} with net income {net_income}")
            query = "UPDATE financial_years SET is_closed = 1 WHERE id = ?"
            self.execute_query(query, (year_id,))
            conn.commit()
            return True, "Closing process simulated successfully."
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Database error in create_year_end_closing_entry: {e}")
            return False, f"Database error: {e}"
        finally:
            if conn:
                conn.close()

    def reverse_closing_entry(self, year_id):
        """
        Reverses a financial year closing. (Simplified version and needs more detailed logic)
        In a real application, this would involve:
        1. Deleting the closing entry that was created.
        2. Updating the financial year status to 'open'.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Check if the year is already open
            cursor.execute("SELECT is_closed FROM financial_years WHERE id = ?", (year_id,))
            if cursor.fetchone()[0] == 0:
                return False, "Financial year is already open."

            # Simulate deleting the closing entry
            # (Here there should be logic to delete the real entry)
            
            # Update financial year status to open
            query = "UPDATE financial_years SET is_closed = 0, closing_entry_id = NULL WHERE id = ?"
            self.execute_query(query, (year_id,))
            conn.commit()
            return True, "Reopening process simulated successfully."
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Database error in reverse_closing_entry: {e}")
            return False, f"Database error: {e}"
        finally:
            if conn:
                conn.close()

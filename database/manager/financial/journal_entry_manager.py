# database/manager/journal_entry_manager.py

import sqlite3
import os
import sys
from PyQt5.QtWidgets import QMessageBox

# =====================================================================
# تصحيح مسار المشروع الجذر
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.base_manager import BaseManager

class JournalEntryManager(BaseManager):
    """
    مسؤول عن العمليات الأساسية على قيود اليومية (إضافة، تعديل، حذف، بحث).
    """
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func)
        print(f"DEBUG: JournalEntryManager initialized from {__file__}.")

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

    def add_journal_entry(self, entry_date, system_date, description, transaction_type_id,  total_debit, total_credit, lines, status='Under Review', created_by=None):
        """Adds a new journal entry with its lines."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()

            entry_number = self._generate_next_entry_number()
            if entry_number is None:
                return False

            cursor.execute("""
                INSERT INTO journal_entries (entry_number, entry_date, description, transaction_type_id, total_debit, total_credit, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
        """Updates an existing journal entry with its lines."""
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
            params = [entry_date, description, transaction_type_id,total_debit, total_credit]

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
        """Deletes a journal entry and its associated lines."""
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
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = "SELECT * FROM journal_entries WHERE id = ?"
            cursor.execute(query, (entry_id,))
            result = cursor.fetchone()
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
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM journal_entry_lines WHERE journal_entry_id = ?", (journal_entry_id,))
            return [dict(row) for row in cursor.fetchall()]
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
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    JE.id, JE.entry_number, JE.entry_date, JE.description,
                    JE.total_debit, JE.total_credit, JE.status,
                    DT.name_ar AS transaction_type_name
                FROM journal_entries JE
                LEFT JOIN Document_Types DT ON JE.transaction_type_id = DT.id
                ORDER BY JE.entry_date DESC, JE.entry_number DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error fetching all journal entries: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def search_journal_entries(self, search_term):
        """Searches for journal entries by entry number or description."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return []
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = """
                SELECT
                    JE.id, JE.entry_number, JE.entry_date, JE.description,
                    JE.total_debit, JE.total_credit, JE.status,
                    DT.name_ar AS transaction_type_name
                FROM journal_entries JE
                LEFT JOIN Document_Types DT ON JE.transaction_type_id = DT.id
                WHERE JE.entry_number LIKE ? COLLATE NOCASE OR JE.description LIKE ? COLLATE NOCASE
                ORDER BY JE.entry_date DESC, JE.entry_number DESC
            """
            params = (f'%{search_term}%', f'%{search_term}%')
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error searching journal entries: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def set_journal_entry_status(self, journal_id, new_status):
        """Updates the status of a journal entry."""
        conn = None
        try:
            conn = self.get_connection()
            if conn is None: return False
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE journal_entries
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_status, journal_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            conn.rollback()
            QMessageBox.critical(None, "Database Error", f"Error updating entry status: {e}")
            return False
        finally:
            if conn:
                conn.close()

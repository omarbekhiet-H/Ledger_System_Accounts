# database/manager/financial_year_manager.py

import sqlite3
import os
import sys
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QMessageBox

# =====================================================================
# تصحيح مسار المشروع الجذر
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.base_manager import BaseManager

class FinancialYearManager(BaseManager):
    """
    مسؤول عن إدارة السنوات المالية (إنشاء، إقفال، إعادة فتح).
    """
    def __init__(self, get_connection_func):
        super().__init__(get_connection_func)
        print(f"DEBUG: FinancialYearManager initialized from {__file__}.")

    def get_all_financial_years(self):
        """Retrieves all financial years from the database."""
        conn = self.get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, year_name, start_date, end_date, is_closed FROM financial_years ORDER BY start_date DESC")
            return [dict(year) for year in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error in get_all_financial_years: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def create_financial_year(self):
        """Creates a new financial year."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM financial_years WHERE is_closed = 0")
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(None, "Error", "The current financial year must be closed before creating a new one.")
                return False

            cursor.execute("SELECT MAX(end_date) FROM financial_years")
            last_end_date_str = cursor.fetchone()[0]

            if last_end_date_str:
                last_end_date = datetime.strptime(last_end_date_str, '%Y-%m-%d').date()
                start_date = last_end_date + timedelta(days=1)
            else:
                start_date = datetime.now().date().replace(month=1, day=1)

            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
            year_name = f"Financial Year {start_date.year}"
            
            query = "INSERT INTO financial_years (year_name, start_date, end_date, is_closed) VALUES (?, ?, ?, 0)"
            params = (year_name, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            cursor.execute(query, params)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error in create_financial_year: {e}")
            conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def calculate_net_income(self, end_date):
        """Calculates net income/loss up to a certain date. (Simulation)"""
        print(f"Simulation: Calculating net income up to {end_date}")
        return 150000.75 

    def create_year_end_closing_entry(self, year_id):
        """Creates the year-end closing entry. (Simulation)"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT is_closed FROM financial_years WHERE id = ?", (year_id,))
            if cursor.fetchone()[0] == 1:
                return False, "Financial year is already closed."
            
            query = "UPDATE financial_years SET is_closed = 1 WHERE id = ?"
            cursor.execute(query, (year_id,))
            conn.commit()
            return True, "Closing process simulated successfully."
        except sqlite3.Error as e:
            conn.rollback()
            return False, f"Database error: {e}"
        finally:
            if conn:
                conn.close()

    def reverse_closing_entry(self, year_id):
        """Reverses a financial year closing. (Simulation)"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT is_closed FROM financial_years WHERE id = ?", (year_id,))
            if cursor.fetchone()[0] == 0:
                return False, "Financial year is already open."
            
            query = "UPDATE financial_years SET is_closed = 0, closing_entry_id = NULL WHERE id = ?"
            cursor.execute(query, (year_id,))
            conn.commit()
            return True, "Reopening process simulated successfully."
        except sqlite3.Error as e:
            conn.rollback()
            

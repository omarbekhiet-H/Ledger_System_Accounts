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

from database.db_connection import get_financials_db_connection
from database.base_manager import BaseManager

class FinancialYearManager(BaseManager):
    """
    مسؤول عن إدارة السنوات المالية (إنشاء، إقفال، إعادة فتح).
    """
    def __init__(self, get_connection_func=get_financials_db_connection):
        super().__init__(get_connection_func)
        print(f"DEBUG: FinancialYearManager initialized from {__file__}.")

    def get_all_financial_years(self):
        conn = self.get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, year_name, start_date, end_date, is_closed, closing_entry_id 
                FROM financial_years 
                ORDER BY start_date DESC
            """)
            return [dict(year) for year in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error in get_all_financial_years: {e}")
            return []
        finally:
            conn.close()

    def get_financial_year_by_id(self, year_id):
        conn = self.get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, year_name, start_date, end_date, is_closed, closing_entry_id 
                FROM financial_years 
                WHERE id = ?
            """, (year_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        except sqlite3.Error as e:
            print(f"Database error in get_financial_year_by_id: {e}")
            return None
        finally:
            conn.close()

    def get_active_financial_year(self):
        conn = self.get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, year_name, start_date, end_date 
                FROM financial_years 
                WHERE is_closed = 0 
                ORDER BY start_date DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            return dict(result) if result else None
        except sqlite3.Error as e:
            print(f"Database error in get_active_financial_year: {e}")
            return None
        finally:
            conn.close()

    def create_financial_year(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM financial_years WHERE is_closed = 0")
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(None, "خطأ", "يجب إقفال السنة المالية الحالية قبل إنشاء سنة جديدة.")
                return False

            cursor.execute("SELECT MAX(end_date) FROM financial_years")
            last_end_date_str = cursor.fetchone()[0]
            retained_earnings = self.calculate_retained_earnings()

            if last_end_date_str:
                last_end_date = datetime.strptime(last_end_date_str, '%Y-%m-%d').date()
                start_date = last_end_date + timedelta(days=1)
            else:
                start_date = datetime.now().date().replace(month=1, day=1)

            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
            year_name = f"السنة المالية {start_date.year}"

            query = "INSERT INTO financial_years (year_name, start_date, end_date, is_closed) VALUES (?, ?, ?, 0)"
            params = (year_name, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            cursor.execute(query, params)
            conn.commit()

            QMessageBox.information(None, "نجاح", f"تم إنشاء السنة المالية الجديدة: {year_name}\nالأرباح المحتجزة المنقولة: {retained_earnings:,.2f}")
            return True

        except sqlite3.Error as e:
            print(f"Database error in create_financial_year: {e}")
            conn.rollback()
            QMessageBox.critical(None, "خطأ", f"فشل في إنشاء السنة المالية: {e}")
            return False
        finally:
            conn.close()

    def create_year_end_closing_entry(self, year_id, revenue_account_id, expense_account_id, retained_earnings_account_id):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT year_name, start_date, end_date, is_closed FROM financial_years WHERE id = ?", (year_id,))
            row = cursor.fetchone()
            if not row:
                return False, "السنة غير موجودة"

            year_name, start_date, end_date, is_closed = row
            if is_closed:
                return False, "السنة مقفلة بالفعل"

            revenues, expenses, net_income = self.calculate_year_figures(start_date, end_date)

            cursor.execute("SELECT COALESCE(MAX(CAST(entry_number AS INTEGER)), 0) + 1 FROM journal_entries")
            next_number_int = cursor.fetchone()[0]
            next_number = str(next_number_int).zfill(6)

            desc = f"قيد إقفال السنة {year_name}"
            cursor.execute("""
                INSERT INTO journal_entries 
                    (entry_number, entry_date, description, transaction_type_id, currency_id, exchange_rate, total_debit, total_credit, status)
                VALUES (?, ?, ?, ?, ?, 1.0, ?, ?, 'معتمد')
            """, (
                next_number,
                end_date,
                desc,
                1,
                1,
                revenues,
                expenses
            ))
            closing_entry_id = cursor.lastrowid

            if revenues > 0:
                cursor.execute("""
                    INSERT INTO journal_entry_lines (journal_entry_id, account_id, debit, credit, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (closing_entry_id, revenue_account_id, revenues, 0, "إقفال الإيرادات"))
                cursor.execute("""
                    INSERT INTO journal_entry_lines (journal_entry_id, account_id, debit, credit, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (closing_entry_id, retained_earnings_account_id, 0, revenues, "تحويل الإيرادات إلى الأرباح المحتجزة"))

            if expenses > 0:
                cursor.execute("""
                    INSERT INTO journal_entry_lines (journal_entry_id, account_id, debit, credit, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (closing_entry_id, retained_earnings_account_id, expenses, 0, "تحميل المصروفات على الأرباح المحتجزة"))
                cursor.execute("""
                    INSERT INTO journal_entry_lines (journal_entry_id, account_id, debit, credit, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (closing_entry_id, expense_account_id, 0, expenses, "إقفال المصروفات"))

            cursor.execute("""
                UPDATE financial_years
                SET is_closed = 1,
                    closing_entry_id = ?
                WHERE id = ?
            """, (closing_entry_id, year_id))

            conn.commit()
            return True, f"تم إقفال السنة {year_name} ✅\nرقم القيد: {next_number} | صافي الربح: {net_income:,.2f}"

        except Exception as e:
            conn.rollback()
            return False, f"⚠️ خطأ أثناء إنشاء قيد الإقفال: {e}"
        finally:
            conn.close()

    def reverse_closing_entry(self, year_id):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT closing_entry_id FROM financial_years WHERE id = ?", (year_id,))
            row = cursor.fetchone()
            if not row or not row[0]:
                return False, "لا يوجد قيد إقفال مرتبط بهذه السنة."

            closing_entry_id = row[0]
            cursor.execute("DELETE FROM journal_entry_lines WHERE journal_entry_id = ?", (closing_entry_id,))
            cursor.execute("DELETE FROM journal_entries WHERE id = ?", (closing_entry_id,))

            cursor.execute("""
                UPDATE financial_years
                SET is_closed = 0,
                    closing_entry_id = NULL
                WHERE id = ?
            """, (year_id,))

            conn.commit()
            return True, "تم التراجع عن الإقفال وإعادة فتح السنة بنجاح."

        except Exception as e:
            conn.rollback()
            return False, f"خطأ أثناء التراجع عن الإقفال: {e}"
        finally:
            conn.close()

    def calculate_net_income(self, end_date):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            query = """
            SELECT 
                (SELECT COALESCE(SUM(jel.credit - jel.debit), 0) 
                 FROM journal_entry_lines jel
                 JOIN journal_entries je ON jel.journal_entry_id = je.id
                 JOIN accounts a ON jel.account_id = a.id
                 JOIN account_types at ON a.account_type_id = at.id
                 WHERE at.code IN ('REVENUE') AND je.entry_date <= ?) 
                -
                (SELECT COALESCE(SUM(jel.debit - jel.credit), 0) 
                 FROM journal_entry_lines jel
                 JOIN journal_entries je ON jel.journal_entry_id = je.id
                 JOIN accounts a ON jel.account_id = a.id
                 JOIN account_types at ON a.account_type_id = at.id
                 WHERE at.code IN ('EXPENSE') AND je.entry_date <= ?)
            AS net_income
            """
            cursor.execute(query, (end_date, end_date))
            result = cursor.fetchone()
            return result[0] if result else 0.00
        except sqlite3.Error as e:
            print(f"Database error in calculate_net_income: {e}")
            return 0.00
        finally:
            conn.close()

    def calculate_year_figures(self, start_date, end_date):
        """حساب إجمالي الإيرادات والمصروفات وصافي الدخل"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            revenues_query = """
            SELECT COALESCE(SUM(jel.credit - jel.debit), 0)
            FROM journal_entry_lines jel
            JOIN journal_entries je ON jel.journal_entry_id = je.id
            JOIN accounts a ON jel.account_id = a.id
            JOIN account_types at ON a.account_type_id = at.id
            WHERE at.code = 'REVENUE' AND je.entry_date BETWEEN ? AND ?
            """
            cursor.execute(revenues_query, (start_date, end_date))
            revenues = cursor.fetchone()[0] or 0.00

            expenses_query = """
            SELECT COALESCE(SUM(jel.debit - jel.credit), 0)
            FROM journal_entry_lines jel
            JOIN journal_entries je ON jel.journal_entry_id = je.id
            JOIN accounts a ON jel.account_id = a.id
            JOIN account_types at ON a.account_type_id = at.id
            WHERE at.code = 'EXPENSE' AND je.entry_date BETWEEN ? AND ?
            """
            cursor.execute(expenses_query, (start_date, end_date))
            expenses = cursor.fetchone()[0] or 0.00

            return revenues, expenses, revenues - expenses
        except sqlite3.Error as e:
            print(f"Database error in calculate_year_figures: {e}")
            return 0.00, 0.00, 0.00
        finally:
            conn.close()

    def validate_year_for_closing(self, year_id):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) 
                FROM journal_entries 
                WHERE status = 'Under Review' 
                AND entry_date BETWEEN 
                    (SELECT start_date FROM financial_years WHERE id = ?) 
                    AND 
                    (SELECT end_date FROM financial_years WHERE id = ?)
            """, (year_id, year_id))
            pending_entries = cursor.fetchone()[0]
            if pending_entries > 0:
                return False, f"يوجد {pending_entries} قيد تحت المراجعة. يجب الموافقة عليها أولاً."
            return True, "السنة المالية جاهزة للإقفال."
        except sqlite3.Error as e:
            return False, f"خطأ في التحقق: {e}"
        finally:
            conn.close()

    def get_financial_year_by_date(self, target_date):
        conn = self.get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, year_name, start_date, end_date, is_closed
                FROM financial_years 
                WHERE start_date <= ? AND end_date >= ?
                LIMIT 1
            """, (target_date, target_date))
            result = cursor.fetchone()
            return dict(result) if result else None
        except sqlite3.Error as e:
            print(f"Database error in get_financial_year_by_date: {e}")
            return None
        finally:
            conn.close()

    def get_years_status(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, year_name, start_date, end_date, is_closed,
                       (SELECT entry_number FROM journal_entries WHERE id = closing_entry_id) as closing_entry_number
                FROM financial_years 
                ORDER BY start_date ASC
            """)
            years = []
            for row in cursor.fetchall():
                year = {
                    'id': row[0],
                    'year_name': row[1],
                    'start_date': row[2],
                    'end_date': row[3],
                    'is_closed': bool(row[4]),
                    'closing_entry': row[5] or 'N/A',
                    'status': 'مقفلة' if row[4] else 'مفتوحة'
                }
                years.append(year)
            return years
        except sqlite3.Error as e:
            print(f"Database error in get_years_status: {e}")
            return []
        finally:
            conn.close()

    def close_previous_years(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, year_name, start_date, end_date 
                FROM financial_years 
                WHERE is_closed = 0 
                ORDER BY start_date ASC
            """)
            open_years = cursor.fetchall()
            results = []
            for year in open_years:
                year_id, year_name, start_date, end_date = year
                net_income = self.calculate_net_income(end_date)
                success, message = self.create_year_end_closing_entry(year_id, None, None, None)
                if success:
                    results.append(f"تم إقفال السنة '{year_name}' بصافي ربح: {net_income:,.2f}")
                else:
                    results.append(f"فشل إقفال السنة '{year_name}': {message}")
            conn.commit()
            return True, results
        except sqlite3.Error as e:
            conn.rollback()
            return False, [f"خطأ في قاعدة البيانات: {e}"]
        finally:
            conn.close()

    def calculate_retained_earnings(self, as_of_date=None):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if as_of_date is None:
                as_of_date = datetime.now().strftime('%Y-%m-%d')
            query = """
            SELECT 
                (SELECT COALESCE(SUM(jel.credit - jel.debit), 0) 
                 FROM journal_entry_lines jel
                 JOIN journal_entries je ON jel.journal_entry_id = je.id
                 JOIN accounts a ON jel.account_id = a.id
                 JOIN account_types at ON a.account_type_id = at.id
                 WHERE at.code IN ('REVENUE') AND je.entry_date <= ?) 
                -
                (SELECT COALESCE(SUM(jel.debit - jel.credit), 0) 
                 FROM journal_entry_lines jel
                 JOIN journal_entries je ON jel.journal_entry_id = je.id
                 JOIN accounts a ON jel.account_id = a.id
                 JOIN account_types at ON a.account_type_id = at.id
                 WHERE at.code IN ('EXPENSE') AND je.entry_date <= ?)
            AS retained_earnings
            """
            cursor.execute(query, (as_of_date, as_of_date))
            result = cursor.fetchone()
            return result[0] if result else 0.00
        except sqlite3.Error as e:
            print(f"Database error in calculate_retained_earnings: {e}")
            return 0.00
        finally:
            conn.close()

    def get_detailed_years_report(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, year_name, start_date, end_date, is_closed, closing_entry_id
                FROM financial_years 
                ORDER BY start_date ASC
            """)
            detailed_years = []
            for row in cursor.fetchall():
                year_id, year_name, start_date, end_date, is_closed, closing_entry_id = row
                revenues, expenses, net_income = self.calculate_year_figures(start_date, end_date)
                closing_entry_number = "N/A"
                if closing_entry_id:
                    cursor2 = conn.cursor()
                    cursor2.execute("SELECT entry_number FROM journal_entries WHERE id = ?", (closing_entry_id,))
                    result = cursor2.fetchone()
                    if result:
                        closing_entry_number = result[0]
                detailed_years.append({
                    'id': year_id,
                    'year_name': year_name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'is_closed': bool(is_closed),
                    'closing_entry': closing_entry_number,
                    'status': 'مقفلة' if is_closed else 'مفتوحة',
                    'revenues': revenues,
                    'expenses': expenses,
                    'net_income': net_income
                })
            return detailed_years
       

        
        except sqlite3.Error as e:
            print(f"Database error in get_detailed_years_report: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def calculate_year_figures(self, start_date, end_date):
        """حساب الإيرادات والمصروفات لفترة محددة"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
        
            # حساب الإيرادات
            revenues_query = """
            SELECT COALESCE(SUM(jel.credit - jel.debit), 0)
            FROM journal_entry_lines jel
            JOIN journal_entries je ON jel.journal_entry_id = je.id
            JOIN accounts a ON jel.account_id = a.id
            JOIN account_types at ON a.account_type_id = at.id
            WHERE at.code IN ('REVENUE') 
            AND je.entry_date BETWEEN ? AND ?
            """
            cursor.execute(revenues_query, (start_date, end_date))
            revenues = cursor.fetchone()[0] or 0.00
        
            # حساب المصروفات
            expenses_query = """
            SELECT COALESCE(SUM(jel.debit - jel.credit), 0)
            FROM journal_entry_lines jel
            JOIN journal_entries je ON jel.journal_entry_id = je.id
            JOIN accounts a ON jel.account_id = a.id
            JOIN account_types at ON a.account_type_id = at.id
            WHERE at.code IN ('EXPENSE') 
            AND je.entry_date BETWEEN ? AND ?
            """
            cursor.execute(expenses_query, (start_date, end_date))
            expenses = cursor.fetchone()[0] or 0.0
        
            return revenues, expenses, revenues - expenses
        
        except sqlite3.Error as e:
            print(f"Database error in calculate_year_figures: {e}")
            return 0.00, 0.00, 0.00
        finally:
            if conn:
                conn.close()

    def get_pending_entries(self, year_id):
        """إرجاع جميع القيود المعلقة لسنة معينة (اعتمادًا على تاريخ القيد)"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # جلب فترة السنة (start_date, end_date)
            cursor.execute("SELECT start_date, end_date FROM financial_years WHERE id = ?", (year_id,))
            row = cursor.fetchone()
            if not row:
                return []

            start_date, end_date = row

            # القيود المعلقة بين تاريخ بداية ونهاية السنة
            cursor.execute("""
                SELECT id, entry_number, entry_date, description, total_debit, total_credit, status
                FROM journal_entries
                WHERE entry_date BETWEEN ? AND ?
                AND status != 'معتمد'
            """, (start_date, end_date))

            return cursor.fetchall()
        except Exception as e:
            print("Error fetching pending entries:", e)
            return []
        finally:
            conn.close()

    def update_year_closing_metadata(
        self,
        year_id,
        legal_reserve_account_id,
        legal_reserve_percent,
        income_tax_account_id,
        income_tax_percent,
        solidarity_tax_account_id,
        solidarity_tax_percent,
        closed_at,
        closed_by_user_id
    ):
        """
        تحديث بيانات إقفال السنة المالية بعد إنشاء قيد الإقفال
        """
        try:
            conn = self.db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE financial_years
                SET legal_reserve_account_id = ?,
                    legal_reserve_percent = ?,
                    income_tax_account_id = ?,
                    income_tax_percent = ?,
                    solidarity_tax_account_id = ?,
                    solidarity_tax_percent = ?,
                    closed_at = ?,
                    closed_by_user_id = ?
                WHERE id = ?
            """, (
                legal_reserve_account_id,
                legal_reserve_percent,
                income_tax_account_id,
                income_tax_percent,
                solidarity_tax_account_id,
                solidarity_tax_percent,
                closed_at,
                closed_by_user_id,
                year_id
            ))
            conn.commit()
            conn.close()
            return True, "تم تحديث بيانات الإقفال بنجاح"
        except Exception as e:
            return False, f"خطأ أثناء تحديث بيانات الإقفال: {e}"
        

# إنشاء نسخة من المدير للاستخدام المباشر
financial_year_manager = FinancialYearManager(get_financials_db_connection)
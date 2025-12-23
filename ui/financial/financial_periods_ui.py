# ui/financial/financial_periods_ui.py
# -*- coding: utf-8 -*-
import sys
import os
from datetime import datetime, date
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QApplication, QStyle, QDialog, QFormLayout, QAbstractItemView,
    QComboBox, QDoubleSpinBox, QDialogButtonBox, QDateEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

# ---------------------------------------------------------------------
# ضبط مسار المشروع الجذر
# ---------------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import managers و DB connection
from database.db_connection import get_financials_db_connection
try:
    from database.manager.financial.transactions.financial_year_manager import FinancialYearManager
except Exception:
    FinancialYearManager = None

# session المستخدم الحالي (اختياري)
try:
    from database.manager.admin import session
except Exception:
    session = None

# ---------------------------
# مساعدات للتعامل مع أعمدة الجدول
# ---------------------------
def _table_columns(conn, table_name):
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        rows = cur.fetchall()
        return [r[1] for r in rows]
    except Exception:
        return []

def _get_user_fullname(conn, user_id):
    try:
        if not user_id:
            return ""
        cur = conn.cursor()
        cur.execute("SELECT full_name FROM users WHERE id = ?", (user_id,))
        r = cur.fetchone()
        return r[0] if r else ""
    except Exception:
        return ""

# =====================================================================
# YearSelectionDialog - اختيار السنة + تواريخ البداية والنهاية يدويًا
# =====================================================================
class YearSelectionDialog(QDialog):
    def __init__(self, existing_years=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إنشاء / تعديل سنة مالية")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(480, 240)
        self.existing_years = existing_years or []
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)

        self.year_combo = QComboBox()
        current_year = date.today().year
        for y in range(current_year - 3, current_year + 6):
            self.year_combo.addItem(str(y))
        self.year_combo.currentIndexChanged.connect(self._on_year_changed)
        layout.addRow("السنة:", self.year_combo)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        layout.addRow("تاريخ البداية:", self.start_date_edit)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        layout.addRow("تاريخ النهاية:", self.end_date_edit)

        info = QLabel("افتراضياً تُملأ تواريخ البداية والنهاية لتطابق السنة المختارة. يمكنك تعديلها يدوياً.")
        info.setWordWrap(True)
        layout.addRow(info)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self._on_year_changed()

    def _on_year_changed(self):
        try:
            y = int(self.year_combo.currentText())
        except Exception:
            y = date.today().year
        self.start_date_edit.setDate(QDate(y, 1, 1))
        self.end_date_edit.setDate(QDate(y, 12, 31))

    def _on_accept(self):
        sd = self.start_date_edit.date().toPyDate()
        ed = self.end_date_edit.date().toPyDate()
        if sd > ed:
            QMessageBox.warning(self, "خطأ تواريخ", "تاريخ البداية يجب أن يكون قبل أو مساوي لتاريخ النهاية.")
            return
        self.accept()

    def get_selected_data(self):
        return {
            "year": int(self.year_combo.currentText()),
            "start_date": self.start_date_edit.date().toString("yyyy-MM-dd"),
            "end_date": self.end_date_edit.date().toString("yyyy-MM-dd")
        }

# =====================================================================
# AccountSelectionDialog - اختيار حسابات الإقفال
# =====================================================================
class AccountSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("اختيار حسابات الإقفال")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(520, 480)
        self.init_ui()
        self.load_accounts()

    def init_ui(self):
        layout = QVBoxLayout(self)
        title_label = QLabel("إعدادات قيد الإقفال السنوي")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        form_layout = QFormLayout()

        self.revenue_combo = QComboBox(); self.revenue_combo.setEditable(True)
        form_layout.addRow("حساب الإيرادات:", self.revenue_combo)

        self.expense_combo = QComboBox(); self.expense_combo.setEditable(True)
        form_layout.addRow("حساب المصروفات:", self.expense_combo)

        self.retained_combo = QComboBox(); self.retained_combo.setEditable(True)
        form_layout.addRow("الأرباح المحتجزة:", self.retained_combo)

        self.legal_combo = QComboBox(); self.legal_combo.setEditable(True)
        self.legal_percent = QDoubleSpinBox(); self.legal_percent.setRange(0,100); self.legal_percent.setDecimals(2); self.legal_percent.setSuffix(" %")
        row_layout = QHBoxLayout(); row_layout.addWidget(self.legal_combo); row_layout.addWidget(self.legal_percent)
        form_layout.addRow("الاحتياطي القانوني:", row_layout)

        self.tax_combo = QComboBox(); self.tax_combo.setEditable(True)
        self.tax_percent = QDoubleSpinBox(); self.tax_percent.setRange(0,100); self.tax_percent.setDecimals(2); self.tax_percent.setSuffix(" %")
        row_layout2 = QHBoxLayout(); row_layout2.addWidget(self.tax_combo); row_layout2.addWidget(self.tax_percent)
        form_layout.addRow("ضريبة الدخل:", row_layout2)

        self.solidarity_combo = QComboBox(); self.solidarity_combo.setEditable(True)
        self.solidarity_percent = QDoubleSpinBox(); self.solidarity_percent.setRange(0,100); self.solidarity_percent.setDecimals(2); self.solidarity_percent.setSuffix(" %")
        row_layout3 = QHBoxLayout(); row_layout3.addWidget(self.solidarity_combo); row_layout3.addWidget(self.solidarity_percent)
        form_layout.addRow("ضريبة التضامن:", row_layout3)

        user_label = QLabel(session.current_user['full_name'] if session and getattr(session, 'current_user', None) else "غير معروف")
        form_layout.addRow("المستخدم المغلق:", user_label)

        date_label = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M"))
        form_layout.addRow("تاريخ الإقفال:", date_label)

        layout.addLayout(form_layout)

        btns = QHBoxLayout()
        self.ok_button = QPushButton("تنفيذ الإقفال"); self.ok_button.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("إلغاء"); self.cancel_button.setStyleSheet("background-color: #c0392b; color: white;")
        self.cancel_button.clicked.connect(self.reject)
        btns.addWidget(self.ok_button); btns.addWidget(self.cancel_button)
        layout.addLayout(btns)

    def load_accounts(self):
        try:
            from database.manager.account_manager import AccountManager
            acc_mgr = AccountManager(get_financials_db_connection)
            accounts = acc_mgr.get_all_accounts()
            for acc in accounts:
                display = f"{acc['acc_code']} - {acc.get('account_name_ar') or acc.get('account_name_en','')}"
                for combo in (self.revenue_combo, self.expense_combo, self.retained_combo, self.legal_combo, self.tax_combo, self.solidarity_combo):
                    combo.addItem(display, acc['id'])
        except Exception as e:
            QMessageBox.warning(self, "خطأ تحميل الحسابات", f"حدث خطأ أثناء تحميل الحسابات: {e}")

    def get_selected(self):
        return {
            "revenues_account_id": self.revenue_combo.currentData(),
            "expenses_account_id": self.expense_combo.currentData(),
            "retained_earnings_account_id": self.retained_combo.currentData(),
            "legal_reserve_account_id": self.legal_combo.currentData(),
            "legal_reserve_percent": self.legal_percent.value(),
            "income_tax_account_id": self.tax_combo.currentData(),
            "income_tax_percent": self.tax_percent.value(),
            "solidarity_tax_account_id": self.solidarity_combo.currentData(),
            "solidarity_tax_percent": self.solidarity_percent.value(),
            "closed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "closed_by_user_id": session.current_user['id'] if session and getattr(session, 'current_user', None) else None
        }
    
# =====================================================================
# Main Window - إدارة الفترات المالية
# =====================================================================
class FinancialPeriodsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.financial_year_manager = FinancialYearManager(get_financials_db_connection) if FinancialYearManager else None
        self.setWindowTitle("إدارة الفترات المالية والإقفال السنوي")
        self.setGeometry(100, 100, 1300, 700)
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_financial_years()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("إدارة الفترات المالية والإقفال السنوي")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # الأزرار
        actions = QHBoxLayout()
        self.new_btn = QPushButton("سنة جديدة"); self.new_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        self.new_btn.clicked.connect(self.create_new_financial_year)

        self.edit_btn = QPushButton("تعديل سنة"); self.edit_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogContentsView))
        self.edit_btn.clicked.connect(self.edit_financial_year)

        self.delete_btn = QPushButton("حذف سنة"); self.delete_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.delete_btn.clicked.connect(self.delete_financial_year)

        self.refresh_btn = QPushButton("تحديث"); self.refresh_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.refresh_btn.clicked.connect(self.load_financial_years)

        self.close_btn = QPushButton("تنفيذ الإقفال"); self.close_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.close_btn.clicked.connect(self.execute_year_end_closing)

        self.reopen_btn = QPushButton("فك الإقفال"); self.reopen_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.reopen_btn.clicked.connect(self.reopen_financial_year)

        for b in (self.new_btn, self.edit_btn, self.delete_btn, self.refresh_btn, self.close_btn, self.reopen_btn):
            actions.addWidget(b)
        layout.addLayout(actions)

        self.info_label = QLabel("حدد سنة مالية")
        self.info_label.setStyleSheet("background:#f7f7f7; padding:6px;")
        layout.addWidget(self.info_label)

        # الجدول
        # Columns mapping:
        # 0: ID(hidden)
        # 1: year_name
        # 2: start_date
        # 3: end_date
        # 4: status
        # 5: created_by (full name)
        # 6: created_at
        # 7: updated_by (full name)
        # 8: updated_at
        # 9: total_revenues
        # 10: total_expenses
        # 11: net_income
        self.table = QTableWidget()
        self.table.setColumnCount(13)
    
        self.table.setHorizontalHeaderLabels([
            "ID", "اسم السنة", "بداية", "نهاية", "الحالة",
            "المنشئ", "تاريخ الإنشاء", "آخر معدل", "تاريخ التعديل",
            "إجمالي الإيرادات", "إجمالي المصروفات", "صافي الربح", "رقم القيد"
        ])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_year_selected)
        layout.addWidget(self.table)
        
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)

    def on_cell_double_clicked(self, row, column):
        if column == 12:  # عمود رقم القيد
            item = self.table.item(row, column)
            entry_id = item.data(Qt.UserRole)
            if entry_id:
                self.show_journal_entry_details(entry_id)


    # -----------------------------------------------------------------
    # حذف سنة (مفتوحة فقط)
    # -----------------------------------------------------------------
    def delete_financial_year(self):
        items = self.table.selectedItems()
        if not items:
            QMessageBox.warning(self, "تحذير", "اختر سنة مالية لحذفها.")
            return
        row = items[0].row()
        year_id = int(self.table.item(row, 0).text())
        year_name = self.table.item(row, 1).text()
        status = self.table.item(row, 4).text()

        if status.strip() == "مقفلة":
            QMessageBox.warning(self, "غير مسموح", f"السنة '{year_name}' مقفلة ولا يمكن حذفها.")
            return

        reply = QMessageBox.question(self, "تأكيد", f"هل تريد حذف السنة '{year_name}'؟", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        try:
            conn = get_financials_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM financial_years WHERE id = ?", (year_id,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "تم", f"تم حذف السنة '{year_name}'.")
            self.load_financial_years()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل حذف السنة: {e}")

    # -----------------------------------------------------------------
    # تعديل سنة (مفتوحة فقط) - يفتح YearSelectionDialog ويحدّث السجل
    # -----------------------------------------------------------------
    def edit_financial_year(self):
        items = self.table.selectedItems()
        if not items:
            QMessageBox.warning(self, "تحذير", "اختر سنة مالية لتعديلها.")
            return

        row = items[0].row()
        try:
            year_id = int(self.table.item(row, 0).text())
        except Exception:
            QMessageBox.critical(self, "خطأ", "تعذر قراءة المعرف (ID) للسنة المحددة.")
            return

        year_name = self.table.item(row, 1).text()
        start_date = self.table.item(row, 2).text()
        end_date = self.table.item(row, 3).text()
        status = self.table.item(row, 4).text()

        if status.strip() == "مقفلة":
            QMessageBox.warning(self, "غير مسموح", f"السنة '{year_name}' مقفلة ولا يمكن تعديلها.")
            return

        # افتح حوار التعديل وعبّئه بالقيم الحالية
        dlg = YearSelectionDialog(existing_years=getattr(self, 'existing_years', []), parent=self)
        try:
            dlg.year_combo.setCurrentText(str(year_name))
            dlg.start_date_edit.setDate(QDate.fromString(start_date, "yyyy-MM-dd"))
            dlg.end_date_edit.setDate(QDate.fromString(end_date, "yyyy-MM-dd"))
        except Exception:
            pass

        if dlg.exec_() != QDialog.Accepted:
            return

        data = dlg.get_selected_data()
        new_year = data["year"]
        new_start = data["start_date"]
        new_end = data["end_date"]

        # تحقق من عدم التداخل أو التكرار مع سجلات أخرى
        try:
            conn = get_financials_db_connection()
            if not conn:
                QMessageBox.critical(self, "خطأ", "لا يمكن الاتصال بقاعدة البيانات.")
                return
            cur = conn.cursor()

            cur.execute("""
                SELECT id, year_name, start_date, end_date
                FROM financial_years
                WHERE id <> ?
                  AND (year_name = ? OR NOT (date(end_date) < date(?) OR date(start_date) > date(?)))
                LIMIT 1
            """, (year_id, str(new_year), new_start, new_end))
            existing = cur.fetchone()
            if existing:
                eid, ename, estart, eend = existing[0], existing[1], existing[2], existing[3]
                QMessageBox.warning(self, "تداخل سنوات",
                                f"يوجد سنة أخرى بنفس الاسم أو فترة متداخلة:\nالاسم: {ename}\nالفترة: {estart} إلى {eend}")
                try:
                    conn.close()
                except:
                    pass
                return

            # بناء الاستعلام بشكل ديناميكي تبعًا لوجود الأعمدة
            cur.execute("PRAGMA table_info(financial_years)")
            cols = [r[1] for r in cur.fetchall()]

            update_parts = []
            params = []

            update_parts.append("year_name = ?"); params.append(str(new_year))
            update_parts.append("start_date = ?"); params.append(new_start)
            update_parts.append("end_date = ?"); params.append(new_end)

            # إذا العمود updated_at موجود نضيف CURRENT_TIMESTAMP مباشرة في SQL
            if 'updated_at' in cols:
                update_parts.append("updated_at = CURRENT_TIMESTAMP")

            # إذا العمود updated_by_user_id موجود نضيفه كمعامل
            current_user_id = None
            if session and getattr(session, 'current_user', None):
                current_user_id = session.current_user.get('id')
            if 'updated_by_user_id' in cols:
                update_parts.append("updated_by_user_id = ?")
                params.append(current_user_id)

            params.append(year_id)
            sql = f"UPDATE financial_years SET {', '.join(update_parts)} WHERE id = ?"

            cur.execute(sql, tuple(params))
            conn.commit()
            try:
                conn.close()
            except:
                pass

            QMessageBox.information(self, "تم", "تم تعديل بيانات السنة المالية بنجاح.")
            self.load_financial_years()

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تعديل بيانات السنة: {e}")

    # -----------------------------------------------------------------
    # تحميل السنوات واظهار المنشئ/آخر معدل/تواريخ/المجاميع
    # -----------------------------------------------------------------
    def load_financial_years(self):
        """
        محاولة استخدام manager.get_detailed_years_report() لو متوفر.
        fallback: سحب من جدول financial_years ثم حساب المجاميع داخل الفترة.
        يدعم حقول created_at أو create_at وبحث عن created_by_user_id و updated_by_user_id إن وجدت.
        """
        try:
            self.table.setRowCount(0)
            self.existing_years = []

            years = None
            if self.financial_year_manager and hasattr(self.financial_year_manager, "get_detailed_years_report"):
                try:
                    years = self.financial_year_manager.get_detailed_years_report()
                except Exception:
                    years = None

            if not years:
                conn = get_financials_db_connection()
                if not conn:
                    QMessageBox.critical(self, "خطأ", "لا يمكن الاتصال بقاعدة البيانات.")
                    return

                # تأكد من أسماء الأعمدة في الجدول لتعامل مرن
                cols = _table_columns(conn, "financial_years")
                select_fields = ["id", "year_name", "start_date", "end_date", "is_closed"]
                if "created_at" in cols:
                    select_fields.append("created_at")
                elif "create_at" in cols:
                    select_fields.append("create_at")
                if "created_by_user_id" in cols:
                    select_fields.append("created_by_user_id")
                if "updated_at" in cols:
                    select_fields.append("updated_at")
                if "updated_by_user_id" in cols:
                    select_fields.append("updated_by_user_id")
                if "closing_entry_id" in cols:
                    select_fields.append("closing_entry_id")

                cur = conn.cursor()
                cur.execute(f"SELECT {','.join(select_fields)} FROM financial_years ORDER BY start_date DESC")
                rows = cur.fetchall()
                years = []
                for r in rows:
                    rowdict = dict(zip(select_fields, r))
                    yr = {
                        'id': rowdict.get('id'),
                        'year_name': rowdict.get('year_name'),
                        'start_date': rowdict.get('start_date'),
                        'end_date': rowdict.get('end_date'),
                        'is_closed': rowdict.get('is_closed'),
                        'status': "مقفلة" if rowdict.get('is_closed') else "مفتوحة"
                    }
                    # created_at (handle both spelled variants)
                    created_at_val = rowdict.get('created_at') if 'created_at' in rowdict else rowdict.get('create_at')
                    yr['created_at'] = created_at_val or ""

                    # created_by_user_id => resolve to full_name if present
                    creator_name = ""
                    if 'created_by_user_id' in rowdict and rowdict.get('created_by_user_id'):
                        creator_name = _get_user_fullname(conn, rowdict.get('created_by_user_id'))
                    yr['created_by_name'] = creator_name

                    # updated info
                    updated_by_name = ""
                    if 'updated_by_user_id' in rowdict and rowdict.get('updated_by_user_id'):
                        updated_by_name = _get_user_fullname(conn, rowdict.get('updated_by_user_id'))
                    yr['updated_by_name'] = updated_by_name
                    yr['updated_at'] = rowdict.get('updated_at') or ""

                    # closing_entry_id if exists
                    yr['closing_entry_id'] = rowdict.get('closing_entry_id') if 'closing_entry_id' in rowdict else None

                    # حساب المجاميع داخل الفترة
                    try:
                        cur2 = conn.cursor()
                        cur2.execute("""
                            SELECT
                                IFNULL(SUM(jel.credit), 0) as total_credit,
                                IFNULL(SUM(jel.debit), 0) as total_debit
                            FROM journal_entries je
                            JOIN journal_entry_lines jel ON jel.journal_entry_id = je.id
                            WHERE je.entry_date BETWEEN ? AND ?
                        """, (yr['start_date'], yr['end_date']))
                        sums = cur2.fetchone()
                        total_credit = sums[0] or 0.0
                        total_debit = sums[1] or 0.0
                        yr['total_revenues'] = float(total_credit)
                        yr['total_expenses'] = float(total_debit)
                        yr['net_income'] = float(total_credit - total_debit)
                    except Exception:
                        yr['total_revenues'] = 0.0
                        yr['total_expenses'] = 0.0
                        yr['net_income'] = 0.0

                    years.append(yr)
                try:
                    conn.close()
                except Exception:
                    pass

            # عرض النتائج في الجدول
            if not years:
                self.info_label.setText("لا توجد سنوات مالية")
                return

            for row_idx, year in enumerate(years):
                self.table.insertRow(row_idx)
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(year.get('id'))))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(year.get('year_name') or "")))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(year.get('start_date') or "")))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(year.get('end_date') or "")))
                st_item = QTableWidgetItem(year.get('status') or ("مفتوحة" if not year.get('is_closed') else "مقفلة"))
                if (year.get('status') or "").strip() == "مفتوحة":
                    st_item.setBackground(Qt.green)
                else:
                    st_item.setBackground(Qt.lightGray)
                self.table.setItem(row_idx, 4, st_item)

                # المنشئ و تاريخ الإنشاء
                creator_display = year.get('created_by_name') or ""
                self.table.setItem(row_idx, 5, QTableWidgetItem(creator_display))
                created_at_display = year.get('created_at') or ""
                self.table.setItem(row_idx, 6, QTableWidgetItem(str(created_at_display)))

                # آخر معدل و تاريخ التعديل
                updated_by_display = year.get('updated_by_name') or ""
                self.table.setItem(row_idx, 7, QTableWidgetItem(updated_by_display))
                updated_at_display = year.get('updated_at') or ""
                self.table.setItem(row_idx, 8, QTableWidgetItem(str(updated_at_display)))

                # الإيرادات / المصروفات / صافي الربح
                rev = float(year.get('total_revenues', 0.0) or 0.0)
                exp = float(year.get('total_expenses', 0.0) or 0.0)
                net = float(year.get('net_income', rev - exp) or (rev - exp))

                self.table.setItem(row_idx, 9, QTableWidgetItem(f"{rev:,.2f}"))
                self.table.setItem(row_idx, 10, QTableWidgetItem(f"{exp:,.2f}"))
                ni_item = QTableWidgetItem(f"{net:,.2f}")
                if net > 0:
                    ni_item.setForeground(Qt.darkGreen)
                elif net < 0:
                    ni_item.setForeground(Qt.red)
                self.table.setItem(row_idx, 11, ni_item)

                # سجل السنة (كقيمة صحيحة) للاستخدام لاحقاً
                try:
                    self.existing_years.append(int(year.get('year_name')))
                except Exception:
                    pass

            self.info_label.setText(f"تم تحميل {len(years)} سنة/سنوات")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل السنوات: {e}")

            # رقم القيد (لو موجود closing_entry_id)
            if year.get('closing_entry_id'):
                    cur2 = conn.cursor()
                    cur2.execute("SELECT entry_number FROM journal_entries WHERE id = ?", (year['closing_entry_id'],))
                    r = cur2.fetchone()
                    entry_number = r[0] if r else str(year['closing_entry_id'])
                    item = QTableWidgetItem(entry_number)
                    item.setForeground(Qt.blue)
                    item.setData(Qt.UserRole, year['closing_entry_id'])
                    self.table.setItem(row_idx, 12, item)
            else:
                    self.table.setItem(row_idx, 12, QTableWidgetItem(""))



    # -----------------------------------------------------------------
    def on_year_selected(self):
        items = self.table.selectedItems()
        if not items:
            self.info_label.setText("حدد سنة مالية")
            return
        row = items[0].row()
        try:
            name = self.table.item(row, 1).text()
            status = self.table.item(row, 4).text()
            net = self.table.item(row, 11).text()
            self.info_label.setText(f"السنة: {name} | الحالة: {status} | صافي الربح: {net}")
        except Exception:
            pass

    # -----------------------------------------------------------------
    def create_new_financial_year(self):
        dlg = YearSelectionDialog(existing_years=getattr(self, 'existing_years', []), parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_selected_data()
        year = data["year"]
        start_date = data["start_date"]
        end_date = data["end_date"]

        # تحقق إذا كانت السنة موجودة بالفعل أو تتداخل فتراتياً مع سنة موجودة
        try:
            conn = get_financials_db_connection()
            if not conn:
                QMessageBox.critical(self, "خطأ", "لا يمكن الاتصال بقاعدة البيانات.")
                return
            cur = conn.cursor()
            cur.execute("""
                SELECT id, year_name, start_date, end_date
                FROM financial_years
                WHERE year_name = ? 
                   OR NOT (date(end_date) < date(?) OR date(start_date) > date(?))
                LIMIT 1
            """, (str(year), start_date, end_date))
            existing = cur.fetchone()
            if existing:
                eid, ename, estart, eend = existing[0], existing[1], existing[2], existing[3]
                QMessageBox.warning(self, "سنة موجودة/تداخل",
                                    f"يوجد سنة مالية متداخلة أو بنفس الاسم:\nالاسم: {ename}\nالفترة: {estart} إلى {eend}\n\nلن يتم إنشاء سنة مكررة.")
                try:
                    conn.close()
                except Exception:
                    pass
                return
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "تحذير فحص التكرار", f"تعذر التحقق من التكرار: {e}\nسنحاول إنشاء السجل لكن ننصح بفحص البيانات بعد الإنشاء.")

        # محاولة الإنشاء عبر manager (إن وُجد) مع تمرير created_by_user_id إن أمكن
        created = False
        message = ""
        current_user_id = session.current_user['id'] if session and getattr(session, 'current_user', None) else None
        if self.financial_year_manager and hasattr(self.financial_year_manager, "create_financial_year"):
            try:
                # حاول تمرير created_by_user_id إن كانت الدالة تقبلها
                try:
                    ok, msg = self.financial_year_manager.create_financial_year(
                        year_name=str(year), start_date=start_date, end_date=end_date, created_by_user_id=current_user_id
                    )
                except TypeError:
                    ok, msg = self.financial_year_manager.create_financial_year(
                        year_name=str(year), start_date=start_date, end_date=end_date
                    )
                if ok:
                    created = True
                    message = msg or f"تم إنشاء السنة {year}."
                else:
                    message = msg or "فشل إنشاء السنة عبر manager."
            except Exception as e:
                message = f"خطأ أثناء إنشاء السنة عبر manager: {e}"

        # fallback: إنشاء مباشرة في قاعدة البيانات (مرن حسب وجود عمود created_by_user_id)
        if not created:
            try:
                conn = get_financials_db_connection()
                if not conn:
                    QMessageBox.critical(self, "خطأ", "لا يمكن الاتصال بقاعدة البيانات.")
                    return
                cols = _table_columns(conn, "financial_years")
                insert_cols = ["year_name", "start_date", "end_date", "is_closed", "created_at"]
                params = [str(year), start_date, end_date, 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                if "created_by_user_id" in cols and current_user_id is not None:
                    insert_cols.append("created_by_user_id")
                    params.append(current_user_id)
                placeholders = ",".join(["?"] * len(insert_cols))
                cur = conn.cursor()
                cur.execute(f"INSERT INTO financial_years ({','.join(insert_cols)}) VALUES ({placeholders})", tuple(params))
                conn.commit()
                try:
                    conn.close()
                except Exception:
                    pass
                created = True
                message = f"تم إنشاء السنة {year} (تم الإنشاء عبر SQL)."
            except Exception as e:
                message = f"فشل إنشاء السنة في قاعدة البيانات: {e}"

        if created:
            QMessageBox.information(self, "نجاح", message)
            self.load_financial_years()
        else:
            QMessageBox.critical(self, "خطأ", message)

    # -----------------------------------------------------------------
    def execute_year_end_closing(self):
        items = self.table.selectedItems()
        if not items:
            QMessageBox.warning(self, "تحذير", "اختر سنة مالية ثم حاول الإقفال.")
            return
        row = items[0].row()
        year_id = int(self.table.item(row, 0).text())
        year_name = self.table.item(row, 1).text()
        status = self.table.item(row, 4).text()
        if status.strip() == "مقفلة":
            QMessageBox.warning(self, "تنبيه", f"السنة '{year_name}' مقفلة بالفعل.")
            return

        if self.financial_year_manager and hasattr(self.financial_year_manager, "validate_year_for_closing"):
            ok, msg = self.financial_year_manager.validate_year_for_closing(year_id)
            if not ok:
                QMessageBox.warning(self, "تحذير", msg or "السنة غير صالحة للإقفال.")
                return

        dlg = AccountSelectionDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        sel = dlg.get_selected()

        reply = QMessageBox.question(self, "تأكيد", f"هل تريد تنفيذ إقفال السنة '{year_name}'؟", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        if self.financial_year_manager and hasattr(self.financial_year_manager, "create_year_end_closing_entry"):
            try:
                success, message = self.financial_year_manager.create_year_end_closing_entry(
                    year_id,
                    sel.get('revenues_account_id'),
                    sel.get('expenses_account_id'),
                    sel.get('retained_earnings_account_id')
                )
                if success:
                    if hasattr(self.financial_year_manager, "update_year_closing_metadata"):
                        try:
                            self.financial_year_manager.update_year_closing_metadata(
                                year_id,
                                sel.get('legal_reserve_account_id'), sel.get('legal_reserve_percent'),
                                sel.get('income_tax_account_id'), sel.get('income_tax_percent'),
                                sel.get('solidarity_tax_account_id'), sel.get('solidarity_tax_percent'),
                                sel.get('closed_at'), sel.get('closed_by_user_id')
                            )
                        except Exception:
                            pass
                    QMessageBox.information(self, "تم", message or "تم تنفيذ إقفال السنة بنجاح.")
                    self.load_financial_years()
                    return
                else:
                    QMessageBox.critical(self, "خطأ", message or "فشل تنفيذ الإقفال عبر manager.")
                    return
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ أثناء تنفيذ الإقفال عبر manager: {e}")
                return

        QMessageBox.critical(self, "غير متاح", "الإقفال التلقائي غير متاح لأن manager لا يحتوي على دوال تنفيذ الإقفال.")
        return

    # -----------------------------------------------------------------
    def reopen_financial_year(self):
        items = self.table.selectedItems()
        if not items:
            QMessageBox.warning(self, "تحذير", "اختر سنة مالية لإعادة فتحها.")
            return
        row = items[0].row()
        year_id = int(self.table.item(row, 0).text())
        year_name = self.table.item(row, 1).text()

        reply = QMessageBox.question(self, "تأكيد", f"هل تريد إعادة فتح السنة '{year_name}'؟", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        if self.financial_year_manager and hasattr(self.financial_year_manager, "reverse_closing_entry"):
            try:
                ok, msg = self.financial_year_manager.reverse_closing_entry(year_id)
                if ok:
                    QMessageBox.information(self, "تم", msg or "تم إعادة فتح السنة.")
                    self.load_financial_years()
                    return
                else:
                    QMessageBox.critical(self, "خطأ", msg or "فشل إعادة فتح السنة عبر manager.")
                    return
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ أثناء إعادة الفتح عبر manager: {e}")
                return

        try:
            conn = get_financials_db_connection()
            if not conn:
                QMessageBox.critical(self, "خطأ", "لا يمكن الاتصال بقاعدة البيانات.")
                return
            cur = conn.cursor()
            cur.execute("UPDATE financial_years SET is_closed = 0, closed_at = NULL, closed_by_user_id = NULL WHERE id = ?", (year_id,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "تم", "تم إعادة فتح السنة (تم التحديث في قاعدة البيانات).")
            self.load_financial_years()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل إعادة فتح السنة في قاعدة البيانات: {e}")
    
    def show_journal_entry_details(self, entry_id):
        try:
            conn = get_financials_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT entry_number, entry_date, description, created_at
                FROM journal_entries
                WHERE id = ?
            """, (entry_id,))
            header = cur.fetchone()

            cur.execute("""
                SELECT a.account_name_ar, jel.debit, jel.credit
                FROM journal_entry_lines jel
                JOIN accounts a ON a.id = jel.account_id
                WHERE jel.journal_entry_id = ?
            """, (entry_id,))
            lines = cur.fetchall()
            conn.close()

            text = f"رقم القيد: {header[0]}\nتاريخ القيد: {header[1]}\nالوصف: {header[2]}\nتاريخ الإنشاء: {header[3]}\n\nالتفاصيل:\n"
            for line in lines:
                text += f"- {line[0]} | مدين: {line[1]} | دائن: {line[2]}\n"

            QMessageBox.information(self, "تفاصيل القيد", text)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل تفاصيل القيد: {e}")


# =====================================================================
# تشغيل الوحدة كنافذة مستقلة (لفحصك المحلي)
# =====================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = FinancialPeriodsWindow()
    w.show()
    sys.exit(app.exec_())

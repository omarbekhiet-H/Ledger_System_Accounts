import sqlite3
import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDateEdit, QGroupBox, QGridLayout, QApplication, QStyle,
    QAbstractItemView, QCheckBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

# =====================================================================
# Correct project root path
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import managers
from database.manager.financial.reports.End_financial_reports_manager import EndFinancialReportsManager
from database.manager.account_manager import AccountManager
from database.db_connection import get_financials_db_connection
from database.schems.default_data.financials_data_population import insert_default_data
from database.schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT


# =====================================================================
# Helper to load stylesheet
# =====================================================================
def load_qss_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"WARNING: Could not load QSS file {file_path}: {e}")
        return None


class BalanceSheetReportWindow(QWidget):
    def __init__(self, journal_manager=None, account_manager=None):
        super().__init__()
        self.journal_manager = journal_manager if journal_manager else EndFinancialReportsManager(get_financials_db_connection)
        self.account_manager = account_manager if account_manager else AccountManager(get_financials_db_connection)

        self.setWindowTitle("الميزانية العمومية المقارنة")
        self.setLayoutDirection(Qt.RightToLeft)
        QApplication.instance().setLayoutDirection(Qt.RightToLeft)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("الميزانية العمومية المقارنة (على المستوى الثالث)")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Controls
        controls_group = QGroupBox("خيارات التقرير")
        controls_layout = QGridLayout(controls_group)

        controls_layout.addWidget(QLabel("الرصيد في تاريخ:"), 0, 0)
        self.report_date_edit = QDateEdit(QDate.currentDate())
        self.report_date_edit.setCalendarPopup(True)
        self.report_date_edit.setDisplayFormat("yyyy-MM-dd")
        controls_layout.addWidget(self.report_date_edit, 0, 1)

        self.generate_report_btn = QPushButton("توليد التقرير")
        self.generate_report_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.generate_report_btn.clicked.connect(self.generate_report)
        controls_layout.addWidget(self.generate_report_btn, 0, 2, 1, 1)

        # ✅ Checkbox filter
        self.active_only_checkbox = QCheckBox("عرض الحسابات النشطة فقط")
        self.active_only_checkbox.setChecked(True)
        controls_layout.addWidget(self.active_only_checkbox, 1, 0, 1, 2)

        main_layout.addWidget(controls_group)

        # Table
        self.report_table = QTableWidget()
        self.report_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.report_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.report_table.setAlternatingRowColors(True)
        self.report_table.setColumnCount(5)
        self.report_table.setHorizontalHeaderLabels([
            "رمز الحساب", "اسم الحساب", "الرصيد الحالي", "الرصيد السابق", "التغير"
        ])
        self.report_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        main_layout.addWidget(self.report_table)

        # Totals
        totals_layout = QVBoxLayout()
        self.total_assets_label = QLabel("إجمالي الأصول: 0.00")
        self.total_assets_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.total_assets_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(self.total_assets_label)

        self.total_liabilities_equity_label = QLabel("إجمالي الخصوم وحقوق الملكية: 0.00")
        self.total_liabilities_equity_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.total_liabilities_equity_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(self.total_liabilities_equity_label)

        self.balance_status_label = QLabel("الميزانية:")
        self.balance_status_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.balance_status_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(self.balance_status_label)

        main_layout.addLayout(totals_layout)

    # ------------------------------------------------------------
    def _normalize_balance_items(self, raw_data):
        """Ensure data is list of dicts, flatten if needed."""
        if isinstance(raw_data, dict):
            items = []
            for section in raw_data.values():
                if isinstance(section, list):
                    items.extend(section)
            return items
        elif isinstance(raw_data, list):
            return raw_data
        return []

    # ------------------------------------------------------------
    def generate_report(self):
        self.report_table.setRowCount(0)

        current_date_q = self.report_date_edit.date()
        current_date_str = current_date_q.toString("yyyy-MM-dd")
        compare_date_q = current_date_q.addYears(-1)
        compare_date_str = compare_date_q.toString("yyyy-MM-dd")

        self.report_table.setHorizontalHeaderLabels([
            "رمز الحساب", "اسم الحساب", f"رصيد {current_date_str}", f"رصيد {compare_date_str}", "التغير"
        ])

        try:
            try:
                current_raw = self.journal_manager.get_balance_sheet_data(current_date_str, level=3)
            except TypeError:
                current_raw = self.journal_manager.get_balance_sheet_data(current_date_str)

            try:
                compare_raw = self.journal_manager.get_balance_sheet_data(compare_date_str, level=3)
            except TypeError:
                compare_raw = self.journal_manager.get_balance_sheet_data(compare_date_str)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"تعذر جلب البيانات:\n{e}")
            return

        current_items = self._normalize_balance_items(current_raw)
        compare_items = self._normalize_balance_items(compare_raw)

        current_lookup = {it['account_code']: it for it in current_items if it.get('account_code')}
        compare_lookup = {it['account_code']: it for it in compare_items if it.get('account_code')}
        all_account_codes = sorted(set(current_lookup.keys()) | set(compare_lookup.keys()))

        if not all_account_codes:
            QMessageBox.information(self, "لا توجد بيانات", "لا توجد بيانات للفترتين المحددتين.")
            return

        # ✅ Apply checkbox filter
        if self.active_only_checkbox.isChecked():
            tol = 0.009
            all_account_codes = [
                code for code in all_account_codes
                if abs(float(current_lookup.get(code, {}).get('balance', 0.0))) > tol
                or abs(float(compare_lookup.get(code, {}).get('balance', 0.0))) > tol
            ]

        if not all_account_codes:
            QMessageBox.information(self, "لا توجد حسابات", "لا توجد حسابات مطابقة للفلتر المحدد.")
            return

        total_assets = 0.0
        total_liabilities_equity = 0.0
        row_idx = 0

        def add_header_row(title, color):
            nonlocal row_idx
            self.report_table.insertRow(row_idx)
            header_item = QTableWidgetItem(title)
            header_item.setFont(QFont("Arial", 11, QFont.Bold))
            header_item.setTextAlignment(Qt.AlignCenter)
            header_item.setBackground(QColor(color))
            self.report_table.setSpan(row_idx, 0, 1, self.report_table.columnCount())
            self.report_table.setItem(row_idx, 0, header_item)
            row_idx += 1

        def add_data_row(current_item, compare_item):
            nonlocal row_idx
            display_item = current_item if current_item else compare_item
            if not display_item:
                return 0.0

            current_balance = current_item.get('balance', 0.0) if current_item else 0.0
            comp_balance = compare_item.get('balance', 0.0) if compare_item else 0.0
            change = current_balance - comp_balance

            self.report_table.insertRow(row_idx)
            self.report_table.setItem(row_idx, 0, QTableWidgetItem(display_item.get('account_code', '')))
            self.report_table.setItem(row_idx, 1, QTableWidgetItem(display_item.get('account_name_ar', '')))
            self.report_table.setItem(row_idx, 2, QTableWidgetItem(f"{current_balance:,.2f}"))
            self.report_table.setItem(row_idx, 3, QTableWidgetItem(f"{comp_balance:,.2f}"))
            self.report_table.setItem(row_idx, 4, QTableWidgetItem(f"{change:,.2f}"))
            row_idx += 1
            return current_balance

        def add_total_row(title, total_value, color, column_index=2):
            nonlocal row_idx
            self.report_table.insertRow(row_idx)
            label_item = QTableWidgetItem(title)
            label_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.report_table.setItem(row_idx, 1, label_item)
            value_item = QTableWidgetItem(f"{total_value:,.2f}")
            value_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.report_table.setItem(row_idx, column_index, value_item)
            for col in range(self.report_table.columnCount()):
                if self.report_table.item(row_idx, col):
                    self.report_table.item(row_idx, col).setBackground(QColor(color))
            row_idx += 1

        # Assets
        add_header_row("الأصول", "#D6EEF8")
        for code in all_account_codes:
            cur = current_lookup.get(code)
            comp = compare_lookup.get(code)
            acc_type = (cur or comp or {}).get('account_type_name')
            if acc_type == 'الأصول':
                total_assets += add_data_row(cur, comp)
        add_total_row("إجمالي الأصول", total_assets, "#B8DAED")

        # Liabilities & Equity
        add_header_row("الخصوم وحقوق الملكية", "#F0E68C")
        for code in all_account_codes:
            cur = current_lookup.get(code)
            comp = compare_lookup.get(code)
            acc_type = (cur or comp or {}).get('account_type_name')
            if acc_type in ['الخصوم', 'حقوق الملكية']:
                total_liabilities_equity += add_data_row(cur, comp)
        add_total_row("إجمالي الخصوم وحقوق الملكية", total_liabilities_equity, "#EEDD82")

        self.total_assets_label.setText(f"إجمالي الأصول: {total_assets:,.2f}")
        self.total_liabilities_equity_label.setText(f"إجمالي الخصوم وحقوق الملكية: {total_liabilities_equity:,.2f}")

        if abs(total_assets - total_liabilities_equity) < 0.01:
            self.balance_status_label.setText("الميزانية: متوازنة")
            self.balance_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            diff = total_assets - total_liabilities_equity
            self.balance_status_label.setText(f"الميزانية: غير متوازنة (الفرق: {diff:,.2f})")
            self.balance_status_label.setStyleSheet("color: red; font-weight: bold;")
            QMessageBox.warning(self, "تحذير", f"الميزانية العمومية غير متوازنة! الفرق: {diff:,.2f}")

        self.report_table.resizeColumnsToContents()
        self.report_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    try:
        conn = get_financials_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='journal_entries';")
            if not cursor.fetchone():
                print("Financials DB schema not found. Initializing...")
                cursor.executescript(FINANCIALS_SCHEMA_SCRIPT)
                conn.commit()
                insert_default_data(conn)
            conn.close()
    except Exception as e:
        QMessageBox.critical(None, "خطأ", f"فشل تهيئة قاعدة البيانات: {e}")
        sys.exit(1)

    qss_file_path = os.path.join(project_root, 'ui', 'styles', 'styles.qss')
    app_stylesheet = load_qss_file(qss_file_path)
    if app_stylesheet:
        app.setStyleSheet(app_stylesheet)

    window = BalanceSheetReportWindow()
    window.showMaximized()
    sys.exit(app.exec_())

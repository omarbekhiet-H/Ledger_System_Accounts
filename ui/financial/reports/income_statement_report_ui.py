import sqlite3
import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDateEdit, QGroupBox, QGridLayout, QApplication, QStyle,
    QAbstractItemView, QComboBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

# =====================================================================
# Correct project root path to enable correct imports
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import necessary managers - Income_statment_report_ui.py
from database.manager.financial.reports.End_financial_reports_manager import EndFinancialReportsManager
from database.manager.account_manager import AccountManager
from database.db_connection import get_financials_db_connection
# Import default data population function and database schema
from database.schems.default_data.financials_data_population import insert_default_data
from database.schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT

# =====================================================================
# Helper function to load QSS files
# =====================================================================
def load_qss_file(file_path):
    """Loads a QSS file and returns its content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: QSS file not found at {file_path}")
        return None
    except Exception as e:
        print(f"ERROR: Could not load QSS file {file_path}: {e}")
        return None

class IncomeStatementReportWindow(QWidget):
    def __init__(self, journal_manager=None, account_manager=None):
        super().__init__()
        self.journal_manager = journal_manager if journal_manager else EndFinancialReportsManager(get_financials_db_connection)
        self.account_manager = account_manager if account_manager else AccountManager(get_financials_db_connection)

        self.setWindowTitle("قائمة الدخل المقارنة")
        self.setLayoutDirection(Qt.RightToLeft)
        QApplication.instance().setLayoutDirection(Qt.RightToLeft) # Apply RTL to the whole application
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("قائمة الدخل المقارنة (حسب المستوى)")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        controls_group = QGroupBox("تحديد فترة التقرير")
        controls_group.setLayoutDirection(Qt.RightToLeft)
        controls_layout = QGridLayout(controls_group)

        controls_layout.addWidget(QLabel("من تاريخ:"), 0, 0)
        self.start_date_edit = QDateEdit(QDate.currentDate().addMonths(-3).addDays(1))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        controls_layout.addWidget(self.start_date_edit, 0, 1)

        controls_layout.addWidget(QLabel("إلى تاريخ:"), 0, 2)
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        controls_layout.addWidget(self.end_date_edit, 0, 3)

        # Level selection (final / level 2 / level 3)
        controls_layout.addWidget(QLabel("المستوى:"), 0, 4)
        self.level_combo = QComboBox()
        self.level_combo.addItem("الحسابات النهائية", None)
        self.level_combo.addItem("المستوى الثاني", 2)
        self.level_combo.addItem("المستوى الثالث", 3)
        controls_layout.addWidget(self.level_combo, 0, 5)

        self.generate_report_btn = QPushButton("توليد التقرير")
        self.generate_report_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.generate_report_btn.clicked.connect(self.generate_report)
        controls_layout.addWidget(self.generate_report_btn, 0, 6, 1, 1)
        
        controls_layout.setColumnStretch(7, 1) # Add stretch to push button to the left

        main_layout.addWidget(controls_group)

        self.report_table = QTableWidget()
        self.report_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.report_table.setColumnCount(5)
        self.report_table.setHorizontalHeaderLabels([
            "رمز الحساب", "اسم الحساب", "الفترة الحالية", "الفترة السابقة", "التغير"
        ])
        self.report_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        main_layout.addWidget(self.report_table)

        totals_layout = QVBoxLayout()
        self.total_revenues_label = QLabel("إجمالي الإيرادات: 0.00")
        self.total_revenues_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.total_revenues_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(self.total_revenues_label)

        self.total_expenses_label = QLabel("إجمالي المصروفات: 0.00")
        self.total_expenses_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.total_expenses_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(self.total_expenses_label)

        self.net_income_label = QLabel("صافي الربح/الخسارة: 0.00")
        self.net_income_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.net_income_label.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(self.net_income_label)

        main_layout.addLayout(totals_layout)

    def generate_report(self):
        self.report_table.setRowCount(0)
        
        start_date_q = self.start_date_edit.date()
        end_date_q = self.end_date_edit.date()
        
        current_period_start = start_date_q.toString("yyyy-MM-dd")
        current_period_end = end_date_q.toString("yyyy-MM-dd")
        
        # Calculate previous period (same duration, shifted back by the duration)
        duration_days = start_date_q.daysTo(end_date_q) + 1 # Include end date
        
        prev_period_end_q = start_date_q.addDays(-1) # Day before current period starts
        prev_period_start_q = prev_period_end_q.addDays(-duration_days + 1)
        
        prev_period_start = prev_period_start_q.toString("yyyy-MM-dd")
        prev_period_end = prev_period_end_q.toString("yyyy-MM-dd")

        # Update column headers to reflect dates
        self.report_table.setHorizontalHeaderLabels([
            "رمز الحساب", "اسم الحساب",
            f"الفترة الحالية ({current_period_start} إلى {current_period_end})",
            f"الفترة السابقة ({prev_period_start} إلى {prev_period_end})",
            "التغير"
        ])

        # اقرأ المستوى من الواجهة (None => حسابات نهائية)
        level = self.level_combo.currentData()

        # استدعاء المدير مع level (قد يكون None أو 2 أو 3)
        current_data = self.journal_manager.get_income_statement_data(current_period_start, current_period_end, level=level)
        compare_data = self.journal_manager.get_income_statement_data(prev_period_start, prev_period_end, level=level)

        # تأكد من سلامة القيم (قد يرجع المدير قائمة فارغة)
        current_data = current_data or []
        compare_data = compare_data or []

        # اعمل dictionary حسب acc_code مع الحذر من المفاتيح المفقودة
        current_balances = { (item.get('acc_code') or item.get('acc_id') or f"_{idx}"): item for idx, item in enumerate(current_data)}
        compare_balances = { (item.get('acc_code') or item.get('acc_id') or f"cmp_{idx}"): item for idx, item in enumerate(compare_data)}

        # اجمع كل الرموز (قد تكون بعض العناصر ليس لديها acc_code ـ فنتعامل باستخدام المفاتيح التعريفية)
        all_account_codes = sorted(list(set(list(current_balances.keys()) + list(compare_balances.keys()))))

        if not all_account_codes:
            QMessageBox.information(self, "لا توجد بيانات", "لا توجد بيانات للفترتين المحددتين على المستوى المختار.")
            return

        total_revenues = 0.0
        total_expenses = 0.0
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
                # لا يوجد بيانات للعرض لهذا السطر
                return 0.0

            # جلب الحقول بأمان
            current_balance = float((current_item.get('final_balance') if current_item and current_item.get('final_balance') is not None else 0.0)) if current_item else 0.0
            comp_balance = float((compare_item.get('final_balance') if compare_item and compare_item.get('final_balance') is not None else 0.0)) if compare_item else 0.0
            
            change = current_balance - comp_balance

            acc_code = display_item.get('acc_code') or str(display_item.get('acc_id', ''))
            acc_name = display_item.get('account_name_ar') or display_item.get('account_name_en') or ''

            self.report_table.insertRow(row_idx)
            self.report_table.setItem(row_idx, 0, QTableWidgetItem(str(acc_code)))
            self.report_table.setItem(row_idx, 1, QTableWidgetItem(str(acc_name)))
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

        # Revenues
        add_header_row("الإيرادات", "#D6EEF8")
        for code in all_account_codes:
            current_item = current_balances.get(code)
            compare_item = compare_balances.get(code)
            
            account_type = None
            if current_item:
                account_type = current_item.get('account_type_name')
            elif compare_item:
                account_type = compare_item.get('account_type_name')

            if account_type == 'الإيرادات' or (account_type is None and (current_item or compare_item) and ( (current_item and (current_item.get('final_balance') or 0)!=0 or (compare_item and (compare_item.get('final_balance') or 0)!=0)) )):
                total_revenues += add_data_row(current_item, compare_item)
        add_total_row("إجمالي الإيرادات", total_revenues, "#B8DAED")

        # Expenses
        add_header_row("المصروفات", "#F0E68C")
        for code in all_account_codes:
            current_item = current_balances.get(code)
            compare_item = compare_balances.get(code)
            
            account_type = None
            if current_item:
                account_type = current_item.get('account_type_name')
            elif compare_item:
                account_type = compare_item.get('account_type_name')

            if account_type == 'المصروفات' or (account_type is None and (current_item or compare_item) and ( (current_item and (current_item.get('final_balance') or 0)!=0 or (compare_item and (compare_item.get('final_balance') or 0)!=0)) )):
                total_expenses += add_data_row(current_item, compare_item)
        add_total_row("إجمالي المصروفات", total_expenses, "#EEDD82")
        
        net_income = total_revenues - total_expenses
        add_total_row("صافي الربح/الخسارة", net_income, "#D3D3D3") # Gray for net income

        self.total_revenues_label.setText(f"إجمالي الإيرادات: {total_revenues:,.2f}")
        self.total_expenses_label.setText(f"إجمالي المصروفات: {total_expenses:,.2f}")
        self.net_income_label.setText(f"صافي الربح/الخسارة: {net_income:,.2f}")

        if net_income >= 0:
            self.net_income_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.net_income_label.setStyleSheet("color: red; font-weight: bold;")

        self.report_table.resizeColumnsToContents()
        self.report_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Database initialization
    try:
        conn = get_financials_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='journal_entries';")
                if not cursor.fetchone():
                    print("Financials DB schema not found. Initializing...")
                    cursor.executescript(FINANCIALS_SCHEMA_SCRIPT)
                    conn.commit()
                    insert_default_data(conn)
                    print("Financials DB schema initialized and default data inserted.")
                else:
                    print("Financials DB already exists and schema is present. Skipping initialization.")
            except sqlite3.Error as e:
                QMessageBox.critical(None, "خطأ في قاعدة البيانات", f"فشل التحقق أو تهيئة المخطط: {e}")
                sys.exit(1)
            finally:
                conn.close()
        else:
            QMessageBox.critical(None, "خطأ في الاتصال بقاعدة البيانات", "فشل الاتصال بقاعدة البيانات المالية.")
            sys.exit(1)

    except Exception as e:
        QMessageBox.critical(None, "خطأ في تشغيل التطبيق", f"حدث خطأ غير متوقع أثناء تهيئة التطبيق: {e}")
        sys.exit(1)

    # Load and apply QSS stylesheet
    qss_file_path = os.path.join(project_root, 'ui', 'styles', 'styles.qss')
    app_stylesheet = load_qss_file(qss_file_path)
    if app_stylesheet:
        app.setStyleSheet(app_stylesheet)
        print("DEBUG: Applied DFD-001 stylesheet.")
    else:
        print("WARNING: Failed to load stylesheet. UI might not be consistent.")

    window = IncomeStatementReportWindow()
    window.showMaximized()
    sys.exit(app.exec_())

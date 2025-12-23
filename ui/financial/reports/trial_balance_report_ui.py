# ui/financial/reports/trial_balance_report_ui.py

import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDateEdit, QGroupBox, QGridLayout, QApplication, QStyle,
    QAbstractItemView, QComboBox, QFrame
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

# --- الاستيرادات المحدثة ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.financial.Ledger_financial_report_manager import FinancialReportManager
from database.db_connection import get_financials_db_connection
from ui.financial.reports.trial_GL_report_ui import GeneralLedgerReportWindow

class TrialBalanceReportWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_manager = FinancialReportManager(get_financials_db_connection)
        self.report_data = []
        self.child_windows = []

        self.setWindowTitle("تقرير ميزان المراجعة")
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.resize(1200, 800)
        self.setWindowFlags(Qt.FramelessWindowHint)

    def init_ui(self):
        # إطار رئيسي مزدوج اللون
        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet("""
            #mainFrame {
                background-color: #FFFFFF;
                border: 3px solid #000000;
                border-radius: 10px;
                padding: 2px;
            }
            #mainFrame::before {
                content: "";
                position: absolute;
                top: 2px;
                left: 2px;
                right: 2px;
                bottom: 2px;
                border: 1px solid #FF0000;
                border-radius: 7px;
                pointer-events: none;
            }
        """)

        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(main_frame)
        self.layout().setContentsMargins(0, 0, 0, 0)

        # شريط العنوان مع زر الإغلاق
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setStyleSheet("""
            #titleBar {
                background-color: #2C3E50;
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
                padding: 5px;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 5, 5, 5)

        # عنوان النافذة
        title_label = QLabel("تقرير ميزان المراجعة")
        title_label.setStyleSheet("""
            color: white;
            font-weight: bold;
            font-size: 16px;
        """)

        # زر إغلاق النافذة (مكبر)
        close_btn = QPushButton("X")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            #closeButton {
                background-color: #E74C3C;
                color: white;
                border-radius: 15px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            #closeButton:hover {
                background-color: #C0392B;
            }
        """)
        close_btn.clicked.connect(self.close)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        main_layout.addWidget(title_bar)

        # خيارات التقرير
        controls_group = QGroupBox("خيارات التقرير")
        controls_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                right: 10px;
                padding: 0 5px;
            }
        """)
        controls_layout = QGridLayout(controls_group)

        controls_layout.addWidget(QLabel("من تاريخ:"), 0, 0)
        self.start_date_edit = QDateEdit(QDate.currentDate().addYears(-2))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        controls_layout.addWidget(self.start_date_edit, 0, 1)

        controls_layout.addWidget(QLabel("إلى تاريخ:"), 1, 0)
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        controls_layout.addWidget(self.end_date_edit, 1, 1)

        controls_layout.addWidget(QLabel("مستوى العرض:"), 0, 2)
        self.level_combo = QComboBox()
        self.level_combo.addItems(["الكل", "المستوى 1", "المستوى 2", "المستوى 3", "المستوى 4", "المستوى 5"])
        controls_layout.addWidget(self.level_combo, 0, 3)

        self.generate_report_btn = QPushButton("توليد التقرير")
        self.generate_report_btn.setObjectName("controlButton")
        self.generate_report_btn.clicked.connect(self.generate_report)
        controls_layout.addWidget(self.generate_report_btn, 1, 2, 1, 2)

        main_layout.addWidget(controls_group)

        # جدول التقرير
        self.report_table = QTableWidget()
        self.report_table.setObjectName("reportTable")
        self.report_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.report_table.setColumnCount(8)
        self.report_table.setHorizontalHeaderLabels([
            "رمز الحساب", "اسم الحساب", "رصيد أول (مدين)", "رصيد أول (دائن)", 
            "حركات (مدين)", "حركات (دائن)", "رصيد نهائي (مدين)", "رصيد نهائي (دائن)"
        ])
        self.report_table.itemDoubleClicked.connect(self.open_general_ledger)
        
        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        main_layout.addWidget(self.report_table)

        # إجماليات التقرير
        totals_layout = QHBoxLayout()
        totals_layout.setSpacing(20)
        
        self.total_debit_label = QLabel("إجمالي المدين: 0.00")
        self.total_credit_label = QLabel("إجمالي الدائن: 0.00")
        
        for label in [self.total_debit_label, self.total_credit_label]:
            label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        totals_layout.addStretch()
        totals_layout.addWidget(self.total_debit_label)
        totals_layout.addWidget(self.total_credit_label)
        main_layout.addLayout(totals_layout)

        # تطبيق التنسيق العام
        self.setStyleSheet("""
            QWidget {
                font-family: Arial;
                font-size: 12px;
            }
            
            #controlButton {
                background-color: #3498DB;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                min-width: 120px;
                border: none;
            }
            
            #controlButton:hover {
                background-color: #2980B9;
            }
            
            #reportTable {
                border: 1px solid #BDC3C7;
                gridline-color: #ECF0F1;
                selection-background-color: #3498DB;
                selection-color: white;
            }
            
            #reportTable QHeaderView::section {
                background-color: #2C3E50;
                color: white;
                padding: 5px;
                border: none;
            }
            
            #reportTable QTableCornerButton::section {
                background-color: #2C3E50;
                border: none;
            }
            
            QDateEdit {
                padding: 5px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
            }
            
            QComboBox {
                padding: 5px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
            }
        """)

    def mousePressEvent(self, event):
        """تمكين حركة النافذة عند السحب"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """تحريك النافذة عند السحب"""
        if hasattr(self, 'drag_position') and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def generate_report(self):
        """توليد تقرير ميزان المراجعة"""
        self.report_table.setRowCount(0)
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        level_text = self.level_combo.currentText()
        selected_level = int(level_text.split(" ")[1]) if "المستوى" in level_text else None

        all_data = self.report_manager.get_trial_balance_data(start_date, end_date)
        if not all_data:
            QMessageBox.information(self, "لا توجد بيانات", "لم يتم العثور على بيانات للفترة المحددة.")
            return

        self.report_data = [item for item in all_data if selected_level is None or item.get('level') == selected_level]
        
        if not self.report_data:
            QMessageBox.information(self, "لا توجد بيانات", "لا توجد حسابات في المستوى المحدد.")
            return

        total_final_debit = 0.0
        total_final_credit = 0.0

        for row_idx, account_data in enumerate(self.report_data):
            self.report_table.insertRow(row_idx)
            self.report_table.setItem(row_idx, 0, QTableWidgetItem(account_data['acc_code']))
            self.report_table.setItem(row_idx, 1, QTableWidgetItem(account_data['account_name_ar']))
            self.add_numeric_item(row_idx, 2, account_data['opening_debit_balance'])
            self.add_numeric_item(row_idx, 3, account_data['opening_credit_balance'])
            self.add_numeric_item(row_idx, 4, account_data['period_debit'])
            self.add_numeric_item(row_idx, 5, account_data['period_credit'])
            self.add_numeric_item(row_idx, 6, account_data['final_debit_balance'])
            self.add_numeric_item(row_idx, 7, account_data['final_credit_balance'])
            total_final_debit += account_data['final_debit_balance']
            total_final_credit += account_data['final_credit_balance']
        
        self.total_debit_label.setText(f"إجمالي الرصيد النهائي المدين: {total_final_debit:,.2f}")
        self.total_credit_label.setText(f"إجمالي الرصيد النهائي الدائن: {total_final_credit:,.2f}")

        style = "color: #27AE60;" if abs(total_final_debit - total_final_credit) < 0.01 else "color: #E74C3C;"
        self.total_debit_label.setStyleSheet(style + "font-weight: bold;")
        self.total_credit_label.setStyleSheet(style + "font-weight: bold;")

        self.report_table.resizeColumnsToContents()
        self.report_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

    def add_numeric_item(self, row, col, value):
        """إضافة عنصر رقمي إلى الجدول"""
        item = QTableWidgetItem(f"{value:,.2f}")
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.report_table.setItem(row, col, item)

    def open_general_ledger(self, item):
        """فتح الأستاذ العام للحساب المحدد"""
        selected_row = item.row()
        if selected_row < len(self.report_data):
            account_data = self.report_data[selected_row]
            if 'account_id' in account_data:
                gl_window = GeneralLedgerReportWindow(
                    account_id=account_data['account_id'],
                    start_date=self.start_date_edit.date(),
                    end_date=self.end_date_edit.date(),
                    parent=self
                )
                gl_window.show()
                self.child_windows.append(gl_window)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TrialBalanceReportWindow()
    window.show()
    sys.exit(app.exec_())
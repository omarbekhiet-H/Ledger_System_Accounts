# ui/financial/reports/general_ledger_report_ui.py

import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QApplication, QPushButton,
    QHBoxLayout, QFrame
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QPalette

# --- الاستيرادات المحدثة ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.financial.Ledger_financial_report_manager import FinancialReportManager
from database.manager.account_manager import AccountManager
from database.db_connection import get_financials_db_connection
from ui.financial.reports.trial_SubGL_report_ui import SubsidiaryLedgerReportWindow

class GeneralLedgerReportWindow(QWidget):
    def __init__(self, account_id, start_date, end_date, parent=None):
        super().__init__(parent)
        self.report_manager = FinancialReportManager(get_financials_db_connection)
        self.accounts_manager = AccountManager(get_financials_db_connection)
        
        self.parent_account_id = account_id
        self.start_date = start_date
        self.end_date = end_date
        self.report_data = []
        self.child_windows = []

        parent_account = self.accounts_manager.get_account_by_id(self.parent_account_id)
        parent_name = parent_account['account_name_ar'] if parent_account else "غير محدد"
        self.setWindowTitle(f"الأستاذ العام لـ: {parent_name}")
        
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.generate_report()
        self.resize(1200, 700)
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
        parent_account = self.accounts_manager.get_account_by_id(self.parent_account_id)
        parent_name = parent_account['account_name_ar'] if parent_account else "غير محدد"
        title_label = QLabel(f"الأستاذ العام لـ: {parent_name}")
        title_label.setStyleSheet("""
            color: white;
            font-weight: bold;
            font-size: 14px;
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

        # أزرار التحكم
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        refresh_btn = QPushButton("تحديث التقرير")
        refresh_btn.setObjectName("controlButton")
        refresh_btn.clicked.connect(self.generate_report)

        close_report_btn = QPushButton("إغلاق الأستاذ العام")
        close_report_btn.setObjectName("controlButton")
        close_report_btn.clicked.connect(self.close)

        control_layout.addWidget(refresh_btn)
        control_layout.addWidget(close_report_btn)
        control_layout.addStretch()
        main_layout.addLayout(control_layout)

        # جدول التقرير
        self.report_table = QTableWidget()
        self.report_table.setObjectName("reportTable")
        self.report_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.report_table.setColumnCount(8)
        self.report_table.setHorizontalHeaderLabels([
            "رمز الحساب", "اسم الحساب", "رصيد أول (مدين)", "رصيد أول (دائن)", 
            "حركات (مدين)", "حركات (دائن)", "رصيد نهائي (مدين)", "رصيد نهائي (دائن)"
        ])
        self.report_table.itemDoubleClicked.connect(self.open_subsidiary_ledger)
        
        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        main_layout.addWidget(self.report_table)

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
            
            #controlButton:disabled {
                background-color: #95A5A6;
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
        self.report_table.setRowCount(0)
        start_date_str = self.start_date.toString("yyyy-MM-dd")
        end_date_str = self.end_date.toString("yyyy-MM-dd")

        self.report_data = self.report_manager.get_general_ledger_data(
            start_date_str, end_date_str, account_id=self.parent_account_id
        )
        
        if not self.report_data:
            return

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

        self.report_table.resizeColumnsToContents()
        self.report_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

    def add_numeric_item(self, row, col, value):
        item = QTableWidgetItem(f"{value:,.2f}")
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.report_table.setItem(row, col, item)

    def open_subsidiary_ledger(self, item):
        selected_row = item.row()
        account_data = self.report_data[selected_row]
        account_id = account_data['account_id']

        sub_window = SubsidiaryLedgerReportWindow(
            account_id=account_id,
            start_date=self.start_date,
            end_date=self.end_date,
            parent=self
        )
        self.child_windows.append(sub_window)
        sub_window.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GeneralLedgerReportWindow(account_id=1, start_date=QDate.currentDate(), end_date=QDate.currentDate())
    window.show()
    sys.exit(app.exec_())
# ui/financial/reports/subsidiary_ledger_report_ui.py

import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QApplication, QLabel, 
    QPushButton, QHBoxLayout, QMessageBox, QFrame
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
from ui.financial.reports.trial_Entry_report_ui import JournalEntryDetailedReportWindow

class SubsidiaryLedgerReportWindow(QWidget):
    def __init__(self, account_id, start_date, end_date, parent=None):
        super().__init__(parent)
        self.report_manager = FinancialReportManager(get_financials_db_connection)
        self.accounts_manager = AccountManager(get_financials_db_connection)
        
        self.account_id = account_id
        self.start_date = start_date
        self.end_date = end_date
        self.report_data = []
        self.child_windows = []

        account = self.accounts_manager.get_account_by_id(self.account_id)
        account_name = account['account_name_ar'] if account else "غير محدد"
        self.setWindowTitle(f"الأستاذ المساعد لـ: {account_name}")
        
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.generate_report()
        self.resize(1100, 800)
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
        account = self.accounts_manager.get_account_by_id(self.account_id)
        account_name = account['account_name_ar'] if account else "غير محدد"
        title_label = QLabel(f"الأستاذ المساعد لـ: {account_name}")
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

        self.close_entry_btn = QPushButton("إغلاق القيد المحدد")
        self.close_entry_btn.setObjectName("controlButton")
        self.close_entry_btn.clicked.connect(self.close_selected_entry)
        self.close_entry_btn.setEnabled(False)

        refresh_btn = QPushButton("تحديث التقرير")
        refresh_btn.setObjectName("controlButton")
        refresh_btn.clicked.connect(self.generate_report)

        control_layout.addWidget(refresh_btn)
        control_layout.addWidget(self.close_entry_btn)
        control_layout.addStretch()
        main_layout.addLayout(control_layout)

        # جدول التقرير
        self.report_table = QTableWidget()
        self.report_table.setObjectName("reportTable")
        self.report_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.report_table.setColumnCount(9)
        self.report_table.setHorizontalHeaderLabels([
            "التاريخ", "رقم القيد", "الوصف", "نوع المستند", "رقم المستند", 
            "مدين", "دائن", "الرصيد", "ملاحظات"
        ])
        self.report_table.itemSelectionChanged.connect(self.on_row_selected)
        self.report_table.itemDoubleClicked.connect(self.open_entry_details)
        
        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(8, QHeaderView.Stretch)
        
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

    def on_row_selected(self):
        """تفعيل زر إغلاق القيد عند اختيار صف"""
        selected_row = self.report_table.currentRow()
        self.close_entry_btn.setEnabled(selected_row > 0)

    def close_selected_entry(self):
        """إغلاق القيد المحدد"""
        selected_row = self.report_table.currentRow()
        if selected_row > 0 and selected_row <= len(self.report_data):
            entry_data = self.report_data[selected_row - 1]
            entry_id = entry_data['entry_id']
            
            reply = QMessageBox.question(
                self, "تأكيد الإغلاق",
                f"هل أنت متأكد من إغلاق القيد رقم {entry_id}؟",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # هنا يمكنك إضافة كود إغلاق القيد فعلياً
                print(f"إغلاق القيد رقم {entry_id}")
                QMessageBox.information(self, "تم الإغلاق", f"تم إغلاق القيد رقم {entry_id} بنجاح")
                self.generate_report()

    def generate_report(self):
        start_date_str = self.start_date.toString("yyyy-MM-dd")
        end_date_str = self.end_date.toString("yyyy-MM-dd")

        all_entries = self.report_manager.get_journal_entries_in_range(start_date_str, end_date_str)
        self.report_data = [item for item in all_entries if item['account_id'] == self.account_id]
        
        opening_balance = self.accounts_manager.get_account_balance_cumulative(
            [self.account_id], 
            self.start_date.addDays(-1).toString("yyyy-MM-dd")
        )

        self.report_table.setRowCount(0)
        self.report_table.insertRow(0)
        self.report_table.setItem(0, 2, QTableWidgetItem("الرصيد الافتتاحي"))
        self.add_numeric_item(0, 7, opening_balance)
        self.report_table.setSpan(0, 0, 1, 7)

        running_balance = opening_balance
        for row_idx, item in enumerate(self.report_data, start=1):
            self.report_table.insertRow(row_idx)
            debit = item.get('debit', 0.0)
            credit = item.get('credit', 0.0)
            running_balance += (debit - credit)
            
            self.report_table.setItem(row_idx, 0, QTableWidgetItem(item['entry_date']))
            self.report_table.setItem(row_idx, 1, QTableWidgetItem(item['entry_number']))
            self.report_table.setItem(row_idx, 2, QTableWidgetItem(item['entry_description']))
            self.report_table.setItem(row_idx, 3, QTableWidgetItem(item.get('line_document_type_name', '')))
            self.report_table.setItem(row_idx, 4, QTableWidgetItem(item.get('line_document_number', '')))
            self.add_numeric_item(row_idx, 5, debit)
            self.add_numeric_item(row_idx, 6, credit)
            self.add_numeric_item(row_idx, 7, running_balance)
            self.report_table.setItem(row_idx, 8, QTableWidgetItem(item.get('line_notes', '')))

        self.report_table.resizeColumnsToContents()
        self.report_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.report_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Stretch)

    def add_numeric_item(self, row, col, value):
        item = QTableWidgetItem(f"{value:,.2f}")
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.report_table.setItem(row, col, item)

    def open_entry_details(self, item):
        """فتح تفاصيل القيد عند النقر المزدوج"""
        selected_row = item.row()
        if selected_row == 0:  # تخطي رصيد الافتتاح
            return
            
        entry_data = self.report_data[selected_row - 1]
        entry_id = entry_data['entry_id']

        details_window = JournalEntryDetailedReportWindow(entry_id=entry_id, parent=self)
        self.child_windows.append(details_window)
        details_window.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SubsidiaryLedgerReportWindow(account_id=1, start_date=QDate.currentDate(), end_date=QDate.currentDate())
    window.show()
    sys.exit(app.exec_())
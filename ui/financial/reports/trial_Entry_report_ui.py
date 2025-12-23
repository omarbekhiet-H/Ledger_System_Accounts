# ui/financial/reports/journal_entry_detailed_report_ui.py

import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QApplication, QPushButton,
    QHBoxLayout, QFrame, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

# --- الاستيرادات المحدثة ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.financial.Ledger_financial_report_manager import FinancialReportManager
from database.db_connection import get_financials_db_connection

class JournalEntryDetailedReportWindow(QWidget):
    def __init__(self, entry_id, parent=None):
        super().__init__(parent)
        self.entry_id = entry_id
        self.report_manager = FinancialReportManager(get_financials_db_connection)
        
        self.setWindowTitle(f"تفاصيل القيد رقم {entry_id}")
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_entry_data()
        self.resize(1000, 600)
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
        title_label = QLabel(f"تفاصيل القيد رقم {self.entry_id}")
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

        # معلومات القيد الأساسية
        self.info_layout = QHBoxLayout()
        self.info_layout.setSpacing(20)
        
        self.entry_number_label = QLabel()
        self.entry_date_label = QLabel()
        self.entry_desc_label = QLabel()
        
        for label in [self.entry_number_label, self.entry_date_label, self.entry_desc_label]:
            label.setStyleSheet("font-weight: bold; color: #2C3E50;")
        
        self.info_layout.addWidget(self.entry_desc_label)
        self.info_layout.addWidget(self.entry_date_label)
        self.info_layout.addWidget(self.entry_number_label)
        self.info_layout.addStretch()
        
        main_layout.addLayout(self.info_layout)

        # أزرار التحكم
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        print_btn = QPushButton("طباعة القيد")
        print_btn.setObjectName("controlButton")
        print_btn.clicked.connect(self.print_entry)

        close_btn = QPushButton("إغلاق النافذة")
        close_btn.setObjectName("controlButton")
        close_btn.clicked.connect(self.close)

        control_layout.addWidget(print_btn)
        control_layout.addWidget(close_btn)
        control_layout.addStretch()
        main_layout.addLayout(control_layout)

        # جدول تفاصيل القيد
        self.entry_table = QTableWidget()
        self.entry_table.setObjectName("entryTable")
        self.entry_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.entry_table.setColumnCount(8)
        self.entry_table.setHorizontalHeaderLabels([
            "الحساب", "مدين", "دائن", "رقم المستند", "نوع المستند",
            "مركز التكلفة", "نوع الضرائب", "ملاحظات"
        ])
        
        header = self.entry_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(7, QHeaderView.Stretch)
        
        main_layout.addWidget(self.entry_table)

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
            
            #entryTable {
                border: 1px solid #BDC3C7;
                gridline-color: #ECF0F1;
                selection-background-color: #3498DB;
                selection-color: white;
            }
            
            #entryTable QHeaderView::section {
                background-color: #2C3E50;
                color: white;
                padding: 5px;
                border: none;
            }
            
            #entryTable QTableCornerButton::section {
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

    def load_entry_data(self):
        """تحميل بيانات القيد"""
        entry_lines = self.report_manager.get_one_entry_details(self.entry_id)
        
        if not entry_lines:
            QMessageBox.warning(self, "خطأ", "لا يوجد بيانات لهذا القيد")
            self.close()
            return

        # عرض المعلومات الأساسية
        header_data = entry_lines[0]
        self.setWindowTitle(f"تفاصيل القيد: {header_data.get('entry_number', '')} - {header_data.get('entry_description', '')}")
        self.entry_number_label.setText(f"رقم القيد: {header_data.get('entry_number', '')}")
        self.entry_date_label.setText(f"التاريخ: {header_data.get('entry_date', '')}")
        self.entry_desc_label.setText(f"الوصف: {header_data.get('entry_description', '')}")

        # عرض بنود القيد
        self.entry_table.setRowCount(len(entry_lines))
        for row_idx, line_data in enumerate(entry_lines):
            account_display = f"{line_data.get('acc_code', '')} - {line_data.get('account_name_ar', '')}"
            self.entry_table.setItem(row_idx, 0, QTableWidgetItem(account_display))
            self.add_numeric_item(row_idx, 1, line_data.get('debit', 0.0))
            self.add_numeric_item(row_idx, 2, line_data.get('credit', 0.0))
            self.entry_table.setItem(row_idx, 3, QTableWidgetItem(line_data.get('line_document_number', '')))
            self.entry_table.setItem(row_idx, 4, QTableWidgetItem(line_data.get('document_type_name', '')))
            self.entry_table.setItem(row_idx, 5, QTableWidgetItem(line_data.get('cost_center_name', '')))
            self.entry_table.setItem(row_idx, 6, QTableWidgetItem(line_data.get('tax_type_name', '')))
            self.entry_table.setItem(row_idx, 7, QTableWidgetItem(line_data.get('line_notes', '')))

        self.entry_table.resizeColumnsToContents()
        self.entry_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.entry_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)

    def add_numeric_item(self, row, col, value):
        item = QTableWidgetItem(f"{value:,.2f}")
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.entry_table.setItem(row, col, item)

    def print_entry(self):
        """طباعة القيد"""
        QMessageBox.information(self, "طباعة", "جاري إعداد القيد للطباعة...")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = JournalEntryDetailedReportWindow(entry_id=1)
    window.show()
    sys.exit(app.exec_())
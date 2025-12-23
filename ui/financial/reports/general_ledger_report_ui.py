# ui/Audit/general_ledger_report_ui.py

import sys
import os
import csv
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDateEdit, QGroupBox, QGridLayout, QApplication, QStyle,
    QAbstractItemView, QLineEdit, QComboBox, QFileDialog, QFrame
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

# استيراد ملف الأنماط الموحد
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.financial.Ledger_financial_report_manager import FinancialReportManager
from database.manager.account_manager import AccountManager
from database.db_connection import get_financials_db_connection

class GeneralLedgerReportWindow(QWidget):
    def __init__(self, journal_manager=None, account_manager=None):
        super().__init__()
        self.journal_manager = journal_manager if journal_manager else FinancialReportManager(get_financials_db_connection)
        self.account_manager = account_manager if account_manager else AccountManager(get_financials_db_connection)
        self.selected_account_id = None
        self.totals = None

        self.setWindowTitle("تقرير الأستاذ العام")
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
        title_label = QLabel("تقرير الأستاذ العام")
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
        controls_layout.setSpacing(10)

        # إضافة عناصر التحكم
        controls_layout.addWidget(QLabel("رمز الحساب:"), 0, 0)
        self.account_code_input = QLineEdit()
        self.account_code_input.setPlaceholderText("اتركه فارغاً لعرض جميع الحسابات")
        self.account_code_input.textChanged.connect(self.update_account_name_from_code)
        controls_layout.addWidget(self.account_code_input, 0, 1)

        controls_layout.addWidget(QLabel("اسم الحساب:"), 0, 2)
        self.account_name_display = QLineEdit()
        self.account_name_display.setReadOnly(True)
        self.account_name_display.setStyleSheet("background-color: #ECF0F1; border: 1px solid #BDC3C7;")
        controls_layout.addWidget(self.account_name_display, 0, 3)

        controls_layout.addWidget(QLabel("من تاريخ:"), 1, 0)
        self.start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        controls_layout.addWidget(self.start_date_edit, 1, 1)

        controls_layout.addWidget(QLabel("إلى تاريخ:"), 1, 2)
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        controls_layout.addWidget(self.end_date_edit, 1, 3)

        self.generate_report_btn = QPushButton("توليد التقرير")
        self.generate_report_btn.setObjectName("controlButton")
        self.generate_report_btn.clicked.connect(self.generate_report)
        controls_layout.addWidget(self.generate_report_btn, 2, 0, 1, 2)

        self.print_btn = QPushButton("طباعة التقرير")
        self.print_btn.setObjectName("controlButton")
        self.print_btn.clicked.connect(self.print_report)
        controls_layout.addWidget(self.print_btn, 2, 2, 1, 1)

        self.export_btn = QPushButton("تصدير إلى Excel")
        self.export_btn.setObjectName("controlButton")
        self.export_btn.clicked.connect(self.export_to_excel)
        controls_layout.addWidget(self.export_btn, 2, 3, 1, 1)

        controls_layout.setColumnStretch(1, 1)
        controls_layout.setColumnStretch(3, 1)

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
        
        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for col in range(2, 8):
            header.setSectionResizeMode(col, QHeaderView.Stretch)
            header.setMinimumSectionSize(100)

        main_layout.addWidget(self.report_table)

        # إجماليات التقرير
        self.footer_layout = QHBoxLayout()
        self.footer_layout.setSpacing(10)
        
        self.total_debit_label = QLabel("إجمالي المدين: 0.00")
        self.total_credit_label = QLabel("إجمالي الدائن: 0.00")
        
        for label in [self.total_debit_label, self.total_credit_label]:
            label.setStyleSheet("""
                font-weight: bold;
                font-size: 14px;
                background-color: #E8F4FC;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                padding: 5px;
                margin: 2px;
                min-width: 120px;
            """)
        
        self.footer_layout.addStretch()
        self.footer_layout.addWidget(self.total_debit_label)
        self.footer_layout.addWidget(self.total_credit_label)
        main_layout.addLayout(self.footer_layout)

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
            
            QTableWidget::item[total-row="true"] {
                background-color: #D4EDDA;
                font-weight: bold;
                color: #155724;
                border-top: 2px solid #34495E;
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

    def update_account_name_from_code(self):
        account_code = self.account_code_input.text().strip()
        if not account_code:
            self.selected_account_id = None
            self.account_name_display.clear()
            return

        account = self.account_manager.get_account_by_code(account_code)
        if account:
            self.selected_account_id = account['id']
            self.account_name_display.setText(account['account_name_ar'])
        else:
            self.selected_account_id = None
            self.account_name_display.setText("لم يتم العثور على الحساب")

    def generate_report(self):
        self.report_table.setRowCount(0)

        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

        general_ledger_data = self.journal_manager.get_general_ledger_data(
            start_date, end_date, account_id=self.selected_account_id
        )

        if not general_ledger_data:
            QMessageBox.information(self, "لا توجد بيانات", "لا توجد حركات في الفترة المحددة للحسابات.")
            return

        self.totals = {
            'opening_debit': 0.0,
            'opening_credit': 0.0,
            'period_debit': 0.0,
            'period_credit': 0.0,
            'final_debit': 0.0,
            'final_credit': 0.0
        }

        for account_data in general_ledger_data:
            row = self.report_table.rowCount()
            self.report_table.insertRow(row)
            
            self.report_table.setItem(row, 0, QTableWidgetItem(account_data['acc_code']))
            self.report_table.setItem(row, 1, QTableWidgetItem(account_data['account_name_ar']))

            self.add_numeric_item(row, 2, account_data['opening_debit_balance'])
            self.add_numeric_item(row, 3, account_data['opening_credit_balance'])
            self.add_numeric_item(row, 4, account_data['period_debit'])
            self.add_numeric_item(row, 5, account_data['period_credit'])
            self.add_numeric_item(row, 6, account_data['final_debit_balance'])
            self.add_numeric_item(row, 7, account_data['final_credit_balance'])

            self.totals['opening_debit'] += account_data['opening_debit_balance']
            self.totals['opening_credit'] += account_data['opening_credit_balance']
            self.totals['period_debit'] += account_data['period_debit']
            self.totals['period_credit'] += account_data['period_credit']
            self.totals['final_debit'] += account_data['final_debit_balance']
            self.totals['final_credit'] += account_data['final_credit_balance']

        self.add_totals_row()
        self.update_footer_totals()
        self.report_table.resizeColumnsToContents()
        self.report_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

    def add_numeric_item(self, row, col, value):
        item = QTableWidgetItem(f"{value:,.2f}")
        item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.report_table.setItem(row, col, item)
        return item

    def add_totals_row(self):
        if not self.totals:
            return

        row = self.report_table.rowCount()
        self.report_table.insertRow(row)

        total_label_item = QTableWidgetItem("الإجماليات")
        total_label_item.setTextAlignment(Qt.AlignCenter)
        total_label_item.setFont(QFont("Arial", 10, QFont.Bold))
        total_label_item.setData(Qt.UserRole, "total-row")
        self.report_table.setItem(row, 0, total_label_item)

        numeric_cols = [2, 3, 4, 5, 6, 7]
        total_values = [
            self.totals['opening_debit'], self.totals['opening_credit'],
            self.totals['period_debit'], self.totals['period_credit'],
            self.totals['final_debit'], self.totals['final_credit']
        ]

        for i, col in enumerate(numeric_cols):
            item = self.add_numeric_item(row, col, total_values[i])
            item.setData(Qt.UserRole, "total-row")
            item.setFont(QFont("Arial", 10, QFont.Bold))

        self.report_table.setSpan(row, 0, 1, 2)

    def update_footer_totals(self):
        if not self.totals:
            return

        self.total_debit_label.setText(f"إجمالي المدين: {self.totals['final_debit']:,.2f}")
        self.total_credit_label.setText(f"إجمالي الدائن: {self.totals['final_credit']:,.2f}")

        # تغيير اللون حسب التوازن
        if abs(self.totals['final_debit'] - self.totals['final_credit']) < 0.01:
            color = "#27AE60"  # أخضر
        else:
            color = "#E74C3C"  # أحمر

        self.total_debit_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.total_credit_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def print_report(self):
        if self.report_table.rowCount() == 0:
            QMessageBox.warning(self, "تحذير", "لا توجد بيانات لطباعتها!")
            return

        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageOrientation(QPrinter.Landscape)
        print_dialog = QPrintDialog(printer, self)
        
        if print_dialog.exec_() == QPrintDialog.Accepted:
            # هنا يمكنك إضافة كود الطباعة الفعلي
            QMessageBox.information(self, "طباعة", "جاري إعداد التقرير للطباعة...")

    def export_to_excel(self):
        if self.report_table.rowCount() == 0:
            QMessageBox.warning(self, "تحذير", "لا توجد بيانات لتصديرها!")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "حفظ الملف", "", "ملفات Excel (*.csv);;جميع الملفات (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # كتابة العناوين
                headers = []
                for col in range(self.report_table.columnCount()):
                    headers.append(self.report_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # كتابة البيانات
                for row in range(self.report_table.rowCount()):
                    row_data = []
                    for col in range(self.report_table.columnCount()):
                        item = self.report_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
                
                # كتابة الإجماليات
                totals_row = [""] * self.report_table.columnCount()
                totals_row[0] = "الإجماليات"
                totals_row[6] = f"{self.totals['final_debit']:,.2f}"
                totals_row[7] = f"{self.totals['final_credit']:,.2f}"
                writer.writerow(totals_row)
                
            QMessageBox.information(self, "تم التصدير", f"تم حفظ الملف بنجاح:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تصدير الملف:\n{str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GeneralLedgerReportWindow()
    window.show()
    sys.exit(app.exec_())
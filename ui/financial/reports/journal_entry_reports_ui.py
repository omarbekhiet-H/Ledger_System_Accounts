# ui/financial/reports/journal_entry_report_ui.py

import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDateEdit, QGroupBox, QGridLayout, QApplication,
    QAbstractItemView, QStyle
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

# =====================================================================
# تصحيح مسار المشروع الجذر
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# استيراد الكلاسات المطلوبة
from database.manager.financial.transactions.journal_summary_manager import JournalSummaryManager
from database.db_connection import get_financials_db_connection
# استيراد نافذة التفاصيل لعرضها عند النقر
from ui.financial.reports.trial_Entry_report_ui import JournalEntryDetailedReportWindow

# =====================================================================
# دالة مساعدة لتحميل ملف التصميم
# =====================================================================
def load_qss_file(file_path):
    """Loads content from a QSS file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: QSS file not found at {file_path}")
        return ""
    except Exception as e:
        print(f"ERROR: Could not load QSS file {file_path}: {e}")
        return ""

class JournalEntryReportWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.summary_manager = JournalSummaryManager(get_financials_db_connection)
        self.setWindowTitle("تقرير قيود اليومية الإجمالي")
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        title_label = QLabel("تقرير قيود اليومية الإجمالي")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        controls_group = QGroupBox("خيارات التقرير")
        controls_layout = QGridLayout(controls_group)
        
        controls_layout.addWidget(QLabel("من تاريخ:"), 0, 0)
        self.start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        controls_layout.addWidget(self.start_date_edit, 0, 1)

        controls_layout.addWidget(QLabel("إلى تاريخ:"), 0, 2)
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        controls_layout.addWidget(self.end_date_edit, 0, 3)

        self.generate_report_btn = QPushButton("توليد التقرير")
        self.generate_report_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.generate_report_btn.clicked.connect(self.generate_report)
        controls_layout.addWidget(self.generate_report_btn, 1, 0, 1, 4)
        
        main_layout.addWidget(controls_group)

        self.report_table = QTableWidget()
        self.report_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.report_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.report_table.setAlternatingRowColors(True)
        
        # --- إضافة عمود مخفي لتخزين ID القيد ---
        self.report_table.setColumnCount(7) 
        self.report_table.setHorizontalHeaderLabels([
            "ID", "رقم القيد", "التاريخ", "الوصف", "نوع الحركة", 
            "إجمالي مدين", "إجمالي دائن"
        ])
        # إخفاء عمود الـ ID
        self.report_table.setColumnHidden(0, True)
        
        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch) # الوصف
        
        # --- ربط النقر المزدوج على الجدول بدالة فتح التفاصيل ---
        self.report_table.doubleClicked.connect(self.open_entry_details)
        
        main_layout.addWidget(self.report_table)

    def add_numeric_item(self, row, col, value):
        item = QTableWidgetItem(f"{value:,.2f}")
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.report_table.setItem(row, col, item)

    def generate_report(self):
        self.report_table.setRowCount(0)
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

        summary_data = self.summary_manager.get_summary_entries_in_range(start_date, end_date)

        if not summary_data:
            QMessageBox.information(self, "لا توجد بيانات", "لا توجد قيود يومية في الفترة المحددة.")
            return

        for row, entry in enumerate(summary_data):
            self.report_table.insertRow(row)
            
            # تخزين ID القيد في العمود المخفي (العمود رقم 0)
            entry_id = entry.get('id', -1)
            self.report_table.setItem(row, 0, QTableWidgetItem(str(entry_id)))
            
            # عرض باقي البيانات في الأعمدة الظاهرة
            self.report_table.setItem(row, 1, QTableWidgetItem(entry.get('entry_number', '')))
            self.report_table.setItem(row, 2, QTableWidgetItem(entry.get('entry_date', '')))
            self.report_table.setItem(row, 3, QTableWidgetItem(entry.get('description', '')))
            self.report_table.setItem(row, 4, QTableWidgetItem(entry.get('transaction_type_name', '')))
            #self.report_table.setItem(row, 5, QTableWidgetItem(entry.get('currency_code', '')))
            self.add_numeric_item(row, 5, entry.get('total_debit', 0.0))
            self.add_numeric_item(row, 6, entry.get('total_credit', 0.0))

        self.report_table.resizeColumnsToContents()
        self.report_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

    def open_entry_details(self, index):
        """
        تفتح نافذة جديدة تعرض تفاصيل القيد الذي تم النقر عليه.
        """
        selected_row = index.row()
        # استرجاع ID القيد من العمود المخفي
        entry_id_item = self.report_table.item(selected_row, 0)
        
        if not entry_id_item:
            QMessageBox.warning(self, "خطأ", "لا يمكن تحديد القيد.")
            return
            
        entry_id = int(entry_id_item.text())
        
        # إنشاء وعرض نافذة التفاصيل
        # نمرر لها ID القيد لتستخدمه في جلب البيانات
        #self.details_window = JournalEntryDetailedReportWindow(entry_id)
        details_window = JournalEntryDetailedReportWindow(entry_id, self) # نمرر self لتكون النافذة تابعة للنافذة الرئيسية
        details_window.show()

# --- للتشغيل المستقل والاختبار ---
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # --- بناء مسار ملف التصميم وتطبيقه ---
    qss_file_path = os.path.join(project_root, 'ui', 'styles', 'styles.qss')
    stylesheet = load_qss_file(qss_file_path)
    if stylesheet:
        app.setStyleSheet(stylesheet)
        print(f"DEBUG: Stylesheet loaded successfully from {qss_file_path}")
    else:
        print("WARNING: Failed to load stylesheet.")

    window = JournalEntryReportWindow()
    window.showMaximized()
    sys.exit(app.exec_())

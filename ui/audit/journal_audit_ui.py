# ui/Audit/journal_audit_ui.py
import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDateEdit, QGroupBox, QApplication, QStyle,
    QAbstractItemView 
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

# =====================================================================
# تصحيح مسار المشروع الجذر لتمكين الاستيراد الصحيح
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..')) 
if project_root not in sys.path:
    sys.path.append(project_root)

# Import necessary managers

from database.manager.financial.journal_entry_manager import JournalEntryManager
from database.manager.financial_lookups_manager import FinancialLookupsManager
from database.manager.account_manager import AccountManager 
from database.db_connection import get_financials_db_connection

# استيراد JournalEntryManagementWindow لعرض التفاصيل
from ui.financial.journal_entry_ui import JournalEntryManagementWindow


class JournalAuditReportWindow(QWidget):
    def __init__(self, journal_manager=None, lookup_manager=None, account_manager=None):
        super().__init__()
        # استخدم الـ managers الذين تم تمريرهم أو أنشئ جدد
        self.journal_manager = journal_manager or JournalEntryManager(get_financials_db_connection)
        self.lookup_manager = lookup_manager or FinancialLookupsManager(get_financials_db_connection)
        self.account_manager = account_manager or AccountManager(get_financials_db_connection)
        
        # قائمة للحفاظ على نوافذ التفاصيل المفتوحة من الحذف بواسطة الـ Garbage Collector
        self.detail_windows = [] 

        self.setWindowTitle("تقرير مراجعة القيود اليومية (المدقق)")
        self.setLayoutDirection(Qt.RightToLeft)
        QApplication.instance().setLayoutDirection(Qt.RightToLeft)
        
        self.STATUS_MAP = {
            "Under Review": {"name": "تحت المراجعة", "color": QColor(255, 255, 204)},
            "Under Audit": {"name": "تحت التدقيق", "color": QColor(204, 229, 255)},
            "Audited": {"name": "تم التدقيق", "color": QColor(204, 255, 204)},
            "Rejected by Auditor": {"name": "مرفوض من المدقق", "color": QColor(255, 204, 204)},
            "All": {"name": "الكل", "color": QColor(240, 240, 240)}
        }
        self.current_filter_status = "All"

        self.init_ui()
        self.load_journal_entries_for_audit(self.current_filter_status) 

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("تقرير مراجعة القيود اليومية (المدقق)")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        filter_group_box = QGroupBox("خيارات التصفية")
        filter_layout = QVBoxLayout(filter_group_box)
        
        date_filter_layout = QHBoxLayout()
        self.start_date_filter = QDateEdit(QDate.currentDate().addYears(-1))
        self.start_date_filter.setCalendarPopup(True)
        self.start_date_filter.setDisplayFormat("yyyy-MM-dd")
        self.end_date_filter = QDateEdit(QDate.currentDate())
        self.end_date_filter.setCalendarPopup(True)
        self.end_date_filter.setDisplayFormat("yyyy-MM-dd")
        self.apply_date_filter_btn = QPushButton("تطبيق فلتر التاريخ")
        self.apply_date_filter_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.apply_date_filter_btn.clicked.connect(lambda: self.load_journal_entries_for_audit(self.current_filter_status))
        date_filter_layout.addWidget(QLabel("من تاريخ:"))
        date_filter_layout.addWidget(self.start_date_filter)
        date_filter_layout.addWidget(QLabel("إلى تاريخ:"))
        date_filter_layout.addWidget(self.end_date_filter)
        date_filter_layout.addWidget(self.apply_date_filter_btn)
        filter_layout.addLayout(date_filter_layout)

        status_buttons_layout = QHBoxLayout()
        self.status_buttons = {}
        for status_code, status_info in self.STATUS_MAP.items():
            btn = QPushButton(f"{status_info['name']} (0)")
            btn.setStyleSheet(f"background-color: {status_info['color'].name()};")
            btn.clicked.connect(lambda checked, sc=status_code: self.load_journal_entries_for_audit(sc))
            status_buttons_layout.addWidget(btn)
            self.status_buttons[status_code] = btn
        filter_layout.addLayout(status_buttons_layout)
        main_layout.addWidget(filter_group_box)

        self.journal_table = QTableWidget()
        self.journal_table.setColumnCount(8)
        self.journal_table.setHorizontalHeaderLabels(["ID", "رقم القيد", "التاريخ", "الوصف", "القيمة", "الحالة", "نوع المستند", "العملة"])
        self.journal_table.setColumnHidden(0, True)
        self.journal_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.journal_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.journal_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.journal_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # استخدام الضغط المزدوج هو الأفضل لتجنب الفتح العرضي
        self.journal_table.itemDoubleClicked.connect(self.view_selected_journal_entry_details)
        main_layout.addWidget(self.journal_table)

        action_buttons_layout = QHBoxLayout()
        self.mark_under_audit_btn = QPushButton("وضع تحت التدقيق")
        self.approve_audit_btn = QPushButton("اعتماد من المدقق")
        self.reject_audit_btn = QPushButton("رفض من المدقق")
        self.view_details_btn = QPushButton("عرض التفاصيل")
        
        self.mark_under_audit_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.approve_audit_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.reject_audit_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.view_details_btn.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))

        action_buttons_layout.addWidget(self.mark_under_audit_btn)
        action_buttons_layout.addWidget(self.approve_audit_btn)
        action_buttons_layout.addWidget(self.reject_audit_btn)
        action_buttons_layout.addWidget(self.view_details_btn)
        main_layout.addLayout(action_buttons_layout)

        self.mark_under_audit_btn.clicked.connect(lambda: self.change_selected_entries_status("Under Audit"))
        self.approve_audit_btn.clicked.connect(lambda: self.change_selected_entries_status("Audited"))
        self.reject_audit_btn.clicked.connect(lambda: self.change_selected_entries_status("Rejected by Auditor"))
        self.view_details_btn.clicked.connect(self.view_selected_journal_entry_details)

    def load_journal_entries_for_audit(self, status_to_filter=None):
        self.current_filter_status = status_to_filter or self.current_filter_status
        start_date = self.start_date_filter.date().toString(Qt.ISODate)
        end_date = self.end_date_filter.date().toString(Qt.ISODate)
        self.journal_table.setRowCount(0)

        full_entries_list = self.journal_manager.get_all_journal_entries()
        all_entries_in_date_range = [entry for entry in full_entries_list if start_date <= entry['entry_date'] <= end_date]

        status_counts = {code: 0 for code in self.STATUS_MAP}
        for entry in all_entries_in_date_range:
            status = entry.get('status', 'Unknown')
            if status in status_counts:
                status_counts[status] += 1
        status_counts["All"] = len(all_entries_in_date_range)

        for code, btn in self.status_buttons.items():
            btn.setText(f"{self.STATUS_MAP[code]['name']} ({status_counts.get(code, 0)})")

        entries_to_display = all_entries_in_date_range if self.current_filter_status == "All" else [e for e in all_entries_in_date_range if e.get('status') == self.current_filter_status]
        
        self.journal_table.setRowCount(len(entries_to_display))
        for row, entry in enumerate(entries_to_display):
            self.journal_table.setItem(row, 0, QTableWidgetItem(str(entry['id'])))
            self.journal_table.setItem(row, 1, QTableWidgetItem(str(entry['entry_number'])))
            self.journal_table.setItem(row, 2, QTableWidgetItem(entry['entry_date']))
            self.journal_table.setItem(row, 3, QTableWidgetItem(entry['description']))
            self.journal_table.setItem(row, 4, QTableWidgetItem(f"{entry['total_debit']:.2f}"))
            self.journal_table.setItem(row, 5, QTableWidgetItem(entry.get('status', 'N/A')))
            self.journal_table.setItem(row, 6, QTableWidgetItem(entry.get('transaction_type_name', 'N/A')))
       
            
            color = self.STATUS_MAP.get(entry.get('status'), {}).get('color', QColor(255, 255, 255))
            for col in range(self.journal_table.columnCount()):
                if self.journal_table.item(row, col):
                    self.journal_table.item(row, col).setBackground(color)
        self.journal_table.resizeColumnsToContents()

    def change_selected_entries_status(self, new_status):
        selected_rows = self.journal_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد قيد واحد على الأقل.")
            return

        reply = QMessageBox.question(self, "تأكيد التغيير", 
                                    f"هل تريد تغيير حالة القيود المحددة إلى '{new_status}'؟", 
                                    QMessageBox.Yes | QMessageBox.No, 
                                    QMessageBox.No)
        if reply == QMessageBox.No:
            return

        success_count = 0
        for index in selected_rows:
            journal_id = int(self.journal_table.item(index.row(), 0).text())
            
            # استدعاء الدالة الجديدة التي أضفناها في JournalManager
            success = self.journal_manager.set_journal_entry_status(journal_id, new_status)
            if success:
                success_count += 1
        
        if success_count > 0:
            QMessageBox.information(self, "تحديث الحالة", f"تم تحديث حالة {success_count} قيد بنجاح.")
        else:
            QMessageBox.warning(self, "فشل التحديث", "لم يتم تحديث حالة أي من القيود المحددة.")

        # إعادة تحميل القيود بنفس الفلتر الحالي لإظهار التغييرات فوراً
        self.load_journal_entries_for_audit(self.current_filter_status)

    def view_selected_journal_entry_details(self):
        selected_rows = self.journal_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد قيد لعرض تفاصيله.")
            return
        
        selected_row_index = selected_rows[0].row()
        journal_id_item = self.journal_table.item(selected_row_index, 0)
        
        if not journal_id_item or not journal_id_item.text():
            QMessageBox.warning(self, "خطأ", "لا يمكن العثور على معرف القيد.")
            return
            
        journal_id = int(journal_id_item.text())
        
        entry_details = self.journal_manager.get_journal_entry_by_id(journal_id)
        entry_lines = self.journal_manager.get_journal_entry_lines(journal_id)

        if not entry_details:
            QMessageBox.warning(self, "خطأ", f"لم يتم العثور على تفاصيل القيد رقم {journal_id}.")
            return

        # إنشاء نسخة جديدة من نافذة التفاصيل
        # هذه النافذة ستستخدم الـ managers الافتراضيين الخاصين بها
        detail_window = JournalEntryManagementWindow()
        
        # استدعاء دالة تحميل البيانات على النسخة التي تم إنشاؤها
        detail_window.load_entry_for_edit(entry_details, entry_lines)
        
        # جعل النافذة للقراءة فقط (نفترض وجود هذه الدالة)
        if hasattr(detail_window, 'set_read_only_mode'):
            detail_window.set_read_only_mode(True)
        
        # إضافة النافذة إلى قائمة للحفاظ عليها من الحذف
        self.detail_windows.append(detail_window)
        detail_window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # يمكنك وضع كود الأنماط هنا إذا أردت
    # app.setStyleSheet(...)
    
    # تهيئة قاعدة البيانات إذا لزم الأمر
    from database.schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT
    try:
        conn = get_financials_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='journal_entries';")
            if not cursor.fetchone():
                cursor.executescript(FINANCIALS_SCHEMA_SCRIPT)
                conn.commit()
            conn.close()
    except Exception as e:
        QMessageBox.critical(None, "خطأ في قاعدة البيانات", f"فشل تهيئة المخطط: {e}")
        sys.exit(1)
            
    window = JournalAuditReportWindow()
    window.show()
    sys.exit(app.exec_())
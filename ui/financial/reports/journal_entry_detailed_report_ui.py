# ui/financial/reports/journal_entry_detailed_report_ui.py
import sqlite3
import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QApplication, QStyle, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# --- الاستيرادات المحدثة ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.financial.reports.financial_report_manager import FinancialReportManager
from database.db_connection import get_financials_db_connection

class JournalEntryDetailedReportWindow(QWidget):
    def __init__(self, entry_id, parent=None):
        super().__init__(parent)
        
        self.entry_id = entry_id
        self.report_manager = FinancialReportManager(get_financials_db_connection)
        
        self.setWindowTitle("تفاصيل القيد")
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_entry_data()
        self.resize(800, 500)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.report_table = QTableWidget()
        self.report_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.report_table.setColumnCount(8)
        self.report_table.setHorizontalHeaderLabels([
            "الحساب", "مدين", "دائن", "رقم المستند", "نوع المستند",
            "مركز التكلفة", "نوع الضرائب", "ملاحظات"
        ])
        main_layout.addWidget(self.report_table)

        button_layout = QHBoxLayout()
        self.close_btn = QPushButton(" إغلاق")
        self.close_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        self.close_btn.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

    def load_entry_data(self):
        # استخدم الدالة الجديدة التي أضفتها
        entry_lines = self.get_one_entry_details(self.entry_id)
        
        if not entry_lines:
            self.close()
            return

        header_data = entry_lines[0]
        self.setWindowTitle(f"تفاصيل القيد: {header_data.get('entry_number', '')} - {header_data.get('entry_description', '')}")
        
        # تأكد من مسح الجدول أولاً
        self.report_table.setRowCount(0)
        
        for row, line_data in enumerate(entry_lines):
            self.report_table.insertRow(row)
            
            # إنشاء عناصر جديدة لكل خلية (لا تعيد استخدام العناصر)
            account_display = f"{line_data.get('acc_code', '')} - {line_data.get('account_name_ar', '')}"
            self.report_table.setItem(row, 0, QTableWidgetItem(account_display))
            
            # استخدام الدالة المساعدة لإضافة العناصر الرقمية
            self.add_numeric_item(row, 1, line_data.get('debit', 0.0))
            self.add_numeric_item(row, 2, line_data.get('credit', 0.0))
            
            # إنشاء عناصر جديدة لكل خلية
            self.report_table.setItem(row, 3, QTableWidgetItem(str(line_data.get('line_document_number') or '')))
            self.report_table.setItem(row, 4, QTableWidgetItem(str(line_data.get('document_type_name') or '')))
            self.report_table.setItem(row, 5, QTableWidgetItem(str(line_data.get('cost_center_name') or '')))
            self.report_table.setItem(row, 6, QTableWidgetItem(str(line_data.get('tax_type_name') or '')))
            self.report_table.setItem(row, 7, QTableWidgetItem(str(line_data.get('line_notes') or '')))

        self.report_table.resizeColumnsToContents()
        self.report_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.report_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)

    def add_numeric_item(self, row, col, value):
        # إنشاء عنصر جديد دائماً
        item = QTableWidgetItem(f"{float(value or 0):,.2f}")
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.report_table.setItem(row, col, item)

    def get_one_entry_details(self, entry_id):
        """
        يجلب التفاصيل الكاملة لقيد واحد محدد بواسطة الـ ID الخاص به.
        هذه الدالة أكثر كفاءة من جلب كل القيود ثم فلترتها.
        """
        conn = None
        try:
            conn = get_financials_db_connection()  # استخدام دالة الاتصال الصحيحة
            if conn is None: 
                return []

            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # نفس الاستعلام القوي، ولكن مع فلترة بـ je.id
            query = """
                SELECT
                    je.id AS entry_id, je.entry_number, je.entry_date,
                    je.description AS entry_description, je.status,
                    tt.name_ar AS transaction_type_name,
                    jel.id AS line_id, jel.debit, jel.credit,
                    jel.notes AS line_notes, jel.document_number AS line_document_number,
                    a.acc_code, a.account_name_ar,
                    cost.name_ar AS cost_center_name,
                    tax.name_ar AS tax_type_name,
                    doc.name_ar AS document_type_name
                FROM
                    journal_entries je
                JOIN
                    journal_entry_lines jel ON je.id = jel.journal_entry_id
                LEFT JOIN accounts a ON jel.account_id = a.id
                LEFT JOIN transaction_types tt ON je.transaction_type_id = tt.id
                LEFT JOIN cost_centers cost ON jel.cost_center_id = cost.id
                LEFT JOIN tax_types tax ON jel.tax_type_id = tax.id
                LEFT JOIN document_types doc ON jel.document_type_id = doc.id
                WHERE
                    je.id = ?  -- <-- الفلترة هنا
                ORDER BY
                    jel.id ASC;
            """
            
            cursor.execute(query, (entry_id,))
            results = [dict(row) for row in cursor.fetchall()]
            return results

        except sqlite3.Error as e:
            print(f"DATABASE ERROR in get_one_entry_details: {e}")
            return []
        finally:
            if conn:
                conn.close()
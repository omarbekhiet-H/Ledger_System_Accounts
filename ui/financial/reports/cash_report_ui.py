import sys
import os
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QMessageBox, QDialog, QGroupBox, 
                             QHeaderView, QDateEdit, QDialogButtonBox, QGridLayout,
                             QFrame, QTextEdit)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QDoubleValidator, QIcon

# --- Project Path and Database Setup ---
project_root = os.getcwd()
DB_PATH = os.path.join(project_root, 'database', 'financials.db')

class CashMovementReportApp(QMainWindow):
    def __init__(self, db_path=None, parent=None):
        super().__init__(parent)
        # تحديد مسار قاعدة البيانات بشكل صحيح
        if db_path is None:
            self.db_path = DB_PATH
        else:
            self.db_path = db_path
            
        # التحقق من وجود قاعدة البيانات
        if not os.path.exists(self.db_path):
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"ملف قاعدة البيانات غير موجود في المسار:\n{self.db_path}")
            sys.exit(1)
            
        self.initUI()
        self.load_cash_chests()
        self.generate_report()

    def initUI(self):
        self.setWindowTitle('تقرير حركة الخزينة')
        self.setGeometry(100, 100, 1400, 800)
        self.setLayoutDirection(Qt.RightToLeft)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel('تقرير حركة الخزينة')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        main_layout.addWidget(title_label)
        
        # Filter Group
        filter_group = QGroupBox("معايير التقرير")
        filter_layout = QGridLayout(filter_group)
        
        self.cash_chest_combo = QComboBox()
        self.start_date = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        
        filter_layout.addWidget(QLabel("الصندوق:"), 0, 0)
        filter_layout.addWidget(self.cash_chest_combo, 0, 1)
        filter_layout.addWidget(QLabel("من تاريخ:"), 0, 2)
        filter_layout.addWidget(self.start_date, 0, 3)
        filter_layout.addWidget(QLabel("إلى تاريخ:"), 0, 4)
        filter_layout.addWidget(self.end_date, 0, 5)
        
        main_layout.addWidget(filter_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.generate_btn = QPushButton("توليد التقرير")
        self.generate_btn.clicked.connect(self.generate_report)
        self.generate_btn.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.export_btn = QPushButton("تصدير إلى Excel")
        self.export_btn.clicked.connect(self.export_to_excel)
        self.export_btn.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.print_btn = QPushButton("طباعة التقرير")
        self.print_btn.clicked.connect(self.print_report)
        self.print_btn.setFont(QFont("Arial", 12, QFont.Bold))
        
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.print_btn)
        main_layout.addLayout(button_layout)
        
        # Summary Group
        summary_group = QGroupBox("ملخص التقرير")
        summary_layout = QGridLayout(summary_group)
        
        self.opening_balance = QLabel("0.00")
        self.total_receipts = QLabel("0.00")
        self.total_payments = QLabel("0.00")
        self.closing_balance = QLabel("0.00")
        self.transaction_count = QLabel("0")
        
        summary_layout.addWidget(QLabel("الرصيد الافتتاحي:"), 0, 0)
        summary_layout.addWidget(self.opening_balance, 0, 1)
        summary_layout.addWidget(QLabel("إجمالي المتحصلات:"), 0, 2)
        summary_layout.addWidget(self.total_receipts, 0, 3)
        summary_layout.addWidget(QLabel("إجمالي المدفوعات:"), 1, 0)
        summary_layout.addWidget(self.total_payments, 1, 1)
        summary_layout.addWidget(QLabel("الرصيد الختامي:"), 1, 2)
        summary_layout.addWidget(self.closing_balance, 1, 3)
        summary_layout.addWidget(QLabel("عدد المعاملات:"), 2, 0)
        summary_layout.addWidget(self.transaction_count, 2, 1)
        
        main_layout.addWidget(summary_group)
        
        # Report Table
        self.report_table = QTableWidget()
        self.report_table.setColumnCount(8)
        self.report_table.setHorizontalHeaderLabels([
            'التاريخ', 'رقم الإيصال', 'رقم القيد', 'نوع المعاملة', 
            'البيان', 'المدين (قبض)', 'الدائن (صرف)', 'الرصيد'
        ])
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.report_table)

    def load_cash_chests(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.id, a.acc_code, a.account_name_ar 
                    FROM cash_chests c 
                    JOIN accounts a ON c.account_id = a.id 
                    WHERE c.is_active = 1 
                    ORDER BY a.acc_code
                """)
                
                self.cash_chest_combo.clear()
                self.cash_chest_combo.addItem("جميع الصناديق", 0)
                
                for chest_id, code, name in cursor.fetchall():
                    self.cash_chest_combo.addItem(f"{code} - {name}", chest_id)
                    
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل الصناديق: {e}")

    def generate_report(self):
        try:
            cash_chest_id = self.cash_chest_combo.currentData()
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get opening balance (balance before start date)
                opening_balance = self.get_opening_balance(cash_chest_id, start_date)
                
                # Get transactions for the period
                transactions = self.get_transactions(cash_chest_id, start_date, end_date)
                
                # Calculate running balance
                current_balance = opening_balance
                transaction_data = []
                
                total_receipts = 0
                total_payments = 0
                
                for transaction in transactions:
                    trans_date, voucher_num, je_num, trans_type, description, amount = transaction
                    
                    if trans_type == 'قبض نقدي':
                        debit = amount
                        credit = 0
                        total_receipts += amount
                    else:  # صرف نقدي
                        debit = 0
                        credit = amount
                        total_payments += amount
                    
                    current_balance += debit - credit
                    
                    transaction_data.append({
                        'date': trans_date,
                        'voucher_num': voucher_num,
                        'je_num': je_num,
                        'type': trans_type,
                        'description': description,
                        'debit': debit,
                        'credit': credit,
                        'balance': current_balance
                    })
                
                # Update summary
                self.opening_balance.setText(f"{opening_balance:,.2f}")
                self.total_receipts.setText(f"{total_receipts:,.2f}")
                self.total_payments.setText(f"{total_payments:,.2f}")
                self.closing_balance.setText(f"{current_balance:,.2f}")
                self.transaction_count.setText(str(len(transactions)))
                
                # Populate table
                self.populate_table(transaction_data)
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في توليد التقرير: {e}")

    def get_opening_balance(self, cash_chest_id, start_date):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT COALESCE(SUM(
                        CASE 
                            WHEN cbt.transaction_type = 'قبض نقدي' THEN cbt.amount 
                            WHEN cbt.transaction_type = 'صرف نقدي' THEN -cbt.amount 
                            ELSE 0 
                        END
                    ), 0) as opening_balance
                    FROM cash_bank_transactions cbt
                    WHERE cbt.transaction_date < ?
                """
                params = [start_date]
                
                if cash_chest_id != 0:
                    query += " AND cbt.cash_chest_id = ?"
                    params.append(cash_chest_id)
                
                cursor.execute(query, params)
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في حساب الرصيد الافتتاحي: {e}")
            return 0

    def get_transactions(self, cash_chest_id, start_date, end_date):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        cbt.transaction_date,
                        cbt.transaction_number,
                        je.entry_number,
                        cbt.transaction_type,
                        cbt.description,
                        cbt.amount
                    FROM cash_bank_transactions cbt
                    LEFT JOIN journal_entries je ON cbt.journal_entry_id = je.id
                    WHERE cbt.transaction_date BETWEEN ? AND ?
                    AND cbt.transaction_type IN ('قبض نقدي', 'صرف نقدي')
                """
                
                params = [start_date, end_date]
                
                if cash_chest_id != 0:
                    query += " AND cbt.cash_chest_id = ?"
                    params.append(cash_chest_id)
                
                query += " ORDER BY cbt.transaction_date, cbt.transaction_number"
                
                cursor.execute(query, params)
                return cursor.fetchall()
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في جلب المعاملات: {e}")
            return []

    def populate_table(self, transactions):
        self.report_table.setRowCount(len(transactions))
        
        for row, transaction in enumerate(transactions):
            self.report_table.setItem(row, 0, QTableWidgetItem(transaction['date']))
            self.report_table.setItem(row, 1, QTableWidgetItem(transaction['voucher_num']))
            self.report_table.setItem(row, 2, QTableWidgetItem(transaction['je_num'] or ''))
            self.report_table.setItem(row, 3, QTableWidgetItem(transaction['type']))
            self.report_table.setItem(row, 4, QTableWidgetItem(transaction['description']))
            self.report_table.setItem(row, 5, QTableWidgetItem(f"{transaction['debit']:,.2f}" if transaction['debit'] > 0 else ''))
            self.report_table.setItem(row, 6, QTableWidgetItem(f"{transaction['credit']:,.2f}" if transaction['credit'] > 0 else ''))
            self.report_table.setItem(row, 7, QTableWidgetItem(f"{transaction['balance']:,.2f}"))
            
            # Color coding
            if transaction['debit'] > 0:  # Receipts
                for col in [5, 7]:
                    item = self.report_table.item(row, col)
                    if item:
                        item.setBackground(Qt.lightGray)
                        item.setForeground(Qt.darkGreen)
            elif transaction['credit'] > 0:  # Payments
                for col in [6, 7]:
                    item = self.report_table.item(row, col)
                    if item:
                        item.setBackground(Qt.lightGray)
                        item.setForeground(Qt.darkRed)

    def export_to_excel(self):
        QMessageBox.information(self, "تصدير", "سيتم تنفيذ وظيفة التصدير إلى Excel هنا.")

    def print_report(self):
        QMessageBox.information(self, "طباعة", "سيتم تنفيذ وظيفة الطباعة هنا.")

# دالة لإنشاء النافذة بدون معلمات (للتكامل مع النظام الرئيسي)
def create_cash_movement_report(parent=None):
    return CashMovementReportApp(parent=parent)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CashMovementReportApp()
    window.show()
    sys.exit(app.exec_())
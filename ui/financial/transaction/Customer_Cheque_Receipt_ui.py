import sys
import os
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QMessageBox, QDialog,
                             QGroupBox, QHeaderView, QDateEdit, QDialogButtonBox,
                             QGridLayout)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QDoubleValidator, QPalette, QColor

# --- Project Path and Database Setup ---
project_root = os.getcwd()
DB_PATH = os.path.join(project_root, 'database', 'financials.db')

# --- Reusable Invoice Selection Dialog (No changes needed here) ---
class InvoiceSelectionDialog(QDialog):
    def __init__(self, account_id, db_path, parent=None):
        super().__init__(parent)
        self.account_id = account_id
        self.db_path = db_path
        self.selected_invoices_data = []
        
        self.setWindowTitle("اختر الفواتير المستحقة للتحصيل")
        self.setMinimumSize(900, 500)
        self.setLayoutDirection(Qt.RightToLeft)
        
        layout = QVBoxLayout(self)
        
        self.invoice_table = QTableWidget(columnCount=8)
        self.invoice_table.setHorizontalHeaderLabels(['اختر', 'رقم الفاتورة', 'التاريخ', 'قيمة الفاتورة', 'قيمة مضافة', 'الإجمالي', 'المسدد', 'الرصيد'])
        self.invoice_table.setSelectionMode(QTableWidget.NoSelection)
        layout.addWidget(self.invoice_table)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("موافق")
        buttons.button(QDialogButtonBox.Cancel).setText("إلغاء")
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.load_invoices()

    def load_invoices(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        je.id, je.entry_number, je.entry_date,
                        (SELECT SUM(jel.credit) FROM journal_entry_lines jel WHERE jel.journal_entry_id = je.id AND jel.account_id IN (SELECT id FROM accounts WHERE account_type_id IN (SELECT id FROM account_types WHERE name_en = 'Revenues'))) as base_amount,
                        (SELECT SUM(jel.credit) FROM journal_entry_lines jel WHERE jel.journal_entry_id = je.id AND jel.tax_type_id IS NOT NULL) as vat_amount,
                        je.total_credit as total_amount,
                        (SELECT SUM(credit) FROM journal_entry_lines WHERE contra_account_id = je.id AND account_id = ?) as paid_amount
                    FROM journal_entries je
                    WHERE je.id IN (SELECT journal_entry_id FROM journal_entry_lines WHERE account_id = ? AND debit > 0)
                    GROUP BY je.id
                    HAVING total_amount > IFNULL(paid_amount, 0)
                """, (self.account_id, self.account_id))
                
                invoices = cursor.fetchall()
                self.invoice_table.setRowCount(len(invoices))
                
                for row, inv_data in enumerate(invoices):
                    je_id, inv_num, inv_date, base_amt, vat_amt, total_amt, paid_amt = inv_data
                    balance = (total_amt or 0.0) - (paid_amt or 0.0)
                    
                    chk_box_item = QTableWidgetItem()
                    chk_box_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    chk_box_item.setCheckState(Qt.Unchecked)
                    self.invoice_table.setItem(row, 0, chk_box_item)
                    
                    chk_box_item.setData(Qt.UserRole, {'id': je_id, 'num': inv_num, 'balance': balance, 'vat': (vat_amt or 0.0)})

                    self.invoice_table.setItem(row, 1, QTableWidgetItem(inv_num))
                    self.invoice_table.setItem(row, 2, QTableWidgetItem(inv_date))
                    self.invoice_table.setItem(row, 3, QTableWidgetItem(f"{(base_amt or 0.0):.2f}"))
                    self.invoice_table.setItem(row, 4, QTableWidgetItem(f"{(vat_amt or 0.0):.2f}"))
                    self.invoice_table.setItem(row, 5, QTableWidgetItem(f"{(total_amt or 0.0):.2f}"))
                    self.invoice_table.setItem(row, 6, QTableWidgetItem(f"{(paid_amt or 0.0):.2f}"))
                    self.invoice_table.setItem(row, 7, QTableWidgetItem(f"{balance:.2f}"))

                self.invoice_table.resizeColumnsToContents()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل فواتير العميل: {e}")

    def accept_selection(self):
        for row in range(self.invoice_table.rowCount()):
            if self.invoice_table.item(row, 0).checkState() == Qt.Checked:
                self.selected_invoices_data.append(self.invoice_table.item(row, 0).data(Qt.UserRole))
        self.accept()

# --- Main Application Window (Redesigned) ---
class CustomerChequeReceiptApp(QMainWindow):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.selected_invoices = []
        self.initUI()
        self.load_data()
        self.new_voucher()

    def initUI(self):
        self.setWindowTitle('حافظة تحصيل شيكات العملاء')
        self.setGeometry(100, 100, 1000, 750) # Adjusted size
        self.setLayoutDirection(Qt.RightToLeft)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        
        title_label = QLabel('حافظة تحصيل شيكات العملاء')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 22, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        main_layout.addWidget(title_label)

        # --- Palettes for styling ---
        read_only_palette = QPalette(); read_only_palette.setColor(QPalette.Base, QColor(245, 245, 245))
        total_palette = QPalette(); total_palette.setColor(QPalette.Text, QColor("#27ae60")) # Green color

        # --- Customer and Invoice Selection Group ---
        customer_group = QGroupBox("بيانات العميل والفواتير")
        customer_layout = QGridLayout(customer_group)
        self.general_account = QComboBox()
        self.general_account.currentIndexChanged.connect(self.filter_subsidiary_accounts)
        self.subsidiary_account = QComboBox()
        self.show_invoices_btn = QPushButton("... عرض فواتير العميل المستحقة")
        self.show_invoices_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.show_invoices_btn.clicked.connect(self.show_invoice_dialog)
        customer_layout.addWidget(QLabel("الحساب العام للعملاء:"), 0, 0)
        customer_layout.addWidget(self.general_account, 0, 1)
        customer_layout.addWidget(QLabel("حساب العميل (الدائن):"), 1, 0)
        customer_layout.addWidget(self.subsidiary_account, 1, 1)
        customer_layout.addWidget(self.show_invoices_btn, 2, 0, 1, 2)
        customer_layout.setColumnStretch(1, 1)
        main_layout.addWidget(customer_group)

        # --- Cheque Details Group ---
        cheque_group = QGroupBox("بيانات الشيك المستلم")
        cheque_layout = QGridLayout(cheque_group)
        self.cheque_number = QLineEdit()
        self.cheque_due_date = QDateEdit(QDate.currentDate(), calendarPopup=True, displayFormat="yyyy-MM-dd")
        self.bank_account = QComboBox()
        self.description = QLineEdit()
        cheque_layout.addWidget(QLabel("رقم الشيك:"), 0, 0)
        cheque_layout.addWidget(self.cheque_number, 0, 1)
        cheque_layout.addWidget(QLabel("تاريخ الاستحقاق:"), 0, 2)
        cheque_layout.addWidget(self.cheque_due_date, 0, 3)
        cheque_layout.addWidget(QLabel("حساب البنك للإيداع:"), 1, 0)
        cheque_layout.addWidget(self.bank_account, 1, 1, 1, 3)
        cheque_layout.addWidget(QLabel("البيان:"), 2, 0)
        cheque_layout.addWidget(self.description, 2, 1, 1, 3)
        main_layout.addWidget(cheque_group)

        # --- Totals and Summary Group ---
        summary_group = QGroupBox("ملخص التحصيل")
        summary_layout = QGridLayout(summary_group)
        self.voucher_number = QLineEdit(readOnly=True, palette=read_only_palette)
        self.voucher_date = QDateEdit(QDate.currentDate(), calendarPopup=True, displayFormat="yyyy-MM-dd")
        self.total_invoices_amount = QLineEdit(readOnly=True, palette=read_only_palette)
        self.total_vat_amount = QLineEdit(readOnly=True, palette=read_only_palette)
        self.cheque_net_amount = QLineEdit(readOnly=True, palette=read_only_palette, font=QFont("Arial", 14, QFont.Bold))
        self.cheque_net_amount.setPalette(total_palette)
        summary_layout.addWidget(QLabel("رقم الحافظة:"), 0, 0); summary_layout.addWidget(self.voucher_number, 0, 1)
        summary_layout.addWidget(QLabel("تاريخ التحرير:"), 0, 2); summary_layout.addWidget(self.voucher_date, 0, 3)
        summary_layout.addWidget(QLabel("إجمالي الفواتير:"), 1, 0); summary_layout.addWidget(self.total_invoices_amount, 1, 1)
        summary_layout.addWidget(QLabel("إجمالي ق.م:"), 1, 2); summary_layout.addWidget(self.total_vat_amount, 1, 3)
        summary_layout.addWidget(QLabel("صافي قيمة الشيك:"), 2, 0); summary_layout.addWidget(self.cheque_net_amount, 2, 1, 1, 3)
        main_layout.addWidget(summary_group)
        
        # --- Action Buttons ---
        button_layout = QHBoxLayout()
        buttons = {'new_btn': ('جديد', self.new_voucher), 'save_btn': ('حفظ', self.save_voucher)}
        for name, (text, func) in buttons.items():
            btn = QPushButton(text); btn.setFont(QFont("Arial", 12, QFont.Bold)); btn.setMinimumHeight(40)
            setattr(self, name, btn); button_layout.addWidget(btn)
        main_layout.addLayout(button_layout)
        
        main_layout.addStretch() # Pushes everything up

    def load_data(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                self.bank_account.clear()
                cursor.execute("SELECT b.id, a.acc_code, a.account_name_ar FROM bank_accounts b JOIN accounts a ON b.account_id = a.id WHERE b.is_active = 1")
                for bank_id, code, name in cursor.fetchall(): self.bank_account.addItem(f"{code} - {name}", bank_id)
                
                self.general_account.clear(); self.general_account.addItem("--- اختر الحساب العام ---", None)
                cursor.execute("SELECT id, acc_code, account_name_ar FROM accounts WHERE is_final = 0 AND is_active = 1 AND acc_code LIKE '121%' ORDER BY acc_code") # Assuming customers start with 121
                for acc_id, code, name in cursor.fetchall(): self.general_account.addItem(f"{code} - {name}", acc_id)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل البيانات: {e}")

    def filter_subsidiary_accounts(self):
        parent_id = self.general_account.currentData()
        self.subsidiary_account.clear()
        if parent_id is None: return
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, acc_code, account_name_ar FROM accounts WHERE parent_account_id = ? AND is_final = 1 ORDER BY acc_code", (parent_id,))
                for acc_id, code, name in cursor.fetchall(): self.subsidiary_account.addItem(f"{code} - {name}", acc_id)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في فلترة الحسابات: {e}")

    def show_invoice_dialog(self):
        account_id = self.subsidiary_account.currentData()
        if not account_id:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار حساب العميل أولاً.")
            return
        
        dialog = InvoiceSelectionDialog(account_id, self.db_path, self)
        if dialog.exec_() == QDialog.Accepted:
            self.selected_invoices = dialog.selected_invoices_data
            if self.selected_invoices:
                total_balance = sum(inv['balance'] for inv in self.selected_invoices)
                total_vat = sum(inv['vat'] for inv in self.selected_invoices)
                invoice_numbers = ", ".join(inv['num'] for inv in self.selected_invoices)
                
                self.total_invoices_amount.setText(f"{total_balance:.2f}")
                self.total_vat_amount.setText(f"{total_vat:.2f}")
                self.cheque_net_amount.setText(f"{total_balance:.2f}")
                self.description.setText(f"تحصيل قيمة الفواتير: {invoice_numbers}")

    def new_voucher(self):
        self.voucher_number.setText(f"CRV-{datetime.now().year}-{datetime.now().strftime('%m%d%H%M%S')}")
        self.voucher_date.setDate(QDate.currentDate())
        self.cheque_due_date.setDate(QDate.currentDate())
        for w in [self.cheque_number, self.total_invoices_amount, self.total_vat_amount, 
                  self.cheque_net_amount, self.description]: w.clear()
        for c in [self.bank_account, self.general_account, self.subsidiary_account]: c.setCurrentIndex(0)
        self.selected_invoices = []

    def save_voucher(self):
        if not self.validate_form(): return
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                self.create_journal_entry(cursor)
                # Here you would also save the cheque details to a `customer_cheques` table
                conn.commit()
                QMessageBox.information(self, "نجاح", "تم حفظ حافظة تحصيل الشيك بنجاح.")
                self.new_voucher()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "خطأ", f"فشل حفظ الحافظة: {e}")

    def create_journal_entry(self, cursor):
        cursor.execute("SELECT id FROM financial_years WHERE is_active = 1 AND is_closed = 0")
        financial_year = cursor.fetchone()
        if not financial_year: raise Exception("لا توجد سنة مالية نشطة.")
        
        credit_acc_id = self.subsidiary_account.currentData()
        cursor.execute("SELECT account_id FROM bank_accounts WHERE id = ?", (self.bank_account.currentData(),))
        debit_bank_acc_id = cursor.fetchone()[0]
        
        net_cheque = float(self.cheque_net_amount.text())
        
        entry_number = f"JV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cursor.execute("INSERT INTO journal_entries (entry_number, entry_date, financial_year_id, description, total_debit, total_credit, status) VALUES (?, ?, ?, ?, ?, ?, 'مؤكد')",
                       (self.voucher_date.date().toString("yyyy-MM-dd"), financial_year[0], self.description.text(), net_cheque, net_cheque))
        journal_entry_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO journal_entry_lines (journal_entry_id, account_id, debit, credit, notes) VALUES (?, ?, ?, 0, ?)",
                       (journal_entry_id, debit_bank_acc_id, net_cheque, f"تحصيل شيك رقم: {self.cheque_number.text()}"))

        for inv in self.selected_invoices:
             cursor.execute("INSERT INTO journal_entry_lines (journal_entry_id, account_id, debit, credit, notes, contra_account_id) VALUES (?, ?, 0, ?, ?, ?)",
                           (journal_entry_id, credit_acc_id, inv['balance'], f"تحصيل فاتورة {inv['num']}", inv['id']))

    def validate_form(self):
        if not self.cheque_number.text().strip():
            QMessageBox.warning(self, "بيانات ناقصة", "يرجى إدخال رقم الشيك."); return False
        if not self.selected_invoices:
            QMessageBox.warning(self, "بيانات ناقصة", "يرجى اختيار فاتورة واحدة على الأقل للتحصيل."); return False
        return True

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion') # Recommended for a modern look
    window = CustomerChequeReceiptApp(DB_PATH)
    window.show()
    sys.exit(app.exec_())

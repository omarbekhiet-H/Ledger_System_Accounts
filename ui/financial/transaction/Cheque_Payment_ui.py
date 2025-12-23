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

# --- Reusable Invoice Selection Dialog (No changes needed) ---
class InvoiceSelectionDialog(QDialog):
    def __init__(self, account_id, db_path, parent=None):
        super().__init__(parent)
        self.account_id = account_id
        self.db_path = db_path
        self.selected_invoices_data = []
        
        self.setWindowTitle("اختر الفواتير المستحقة للدفع")
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
                        (SELECT SUM(jel.debit) FROM journal_entry_lines jel WHERE jel.journal_entry_id = je.id AND jel.account_id IN (SELECT id FROM accounts WHERE account_type_id IN (SELECT id FROM account_types WHERE name_en = 'Expenses'))) as base_amount,
                        (SELECT SUM(jel.debit) FROM journal_entry_lines jel WHERE jel.journal_entry_id = je.id AND jel.tax_type_id IS NOT NULL) as vat_amount,
                        je.total_debit as total_amount,
                        (SELECT SUM(debit) FROM journal_entry_lines WHERE contra_account_id = je.id AND account_id = ?) as paid_amount
                    FROM journal_entries je
                    WHERE je.id IN (SELECT journal_entry_id FROM journal_entry_lines WHERE account_id = ? AND credit > 0)
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
            QMessageBox.critical(self, "خطأ", f"فشل تحميل فواتير المورد: {e}")

    def accept_selection(self):
        for row in range(self.invoice_table.rowCount()):
            if self.invoice_table.item(row, 0).checkState() == Qt.Checked:
                self.selected_invoices_data.append(self.invoice_table.item(row, 0).data(Qt.UserRole))
        self.accept()

# --- Main Application Window (Redesigned) ---
class ChequePaymentVoucherApp(QMainWindow):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.selected_invoices = []
        self.initUI()
        self.load_data()
        self.new_voucher()

    def initUI(self):
        self.setWindowTitle('حافظة صرف الشيكات')
        self.setGeometry(100, 100, 1000, 750)
        self.setLayoutDirection(Qt.RightToLeft)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        
        title_label = QLabel('حافظة صرف الشيكات')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 22, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        main_layout.addWidget(title_label)

        read_only_palette = QPalette(); read_only_palette.setColor(QPalette.Base, QColor(245, 245, 245))
        total_palette = QPalette(); total_palette.setColor(QPalette.Text, QColor("#c0392b")) # Red color for payments

        # --- Vendor and Invoice Selection Group ---
        vendor_group = QGroupBox("بيانات المورد والفواتير")
        vendor_layout = QGridLayout(vendor_group)
        self.general_account = QComboBox()
        self.general_account.currentIndexChanged.connect(self.filter_subsidiary_accounts)
        self.subsidiary_account = QComboBox()
        self.show_invoices_btn = QPushButton("... عرض فواتير المورد المستحقة")
        self.show_invoices_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.show_invoices_btn.clicked.connect(self.show_invoice_dialog)
        vendor_layout.addWidget(QLabel("الحساب العام للموردين:"), 0, 0)
        vendor_layout.addWidget(self.general_account, 0, 1)
        vendor_layout.addWidget(QLabel("حساب المورد (المدين):"), 1, 0)
        vendor_layout.addWidget(self.subsidiary_account, 1, 1)
        vendor_layout.addWidget(self.show_invoices_btn, 2, 0, 1, 2)
        vendor_layout.setColumnStretch(1, 1)
        main_layout.addWidget(vendor_group)

        # --- Cheque Details Group ---
        cheque_group = QGroupBox("بيانات الشيك الصادر")
        cheque_layout = QGridLayout(cheque_group)
        self.cheque_number = QLineEdit()
        self.cheque_due_date = QDateEdit(QDate.currentDate(), calendarPopup=True, displayFormat="yyyy-MM-dd")
        self.bank_account = QComboBox()
        self.description = QLineEdit()
        cheque_layout.addWidget(QLabel("رقم الشيك:"), 0, 0)
        cheque_layout.addWidget(self.cheque_number, 0, 1)
        cheque_layout.addWidget(QLabel("تاريخ الاستحقاق:"), 0, 2)
        cheque_layout.addWidget(self.cheque_due_date, 0, 3)
        cheque_layout.addWidget(QLabel("حساب البنك للسحب:"), 1, 0)
        cheque_layout.addWidget(self.bank_account, 1, 1, 1, 3)
        cheque_layout.addWidget(QLabel("البيان:"), 2, 0)
        cheque_layout.addWidget(self.description, 2, 1, 1, 3)
        main_layout.addWidget(cheque_group)

        # --- Totals and Summary Group ---
        summary_group = QGroupBox("ملخص الدفع والضرائب")
        summary_layout = QGridLayout(summary_group)
        self.voucher_number = QLineEdit(readOnly=True, palette=read_only_palette)
        self.voucher_date = QDateEdit(QDate.currentDate(), calendarPopup=True, displayFormat="yyyy-MM-dd")
        self.total_invoices_amount = QLineEdit(readOnly=True, palette=read_only_palette)
        self.wht_tax_type = QComboBox(); self.wht_tax_type.currentIndexChanged.connect(self.calculate_final_cheque)
        self.wht_tax_value = QLineEdit(readOnly=True, palette=read_only_palette)
        self.cheque_net_amount = QLineEdit(readOnly=True, palette=read_only_palette, font=QFont("Arial", 14, QFont.Bold))
        self.cheque_net_amount.setPalette(total_palette)
        summary_layout.addWidget(QLabel("رقم الحافظة:"), 0, 0); summary_layout.addWidget(self.voucher_number, 0, 1)
        summary_layout.addWidget(QLabel("تاريخ التحرير:"), 0, 2); summary_layout.addWidget(self.voucher_date, 0, 3)
        summary_layout.addWidget(QLabel("إجمالي الفواتير:"), 1, 0); summary_layout.addWidget(self.total_invoices_amount, 1, 1)
        summary_layout.addWidget(QLabel("ضريبة الخصم:"), 1, 2); summary_layout.addWidget(self.wht_tax_type, 1, 3)
        summary_layout.addWidget(QLabel("قيمة ضريبة الخصم:"), 2, 2); summary_layout.addWidget(self.wht_tax_value, 2, 3)
        summary_layout.addWidget(QLabel("صافي قيمة الشيك:"), 3, 0); summary_layout.addWidget(self.cheque_net_amount, 3, 1, 1, 3)
        main_layout.addWidget(summary_group)
        
        button_layout = QHBoxLayout()
        buttons = {'new_btn': ('جديد', self.new_voucher), 'save_btn': ('حفظ', self.save_voucher)}
        for name, (text, func) in buttons.items():
            btn = QPushButton(text); btn.setFont(QFont("Arial", 12, QFont.Bold)); btn.setMinimumHeight(40)
            setattr(self, name, btn); button_layout.addWidget(btn)
        main_layout.addLayout(button_layout)
        
        main_layout.addStretch()

    def load_data(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                self.bank_account.clear()
                cursor.execute("SELECT b.id, a.acc_code, a.account_name_ar FROM bank_accounts b JOIN accounts a ON b.account_id = a.id WHERE b.is_active = 1")
                for bank_id, code, name in cursor.fetchall(): self.bank_account.addItem(f"{code} - {name}", bank_id)
                
                self.general_account.clear(); self.general_account.addItem("--- اختر الحساب العام ---", None)
                cursor.execute("SELECT id, acc_code, account_name_ar FROM accounts WHERE is_final = 0 AND is_active = 1 AND acc_code LIKE '211%' ORDER BY acc_code") # Assuming vendors start with 211
                for acc_id, code, name in cursor.fetchall(): self.general_account.addItem(f"{code} - {name}", acc_id)

                self.wht_tax_type.clear(); self.wht_tax_type.addItem("--- بدون ضريبة خصم ---", 0.0)
                cursor.execute("SELECT name_ar, rate FROM tax_types WHERE is_active = 1")
                for name, rate in cursor.fetchall(): self.wht_tax_type.addItem(f"{name} ({rate}%)", rate)
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
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار حساب المورد أولاً.")
            return
        
        dialog = InvoiceSelectionDialog(account_id, self.db_path, self)
        if dialog.exec_() == QDialog.Accepted:
            self.selected_invoices = dialog.selected_invoices_data
            if self.selected_invoices:
                total_balance = sum(inv['balance'] for inv in self.selected_invoices)
                invoice_numbers = ", ".join(inv['num'] for inv in self.selected_invoices)
                
                self.total_invoices_amount.setText(f"{total_balance:.2f}")
                self.description.setText(f"سداد قيمة الفواتير: {invoice_numbers}")
                self.calculate_final_cheque()

    def calculate_final_cheque(self):
        try:
            total_inv_amt = float(self.total_invoices_amount.text())
        except (ValueError, TypeError):
            total_inv_amt = 0.0
        
        wht_rate = self.wht_tax_type.currentData() or 0.0
        wht_value = total_inv_amt * (wht_rate / 100.0)
        net_cheque = total_inv_amt - wht_value
        
        self.wht_tax_value.setText(f"{wht_value:.2f}")
        self.cheque_net_amount.setText(f"{net_cheque:.2f}")

    def new_voucher(self):
        self.voucher_number.setText(f"CPV-{datetime.now().year}-{datetime.now().strftime('%m%d%H%M%S')}")
        self.voucher_date.setDate(QDate.currentDate())
        self.cheque_due_date.setDate(QDate.currentDate())
        for w in [self.cheque_number, self.total_invoices_amount, self.wht_tax_value, 
                  self.cheque_net_amount, self.description]: w.clear()
        for c in [self.bank_account, self.general_account, self.subsidiary_account, self.wht_tax_type]: c.setCurrentIndex(0)
        self.selected_invoices = []

    def save_voucher(self):
        if not self.validate_form(): return
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                self.create_journal_entry(cursor)
                conn.commit()
                QMessageBox.information(self, "نجاح", "تم حفظ حافظة صرف الشيك بنجاح.")
                self.new_voucher()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "خطأ", f"فشل حفظ الحافظة: {e}")

    def create_journal_entry(self, cursor):
        cursor.execute("SELECT id FROM financial_years WHERE is_active = 1 AND is_closed = 0")
        financial_year = cursor.fetchone()
        if not financial_year: raise Exception("لا توجد سنة مالية نشطة.")
        
        debit_acc_id = self.subsidiary_account.currentData()
        cursor.execute("SELECT account_id FROM bank_accounts WHERE id = ?", (self.bank_account.currentData(),))
        credit_bank_acc_id = cursor.fetchone()[0]
        
        wht_rate = self.wht_tax_type.currentData() or 0.0
        credit_wht_acc_id = None
        if wht_rate > 0:
            cursor.execute("SELECT tax_account_id FROM tax_types WHERE rate = ?", (wht_rate,))
            res = cursor.fetchone()
            if not res or not res[0]: raise Exception("لم يتم العثور على حساب لضريبة الخصم المحددة.")
            credit_wht_acc_id = res[0]

        total_payment = float(self.total_invoices_amount.text())
        wht_value = float(self.wht_tax_value.text())
        net_cheque = float(self.cheque_net_amount.text())
        
        entry_number = f"JV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cursor.execute("INSERT INTO journal_entries (entry_number, entry_date, financial_year_id, description, total_debit, total_credit, status) VALUES (?, ?, ?, ?, ?, ?, 'مؤكد')",
                       (self.voucher_date.date().toString("yyyy-MM-dd"), financial_year[0], self.description.text(), total_payment, total_payment))
        journal_entry_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO journal_entry_lines (journal_entry_id, account_id, debit, credit, notes) VALUES (?, ?, ?, 0, ?)",
                       (journal_entry_id, debit_acc_id, total_payment, self.description.text()))

        if wht_value > 0 and credit_wht_acc_id:
            cursor.execute("INSERT INTO journal_entry_lines (journal_entry_id, account_id, debit, credit, notes) VALUES (?, ?, 0, ?, ?)",
                           (journal_entry_id, credit_wht_acc_id, wht_value, "ضريبة خصم ومنبع"))

        cursor.execute("INSERT INTO journal_entry_lines (journal_entry_id, account_id, debit, credit, notes) VALUES (?, ?, 0, ?, ?)",
                       (journal_entry_id, credit_bank_acc_id, net_cheque, f"قيمة شيك رقم: {self.cheque_number.text()}"))
        
        # Link payment to invoices
        for inv in self.selected_invoices:
            cursor.execute("INSERT INTO journal_entry_lines (journal_entry_id, account_id, debit, credit, notes, contra_account_id) VALUES (?, ?, ?, 0, ?, ?)",
                           (journal_entry_id, debit_acc_id, 0, 0, f"تسوية فاتورة {inv['num']}", inv['id']))


    def validate_form(self):
        if not self.cheque_number.text().strip():
            QMessageBox.warning(self, "بيانات ناقصة", "يرجى إدخال رقم الشيك."); return False
        if not self.selected_invoices:
            QMessageBox.warning(self, "بيانات ناقصة", "يرجى اختيار فاتورة واحدة على الأقل للدفع."); return False
        return True

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ChequePaymentVoucherApp(DB_PATH)
    window.show()
    sys.exit(app.exec_())

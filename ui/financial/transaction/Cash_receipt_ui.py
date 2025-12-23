import sys
import os
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QMessageBox, QDialog,
                             QGroupBox, QHeaderView, QDateEdit, QDialogButtonBox,
                             QGridLayout, QCompleter)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QDoubleValidator, QPalette, QColor

# --- Project Path and Database Setup ---
project_root = os.getcwd()
DB_PATH = os.path.join(project_root, 'database', 'financials.db')

# --- Reusable Journal Viewer Dialog ---
class JournalEntryViewer(QDialog):
    def __init__(self, journal_entry_id, db_path, parent=None):
        super().__init__(parent)
        self.journal_entry_id = journal_entry_id
        self.db_path = db_path
        self.setWindowTitle("عرض القيد المحاسبي")
        self.setMinimumSize(700, 350)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.load_entry_details()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        header_group = QGroupBox("بيانات القيد الأساسية")
        header_layout = QGridLayout(header_group)
        self.entry_number_value = QLabel("...")
        self.entry_date_value = QLabel("...")
        self.description_value = QLabel("...")
        self.transaction_type_value = QLabel("...")
        
        header_layout.addWidget(QLabel("<b>رقم القيد:</b>"), 0, 0); header_layout.addWidget(self.entry_number_value, 0, 1)
        header_layout.addWidget(QLabel("<b>التاريخ:</b>"), 0, 2); header_layout.addWidget(self.entry_date_value, 0, 3)
        header_layout.addWidget(QLabel("<b>نوع الحركة:</b>"), 1, 0); header_layout.addWidget(self.transaction_type_value, 1, 1)
        header_layout.addWidget(QLabel("<b>البيان:</b>"), 1, 2); header_layout.addWidget(self.description_value, 1, 3)
        layout.addWidget(header_group)
        
        self.lines_table = QTableWidget(columnCount=9)
        self.lines_table.setHorizontalHeaderLabels([
            'كود الحساب', 'اسم الحساب', 'مدين', 'دائن', 'البيان',
            'نوع المستند', 'رقم المستند', 'نوع الضريبة', 'مركز التكلفة'
        ])
        self.lines_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.lines_table)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.button(QDialogButtonBox.Ok).setText("موافق")
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def load_entry_details(self):
        try:
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                conn.execute("PRAGMA foreign_keys=ON;")
                conn.execute("PRAGMA journal_mode=WAL;")
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT je.entry_number, je.entry_date, je.description, tt.name_ar
                    FROM journal_entries je 
                    LEFT JOIN transaction_types tt ON je.transaction_type_id = tt.id
                    WHERE je.id = ?
                """, (self.journal_entry_id,))
                entry = cursor.fetchone()
                if entry:
                    self.entry_number_value.setText(str(entry[0] or ""))
                    self.entry_date_value.setText(str(entry[1] or ""))
                    self.description_value.setText(str(entry[2] or ""))
                    self.transaction_type_value.setText(entry[3] if entry[3] else "بدون")
                
                cursor.execute("""
                   SELECT a.acc_code, a.account_name_ar, jel.debit, jel.credit, jel.notes,
                        dt.name_ar AS doc_type, jel.document_number,
                        ttypes.name_ar AS tax_type, cc.name_ar AS cost_center
                    FROM journal_entry_lines jel 
                    JOIN accounts a ON jel.account_id = a.id
                    LEFT JOIN document_types dt ON jel.document_type_id = dt.id
                    LEFT JOIN tax_types ttypes ON jel.tax_type_id = ttypes.id
                    LEFT JOIN cost_centers cc ON jel.cost_center_id = cc.id
                    WHERE jel.journal_entry_id = ? 
                    ORDER BY COALESCE(jel.debit,0) DESC, COALESCE(jel.credit,0) DESC
                """, (self.journal_entry_id,))
                lines = cursor.fetchall()
                self.lines_table.setRowCount(len(lines))
                for row, line_data in enumerate(lines):
                    for col, value in enumerate(line_data):
                        self.lines_table.setItem(row, col, QTableWidgetItem(str(value) if value is not None else ""))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"لا يمكن تحميل تفاصيل القيد: {e}")

# --- Cash Receipt Voucher App (متحصلات) ---
class CashReceiptVoucherApp(QMainWindow):
    def __init__(self, db_path=None):
        super().__init__()
        if db_path is None:
            db_path = DB_PATH
        self.db_path = db_path
        self.current_voucher_id = None
        self.additional_deductions = []
        if not os.path.exists(self.db_path):
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"ملف قاعدة البيانات غير موجود في المسار:\n{self.db_path}")
            sys.exit(1)

        try:
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA foreign_keys=ON;")
        except Exception as e:
            print(f"Could not set PRAGMA: {e}")

        self.initUI()
        self.set_focus_order()
        self.load_data()
        self.new_voucher()

    def initUI(self):
        self.setWindowTitle('نظام إيصالات المتحصلات النقدية')
        self.setGeometry(100, 100, 1200, 900)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet("background-color: #E6F2FF;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        title_label = QLabel('إيصالات المتحصلات النقدية')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        main_layout.addWidget(title_label)

        self.read_only_palette = QPalette()
        self.read_only_palette.setColor(QPalette.Base, QColor(240, 240, 240))

        # ---- Basic info ----
        basic_info_group = QGroupBox("البيانات الأساسية")
        basic_layout = QGridLayout(basic_info_group)
        self.voucher_number = QLineEdit(readOnly=True); self.voucher_number.setPalette(self.read_only_palette)
        self.voucher_date = QDateEdit(QDate.currentDate(), calendarPopup=True, displayFormat="yyyy-MM-dd")
        self.cash_chests = QComboBox()
        self.document_type = QComboBox()
        self.document_number = QLineEdit()
        self.transaction_type = QComboBox()

        basic_layout.addWidget(QLabel("رقم الإيصال:"), 0, 0); basic_layout.addWidget(self.voucher_number, 0, 1)
        basic_layout.addWidget(QLabel("التاريخ:"), 0, 2); basic_layout.addWidget(self.voucher_date, 0, 3)
        basic_layout.addWidget(QLabel("حساب الصندوق (المدين):"), 0, 4); basic_layout.addWidget(self.cash_chests, 0, 5)
        basic_layout.addWidget(QLabel("نوع المستند:"), 1, 0); basic_layout.addWidget(self.document_type, 1, 1)
        basic_layout.addWidget(QLabel("رقم المستند:"), 1, 2); basic_layout.addWidget(self.document_number, 1, 3)
        basic_layout.addWidget(QLabel("نوع الحركة:"), 1, 4); basic_layout.addWidget(self.transaction_type, 1, 5)

        main_layout.addWidget(basic_info_group)

        # ---- Transaction details ----
        transaction_group = QGroupBox("تفاصيل المعاملة")
        trans_layout = QGridLayout(transaction_group)
        self.general_account = QComboBox(); self.general_account.currentIndexChanged.connect(self.filter_subsidiary_accounts)
        self.subsidiary_account = QComboBox(); self.subsidiary_account.currentIndexChanged.connect(self.on_subsidiary_account_change)
        self.account_code_input = QLineEdit(readOnly=True); self.account_code_input.setPalette(self.read_only_palette)
        self.account_code_search = QLineEdit(); self.account_code_search.setPlaceholderText("اكتب كود واضغط Enter")
        self.account_code_search.returnPressed.connect(self.find_account_by_code)

        self.description = QLineEdit()
        self.cost_center = QComboBox()
        self.tax_type = QComboBox(); self.tax_type.currentIndexChanged.connect(self.update_calculations)
        self.total_amount = QLineEdit(); self.total_amount.setValidator(QDoubleValidator(0, 999999999.99, 2)); self.total_amount.textChanged.connect(self.update_calculations)
        self.tax_value = QLineEdit(readOnly=True); self.tax_value.setPalette(self.read_only_palette)
        self.net_amount = QLineEdit(readOnly=True); self.net_amount.setPalette(self.read_only_palette)

        trans_layout.addWidget(QLabel("بحث بالكود:"), 0, 0); trans_layout.addWidget(self.account_code_search, 0, 1)
        trans_layout.addWidget(QLabel("الحساب العام:"), 0, 2); trans_layout.addWidget(self.general_account, 0, 3)
        trans_layout.addWidget(QLabel("الحساب المساعد (الدائن):"), 0, 4); trans_layout.addWidget(self.subsidiary_account, 0, 5)
        trans_layout.addWidget(QLabel("نوع الضريبة:"), 1, 0); trans_layout.addWidget(self.tax_type, 1, 1)
        trans_layout.addWidget(QLabel("مركز التكلفة:"), 1, 2); trans_layout.addWidget(self.cost_center, 1, 3)
        trans_layout.addWidget(QLabel("<b>المبلغ الإجمالي:</b>"), 2, 0); trans_layout.addWidget(self.total_amount, 2, 1)
        trans_layout.addWidget(QLabel("قيمة الضريبة:"), 2, 2); trans_layout.addWidget(self.tax_value, 2, 3)
        trans_layout.addWidget(QLabel("<b>الصافي (للحساب الدائن):</b>"), 2, 4); trans_layout.addWidget(self.net_amount, 2, 5)
        trans_layout.addWidget(QLabel("البيان:"), 3, 0); trans_layout.addWidget(self.description, 3, 1, 1, 5)

        main_layout.addWidget(transaction_group)

        # ---- Deductions ----
        deductions_group = QGroupBox("الخصومات الإضافية")
        deductions_layout = QGridLayout(deductions_group)
        self.deduction_account = QComboBox()
        self.deduction_account.setEditable(True)
        self.deduction_account.setInsertPolicy(QComboBox.NoInsert)
        completer = QCompleter(self.deduction_account.model(), self)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.deduction_account.setCompleter(completer)
        self.deduction_amount = QLineEdit(); self.deduction_amount.setValidator(QDoubleValidator(0, 999999999.99, 2))
        self.add_deduction_btn = QPushButton("إضافة خصم")
        self.add_deduction_btn.clicked.connect(self.add_deduction)
        deductions_layout.addWidget(QLabel("حساب الخصم:"), 0, 0); deductions_layout.addWidget(self.deduction_account, 0, 1)
        deductions_layout.addWidget(QLabel("مبلغ الخصم:"), 0, 2); deductions_layout.addWidget(self.deduction_amount, 0, 3)
        deductions_layout.addWidget(self.add_deduction_btn, 0, 4)

        self.deductions_table = QTableWidget(columnCount=4)
        self.deductions_table.setHorizontalHeaderLabels(['ID الحساب', 'اسم حساب الخصم', 'المبلغ', 'حذف'])
        self.deductions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.deductions_table.setColumnHidden(0, True)
        deductions_layout.addWidget(self.deductions_table, 1, 0, 1, 5)
        main_layout.addWidget(deductions_group)

        # ---- Buttons ----
        button_layout = QHBoxLayout()
        buttons = {
            'new_btn': ('جديد', self.new_voucher),
            'save_btn': ('حفظ', self.save_voucher),
            'edit_btn': ('تعديل', self.edit_voucher),
            'delete_btn': ('حذف', self.delete_voucher)
        }
        for name, (text, func) in buttons.items():
            btn = QPushButton(text); btn.setFont(QFont("Arial", 10, QFont.Bold)); btn.setMinimumHeight(35)
            btn.clicked.connect(func); setattr(self, name, btn); button_layout.addWidget(btn)
        main_layout.addLayout(button_layout)

        # ---- Vouchers table ----
        self.voucher_table = QTableWidget(columnCount=12)
        self.voucher_table.setHorizontalHeaderLabels([
            'ID', 'رقم الإيصال', 'التاريخ', 'الصندوق', 'الحساب الدائن',
            'المبلغ', 'نوع المستند', 'رقم المستند', 'نوع الحركة', 'رقم القيد', 'عرض القيد', 'تحديد'
        ])
        self.voucher_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.voucher_table.setColumnHidden(0, True)
        main_layout.addWidget(self.voucher_table)

    def set_focus_order(self):
        widgets = [
            self.voucher_date, self.cash_chests, self.document_type, self.document_number,
            self.transaction_type, self.account_code_search, self.general_account,
            self.subsidiary_account, self.description, self.tax_type, self.cost_center,
            self.total_amount, self.deduction_account, self.deduction_amount, self.add_deduction_btn
        ]
        for i in range(len(widgets) - 1):
            self.setTabOrder(widgets[i], widgets[i+1])
        self.setTabOrder(widgets[-1], self.save_btn)
        for widget in widgets:
            widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if obj is self.account_code_search:
                self.find_account_by_code()
                return True
            if isinstance(obj, QComboBox) and obj.isEditable():
                return False
            elif obj is not self.total_amount:
                self.focusNextChild()
            else:
                self.save_btn.setFocus()
            return True
        return super().eventFilter(obj, event)

    def update_calculations(self):
        try:
            total = float(self.total_amount.text())
        except (ValueError, TypeError):
            total = 0.0

        tax_id = self.tax_type.currentData()
        tax_amount = 0.0
        
        if tax_id:
            try:
                with sqlite3.connect(self.db_path, timeout=20) as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT rate FROM tax_types WHERE id=?", (tax_id,))
                    r = cur.fetchone()
                    if r:
                        tax_amount = total * (r[0] / 100.0)
            except sqlite3.Error:
                tax_amount = 0.0
        
        total_deductions = sum(item['amount'] for item in self.additional_deductions)
        net = total - tax_amount - total_deductions

        self.tax_value.setText(f"{tax_amount:.2f}")
        self.net_amount.setText(f"{net:.2f}")

    def load_data(self):
        try:
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                cursor = conn.cursor()

                self.document_type.clear()
                self.document_type.addItem("--- اختر نوع المستند ---", None)
                cursor.execute("SELECT id, code, name_ar FROM document_types WHERE is_active = 1 ORDER BY code")
                for doc_id, code, name in cursor.fetchall():
                    self.document_type.addItem(f"{code} - {name}", doc_id)

                self.transaction_type.clear()
                self.transaction_type.addItem("--- اختر نوع الحركة ---", None)
                cursor.execute("SELECT id, code, name_ar FROM transaction_types WHERE is_active = 1 ORDER BY code")
                for trans_id, code, name in cursor.fetchall():
                    self.transaction_type.addItem(f"{code} - {name}", trans_id)

                self.cash_chests.clear()
                cursor.execute("SELECT c.id, a.acc_code, a.account_name_ar FROM cash_chests c JOIN accounts a ON c.account_id = a.id WHERE c.is_active = 1 AND a.is_active = 1")
                for chest_id, code, name in cursor.fetchall():
                    self.cash_chests.addItem(f"{code} - {name}", chest_id)

                self.general_account.blockSignals(True)
                self.general_account.clear(); self.general_account.addItem("--- اختر الحساب العام ---", None)
                cursor.execute("SELECT id, acc_code, account_name_ar FROM accounts WHERE is_final = 0 AND is_active = 1 ORDER BY acc_code")
                for acc_id, code, name in cursor.fetchall():
                    self.general_account.addItem(f"{code} - {name}", acc_id)
                self.general_account.blockSignals(False)
                self.filter_subsidiary_accounts()

                self.cost_center.clear(); self.cost_center.addItem("--- بدون مركز تكلفة ---", None)
                cursor.execute("SELECT id, code, name_ar FROM cost_centers WHERE is_active = 1")
                for cc_id, code, name in cursor.fetchall():
                    self.cost_center.addItem(f"{code} - {name}", cc_id)

                self.tax_type.clear(); self.tax_type.addItem("--- بدون ضريبة ---", None)
                cursor.execute("SELECT id, name_ar, rate FROM tax_types WHERE is_active = 1")
                for tax_id, name, rate in cursor.fetchall():
                    self.tax_type.addItem(f"{name} ({rate}%)", tax_id)

                self.deduction_account.clear(); self.deduction_account.addItem("", None)
                cursor.execute("SELECT id, acc_code, account_name_ar FROM accounts WHERE is_final = 1 AND is_active = 1 ORDER BY acc_code")
                for acc_id, code, name in cursor.fetchall():
                    self.deduction_account.addItem(f"{code} - {name}", acc_id)

            self.load_vouchers()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل البيانات: {e}")

    def add_deduction(self):
        account_id = self.deduction_account.currentData()
        account_name = self.deduction_account.currentText()
        try:
            amount = float(self.deduction_amount.text())
        except (ValueError, TypeError):
            amount = 0.0

        if not account_id:
            QMessageBox.warning(self, "خطأ", "يرجى اختيار حساب خصم صحيح.")
            return
        if amount <= 0:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال مبلغ خصم صحيح.")
            return

        if any(d['account_id'] == account_id for d in self.additional_deductions):
            QMessageBox.warning(self, "مكرر", "هذا الحساب تم إضافته بالفعل كخصم.")
            return

        self.additional_deductions.append({'account_id': account_id, 'account_name': account_name, 'amount': amount})
        self.update_deductions_table()
        self.update_calculations()

        self.deduction_account.setCurrentIndex(0)
        self.deduction_amount.clear()

    def update_deductions_table(self):
        self.deductions_table.setRowCount(len(self.additional_deductions))
        for row, item in enumerate(self.additional_deductions):
            self.deductions_table.setItem(row, 0, QTableWidgetItem(str(item['account_id'])))
            self.deductions_table.setItem(row, 1, QTableWidgetItem(item['account_name']))
            self.deductions_table.setItem(row, 2, QTableWidgetItem(f"{item['amount']:.2f}"))
            delete_btn = QPushButton("حذف")
            delete_btn.clicked.connect(lambda ch, r=row: self.delete_deduction(r))
            self.deductions_table.setCellWidget(row, 3, delete_btn)

    def delete_deduction(self, row_index):
        if 0 <= row_index < len(self.additional_deductions):
            del self.additional_deductions[row_index]
            self.update_deductions_table()
            self.update_calculations()

    def filter_subsidiary_accounts(self):
        parent_id = self.general_account.currentData()
        self.subsidiary_account.blockSignals(True)
        self.subsidiary_account.clear()
        self.subsidiary_account.addItem("--- اختر الحساب المساعد ---", None)
        if parent_id is None:
            self.subsidiary_account.blockSignals(False)
            self.on_subsidiary_account_change()
            return
        try:
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, acc_code, account_name_ar
                    FROM accounts
                    WHERE parent_account_id = ? AND is_final = 1 AND is_active = 1
                    ORDER BY acc_code
                """, (parent_id,))
                for acc_id, code, name in cursor.fetchall():
                    self.subsidiary_account.addItem(f"{code} - {name}", (acc_id, code))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في فلترة الحسابات: {e}")
        self.subsidiary_account.blockSignals(False)
        self.on_subsidiary_account_change()

    def on_subsidiary_account_change(self):
        data = self.subsidiary_account.currentData()
        if data:
            acc_id, acc_code = data
            self.account_code_input.setText(acc_code)
            self.check_cost_center_eligibility(acc_id)
        else:
            self.account_code_input.clear()
            self.cost_center.setEnabled(False)
            self.cost_center.setCurrentIndex(0)

    def check_cost_center_eligibility(self, account_id):
        try:
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    WITH RECURSIVE account_path(id, parent_id) AS (
                        SELECT id, parent_account_id FROM accounts WHERE id = ?
                        UNION ALL
                        SELECT a.id, a.parent_account_id FROM accounts a JOIN account_path p ON a.id = p.parent_id
                    )
                    SELECT at.name_en FROM accounts a
                    JOIN account_types at ON a.account_type_id = at.id
                    WHERE a.parent_account_id IS NULL AND a.id IN (SELECT id FROM account_path)
                """, (account_id,))
                root_type = cursor.fetchone()
                if root_type and root_type[0].lower() in ['expenses', 'revenues']:
                    self.cost_center.setEnabled(True)
                else:
                    self.cost_center.setEnabled(False)
                    self.cost_center.setCurrentIndex(0)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في التحقق من نوع الحساب: {e}")
            self.cost_center.setEnabled(False)

    def find_account_by_code(self):
        acc_code = self.account_code_search.text().strip()
        if not acc_code:
            return
        try:
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, parent_account_id FROM accounts WHERE acc_code = ? AND is_final = 1 AND is_active = 1", (acc_code,))
                result = cursor.fetchone()
                if result:
                    acc_id, parent_id = result
                    general_account_index = self.general_account.findData(parent_id)
                    if general_account_index != -1:
                        self.general_account.setCurrentIndex(general_account_index)
                        QApplication.processEvents()
                        subsidiary_account_index = -1
                        for i in range(self.subsidiary_account.count()):
                            item_data = self.subsidiary_account.itemData(i)
                            if item_data and item_data[0] == acc_id:
                                subsidiary_account_index = i
                                break
                        if subsidiary_account_index != -1:
                            self.subsidiary_account.setCurrentIndex(subsidiary_account_index)
                            self.description.setFocus()
                        else:
                            QMessageBox.warning(self, "غير موجود", "لم يتم العثور على حساب فرعي بهذا الكود ضمن الحساب العام المحدد.")
                    else:
                        QMessageBox.warning(self, "غير موجود", "لم يتم العثور على الحساب العام المرتبط بهذا الكود.")
                else:
                    QMessageBox.warning(self, "غير موجود", "لم يتم العثور على حساب بهذا الكود.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ أثناء البحث عن الحساب: {e}")

    def load_vouchers(self):
        try:
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                cursor = conn.cursor()
                # جلب كل البيانات المطلوبة في استعلام واحد
                cursor.execute("""
                    SELECT 
                        cbt.id, 
                        cbt.transaction_number, 
                        cbt.transaction_date,
                        a_chest.account_name_ar as chest_name,
                        a_credit.account_name_ar as credit_account_name,
                        cbt.amount, 
                        dt.name_ar as document_type,
                        jel.document_number, 
                        tt.name_ar as transaction_type,
                        je.entry_number, 
                        cbt.journal_entry_id
                    FROM cash_bank_transactions cbt
                    LEFT JOIN cash_chests cc ON cbt.cash_chest_id = cc.id
                    LEFT JOIN accounts a_chest ON cc.account_id = a_chest.id
                    LEFT JOIN journal_entries je ON cbt.journal_entry_id = je.id
                    LEFT JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id AND jel.credit > 0 AND jel.account_id != (SELECT tax_account_id FROM tax_types WHERE id = jel.tax_type_id)
                    LEFT JOIN document_types dt ON jel.document_type_id = dt.id
                    LEFT JOIN transaction_types tt ON je.transaction_type_id = tt.id
                    LEFT JOIN accounts a_credit ON jel.account_id = a_credit.id
                    WHERE cbt.transaction_type = 'قبض نقدي'
                    ORDER BY cbt.transaction_date DESC, cbt.transaction_number DESC
                """)
                vouchers = cursor.fetchall()
                self.voucher_table.setRowCount(len(vouchers))

                for row, voucher_data in enumerate(vouchers):
                    # ملء الجدول بطريقة عامة
                    for col, value in enumerate(voucher_data):
                        # العمود الخامس (المبلغ) يتم تنسيقه
                        if col == 5:
                           formatted_value = f"{float(value):,.2f}" if value is not None else "0.00"
                           self.voucher_table.setItem(row, col, QTableWidgetItem(formatted_value))
                        else:
                           self.voucher_table.setItem(row, col, QTableWidgetItem(str(value) if value is not None else ""))
                    
                    journal_entry_id = voucher_data[10]

                    # إضافة زر عرض القيد
                    if journal_entry_id:
                        view_btn = QPushButton("عرض القيد")
                        view_btn.clicked.connect(lambda checked, je_id=journal_entry_id: self.view_journal_entry(je_id))
                        self.voucher_table.setCellWidget(row, 10, view_btn)

                    # إضافة زر تحديد
                    voucher_id = voucher_data[0]
                    select_btn = QPushButton("تحديد")
                    select_btn.clicked.connect(lambda checked, v_id=voucher_id: self.select_voucher_for_edit(v_id))
                    self.voucher_table.setCellWidget(row, 11, select_btn)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل الإيصالات: {e}")


    def view_journal_entry(self, journal_entry_id):
        dialog = JournalEntryViewer(journal_entry_id, self.db_path, self)
        dialog.exec_()

    def select_voucher_for_edit(self, voucher_id):
        try:
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        cbt.transaction_number, cbt.transaction_date, cbt.cash_chest_id, 
                        cbt.description, cbt.amount, cbt.cost_center_id, 
                        jel_credit.account_id as credit_account_id,
                        jel_main.tax_type_id,
                        jel_main.document_type_id, 
                        jel_main.document_number, 
                        je.transaction_type_id
                    FROM cash_bank_transactions cbt
                    LEFT JOIN journal_entries je ON cbt.journal_entry_id = je.id
                    LEFT JOIN journal_entry_lines jel_main ON je.id = jel_main.journal_entry_id AND jel_main.debit > 0
                    LEFT JOIN journal_entry_lines jel_credit ON je.id = jel_credit.journal_entry_id AND jel_credit.credit > 0 AND jel_credit.account_id NOT IN (SELECT tax_account_id FROM tax_types) AND jel_credit.account_id NOT IN (SELECT account_id FROM voucher_deductions WHERE cash_bank_transaction_id = cbt.id)
                    WHERE cbt.id = ?
                """, (voucher_id,))

                voucher = cursor.fetchone()
                if voucher:
                    self.current_voucher_id = voucher_id
                    (trans_num, trans_date, chest_id, desc, amount, cc_id, credit_acc_id,
                     tax_type_id, doc_type_id, doc_number, trans_type_id) = voucher

                    self.voucher_number.setText(str(trans_num or ""))
                    if trans_date:
                        self.voucher_date.setDate(QDate.fromString(trans_date, "yyyy-MM-dd"))

                    self.cash_chests.setCurrentIndex(self.cash_chests.findData(chest_id) if chest_id else 0)
                    self.description.setText(desc or "")
                    self.total_amount.setText(str(amount or ""))
                    self.cost_center.setCurrentIndex(self.cost_center.findData(cc_id) if cc_id else 0)
                    self.tax_type.setCurrentIndex(self.tax_type.findData(tax_type_id) if tax_type_id else 0)
                    self.document_type.setCurrentIndex(self.document_type.findData(doc_type_id) if doc_type_id else 0)
                    self.document_number.setText(doc_number or "")
                    self.transaction_type.setCurrentIndex(self.transaction_type.findData(trans_type_id) if trans_type_id else 0)

                    # set subsidiary account
                    if credit_acc_id:
                        cursor.execute("SELECT parent_account_id FROM accounts WHERE id = ?", (credit_acc_id,))
                        parent_id_result = cursor.fetchone()
                        if parent_id_result:
                            parent_id = parent_id_result[0]
                            self.general_account.setCurrentIndex(self.general_account.findData(parent_id))
                            QApplication.processEvents()
                            for i in range(self.subsidiary_account.count()):
                                item_data = self.subsidiary_account.itemData(i)
                                if item_data and item_data[0] == credit_acc_id:
                                    self.subsidiary_account.setCurrentIndex(i)
                                    break

                    # load deductions
                    self.additional_deductions.clear()
                    cursor.execute("""
                        SELECT vd.account_id, a.acc_code, a.account_name_ar, vd.amount
                        FROM voucher_deductions vd 
                        JOIN accounts a ON vd.account_id = a.id
                        WHERE vd.cash_bank_transaction_id = ?
                    """, (voucher_id,))
                    for acc_id, code, name, ded_amount in cursor.fetchall():
                        self.additional_deductions.append({'account_id': acc_id, 'account_name': f"{code} - {name}", 'amount': ded_amount})

                    self.update_deductions_table()
                    self.update_calculations()
                    self.save_btn.setText("تحديث")
                    QMessageBox.information(self, "تم التحديد", f"تم تحديد الإيصال رقم {trans_num} للتعديل")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل بيانات الإيصال: {e}")

    def new_voucher(self):
        self.current_voucher_id = None
        self.generate_next_voucher_number()
        
        for w in [self.account_code_search, self.account_code_input, self.description,
                  self.total_amount, self.tax_value, self.net_amount, self.deduction_amount,
                  self.document_number]:
            w.clear()
            
        self.voucher_date.setDate(QDate.currentDate())
        
        for combo in [self.cash_chests, self.general_account, self.cost_center,
                      self.tax_type, self.deduction_account, self.document_type,
                      self.transaction_type]:
            combo.setCurrentIndex(0)
            
        self.additional_deductions.clear()
        self.update_deductions_table()
        self.update_calculations()
        self.save_btn.setText("حفظ")
        self.save_btn.setEnabled(True)

    def generate_next_voucher_number(self):
        try:
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(transaction_number) FROM cash_bank_transactions WHERE transaction_type = 'قبض نقدي'")
                last_number_str = cursor.fetchone()[0]
                
                next_num = 1
                if last_number_str:
                    try:
                        # استخلاص الرقم من السلسلة "CR-00001"
                        if "-" in last_number_str:
                           num_part = last_number_str.split('-')[-1]
                           next_num = int(num_part) + 1
                        else:
                           next_num = int(last_number_str) + 1
                    except (ValueError, IndexError):
                        # في حالة وجود قيمة غير متوقعة، ابدأ من 1
                        next_num = 1
                
                new_voucher_number = f"CR-{next_num:05d}"
                self.voucher_number.setText(new_voucher_number)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"لا يمكن توليد رقم الإيصال: {e}")
            self.voucher_number.setText("CR-00001")


    def validate_form(self):
        if not self.voucher_date.date().isValid():
            QMessageBox.warning(self, "خطأ", "يرجى إدخال تاريخ صحيح.")
            return False
        if not self.cash_chests.currentData():
            QMessageBox.warning(self, "خطأ", "يرجى اختيار صندوق نقدي.")
            return False
        if not self.subsidiary_account.currentData():
            QMessageBox.warning(self, "خطأ", "يرجى اختيار الحساب الدائن.")
            return False
        
        try:
            amt = float(self.total_amount.text())
            if amt <= 0:
                QMessageBox.warning(self, "خطأ", "المبلغ يجب أن يكون أكبر من صفر.")
                return False
        except (ValueError, TypeError):
            QMessageBox.warning(self, "خطأ", "يرجى إدخال مبلغ صحيح.")
            return False
        return True

    def save_voucher(self):
        if not self.validate_form():
            return

        # جلب السنة المالية النشطة قبل أي عملية حفظ
        active_year_id = self.get_active_financial_year_id()
        if not active_year_id:
            return # إيقاف الحفظ إذا لم يتم العثور على سنة مالية نشطة

        try:
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                cursor = conn.cursor()
                conn.execute("PRAGMA foreign_keys=ON;")

                voucher_data = {
                    "number": self.voucher_number.text(),
                    "date": self.voucher_date.date().toString("yyyy-MM-dd"),
                    "chest_id": self.cash_chests.currentData(),
                    "desc": self.description.text().strip() or None,
                    "amount": float(self.total_amount.text()),
                    "cost_center_id": self.cost_center.currentData(),
                    "credit_acc_id": self.subsidiary_account.currentData()[0],
                    "tax_type_id": self.tax_type.currentData(),
                    "doc_type_id": self.document_type.currentData(),
                    "doc_number": self.document_number.text().strip() or None,
                    "trans_type_id": self.transaction_type.currentData()
                }

                if self.current_voucher_id:
                    # --- وضع التحديث ---
                    cursor.execute("""
                        UPDATE cash_bank_transactions
                        SET transaction_number=?, transaction_date=?, cash_chest_id=?, description=?, amount=?, cost_center_id=?
                        WHERE id=?
                    """, (
                        voucher_data["number"], voucher_data["date"], voucher_data["chest_id"],
                        voucher_data["desc"], voucher_data["amount"], voucher_data["cost_center_id"],
                        self.current_voucher_id
                    ))
                    
                    cursor.execute("DELETE FROM voucher_deductions WHERE cash_bank_transaction_id=?", (self.current_voucher_id,))
                    for item in self.additional_deductions:
                        cursor.execute("INSERT INTO voucher_deductions (cash_bank_transaction_id, account_id, amount) VALUES (?, ?, ?)",
                                       (self.current_voucher_id, item['account_id'], item['amount']))
                    
                    # تمرير السنة المالية إلى دالة تحديث القيد
                    self.update_journal_entry(cursor, self.current_voucher_id, voucher_data, active_year_id)

                else:
                    # --- وضع الإنشاء ---
                    cursor.execute("""
                        INSERT INTO cash_bank_transactions
                        (transaction_number, transaction_date, cash_chest_id, description, amount, cost_center_id, transaction_type)
                        VALUES (?, ?, ?, ?, ?, ?, 'قبض نقدي')
                    """, (
                        voucher_data["number"], voucher_data["date"], voucher_data["chest_id"],
                        voucher_data["desc"], voucher_data["amount"], voucher_data["cost_center_id"]
                    ))
                    voucher_id = cursor.lastrowid
                    self.current_voucher_id = voucher_id
                    
                    for item in self.additional_deductions:
                        cursor.execute("INSERT INTO voucher_deductions (cash_bank_transaction_id, account_id, amount) VALUES (?, ?, ?)",
                                       (voucher_id, item['account_id'], item['amount']))

                    # تمرير السنة المالية إلى دالة إنشاء القيد
                    self.create_journal_entry(cursor, voucher_id, voucher_data, active_year_id)
                
                conn.commit()
                QMessageBox.information(self, "تم", f"تم حفظ الإيصال رقم {voucher_data['number']} بنجاح.")
                self.load_vouchers()
                self.new_voucher()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ أثناء الحفظ: {e}")
            conn.rollback()

    def create_journal_entry(self, cursor, voucher_id, data, financial_year_id):
        """
        إنشاء قيد محاسبي جديد للإيصال مع حساب إجمالي المدين والدائن.
        """
        try:
            # 1. حساب جميع المبالغ الفردية (كما كان في السابق)
            total_amount = data['amount']
            tax_rate_result = cursor.execute("SELECT rate FROM tax_types WHERE id=?", (data['tax_type_id'],)).fetchone()
            tax_amount = total_amount * (tax_rate_result[0] / 100.0) if tax_rate_result and data['tax_type_id'] else 0.0
            deductions_total = sum(d['amount'] for d in self.additional_deductions)
            net_amount = total_amount - tax_amount - deductions_total
            
            chest_account_id = cursor.execute("SELECT account_id FROM cash_chests WHERE id=?", (data['chest_id'],)).fetchone()[0]
            
            # --- الجزء الجديد: حساب إجمالي المدين والدائن للقيد ---
            # في سند القبض: المدين هو المبلغ الإجمالي المستلم، والدائن هو مجموع الأطراف الأخرى
            journal_total_debit = total_amount
            journal_total_credit = net_amount + tax_amount + deductions_total
            # ----------------------------------------------------

            cursor.execute("SELECT MAX(CAST(entry_number AS INTEGER)) FROM journal_entries")
            next_entry_number = (cursor.fetchone()[0] or 0) + 1
            entry_desc = data['desc'] or f"إيصال قبض رقم {data['number']}"
            
            # --- التعديل هنا: إضافة total_debit و total_credit إلى جملة الإدخال ---
            cursor.execute("""
                INSERT INTO journal_entries (entry_number, entry_date, description, transaction_type_id, financial_year_id, total_debit, total_credit) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (str(next_entry_number), data['date'], entry_desc, data['trans_type_id'], financial_year_id, journal_total_debit, journal_total_credit))
            journal_entry_id = cursor.lastrowid

            # --- باقي الكود لإدخال أطراف القيد يبقى كما هو ---
            # الطرف المدين: الصندوق
            cursor.execute("""
                INSERT INTO journal_entry_lines (journal_entry_id, account_id, debit, notes, document_type_id, document_number, cost_center_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (journal_entry_id, chest_account_id, total_amount, entry_desc, data['doc_type_id'], data['doc_number'], data['cost_center_id']))

            # الطرف الدائن: الحساب المساعد
            cursor.execute("""
                INSERT INTO journal_entry_lines (journal_entry_id, account_id, credit, notes, document_type_id, document_number, cost_center_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (journal_entry_id, data['credit_acc_id'], net_amount, entry_desc, data['doc_type_id'], data['doc_number'], data['cost_center_id']))
            
            # الطرف الدائن: الضريبة
            if tax_amount > 0:
                tax_account_id_result = cursor.execute("SELECT tax_account_id FROM tax_types WHERE id=?", (data['tax_type_id'],)).fetchone()
                if tax_account_id_result and tax_account_id_result[0]:
                    tax_account_id = tax_account_id_result[0]
                    cursor.execute("""
                        INSERT INTO journal_entry_lines (journal_entry_id, account_id, credit, notes, tax_type_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (journal_entry_id, tax_account_id, tax_amount, f"ضريبة على إيصال {data['number']}", data['tax_type_id']))

            # الطرف الدائن: الخصومات
            for item in self.additional_deductions:
                cursor.execute("""
                    INSERT INTO journal_entry_lines (journal_entry_id, account_id, credit, notes)
                    VALUES (?, ?, ?, ?)
                """, (journal_entry_id, item['account_id'], item['amount'], f"خصم من إيصال {data['number']}"))

            cursor.execute("UPDATE cash_bank_transactions SET journal_entry_id = ? WHERE id = ?", (journal_entry_id, voucher_id))
            
        except sqlite3.Error as e:
            # إضافة تفاصيل أكثر للخطأ للمساعدة في التشخيص
            import traceback
            print(traceback.format_exc())
            raise sqlite3.Error(f"فشل في إنشاء القيد المحاسبي: {e}")
        
    def update_journal_entry(self, cursor, voucher_id, data, financial_year_id):
        """
        تحديث القيد المحاسبي المرتبط بإيصال.
        """
        try:
            cursor.execute("SELECT journal_entry_id FROM cash_bank_transactions WHERE id = ?", (voucher_id,))
            result = cursor.fetchone()
            if result and result[0]:
                old_journal_entry_id = result[0]
                cursor.execute("DELETE FROM journal_entry_lines WHERE journal_entry_id = ?", (old_journal_entry_id,))
                cursor.execute("DELETE FROM journal_entries WHERE id = ?", (old_journal_entry_id,))
            
            # تمرير السنة المالية عند إعادة إنشاء القيد
            self.create_journal_entry(cursor, voucher_id, data, financial_year_id)
        
        except sqlite3.Error as e:
            raise sqlite3.Error(f"فشل في تحديث القيد المحاسبي: {e}")

    def delete_voucher(self):
        if not self.current_voucher_id:
            QMessageBox.warning(self, "تحذير", "يرجى تحديد إيصال للحذف أولاً")
            return

        reply = QMessageBox.question(self, "تأكيد الحذف",
                                     f"هل أنت متأكد من حذف الإيصال رقم {self.voucher_number.text()}؟\nسيتم حذف القيد المحاسبي المرتبط به أيضاً.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        try:
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                cursor = conn.cursor()
                conn.execute("PRAGMA foreign_keys=ON;")

                # جلب رقم القيد قبل حذف الإيصال
                cursor.execute("SELECT journal_entry_id FROM cash_bank_transactions WHERE id = ?", (self.current_voucher_id,))
                r = cursor.fetchone()
                journal_entry_id = r[0] if r else None

                # الحذف سيتتالي بفضل PRAGMA foreign_keys=ON إذا تم ضبط الحذف المتتالي (ON DELETE CASCADE) في تصميم الجداول
                # للتأكيد، يمكن الحذف بشكل يدوي
                cursor.execute("DELETE FROM voucher_deductions WHERE cash_bank_transaction_id = ?", (self.current_voucher_id,))
                cursor.execute("DELETE FROM cash_bank_transactions WHERE id = ?", (self.current_voucher_id,))

                if journal_entry_id:
                    cursor.execute("DELETE FROM journal_entry_lines WHERE journal_entry_id = ?", (journal_entry_id,))
                    cursor.execute("DELETE FROM journal_entries WHERE id = ?", (journal_entry_id,))

                conn.commit()
                QMessageBox.information(self, "تم", "تم حذف الإيصال بنجاح.")
                self.load_vouchers()
                self.new_voucher()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ أثناء الحذف: {e}")
            conn.rollback()

    def edit_voucher(self):
        if not self.current_voucher_id:
            QMessageBox.warning(self, "تحذير", "يرجى تحديد إيصال للتعديل أولاً من قائمة الإيصالات بالأسفل.")
            return
        # لا حاجة لتغيير النص أو تفعيل الزر لأنه يتم بالفعل عند تحديد الإيصال
        self.save_btn.setText("تحديث")
        self.save_btn.setEnabled(True)
        self.voucher_date.setFocus()

    def get_active_financial_year_id(self):
        """
        تجلب هذه الدالة معرّف السنة المالية النشطة حالياً من قاعدة البيانات
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM financial_years WHERE is_active = 1 LIMIT 1")
                result = cursor.fetchone()
                if result:
                    return result[0]
                else:
                    QMessageBox.critical(self, "خطأ فادح", "لا توجد سنة مالية نشطة في النظام. يرجى تفعيل سنة مالية أولاً.")
                    return None
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"لا يمكن العثور على السنة المالية النشطة: {e}")
            return None

# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))
    window = CashReceiptVoucherApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
    # ... (الكود السابق يبقى كما هو)

    def load_vouchers(self):
        try:
            with sqlite3.connect(self.db_path, timeout=20) as conn:
                cursor = conn.cursor()
                # تصحيح الاستعلام لجلب البيانات بشكل صحيح
                cursor.execute("""
                    SELECT 
                        cbt.id, 
                        cbt.transaction_number, 
                        cbt.transaction_date,
                        a_chest.account_name_ar as chest_name,
                        a_credit.account_name_ar as credit_account_name,
                        cbt.amount, 
                        dt.name_ar as document_type,
                        cbt.document_number, 
                        tt.name_ar as transaction_type,
                        je.entry_number, 
                        cbt.journal_entry_id
                    FROM cash_bank_transactions cbt
                    JOIN cash_chests cc ON cbt.cash_chest_id = cc.id
                    JOIN accounts a_chest ON cc.account_id = a_chest.id
                    LEFT JOIN journal_entries je ON cbt.journal_entry_id = je.id
                    LEFT JOIN journal_entry_lines jel_credit ON je.id = jel_credit.journal_entry_id 
                        AND jel_credit.credit > 0 
                    LEFT JOIN accounts a_credit ON jel_credit.account_id = a_credit.id
                    LEFT JOIN document_types dt ON cbt.document_type_id = dt.id
                    LEFT JOIN transaction_types tt ON cbt.transaction_type_id = tt.id
                    WHERE cbt.transaction_type = 'قبض نقدي'
                    ORDER BY cbt.transaction_date DESC, cbt.transaction_number DESC
                """)
                vouchers = cursor.fetchall()
                self.voucher_table.setRowCount(len(vouchers))

                for row, voucher_data in enumerate(vouchers):
                    for col, value in enumerate(voucher_data):
                        if col == 5:  # عمود المبلغ
                            formatted_value = f"{float(value):,.2f}" if value is not None else "0.00"
                            self.voucher_table.setItem(row, col, QTableWidgetItem(formatted_value))
                        else:
                            self.voucher_table.setItem(row, col, QTableWidgetItem(str(value) if value is not None else ""))
                    
                    journal_entry_id = voucher_data[10]

                    if journal_entry_id:
                        view_btn = QPushButton("عرض القيد")
                        view_btn.clicked.connect(lambda checked, je_id=journal_entry_id: self.view_journal_entry(je_id))
                        self.voucher_table.setCellWidget(row, 10, view_btn)

                    voucher_id = voucher_data[0]
                    select_btn = QPushButton("تحديد")
                    select_btn.clicked.connect(lambda checked, v_id=voucher_id: self.select_voucher_for_edit(v_id))
                    self.voucher_table.setCellWidget(row, 11, select_btn)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل الإيصالات: {e}")

    def create_journal_entry(self, cursor, voucher_id, data, financial_year_id):
        """
        إنشاء قيد محاسبي جديد للإيصال
        """
        try:
            total_amount = data['amount']
            tax_rate_result = cursor.execute("SELECT rate, tax_account_id FROM tax_types WHERE id=?", (data['tax_type_id'],)).fetchone()
            tax_amount = total_amount * (tax_rate_result[0] / 100.0) if tax_rate_result and data['tax_type_id'] else 0.0
            deductions_total = sum(d['amount'] for d in self.additional_deductions)
            net_amount = total_amount - tax_amount - deductions_total
            
            chest_account_id = cursor.execute("SELECT account_id FROM cash_chests WHERE id=?", (data['chest_id'],)).fetchone()[0]
            
            # حساب إجمالي المدين والدائن (يجب أن يكونا متساويين)
            journal_total_debit = total_amount
            journal_total_credit = net_amount + tax_amount + deductions_total
            
            cursor.execute("SELECT MAX(CAST(entry_number AS INTEGER)) FROM journal_entries")
            next_entry_number = (cursor.fetchone()[0] or 0) + 1
            entry_desc = data['desc'] or f"إيصال قبض رقم {data['number']}"
            
            cursor.execute("""
                INSERT INTO journal_entries (entry_number, entry_date, description, transaction_type_id, financial_year_id, total_debit, total_credit) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (str(next_entry_number), data['date'], entry_desc, data['trans_type_id'], financial_year_id, journal_total_debit, journal_total_credit))
            journal_entry_id = cursor.lastrowid

            # الطرف المدين: الصندوق
            cursor.execute("""
                INSERT INTO journal_entry_lines (journal_entry_id, account_id, debit, notes, document_type_id, document_number, cost_center_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (journal_entry_id, chest_account_id, total_amount, entry_desc, data['doc_type_id'], data['doc_number'], data['cost_center_id']))

            # الطرف الدائن: الحساب المساعد
            cursor.execute("""
                INSERT INTO journal_entry_lines (journal_entry_id, account_id, credit, notes, document_type_id, document_number, cost_center_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (journal_entry_id, data['credit_acc_id'], net_amount, entry_desc, data['doc_type_id'], data['doc_number'], data['cost_center_id']))
            
            # الطرف الدائن: الضريبة
            if tax_amount > 0 and tax_rate_result and tax_rate_result[1]:
                cursor.execute("""
                    INSERT INTO journal_entry_lines (journal_entry_id, account_id, credit, notes, tax_type_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (journal_entry_id, tax_rate_result[1], tax_amount, f"ضريبة على إيصال {data['number']}", data['tax_type_id']))

            # الطرف الدائن: الخصومات
            for item in self.additional_deductions:
                cursor.execute("""
                    INSERT INTO journal_entry_lines (journal_entry_id, account_id, credit, notes)
                    VALUES (?, ?, ?, ?)
                """, (journal_entry_id, item['account_id'], item['amount'], f"خصم من إيصال {data['number']}"))

            cursor.execute("UPDATE cash_bank_transactions SET journal_entry_id = ? WHERE id = ?", (journal_entry_id, voucher_id))
            
        except sqlite3.Error as e:
            import traceback
            print(traceback.format_exc())
            raise sqlite3.Error(f"فشل في إنشاء القيد المحاسبي: {e}")

    def update_journal_entry(self, cursor, voucher_id, data, financial_year_id):
        """
        تحديث القيد المحاسبي المرتبط بإيصال
        """
        try:
            # البحث عن journal_entry_id المرتبط بالإيصال
            cursor.execute("SELECT journal_entry_id FROM cash_bank_transactions WHERE id = ?", (voucher_id,))
            result = cursor.fetchone()
            
            if result and result[0]:
                journal_entry_id = result[0]
                # حذف الخطوات القديمة للقيد
                cursor.execute("DELETE FROM journal_entry_lines WHERE journal_entry_id = ?", (journal_entry_id,))
                
                # تحديث بيانات القيد الرئيسية
                total_amount = data['amount']
                tax_rate_result = cursor.execute("SELECT rate, tax_account_id FROM tax_types WHERE id=?", (data['tax_type_id'],)).fetchone()
                tax_amount = total_amount * (tax_rate_result[0] / 100.0) if tax_rate_result and data['tax_type_id'] else 0.0
                deductions_total = sum(d['amount'] for d in self.additional_deductions)
                net_amount = total_amount - tax_amount - deductions_total
                
                journal_total_debit = total_amount
                journal_total_credit = net_amount + tax_amount + deductions_total
                
                entry_desc = data['desc'] or f"إيصال قبض رقم {data['number']}"
                
                cursor.execute("""
                    UPDATE journal_entries 
                    SET entry_date = ?, description = ?, transaction_type_id = ?, financial_year_id = ?, total_debit = ?, total_credit = ?
                    WHERE id = ?
                """, (data['date'], entry_desc, data['trans_type_id'], financial_year_id, journal_total_debit, journal_total_credit, journal_entry_id))
                
                # إعادة إنشاء خطوات القيد
                chest_account_id = cursor.execute("SELECT account_id FROM cash_chests WHERE id=?", (data['chest_id'],)).fetchone()[0]
                
                # الطرف المدين: الصندوق
                cursor.execute("""
                    INSERT INTO journal_entry_lines (journal_entry_id, account_id, debit, notes, document_type_id, document_number, cost_center_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (journal_entry_id, chest_account_id, total_amount, entry_desc, data['doc_type_id'], data['doc_number'], data['cost_center_id']))

                # الطرف الدائن: الحساب المساعد
                cursor.execute("""
                    INSERT INTO journal_entry_lines (journal_entry_id, account_id, credit, notes, document_type_id, document_number, cost_center_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (journal_entry_id, data['credit_acc_id'], net_amount, entry_desc, data['doc_type_id'], data['doc_number'], data['cost_center_id']))
                
                # الطرف الدائن: الضريبة
                if tax_amount > 0 and tax_rate_result and tax_rate_result[1]:
                    cursor.execute("""
                        INSERT INTO journal_entry_lines (journal_entry_id, account_id, credit, notes, tax_type_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (journal_entry_id, tax_rate_result[1], tax_amount, f"ضريبة على إيصال {data['number']}", data['tax_type_id']))

                # الطرف الدائن: الخصومات
                for item in self.additional_deductions:
                    cursor.execute("""
                        INSERT INTO journal_entry_lines (journal_entry_id, account_id, credit, notes)
                        VALUES (?, ?, ?, ?)
                    """, (journal_entry_id, item['account_id'], item['amount'], f"خصم من إيصال {data['number']}"))
            else:
                # إذا لم يكن هناك قيد مرتبط، إنشاء قيد جديد
                self.create_journal_entry(cursor, voucher_id, data, financial_year_id)
        
        except sqlite3.Error as e:
            raise sqlite3.Error(f"فشل في تحديث القيد المحاسبي: {e}")

# ... (باقي الكود يبقى كما هو)
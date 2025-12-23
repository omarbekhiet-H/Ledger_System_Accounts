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
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT je.entry_number, je.entry_date, je.description, tt.name_ar
                    FROM journal_entries je 
                    LEFT JOIN transaction_types tt ON je.transaction_type_id = tt.id
                    WHERE je.id = ?
                """, (self.journal_entry_id,))
                entry = cursor.fetchone()
                if entry:
                    self.entry_number_value.setText(entry[0])
                    self.entry_date_value.setText(entry[1])
                    self.description_value.setText(entry[2])
                    self.transaction_type_value.setText(entry[3] if entry[3] else "بدون")
                
                cursor.execute("""
                   SELECT a.acc_code, a.account_name_ar, jel.debit, jel.credit, jel.notes,
                        dt.name_ar AS doc_type, jel.document_number,
                        tt.name_ar AS tax_type, cc.name_ar AS cost_center
                        FROM journal_entry_lines jel 
                    JOIN accounts a ON jel.account_id = a.id
                    LEFT JOIN document_types dt ON jel.document_type_id = dt.id
                    LEFT JOIN tax_types tt ON jel.tax_type_id = tt.id
                    LEFT JOIN cost_centers cc ON jel.cost_center_id = cc.id
                    WHERE jel.journal_entry_id = ? ORDER BY jel.debit DESC

                """, (self.journal_entry_id,))
                lines = cursor.fetchall()
                self.lines_table.setRowCount(len(lines))
                for row, line_data in enumerate(lines):
                    for col, value in enumerate(line_data):
                        self.lines_table.setItem(row, col, QTableWidgetItem(str(value) if value is not None else ""))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"لا يمكن تحميل تفاصيل القيد: {e}")

#class CashPaymentVoucherApp(QMainWindow):
    #def __init__(self, db_path):
    #    super().__init__()
    #    self.db_path = db_path
    #    self.current_voucher_id = None
    #    self.additional_deductions = []
    #    if not os.path.exists(self.db_path):
    #        QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"ملف قاعدة البيانات غير موجود في المسار:\n{self.db_path}")
    #        sys.exit(1)
    #    self.initUI()
    #    self.set_focus_order()
    #    self.load_data()
    #   self.new_voucher()

class CashPaymentVoucherApp(QMainWindow):
    def __init__(self, db_path=None):  # جعل db_path اختياريًا
        super().__init__()
        if db_path is None:
            # إذا لم يتم توفير db_path، استخدم المسار الافتراضي
            project_root = os.getcwd()
            db_path = os.path.join(project_root, 'database', 'financials.db')
        self.db_path = db_path
        self.current_voucher_id = None
        self.additional_deductions = []
        if not os.path.exists(self.db_path):
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"ملف قاعدة البيانات غير موجود في المسار:\n{self.db_path}")
            sys.exit(1)
        self.initUI()
        self.set_focus_order()
        self.load_data()
        self.new_voucher()

    def initUI(self):
        self.setWindowTitle('نظام إيصالات الصرف النقدي')
        self.setGeometry(100, 100, 1200, 900)
        self.setLayoutDirection(Qt.RightToLeft)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        title_label = QLabel('إيصالات الصرف النقدي')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        main_layout.addWidget(title_label)
        
        self.read_only_palette = QPalette()
        self.read_only_palette.setColor(QPalette.Base, QColor(240, 240, 240))

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
        basic_layout.addWidget(QLabel("حساب الصندوق (الدائن):"), 0, 4); basic_layout.addWidget(self.cash_chests, 0, 5)
        basic_layout.addWidget(QLabel("نوع المستند:"), 1, 0); basic_layout.addWidget(self.document_type, 1, 1)
        basic_layout.addWidget(QLabel("رقم المستند:"), 1, 2); basic_layout.addWidget(self.document_number, 1, 3)
        basic_layout.addWidget(QLabel("نوع الحركة:"), 1, 4); basic_layout.addWidget(self.transaction_type, 1, 5)
        main_layout.addWidget(basic_info_group)

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
        self.total_amount = QLineEdit(); self.total_amount.setValidator(QDoubleValidator(0, 9999999.99, 2)); self.total_amount.textChanged.connect(self.update_calculations)
        self.tax_value = QLineEdit(readOnly=True); self.tax_value.setPalette(self.read_only_palette)
        self.net_amount = QLineEdit(readOnly=True); self.net_amount.setPalette(self.read_only_palette)
        
        trans_layout.addWidget(QLabel("بحث بالكود:"), 0, 0); trans_layout.addWidget(self.account_code_search, 0, 1)
        trans_layout.addWidget(QLabel("الحساب العام:"), 0, 2); trans_layout.addWidget(self.general_account, 0, 3)
        trans_layout.addWidget(QLabel("الحساب المساعد (المدين):"), 0, 4); trans_layout.addWidget(self.subsidiary_account, 0, 5)
        trans_layout.addWidget(QLabel("نوع الضريبة:"), 1, 0); trans_layout.addWidget(self.tax_type, 1, 1)
        trans_layout.addWidget(QLabel("مركز التكلفة:"), 1, 2); trans_layout.addWidget(self.cost_center, 1, 3)
        trans_layout.addWidget(QLabel("<b>المبلغ الإجمالي:</b>"), 2, 0); trans_layout.addWidget(self.total_amount, 2, 1)
        trans_layout.addWidget(QLabel("قيمة الضريبة:"), 2, 2); trans_layout.addWidget(self.tax_value, 2, 3)
        trans_layout.addWidget(QLabel("<b>الصافي (للخزينة):</b>"), 2, 4); trans_layout.addWidget(self.net_amount, 2, 5)
        trans_layout.addWidget(QLabel("البيان:"), 3, 0); trans_layout.addWidget(self.description, 3, 1, 1, 5)
        main_layout.addWidget(transaction_group)
        
        deductions_group = QGroupBox("الخصومات الإضافية")
        deductions_layout = QGridLayout(deductions_group)
        self.deduction_account = QComboBox()
        self.deduction_account.setEditable(True)
        self.deduction_account.setInsertPolicy(QComboBox.NoInsert)
        completer = QCompleter(self.deduction_account.model(), self)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.deduction_account.setCompleter(completer)
        self.deduction_amount = QLineEdit(); self.deduction_amount.setValidator(QDoubleValidator(0, 9999999.99, 2))
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
        
        button_layout = QHBoxLayout()
        buttons = {'new_btn': ('جديد', self.new_voucher), 'save_btn': ('حفظ', self.save_voucher), 'edit_btn': ('تعديل', self.edit_voucher), 'delete_btn': ('حذف', self.delete_voucher)}
        for name, (text, func) in buttons.items():
            btn = QPushButton(text); btn.setFont(QFont("Arial", 10, QFont.Bold)); btn.setMinimumHeight(35)
            btn.clicked.connect(func); setattr(self, name, btn); button_layout.addWidget(btn)
        main_layout.addLayout(button_layout)
        
        self.voucher_table = QTableWidget(columnCount=11)
        self.voucher_table.setHorizontalHeaderLabels(['ID', 'رقم الإيصال', 'التاريخ', 'الصندوق', 'الحساب المدين', 'المبلغ', 'نوع المستند', 'رقم المستند', 'نوع الحركة', 'رقم القيد', 'عرض القيد', 'تحديد'])
        self.voucher_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.voucher_table.setColumnHidden(0, True)
        main_layout.addWidget(self.voucher_table)

    def set_focus_order(self):
        widgets = [self.voucher_date, self.cash_chests, self.document_type, self.document_number, 
                   self.transaction_type, self.account_code_search, self.general_account, 
                   self.subsidiary_account, self.description, self.tax_type, self.cost_center, 
                   self.total_amount, self.deduction_account, self.deduction_amount, self.add_deduction_btn]
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
        
        tax_rate = self.tax_type.currentData() or 0.0
        tax = total * (tax_rate / 100.0)
        
        total_deductions = sum(item['amount'] for item in self.additional_deductions)
        
        net = total - tax - total_deductions
        
        self.tax_value.setText(f"{tax:.2f}")
        self.net_amount.setText(f"{net:.2f}")

    def load_data(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # تحميل أنواع المستندات
                self.document_type.clear()
                self.document_type.addItem("--- اختر نوع المستند ---", None)
                cursor.execute("SELECT id, code, name_ar FROM document_types WHERE is_active = 1 ORDER BY code")
                for doc_id, code, name in cursor.fetchall():
                    self.document_type.addItem(f"{code} - {name}", doc_id)
                
                # تحميل أنواع الحركات
                self.transaction_type.clear()
                self.transaction_type.addItem("--- اختر نوع الحركة ---", None)
                cursor.execute("SELECT id, code, name_ar FROM transaction_types WHERE is_active = 1 ORDER BY code")
                for trans_id, code, name in cursor.fetchall():
                    self.transaction_type.addItem(f"{code} - {name}", trans_id)
                
                # تحميل باقي البيانات
                self.cash_chests.clear()
                cursor.execute("SELECT c.id, a.acc_code, a.account_name_ar FROM cash_chests c JOIN accounts a ON c.account_id = a.id WHERE c.is_active = 1 AND a.is_active = 1")
                for chest_id, code, name in cursor.fetchall(): 
                    self.cash_chests.addItem(f"{code} - {name}", chest_id)
                
                self.general_account.blockSignals(True)
                self.general_account.clear(); self.general_account.addItem("--- اختر الحساب العام ---", None)
                cursor.execute("SELECT id, acc_code, account_name_ar FROM accounts WHERE is_final = 0 AND is_active = 1 ORDER BY acc_code")
                for acc_id, code, name in cursor.fetchall(): 
                    self.general_account.addItem(f"{code} - {name}", acc_id)
                self.general_account.blockSignals(False); self.filter_subsidiary_accounts()
                
                self.cost_center.clear(); self.cost_center.addItem("--- بدون مركز تكلفة ---", None)
                cursor.execute("SELECT id, code, name_ar FROM cost_centers WHERE is_active = 1")
                for cc_id, code, name in cursor.fetchall(): 
                    self.cost_center.addItem(f"{code} - {name}", cc_id)

                self.tax_type.clear(); self.tax_type.addItem("--- بدون ضريبة ---", 0.0)
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
            self.deductions_table.setItem(row, 2, QTableWidgetItem(str(item['amount'])))
            
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
        if parent_id is None:
            self.subsidiary_account.blockSignals(False)
            self.on_subsidiary_account_change()
            return
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, acc_code, account_name_ar FROM accounts WHERE parent_account_id = ? AND is_final = 1 AND is_active = 1 ORDER BY acc_code", (parent_id,))
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

    def check_cost_center_eligibility(self, account_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
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
        if not acc_code: return
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, parent_account_id FROM accounts WHERE acc_code = ? AND is_final = 1", (acc_code,))
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
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT cbt.id, cbt.transaction_number, cbt.transaction_date, 
                           a_chest.account_name_ar as chest_name,
                           a_debit.account_name_ar as debit_account_name,
                           cbt.amount, dt.name_ar as document_type,
                           jel.document_number, 
                           cbt.transaction_type,        -- 👈 هنا بنعرض نوع المعاملة من العمود نفسه
                           je.entry_number, 
                           cbt.journal_entry_id
                    FROM cash_bank_transactions cbt
                    LEFT JOIN cash_chests cc ON cbt.cash_chest_id = cc.id
                    LEFT JOIN accounts a_chest ON cc.account_id = a_chest.id
                    LEFT JOIN journal_entries je ON cbt.journal_entry_id = je.id
                    LEFT JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id AND jel.debit > 0
                    LEFT JOIN document_types dt ON jel.document_type_id = dt.id
                    LEFT JOIN accounts a_debit ON jel.account_id = a_debit.id
                    ORDER BY cbt.transaction_date DESC, cbt.transaction_number DESC
                """)
                vouchers = cursor.fetchall()
                self.voucher_table.setRowCount(len(vouchers))
    
                for row, voucher in enumerate(vouchers):
                    for col_idx, value in enumerate(voucher):
                        item = QTableWidgetItem(str(value) if value is not None else "")
                        self.voucher_table.setItem(row, col_idx, item)
        
                    journal_entry_id = voucher[10] if len(voucher) > 10 else None
        
                    if journal_entry_id:
                        view_btn = QPushButton("عرض القيد")
                        view_btn.clicked.connect(lambda checked, je_id=journal_entry_id: self.view_journal_entry(je_id))
                        self.voucher_table.setCellWidget(row, 10, view_btn)
        
                    select_btn = QPushButton("تحديد")
                    select_btn.clicked.connect(lambda checked, v_id=voucher[0]: self.select_voucher_for_edit(v_id))
                    self.voucher_table.setCellWidget(row, 11, select_btn)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل الإيصالات: {e}")


    def view_journal_entry(self, journal_entry_id):
        dialog = JournalEntryViewer(journal_entry_id, self.db_path, self)
        dialog.exec_()

    def select_voucher_for_edit(self, voucher_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT cbt.transaction_number, cbt.transaction_date, cbt.cash_chest_id, cbt.description,
                           cbt.amount, cbt.cost_center_id, jel.account_id as debit_account_id,
                           (SELECT rate FROM tax_types tt JOIN journal_entry_lines jel_tax ON tt.id = jel_tax.tax_type_id WHERE jel_tax.journal_entry_id = je.id AND jel_tax.credit > 0 LIMIT 1) as tax_rate_value,
                           jel.document_type_id, jel.document_number, je.transaction_type_id
                    FROM cash_bank_transactions cbt
                    LEFT JOIN journal_entries je ON cbt.journal_entry_id = je.id
                    LEFT JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id AND jel.debit > 0
                    WHERE cbt.id = ?
                """, (voucher_id,))
            
                voucher = cursor.fetchone()
                if voucher:
                    self.current_voucher_id = voucher_id
                    (trans_num, trans_date, chest_id, desc, amount, cc_id, debit_acc_id, 
                     tax_rate, doc_type_id, doc_number, trans_type_id) = voucher

                    self.voucher_number.setText(trans_num)
                    self.voucher_date.setDate(QDate.fromString(trans_date, "yyyy-MM-dd"))
                    self.cash_chests.setCurrentIndex(self.cash_chests.findData(chest_id))
                    self.description.setText(desc or "")
                    self.total_amount.setText(str(amount))
                    self.cost_center.setCurrentIndex(self.cost_center.findData(cc_id) if cc_id else 0)
                    self.tax_type.setCurrentIndex(self.tax_type.findData(tax_rate) if tax_rate is not None else 0)
                
                    # بيانات المستند من journal_entry_lines بدلاً من journal_entries
                    self.document_type.setCurrentIndex(self.document_type.findData(doc_type_id) if doc_type_id else 0)
                    self.document_number.setText(doc_number or "")
                    self.transaction_type.setCurrentIndex(self.transaction_type.findData(trans_type_id) if trans_type_id else 0)

                    if debit_acc_id:
                        cursor.execute("SELECT parent_account_id FROM accounts WHERE id = ?", (debit_acc_id,))
                        parent_id_result = cursor.fetchone()
                        if parent_id_result:
                            parent_id = parent_id_result[0]
                            self.general_account.setCurrentIndex(self.general_account.findData(parent_id))
                            QApplication.processEvents()
                            for i in range(self.subsidiary_account.count()):
                                item_data = self.subsidiary_account.itemData(i)
                                if item_data and item_data[0] == debit_acc_id:
                                    self.subsidiary_account.setCurrentIndex(i)
                                    break
                
                    self.additional_deductions.clear()
                    cursor.execute("""
                        SELECT vd.account_id, a.acc_code, a.account_name_ar, vd.amount
                        FROM voucher_deductions vd JOIN accounts a ON vd.account_id = a.id
                        WHERE vd.cash_bank_transaction_id = ?
                    """, (voucher_id,))
                    for acc_id, code, name, ded_amount in cursor.fetchall():
                        self.additional_deductions.append({
                            'account_id': acc_id, 'account_name': f"{code} - {name}", 'amount': ded_amount
                        })
                
                    self.update_deductions_table()
                    self.update_calculations()
                    self.save_btn.setText("تحديث")
                    QMessageBox.information(self, "تم التحديد", f"تم تحديد الإيصال رقم {trans_num} للتعديل")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل بيانات الإيصال: {e}")

    def new_voucher(self):
        self.current_voucher_id = None
        self.voucher_number.setText(self.generate_next_voucher_number())
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
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(CAST(transaction_number AS INTEGER)) FROM cash_bank_transactions WHERE transaction_type = 'صرف نقدي'")
                result = cursor.fetchone()
                next_number = 1 if result[0] is None else int(result[0]) + 1
                return str(next_number)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في توليد رقم الإيصال: {e}")
            return "1"

    def validate_form(self):
        if not self.cash_chests.currentData():
            QMessageBox.warning(self, "بيانات ناقصة", "يرجى اختيار صندوق/بنك.")
            return False
            
        if not self.subsidiary_account.currentData():
            QMessageBox.warning(self, "بيانات ناقصة", "يرجى اختيار حساب مدين.")
            return False
            
        try:
            amount = float(self.total_amount.text())
            if amount <= 0:
                QMessageBox.warning(self, "قيمة غير صحيحة", "يرجى إدخال مبلغ صحيح أكبر من الصفر.")
                return False
        except ValueError:
            QMessageBox.warning(self, "قيمة غير صحيحة", "يرجى إدخال مبلغ صحيح.")
            return False
            
        return True

    def save_voucher(self):
        if not self.validate_form():
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
            
                # حساب المبالغ
                total_amount = float(self.total_amount.text())
                tax_rate = self.tax_type.currentData() or 0.0
                tax_amount = total_amount * (tax_rate / 100.0)
                deductions_total = sum(d['amount'] for d in self.additional_deductions)
                net_amount = total_amount - tax_amount - deductions_total
            
                if self.current_voucher_id:
                    # تحديث الإيصال الحالي - إزالة document_type_id و document_number
                    cursor.execute("""
                        UPDATE cash_bank_transactions 
                        SET transaction_date=?, cash_chest_id=?, description=?, amount=?,
                            cost_center_id=?, transaction_type_id=?
                        WHERE id=?
                    """, (
                        self.voucher_date.date().toString("yyyy-MM-dd"),
                        self.cash_chests.currentData(),
                        self.description.text(),
                        total_amount,
                        self.cost_center.currentData(),
                        self.transaction_type.currentData(),
                        self.current_voucher_id
                    ))
                
                    # حذف الخصومات القديمة
                    cursor.execute("DELETE FROM voucher_deductions WHERE cash_bank_transaction_id=?", (self.current_voucher_id,))
                
                    # إضافة الخصومات الجديدة
                    for deduction in self.additional_deductions:
                        cursor.execute("""
                            INSERT INTO voucher_deductions (cash_bank_transaction_id, account_id, amount)
                            VALUES (?, ?, ?)
                        """, (self.current_voucher_id, deduction['account_id'], deduction['amount']))
                
                    # تحديث القيد المحاسبي
                    self.update_journal_entry(cursor, self.current_voucher_id)
                
                else:
                    # إنشاء إيصال جديد - إزالة document_type_id و document_number
                    cursor.execute("""
                        INSERT INTO cash_bank_transactions 
                        (transaction_number, transaction_date, cash_chest_id, transaction_type, description, amount, cost_center_id, transaction_type_id)
                        VALUES (?, ?, ?, 'صرف نقدي', ?, ?, ?, ?)
                    """, (
                        self.voucher_number.text(),
                        self.voucher_date.date().toString("yyyy-MM-dd"),
                        self.cash_chests.currentData(),
                        self.description.text(),
                        total_amount,
                        self.cost_center.currentData(),
                        self.transaction_type.currentData()
                    ))
                
                    voucher_id = cursor.lastrowid
                
                    # إضافة الخصومات
                    for deduction in self.additional_deductions:
                        cursor.execute("""
                            INSERT INTO voucher_deductions (cash_bank_transaction_id, account_id, amount)
                            VALUES (?, ?, ?)
                        """, (voucher_id, deduction['account_id'], deduction['amount']))
                
                    # إنشاء قيد محاسبي
                    self.create_journal_entry(cursor, voucher_id, total_amount, tax_amount, net_amount, deductions_total)
            
                conn.commit()
                QMessageBox.information(self, "نجاح", "تم حفظ الإيصال بنجاح")
                self.load_vouchers()
                self.new_voucher()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في حفظ البيانات: {e}")
            
    def create_journal_entry(self, cursor, voucher_id, total_amount, tax_amount, net_amount, deductions_total):
        # إنشاء رقم قيد جديد - البحث عن آخر رقم قيد
        cursor.execute("SELECT MAX(CAST(entry_number AS INTEGER)) FROM journal_entries")
        result = cursor.fetchone()
        next_entry_number = 1 if result[0] is None else int(result[0]) + 1

        # إدخال القيد الرئيسي
        cursor.execute("""
            INSERT INTO journal_entries 
            (entry_number, entry_date, description, transaction_type_id)
            VALUES (?, ?, ?, ?)
        """, (
            str(next_entry_number),
            self.voucher_date.date().toString("yyyy-MM-dd"),
            self.description.text() or f"إيصال صرف نقدي رقم {self.voucher_number.text()}",
            self.transaction_type.currentData()
        ))

        journal_entry_id = cursor.lastrowid

        # الحصول على حساب الصندوق من الخزينة المحددة
        cursor.execute("SELECT account_id FROM cash_chests WHERE id = ?", (self.cash_chests.currentData(),))
        cash_account_id = cursor.fetchone()[0]

        # الحصول على الحساب المدين
        subsidiary_account_id = self.subsidiary_account.currentData()[0]

        # إضافة حركة الدائن (الصندوق) - المبلغ الصافي
        cursor.execute("""
            INSERT INTO journal_entry_lines 
                (journal_entry_id, account_id, credit, notes, document_type_id, document_number, tax_type_id, cost_center_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                journal_entry_id,
                cash_account_id,
                net_amount,
                f"إيصال صرف نقدي رقم {self.voucher_number.text()} - صرف من الصندوق",
                self.document_type.currentData(),
                self.document_number.text() if self.document_number.text() else None,
                None,  # لا ضريبة على جانب الدائن
                None   # لا مركز تكلفة للصندوق
            ))

        # إضافة حركة المدين (الحساب الرئيسي) - المبلغ الإجمالي
        cursor.execute("""
            INSERT INTO journal_entry_lines 
                (journal_entry_id, account_id, debit, notes, document_type_id, document_number, tax_type_id, cost_center_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                journal_entry_id,
                subsidiary_account_id,
                total_amount,
                f"إيصال صرف نقدي رقم {self.voucher_number.text()}",
                self.document_type.currentData(),
                self.document_number.text() if self.document_number.text() else None,
                self.tax_type.currentData(),
                self.cost_center.currentData()
            ))

        # إضافة حركة الضريبة إذا وجدت (جانب دائن)
        if tax_amount > 0:
            tax_type_id = self.tax_type.currentData()
            if tax_type_id:
                cursor.execute("SELECT tax_account_id FROM tax_types WHERE id = ?", (tax_type_id,))
                tax_account_result = cursor.fetchone()
        
                if tax_account_result and tax_account_result[0]:
                    tax_account_id = tax_account_result[0]
                    cursor.execute("""
                        INSERT INTO journal_entry_lines 
                            (journal_entry_id, account_id, credit, notes, document_type_id, document_number, tax_type_id, cost_center_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            journal_entry_id,
                            tax_account_id,
                            tax_amount,
                            f"إيصال صرف نقدي رقم {self.voucher_number.text()} - ضريبة",
                            self.document_type.currentData(),
                            self.document_number.text() if self.document_number.text() else None,
                            tax_type_id,
                            None  # لا مركز تكلفة للضريبة
                    ))

        # إضافة حركات الخصومات (جانب دائن)
        for deduction in self.additional_deductions:
            cursor.execute("""
                INSERT INTO journal_entry_lines 
                    (journal_entry_id, account_id, credit, notes, document_type_id, document_number, tax_type_id, cost_center_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    journal_entry_id,
                    deduction['account_id'],
                    deduction['amount'],
                    f"إيصال صرف نقدي رقم {self.voucher_number.text()} - {deduction['account_name']}",
                    self.document_type.currentData(),
                    self.document_number.text() if self.document_number.text() else None,
                    None,  # لا ضريبة على الخصومات
                    None   # لا مركز تكلفة للخصومات
            ))

        # ربط القيد المحاسبي بالإيصال
        cursor.execute("""
            UPDATE cash_bank_transactions 
            SET journal_entry_id = ? 
            WHERE id = ?
        """, (journal_entry_id, voucher_id))

    def update_journal_entry(self, cursor, voucher_id):
        # هذه الدالة تحتاج إلى تنفيذ منطق تحديث القيد المحاسبي
        # يمكن تنفيذها لاحقاً حسب الحاجة
        pass

    def edit_voucher(self):
        if not self.current_voucher_id:
            QMessageBox.warning(self, "تحذير", "يرجى تحديد إيصال للتعديل أولاً")
            return
        
        self.save_btn.setText("تحديث")
        self.save_btn.setEnabled(True)

    def delete_voucher(self):
        if not self.current_voucher_id:
            QMessageBox.warning(self, "تحذير", "يرجى تحديد إيصال للحذف أولاً")
            return
        
        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                    "هل أنت متأكد من رغبتك في حذف هذا الإيصال؟",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # الحصول على journal_entry_id المرتبط بالإيصال
                    cursor.execute("SELECT journal_entry_id FROM cash_bank_transactions WHERE id = ?", (self.current_voucher_id,))
                    journal_entry_id = cursor.fetchone()[0]
                    
                    # حذف الخصومات المرتبطة بالإيصال
                    cursor.execute("DELETE FROM voucher_deductions WHERE cash_bank_transaction_id = ?", (self.current_voucher_id,))
                    
                    # حذف الإيصال
                    cursor.execute("DELETE FROM cash_bank_transactions WHERE id = ?", (self.current_voucher_id,))
                    
                    # حذف القيد المحاسبي إذا وجد
                    if journal_entry_id:
                        cursor.execute("DELETE FROM journal_entry_lines WHERE journal_entry_id = ?", (journal_entry_id,))
                        cursor.execute("DELETE FROM journal_entries WHERE id = ?", (journal_entry_id,))
                    
                    conn.commit()
                    QMessageBox.information(self, "نجاح", "تم حذف الإيصال بنجاح")
                    self.load_vouchers()
                    self.new_voucher()
                    
            except sqlite3.Error as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في حذف الإيصال: {e}")

def main():
    app = QApplication(sys.argv)
    window = CashPaymentVoucherApp(DB_PATH)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
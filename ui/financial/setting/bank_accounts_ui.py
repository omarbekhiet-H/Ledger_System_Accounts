# ui/financial/bank_accounts_ui.py

import sqlite3
import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QComboBox, QGroupBox, QGridLayout, QSizePolicy,
    QAbstractItemView, QApplication, QStyle
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QIcon

# =====================================================================
# تصحيح مسار المشروع الجذر لتمكين الاستيراد الصحيح
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..')) 
if project_root not in sys.path:
    sys.path.append(project_root)

# Import necessary managers
from database.manager.financial_lookups_manager import FinancialLookupsManager 
from database.manager.account_manager import AccountManager # لإدارة الحسابات
from database.db_connection import get_financials_db_connection 

# سيتم تهيئة مخطط قاعدة البيانات مباشرةً باستخدام FINANCIALS_SCHEMA_SCRIPT
from database.schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT


class BankAccountsManagementWindow(QWidget):
    def __init__(self, lookup_manager=None, account_manager=None):
        super().__init__()
        self.lookup_manager = lookup_manager if lookup_manager else FinancialLookupsManager(get_financials_db_connection)
        self.account_manager = account_manager if account_manager else AccountManager(get_financials_db_connection)
        self.current_bank_id = None 

        self.setWindowTitle("إدارة الحسابات البنكية")
        self.setLayoutDirection(Qt.RightToLeft)
        QApplication.instance().setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_bank_accounts() 
        self.populate_comboboxes()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("إدارة الحسابات البنكية")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #333;")
        main_layout.addWidget(title_label)

        form_group_box = QGroupBox("بيانات الحساب البنكي")
        form_layout = QGridLayout(form_group_box)
        form_group_box.setLayoutDirection(Qt.RightToLeft)

        self.bank_name_ar_input = QLineEdit()
        self.account_number_input = QLineEdit()
        self.account_combo = QComboBox()
        self.currency_combo = QComboBox()
        
        self.is_active_combo = QComboBox()
        self.is_active_combo.addItem("نشط", 1)
        self.is_active_combo.addItem("غير نشط", 0)


        form_layout.addWidget(QLabel("اسم البنك (عربي):"), 0, 0)
        form_layout.addWidget(self.bank_name_ar_input, 0, 1)
        form_layout.addWidget(QLabel("رقم الحساب البنكي:"), 1, 0)
        form_layout.addWidget(self.account_number_input, 1, 1)
        form_layout.addWidget(QLabel("حساب دليل الحسابات:"), 2, 0)
        form_layout.addWidget(self.account_combo, 2, 1)
        form_layout.addWidget(QLabel("العملة:"), 3, 0)
        form_layout.addWidget(self.currency_combo, 3, 1)
        form_layout.addWidget(QLabel("الحالة:"), 4, 0)
        form_layout.addWidget(self.is_active_combo, 4, 1)

        main_layout.addWidget(form_group_box)

        buttons_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("إضافة")
        self.add_btn.setObjectName("addButton")
        self.add_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        buttons_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("تحديث")
        self.update_btn.setObjectName("updateButton")
        self.update_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogResetButton))
        buttons_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("حذف / تعطيل") 
        self.delete_btn.setObjectName("deleteButton")
        self.delete_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        buttons_layout.addWidget(self.delete_btn)

        self.clear_btn = QPushButton("مسح")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        buttons_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(buttons_layout)

        self.bank_accounts_table = QTableWidget()
        self.bank_accounts_table.setColumnCount(6) # ID, Bank Name, Account Number, Account Name, Currency Code, Is Active
        self.bank_accounts_table.setHorizontalHeaderLabels([
            "المعرف", "اسم البنك", "رقم الحساب", "حساب دليل الحسابات", "العملة", "الحالة"
        ])
        self.bank_accounts_table.setColumnHidden(0, True) # إخفاء عمود المعرف (ID)

        self.bank_accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.bank_accounts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Stretch Bank Name
        
        self.bank_accounts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.bank_accounts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        main_layout.addWidget(self.bank_accounts_table)

        self.add_btn.clicked.connect(self.add_bank_account)
        self.update_btn.clicked.connect(self.update_bank_account)
        self.delete_btn.clicked.connect(self.delete_bank_account) 
        self.clear_btn.clicked.connect(self.clear_form)
        self.bank_accounts_table.itemSelectionChanged.connect(self.display_selected_bank_account)

        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def populate_comboboxes(self):
        # Populate Accounts Combo Box
        self.account_combo.clear()
        self.account_combo.addItem("اختر حساب", None)
        accounts = self.account_manager.get_all_accounts() # جلب جميع الحسابات
        if accounts:
            for acc in accounts:
                self.account_combo.addItem(f"{acc['acc_code']} - {acc['account_name_ar']}", acc['id'])

        # Populate Currencies Combo Box
        self.currency_combo.clear()
        self.currency_combo.addItem("اختر عملة", None)
        currencies = self.lookup_manager.get_all_currencies()
        if currencies:
            for cur in currencies:
                self.currency_combo.addItem(f"{cur['code']} - {cur['name_ar']}", cur['id'])

    def load_bank_accounts(self):
        self.bank_accounts_table.setRowCount(0)
        
        bank_accounts = self.lookup_manager.get_all_bank_accounts()
        
        print(f"Loaded bank accounts: {bank_accounts}") # سطر الطباعة للتصحيح

        if bank_accounts:
            for i, bank_acc in enumerate(bank_accounts):
                self.bank_accounts_table.insertRow(i)
                self.bank_accounts_table.setItem(i, 0, QTableWidgetItem(str(bank_acc['id'])))
                self.bank_accounts_table.setItem(i, 1, QTableWidgetItem(bank_acc['bank_name_ar']))
                self.bank_accounts_table.setItem(i, 2, QTableWidgetItem(bank_acc['account_number']))
                
                # جلب اسم الحساب
                account_name = ""
                if bank_acc['account_id']:
                    account = self.account_manager.get_account_by_id(bank_acc['account_id'])
                    if account:
                        account_name = account['account_name_ar']
                self.bank_accounts_table.setItem(i, 3, QTableWidgetItem(account_name))

                # جلب كود العملة
                currency_code = ""
                if bank_acc['currency_id']:
                    currency = self.lookup_manager.get_currency_by_id(bank_acc['currency_id'])
                    if currency:
                        currency_code = currency['code']
                self.bank_accounts_table.setItem(i, 4, QTableWidgetItem(currency_code))
                
                self.bank_accounts_table.setItem(i, 5, QTableWidgetItem("نشط" if bank_acc['is_active'] == 1 else "غير نشط"))
        self.clear_form()

    def add_bank_account(self):
        bank_name_ar = self.bank_name_ar_input.text().strip()
        account_number = self.account_number_input.text().strip()
        account_id = self.account_combo.currentData()
        currency_id = self.currency_combo.currentData()
        is_active = self.is_active_combo.currentData()

        if not bank_name_ar or not account_number or account_id is None or currency_id is None:
            QMessageBox.warning(self, "بيانات ناقصة", "اسم البنك، رقم الحساب، الحساب، والعملة مطلوبون.")
            return
        
        success = self.lookup_manager.add_bank_account(
            bank_name_ar=bank_name_ar,
            account_number=account_number,
            account_id=account_id,
            currency_id=currency_id,
            is_active=is_active
        )

        if success:
            QMessageBox.information(self, "نجاح", "تمت إضافة الحساب البنكي بنجاح.")
            self.load_bank_accounts()
        # رسائل الخطأ ستظهر من داخل lookup_manager.add_bank_account

    def update_bank_account(self):
        if self.current_bank_id is None:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد حساب بنكي لتعديله.")
            return

        bank_name_ar = self.bank_name_ar_input.text().strip()
        account_number = self.account_number_input.text().strip()
        account_id = self.account_combo.currentData()
        currency_id = self.currency_combo.currentData()
        is_active = self.is_active_combo.currentData()

        if not bank_name_ar or not account_number or account_id is None or currency_id is None:
            QMessageBox.warning(self, "بيانات ناقصة", "اسم البنك، رقم الحساب، الحساب، والعملة مطلوبون.")
            return
        
        data = {
            'bank_name_ar': bank_name_ar,
            'account_number': account_number,
            'account_id': account_id,
            'currency_id': currency_id,
            'is_active': is_active
        }

        success = self.lookup_manager.update_bank_account(self.current_bank_id, data)

        if success:
            QMessageBox.information(self, "نجاح", "تم تحديث الحساب البنكي بنجاح.")
            self.load_bank_accounts()
        # رسائل الخطأ ستظهر من داخل lookup_manager.update_bank_account

    def delete_bank_account(self):
        if self.current_bank_id is None:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد حساب بنكي لحذفه/تعطيله.")
            return
        
        selected_row = self.bank_accounts_table.currentRow()
        if selected_row >= 0:
            bank_name = self.bank_accounts_table.item(selected_row, 1).text()

            reply = QMessageBox.question(self, "تأكيد الحذف/التعطيل", 
                                         f"هل أنت متأكد أنك تريد حذف/تعطيل الحساب البنكي '{bank_name}'؟\n(سيتم تعطيله بدلاً من حذفه فعلياً)",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                success = self.lookup_manager.deactivate_bank_account(self.current_bank_id)
                if success:
                    QMessageBox.information(self, "نجاح", "تم تعطيل الحساب البنكي بنجاح.")
                    self.load_bank_accounts()
                # رسائل الخطأ ستظهر من داخل lookup_manager.deactivate_bank_account
        else:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على معرف الحساب البنكي المحدد.")


    def display_selected_bank_account(self):
        selected_row = self.bank_accounts_table.currentRow()
        if selected_row >= 0:
            self.current_bank_id = int(self.bank_accounts_table.item(selected_row, 0).text())
            bank_acc = self.lookup_manager.get_bank_account_by_id(self.current_bank_id)
            if bank_acc:
                self.bank_name_ar_input.setText(bank_acc['bank_name_ar'])
                self.account_number_input.setText(bank_acc['account_number'])
                
                # تعيين الحساب
                if bank_acc['account_id']:
                    index = self.account_combo.findData(bank_acc['account_id'])
                    if index != -1:
                        self.account_combo.setCurrentIndex(index)
                    else:
                        self.account_combo.setCurrentIndex(0)
                else:
                    self.account_combo.setCurrentIndex(0)

                # تعيين العملة
                if bank_acc['currency_id']:
                    index = self.currency_combo.findData(bank_acc['currency_id'])
                    if index != -1:
                        self.currency_combo.setCurrentIndex(index)
                    else:
                        self.currency_combo.setCurrentIndex(0)
                else:
                    self.currency_combo.setCurrentIndex(0)
                
                index_active = self.is_active_combo.findData(bank_acc['is_active'])
                if index_active != -1:
                    self.is_active_combo.setCurrentIndex(index_active)

                self.add_btn.setEnabled(False)
                self.update_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)
                
                self.account_number_input.setReadOnly(True)
                self.account_number_input.setProperty("readOnly", True) 
        else:
            self.clear_form()

    def clear_form(self):
        self.current_bank_id = None
        self.bank_name_ar_input.clear()
        self.account_number_input.clear()
        self.account_combo.setCurrentIndex(0) 
        self.currency_combo.setCurrentIndex(0) 
        self.is_active_combo.setCurrentIndex(0) 
        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        
        self.account_number_input.setReadOnly(False)
        self.account_number_input.setProperty("readOnly", False) 
        
        self.bank_accounts_table.blockSignals(True) 
        self.bank_accounts_table.clearSelection() 
        self.bank_accounts_table.blockSignals(False) 


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    style_sheet = """
    QWidget {
        font-family: "Segoe UI", "Noto Sans Arabic", "Inter", "Arial", sans-serif;
        font-size: 14px;
        color: #333333;
        background-color: #f8f8f8;
    }

    QMainWindow, QDialog, QGroupBox {
        background-color: #ffffff;
    }

    QPushButton {
        background-color: #007bff;
        color: white;
        border: 1px solid #007bff;
        border-radius: 8px;
        padding: 8px 15px;
        font-size: 14px;
        min-width: 80px;
        font-weight: 500;
        text-align: center; 
        qproperty-iconSize: 16px 16px;
    }
    QPushButton:hover {
        background-color: #0056b3;
        border-color: #0056b3;
    }
    QPushButton:pressed {
        background-color: #004085;
    }

    QPushButton#addButton {
        background-color: #28a745;
        border-color: #28a745;
    }
    QPushButton#addButton:hover {
        background-color: #218838;
        border-color: #1e7e34;
    }

    QPushButton#updateButton {
        background-color: #ffc107;
        border-color: #ffc107;
        color: #333333;
    }
    QPushButton#updateButton:hover {
        background-color: #e0a800;
        border-color: #d39e00;
    }

    QPushButton#deleteButton {
        background-color: #dc3545;
        border-color: #dc3545;
    }
    QPushButton#deleteButton:hover {
        background-color: #c82333;
        border-color: #bd2130;
    }

    QPushButton#clearButton {
        background-color: #17a2b8;
        border-color: #17a2b8;
    }
    QPushButton#clearButton:hover {
        background-color: #138496;
        border-color: #117a8b;
    }


    QLineEdit, QComboBox {
        border: 1px solid #cccccc;
        border-radius: 5px;
        padding: 5px;
        background-color: #ffffff;
    }
    QLineEdit:focus, QComboBox:focus {
        border-color: #007bff;
        outline: none;
    }

    QTableWidget {
        border: 1px solid #dddddd;
        border-radius: 5px;
        background-color: #ffffff;
        alternate-background-color: #f5f5f5;
        selection-background-color: #e0e0e0;
        selection-color: #333333;
        gridline-color: #eeeeee;
    }
    QTableWidget::item {
        padding: 3px 0;
    }
    QTableWidget::item:selected {
        background-color: #e0e0e0;
        color: #333333;
    }
    QHeaderView::section {
        background-color: #e0e0e0;
        padding: 5px;
        border: 1px solid #dddddd;
        font-weight: bold;
        color: #555555;
    }


    QLabel {
        color: #555555;
        font-weight: 500;
    }

    QLineEdit[readOnly="true"] {
        background-color: #e9ecef;
        color: #6c757d;
        border: 1px solid #ced4da;
    }
    """
    app.setStyleSheet(style_sheet)
    
    # <--- تهيئة مخطط قاعدة البيانات فقط، بدون تعبئة بيانات افتراضية
    from database.schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT
    
    try:
        conn = get_financials_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='currencies';")
                table_exists = cursor.fetchone()
                
                if not table_exists:
                    print("Financials DB schema not found. Initializing...")
                    cursor.executescript(FINANCIALS_SCHEMA_SCRIPT)
                    conn.commit()
                    print("Financials DB schema initialized.")
                else:
                    print("Financials DB already exists and schema is present. Skipping initialization.")
            except sqlite3.Error as e:
                QMessageBox.critical(None, "خطأ في قاعدة البيانات", f"فشل التحقق أو تهيئة المخطط: {e}")
                sys.exit(1)
            finally:
                conn.close()
        else:
            QMessageBox.critical(None, "خطأ في الاتصال", "فشل الاتصال بقاعدة البيانات المالية.")
            sys.exit(1)
            
        test_lookup_manager = FinancialLookupsManager(get_financials_db_connection)
        test_account_manager = AccountManager(get_financials_db_connection)
        window = BankAccountsManagementWindow(lookup_manager=test_lookup_manager, account_manager=test_account_manager)
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, "خطأ في تشغيل التطبيق", f"حدث خطأ غير متوقع: {e}")
        sys.exit(1)

# ui/financial/cash_chests_ui.py

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

# =====================================================================
# Helper function to load QSS files
# =====================================================================
def load_qss_file(file_path):
    """Loads a QSS file and returns its content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: QSS file not found at {file_path}")
        return None
    except Exception as e:
        print(f"ERROR: Could not load QSS file {file_path}: {e}")
        return None


class CashChestsManagementWindow(QWidget):
    def __init__(self, lookup_manager=None, account_manager=None):
        super().__init__()
        self.lookup_manager = lookup_manager if lookup_manager else FinancialLookupsManager(get_financials_db_connection)
        self.account_manager = account_manager if account_manager else AccountManager(get_financials_db_connection)
        self.current_chest_id = None

        self.setWindowTitle("إدارة الصناديق النقدية")
        self.setLayoutDirection(Qt.RightToLeft)
        QApplication.instance().setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_cash_chests()
        self.populate_comboboxes()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("إدارة الصناديق النقدية")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        form_group_box = QGroupBox("بيانات الصندوق النقدي")
        form_layout = QGridLayout(form_group_box)
        form_group_box.setLayoutDirection(Qt.RightToLeft)

        self.name_ar_input = QLineEdit()
        self.chest_code_input = QLineEdit()
        self.account_combo = QComboBox()
        self.currency_combo = QComboBox()
        self.is_active_combo = QComboBox()
        self.is_active_combo.addItem("نشط", 1)
        self.is_active_combo.addItem("غير نشط", 0)

    # التعديل هنا: عرض "الاسم (عربي)" و "كود الصندوق" و "حساب دليل الحسابات" في سطر واحد
        form_layout.addWidget(QLabel("الاسم (عربي):"), 0, 0) # تسمية الاسم العربي في العمود 0 من السطر 0
        form_layout.addWidget(self.name_ar_input, 0, 1)      # حقل الاسم العربي في العمود 1 من السطر 0

        form_layout.addWidget(QLabel("كود الصندوق:"), 0, 2)  # تسمية كود الصندوق في العمود 2 من السطر 0
        form_layout.addWidget(self.chest_code_input, 0, 3)    # حقل كود الصندوق في العمود 3 من السطر 0

        form_layout.addWidget(QLabel("حساب دليل الحسابات:"), 0, 4) # تسمية حساب الدليل في العمود 4 من السطر 0
        form_layout.addWidget(self.account_combo, 0, 5)       # حقل حساب الدليل في العمود 5 من السطر 0

    # باقي الكود كما هو، مع تعديل صف إضافة العملة والحالة
    # إضافة العملة والحالة في سطر واحد (الآن سيكون السطر 1 بدلاً من 3 بسبب تغيير ترتيب الحقول العلوية)
        hbox_currency_status = QHBoxLayout()
        hbox_currency_status.addWidget(QLabel("العملة:"))
        hbox_currency_status.addWidget(self.currency_combo)
        hbox_currency_status.addWidget(QLabel("الحالة:"))
        hbox_currency_status.addWidget(self.is_active_combo)
        form_layout.addLayout(hbox_currency_status, 1, 0, 1, 6) # يمتد على 6 أعمدة ليغطي العرض الجديد


        main_layout.addWidget(form_group_box)

        buttons_layout = QHBoxLayout()

        self.add_btn = QPushButton("إضافة")
        self.add_btn.setObjectName("addButton")
        self.add_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        buttons_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("تحديث")
        self.update_btn.setObjectName("updateButton")
        self.update_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        buttons_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("حذف / تعطيل")
        self.delete_btn.setObjectName("deleteButton")
        self.delete_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        buttons_layout.addWidget(self.delete_btn)

        self.clear_btn = QPushButton("مسح")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        buttons_layout.addWidget(self.clear_btn)

        main_layout.addLayout(buttons_layout)

        self.chests_table = QTableWidget()
        self.chests_table.setColumnCount(6) # ID, Name AR, Code, Account Name, Currency Code, Is Active
        self.chests_table.setHorizontalHeaderLabels([
            "المعرف", "الاسم (عربي)", "كود الصندوق", "حساب دليل الحسابات", "العملة", "الحالة"
        ])
        self.chests_table.setColumnHidden(0, True) # إخفاء عمود المعرف (ID)

        self.chests_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.chests_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Stretch Arabic Name
        self.chests_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents) # Chest Code
        self.chests_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch) # Account Name
        self.chests_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # Currency
        self.chests_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # Is Active

        self.chests_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.chests_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        main_layout.addWidget(self.chests_table)

        self.add_btn.clicked.connect(self.add_cash_chest)
        self.update_btn.clicked.connect(self.update_cash_chest)
        self.delete_btn.clicked.connect(self.delete_cash_chest)
        self.clear_btn.clicked.connect(self.clear_form)
        self.chests_table.itemSelectionChanged.connect(self.display_selected_chest)

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

    def load_cash_chests(self):
        self.chests_table.setRowCount(0)

        chests = self.lookup_manager.get_all_cash_chests()

        print(f"Loaded cash chests: {chests}") # سطر الطباعة للتصحيح

        if chests:
            for i, chest in enumerate(chests):
                self.chests_table.insertRow(i)
                self.chests_table.setItem(i, 0, QTableWidgetItem(str(chest['id'])))
                self.chests_table.setItem(i, 1, QTableWidgetItem(chest['name_ar']))
                self.chests_table.setItem(i, 2, QTableWidgetItem(chest['chest_code']))

                # جلب اسم الحساب
                account_name = ""
                if chest['account_id']:
                    account = self.account_manager.get_account_by_id(chest['account_id'])
                    if account:
                        account_name = account['account_name_ar']
                self.chests_table.setItem(i, 3, QTableWidgetItem(account_name))

                # جلب كود العملة
                currency_code = ""
                if chest['currency_id']:
                    currency = self.lookup_manager.get_currency_by_id(chest['currency_id'])
                    if currency:
                        currency_code = currency['code']
                self.chests_table.setItem(i, 4, QTableWidgetItem(currency_code))

                self.chests_table.setItem(i, 5, QTableWidgetItem("نشط" if chest['is_active'] == 1 else "غير نشط"))
        self.clear_form()

    def add_cash_chest(self):
        name_ar = self.name_ar_input.text().strip()
        chest_code = self.chest_code_input.text().strip()
        account_id = self.account_combo.currentData()
        currency_id = self.currency_combo.currentData()
        is_active = self.is_active_combo.currentData()

        if not name_ar or not chest_code or account_id is None or currency_id is None:
            QMessageBox.warning(self, "بيانات ناقصة", "الاسم العربي، كود الصندوق، الحساب، والعملة مطلوبون.")
            return

        success = self.lookup_manager.add_cash_chest(
            name_ar=name_ar,
            chest_code=chest_code,
            account_id=account_id,
            currency_id=currency_id,
            is_active=is_active
        )

        if success:
            QMessageBox.information(self, "نجاح", "تمت إضافة الصندوق النقدي بنجاح.")
            self.load_cash_chests()
        # رسائل الخطأ ستظهر من داخل lookup_manager.add_cash_chest

    def update_cash_chest(self):
        if self.current_chest_id is None:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد صندوق نقدي لتعديله.")
            return

        name_ar = self.name_ar_input.text().strip()
        chest_code = self.chest_code_input.text().strip()
        account_id = self.account_combo.currentData()
        currency_id = self.currency_combo.currentData()
        is_active = self.is_active_combo.currentData()

        if not name_ar or not chest_code or account_id is None or currency_id is None:
            QMessageBox.warning(self, "بيانات ناقصة", "الاسم العربي، كود الصندوق، الحساب، والعملة مطلوبون.")
            return

        data = {
            'name_ar': name_ar,
            'chest_code': chest_code,
            'account_id': account_id,
            'currency_id': currency_id,
            'is_active': is_active
        }

        success = self.lookup_manager.update_cash_chest(self.current_chest_id, data)

        if success:
            QMessageBox.information(self, "نجاح", "تم تحديث الصندوق النقدي بنجاح.")
            self.load_cash_chests()
        # رسائل الخطأ ستظهر من داخل lookup_manager.update_cash_chest

    def delete_cash_chest(self):
        if self.current_chest_id is None:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد صندوق نقدي لحذفه/تعطيله.")
            return

        selected_row = self.chests_table.currentRow()
        if selected_row >= 0:
            chest_name = self.chests_table.item(selected_row, 1).text()

            reply = QMessageBox.question(self, "تأكيد الحذف/التعطيل",
                                         f"هل أنت متأكد أنك تريد حذف/تعطيل الصندوق النقدي '{chest_name}'؟\n(سيتم تعطيله بدلاً من حذفه فعلياً)",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                success = self.lookup_manager.deactivate_cash_chest(self.current_chest_id)
                if success:
                    QMessageBox.information(self, "نجاح", "تم تعطيل الصندوق النقدي بنجاح.")
                    self.load_cash_chests()
                # رسائل الخطأ ستظهر من داخل lookup_manager.deactivate_cash_chest
        else:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على معرف الصندوق المحدد.")


    def display_selected_chest(self):
        selected_row = self.chests_table.currentRow()
        if selected_row >= 0:
            self.current_chest_id = int(self.chests_table.item(selected_row, 0).text())
            chest = self.lookup_manager.get_cash_chest_by_id(self.current_chest_id)
            if chest:
                self.name_ar_input.setText(chest['name_ar'])
                self.chest_code_input.setText(chest['chest_code'])

                # تعيين الحساب
                if chest['account_id']:
                    index = self.account_combo.findData(chest['account_id'])
                    if index != -1:
                        self.account_combo.setCurrentIndex(index)
                    else:
                        self.account_combo.setCurrentIndex(0)
                else:
                    self.account_combo.setCurrentIndex(0)

                # تعيين العملة
                if chest['currency_id']:
                    index = self.currency_combo.findData(chest['currency_id'])
                    if index != -1:
                        self.currency_combo.setCurrentIndex(index)
                    else:
                        self.currency_combo.setCurrentIndex(0)
                else:
                    self.currency_combo.setCurrentIndex(0)

                index_active = self.is_active_combo.findData(chest['is_active'])
                if index_active != -1:
                    self.is_active_combo.setCurrentIndex(index_active)

                self.add_btn.setEnabled(False)
                self.update_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)

                self.chest_code_input.setReadOnly(True)
                self.chest_code_input.setProperty("readOnly", True)
        else:
            self.clear_form()

    def clear_form(self):
        self.current_chest_id = None
        self.name_ar_input.clear()
        self.chest_code_input.clear()
        self.account_combo.setCurrentIndex(0)
        self.currency_combo.setCurrentIndex(0)
        self.is_active_combo.setCurrentIndex(0)
        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

        self.chest_code_input.setReadOnly(False)
        self.chest_code_input.setProperty("readOnly", False)

        self.chests_table.blockSignals(True)
        self.chests_table.clearSelection()
        self.chests_table.blockSignals(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Database initialization
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

    except Exception as e:
        QMessageBox.critical(None, "خطأ في تشغيل التطبيق", f"حدث خطأ غير متوقع أثناء تهيئة التطبيق: {e}")
        sys.exit(1)

    # Load and apply QSS stylesheet
    qss_file_path = os.path.join(project_root, 'ui', 'styles', 'styles.qss')
    app_stylesheet = load_qss_file(qss_file_path)
    if app_stylesheet:
        app.setStyleSheet(app_stylesheet)
        print("DEBUG: Applied DFD-001 stylesheet.")
    else:
        print("WARNING: Failed to load stylesheet. UI might not be consistent.")

    test_lookup_manager = FinancialLookupsManager(get_financials_db_connection)
    test_account_manager = AccountManager(get_financials_db_connection)
    window = CashChestsManagementWindow(lookup_manager=test_lookup_manager, account_manager=test_account_manager)
    window.showMaximized()
    sys.exit(app.exec_())

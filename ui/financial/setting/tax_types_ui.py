# ui/financial/tax_types_ui.py

import sqlite3
import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QAbstractItemView, QGroupBox, QGridLayout, QSizePolicy, QComboBox, QApplication,
    QStyle
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QDoubleValidator, QIcon

# =====================================================================
# تصحيح مسار المشروع الجذر لتمكين الاستيراد الصحيح
# تم التعديل هنا: الصعود مستويين بدلاً من مستوى واحد (لأن الملف في ui/financial/)
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import necessary managers
from database.manager.financial_lookups_manager import FinancialLookupsManager
from database.db_connection import get_financials_db_connection
from database.manager.account_manager import AccountManager

# سيتم تهيئة مخطط قاعدة البيانات مباشرةً باستخدام FINANCIALS_SCHEMA_SCRIPT
from database.schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT

# =====================================================================
# Helper function to load QSS files - ADDED for consistency
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

class TaxTypesManagementWindow(QWidget):
    def __init__(self, lookup_manager=None, account_manager=None):
        super().__init__()
        self.lookup_manager = lookup_manager if lookup_manager else FinancialLookupsManager(get_financials_db_connection)
        self.accounts_manager = account_manager if account_manager else AccountManager(get_financials_db_connection)
        self.current_tax_type_id = None

        self.setWindowTitle("إدارة أنواع الضرائب")
        self.setLayoutDirection(Qt.RightToLeft)
        QApplication.instance().setLayoutDirection(Qt.RightToLeft) # تطبيق الاتجاه على التطبيق بالكامل
        self.init_ui()
        self.load_tax_types()
        self.load_accounts_into_combo()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("إدارة أنواع الضرائب")
        # MODIFIED: Removed direct font and stylesheet setting to allow QSS to control styling
        # title_label.setFont(QFont("Arial", 16, QFont.Bold))
        # title_label.setStyleSheet("color: #333;")
        # ADDED: Set object name for QSS styling
        title_label.setObjectName("windowTitleLabel") # A specific object name for the title label
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        form_group = QGroupBox("تفاصيل نوع الضريبة")
        form_layout = QGridLayout(form_group)
        form_group.setLayoutDirection(Qt.RightToLeft)

        self.code_input = QLineEdit()
        self.name_ar_input = QLineEdit()
        self.name_en_input = QLineEdit()
        self.rate_input = QLineEdit()
        self.rate_input.setValidator(QDoubleValidator(0.0, 100.0, 2))
        self.tax_account_combo = QComboBox()
        self.tax_account_combo.addItem("اختر حساب الضريبة", userData=None)

        self.is_active_combo = QComboBox()
        self.is_active_combo.addItem("نشط", 1)
        self.is_active_combo.addItem("غير نشط", 0)

        # التنسيق البصري: أول ثلاثة حقول في سطر واحد، والباقي في سطر آخر
        # السطر 0 (الصف الأول): "رمز الضريبة", "الاسم (عربي)", "الاسم (إنجليزي)"
        form_layout.addWidget(QLabel("رمز الضريبة:"), 0, 0)
        form_layout.addWidget(self.code_input, 0, 1)

        form_layout.addWidget(QLabel("الاسم (عربي):"), 0, 2)
        form_layout.addWidget(self.name_ar_input, 0, 3)

        form_layout.addWidget(QLabel("الاسم (إنجليزي):"), 0, 4)
        form_layout.addWidget(self.name_en_input, 0, 5)

        # السطر 1 (الصف الثاني): "النسبة", "حساب الضريبة", "الحالة"
        form_layout.addWidget(QLabel("النسبة (%):"), 1, 0)
        form_layout.addWidget(self.rate_input, 1, 1)

        form_layout.addWidget(QLabel("حساب الضريبة:"), 1, 2)
        form_layout.addWidget(self.tax_account_combo, 1, 3)

        form_layout.addWidget(QLabel("الحالة:"), 1, 4)
        form_layout.addWidget(self.is_active_combo, 1, 5)

        main_layout.addWidget(form_group)

        buttons_layout = QHBoxLayout()

        self.add_btn = QPushButton("إضافة")
        self.add_btn.setObjectName("addButton")
        # MODIFIED: Changed icon to match cost_centers_ui.py
        self.add_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        buttons_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("تحديث")
        self.update_btn.setObjectName("updateButton")
        # MODIFIED: Changed icon to match cost_centers_ui.py
        self.update_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        buttons_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("حذف / تعطيل")
        self.delete_btn.setObjectName("deleteButton")
        # MODIFIED: Changed icon to match cost_centers_ui.py
        self.delete_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        buttons_layout.addWidget(self.delete_btn)

        self.clear_btn = QPushButton("مسح")
        self.clear_btn.setObjectName("clearButton")
        # MODIFIED: Changed icon to match cost_centers_ui.py
        self.clear_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        buttons_layout.addWidget(self.clear_btn)

        main_layout.addLayout(buttons_layout)

        self.tax_types_table = QTableWidget()
        self.tax_types_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tax_types_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tax_types_table.setAlternatingRowColors(True)
        self.tax_types_table.setColumnCount(7)
        self.tax_types_table.setHorizontalHeaderLabels([
            "المعرف", "الرمز", "الاسم (عربي)", "الاسم (إنجليزي)", "النسبة (%)", "حساب الضريبة", "الحالة"
        ])
        self.tax_types_table.setColumnHidden(0, True)

        # MODIFIED: Table header resize mode to match cost_centers_ui.py
        self.tax_types_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents) # Default for all
        self.tax_types_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # الرمز
        self.tax_types_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # الاسم العربي
        self.tax_types_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch) # الاسم الإنجليزي
        self.tax_types_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # النسبة (%)
        self.tax_types_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch) # حساب الضريبة
        self.tax_types_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents) # الحالة

        self.tax_types_table.clicked.connect(self.item_selected) # Keep clicked for consistency
        # Assuming cost_centers_table uses itemSelectionChanged, it's good to use for consistency
        # self.tax_types_table.itemSelectionChanged.connect(self.item_selected) # Alternative for consistency

        main_layout.addWidget(self.tax_types_table)

        self.add_btn.clicked.connect(self.add_tax_type) # Connect signals
        self.update_btn.clicked.connect(self.update_tax_type)
        self.delete_btn.clicked.connect(self.delete_tax_type)
        self.clear_btn.clicked.connect(self.clear_form)
        self.tax_types_table.itemSelectionChanged.connect(self.item_selected) # Using itemSelectionChanged for consistency


        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def load_accounts_into_combo(self):
        self.tax_account_combo.clear()
        self.tax_account_combo.addItem("اختر حساب الضريبة", userData=None)
        accounts = self.accounts_manager.get_all_accounts()
        self.accounts_map = {}
        if accounts:
            for account in accounts:
                account_name = account['account_name_ar']
                account_id = account['id']
                self.tax_account_combo.addItem(account_name, userData=account_id)
                self.accounts_map[account_name] = account_id


    def load_tax_types(self):
        self.tax_types_table.setRowCount(0)
        tax_types = self.lookup_manager.get_all_tax_types()

        if not isinstance(tax_types, list):
            QMessageBox.critical(self, "خطأ في البيانات", "فشل جلب أنواع الضرائب. الرجاء التحقق من قاعدة البيانات.")
            return

        for row_idx, tax_type in enumerate(tax_types):
            self.tax_types_table.insertRow(row_idx)
            self.tax_types_table.setItem(row_idx, 0, QTableWidgetItem(str(tax_type['id'])))
            self.tax_types_table.setItem(row_idx, 1, QTableWidgetItem(tax_type['code']))
            self.tax_types_table.setItem(row_idx, 2, QTableWidgetItem(tax_type['name_ar']))
            self.tax_types_table.setItem(row_idx, 3, QTableWidgetItem(tax_type['name_en'] if tax_type['name_en'] else ""))
            self.tax_types_table.setItem(row_idx, 4, QTableWidgetItem(str(tax_type['rate'])))

            tax_account_name = ""
            if tax_type['tax_account_id']:
                account = self.accounts_manager.get_account_by_id(tax_type['tax_account_id'])
                if account:
                    tax_account_name = account['account_name_ar']
            self.tax_types_table.setItem(row_idx, 5, QTableWidgetItem(tax_account_name))
            self.tax_types_table.setItem(row_idx, 6, QTableWidgetItem("نشط" if tax_type['is_active'] == 1 else "غير نشط"))

        self.clear_form()

    def add_tax_type(self):
        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()
        rate_str = self.rate_input.text().strip()

        tax_account_id = self.tax_account_combo.currentData()
        is_active = self.is_active_combo.currentData()

        if not code or not name_ar or not rate_str:
            QMessageBox.warning(self, "إدخال ناقص", "الرجاء إدخال رمز الضريبة، الاسم (عربي)، والنسبة.")
            return

        try:
            rate = float(rate_str)
        except ValueError:
            QMessageBox.warning(self, "إدخال غير صالح", "الرجاء إدخال نسبة الضريبة كرقم صحيح أو عشري.")
            return

        existing_tax = self.lookup_manager.get_tax_type_by_code(code)
        if existing_tax:
            QMessageBox.warning(self, "رمز مكرر", "رمز الضريبة هذا موجود بالفعل.")
            return

        success = self.lookup_manager.add_tax_type(code, name_ar, rate, name_en if name_en else None, tax_account_id, is_active)
        if success:
            QMessageBox.information(self, "نجاح", "تمت إضافة نوع الضريبة بنجاح.")
            self.load_tax_types()
        else:
            QMessageBox.critical(self, "خطأ", "فشل إضافة نوع الضريبة.")

    def update_tax_type(self):
        selected_row = self.tax_types_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد نوع ضريبة لتحديثه.")
            return

        tax_id = int(self.tax_types_table.item(selected_row, 0).text())
        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()
        rate_str = self.rate_input.text().strip()

        tax_account_id = self.tax_account_combo.currentData()
        is_active = self.is_active_combo.currentData()

        if not code or not name_ar or not rate_str:
            QMessageBox.warning(self, "إدخال ناقص", "الرجاء إدخال رمز الضريبة، الاسم (عربي)، والنسبة.")
            return

        try:
            rate = float(rate_str)
        except ValueError:
            QMessageBox.warning(self, "إدخال غير صالح", "الرجاء إدخال نسبة الضريبة كرقم صحيح أو عشري.")
            return

        existing_tax = self.lookup_manager.get_tax_type_by_code(code)
        if existing_tax and existing_tax['id'] != tax_id:
            QMessageBox.warning(self, "رمز مكرر", "رمز الضريبة هذا موجود بالفعل لنوع ضريبة آخر.")
            return

        data = {
            'code': code,
            'name_ar': name_ar,
            'name_en': name_en if name_en else None,
            'rate': rate,
            'tax_account_id': tax_account_id,
            'is_active': is_active
        }
        success = self.lookup_manager.update_tax_type(tax_id, data)
        if success:
            QMessageBox.information(self, "نجاح", "تم تعديل نوع الضريبة بنجاح.")
            self.load_tax_types()
        else:
            QMessageBox.critical(self, "خطأ", "فشل تعديل نوع الضريبة.")

    def delete_tax_type(self):
        selected_row = self.tax_types_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد نوع ضريبة لحذفه/تعطيله.")
            return

        tax_id = int(self.tax_types_table.item(selected_row, 0).text())
        tax_name = self.tax_types_table.item(selected_row, 2).text()

        reply = QMessageBox.question(self, "تأكيد الحذف/التعطيل",
                                     f"هل أنت متأكد أنك تريد حذف/تعطيل نوع الضريبة '{tax_name}'؟\n(سيتم تعطيله فعلياً)",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if self.lookup_manager.deactivate_tax_type(tax_id):
                QMessageBox.information(self, "نجاح", "تم تعطيل نوع الضريبة بنجاح.")
                self.load_tax_types()
            else:
                QMessageBox.critical(self, "خطأ", "فشل تعطيل نوع الضريبة. تحقق من السجلات.")

    def item_selected(self):
        selected_row = self.tax_types_table.currentRow()
        if selected_row >= 0:
            tax_id = int(self.tax_types_table.item(selected_row, 0).text())
            tax_type = self.lookup_manager.get_tax_type_by_id(tax_id)
            if tax_type:
                self.current_tax_type_id = tax_id
                self.code_input.setText(tax_type['code'])
                self.name_ar_input.setText(tax_type['name_ar'])
                self.name_en_input.setText(tax_type['name_en'] if tax_type['name_en'] else "")
                self.rate_input.setText(str(tax_type['rate']))

                if tax_type['tax_account_id']:
                    account = self.accounts_manager.get_account_by_id(tax_type['tax_account_id'])
                    if account:
                        index = self.tax_account_combo.findData(account['id'])
                        if index != -1:
                            self.tax_account_combo.setCurrentIndex(index)
                        else:
                            self.tax_account_combo.setCurrentIndex(0)
                    else:
                        self.tax_account_combo.setCurrentIndex(0)
                else:
                    self.tax_account_combo.setCurrentIndex(0)

                index_active = self.is_active_combo.findData(tax_type['is_active'])
                if index_active != -1:
                    self.is_active_combo.setCurrentIndex(index_active)

                self.add_btn.setEnabled(False)
                self.update_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)

                self.code_input.setReadOnly(True)
                self.code_input.setProperty("readOnly", True)
        else:
            self.clear_form()

    def clear_form(self):
        self.current_tax_type_id = None
        self.code_input.clear()
        self.name_ar_input.clear()
        self.name_en_input.clear()
        self.rate_input.clear()
        self.tax_account_combo.setCurrentIndex(0)
        self.is_active_combo.setCurrentIndex(0)
        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

        self.code_input.setReadOnly(False)
        self.code_input.setProperty("readOnly", False)

        self.tax_types_table.blockSignals(True)
        self.tax_types_table.clearSelection()
        self.tax_types_table.blockSignals(False)


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

    # Load and apply QSS stylesheet - MODIFIED to load from external file for consistency
    qss_file_path = os.path.join(project_root, 'ui', 'styles', 'styles.qss')
    app_stylesheet = load_qss_file(qss_file_path)
    if app_stylesheet:
        app.setStyleSheet(app_stylesheet)
        print("DEBUG: Applied stylesheet.")
    else:
        print("WARNING: Failed to load stylesheet. UI might not be consistent.")

    test_lookup_manager = FinancialLookupsManager(get_financials_db_connection)
    test_account_manager = AccountManager(get_financials_db_connection)
    window = TaxTypesManagementWindow(lookup_manager=test_lookup_manager, account_manager=test_account_manager)
    window.showMaximized() # MODIFIED: show maximized for consistency
    sys.exit(app.exec_())
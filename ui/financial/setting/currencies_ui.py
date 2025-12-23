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
from PyQt5.QtGui import QFont, QColor, QDoubleValidator, QIcon

# =====================================================================
# تصحيح مسار المشروع الجذر لتمكين الاستيراد الصحيح
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import necessary managers
from database.manager.financial_lookups_manager import FinancialLookupsManager
from database.db_connection import get_financials_db_connection

# سيتم تهيئة مخطط قاعدة البيانات مباشرةً باستخدام FINANCIALS_SCHEMA_SCRIPT
from database.schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT

# =====================================================================
# Helper function to load QSS files (moved here for general use)
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


class CurrenciesManagementWindow(QWidget):
    def __init__(self, lookup_manager=None):
        super().__init__()
        self.lookup_manager = lookup_manager if lookup_manager else FinancialLookupsManager(get_financials_db_connection)
        self.current_currency_id = None

        self.setWindowTitle("إدارة العملات")
        self.setLayoutDirection(Qt.RightToLeft)
        QApplication.instance().setLayoutDirection(Qt.RightToLeft) # Apply RTL to the whole application
        self.init_ui()
        self.load_currencies()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("إدارة العملات")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        form_group_box = QGroupBox("بيانات العملة")
        form_layout = QGridLayout(form_group_box)
        form_group_box.setLayoutDirection(Qt.RightToLeft)

        self.name_ar_input = QLineEdit()
        self.name_en_input = QLineEdit()
        self.code_input = QLineEdit()
        self.symbol_input = QLineEdit()
        self.exchange_rate_input = QLineEdit()
        self.exchange_rate_input.setValidator(QDoubleValidator(0.01, 1000000.00, 2))

        self.is_active_combo = QComboBox()
        self.is_active_combo.addItem("نشط", 1)
        self.is_active_combo.addItem("غير نشط", 0)

        # أول ثلاثة حقول في سطر واحد (السطر 0)
        form_layout.addWidget(QLabel("الاسم (عربي):"), 0, 0) # تسمية الاسم العربي في العمود 0 من السطر 0
        form_layout.addWidget(self.name_ar_input, 0, 1)      # حقل الاسم العربي في العمود 1 من السطر 0

        form_layout.addWidget(QLabel("الاسم (إنجليزي):"), 0, 2) # تسمية الاسم الإنجليزي في العمود 2 من السطر 0
        form_layout.addWidget(self.name_en_input, 0, 3)      # حقل الاسم الإنجليزي في العمود 3 من السطر 0

        form_layout.addWidget(QLabel("الكود:"), 0, 4) # تسمية الكود في العمود 4 من السطر 0
        form_layout.addWidget(self.code_input, 0, 5)          # حقل الكود في العمود 5 من السطر 0

        # باقي الحقول في سطر واحد (السطر 1)
        form_layout.addWidget(QLabel("الرمز:"), 1, 0) # تسمية الرمز في العمود 0 من السطر 1
        form_layout.addWidget(self.symbol_input, 1, 1)      # حقل الرمز في العمود 1 من السطر 1

        form_layout.addWidget(QLabel("سعر الصرف (مقابل العملة الأساسية):"), 1, 2) # تسمية سعر الصرف في العمود 2 من السطر 1
        form_layout.addWidget(self.exchange_rate_input, 1, 3) # حقل سعر الصرف في العمود 3 من السطر 1

        form_layout.addWidget(QLabel("الحالة:"), 1, 4) # تسمية الحالة في العمود 4 من السطر 1
        form_layout.addWidget(self.is_active_combo, 1, 5)     # حقل الحالة في العمود 5 من السطر 1


        main_layout.addWidget(form_group_box)

        buttons_layout = QHBoxLayout()

        self.add_btn = QPushButton("إضافة")
        self.add_btn.setObjectName("addButton") # Set object name for QSS
        self.add_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton)) # Add icon
        buttons_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("تحديث")
        self.update_btn.setObjectName("updateButton") # Set object name for QSS
        self.update_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton)) # Add icon
        buttons_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("حذف / تعطيل")
        self.delete_btn.setObjectName("deleteButton") # Set object name for QSS
        self.delete_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton)) # Add icon
        buttons_layout.addWidget(self.delete_btn)

        self.clear_btn = QPushButton("مسح")
        self.clear_btn.setObjectName("clearButton") # Set object name for QSS
        self.clear_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload)) # Add icon
        buttons_layout.addWidget(self.clear_btn)

        main_layout.addLayout(buttons_layout)

        self.currencies_table = QTableWidget()
        self.currencies_table.setColumnCount(7) 
        self.currencies_table.setHorizontalHeaderLabels([
            "المعرف", "الاسم (عربي)", "الاسم (إنجليزي)", "الكود", "الرمز", "سعر الصرف", "الحالة"
        ])
        self.currencies_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.currencies_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # الاسم العربي
        self.currencies_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # الاسم الإنجليزي
        self.currencies_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) # الكود
        self.currencies_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # الرمز
        self.currencies_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch) # سعر الصرف
        self.currencies_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents) # الحالة
        main_layout.addWidget(self.currencies_table)

        self.add_btn.clicked.connect(self.add_currency)
        self.update_btn.clicked.connect(self.update_currency)
        self.delete_btn.clicked.connect(self.delete_currency)
        self.clear_btn.clicked.connect(self.clear_form)
        self.currencies_table.itemSelectionChanged.connect(self.display_selected_currency)

        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def load_currencies(self):
        self.currencies_table.setRowCount(0)
        currencies = self.lookup_manager.get_all_currencies()
        if currencies:
            for i, curr in enumerate(currencies):
                self.currencies_table.insertRow(i)
                self.currencies_table.setItem(i, 0, QTableWidgetItem(str(curr['id'])))
                self.currencies_table.setItem(i, 1, QTableWidgetItem(curr['name_ar']))
                self.currencies_table.setItem(i, 2, QTableWidgetItem(curr['name_en']))
                self.currencies_table.setItem(i, 3, QTableWidgetItem(curr['code']))
                self.currencies_table.setItem(i, 4, QTableWidgetItem(curr['symbol']))
                self.currencies_table.setItem(i, 5, QTableWidgetItem(f"{curr['exchange_rate']:.2f}"))
                self.currencies_table.setItem(i, 6, QTableWidgetItem("نشط" if curr['is_active'] == 1 else "غير نشط"))

    def add_currency(self):
        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()
        code = self.code_input.text().strip()
        symbol = self.symbol_input.text().strip()
        exchange_rate_text = self.exchange_rate_input.text().strip()
        is_active = self.is_active_combo.currentData()

        if not name_ar or not code or not exchange_rate_text:
            QMessageBox.warning(self, "حقول فارغة", "الرجاء ملء حقول الاسم (عربي) والكود وسعر الصرف.")
            return
        
        try:
            exchange_rate = float(exchange_rate_text)
            if exchange_rate <= 0:
                QMessageBox.warning(self, "مدخلات غير صالحة", "سعر الصرف يجب أن يكون رقماً موجباً أكبر من صفر.")
                return
        except ValueError:
            QMessageBox.warning(self, "مدخلات غير صالحة", "الرجاء إدخال قيمة رقمية صحيحة لسعر الصرف.")
            return

        if self.lookup_manager.add_currency(name_ar, name_en, code, symbol, exchange_rate, is_active):
            QMessageBox.information(self, "نجاح", "تم إضافة العملة بنجاح.")
            self.load_currencies()
            self.clear_form()
        else:
            QMessageBox.critical(self, "خطأ", "فشل إضافة العملة. قد يكون الكود موجوداً بالفعل.")

    def update_currency(self):
        if self.current_currency_id is None:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد عملة لتعديلها.")
            return

        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()
        code = self.code_input.text().strip()
        symbol = self.symbol_input.text().strip()
        exchange_rate_text = self.exchange_rate_input.text().strip()
        is_active = self.is_active_combo.currentData()

        if not name_ar or not code or not exchange_rate_text:
            QMessageBox.warning(self, "حقول فارغة", "الرجاء ملء حقول الاسم (عربي) والكود وسعر الصرف.")
            return
        
        try:
            exchange_rate = float(exchange_rate_text)
            if exchange_rate <= 0:
                QMessageBox.warning(self, "مدخلات غير صالحة", "سعر الصرف يجب أن يكون رقماً موجباً أكبر من صفر.")
                return
        except ValueError:
            QMessageBox.warning(self, "مدخلات غير صالحة", "الرجاء إدخال قيمة رقمية صحيحة لسعر الصرف.")
            return

        if self.lookup_manager.update_currency(self.current_currency_id, name_ar, name_en, code, symbol, exchange_rate, is_active):
            QMessageBox.information(self, "نجاح", "تم تحديث العملة بنجاح.")
            self.load_currencies()
            self.clear_form()
        else:
            QMessageBox.critical(self, "خطأ", "فشل تحديث العملة. قد يكون الكود موجوداً بالفعل.")

    def delete_currency(self):
        if self.current_currency_id is None:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد عملة لحذفها/تعطيلها.")
            return

        reply = QMessageBox.question(self, "تأكيد الحذف/التعطيل", "هل أنت متأكد أنك تريد حذف/تعطيل هذه العملة؟",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.lookup_manager.delete_currency(self.current_currency_id):
                QMessageBox.information(self, "نجاح", "تم حذف العملة بنجاح.")
                self.load_currencies()
                self.clear_form()
            else:
                QMessageBox.critical(self, "خطأ", "فشل حذف العملة. قد تكون مرتبطة بسجلات أخرى.")

    def clear_form(self):
        self.name_ar_input.clear()
        self.name_en_input.clear()
        self.code_input.clear()
        self.symbol_input.clear()
        self.exchange_rate_input.clear()
        self.is_active_combo.setCurrentIndex(self.is_active_combo.findData(1)) # Reset to "Active"
        self.current_currency_id = None
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.add_btn.setEnabled(True)
        self.currencies_table.clearSelection()

    def display_selected_currency(self):
        selected_items = self.currencies_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            self.current_currency_id = int(self.currencies_table.item(row, 0).text())
            self.name_ar_input.setText(self.currencies_table.item(row, 1).text())
            self.name_en_input.setText(self.currencies_table.item(row, 2).text())
            self.code_input.setText(self.currencies_table.item(row, 3).text())
            self.symbol_input.setText(self.currencies_table.item(row, 4).text())
            self.exchange_rate_input.setText(self.currencies_table.item(row, 5).text())

            is_active_text = self.currencies_table.item(row, 6).text()
            if is_active_text == "نشط":
                self.is_active_combo.setCurrentIndex(self.is_active_combo.findData(1))
            else:
                self.is_active_combo.setCurrentIndex(self.is_active_combo.findData(0))

            self.update_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            self.add_btn.setEnabled(False)
        else:
            self.clear_form()


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
    window = CurrenciesManagementWindow(lookup_manager=test_lookup_manager)
    window.showMaximized()
    sys.exit(app.exec_())
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


class DocumentTypesManagementWindow(QWidget):
    def __init__(self, lookup_manager=None):
        super().__init__()
        self.lookup_manager = lookup_manager if lookup_manager else FinancialLookupsManager(get_financials_db_connection)
        self.current_document_type_id = None

        self.setWindowTitle("إدارة أنواع المستندات")
        self.setLayoutDirection(Qt.RightToLeft)
        QApplication.instance().setLayoutDirection(Qt.RightToLeft) # Apply RTL to the whole application
        self.init_ui()
        self.load_document_types()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("إدارة أنواع المستندات")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        form_group_box = QGroupBox("بيانات نوع المستند")
        form_layout = QGridLayout(form_group_box)
        form_group_box.setLayoutDirection(Qt.RightToLeft)

        self.name_ar_input = QLineEdit()
        self.name_en_input = QLineEdit()
        
        self.is_active_combo = QComboBox()
        self.is_active_combo.addItem("نشط", 1)
        self.is_active_combo.addItem("غير نشط", 0)

        form_layout.addWidget(QLabel("الاسم (عربي):"), 0, 0)
        form_layout.addWidget(self.name_ar_input, 0, 1)
       
        form_layout.addWidget(QLabel("الاسم (إنجليزي):"), 0, 2)
        form_layout.addWidget(self.name_en_input, 0, 3)
       
        form_layout.addWidget(QLabel("الحالة:"), 0, 4)
        form_layout.addWidget(self.is_active_combo, 0, 5)

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

        self.document_types_table = QTableWidget()
        self.document_types_table.setColumnCount(4) # ID, Name AR, Name EN, Is Active
        self.document_types_table.setHorizontalHeaderLabels([
            "المعرف", "الاسم (عربي)", "الاسم (إنجليزي)", "الحالة"
        ])
        self.document_types_table.setColumnHidden(0, True) # Hide ID column
        self.document_types_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.document_types_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Stretch Arabic Name
        self.document_types_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # Stretch English Name
        self.document_types_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) # حالة
        self.document_types_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.document_types_table.setEditTriggers(QAbstractItemView.NoEditTriggers)


        main_layout.addWidget(self.document_types_table)


        self.add_btn.clicked.connect(self.add_document_type)
        self.update_btn.clicked.connect(self.update_document_type)
        self.delete_btn.clicked.connect(self.delete_document_type)
        self.clear_btn.clicked.connect(self.clear_form)
        self.document_types_table.itemSelectionChanged.connect(self.display_selected_document_type)


        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def load_document_types(self):
        self.document_types_table.setRowCount(0)
        document_types = self.lookup_manager.get_all_document_types()
        if document_types:
            for i, dt in enumerate(document_types):
                self.document_types_table.insertRow(i)
                self.document_types_table.setItem(i, 0, QTableWidgetItem(str(dt['id'])))
                self.document_types_table.setItem(i, 1, QTableWidgetItem(dt['name_ar']))
                self.document_types_table.setItem(i, 2, QTableWidgetItem(dt['name_en']))
                self.document_types_table.setItem(i, 3, QTableWidgetItem("نشط" if dt['is_active'] == 1 else "غير نشط"))

    def add_document_type(self):
        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()
        is_active = self.is_active_combo.currentData()

        if not name_ar:
            QMessageBox.warning(self, "حقول فارغة", "الرجاء ملء حقل الاسم (عربي).")
            return

        if self.lookup_manager.add_document_type(name_ar, name_en, is_active):
            QMessageBox.information(self, "نجاح", "تم إضافة نوع المستند بنجاح.")
            self.load_document_types()
            self.clear_form()
        else:
            QMessageBox.critical(self, "خطأ", "فشل إضافة نوع المستند. قد يكون الاسم موجوداً بالفعل.")

    def update_document_type(self):
        if self.current_document_type_id is None:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد نوع مستند لتعديله.")
            return

        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()
        is_active = self.is_active_combo.currentData()

        if not name_ar:
            QMessageBox.warning(self, "حقول فارغة", "الرجاء ملء حقل الاسم (عربي).")
            return

        if self.lookup_manager.update_document_type(self.current_document_type_id, name_ar, name_en, is_active):
            QMessageBox.information(self, "نجاح", "تم تحديث نوع المستند بنجاح.")
            self.load_document_types()
            self.clear_form()
        else:
            QMessageBox.critical(self, "خطأ", "فشل تحديث نوع المستند. قد يكون الاسم موجوداً بالفعل.")

    def delete_document_type(self):
        if self.current_document_type_id is None:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد نوع مستند لحذفه/تعطيله.")
            return

        reply = QMessageBox.question(self, "تأكيد الحذف/التعطيل", "هل أنت متأكد أنك تريد حذف/تعطيل نوع المستند هذا؟",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.lookup_manager.delete_document_type(self.current_document_type_id):
                QMessageBox.information(self, "نجاح", "تم حذف نوع المستند بنجاح.")
                self.load_document_types()
                self.clear_form()
            else:
                QMessageBox.critical(self, "خطأ", "فشل حذف نوع المستند. قد يكون مرتبطًا بسجلات أخرى.")

    def clear_form(self):
        self.name_ar_input.clear()
        self.name_en_input.clear()
        self.is_active_combo.setCurrentIndex(self.is_active_combo.findData(1)) # Reset to "Active"
        self.current_document_type_id = None
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.add_btn.setEnabled(True)
        self.document_types_table.clearSelection()

    def display_selected_document_type(self):
        selected_items = self.document_types_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            self.current_document_type_id = int(self.document_types_table.item(row, 0).text())
            self.name_ar_input.setText(self.document_types_table.item(row, 1).text())
            self.name_en_input.setText(self.document_types_table.item(row, 2).text())
            
            is_active_text = self.document_types_table.item(row, 3).text()
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
    window = DocumentTypesManagementWindow(lookup_manager=test_lookup_manager)
    window.showMaximized()
    sys.exit(app.exec_())
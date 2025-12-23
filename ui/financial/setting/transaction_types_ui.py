# ui/financial/transaction_types_ui.py

import sqlite3
import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QComboBox, QGroupBox, QGridLayout,
    QSizePolicy, QAbstractItemView, QDialog, QFormLayout, QAction, QMenu, QStyle
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

# =====================================================================
# تصحيح مسار المشروع الجذر لتمكين الاستيراد الصحيح
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import necessary managers
from database.db_connection import get_financials_db_connection
from database.manager.db_schema_manager import DBSchemaManager

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

# =====================================================================
# 1. TransactionTypeDBManager: فئة لإدارة التفاعل مع قاعدة البيانات
# =====================================================================
class TransactionTypeDBManager:
    def __init__(self):
        pass

    def _execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """Helper function to execute SQL queries."""
        conn = None
        try:
            conn = get_financials_db_connection()
            if conn is None:
                QMessageBox.critical(None, "خطأ في الاتصال", "فشل الاتصال بقاعدة البيانات المالية.")
                return None

            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()

            if fetch_one:
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
            elif fetch_all:
                rows = cursor.fetchall()
                if rows:
                    columns = [description[0] for description in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
                return []
            return True # For insert/update/delete operations
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ في قاعدة البيانات", f"حدث خطأ في قاعدة البيانات: {e}")
            print(f"Database error: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_all_transaction_types(self):
        """Fetch all transaction types."""
        #query = "SELECT id, code, name_ar, name_en, description, is_active FROM transaction_types ORDER BY name_ar"
        query = "SELECT id, code, name_ar, name_en, description, is_active FROM transaction_types WHERE is_active = 1 ORDER BY name_ar"
        return self._execute_query(query, fetch_all=True)

    def get_transaction_type_by_id(self, type_id):
        """Fetch a transaction type by ID."""
        query = "SELECT id, code, name_ar, name_en, description, is_active FROM transaction_types WHERE id = ?"
        return self._execute_query(query, (type_id,), fetch_one=True)

    def get_transaction_type_by_code(self, code):
        """Fetch a transaction type by code."""
        query = "SELECT id FROM transaction_types WHERE code = ? COLLATE NOCASE"
        return self._execute_query(query, (code,), fetch_one=True)

    def get_transaction_type_by_name_ar(self, name_ar):
        """Fetch a transaction type by Arabic name."""
        query = "SELECT id FROM transaction_types WHERE name_ar = ?"
        return self._execute_query(query, (name_ar,), fetch_one=True)

    def add_transaction_type(self, code, name_ar, name_en, description, is_active):
        """Add a new transaction type."""
        query = """
            INSERT INTO transaction_types (code, name_ar, name_en, description, is_active)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (code, name_ar, name_en, description, is_active)
        return self._execute_query(query, params)

    def update_transaction_type(self, type_id, code, name_ar, name_en, description, is_active):
        """Update an existing transaction type."""
        query = """
            UPDATE transaction_types
            SET code = ?, name_ar = ?, name_en = ?, description = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        params = (code, name_ar, name_en, description, is_active, type_id)
        return self._execute_query(query, params)

    def deactivate_transaction_type(self, type_id):
        """Deactivate a transaction type (set is_active to 0)."""
        query = "UPDATE transaction_types SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        return self._execute_query(query, (type_id,))

# =====================================================================
# 2. TransactionTypeFormDialog: Form (Dialog) for adding/editing transaction types
# =====================================================================
class TransactionTypeFormDialog(QDialog):
    def __init__(self, db_manager, type_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.type_id = type_id
        self.setWindowTitle("إضافة نوع معاملة جديد" if type_id is None else "تعديل نوع معاملة")
        self.setMinimumWidth(400)
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QFormLayout()

        self.code_input = QLineEdit()
        layout.addRow("الكود:", self.code_input)

        self.name_ar_input = QLineEdit()
        layout.addRow("الاسم بالعربية:", self.name_ar_input)

        self.name_en_input = QLineEdit()
        layout.addRow("الاسم بالإنجليزية:", self.name_en_input)

        self.description_input = QLineEdit()
        layout.addRow("الوصف:", self.description_input)

        self.is_active_combo = QComboBox()
        self.is_active_combo.addItem("نشط", 1)
        self.is_active_combo.addItem("غير نشط", 0)
        layout.addRow("الحالة:", self.is_active_combo)

        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("حفظ")
        self.save_button.clicked.connect(self.save_transaction_type)
        buttons_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("إلغاء")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        layout.addRow(buttons_layout)
        self.setLayout(layout)

    def load_data(self):
        if self.type_id is not None:
            type_data = self.db_manager.get_transaction_type_by_id(self.type_id)
            if type_data:
                self.code_input.setText(type_data['code'])
                self.name_ar_input.setText(type_data['name_ar'])
                self.name_en_input.setText(type_data['name_en'] if type_data['name_en'] else "")
                self.description_input.setText(type_data['description'] if type_data['description'] else "")
                
                index = self.is_active_combo.findData(type_data['is_active'])
                if index != -1:
                    self.is_active_combo.setCurrentIndex(index)
            else:
                QMessageBox.warning(self, "خطأ", "فشل تحميل بيانات نوع المعاملة.")
                self.reject()
        
        # Disable code field when editing to prevent changing the unique code
        if self.type_id is not None:
            self.code_input.setReadOnly(True)
            self.code_input.setProperty("readOnly", True) # For QSS recognition

    def save_transaction_type(self):
        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()
        description = self.description_input.text().strip()
        is_active = self.is_active_combo.currentData()

        if not code or not name_ar:
            QMessageBox.warning(self, "بيانات ناقصة", "الرجاء ملء الكود والاسم بالعربية.")
            return

        # Check for uniqueness of code and name_ar (case-insensitive for code)
        if self.type_id is None: # Only check uniqueness when adding new
            if self.db_manager.get_transaction_type_by_code(code):
                QMessageBox.warning(self, "كود مكرر", "كود نوع المعاملة هذا موجود بالفعل. الرجاء اختيار كود فريد.")
                return
            if self.db_manager.get_transaction_type_by_name_ar(name_ar):
                QMessageBox.warning(self, "اسم عربي مكرر", "الاسم بالعربية هذا موجود بالفعل. الرجاء اختيار اسم فريد.")
                return
            
            # name_en is optional and not unique, so no check needed for it here
            # If name_en is provided, check if it's unique if the schema requires it, but current schema doesn't enforce it.

            if self.db_manager.add_transaction_type(code, name_ar, name_en, description, is_active):
                QMessageBox.information(self, "نجاح", "تمت إضافة نوع المعاملة بنجاح.")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل إضافة نوع المعاملة.")
        else: # Edit mode
            # For update, check uniqueness only if the code/name_ar has changed to another existing one
            original_data = self.db_manager.get_transaction_type_by_id(self.type_id)
            if original_data:
                if original_data['code'].lower() != code.lower() and self.db_manager.get_transaction_type_by_code(code):
                    QMessageBox.warning(self, "كود مكرر", "كود نوع المعاملة هذا موجود بالفعل. الرجاء اختيار كود فريد.")
                    return
                if original_data['name_ar'] != name_ar and self.db_manager.get_transaction_type_by_name_ar(name_ar):
                    QMessageBox.warning(self, "اسم عربي مكرر", "الاسم بالعربية هذا موجود بالفعل. الرجاء اختيار اسم فريد.")
                    return

            if self.db_manager.update_transaction_type(self.type_id, code, name_ar, name_en, description, is_active):
                QMessageBox.information(self, "نجاح", "تم تحديث نوع المعاملة بنجاح.")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل تحديث نوع المعاملة.")


# =====================================================================
# 3. TransactionTypesWindow: Main interface for managing transaction types
# =====================================================================
class TransactionTypesWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = TransactionTypeDBManager()
        self.setWindowTitle("إدارة أنواع المعاملات")
        self.setGeometry(100, 100, 1000, 600)
        self.current_type_id = None # To keep track of the selected item for update/delete

        self.setLayoutDirection(Qt.RightToLeft)
        QApplication.instance().setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_transaction_types()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        title_label = QLabel("إدارة أنواع المعاملات")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Form Group Box
        form_group_box = QGroupBox("بيانات نوع المعاملة")
        form_layout = QGridLayout(form_group_box)
        form_group_box.setLayoutDirection(Qt.RightToLeft)

        self.code_input = QLineEdit()
        self.name_ar_input = QLineEdit()
        self.name_en_input = QLineEdit()
        self.description_input = QLineEdit()
        self.is_active_combo = QComboBox()
        self.is_active_combo.addItem("نشط", 1)
        self.is_active_combo.addItem("غير نشط", 0)

        form_layout.addWidget(QLabel("الكود:"), 0, 0)
        form_layout.addWidget(self.code_input, 0, 1)
        form_layout.addWidget(QLabel("الاسم (عربي):"), 0, 2)
        form_layout.addWidget(self.name_ar_input, 0, 3)
        
        form_layout.addWidget(QLabel("الاسم (إنجليزي):"), 1, 0)
        form_layout.addWidget(self.name_en_input, 1, 1)
        form_layout.addWidget(QLabel("الوصف:"), 1, 2)
        form_layout.addWidget(self.description_input, 1, 3)

        form_layout.addWidget(QLabel("الحالة:"), 2, 0)
        form_layout.addWidget(self.is_active_combo, 2, 1)

        main_layout.addWidget(form_group_box)

        # Buttons Layout
        buttons_layout = QHBoxLayout()

        self.add_btn = QPushButton("إضافة")
        self.add_btn.setObjectName("addButton")
        self.add_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.add_btn.clicked.connect(self.add_transaction_type)
        buttons_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("تحديث")
        self.update_btn.setObjectName("updateButton")
        self.update_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.update_btn.clicked.connect(self.update_transaction_type)
        buttons_layout.addWidget(self.update_btn)

        self.deactivate_btn = QPushButton("تعطيل")
        self.deactivate_btn.setObjectName("deleteButton") # Using deleteButton style for deactivation
        self.deactivate_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.deactivate_btn.clicked.connect(self.deactivate_transaction_type)
        buttons_layout.addWidget(self.deactivate_btn)

        self.clear_btn = QPushButton("مسح")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.clear_btn.clicked.connect(self.clear_form)
        buttons_layout.addWidget(self.clear_btn)

        main_layout.addLayout(buttons_layout)

        # Table for displaying transaction types
        self.types_table = QTableWidget()
        self.types_table.setColumnCount(6) # ID, Code, Name AR, Name EN, Description, Is Active
        self.types_table.setHorizontalHeaderLabels([
            "المعرف", "الكود", "الاسم (عربي)", "الاسم (إنجليزي)", "الوصف", "الحالة"
        ])
        self.types_table.setColumnHidden(0, True) # Hide ID column

        self.types_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.types_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # Stretch Arabic Name
        self.types_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch) # Stretch English Name
        self.types_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch) # Stretch Description

        self.types_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.types_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.types_table.itemSelectionChanged.connect(self.display_selected_type)

        main_layout.addWidget(self.types_table)

        # Initial state of buttons
        self.update_btn.setEnabled(False)
        self.deactivate_btn.setEnabled(False)

    def load_transaction_types(self):
        """Loads all transaction types from the database and populates the table."""
        self.types_table.setRowCount(0) # Clear existing rows
        transaction_types = self.db_manager.get_all_transaction_types()

        if transaction_types:
            for i, tt_data in enumerate(transaction_types):
                self.types_table.insertRow(i)
                self.types_table.setItem(i, 0, QTableWidgetItem(str(tt_data['id'])))
                self.types_table.setItem(i, 1, QTableWidgetItem(tt_data['code']))
                self.types_table.setItem(i, 2, QTableWidgetItem(tt_data['name_ar']))
                self.types_table.setItem(i, 3, QTableWidgetItem(tt_data['name_en'] if tt_data['name_en'] else ""))
                self.types_table.setItem(i, 4, QTableWidgetItem(tt_data['description'] if tt_data['description'] else ""))
                self.types_table.setItem(i, 5, QTableWidgetItem("نشط" if tt_data['is_active'] == 1 else "غير نشط"))
        self.clear_form()

    def add_transaction_type(self):
        """Opens a dialog to add a new transaction type."""
        dialog = TransactionTypeFormDialog(self.db_manager, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_transaction_types() # Reload data after adding

    def update_transaction_type(self):
        """Opens a dialog to update the selected transaction type."""
        if self.current_type_id is None:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد نوع معاملة لتعديله.")
            return

        dialog = TransactionTypeFormDialog(self.db_manager, type_id=self.current_type_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_transaction_types() # Reload data after updating

    def deactivate_transaction_type(self):
        """Deactivates the selected transaction type."""
        print(f"DEBUG: Deactivate button clicked. current_type_id: {self.current_type_id}")
        if self.current_type_id is None:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد نوع معاملة لتعطيله.")
            print("DEBUG: No type selected for deactivation.")
            return

        selected_row = self.types_table.currentRow()
        if selected_row >= 0:
            type_name = self.types_table.item(selected_row, 2).text() # Get Arabic name for confirmation

            reply = QMessageBox.question(self, "تأكيد التعطيل",
                                         f"هل أنت متأكد أنك تريد تعطيل نوع المعاملة '{type_name}'؟",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                print(f"DEBUG: User confirmed deactivation for type_id: {self.current_type_id}")
                success = self.db_manager.deactivate_transaction_type(self.current_type_id)
                if success:
                    QMessageBox.information(self, "نجاح", "تم تعطيل نوع المعاملة بنجاح.")
                    self.load_transaction_types()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل تعطيل نوع المعاملة. يرجى مراجعة سجلات الأخطاء.")
                # Error messages will appear from within db_manager.deactivate_transaction_type
        else:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على معرف نوع المعاملة المحدد.")
            print("DEBUG: No row selected in table for deactivation.")

    def display_selected_type(self):
        """Displays the details of the selected transaction type in the form."""
        selected_row = self.types_table.currentRow()
        if selected_row >= 0:
            self.current_type_id = int(self.types_table.item(selected_row, 0).text())
            type_data = self.db_manager.get_transaction_type_by_id(self.current_type_id)
            if type_data:
                self.code_input.setText(type_data['code'])
                self.name_ar_input.setText(type_data['name_ar'])
                self.name_en_input.setText(type_data['name_en'] if type_data['name_en'] else "")
                self.description_input.setText(type_data['description'] if type_data['description'] else "")
                
                index_active = self.is_active_combo.findData(type_data['is_active'])
                if index_active != -1:
                    self.is_active_combo.setCurrentIndex(index_active)

                self.add_btn.setEnabled(False)
                self.update_btn.setEnabled(True)
                self.deactivate_btn.setEnabled(True)

                self.code_input.setReadOnly(True) # Code should be read-only when editing
                self.code_input.setProperty("readOnly", True) # For QSS recognition
        else:
            self.clear_form()

    def clear_form(self):
        """Clears the form fields and resets button states."""
        self.current_type_id = None
        self.code_input.clear()
        self.name_ar_input.clear()
        self.name_en_input.clear()
        self.description_input.clear()
        self.is_active_combo.setCurrentIndex(0) # Set to 'نشط'

        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        self.deactivate_btn.setEnabled(False)

        self.code_input.setReadOnly(False) # Code should be editable when adding new
        self.code_input.setProperty("readOnly", False)

        self.types_table.blockSignals(True) # Prevent signal during clearSelection
        self.types_table.clearSelection()
        self.types_table.blockSignals(False)


# =====================================================================
# 4. Entry point for the application
# =====================================================================
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Database initialization
    print("Ensuring Financials DB schema is initialized...")
    schema_manager = DBSchemaManager()
    # Ensure transaction_types table is created if it doesn't exist
    schema_manager.initialize_specific_database('financials') # This should ensure all financial schemas, including transaction_types, are created.
    
    # You might need to add the SQL for transaction_types to your financials_schema.py
    # if it's not already there. For example:
    # FINANCIALS_SCHEMA_SCRIPT = """
    # -- existing tables...
    # CREATE TABLE IF NOT EXISTS transaction_types (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    #     name_ar TEXT NOT NULL UNIQUE,
    #     name_en TEXT UNIQUE, -- This UNIQUE constraint might cause issues if you expect non-unique English names
    #     description TEXT,
    #     is_active INTEGER DEFAULT 1,
    #     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    #     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    # );
    # -- other tables...
    # """
    # And then ensure DBSchemaManager uses this script.

    # Load and apply QSS stylesheet
    qss_file_path = os.path.join(project_root, 'ui', 'styles', 'styles.qss')
    app_stylesheet = load_qss_file(qss_file_path)
    if app_stylesheet:
        app.setStyleSheet(app_stylesheet)
        print("DEBUG: Applied DFD-001 stylesheet.")
    else:
        print("WARNING: Failed to load stylesheet. UI might not be consistent.")

    window = TransactionTypesWindow()
    window.showMaximized()
    sys.exit(app.exec_())

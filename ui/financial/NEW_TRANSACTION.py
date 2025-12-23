# ui/financial/journal_entry_ui.py
import sys
import sqlite3
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDateEdit, QComboBox, QGroupBox, QGridLayout,
    QAbstractItemView, QApplication, QStyle, QDoubleSpinBox,
    QDialog, QDialogButtonBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate, QDateTime
from PyQt5.QtGui import QFont, QDoubleValidator

# =====================================================================
# Correcting the root project path to enable proper imports
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import necessary managers
from database.manager.financial_lookups_manager import FinancialLookupsManager
from database.manager.account_manager import AccountManager
from database.manager.journal_manager import JournalManager
from database.db_connection import get_financials_db_connection

# Missing imports added to fix errors
from database.schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT
from database.schems.default_data.financials_data_population import insert_default_data
from database.manager.admin.NEWuser_manager import NEWUserManager
from database.manager.admin.session import get_current_user_id,get_current_user
print("DEBUG: journal_entry_ui.py module loaded")


# =====================================================================
# Helper function to load QSS files
# =====================================================================
def load_qss_file(file_path):
    """Loads content from a QSS file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: QSS file not found at {file_path}")
        return ""
    except Exception as e:
        print(f"ERROR: Could not load QSS file {file_path}: {e}")
        return ""

class AccountCodeLineEdit(QLineEdit):
    def __init__(self, row, table, manager, parent=None):
        super().__init__(parent)
        self.row = row
        self.table = table
        self.account_manager = manager
        self.editingFinished.connect(self.validate_account_code)

    def validate_account_code(self):
        acc_code = self.text().strip()
        if not acc_code:
            # Clear account name if code is empty
            self.table.item(self.row, 2).setText("")
            return

        account = self.account_manager.get_final_account_by_code(acc_code)

        if account:
            self.table.item(self.row, 0).setText(str(account['id']))
            self.table.item(self.row, 2).setText(account['account_name_ar'])
        else:
            QMessageBox.warning(self.parent(), "خطأ في الحساب", f"كود الحساب '{acc_code}' غير موجود أو أنه حساب رئيسي لا يمكن إجراء حركات عليه.")
            self.clear()
            self.table.item(self.row, 2).setText("")
            self.setFocus()

# =====================================================================
# Custom LineEdit for Debit/Credit
# =====================================================================
class CustomLineEditForNumbers(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setValidator(QDoubleValidator(0.00, 999999999.99, 2, self))
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setPlaceholderText("0.00")
        self.setText("")
        self.original_stylesheet = self.styleSheet()

    def setValue(self, value):
        """Sets the value and formats it."""
        if value == 0.0:
            self.setText("")
        else:
            self.setText(f"{value:,.2f}")

    def value(self):
        """Returns the float value from the text."""
        try:
            return float(self.text().replace(',', '')) if self.text() else 0.0
        except ValueError:
            return 0.0

    def clear(self):
        """Clears the text."""
        self.setText("")

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        if not enabled:
            self.setStyleSheet("background-color: #e9ecef; color: #6c757d;")
        else:
            self.setStyleSheet(self.original_stylesheet if self.original_stylesheet else "")

class NewJournalEntryManagementWindow(QWidget):
    def __init__(self, journal_manager=None, lookup_manager=None, account_manager=None, user_manager=None):
        self.current_journal_entry_id = None
        print("DEBUG: NewJournalEntryManagementWindow initialized")
        super().__init__()
        self.journal_manager = journal_manager if journal_manager else JournalManager(get_financials_db_connection)
        self.lookup_manager = lookup_manager if lookup_manager else FinancialLookupsManager(get_financials_db_connection)
        self.account_manager = account_manager if account_manager else AccountManager(get_financials_db_connection)
        self.user_manager = user_manager if user_manager else NEWUserManager()  # إضافة UserManager
    
        # الحصول على معرف المستخدم الحالي
        self.current_user_id = self.get_current_user_id()

        self.setWindowTitle("إدارة قيود اليومية")
        self.setLayoutDirection(Qt.RightToLeft)
        QApplication.instance().setLayoutDirection(Qt.RightToLeft)

        self.setup_line_table_comboboxes()
        self.init_ui()
        self.populate_header_comboboxes()
        self.set_next_entry_number()

        # Signal connections
        self.add_line_btn.clicked.connect(self.add_empty_line)
        self.remove_line_btn.clicked.connect(self.remove_selected_line)
        self.save_btn.clicked.connect(self.save_journal_entry)
        self.update_entry_btn.clicked.connect(self.update_journal_entry)
        self.delete_entry_btn.clicked.connect(self.delete_journal_entry)
        self.clear_entry_btn.clicked.connect(self.clear_form)
        self.search_btn.clicked.connect(self.perform_search)

        # Connect Enter key for header fields
        self.entry_date_input.lineEdit().returnPressed.connect(self.focus_next_widget)
        self.description_input.returnPressed.connect(self.focus_next_widget)
        self.tranaction_type_combo.activated.connect(self.focus_next_widget)
        self.search_input.returnPressed.connect(self.perform_search)

        # Override keyPressEvent for the table for Enter key navigation
        self.lines_table.keyPressEvent = self._lines_table_key_press_event

        # Initial state updates
        self.update_main_buttons_state()

    def get_current_user_id(self):
        """الحصول على معرف المستخدم الحالي"""
        try:
            # المحاولة الأولى: من الجلسة
            user_id = get_current_user_id()
            print(f"DEBUG: User ID from session: {user_id}")
        
            if user_id:
                return user_id
        
            # المحاولة الثانية: من بيانات الجلسة
            user_data = get_current_user()
            print(f"DEBUG: User data from session: {user_data}")
        
            if user_data and 'id' in user_data:
                return user_data['id']
            
            # المحاولة الثالثة: استخدام UserManager للعثور على المستخدم الحالي
            if self.user_manager:
                # جلب أول مستخدم نشط (لأغراض الاختبار)
                users = self.user_manager.get_all_users()
                if users:
                    return users[0]['id']
                
        except Exception as e:
            print(f"خطأ في الحصول على معرف المستخدم: {e}")
    
        # قيمة افتراضية للاختبار
        return 1
    
    def get_current_user_name(self):
        """الحصول على اسم المستخدم الحالي"""
        try:
            user_id = self.get_current_user_id()
            if user_id:
                # استخدم الدالة المعدلة
                return self.get_user_name_by_id(user_id)
        except Exception as e:
            print(f"خطأ في الحصول على اسم المستخدم الحالي: {e}")
    
        return "مستخدم غير معروف"
    
    def init_ui(self):
        print("DEBUG: Initializing UI for NewJournalEntryManagementWindow")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(6)

        # Header Section
        title_label = QLabel("إدارة قيود اليومية")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("windowTitle")
        main_layout.addWidget(title_label)

        # Entry Header Group
        header_group_box = QGroupBox("بيانات رأس القيد")
        header_group_box.setObjectName("headerGroupBox")
        header_group_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        header_layout = QGridLayout(header_group_box)
        header_layout.setSpacing(5)

        # Row 0: Entry Number, Date, Transaction Type
        self.entry_number_input = QLineEdit()
        self.entry_number_input.setReadOnly(True)
        self.entry_number_input.setProperty("readOnly", True)
        self.entry_date_input = QDateEdit(QDate.currentDate())
        self.entry_date_input.setCalendarPopup(True)
        self.entry_date_input.setDisplayFormat("yyyy-MM-dd")
        self.tranaction_type_combo = QComboBox()

        # بعد وصف القيد (الصف 1) وإضافة صف جديد
        # Row 2: Created by, Created at, Updated by, Updated at
        self.created_by_input = QLineEdit()
        self.created_by_input.setReadOnly(True)
        self.created_at_input = QLineEdit()
        self.created_at_input.setReadOnly(True)
        self.updated_by_input = QLineEdit()
        self.updated_by_input.setReadOnly(True)
        self.updated_at_input = QLineEdit()
        self.updated_at_input.setReadOnly(True)
       
        header_layout.addWidget(QLabel("رقم القيد:"), 0, 0)
        header_layout.addWidget(self.entry_number_input, 0, 1)
        header_layout.addWidget(QLabel("تاريخ القيد:"), 0, 2)
        header_layout.addWidget(self.entry_date_input, 0, 3)
        header_layout.addWidget(QLabel("نوع الحركة:"), 0, 4)
        header_layout.addWidget(self.tranaction_type_combo, 0, 5)
        header_layout.addWidget(QLabel("أنشئ بواسطة:"), 0, 6)
        header_layout.addWidget(self.created_by_input, 0, 7)
        header_layout.addWidget(QLabel("تاريخ الإنشاء:"), 0, 8)
        header_layout.addWidget(self.created_at_input, 0, 9)

        # Row 1: Description (spanning all columns)
        self.description_input = QLineEdit()
        header_layout.addWidget(QLabel("الوصف:"), 1, 0)
        header_layout.addWidget(self.description_input, 1, 1, 1, 5)
        header_layout.addWidget(QLabel("عدل بواسطة:"), 1, 6)
        header_layout.addWidget(self.updated_by_input, 1, 7)
        header_layout.addWidget(QLabel("تاريخ التعديل:"), 1, 8)
        header_layout.addWidget(self.updated_at_input, 1, 9)

        # Balance Status Section
        balance_layout = QHBoxLayout()
        balance_layout.setSpacing(5)

        self.total_debit_label = QLabel("إجمالي المدين: 0.00")
        self.total_debit_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.total_debit_label.setObjectName("totalLabel")
        self.total_debit_label.setAlignment(Qt.AlignCenter)

        self.total_credit_label = QLabel("إجمالي الدائن: 0.00")
        self.total_credit_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.total_credit_label.setObjectName("totalLabel")
        self.total_credit_label.setAlignment(Qt.AlignCenter)

        self.balance_status_label = QLabel("الميزانية: متوازنة (الفرق: 0.00)")
        self.balance_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.balance_status_label.setObjectName("balanceStatusLabel")
        self.balance_status_label.setAlignment(Qt.AlignCenter)
        self.balance_status_label.setStyleSheet("color: #28a745;")

        balance_layout.addWidget(self.total_debit_label)
        balance_layout.addWidget(self.total_credit_label)
        balance_layout.addWidget(self.balance_status_label)

        header_layout.addLayout(balance_layout, 2, 0, 1, 6)

        # Set current user and date
        current_user_name = self.get_current_user_name()
        current_datetime = QDateTime.currentDateTime()
        print(f"DEBUG: Current user name: {current_user_name}")

        self.created_by_input.setText(current_user_name)
        self.updated_by_input.setText(current_user_name)
        self.created_at_input.setText(current_datetime.toString("yyyy-MM-dd hh:mm:ss"))
        self.updated_at_input.setText(current_datetime.toString("yyyy-MM-dd hh:mm:ss"))
       
        # تعديل التخطيط لجعل هذه الحقول تمتد على عرض كامل
        header_layout.setColumnStretch(0, 1)
        header_layout.setColumnStretch(1, 2)
        header_layout.setColumnStretch(2, 1)
        header_layout.setColumnStretch(3, 2)
        header_layout.setColumnStretch(4, 1)
        header_layout.setColumnStretch(5, 2)
        header_layout.setColumnStretch(6, 1)
        header_layout.setColumnStretch(7, 2)

        # Search Section
        search_group_box = QGroupBox("البحث عن قيد")
        search_group_box.setObjectName("searchGroupBox")
        search_group_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        search_layout = QHBoxLayout(search_group_box)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث بررقم القيد أو الوصف...")
        self.search_btn = QPushButton("بحث")
        self.search_btn.setObjectName("searchButton")
        self.search_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogContentsView))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)

        main_layout.addWidget(header_group_box)
        main_layout.addWidget(search_group_box)

        # Entry Lines Section
        lines_group_box = QGroupBox("بنود القيد")
        lines_group_box.setObjectName("linesGroupBox")
        lines_group_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        lines_layout = QVBoxLayout(lines_group_box)

        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(10)
        self.lines_table.setHorizontalHeaderLabels([
            "ID", "كود الحساب", "اسم الحساب", "مدين", "دائن",
            "نوع المستند", "رقم المستند", "نوع الضريبة", "مركز التكلفة", "ملاحظات"
        ])
        self.lines_table.setColumnHidden(0, True)
        self.lines_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.lines_table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Stretch)

        self.lines_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lines_table.setSelectionMode(QAbstractItemView.SingleSelection)

        self.add_empty_line()

        lines_layout.addWidget(self.lines_table)

        line_buttons_layout = QHBoxLayout()
        self.add_line_btn = QPushButton("إضافة سطر")
        self.add_line_btn.setObjectName("addLineButton")
        self.add_line_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        self.remove_line_btn = QPushButton("حذف سطر")
        self.remove_line_btn.setObjectName("removeLineButton")
        self.remove_line_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        line_buttons_layout.addWidget(self.add_line_btn)
        line_buttons_layout.addWidget(self.remove_line_btn)
        lines_layout.addLayout(line_buttons_layout)

        main_layout.addWidget(lines_group_box)

        # Main Buttons
        main_buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("حفظ القيد")
        self.save_btn.setObjectName("saveButton")
        self.update_entry_btn = QPushButton("تعديل القيد")
        self.update_entry_btn.setObjectName("updateButton")
        self.delete_entry_btn = QPushButton("حذف القيد")
        self.delete_entry_btn.setObjectName("deleteButton")
        self.clear_entry_btn = QPushButton("قيد جديد")
        self.clear_entry_btn.setObjectName("clearButton")
        main_buttons_layout.addWidget(self.save_btn)
        main_buttons_layout.addWidget(self.update_entry_btn)
        main_buttons_layout.addWidget(self.delete_entry_btn)
        main_buttons_layout.addWidget(self.clear_entry_btn)
        main_layout.addLayout(main_buttons_layout)

    def get_current_user_id(self):
        """الحصول على معرف المستخدم الحالي"""
        try:
            user_id = get_current_user_id()
            print(f"DEBUG: User ID from session: {user_id}")
        
            if user_id:
                return user_id
        
            # إذا لم يتم العثور على معرف المستخدم، جرب الطريقة البديلة
            user_data = get_current_user()
            print(f"DEBUG: User data from session: {user_data}")
        
            if user_data and 'id' in user_data:
                return user_data['id']
        except Exception as e:
            print(f"خطأ في الحصول على معرف المستخدم: {e}")
    
        # قيمة افتراضية للاختبار
        return 1

    def set_next_entry_number(self):
        next_num = self.journal_manager._generate_next_entry_number()
        self.entry_number_input.setText(str(next_num))

    def populate_header_comboboxes(self):
        # Transaction types
        self.tranaction_type_combo.clear()
        self.tranaction_type_combo.addItem("اختر نوع الحركة", None)
        entry_types = self.lookup_manager.get_all_entry_types() 
        if entry_types:
            for et in entry_types:
                self.tranaction_type_combo.addItem(et['name_ar'], et['id'])

    def setup_line_table_comboboxes(self):
        self.all_doc_types = self.lookup_manager.get_all_document_types() 
        self.all_tax_types = self.lookup_manager.get_all_tax_types()
        self.all_cost_centers = self.lookup_manager.get_all_cost_centers()

    def add_empty_line(self, account_data=None, line_data=None):
        row_position = self.lines_table.rowCount()
        self.lines_table.insertRow(row_position)

        # Column 0: Account ID (hidden)
        self.lines_table.setItem(row_position, 0, QTableWidgetItem(str(account_data['id']) if account_data else ""))

        # Column 1: Account Code
        acc_code_editor = AccountCodeLineEdit(row_position, self.lines_table, self.account_manager)
        if account_data:
            acc_code_editor.setText(account_data['acc_code'])
        self.lines_table.setCellWidget(row_position, 1, acc_code_editor)

        # Column 2: Account Name
        acc_name_item = QTableWidgetItem(account_data['account_name_ar'] if account_data else "")
        acc_name_item.setFlags(acc_name_item.flags() & ~Qt.ItemIsEditable)
        self.lines_table.setItem(row_position, 2, acc_name_item)

        # Column 3: Debit
        debit_input = CustomLineEditForNumbers()
        if line_data:
            debit_input.setValue(line_data.get('debit', 0.0))
        self.lines_table.setCellWidget(row_position, 3, debit_input)

        # Column 4: Credit
        credit_input = CustomLineEditForNumbers()
        if line_data:
            credit_input.setValue(line_data.get('credit', 0.0))
        self.lines_table.setCellWidget(row_position, 4, credit_input)

        # Connect textChanged signals for mutual exclusivity and total calculation
        debit_input.textChanged.connect(lambda text, r=row_position: self._handle_debit_credit_input(text, r, 'debit'))
        credit_input.textChanged.connect(lambda text, r=row_position: self._handle_debit_credit_input(text, r, 'credit'))

        # Column 5: Document Type
        doc_type_combo = self.create_combo_editor(
            self.all_doc_types,
            line_data.get('document_type_id') if line_data else None
        )
        self.lines_table.setCellWidget(row_position, 5, doc_type_combo)

        # Column 6: Document Number
        doc_number_input = QLineEdit()
        if line_data:
            doc_number_input.setText(line_data.get('document_number', ''))
        self.lines_table.setCellWidget(row_position, 6, doc_number_input)

        # Column 7: Tax Type
        tax_type_combo = self.create_combo_editor(
            self.all_tax_types,
            line_data.get('tax_type_id') if line_data else None
        )
        self.lines_table.setCellWidget(row_position, 7, tax_type_combo)

        # Column 8: Cost Center
        cost_center_combo = self.create_combo_editor(
            self.all_cost_centers,
            line_data.get('cost_center_id') if line_data else None
        )
        self.lines_table.setCellWidget(row_position, 8, cost_center_combo)

        # Column 9: Notes
        notes_item = QTableWidgetItem(line_data.get('notes', '') if line_data else "")
        self.lines_table.setItem(row_position, 9, notes_item)
        notes_item.setFlags(notes_item.flags() | Qt.ItemIsEditable)

        self.lines_table.scrollToBottom()

    def _handle_debit_credit_input(self, text, row_idx, changed_column_type):
        """
        Handles mutual exclusivity between Debit and Credit inputs in a row.
        """
        debit_input = self.lines_table.cellWidget(row_idx, 3)
        credit_input = self.lines_table.cellWidget(row_idx, 4)

        # Disconnect signals temporarily to prevent infinite loop when clearing
        debit_input.textChanged.disconnect()
        credit_input.textChanged.disconnect()

        try:
            current_value = float(text.replace(',', '')) if text else 0.0

            if changed_column_type == 'debit':
                if current_value > 0 and credit_input.value() > 0:
                    QMessageBox.warning(self, "خطأ في الإدخال", f"لا يمكن إدخال قيمة في عمودي 'المدين' و 'الدائن' في نفس السطر رقم {row_idx + 1}. تم مسح كلا القيمتين.")
                    debit_input.clear()
                    credit_input.clear()
                elif current_value > 0 and credit_input.value() == 0.0:
                    credit_input.clear()

            elif changed_column_type == 'credit':
                if current_value > 0 and debit_input.value() > 0:
                    QMessageBox.warning(self, "خطأ في الإدخال", f"لا يمكن إدخال قيمة في عمودي 'المدين' و 'الدائن' في نفس السطر رقم {row_idx + 1}. تم مسح كلا القيمتين.")
                    credit_input.clear()
                    debit_input.clear()
                elif current_value > 0 and debit_input.value() == 0.0:
                    debit_input.clear()

        except ValueError:
            pass
        finally:
            # Reconnect signals
            debit_input.textChanged.connect(lambda t, r=row_idx: self._handle_debit_credit_input(t, r, 'debit'))
            credit_input.textChanged.connect(lambda t, r=row_idx: self._handle_debit_credit_input(t, r, 'credit'))
            self.calculate_totals()

    def create_combo_editor(self, items, current_id):
        combo = QComboBox()
        combo.addItem("اختر...", None)
        if items:
            for item in items:
                combo.addItem(item['name_ar'], item['id'])
        if current_id is not None:
            index = combo.findData(current_id)
            if index != -1:
                combo.setCurrentIndex(index)
        return combo

    def remove_selected_line(self):
        selected_rows = self.lines_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد سطر لحذفه.")
            return
        for index in sorted(selected_rows, reverse=True):
            self.lines_table.removeRow(index.row())
        self.calculate_totals()
        if self.lines_table.rowCount() == 0:
            self.add_empty_line()

    def calculate_totals(self):
        total_debit = 0.0
        total_credit = 0.0

        for row in range(self.lines_table.rowCount()):
            debit_widget = self.lines_table.cellWidget(row, 3)
            credit_widget = self.lines_table.cellWidget(row, 4)

            debit_val = debit_widget.value() if isinstance(debit_widget, CustomLineEditForNumbers) else 0.0
            credit_val = credit_widget.value() if isinstance(credit_widget, CustomLineEditForNumbers) else 0.0

            total_debit += debit_val
            total_credit += credit_val

        self.total_debit_label.setText(f"إجمالي المدين: {total_debit:,.2f}")
        self.total_credit_label.setText(f"إجمالي الدائن: {total_credit:,.2f}")

        diff = total_debit - total_credit
        if abs(diff) < 0.01:
            self.balance_status_label.setText("الميزانية: متوازنة (الفرق: 0.00)")
            self.balance_status_label.setStyleSheet("color: #28a745;")
        else:
            self.balance_status_label.setText(f"الميزانية: غير متوازنة (الفرق: {abs(diff):,.2f} {'مدين' if diff > 0 else 'دائن'})")
            self.balance_status_label.setStyleSheet("color: #dc3545;")

    def get_lines_data_from_table(self):
        lines_data = []
        for row in range(self.lines_table.rowCount()):
            account_id_item = self.lines_table.item(row, 0)
            debit_input = self.lines_table.cellWidget(row, 3)
            credit_input = self.lines_table.cellWidget(row, 4)
            doc_number_input = self.lines_table.cellWidget(row, 6)
            notes_item = self.lines_table.item(row, 9)

            account_id = account_id_item.text() if account_id_item else None
            debit_value = debit_input.value() if isinstance(debit_input, CustomLineEditForNumbers) else 0.0
            credit_value = credit_input.value() if isinstance(credit_input, CustomLineEditForNumbers) else 0.0
            document_number = doc_number_input.text().strip() if doc_number_input else ""
            notes = notes_item.text() if notes_item else ""

            # Skip entirely empty rows
            if not account_id and debit_value == 0.0 and credit_value == 0.0 and not document_number and not notes:
                continue

            if not account_id:
                QMessageBox.warning(self, "بيانات ناقصة", f"الرجاء إدخال كود حساب صحيح في السطر رقم {row + 1}.")
                return None

            if debit_value > 0 and credit_value > 0:
                QMessageBox.warning(self, "خطأ في بنود القيد", f"لا يمكن إدخال قيم في عمودي 'المدين' و 'الدائن' في نفس السطر رقم {row + 1}. الرجاء إدخال القيمة في عمود واحد فقط.")
                return None
            
            if account_id and debit_value == 0.0 and credit_value == 0.0:
                QMessageBox.warning(self, "بيانات ناقصة", f"الرجاء إدخال قيمة في عمود 'المدين' أو 'الدائن' للسطر رقم {row + 1}.")
                return None

            line = {
                'account_id': int(account_id),
                'debit': debit_value,
                'credit': credit_value,
                'document_type_id': self.lines_table.cellWidget(row, 5).currentData(),
                'document_number': document_number,
                'tax_type_id': self.lines_table.cellWidget(row, 7).currentData(),
                'cost_center_id': self.lines_table.cellWidget(row, 8).currentData(),
                'notes': notes
            }
            lines_data.append(line)
        return lines_data

    def save_journal_entry(self):
        entry_date = self.entry_date_input.date().toString(Qt.ISODate)
        description = self.description_input.text().strip()
        transaction_type_id = self.tranaction_type_combo.currentData()
        system_date = QDate.currentDate().toString(Qt.ISODate)

        # الحصول على financial_year_id
        financial_year_id = self.get_financial_year_id(entry_date)
    
        # التحقق من وجود financial_year_id
        if financial_year_id is None:
            QMessageBox.warning(self, "خطأ", "لا يمكن تحديد السنة المالية. الرجاء التحقق من إعدادات السنوات المالية.")
            return

        if not all([entry_date, description, transaction_type_id]):
            QMessageBox.warning(self, "بيانات ناقصة", "الرجاء إدخال جميع بيانات رأس القيد.")
            return

        lines = self.get_lines_data_from_table()
        if lines is None:
            return  # تم عرض رسالة الخطأ بالفعل في get_lines_data_from_table
        if not lines:
            QMessageBox.warning(self, "بنود القيد", "الرجاء إضافة بنود صالحة للقيد.")
            return

        total_debit = sum(line['debit'] for line in lines)
        total_credit = sum(line['credit'] for line in lines)

        if abs(total_debit - total_credit) >= 0.01:
            QMessageBox.warning(self, "قيد غير متوازن", "إجمالي المدين لا يساوي إجمالي الدائن.")
            return

        success = self.journal_manager.add_journal_entry(
            entry_date=entry_date,
            description=description,
            transaction_type_id=transaction_type_id,
            total_debit=total_debit,
            total_credit=total_credit,
            lines=lines,
            status='Under Review',
            system_date=system_date,
            financial_year_id=financial_year_id,
            created_by=self.current_user_id  # استخدام ID المستخدم الحالي
        )

        if success:
            QMessageBox.information(self, "نجاح", "تم حفظ القيد بنجاح.")
            self.clear_form()


    def get_financial_year_id(self, entry_date):
        """الحصول على financial_year_id من تاريخ القيد"""
        print(f"DEBUG: Searching for financial year for date: {entry_date}")

        conn = None
        try:
            conn = get_financials_db_connection()
            if conn is None:
                raise ConnectionError("لا يمكن الاتصال بقاعدة البيانات.")

            cursor = conn.cursor()

            # --- المحاولة الأولى: سنة مالية مناسبة للتاريخ (مفتوحة أو مغلقة) ---
            query1 = """
                SELECT id FROM financial_years
                WHERE start_date <= ? AND end_date >= ?
                ORDER BY is_closed ASC, end_date DESC
                LIMIT 1
            """
            cursor.execute(query1, (entry_date, entry_date))
            result = cursor.fetchone()
            print(f"DEBUG: Query 1 (in range) result: {result}")
        
            if result and result[0]:
                financial_year_id = result[0]
                # تحقق إذا كانت السنة مغلقة وأعط تحذيراً
                cursor.execute("SELECT is_closed FROM financial_years WHERE id = ?", (financial_year_id,))
                is_closed = cursor.fetchone()[0]
                if is_closed:
                    QMessageBox.warning(self, "تحذير", 
                        f"تم استخدام سنة مالية مغلقة ({entry_date}). الرجاء فتح السنة المالية أو استخدام تاريخ مختلف.")
                print(f"DEBUG: Using financial_year_id: {financial_year_id}")
                return financial_year_id

            # --- المحاولة الثانية: أحدث سنة مالية مفتوحة ---
            query2 = """
                SELECT id FROM financial_years
                WHERE is_closed = 0
                ORDER BY end_date DESC
                LIMIT 1
            """
            cursor.execute(query2)
            result = cursor.fetchone()
            print(f"DEBUG: Query 2 (latest open) result: {result}")
        
            if result and result[0]:
                QMessageBox.warning(self, "تحذير", 
                    "لم يتم العثور على سنة مالية مناسبة للتاريخ، سيتم استخدام أحدث سنة مالية مفتوحة.")
                print(f"DEBUG: Using financial_year_id from latest open: {result[0]}")
                return result[0]

            # --- إذا فشلت كل المحاولات ---
            raise ValueError("لا توجد أي سنوات مالية محددة في النظام. الرجاء إضافة سنة مالية أولاً.")

        except Exception as e:
            print(f"CRITICAL ERROR in get_financial_year_id: {e}")
            QMessageBox.critical(self, "خطأ في تحديد السنة المالية", 
                                f"حدث خطأ أثناء تحديد السنة المالية:\n{str(e)}")
            return None

        finally:
            if conn:
                conn.close()
                print("DEBUG: Database connection closed.")
                
    def update_journal_entry(self):
        if self.current_journal_entry_id is None:
            QMessageBox.warning(self, "لا يوجد قيد محدد", "الرجاء تحديد قيد للتعديل.")
            return

        entry_date = self.entry_date_input.date().toString(Qt.ISODate)
        description = self.description_input.text().strip()
        transaction_type_id = self.tranaction_type_combo.currentData()
        system_date = QDate.currentDate().toString(Qt.ISODate)

        # الحصول على financial_year_id للتعديل أيضاً
        financial_year_id = self.get_financial_year_id(entry_date)
    
        # التحقق من وجود financial_year_id
        if financial_year_id is None:
            QMessageBox.warning(self, "خطأ", "لا يمكن تحديد السنة المالية. الرجاء التحقق من إعدادات السنوات المالية.")
            return

        if not all([entry_date, description, transaction_type_id]):
            QMessageBox.warning(self, "بيانات ناقصة", "الرجاء إدخال جميع بيانات رأس القيد.")
            return

        lines = self.get_lines_data_from_table()
        if lines is None:
            return  # تم عرض رسالة الخطأ بالفعل في get_lines_data_from_table
        if not lines:
            QMessageBox.warning(self, "بنود القيد", "الرجاء إضافة بنود صالحة للقيد.")
            return

        total_debit = sum(line['debit'] for line in lines)
        total_credit = sum(line['credit'] for line in lines)

        if abs(total_debit - total_credit) >= 0.01:
            QMessageBox.warning(self, "قيد غير متوازن", "إجمالي المدين لا يساوي إجمالي الدائن.")
            return

        success = self.journal_manager.update_journal_entry(
            entry_id=self.current_journal_entry_id,
            entry_date=entry_date,
            description=description,
            transaction_type_id=transaction_type_id,
            total_debit=total_debit,
            total_credit=total_credit,
            lines=lines,
            system_date=system_date,
            financial_year_id=financial_year_id,
            updated_by=self.current_user_id  # استخدام ID المستخدم الحالي
        )

        if success:
            QMessageBox.information(self, "نجاح", "تم تحديث القيد بنجاح.")
            self.clear_form()
            
    def delete_journal_entry(self):
        if self.current_journal_entry_id is None:
            QMessageBox.warning(self, "لا يوجد قيد محدد", "الرجاء تحديد قيد للحذف.")
            return

        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من رغبتك في حذف هذا القيد؟ لا يمكن التراجع عن هذه العملية.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success = self.journal_manager.delete_journal_entry(self.current_journal_entry_id)
            if success:
                QMessageBox.information(self, "نجاح", "تم حذف القيد بنجاح.")
                self.clear_form()

    def perform_search(self):
        search_text = self.search_input.text().strip()
        if not search_text:
            QMessageBox.warning(self, "بحث فارغ", "الرجاء إدخال نص للبحث.")
            return

        entries = self.journal_manager.search_journal_entries(search_text)

        if not entries:
            QMessageBox.information(self, "لا توجد نتائج", "لم يتم العثور على قيود مطابقة للبحث.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("نتائج البحث")
        dialog.setLayoutDirection(Qt.RightToLeft)
        layout = QVBoxLayout(dialog)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["رقم القيد", "التاريخ", "الوصف", "الحالة"])
        table.setRowCount(len(entries))
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for row, entry in enumerate(entries):
            table.setItem(row, 0, QTableWidgetItem(str(entry['entry_number'])))
            table.setItem(row, 1, QTableWidgetItem(str(entry['entry_date'])))
            table.setItem(row, 2, QTableWidgetItem(str(entry['description'])))
            table.setItem(row, 3, QTableWidgetItem(str(entry['status'])))
            table.resizeColumnsToContents()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        layout.addWidget(table)
        layout.addWidget(button_box)

        if dialog.exec_() == QDialog.Accepted:
            selected_row = table.currentRow()
            if selected_row >= 0:
                entry_id = entries[selected_row]['id']
                self.load_selected_entry(entry_id)

    def load_selected_entry(self, entry_id):
        entry_details = self.journal_manager.get_journal_entry_by_id(entry_id)
        entry_lines = self.journal_manager.get_journal_entry_lines(entry_id)

        if entry_details and entry_lines:
            self.current_journal_entry_id = entry_id
            self.entry_number_input.setText(entry_details['entry_number'])
            self.entry_date_input.setDate(QDate.fromString(entry_details['entry_date'], Qt.ISODate))
            self.description_input.setText(entry_details['description'])

            # Set transaction type
            index = self.tranaction_type_combo.findData(entry_details['transaction_type_id'])
            if index >= 0:
                self.tranaction_type_combo.setCurrentIndex(index)

            # تحميل بيانات المستخدمين والتواريخ
            self.load_user_dates_info(entry_details)

            # Load lines
            self.lines_table.setRowCount(0)
            for line in entry_lines:
                account_data = self.account_manager.get_account_by_id(line['account_id'])
                self.add_empty_line(account_data=account_data, line_data=line)

            self.calculate_totals()
            self.update_main_buttons_state()
            
    def get_user_name_by_id(self, user_id):
        """الحصول على اسم المستخدم من معرفه (full_name إذا متاح، أو username)"""
        try:
            if not user_id or user_id == 0 or user_id == "0":
                return "غير معروف"

            conn = get_financials_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT full_name, username FROM users WHERE id = ?", (user_id,))
                result = cursor.fetchone()
                conn.close()

                if result:
                    full_name, username = result
                    if full_name and full_name.strip():
                        return full_name.strip()
                    elif username and username.strip():
                        return username.strip()
        except Exception as e:
            print(f"خطأ في get_user_name_by_id: {e}")

        return "غير معروف"

    
    
    def load_user_dates_info(self, entry_details):
        """تحميل معلومات المستخدمين والتواريخ للقيد"""
        try:
            print(f"DEBUG: Entry details - created_by: {entry_details.get('created_by')}, updated_by: {entry_details.get('updated_by')}")
        
            # تحميل اسم المستخدم الذي أنشأ القيد
            created_by_id = entry_details.get('created_by')
            if created_by_id and created_by_id != 0 and created_by_id != "0":
                created_by_name = self.get_user_name_by_id(created_by_id)
                self.created_by_input.setText(created_by_name)
            else:
                self.created_by_input.setText("غير معروف")
                print("DEBUG: created_by is NULL or 0")

            # تحميل تاريخ الإنشاء
            if entry_details.get('created_at'):
                created_at_str = entry_details['created_at']
                if 'T' in created_at_str:
                    created_at = QDateTime.fromString(created_at_str, Qt.ISODate)
                    self.created_at_input.setText(created_at.toString("yyyy-MM-dd hh:mm:ss"))
                else:
                    created_at = QDate.fromString(created_at_str, Qt.ISODate)
                    self.created_at_input.setText(created_at.toString("yyyy-MM-dd"))
            else:
                self.created_at_input.setText("غير معروف")

            # تحميل اسم المستخدم الذي عدل القيد
            updated_by_id = entry_details.get('updated_by')
            if updated_by_id and updated_by_id != 0 and updated_by_id != "0":
                updated_by_name = self.get_user_name_by_id(updated_by_id)
                self.updated_by_input.setText(updated_by_name)
            else:
                self.updated_by_input.setText("غير معروف")
                print("DEBUG: updated_by is NULL or 0")

            # تحميل تاريخ التعديل
            if entry_details.get('updated_at'):
                updated_at_str = entry_details['updated_at']
                if 'T' in updated_at_str:
                    updated_at = QDateTime.fromString(updated_at_str, Qt.ISODate)
                    self.updated_at_input.setText(updated_at.toString("yyyy-MM-dd hh:mm:ss"))
                else:
                    updated_at = QDate.fromString(updated_at_str, Qt.ISODate)
                    self.updated_at_input.setText(updated_at.toString("yyyy-MM-dd"))
            else:
                self.updated_at_input.setText("غير معروف")
            
        except Exception as e:
            print(f"Error loading user dates info: {e}")
            self.created_by_input.setText("خطأ في التحميل")
            self.created_at_input.setText("خطأ في التحميل")
            self.updated_by_input.setText("خطأ في التحميل")
            self.updated_at_input.setText("خطأ في التحميل")

    def debug_user_data(self):
        """دالة لفحص بيانات المستخدمين للتdebug"""
        try:
            conn = get_financials_db_connection()
            if conn:
                cursor = conn.cursor()
                # جلب كل المستخدمين
                cursor.execute("SELECT id, username, name_ar, name_en FROM users")
                users = cursor.fetchall()
                conn.close()
            
                print("=== DEBUG: All Users ===")
                for user in users:
                    print(f"ID: {user[0]}, Username: {user[1]}, Name_ar: {user[2]}, Name_en: {user[3]}")
                
        except Exception as e:
            print(f"Debug error: {e}")


    def clear_form(self):
        self.current_journal_entry_id = None
        self.set_next_entry_number()
        self.entry_date_input.setDate(QDate.currentDate())
        self.description_input.clear()
        self.tranaction_type_combo.setCurrentIndex(0)
        self.search_input.clear()
        
        # Reset user and date fields to current user/date
        current_user_name = self.get_current_user_name()
        current_datetime = QDateTime.currentDateTime()
        
        self.created_by_input.setText(current_user_name)
        self.updated_by_input.setText(current_user_name)
        self.created_at_input.setText(current_datetime.toString("yyyy-MM-dd hh:mm:ss"))
        self.updated_at_input.setText(current_datetime.toString("yyyy-MM-dd hh:mm:ss"))

        self.lines_table.setRowCount(0)
        self.add_empty_line()
        self.calculate_totals()
        self.update_main_buttons_state()

    def update_main_buttons_state(self):
        is_entry_selected = (self.current_journal_entry_id is not None)
        self.save_btn.setEnabled(not is_entry_selected)
        self.update_entry_btn.setEnabled(is_entry_selected)
        self.delete_entry_btn.setEnabled(is_entry_selected)

    def load_entry_for_edit(self, entry_details, entry_lines):
        self.current_journal_entry_id = entry_details['id']
        self.entry_number_input.setText(entry_details['entry_number'])
        self.entry_date_input.setDate(QDate.fromString(entry_details['entry_date'], Qt.ISODate))
        self.description_input.setText(entry_details['description'])

        index = self.tranaction_type_combo.findData(entry_details['transaction_type_id'])
        if index >= 0:
            self.tranaction_type_combo.setCurrentIndex(index)

        self.lines_table.setRowCount(0)
        for line in entry_lines:
            account_data = self.account_manager.get_account_by_id(line['account_id'])
            self.add_empty_line(account_data=account_data, line_data=line)

        self.calculate_totals()
        self.update_main_buttons_state()

    def load_journal_entries(self):
        pass

    def focus_next_widget(self):
        if self.focusNextChild():
            next_focused_widget = self.focusWidget()
            if next_focused_widget:
                if isinstance(next_focused_widget, QComboBox):
                    next_focused_widget.showPopup()
                elif isinstance(next_focused_widget, QDateEdit):
                    next_focused_widget.lineEdit().selectAll()
                elif isinstance(next_focused_widget, QLineEdit) or isinstance(next_focused_widget, CustomLineEditForNumbers):
                    next_focused_widget.selectAll()
        else:
            self.lines_table.setFocus()
            if self.lines_table.rowCount() > 0:
                self.lines_table.setCurrentCell(0, 1)
                self._activate_cell_editor(0, 1)

    def _lines_table_key_press_event(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            current_row = self.lines_table.currentRow()
            current_col = self.lines_table.currentColumn()
            
            navigable_columns = [1, 3, 4, 5, 6, 7, 8, 9]

            try:
                current_nav_idx = navigable_columns.index(current_col)
            except ValueError:
                next_col_after_non_navigable = -1
                for i in range(current_col + 1, self.lines_table.columnCount()):
                    if i in navigable_columns:
                        next_col_after_non_navigable = i
                        break
                
                if next_col_after_non_navigable != -1:
                    self.lines_table.setCurrentCell(current_row, next_col_after_non_navigable)
                    self._activate_cell_editor(current_row, next_col_after_non_navigable)
                else:
                    if current_row < self.lines_table.rowCount() - 1:
                        self.lines_table.setCurrentCell(current_row + 1, navigable_columns[0])
                        self._activate_cell_editor(current_row + 1, navigable_columns[0])
                    else:
                        self.add_empty_line()
                        new_row = self.lines_table.rowCount() - 1
                        new_col = navigable_columns[0]
                        self.lines_table.setCurrentCell(new_row, new_col)
                        self._activate_cell_editor(new_row, new_col)
                return

            next_nav_idx = current_nav_idx + 1
            
            if next_nav_idx < len(navigable_columns):
                next_col = navigable_columns[next_nav_idx]
                self.lines_table.setCurrentCell(current_row, next_col)
                self._activate_cell_editor(current_row, next_col)
            else:
                if current_row < self.lines_table.rowCount() - 1:
                    next_row = current_row + 1
                    next_col = navigable_columns[0]
                    self.lines_table.setCurrentCell(next_row, next_col)
                    self._activate_cell_editor(next_row, next_col)
                else:
                    self.add_empty_line()
                    new_row = self.lines_table.rowCount() - 1
                    new_col = navigable_columns[0]
                    self.lines_table.setCurrentCell(new_row, new_col)
                    self._activate_cell_editor(new_row, new_col)
        else:
            QTableWidget.keyPressEvent(self.lines_table, event)

    def _activate_cell_editor(self, row, col):
        widget = self.lines_table.cellWidget(row, col)
        if widget:
            widget.setFocus()
            if isinstance(widget, QLineEdit):
                widget.selectAll()
            elif isinstance(widget, CustomLineEditForNumbers):
                widget.selectAll()
            elif isinstance(widget, QComboBox):
                widget.showPopup()
        else:
            item = self.lines_table.item(row, col)
            if item and (item.flags() & Qt.ItemIsEditable):
                self.lines_table.editItem(item)
                editor = self.lines_table.focusWidget()
                if editor:
                    editor.setFocus()
                    if isinstance(editor, QLineEdit):
                        editor.selectAll()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Initialize database schema and populate default data for testing
    conn = None
    try:
        print("DEBUG: Attempting to get financials DB connection...")
        conn = get_financials_db_connection()
        if conn:
            print("DEBUG: Connection to financials DB successful.")
            try:
                cursor = conn.cursor()
                print("DEBUG: Checking for 'journal_entries' table existence...")
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='journal_entries';")
                journal_entries_table_exists = cursor.fetchone() 
                
                if not journal_entries_table_exists: 
                    print("Financials DB schema (journal_entries table) not found. Initializing full schema...")
                    cursor.executescript(FINANCIALS_SCHEMA_SCRIPT)
                    conn.commit()
                    print("Financials DB schema initialized.")
                    
                    try:
                        print("DEBUG: Attempting to insert default data...")
                        insert_default_data(conn)
                        print("Default lookups, accounts, and dummy journal entries populated.")
                    except Exception as e: 
                        print(f"WARNING: Error populating default data after schema init: {e}.")
                        import traceback
                        traceback.print_exc()
                else:
                    print("Financials DB (journal_entries table) already exists. Ensuring default data is present.")
                    try:
                        print("DEBUG: Ensuring default data is present (INSERT OR IGNORE)...")
                        insert_default_data(conn)
                        print("Ensured default data is present (INSERT OR IGNORE).")
                    except Exception as e:
                        print(f"WARNING: Error ensuring default data is present: {e}")
                        import traceback
                        traceback.print_exc()

            except sqlite3.Error as e:
                QMessageBox.critical(None, "خطأ في قاعدة البيانات", f"فشل التحقق أو تهيئة المخطط: {e}")
                print(f"ERROR: SQLite error during schema check/init: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
            finally:
                if conn:
                    conn.close()
                    print("DEBUG: Connection closed after schema/data check.")
        else:
            QMessageBox.critical(None, "خطأ في الاتصال", "فشل الاتصال بقاعدة البيانات المالية.")
            print("ERROR: Failed to get financials DB connection.")
            sys.exit(1)
                
    except Exception as e:
        QMessageBox.critical(None, "خطأ في تشغيل التطبيق", f"حدث خطأ غير متوقع أثناء تهيئة التطبيق: {e}")
        print(f"CRITICAL ERROR: Unhandled exception during app initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Determine the path to the QSS file
    qss_file_path = os.path.join(current_dir, '..', '..', 'ui', 'styles', 'styles.qss')

    # Load and apply the QSS file
    app_stylesheet = load_qss_file(qss_file_path)
    if app_stylesheet:
        app.setStyleSheet(app_stylesheet)
        print("DEBUG: Applied DFD-001 stylesheet.")
    else:
        print("WARNING: Failed to load stylesheet. UI might not be consistent.")

    print("DEBUG: Initializing JournalManager...")
    try:
        test_journal_manager = JournalManager(get_financials_db_connection)
        print("DEBUG: JournalManager initialized successfully.")
    except Exception as e:
        QMessageBox.critical(None, "خطأ في تهيئة المدير", f"فشل تهيئة JournalManager: {e}")
        print(f"ERROR: Failed to initialize JournalManager: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("DEBUG: Creating and showing NewJournalEntryManagementWindow...")
    try:
        window = NewJournalEntryManagementWindow(
            journal_manager=test_journal_manager,
            lookup_manager=FinancialLookupsManager(get_financials_db_connection),
            account_manager=AccountManager(get_financials_db_connection)
        )
        window.showMaximized()
        print("DEBUG: Window shown. Starting application event loop...")
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, "خطأ في عرض الواجهة", f"حدث خطأ غير متوقع أثناء عرض الواجهة: {e}")
        print(f"ERROR: Unhandled exception during window display or event loop: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
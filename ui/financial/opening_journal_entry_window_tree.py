# opening_journal_entry_window_tree.py

import sys
import os
import sqlite3
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QHeaderView, QDialog, QMessageBox, QDateEdit, QGroupBox,
    QSpinBox, QApplication, QTreeWidgetItem, QTreeWidget, QFrame,
    QTreeWidgetItemIterator, QGridLayout, QDialogButtonBox, QFormLayout,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QComboBox,QStyle,
    QInputDialog, QCheckBox
)
from PyQt5.QtCore import Qt, QDate, QLocale, QTimer
from PyQt5.QtGui import QFont, QIcon, QDoubleValidator

# --- Database Connection Function ---
DATABASE_NAME = "financials.db"

def get_db_connection():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        db_path = os.path.join(project_root, 'database', DATABASE_NAME)
        
        if not os.path.exists(db_path):
            QMessageBox.critical(None, "Fatal Error", f"Database not found at: {db_path}")
            return None

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        QMessageBox.critical(None, "Connection Error", f"Failed to connect to database: {e}")
        return None

# --- Analysis Details Dialog (No changes needed here) ---
class AnalysisDetailsDialog(QDialog):
    def __init__(self, account_name, document_types_map, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"تفاصيل تحليل - {account_name}")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(600, 400)
        
        self.document_types_map = document_types_map
        self.reversed_doc_map = {v: k for k, v in document_types_map.items()}
        self.lines = []
        
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["نوع المستند", "رقم المستند", "المبلغ", "ملاحظات"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        table_buttons_layout = QHBoxLayout()
        self.add_row_button = QPushButton("إضافة سطر")
        self.delete_row_button = QPushButton("حذف السطر")
        table_buttons_layout.addWidget(self.add_row_button)
        table_buttons_layout.addWidget(self.delete_row_button)
        table_buttons_layout.addStretch()

        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_buttons.button(QDialogButtonBox.Ok).setText("موافق")
        dialog_buttons.button(QDialogButtonBox.Cancel).setText("إلغاء")

        main_layout.addWidget(self.table)
        main_layout.addLayout(table_buttons_layout)
        main_layout.addWidget(dialog_buttons)

        self.add_row_button.clicked.connect(self.add_row)
        self.delete_row_button.clicked.connect(self.delete_row)
        dialog_buttons.accepted.connect(self.on_accept)
        dialog_buttons.rejected.connect(self.reject)

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #f8f9fa; }
            QTableWidget { font-size: 13px; }
            QPushButton { background-color: #007bff; color: white; border: none; padding: 8px 12px; border-radius: 4px; }
            QPushButton:hover { background-color: #0056b3; }
        """)

    def add_row(self, data=None):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        doc_type_combo = QComboBox()
        doc_type_combo.addItems(self.document_types_map.values())
        self.table.setCellWidget(row_position, 0, doc_type_combo)

        amount_item = QTableWidgetItem("0.00")
        amount_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row_position, 2, amount_item)

        if data:
            doc_type_name = self.document_types_map.get(data.get('document_type_id'))
            if doc_type_name:
                doc_type_combo.setCurrentText(doc_type_name)
            self.table.setItem(row_position, 1, QTableWidgetItem(data.get('document_number', '')))
            self.table.item(row_position, 2).setText(str(data.get('amount', 0.0)))
            self.table.setItem(row_position, 3, QTableWidgetItem(data.get('notes', '')))

    def delete_row(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)

    def on_accept(self):
        self.lines = []
        total = 0.0
        for row in range(self.table.rowCount()):
            try:
                doc_type_name = self.table.cellWidget(row, 0).currentText()
                doc_type_id = self.reversed_doc_map.get(doc_type_name)
                doc_number = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
                amount = float(self.table.item(row, 2).text())
                notes = self.table.item(row, 3).text() if self.table.item(row, 3) else ""

                if amount > 0:
                    self.lines.append({
                        'document_type_id': doc_type_id,
                        'document_number': doc_number,
                        'amount': amount,
                        'notes': notes
                    })
                    total += amount
            except (ValueError, AttributeError):
                QMessageBox.warning(self, "Invalid Data", f"Please enter a valid amount in row {row + 1}.")
                return
        
        self.accept()

    def get_data(self):
        return self.lines, sum(line['amount'] for line in self.lines)
    
    def set_data(self, lines):
        for line in lines:
            self.add_row(line)

# --- New Search Dialog for Journal Entries ---
class SearchJournalEntryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("بحث عن قيد افتتاحي")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(800, 500)
        self.selected_entry_id = None # To store the ID of the selected entry

        self.init_ui()
        self.apply_styles()
        self.search_entries() # Perform initial search on dialog open

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Search criteria inputs
        search_group = QGroupBox("معايير البحث")
        search_layout = QGridLayout(search_group)
        
        search_layout.addWidget(QLabel("رقم القيد:"), 0, 0)
        self.entry_number_input = QLineEdit()
        search_layout.addWidget(self.entry_number_input, 0, 1)

        search_layout.addWidget(QLabel("الوصف:"), 0, 2)
        self.description_input = QLineEdit()
        search_layout.addWidget(self.description_input, 0, 3)

        search_layout.addWidget(QLabel("من تاريخ:"), 1, 0)
        self.start_date_input = QDateEdit(calendarPopup=True)
        self.start_date_input.setDisplayFormat("yyyy-MM-dd")
        self.start_date_input.setDate(QDate.currentDate().addYears(-1)) # Default to last year
        search_layout.addWidget(self.start_date_input, 1, 1)

        search_layout.addWidget(QLabel("إلى تاريخ:"), 1, 2)
        self.end_date_input = QDateEdit(calendarPopup=True)
        self.end_date_input.setDisplayFormat("yyyy-MM-dd")
        self.end_date_input.setDate(QDate.currentDate())
        search_layout.addWidget(self.end_date_input, 1, 3)

        # New checkbox to filter for opening entries only
        self.opening_entries_only_checkbox = QCheckBox("عرض القيود الافتتاحية فقط")
        self.opening_entries_only_checkbox.setChecked(True) # Default to true as per user request
        search_layout.addWidget(self.opening_entries_only_checkbox, 2, 0, 1, 4) # Span across columns

        self.search_button = QPushButton("بحث")
        self.search_button.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        search_layout.addWidget(self.search_button, 0, 4, 3, 1) # Span 3 rows to accommodate checkbox

        main_layout.addWidget(search_group)

        # Search results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["رقم القيد", "التاريخ", "الوصف", "مدين كلي", "دائن كلي"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Make table read-only

        main_layout.addWidget(self.results_table)

        # Dialog buttons
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_buttons.button(QDialogButtonBox.Ok).setText("اختيار")
        dialog_buttons.button(QDialogButtonBox.Cancel).setText("إلغاء")
        main_layout.addWidget(dialog_buttons)

        # Connect signals
        self.search_button.clicked.connect(self.search_entries)
        self.results_table.doubleClicked.connect(self.on_accept) # Double click to select and close
        dialog_buttons.accepted.connect(self.on_accept)
        dialog_buttons.rejected.connect(self.reject)

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #F8F9F9; }
            QGroupBox { 
                font-weight: bold; 
                border: 1px solid #D5D8DC; 
                border-radius: 8px; 
                margin-top: 10px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
            }
            QLineEdit, QDateEdit {
                padding: 5px;
                border: 1px solid #ced4da;
                border-radius: 4px;
            }
            QPushButton { 
                background-color: #007bff; 
                color: white; 
                border: none; 
                padding: 8px 12px; 
                border-radius: 4px; 
            }
            QPushButton:hover { background-color: #0056b3; }
            QTableWidget { 
                background-color: white;
                border: 1px solid #BDC3C7;
                border-radius: 8px;
                gridline-color: #E5E8E8;
                alternate-background-color: #F8F9F9;
                color: #2C3E50;
                font-size: 9pt;
            }
            QHeaderView::section {
                background-color: #34495E;
                color: white;
                padding: 8px;
                border: 1px solid #BDC3C7;
                font-weight: bold;
                text-align: center;
            }
            QTableWidget::item {
                padding: 7px;
                text-align: right;
                color: #2C3E50;
            }
            QTableWidget::item:selected {
                background-color: #D6EAF8;
                color: #2C3E50;
                font-weight: bold;
            }
        """)

    def search_entries(self):
        conn = get_db_connection()
        if not conn: return
        
        entry_number = self.entry_number_input.text().strip()
        description = self.description_input.text().strip()
        start_date = self.start_date_input.date().toString("yyyy-MM-dd")
        end_date = self.end_date_input.date().toString("yyyy-MM-dd")
        only_opening_entries = self.opening_entries_only_checkbox.isChecked() # Get checkbox state

        query = "SELECT id, entry_number, entry_date, description, total_debit, total_credit FROM journal_entries WHERE 1=1"
        params = []

        if entry_number:
            query += " AND entry_number LIKE ?"
            params.append(f"%{entry_number}%")
        if description:
            query += " AND description LIKE ?"
            params.append(f"%{description}%")
        
        # Filter for opening entries if checkbox is checked
        if only_opening_entries:
            query += " AND description LIKE ?"
            params.append("قيد افتتاحي للسنة المالية%") # Filter by description pattern

        query += " AND entry_date BETWEEN ? AND ?"
        params.append(start_date)
        params.append(end_date)

        query += " ORDER BY entry_date DESC, entry_number DESC"

        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            self.display_results(results)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to search entries: {e}")
        finally:
            conn.close()

    def display_results(self, results):
        self.results_table.setRowCount(0)
        # Ensure the table has enough columns for the hidden ID
        if self.results_table.columnCount() < 6:
            self.results_table.setColumnCount(6) # Add a 6th column for ID
        self.results_table.setColumnHidden(5, True) # Hide the ID column

        for row_idx, row_data in enumerate(results):
            self.results_table.insertRow(row_idx)
            self.results_table.setItem(row_idx, 0, QTableWidgetItem(row_data['entry_number']))
            self.results_table.setItem(row_idx, 1, QTableWidgetItem(row_data['entry_date']))
            self.results_table.setItem(row_idx, 2, QTableWidgetItem(row_data['description']))
            
            debit_item = QTableWidgetItem(f"{row_data['total_debit']:,.2f}")
            debit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.results_table.setItem(row_idx, 3, debit_item)

            credit_item = QTableWidgetItem(f"{row_data['total_credit']:,.2f}")
            credit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.results_table.setItem(row_idx, 4, credit_item)
            
            # Store the journal_entry_id in the 6th column (index 5)
            self.results_table.setItem(row_idx, 5, QTableWidgetItem(str(row_data['id']))) 

        self.results_table.resizeColumnsToContents()

    def on_accept(self):
        selected_rows = self.results_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select an entry to load.")
            self.selected_entry_id = None # Ensure ID is reset if nothing selected
            return

        # Get the ID from the hidden column of the selected row
        row = selected_rows[0].row()
        item_id = self.results_table.item(row, 5) # Get the QTableWidgetItem
        
        if item_id is not None: # Check if the item exists
            self.selected_entry_id = int(item_id.text())
            self.accept() # Close the dialog
        else:
            QMessageBox.warning(self, "Error", "Selected row does not contain valid entry ID.")
            self.selected_entry_id = None # Reset ID if invalid item
            self.reject() # Reject the dialog to keep it open or handle as needed

    def get_selected_entry_id(self):
        return self.selected_entry_id


# --- Main Opening Journal Entry Window ---
class OpeningJournalEntryWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setLocale(QLocale(QLocale.Arabic, QLocale.Egypt))

        self.all_accounts_data = {}
        self.analytical_lines = {} # Stores analytical lines for each final account
        self.document_types_map = {}
        self.current_journal_entry_id = None # Tracks the ID of the currently loaded entry (for editing)
        
        if not self.load_initial_data():
            QTimer.singleShot(0, self.close)
            return

        self.init_ui()
        self.build_account_tree()
        self.apply_styles()
        self.new_entry() # Start with a new entry form

    def load_initial_data(self):
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            sql = """
                SELECT acc.id, acc.acc_code, acc.account_name_ar, acc.parent_account_id, 
                       acc.is_final, at.account_side
                FROM accounts acc
                JOIN account_types at ON acc.account_type_id = at.id
                WHERE acc.is_active = 1 AND acc.is_balance_sheet = 1
            """
            accounts_list = cursor.execute(sql).fetchall()
            if not accounts_list:
                QMessageBox.critical(self, "Data Error", "No balance sheet accounts found in chart of accounts. Please define them first.")
                conn.close()
                return False
            self.all_accounts_data = {dict(row)['id']: dict(row) for row in accounts_list}
            doc_types_list = cursor.execute("SELECT id, name_ar FROM document_types WHERE is_active = 1").fetchall()
            self.document_types_map = {row['id']: row['name_ar'] for row in doc_types_list}
            conn.close()
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            if conn: conn.close()
            return False

    def get_next_entry_number(self):
        conn = get_db_connection()
        if not conn: return "Error-DB"
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT entry_number FROM journal_entries ORDER BY id DESC LIMIT 1")
            last_entry = cursor.fetchone()
            conn.close()
            if last_entry and last_entry['entry_number']:
                prefix = ''.join(filter(str.isalpha, last_entry['entry_number'])) or 'JE'
                last_num_str = ''.join(filter(str.isdigit, last_entry['entry_number']))
                if last_num_str:
                    next_num = int(last_num_str) + 1
                    return f"{prefix}-{next_num:05d}"
            return "JE-00001"
        except sqlite3.Error as e:
            print(f"Error getting next entry number: {e}")
            if conn: conn.close()
            return "Error-SQL"

    def init_ui(self):
        self.setWindowTitle("القيد الافتتاحي")
        self.setGeometry(100, 100, 1200, 800)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        header_group = QGroupBox("بيانات القيد الأساسية")
        header_layout = QGridLayout(header_group)
        header_layout.setSpacing(10)
        self.entry_id_label = QLabel()
        self.fiscal_year_spinbox = QSpinBox()
        self.fiscal_year_spinbox.setRange(2000, 2100)
        self.entry_date_edit = QDateEdit(calendarPopup=True)
        self.entry_date_edit.setReadOnly(True) # Date is derived from fiscal year for opening entries
        self.description_textEdit = QLineEdit()
        self.description_textEdit.setPlaceholderText("اكتب وصفًا للقيد هنا...")
        header_layout.addWidget(QLabel("<b>رقم القيد:</b>"), 0, 0)
        header_layout.addWidget(self.entry_id_label, 0, 1)
        header_layout.addWidget(QLabel("<b>السنة المالية:</b>"), 0, 2)
        header_layout.addWidget(self.fiscal_year_spinbox, 0, 3)
        header_layout.addWidget(QLabel("<b>التاريخ:</b>"), 1, 0)
        header_layout.addWidget(self.entry_date_edit, 1, 1)
        header_layout.addWidget(QLabel("<b>الوصف:</b>"), 1, 2)
        header_layout.addWidget(self.description_textEdit, 1, 3, 1, 2)
        
        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["الحساب", "الكود", "مدين", "دائن"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)

        footer_frame = QFrame()
        footer_frame.setFrameShape(QFrame.StyledPanel)
        footer_layout = QVBoxLayout(footer_frame)
        
        totals_layout = QHBoxLayout()
        self.debit_total_label = QLabel("إجمالي المدين: 0.00")
        self.credit_total_label = QLabel("إجمالي الدائن: 0.00")
        self.difference_label = QLabel("الفرق: 0.00")
        totals_layout.addWidget(self.debit_total_label)
        totals_layout.addStretch(1)
        totals_layout.addWidget(self.credit_total_label)
        totals_layout.addStretch(1)
        totals_layout.addWidget(self.difference_label)
        
        buttons_layout = QHBoxLayout()
        self.search_button = QPushButton("بحث")
        self.edit_button = QPushButton("تعديل")
        self.new_button = QPushButton("جديد")
        self.save_button = QPushButton("حفظ")
        self.exit_button = QPushButton("خروج")
        
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.search_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.new_button)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.exit_button)

        footer_layout.addLayout(totals_layout)
        footer_layout.addLayout(buttons_layout)

        main_layout.addWidget(header_group)
        main_layout.addWidget(self.tree, 1)
        main_layout.addWidget(footer_frame)

        self.fiscal_year_spinbox.valueChanged.connect(self.update_entry_date_and_description)
        self.tree.itemChanged.connect(self.on_tree_item_changed)
        self.tree.itemDoubleClicked.connect(self.on_tree_item_double_clicked)
        self.new_button.clicked.connect(self.new_entry)
        self.save_button.clicked.connect(self.save_journal_entry)
        self.exit_button.clicked.connect(self.close)
        
        self.search_button.clicked.connect(self.search_entry)
        self.edit_button.clicked.connect(self.edit_entry)

    def apply_styles(self):
        self.setFont(QFont("Segoe UI", 10))
        font_bold = QFont("Segoe UI", 11)
        font_bold.setBold(True)
        
        self.debit_total_label.setFont(font_bold)
        self.credit_total_label.setFont(font_bold)
        self.difference_label.setFont(font_bold)
        self.entry_id_label.setFont(font_bold)
        
        self.setStyleSheet("""
            QWidget { background-color: #FDFEFE; }
            QGroupBox { 
                font-weight: bold; 
                border: 1px solid #D5D8DC; 
                border-radius: 8px; 
                margin-top: 10px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
            }
            QTreeWidget { 
                font-size: 14px; 
                border: 1px solid #D5D8DC;
                border-radius: 5px;
            }
            QHeaderView::section { 
                background-color: #34495E; 
                color: white; 
                padding: 6px; 
                font-weight: bold; 
                border: 1px solid #34495E;
            }
            QPushButton { 
                font-size: 12px; 
                padding: 8px 20px; 
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton#save_button {
                background-color: #28a745; /* Green */
                color: white;
            }
            QPushButton#save_button:hover { background-color: #218838; }
            QPushButton#new_button {
                background-color: #007bff; /* Blue */
                color: white;
            }
            QPushButton#new_button:hover { background-color: #0069d9; }
            QPushButton#exit_button {
                background-color: #6c757d; /* Gray */
                color: white;
            }
            QPushButton#exit_button:hover { background-color: #5a6268; }
            
            QPushButton#search_button {
                background-color: #ffc107; /* Yellow/Orange */
                color: #343a40; /* Dark text for contrast */
            }
            QPushButton#search_button:hover { background-color: #e0a800; }
            QPushButton#edit_button {
                background-color: #17a2b8; /* Cyan/Teal */
                color: white;
            }
            QPushButton#edit_button:hover { background-color: #138496; }
            QLineEdit, QDateEdit, QSpinBox {
                padding: 5px;
                border: 1px solid #ced4da;
                border-radius: 4px;
            }
            QCheckBox { /* Style for the new checkbox */
                spacing: 5px;
                color: #34495E;
                font-weight: bold;
            }
        """)
        self.save_button.setObjectName("save_button")
        self.new_button.setObjectName("new_button")
        self.exit_button.setObjectName("exit_button")
        self.search_button.setObjectName("search_button")
        self.edit_button.setObjectName("edit_button")

    def build_account_tree(self):
        self.tree.clear()
        items = {}
        for acc_id, account in self.all_accounts_data.items():
            item = QTreeWidgetItem([account['account_name_ar'], account['acc_code'], "0.00", "0.00"])
            item.setData(0, Qt.UserRole, acc_id)
            font = item.font(0)
            if not account['is_final']:
                font.setBold(True)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            else:
                font.setItalic(True)
                item.setText(0, f"  - {account['account_name_ar']} [...]")
                item.setToolTip(0, "Double-click to add details or directly edit balance")
                item.setFlags(item.flags() | Qt.ItemIsEditable)
            item.setFont(0, font)
            items[acc_id] = item
        for acc_id, account in self.all_accounts_data.items():
            parent_id = account.get('parent_account_id')
            if parent_id in items:
                items[parent_id].addChild(items[acc_id])
            elif not parent_id:
                self.tree.addTopLevelItem(items[acc_id])
        self.tree.expandAll()

    def new_entry(self):
        self.current_journal_entry_id = None # Reset current entry ID
        next_entry_num = self.get_next_entry_number()
        self.entry_id_label.setText(f"<b>{next_entry_num}</b>")
        self.fiscal_year_spinbox.setValue(QDate.currentDate().year())
        self.update_entry_date_and_description()
        self.description_textEdit.setText(f"قيد افتتاحي للسنة المالية {self.fiscal_year_spinbox.value()}") # Reset description
        self.description_textEdit.setReadOnly(False) # Ensure description is editable for new entries
        self.fiscal_year_spinbox.setReadOnly(False) # Ensure fiscal year is editable for new entries

        self.analytical_lines.clear()
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            item.setText(2, "0.00")
            item.setText(3, "0.00")
            item.setFlags(item.flags() | Qt.ItemIsEditable) # Ensure final accounts are editable
            iterator += 1
        self.update_totals()
        self.save_button.setEnabled(True) # Enable save for new entry

    def update_entry_date_and_description(self):
        year = self.fiscal_year_spinbox.value()
        self.entry_date_edit.setDate(QDate(year, 1, 1))
        # self.description_textEdit.setText(f"قيد افتتاحي للسنة المالية {year}") # Removed to allow manual edit on new

    def on_tree_item_changed(self, item, column):
        if column not in [2, 3]: return
        self.tree.blockSignals(True)
        try:
            value = float(item.text(column).replace(',', ''))
            if value < 0: value = 0
            if column == 2 and value > 0: item.setText(3, "0.00")
            elif column == 3 and value > 0: item.setText(2, "0.00")
            item.setText(column, f"{value:,.2f}")
            
            # Clear analytical lines if direct edit
            acc_id = item.data(0, Qt.UserRole)
            if acc_id in self.analytical_lines:
                self.analytical_lines.pop(acc_id)

            self.update_parent_totals(item)
        except (ValueError, TypeError):
            item.setText(column, "0.00")
        self.tree.blockSignals(False)
        self.update_totals()

    def on_tree_item_double_clicked(self, item, column):
        acc_id = item.data(0, Qt.UserRole)
        account = self.all_accounts_data.get(acc_id)
        if not (account and account['is_final']): return
        
        dialog = AnalysisDetailsDialog(account['account_name_ar'], self.document_types_map, self)
        if acc_id in self.analytical_lines:
            dialog.set_data(self.analytical_lines[acc_id])
            
        if dialog.exec_() == QDialog.Accepted:
            lines, total = dialog.get_data()
            self.analytical_lines[acc_id] = lines
            self.tree.blockSignals(True)
            if account.get('account_side', '').lower() == 'credit':
                item.setText(2, "0.00")
                item.setText(3, f"{total:,.2f}")
            else:
                item.setText(2, f"{total:,.2f}")
                item.setText(3, "0.00")
            self.update_parent_totals(item)
            self.tree.blockSignals(False)
            self.update_totals()

    def update_parent_totals(self, item):
        parent = item.parent()
        while parent:
            debit_sum = sum(float(parent.child(i).text(2).replace(',', '')) for i in range(parent.childCount()))
            credit_sum = sum(float(parent.child(i).text(3).replace(',', '')) for i in range(parent.childCount()))
            parent.setText(2, f"{debit_sum:,.2f}")
            parent.setText(3, f"{credit_sum:,.2f}")
            parent = parent.parent()

    def update_totals(self):
        total_debit = sum(float(self.tree.topLevelItem(i).text(2).replace(',', '')) for i in range(self.tree.topLevelItemCount()))
        total_credit = sum(float(self.tree.topLevelItem(i).text(3).replace(',', '')) for i in range(self.tree.topLevelItemCount()))
        difference = total_debit - total_credit
        self.debit_total_label.setText(f"إجمالي المدين: {total_debit:,.2f}")
        self.credit_total_label.setText(f"إجمالي الدائن: {total_credit:,.2f}")
        self.difference_label.setText(f"الفرق: {difference:,.2f}")
        self.difference_label.setStyleSheet("color: #28a745; font-weight: bold;" if abs(difference) < 0.01 else "color: #dc3545; font-weight: bold;")

    def save_journal_entry(self):
        total_debit = float(self.debit_total_label.text().split(':')[1].strip().replace(',', ''))
        total_credit = float(self.credit_total_label.text().split(':')[1].strip().replace(',', ''))
        if abs(total_debit - total_credit) > 0.01:
            QMessageBox.warning(self, "Balance Error", "Cannot save an unbalanced entry.")
            return

        header_data = {
            'entry_number': self.entry_id_label.text().replace('<b>', '').replace('</b>', ''),
            'entry_date': self.entry_date_edit.date().toString("yyyy-MM-dd"),
            'description': self.description_textEdit.text(),
            'total_debit': total_debit,
            'total_credit': total_credit,
            'currency_id': 1,
            'transaction_type_id': None # Can specify a custom type for opening entry
        }
        
        lines_data = []
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            acc_id = item.data(0, Qt.UserRole)
            account = self.all_accounts_data.get(acc_id)
            if account and account['is_final']:
                if acc_id in self.analytical_lines and self.analytical_lines[acc_id]:
                    for line in self.analytical_lines[acc_id]:
                        debit, credit = (line['amount'], 0) if account['account_side'].lower() == 'debit' else (0, line['amount'])
                        lines_data.append({
                            'account_id': acc_id, 'debit': debit, 'credit': credit, 
                            'document_type_id': line['document_type_id'], 
                            'document_number': line['document_number'], 'notes': line['notes']
                        })
                else:
                    debit = float(item.text(2).replace(',', ''))
                    credit = float(item.text(3).replace(',', ''))
                    if debit > 0 or credit > 0:
                        lines_data.append({
                            'account_id': acc_id, 'debit': debit, 'credit': credit, 
                            'notes': 'Direct opening balance'
                        })
            iterator += 1

        if not lines_data:
            QMessageBox.warning(self, "Empty Entry", "Cannot save an empty entry.")
            return

        conn = get_db_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION;")

            if self.current_journal_entry_id: # Update existing entry
                # Delete old lines
                cursor.execute("DELETE FROM journal_entry_lines WHERE journal_entry_id = ?", (self.current_journal_entry_id,))
                # Update header
                header_sql = """
                    UPDATE journal_entries SET
                    entry_number = :entry_number, entry_date = :entry_date, description = :description,
                    total_debit = :total_debit, total_credit = :total_credit, currency_id = :currency_id,
                    transaction_type_id = :transaction_type_id
                    WHERE id = :id
                """
                header_data['id'] = self.current_journal_entry_id
                cursor.execute(header_sql, header_data)
                journal_entry_id = self.current_journal_entry_id
                QMessageBox.information(self, "Success", f"Entry updated successfully with number: {header_data['entry_number']}")
            else: # Insert new entry
                header_sql = """
                    INSERT INTO journal_entries 
                    (entry_number, entry_date, description, total_debit, total_credit, currency_id, transaction_type_id) 
                    VALUES (:entry_number, :entry_date, :description, :total_debit, :total_credit, :currency_id, :transaction_type_id)
                """
                cursor.execute(header_sql, header_data)
                journal_entry_id = cursor.lastrowid
                QMessageBox.information(self, "Success", f"Entry saved successfully with number: {header_data['entry_number']}")
            
            lines_sql = """
                INSERT INTO journal_entry_lines 
                (journal_entry_id, account_id, debit, credit, document_type_id, document_number, notes) 
                VALUES (:journal_entry_id, :account_id, :debit, :credit, :document_type_id, :document_number, :notes)
            """
            for line in lines_data:
                line['journal_entry_id'] = journal_entry_id
                line.setdefault('document_type_id', None)
                line.setdefault('document_number', None)
                line.setdefault('notes', None)
                cursor.execute(lines_sql, line)
            
            conn.commit()
            self.new_entry() # Clear form after save/update
        except sqlite3.Error as e:
            conn.rollback()
            QMessageBox.critical(self, "Save Failed", f"Database error occurred:\n{e}")
        finally:
            if conn: conn.close()

    def search_entry(self):
        """
        Opens a search dialog to find existing journal entries.
        If an entry is selected, it loads its details into the main form.
        """
        search_dialog = SearchJournalEntryDialog(self)
        if search_dialog.exec_() == QDialog.Accepted:
            selected_id = search_dialog.get_selected_entry_id()
            if selected_id:
                self.load_journal_entry(selected_id)
            else:
                QMessageBox.information(self, "بحث", "لم يتم اختيار أي قيد.")

    def load_journal_entry(self, entry_id):
        """
        Loads the details of a specific journal entry into the UI.
        """
        conn = get_db_connection()
        if not conn: return

        try:
            # Fetch header data
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM journal_entries WHERE id = ?", (entry_id,))
            entry_header = cursor.fetchone()

            if not entry_header:
                QMessageBox.warning(self, "خطأ في التحميل", "القيد اليومي غير موجود.")
                return

            self.current_journal_entry_id = entry_id
            
            # Populate header fields
            self.entry_id_label.setText(f"<b>{entry_header['entry_number']}</b>")
            self.entry_date_edit.setDate(QDate.fromString(entry_header['entry_date'], "yyyy-MM-dd"))
            self.fiscal_year_spinbox.setValue(QDate.fromString(entry_header['entry_date'], "yyyy-MM-dd").year())
            self.description_textEdit.setText(entry_header['description'])

            # Disable editing for loaded entry until 'Edit' is clicked
            self.description_textEdit.setReadOnly(True)
            self.fiscal_year_spinbox.setReadOnly(True)
            self.save_button.setEnabled(False) # Disable save until edited

            # Clear existing tree data and analytical lines
            self.analytical_lines.clear()
            iterator = QTreeWidgetItemIterator(self.tree)
            while iterator.value():
                item = iterator.value()
                item.setText(2, "0.00")
                item.setText(3, "0.00")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable) # Make non-editable
                iterator += 1
            self.update_totals() # Reset totals to zero initially

            # Fetch and populate lines data
            cursor.execute("SELECT * FROM journal_entry_lines WHERE journal_entry_id = ?", (entry_id,))
            entry_lines = cursor.fetchall()

            temp_analytical_lines = {} # Temporarily store lines to update tree
            for line in entry_lines:
                acc_id = line['account_id']
                if acc_id not in temp_analytical_lines:
                    temp_analytical_lines[acc_id] = []
                
                # Store analytical line details
                temp_analytical_lines[acc_id].append({
                    'document_type_id': line['document_type_id'],
                    'document_number': line['document_number'],
                    'amount': line['debit'] if line['debit'] > 0 else line['credit'],
                    'notes': line['notes']
                })
            
            # Update tree items and analytical_lines dictionary
            iterator = QTreeWidgetItemIterator(self.tree)
            while iterator.value():
                item = iterator.value()
                acc_id = item.data(0, Qt.UserRole)
                account = self.all_accounts_data.get(acc_id)

                if account and account['is_final'] and acc_id in temp_analytical_lines:
                    self.analytical_lines[acc_id] = temp_analytical_lines[acc_id]
                    
                    # Calculate total for this account from its analytical lines
                    total_debit_for_account = sum(l['amount'] for l in temp_analytical_lines[acc_id] if account['account_side'].lower() == 'debit')
                    total_credit_for_account = sum(l['amount'] for l in temp_analytical_lines[acc_id] if account['account_side'].lower() == 'credit')

                    item.setText(2, f"{total_debit_for_account:,.2f}")
                    item.setText(3, f"{total_credit_for_account:,.2f}")
                    
                iterator += 1
            
            self.update_parent_totals_after_load() # Update parent totals after all lines are set
            self.update_totals() # Update overall totals

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ في التحميل", f"فشل تحميل القيد اليومي: {e}")
        finally:
            if conn: conn.close()

    def update_parent_totals_after_load(self):
        # This function is needed because update_parent_totals relies on itemChanged signal
        # which is blocked during loading. We need to manually propagate totals from bottom up.
        
        # First, reset all parent totals to zero
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            acc_id = item.data(0, Qt.UserRole)
            account = self.all_accounts_data.get(acc_id)
            if not account['is_final']: # Only for parent accounts
                item.setText(2, "0.00")
                item.setText(3, "0.00")
            iterator += 1

        # Then, re-calculate from final accounts upwards
        for acc_id, account in self.all_accounts_data.items():
            if account['is_final']:
                item = self.find_tree_item_by_id(acc_id)
                if item:
                    self.update_parent_totals(item) # Use existing function to propagate upwards

    def find_tree_item_by_id(self, acc_id):
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if item.data(0, Qt.UserRole) == acc_id:
                return item
            iterator += 1
        return None

    def edit_entry(self):
        """
        Enables editing of the currently displayed journal entry.
        """
        if self.current_journal_entry_id is None:
            QMessageBox.warning(self, "تعديل", "الرجاء البحث عن قيد وتحميله أولاً لتمكين التعديل.")
            return
        
        # Enable header fields for editing
        self.description_textEdit.setReadOnly(False)
        self.fiscal_year_spinbox.setReadOnly(False)
        self.save_button.setEnabled(True) # Enable save button

        # Enable editing for final accounts in the tree
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            acc_id = item.data(0, Qt.UserRole)
            account = self.all_accounts_data.get(acc_id)
            if account and account['is_final']:
                item.setFlags(item.flags() | Qt.ItemIsEditable)
            iterator += 1
        
        QMessageBox.information(self, "وضع التعديل", "تم تمكين وضع التعديل. يمكنك الآن تعديل القيد وحفظه.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OpeningJournalEntryWindow()
    window.show()
    sys.exit(app.exec_())


import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
                             QGroupBox, QDateEdit, QTextEdit, QDoubleSpinBox,QCompleter)
from PyQt5.QtCore import Qt, QDate
from datetime import datetime
import sqlite3

# --- إعداد المسارات ---
try:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
except NameError:
    project_root = os.getcwd()

if project_root not in sys.path:
    sys.path.append(project_root)

from database.db_connection import get_inventory_db_connection
from INVENTORY_MAIN import load_stylesheet

class DepartmentReturnUI(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.setWindowTitle("إذن ارتجاع من قسم إلى مخزن")
        self.setup_ui()
        self.setStyleSheet(load_stylesheet())
        self.load_initial_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        info_group = QGroupBox("معلومات إذن الارتجاع")
        info_layout = QHBoxLayout(info_group)
        self.from_department_combo = QComboBox()
        self.to_warehouse_combo = QComboBox()
        self.return_date = QDateEdit(QDate.currentDate())
        self.return_date.setCalendarPopup(True)
        info_layout.addWidget(QLabel("من قسم:"))
        info_layout.addWidget(self.from_department_combo)
        info_layout.addWidget(QLabel("إلى مخزن:"))
        info_layout.addWidget(self.to_warehouse_combo)
        info_layout.addWidget(QLabel("تاريخ الارتجاع:"))
        info_layout.addWidget(self.return_date)
        main_layout.addWidget(info_group)

        add_item_group = QGroupBox("إضافة صنف للإرجاع")
        add_item_layout = QHBoxLayout(add_item_group)
        
        self.item_combo = QComboBox()
        self.item_combo.setEditable(True)
        self.item_combo.setInsertPolicy(QComboBox.NoInsert)
        self.item_combo.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.item_combo.setMinimumWidth(300)
        self.item_combo.currentIndexChanged.connect(self.on_item_selected)

        self.unit_combo = QComboBox()
        self.quantity_spinbox = QDoubleSpinBox()
        self.quantity_spinbox.setRange(0.01, 10000.0)
        add_btn = QPushButton("➕ إضافة صنف")
        add_btn.setProperty("role", "add")
        add_btn.clicked.connect(self.add_item_to_table)

        add_item_layout.addWidget(QLabel("الصنف:"))
        add_item_layout.addWidget(self.item_combo)
        add_item_layout.addWidget(QLabel("الوحدة:"))
        add_item_layout.addWidget(self.unit_combo)
        add_item_layout.addWidget(QLabel("الكمية:"))
        add_item_layout.addWidget(self.quantity_spinbox)
        add_item_layout.addWidget(add_btn)
        main_layout.addWidget(add_item_group)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["ID الصنف", "اسم الصنف", "الكمية", "الوحدة", "إجراء"])
        self.items_table.setColumnHidden(0, True)
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        main_layout.addWidget(self.items_table)

        self.reason_edit = QTextEdit()
        self.reason_edit.setPlaceholderText("أدخل سبب الارتجاع...")
        self.reason_edit.setMaximumHeight(80)
        main_layout.addWidget(QLabel("سبب الارتجاع:"))
        main_layout.addWidget(self.reason_edit)

        button_layout = QHBoxLayout()
        save_btn = QPushButton("💾 حفظ إذن الارتجاع")
        save_btn.setProperty("role", "add")
        save_btn.clicked.connect(self.save_return)
        button_layout.addWidget(save_btn)
        main_layout.addLayout(button_layout)

    def execute_query(self, query, params=(), fetch=None):
        conn = get_inventory_db_connection()
        if not conn: return None
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetch == 'one': result = cursor.fetchone()
            elif fetch == 'all': result = cursor.fetchall()
            else: result = None
            conn.commit()
            return result
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ قاعدة بيانات", f"حدث خطأ: {e}")
            return None
        finally:
            if conn: conn.close()

    def load_initial_data(self):
        departments = self.execute_query("SELECT id, name_ar FROM departments WHERE is_active = 1", fetch='all')
        warehouses = self.execute_query("SELECT id, name_ar FROM warehouses WHERE is_active = 1", fetch='all')
        items = self.execute_query("SELECT id, item_name_ar, item_code FROM items WHERE is_active = 1", fetch='all')

        self.from_department_combo.addItem("-- اختر قسم --", None)
        if departments:
            for dept in departments:
                self.from_department_combo.addItem(dept['name_ar'], dept['id'])

        self.to_warehouse_combo.addItem("-- اختر مخزن --", None)
        if warehouses:
            for wh in warehouses:
                self.to_warehouse_combo.addItem(wh['name_ar'], wh['id'])

        self.item_combo.addItem("-- ابحث أو اختر صنف --", None)
        if items:
            for item in items:
                self.item_combo.addItem(f"{item['item_name_ar']} ({item['item_code']})", item['id'])

    def on_item_selected(self):
        self.unit_combo.clear()
        item_id = self.item_combo.currentData()
        if not item_id: return
        units = self.execute_query("SELECT u.id, u.name_ar FROM item_units iu JOIN units u ON iu.unit_id = u.id WHERE iu.item_id = ?", (item_id,), fetch='all')
        if units:
            for unit in units:
                self.unit_combo.addItem(unit['name_ar'], unit['id'])

    def add_item_to_table(self):
        item_id = self.item_combo.currentData()
        item_name = self.item_combo.currentText()
        unit_id = self.unit_combo.currentData()
        unit_name = self.unit_combo.currentText()
        quantity = self.quantity_spinbox.value()

        if not all([item_id, unit_id, quantity > 0]):
            QMessageBox.warning(self, "بيانات ناقصة", "يرجى اختيار صنف، وحدة، وتحديد كمية صحيحة.")
            return

        for row in range(self.items_table.rowCount()):
            if self.items_table.item(row, 0).text() == str(item_id):
                QMessageBox.information(self, "مكرر", "هذا الصنف موجود بالفعل في القائمة.")
                return

        row_count = self.items_table.rowCount()
        self.items_table.insertRow(row_count)
        self.items_table.setItem(row_count, 0, QTableWidgetItem(str(item_id)))
        self.items_table.setItem(row_count, 1, QTableWidgetItem(item_name))
        self.items_table.setItem(row_count, 2, QTableWidgetItem(str(quantity)))
        self.items_table.setItem(row_count, 3, QTableWidgetItem(unit_name))
        
        remove_btn = QPushButton("🗑️")
        remove_btn.setProperty("role", "delete")
        remove_btn.clicked.connect(lambda: self.items_table.removeRow(self.items_table.currentRow()))
        self.items_table.setCellWidget(row_count, 4, remove_btn)

    def save_return(self):
        from_dept = self.from_department_combo.currentData()
        to_warehouse = self.to_warehouse_combo.currentData()
        return_date = self.return_date.date().toString("yyyy-MM-dd")
        reason = self.reason_edit.toPlainText().strip()

        if not from_dept or not to_warehouse or not reason:
            QMessageBox.warning(self, "بيانات ناقصة", "يرجى تحديد القسم والمخزن وسبب الارتجاع.")
            return

        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, "بيانات ناقصة", "يجب إضافة صنف واحد على الأقل للإرجاع.")
            return

        try:
            conn = get_inventory_db_connection()
            cursor = conn.cursor()
            
            return_number = f"DR-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            cursor.execute("INSERT INTO department_returns (return_number, return_date, from_department_id, to_warehouse_id, reason, status) VALUES (?, ?, ?, ?, ?, 'completed')", (return_number, return_date, from_dept, to_warehouse, reason))
            return_id = cursor.lastrowid

            for row in range(self.items_table.rowCount()):
                item_id = int(self.items_table.item(row, 0).text())
                quantity = float(self.items_table.item(row, 2).text())
                unit_name = self.items_table.item(row, 3).text()
                
                unit_id_result = self.execute_query("SELECT id FROM units WHERE name_ar = ?", (unit_name,), fetch='one')
                unit_id = unit_id_result['id'] if unit_id_result else 1

                cursor.execute("INSERT INTO department_return_items (return_id, item_id, quantity, unit_id) VALUES (?, ?, ?, ?)", (return_id, item_id, quantity, unit_id))
                cursor.execute("INSERT INTO stock_transactions (transaction_number, transaction_date, item_id, warehouse_id, transaction_type, quantity, description) VALUES (?, ?, ?, ?, 'In', ?, ?)", (f"{return_number}-IN", return_date, item_id, to_warehouse, quantity, f"ارتجاع من قسم: {self.from_department_combo.currentText()}"))

            conn.commit()
            conn.close()
            QMessageBox.information(self, "نجاح", f"تم حفظ إذن الارتجاع رقم {return_number} بنجاح.")
            self.clear_form()

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل حفظ إذن الارتجاع: {e}")

    def clear_form(self):
        self.from_department_combo.setCurrentIndex(0)
        self.to_warehouse_combo.setCurrentIndex(0)
        self.item_combo.setCurrentIndex(0)
        self.unit_combo.clear()
        self.quantity_spinbox.setValue(0.01)
        self.items_table.setRowCount(0)
        self.reason_edit.clear()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    # مسار قاعدة البيانات (ممكن تحدده هنا أو تخليه ثابت)
    db_path = os.path.join(project_root, "inventory.db")

    window = DepartmentReturnUI(db_path)
    window.resize(900, 600)  # حجم مناسب للشاشة
    window.show()

    sys.exit(app.exec_())

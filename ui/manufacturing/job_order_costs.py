import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QMessageBox, QCompleter, QDateEdit, QFrame,
    QGroupBox, QTextEdit, QGridLayout, QListWidget, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer

# إعداد مسار المشروع
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.db_connection import get_manufacturing_db_connection, get_financials_db_connection

def fetch_all(connection_func, query, params=()):
    try:
        conn = connection_func()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, params)
        result = [dict(row) for row in cur.fetchall()]
        conn.close()
        return result
    except Exception as e:
        print(f"DB Error (fetch_all): {e}")
        return []

def fetch_one(connection_func, query, params=()):
    try:
        conn = connection_func()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, params)
        result = cur.fetchone()
        conn.close()
        return dict(result) if result else None
    except Exception as e:
        print(f"DB Error (fetch_one): {e}")
        return None

class EnterLineEdit(QLineEdit):
    enterPressed = pyqtSignal()
    
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.enterPressed.emit()
        else:
            super().keyPressEvent(event)

class OrderSelectionDialog(QDialog):
    def __init__(self, orders, parent=None):
        super().__init__(parent)
        self.setWindowTitle("اختر أمر التشغيل")
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self.selected_order = None
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("اختر أمر التشغيل من القائمة:"))
        
        self.orders_list = QListWidget()
        for order in orders:
            self.orders_list.addItem(f"{order['order_number']} - {order['customer_name']} - {order['order_date']}")
        self.orders_list.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.orders_list)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def accept_selection(self):
        current_row = self.orders_list.currentRow()
        if current_row >= 0:
            self.selected_order = current_row
            self.accept()

class CostsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("نظام إدارة مصروفات أوامر التشغيل")
        self.setMinimumSize(1200, 700)
        self.setLayoutDirection(Qt.RightToLeft)
        self.account_data = {} # لتخزين بيانات الحسابات
        self.apply_styles()
        self.init_ui()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; font-family: 'Segoe UI'; }
            QLabel { font-size: 12px; font-weight: bold; color: #333; padding: 5px; }
            QLineEdit, QComboBox, QDateEdit { padding: 8px; border: 2px solid #ddd; border-radius: 5px; }
            QPushButton { 
                font-size: 12px; font-weight: bold; padding: 10px 15px; 
                border: none; border-radius: 5px; min-width: 80px; 
            }
            #save_btn { background-color: #7B1FA2; color: white; }
            #load_btn { background-color: #FFC107; color: black; }
            #delete_btn { background-color: #F44336; color: white; }
            #add_btn { background-color: #9C27B0; color: white; }
            #remove_btn { background-color: #f44336; color: white; }
            #new_order_btn { background-color: #4CAF50; color: white; }
            QTableWidget { 
                gridline-color: #d0d0d0; font-size: 11px; 
                selection-background-color: #e3f2fd; 
            }
            QHeaderView::section { 
                background-color: #7B1FA2; color: white; font-weight: bold; 
                padding: 8px; border: none; 
            }
        """)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        title = QLabel("إدارة مصروفات أوامر التشغيل")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #7B1FA2; padding: 15px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        top_bar_layout = QHBoxLayout()
        info_group = QGroupBox("معلومات أمر التشغيل")
        info_layout = QGridLayout(info_group)
        
        info_layout.addWidget(QLabel("رقم الأمر:"), 0, 0)
        self.order_number = QLineEdit()
        self.order_number.setPlaceholderText("سيتم إنشاء الرقم تلقائياً...")
        self.order_number.setReadOnly(True)
        info_layout.addWidget(self.order_number, 0, 1)

        self.new_order_btn = QPushButton("أمر جديد")
        self.new_order_btn.setObjectName("new_order_btn")
        self.new_order_btn.clicked.connect(self.create_new_order)
        info_layout.addWidget(self.new_order_btn, 0, 2)

        self.load_btn = QPushButton("تحميل أمر")
        self.load_btn.setObjectName("load_btn")
        self.load_btn.clicked.connect(self.show_orders_dialog)
        info_layout.addWidget(self.load_btn, 0, 3)

        info_layout.addWidget(QLabel("العميل:"), 1, 0)
        self.customer = QLineEdit()
        self.customer.setPlaceholderText("اسم العميل...")
        info_layout.addWidget(self.customer, 1, 1)

        info_layout.addWidget(QLabel("التاريخ:"), 1, 2)
        self.order_date = QDateEdit(QDate.currentDate())
        self.order_date.setDisplayFormat("dd/MM/yyyy")
        self.order_date.setCalendarPopup(True)
        info_layout.addWidget(self.order_date, 1, 3)

        top_bar_layout.addWidget(info_group)
        layout.addLayout(top_bar_layout)

        self.costs_table = QTableWidget(0, 5)
        self.costs_table.setHorizontalHeaderLabels([
            "كود الحساب", "اسم الحساب", "الوصف", "المبلغ", "العملة"
        ])
        
        self.costs_table.setColumnWidth(0, 120)
        self.costs_table.setColumnWidth(1, 250)
        self.costs_table.setColumnWidth(2, 300)
        self.costs_table.setColumnWidth(3, 150)
        self.costs_table.setColumnWidth(4, 80)
        
        layout.addWidget(self.costs_table)

        buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ إضافة مصروف")
        self.add_btn.setObjectName("add_btn")
        self.add_btn.clicked.connect(self.add_cost_row)
        buttons_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton("🗑️ حذف مصروف")
        self.remove_btn.setObjectName("remove_btn")
        self.remove_btn.clicked.connect(self.remove_cost_row)
        buttons_layout.addWidget(self.remove_btn)

        buttons_layout.addStretch()

        self.delete_btn = QPushButton("🔥 حذف الأمر")
        self.delete_btn.setObjectName("delete_btn")
        self.delete_btn.clicked.connect(self.delete_order)
        buttons_layout.addWidget(self.delete_btn)

        self.save_btn = QPushButton("💾 حفظ المصروفات")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.clicked.connect(self.save_costs)
        buttons_layout.addWidget(self.save_btn)

        layout.addLayout(buttons_layout)

        totals_layout = QHBoxLayout()
        totals_layout.addWidget(QLabel("إجمالي المصروفات:"))
        self.costs_total = QLabel("0.00")
        self.costs_total.setStyleSheet("font-size: 16px; font-weight: bold; color: #7B1FA2;")
        totals_layout.addWidget(self.costs_total)
        totals_layout.addStretch()
        layout.addLayout(totals_layout)

        QTimer.singleShot(100, self.initialize_table)

    def generate_order_number(self):
        """إنشاء رقم أمر تلقائي"""
        try:
            conn = get_manufacturing_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT MAX(CAST(SUBSTR(order_number, 4) AS INTEGER)) FROM job_orders WHERE order_number LIKE 'ORD%'")
            result = cur.fetchone()
            max_num = result[0] if result[0] else 0
            new_num = max_num + 1
            conn.close()
            return f"ORD{new_num:04d}"
        except Exception as e:
            print(f"Error generating order number: {e}")
            return f"ORD{int(QDate.currentDate().toString('yyyyMMdd'))}"

    def create_new_order(self):
        """إنشاء أمر جديد"""
        new_order_number = self.generate_order_number()
        self.order_number.setText(new_order_number)
        self.customer.clear()
        self.order_date.setDate(QDate.currentDate())
        self.costs_table.setRowCount(0)
        self.add_cost_row()
        self.calculate_total()

    def show_orders_dialog(self):
        """عرض قائمة الأوامر المفتوحة"""
        try:
            orders = fetch_all(get_manufacturing_db_connection, 
                             "SELECT order_number, customer_name, order_date FROM job_orders ORDER BY order_date DESC")
            if not orders:
                QMessageBox.information(self, "لا توجد أوامر", "لا توجد أوامر تشغيل مفتوحة")
                return
            
            dialog = OrderSelectionDialog(orders, self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_order is not None:
                selected_order = orders[dialog.selected_order]
                self.load_order_data(selected_order['order_number'])
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل الأوامر: {str(e)}")

    def load_order_data(self, order_number):
        """تحميل بيانات أمر محدد"""
        self.order_number.setText(order_number)
        self.load_order()

    def initialize_table(self):
        self.setup_autocomplete()
        self.create_new_order()  # إنشاء أمر جديد تلقائياً عند البدء

    def setup_autocomplete(self):
        try:
            accounts = fetch_all(get_financials_db_connection, 
                               "SELECT acc_code, account_name_ar FROM accounts WHERE is_active=1")
            if accounts:
                self.account_data.clear()
                account_list = []
                for acc in accounts:
                    display_text = f"{acc['acc_code']} - {acc['account_name_ar']}"
                    account_list.append(display_text)
                    self.account_data[acc['acc_code']] = {"name": acc['account_name_ar']}
                
                completer = QCompleter(account_list)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                self.completer = completer
        except Exception as e:
            print(f"Error setting up autocomplete: {e}")

    def fetch_account_details(self, row):
        code_widget = self.costs_table.cellWidget(row, 0)
        if not code_widget: return
        
        acc_code = code_widget.text().split(' - ')[0].strip()
        acc_info = self.account_data.get(acc_code)
        
        if acc_info:
            self.costs_table.setItem(row, 1, QTableWidgetItem(acc_info.get("name", "")))
            self.focus_next_cell(row, 2)
        else:
            self.costs_table.setItem(row, 1, QTableWidgetItem(""))

    def add_cost_row(self):
        row = self.costs_table.rowCount()
        self.costs_table.insertRow(row)
        
        code_edit = EnterLineEdit()
        code_edit.setPlaceholderText("اكتب كود الحساب...")
        if hasattr(self, 'completer'):
            code_edit.setCompleter(self.completer)
        
        code_edit.enterPressed.connect(lambda: self.fetch_account_details(row))
        self.costs_table.setCellWidget(row, 0, code_edit)

        self.costs_table.setItem(row, 1, QTableWidgetItem(""))
        self.make_cell_editable(row, 2, "")
        self.make_cell_editable(row, 3, "0.00")
        self.costs_table.setItem(row, 4, QTableWidgetItem("د.ع"))
        
        code_edit.setFocus()

    def make_cell_editable(self, row, col, default_text):
        editor = EnterLineEdit(default_text)
        if col == 3: # المبلغ
            editor.textChanged.connect(self.calculate_total)
            editor.enterPressed.connect(self.add_cost_row)
        else: # الوصف
            editor.enterPressed.connect(lambda: self.focus_next_cell(row, 3))
        
        self.costs_table.setCellWidget(row, col, editor)

    def remove_cost_row(self):
        row = self.costs_table.currentRow()
        if row >= 0:
            self.costs_table.removeRow(row)
            self.calculate_total()

    def focus_next_cell(self, row, col):
        if col < self.costs_table.columnCount():
            widget = self.costs_table.cellWidget(row, col)
            if widget:
                widget.setFocus()
        else:
            self.add_cost_row()

    def calculate_total(self):
        total = 0.0
        for row in range(self.costs_table.rowCount()):
            try:
                amount_widget = self.costs_table.cellWidget(row, 3)
                if amount_widget:
                    amount = float(amount_widget.text() or 0)
                    total += amount
            except (ValueError, AttributeError):
                continue
        
        self.costs_total.setText(f"{total:,.2f}")

    def save_costs(self):
        order_num = self.order_number.text().strip()
        if not order_num:
            QMessageBox.warning(self, "تحذير", "الرجاء إدخال رقم أمر التشغيل")
            return
        
        conn = None
        try:
            conn = get_manufacturing_db_connection()
            cur = conn.cursor()
            cur.execute("BEGIN TRANSACTION;")

            cur.execute("SELECT order_id FROM job_orders WHERE order_number = ?", (order_num,))
            result = cur.fetchone()
            
            if result:
                order_id = result[0]
                cur.execute("UPDATE job_orders SET customer_name = ?, order_date = ? WHERE order_id = ?", 
                            (self.customer.text(), self.order_date.date().toString("yyyy-MM-dd"), order_id))
                cur.execute("DELETE FROM job_order_costs WHERE order_id = ?", (order_id,))
            else:
                cur.execute("INSERT INTO job_orders (order_number, customer_name, order_date) VALUES (?, ?, ?)", 
                            (order_num, self.customer.text(), self.order_date.date().toString("yyyy-MM-dd")))
                order_id = cur.lastrowid

            for row in range(self.costs_table.rowCount()):
                code_widget = self.costs_table.cellWidget(row, 0)
                acc_code = code_widget.text().split(' - ')[0].strip() if code_widget else ""
                
                if not acc_code: continue

                acc_name = self.costs_table.item(row, 1).text() if self.costs_table.item(row, 1) else ""
                desc = self.costs_table.cellWidget(row, 2).text()
                amount = self.costs_table.cellWidget(row, 3).text()
                currency = self.costs_table.item(row, 4).text() if self.costs_table.item(row, 4) else "د.ع"

                cur.execute("""
                    INSERT INTO job_order_costs 
                    (order_id, account_code, account_name, description, amount, currency)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (order_id, acc_code, acc_name, desc, float(amount), currency))
            
            conn.commit()
            QMessageBox.information(self, "تم الحفظ", f"تم حفظ مصروفات أمر التشغيل {order_num} بنجاح")

        except Exception as e:
            if conn: conn.rollback()
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحفظ: {str(e)}")
        finally:
            if conn: conn.close()

    def load_order(self):
        order_num = self.order_number.text().strip()
        if not order_num:
            QMessageBox.warning(self, "تحذير", "الرجاء إدخال رقم أمر التشغيل للتحميل")
            return
            
        order = fetch_all(get_manufacturing_db_connection, "SELECT * FROM job_orders WHERE order_number = ?", (order_num,))
        if not order:
            QMessageBox.information(self, "غير موجود", "أمر التشغيل غير موجود")
            return
        
        order_id = order[0]['order_id']
        self.customer.setText(order[0]['customer_name'])
        self.order_date.setDate(QDate.fromString(order[0]['order_date'], "yyyy-MM-dd"))
        
        costs = fetch_all(get_manufacturing_db_connection, "SELECT * FROM job_order_costs WHERE order_id = ?", (order_id,))
        
        self.costs_table.setRowCount(0)
        for cost in costs:
            row = self.costs_table.rowCount()
            self.add_cost_row()
            
            self.costs_table.cellWidget(row, 0).setText(cost['account_code'])
            self.costs_table.setItem(row, 1, QTableWidgetItem(cost['account_name']))
            self.costs_table.cellWidget(row, 2).setText(cost['description'])
            self.costs_table.cellWidget(row, 3).setText(str(cost['amount']))
            self.costs_table.setItem(row, 4, QTableWidgetItem(cost['currency']))
        
        self.calculate_total()

    def delete_order(self):
        order_num = self.order_number.text().strip()
        if not order_num: return
        
        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                     f"هل أنت متأكد من حذف أمر التشغيل رقم {order_num} وكل بياناته؟",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_manufacturing_db_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM job_orders WHERE order_number = ?", (order_num,))
                conn.commit()
                conn.close()
                self.order_number.clear(); self.customer.clear(); self.costs_table.setRowCount(0)
                self.add_cost_row(); self.calculate_total()
                QMessageBox.information(self, "تم الحذف", f"تم حذف أمر التشغيل {order_num} بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CostsWindow()
    window.show()
    sys.exit(app.exec_())
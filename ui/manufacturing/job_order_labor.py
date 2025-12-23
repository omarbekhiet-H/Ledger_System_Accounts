import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QMessageBox, QCompleter, QDateEdit, QFrame,
    QGroupBox, QTextEdit, QGridLayout
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer

# إعداد مسار المشروع
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.db_connection import get_manufacturing_db_connection, get_users_db_connection

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

class EnterLineEdit(QLineEdit):
    enterPressed = pyqtSignal()
    
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.enterPressed.emit()
        else:
            super().keyPressEvent(event)

class LaborWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("نظام إدارة أجور أوامر التشغيل")
        self.setMinimumSize(1200, 700)
        self.setLayoutDirection(Qt.RightToLeft)
        self.employee_data = {}
        self.apply_styles()
        self.init_ui()

    def apply_styles(self):
        # ... (style code is unchanged)
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; font-family: 'Segoe UI'; }
            QLabel { font-size: 12px; font-weight: bold; color: #333; padding: 5px; }
            QLineEdit, QComboBox, QDateEdit { padding: 8px; border: 2px solid #ddd; border-radius: 5px; }
            QPushButton { 
                font-size: 12px; font-weight: bold; padding: 10px 15px; 
                border: none; border-radius: 5px; min-width: 80px; 
            }
            #save_btn { background-color: #1976D2; color: white; }
            #load_btn { background-color: #FFC107; color: black; }
            #delete_btn { background-color: #F44336; color: white; }
            #add_btn { background-color: #2196F3; color: white; }
            #remove_btn { background-color: #f44336; color: white; }
            QTableWidget { 
                gridline-color: #d0d0d0; font-size: 11px; 
                selection-background-color: #e3f2fd; 
            }
            QHeaderView::section { 
                background-color: #1976D2; color: white; font-weight: bold; 
                padding: 8px; border: none; 
            }
        """)

    def init_ui(self):
        # ... (UI setup is unchanged)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        title = QLabel("إدارة أجور وعمالة أوامر التشغيل")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1976D2; padding: 15px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        top_bar_layout = QHBoxLayout()
        info_group = QGroupBox("معلومات أمر التشغيل")
        info_layout = QGridLayout(info_group)
        
        info_layout.addWidget(QLabel("رقم الأمر:"), 0, 0)
        self.order_number = QLineEdit()
        self.order_number.setPlaceholderText("ادخل رقم أمر التشغيل...")
        info_layout.addWidget(self.order_number, 0, 1)

        self.load_btn = QPushButton("تحميل")
        self.load_btn.setObjectName("load_btn")
        self.load_btn.clicked.connect(self.load_order)
        info_layout.addWidget(self.load_btn, 0, 2)

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

        self.labor_table = QTableWidget(0, 6)
        self.labor_table.setHorizontalHeaderLabels([
            "كود الموظف", "اسم الموظف", "المسمى الوظيفي", 
            "عدد الساعات", "أجر الساعة", "التكلفة الإجمالية"
        ])
        
        self.labor_table.setColumnWidth(0, 120)
        self.labor_table.setColumnWidth(1, 250)
        self.labor_table.setColumnWidth(2, 180)
        self.labor_table.setColumnWidth(3, 100)
        self.labor_table.setColumnWidth(4, 120)
        self.labor_table.setColumnWidth(5, 150)
        
        layout.addWidget(self.labor_table)

        buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ إضافة عامل")
        self.add_btn.setObjectName("add_btn")
        self.add_btn.clicked.connect(self.add_labor_row)
        buttons_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton("🗑️ حذف عامل")
        self.remove_btn.setObjectName("remove_btn")
        self.remove_btn.clicked.connect(self.remove_labor_row)
        buttons_layout.addWidget(self.remove_btn)

        buttons_layout.addStretch()

        self.delete_btn = QPushButton("🔥 حذف الأمر")
        self.delete_btn.setObjectName("delete_btn")
        self.delete_btn.clicked.connect(self.delete_order)
        buttons_layout.addWidget(self.delete_btn)

        self.save_btn = QPushButton("💾 حفظ الأجور")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.clicked.connect(self.save_labor)
        buttons_layout.addWidget(self.save_btn)

        layout.addLayout(buttons_layout)

        totals_layout = QHBoxLayout()
        totals_layout.addWidget(QLabel("إجمالي الأجور:"))
        self.labor_total = QLabel("0.00")
        self.labor_total.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976D2;")
        totals_layout.addWidget(self.labor_total)
        totals_layout.addStretch()
        layout.addLayout(totals_layout)

        QTimer.singleShot(100, self.initialize_table)

    def initialize_table(self):
        self.setup_autocomplete()
        self.add_labor_row()

    def setup_autocomplete(self):
        # ... (function is unchanged from previous version)
        try:
            query = "SELECT username, name_ar FROM users WHERE is_active=1"
            users = fetch_all(get_users_db_connection, query)
            if users:
                self.employee_data.clear()
                user_list = []
                for user in users:
                    display_text = f"{user['username']} - {user['name_ar']}"
                    user_list.append(display_text)
                    self.employee_data[user['username']] = {
                        "name": user['name_ar']
                    }
                completer = QCompleter(user_list)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                self.completer = completer
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الاتصال", f"لا يمكن تحميل بيانات الموظفين. تأكد من صحة أسماء الجداول والأعمدة.\n\n{e}")
            print(f"Error setting up autocomplete for labor: {e}")

    # ### --- دالة جديدة --- ###
    # هذه الدالة تعمل عند اختيار عنصر من القائمة
    def on_employee_selected(self, selected_text, row):
        try:
            code, name = selected_text.split(' - ', 1)
            code_edit = self.labor_table.cellWidget(row, 0)
            if code_edit:
                code_edit.setText(code)

            self.labor_table.setItem(row, 1, QTableWidgetItem(name))
            self.labor_table.setItem(row, 2, QTableWidgetItem("")) # اترك المسمى الوظيفي فارغاً
            self.focus_next_cell(row, 2) # الانتقال لخانة المسمى الوظيفي
        except Exception as e:
            print(f"Error processing selection: {e}")

    def fetch_employee_details(self, row):
        code_widget = self.labor_table.cellWidget(row, 0)
        if not code_widget: return
        
        emp_code = code_widget.text().split(' - ')[0].strip()
        emp_info = self.employee_data.get(emp_code)
        
        if emp_info:
            self.labor_table.setItem(row, 1, QTableWidgetItem(emp_info.get("name", "")))
            self.labor_table.setItem(row, 2, QTableWidgetItem(""))
        else:
            self.labor_table.setItem(row, 1, QTableWidgetItem(""))
            self.labor_table.setItem(row, 2, QTableWidgetItem(""))
            
        self.focus_next_cell(row, 2)

    def add_labor_row(self):
        row = self.labor_table.rowCount()
        self.labor_table.insertRow(row)
        
        code_edit = EnterLineEdit()
        code_edit.setPlaceholderText("اكتب كود الموظف...")
        if hasattr(self, 'completer'):
            code_edit.setCompleter(self.completer)
            # ### --- ربط الإشارة الجديدة هنا --- ###
            code_edit.completer().activated.connect(
                lambda text, r=row: self.on_employee_selected(text, r)
            )
        
        code_edit.enterPressed.connect(lambda: self.fetch_employee_details(row))
        self.labor_table.setCellWidget(row, 0, code_edit)

        self.labor_table.setItem(row, 1, QTableWidgetItem(""))
        self.make_cell_editable(row, 2, "")
        self.make_cell_editable(row, 3, "8")
        self.make_cell_editable(row, 4, "0.00")
        self.labor_table.setItem(row, 5, QTableWidgetItem("0.00"))
        
        code_edit.setFocus()
        
    # Rest of the file is unchanged
    def make_cell_editable(self, row, col, default_text):
        editor = EnterLineEdit(default_text)
        if col != 2: 
            editor.textChanged.connect(self.calculate_total)
        
        if col == 2: # المسمى الوظيفي
            editor.enterPressed.connect(lambda: self.focus_next_cell(row, 3))
        elif col == 3: # الساعات
            editor.enterPressed.connect(lambda: self.focus_next_cell(row, 4))
        elif col == 4: # الأجر
             editor.enterPressed.connect(self.add_labor_row)
        self.labor_table.setCellWidget(row, col, editor)

    def remove_labor_row(self):
        row = self.labor_table.currentRow()
        if row >= 0:
            self.labor_table.removeRow(row)
            self.calculate_total()

    def focus_next_cell(self, row, col):
        if col < self.labor_table.columnCount():
            widget = self.labor_table.cellWidget(row, col)
            if widget:
                widget.setFocus()
        else:
            self.add_labor_row()

    def calculate_total(self):
        total = 0.0
        for row in range(self.labor_table.rowCount()):
            try:
                hours_widget = self.labor_table.cellWidget(row, 3)
                rate_widget = self.labor_table.cellWidget(row, 4)
                
                if hours_widget and rate_widget:
                    hours = float(hours_widget.text() or 0)
                    rate = float(rate_widget.text() or 0)
                    row_total = hours * rate
                    total += row_total
                    
                    self.labor_table.setItem(row, 5, QTableWidgetItem(f"{row_total:.2f}"))
            except (ValueError, AttributeError):
                continue
        
        self.labor_total.setText(f"{total:,.2f}")

    def save_labor(self):
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
                cur.execute("DELETE FROM job_order_labor WHERE order_id = ?", (order_id,))
            else:
                cur.execute("INSERT INTO job_orders (order_number, customer_name, order_date) VALUES (?, ?, ?)", 
                            (order_num, self.customer.text(), self.order_date.date().toString("yyyy-MM-dd")))
                order_id = cur.lastrowid

            for row in range(self.labor_table.rowCount()):
                code_widget = self.labor_table.cellWidget(row, 0)
                emp_code = code_widget.text().split(' - ')[0].strip() if code_widget and code_widget.text() else ""
                
                if not emp_code: continue

                emp_name = self.labor_table.item(row, 1).text() if self.labor_table.item(row, 1) else ""
                title_widget = self.labor_table.cellWidget(row, 2)
                title = title_widget.text() if title_widget else ""
                hours = self.labor_table.cellWidget(row, 3).text()
                rate = self.labor_table.cellWidget(row, 4).text()
                total = self.labor_table.item(row, 5).text()

                cur.execute("""
                    INSERT INTO job_order_labor 
                    (order_id, employee_code, employee_name, job_title, hours, hourly_rate, total_cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (order_id, emp_code, emp_name, title, float(hours), float(rate), float(total)))
            
            conn.commit()
            QMessageBox.information(self, "تم الحفظ", f"تم حفظ أجور أمر التشغيل {order_num} بنجاح")

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
        
        labors = fetch_all(get_manufacturing_db_connection, "SELECT * FROM job_order_labor WHERE order_id = ?", (order_id,))
        
        self.labor_table.setRowCount(0)
        if not labors: self.add_labor_row()
            
        for labor in labors:
            row = self.labor_table.rowCount()
            self.labor_table.insertRow(row)

            code_edit = EnterLineEdit(labor['employee_code'])
            if hasattr(self, 'completer'): code_edit.setCompleter(self.completer)
            code_edit.enterPressed.connect(lambda r=row: self.fetch_employee_details(r))
            self.labor_table.setCellWidget(row, 0, code_edit)
            
            self.labor_table.setItem(row, 1, QTableWidgetItem(labor['employee_name']))
            self.make_cell_editable(row, 2, labor.get('job_title', ''))
            self.make_cell_editable(row, 3, str(labor['hours']))
            self.make_cell_editable(row, 4, str(labor['hourly_rate']))
            self.labor_table.setItem(row, 5, QTableWidgetItem(str(labor['total_cost'])))
        
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
                self.order_number.clear(); self.customer.clear(); self.labor_table.setRowCount(0)
                self.add_labor_row(); self.calculate_total()
                QMessageBox.information(self, "تم الحفظ", f"تم حذف أمر التشغيل {order_num} بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LaborWindow()
    window.show()
    sys.exit(app.exec_())
import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QMessageBox, QCompleter, QDateEdit, QFrame,
    QGroupBox, QTextEdit, QGridLayout, QDialog, QDialogButtonBox, QListWidget
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer

# إعداد مسار المشروع
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.db_connection import get_manufacturing_db_connection, get_inventory_db_connection

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

class ItemSelectionDialog(QDialog):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle("اختر الصنف")
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self.selected_item = None
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # حقل البحث
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("بحث:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.filter_items)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # جدول العناصر
        self.items_table = QTableWidget(0, 3)
        self.items_table.setHorizontalHeaderLabels(["الكود", "اسم الصنف", "الوحدة"])
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # تعبئة البيانات
        self.all_items = items
        self.populate_table(items)
        
        self.items_table.cellDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.items_table)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def populate_table(self, items):
        self.items_table.setRowCount(0)
        for item in items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            self.items_table.setItem(row, 0, QTableWidgetItem(item['item_code']))
            self.items_table.setItem(row, 1, QTableWidgetItem(item['item_name_ar']))
            self.items_table.setItem(row, 2, QTableWidgetItem(item.get('unit_name', '')))
    
    def filter_items(self, text):
        filtered_items = [item for item in self.all_items 
                         if text.lower() in item['item_code'].lower() 
                         or text.lower() in item['item_name_ar'].lower()]
        self.populate_table(filtered_items)
    
    def accept_selection(self):
        current_row = self.items_table.currentRow()
        if current_row >= 0:
            self.selected_item = self.all_items[current_row]
            self.accept()

class MaterialsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("نظام إدارة مواد أوامر التشغيل")
        self.setMinimumSize(1200, 700)
        self.setLayoutDirection(Qt.RightToLeft)
        self.item_data = {}
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
            #save_btn { background-color: #4CAF50; color: white; }
            #load_btn { background-color: #FFC107; color: black; }
            #delete_btn { background-color: #F44336; color: white; }
            #add_btn { background-color: #2196F3; color: white; }
            #remove_btn { background-color: #f44336; color: white; }
            #new_order_btn { background-color: #7B1FA2; color: white; }
            #select_item_btn { background-color: #FF9800; color: white; }
            QTableWidget { 
                gridline-color: #d0d0d0; font-size: 11px; 
                selection-background-color: #e3f2fd; 
            }
            QHeaderView::section { 
                background-color: #37474F; color: white; font-weight: bold; 
                padding: 8px; border: none; 
            }
        """)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        title = QLabel("إدارة مواد أوامر التشغيل")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #D32F2F; padding: 15px;")
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

        # زر اختيار الصنف
        item_selection_layout = QHBoxLayout()
        item_selection_layout.addWidget(QLabel("اختيار الصنف:"))
        self.select_item_btn = QPushButton("📦 اختيار من قائمة الأصناف")
        self.select_item_btn.setObjectName("select_item_btn")
        self.select_item_btn.clicked.connect(self.show_items_dialog)
        item_selection_layout.addWidget(self.select_item_btn)
        item_selection_layout.addStretch()
        layout.addLayout(item_selection_layout)

        self.materials_table = QTableWidget(0, 7)
        self.materials_table.setHorizontalHeaderLabels([
            "كود المادة", "اسم المادة", "الوحدة", "الكمية", 
            "سعر الوحدة", "الإجمالي", "ملاحظات"
        ])
        
        self.materials_table.setColumnWidth(0, 120)
        self.materials_table.setColumnWidth(1, 250)
        self.materials_table.setColumnWidth(2, 80)
        self.materials_table.setColumnWidth(3, 100)
        self.materials_table.setColumnWidth(4, 120)
        self.materials_table.setColumnWidth(5, 120)
        self.materials_table.setColumnWidth(6, 200)
        
        layout.addWidget(self.materials_table)

        buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ إضافة مادة")
        self.add_btn.setObjectName("add_btn")
        self.add_btn.clicked.connect(self.add_material_row)
        buttons_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton("🗑️ حذف مادة")
        self.remove_btn.setObjectName("remove_btn")
        self.remove_btn.clicked.connect(self.remove_material_row)
        buttons_layout.addWidget(self.remove_btn)

        buttons_layout.addStretch()
        
        self.delete_btn = QPushButton("🔥 حذف الأمر")
        self.delete_btn.setObjectName("delete_btn")
        self.delete_btn.clicked.connect(self.delete_order)
        buttons_layout.addWidget(self.delete_btn)

        self.save_btn = QPushButton("💾 حفظ المواد")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.clicked.connect(self.save_materials)
        buttons_layout.addWidget(self.save_btn)

        layout.addLayout(buttons_layout)

        totals_layout = QHBoxLayout()
        totals_layout.addWidget(QLabel("إجمالي المواد:"))
        self.materials_total = QLabel("0.00")
        self.materials_total.setStyleSheet("font-size: 16px; font-weight: bold; color: #D32F2F;")
        totals_layout.addWidget(self.materials_total)
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
        self.materials_table.setRowCount(0)
        self.add_material_row()
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

    def show_items_dialog(self):
        """عرض قائمة الأصناف للاختيار"""
        try:
            items = fetch_all(get_inventory_db_connection, """
                SELECT i.item_code, i.item_name_ar, u.unit_name_ar AS unit_name
                FROM items AS i
                LEFT JOIN units AS u ON i.base_unit_id = u.id
                WHERE i.is_active = 1
                ORDER BY i.item_code
            """)
            
            if not items:
                QMessageBox.information(self, "لا توجد أصناف", "لا توجد أصناف مسجلة في النظام")
                return
            
            dialog = ItemSelectionDialog(items, self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_item:
                self.add_item_to_table(dialog.selected_item)
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل الأصناف: {str(e)}")

    def add_item_to_table(self, item):
        """إضافة الصنف المختار إلى الجدول"""
        row = self.materials_table.rowCount()
        self.materials_table.insertRow(row)
        
        # كود الصنف (غير قابل للتعديل)
        code_item = QTableWidgetItem(item['item_code'])
        code_item.setFlags(code_item.flags() & ~Qt.ItemIsEditable)
        self.materials_table.setItem(row, 0, code_item)
        
        # اسم الصنف (غير قابل للتعديل)
        name_item = QTableWidgetItem(item['item_name_ar'])
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        self.materials_table.setItem(row, 1, name_item)
        
        # الوحدة (غير قابلة للتعديل)
        unit_item = QTableWidgetItem(item.get('unit_name', ''))
        unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)
        self.materials_table.setItem(row, 2, unit_item)
        
        # الكمية (قابلة للتعديل)
        qty_edit = EnterLineEdit("1.00")
        qty_edit.textChanged.connect(self.calculate_row_total)
        qty_edit.textChanged.connect(self.calculate_total)
        self.materials_table.setCellWidget(row, 3, qty_edit)
        
        # السعر (قابل للتعديل)
        price_edit = EnterLineEdit("0.00")
        price_edit.textChanged.connect(self.calculate_row_total)
        price_edit.textChanged.connect(self.calculate_total)
        self.materials_table.setCellWidget(row, 4, price_edit)
        
        # الإجمالي (غير قابل للتعديل)
        total_item = QTableWidgetItem("0.00")
        total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
        self.materials_table.setItem(row, 5, total_item)
        
        # الملاحظات (قابلة للتعديل)
        notes_edit = EnterLineEdit()
        self.materials_table.setCellWidget(row, 6, notes_edit)
        
        qty_edit.setFocus()
        self.calculate_row_total(row)

    def calculate_row_total(self, row=None):
        """حساب إجمالي الصف"""
        if row is None:
            try:
                row = self.sender().parent().property("row")
            except:
                return
        
        try:
            qty_widget = self.materials_table.cellWidget(row, 3)
            price_widget = self.materials_table.cellWidget(row, 4)
            
            if qty_widget and price_widget:
                qty = float(qty_widget.text() or 0)
                price = float(price_widget.text() or 0)
                total = qty * price
                
                total_item = QTableWidgetItem(f"{total:.2f}")
                total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
                self.materials_table.setItem(row, 5, total_item)
        except ValueError:
            pass

    def load_order_data(self, order_number):
        """تحميل بيانات أمر محدد"""
        self.order_number.setText(order_number)
        self.load_order()

    def initialize_table(self):
        self.create_new_order()  # إنشاء أمر جديد تلقائياً عند البدء

    def add_material_row(self):
        """إضافة صف فارغ للمواد"""
        row = self.materials_table.rowCount()
        self.materials_table.insertRow(row)
        
        # كود الصنف (قابل للتعديل)
        code_edit = EnterLineEdit()
        code_edit.setPlaceholderText("اكتب كود الصنف...")
        self.materials_table.setCellWidget(row, 0, code_edit)
        
        # اسم الصنف
        self.materials_table.setItem(row, 1, QTableWidgetItem(""))
        
        # الوحدة
        self.materials_table.setItem(row, 2, QTableWidgetItem(""))
        
        # الكمية
        qty_edit = EnterLineEdit("1.00")
        qty_edit.textChanged.connect(self.calculate_total)
        self.materials_table.setCellWidget(row, 3, qty_edit)
        
        # السعر
        price_edit = EnterLineEdit("0.00")
        price_edit.textChanged.connect(self.calculate_total)
        self.materials_table.setCellWidget(row, 4, price_edit)
        
        # الإجمالي
        self.materials_table.setItem(row, 5, QTableWidgetItem("0.00"))
        
        # الملاحظات
        notes_edit = EnterLineEdit()
        self.materials_table.setCellWidget(row, 6, notes_edit)
        
        code_edit.setFocus()

    def remove_material_row(self):
        row = self.materials_table.currentRow()
        if row >= 0:
            self.materials_table.removeRow(row)
            self.calculate_total()

    def calculate_total(self):
        total = 0.0
        for row in range(self.materials_table.rowCount()):
            try:
                total_item = self.materials_table.item(row, 5)
                if total_item:
                    total += float(total_item.text() or 0)
            except (ValueError, AttributeError):
                continue
        
        self.materials_total.setText(f"{total:,.2f}")

    def save_materials(self):
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
                cur.execute("DELETE FROM job_orders WHERE order_id = ?", (order_id,))
            else:
                cur.execute("INSERT INTO job_orders (order_number, customer_name, order_date) VALUES (?, ?, ?)", 
                            (order_num, self.customer.text(), self.order_date.date().toString("yyyy-MM-dd")))
                order_id = cur.lastrowid

            for row in range(self.materials_table.rowCount()):
                code_widget = self.materials_table.cellWidget(row, 0)
                item_code = code_widget.text().strip() if code_widget else ""
                
                if not item_code: continue

                item_name = self.materials_table.item(row, 1).text() if self.materials_table.item(row, 1) else ""
                unit = self.materials_table.item(row, 2).text() if self.materials_table.item(row, 2) else ""
                qty = self.materials_table.cellWidget(row, 3).text()
                price = self.materials_table.cellWidget(row, 4).text()
                total = self.materials_table.item(row, 5).text() if self.materials_table.item(row, 5) else "0.00"
                notes = self.materials_table.cellWidget(row, 6).text() if self.materials_table.cellWidget(row, 6) else ""

                cur.execute("""
                    INSERT INTO job_orders
                    (order_id, item_code, item_name, unit, quantity, unit_price, total_price, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (order_id, item_code, item_name, unit, float(qty), float(price), float(total), notes))
            
            conn.commit()
            QMessageBox.information(self, "تم الحفظ", f"تم حفظ مواد أمر التشغيل {order_num} بنجاح")

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
        
        materials = fetch_all(get_manufacturing_db_connection, "SELECT * FROM job_orders WHERE order_id = ?", (order_id,))
        
        self.materials_table.setRowCount(0)
        for material in materials:
            row = self.materials_table.rowCount()
            self.materials_table.insertRow(row)
            
            code_edit = EnterLineEdit(material['item_code'])
            self.materials_table.setCellWidget(row, 0, code_edit)
            
            self.materials_table.setItem(row, 1, QTableWidgetItem(material['item_name']))
            self.materials_table.setItem(row, 2, QTableWidgetItem(material['unit']))
            
            qty_edit = EnterLineEdit(str(material['quantity']))
            qty_edit.textChanged.connect(self.calculate_total)
            self.materials_table.setCellWidget(row, 3, qty_edit)
            
            price_edit = EnterLineEdit(str(material['unit_price']))
            price_edit.textChanged.connect(self.calculate_total)
            self.materials_table.setCellWidget(row, 4, price_edit)
            
            self.materials_table.setItem(row, 5, QTableWidgetItem(str(material['total_price'])))
            
            notes_edit = EnterLineEdit(material.get('notes', ''))
            self.materials_table.setCellWidget(row, 6, notes_edit)
        
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
                self.order_number.clear(); self.customer.clear(); self.materials_table.setRowCount(0)
                self.add_material_row(); self.calculate_total()
                QMessageBox.information(self, "تم الحذف", f"تم حذف أمر التشغيل {order_num} بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MaterialsWindow()
    window.show()
    sys.exit(app.exec_())
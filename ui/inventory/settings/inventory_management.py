# -*- coding: utf-8 -*-

import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt

# --- إعدادات قاعدة البيانات (تبقى كما هي) ---
DATABASE = 'inventory.db'

def init_db():
    """
    يقوم بإنشاء الاتصال وقاعدة البيانات والجدول إذا لم يكونوا موجودين.
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT UNIQUE NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 0,
        price REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()
    print("تم التأكد من وجود قاعدة البيانات والجدول بنجاح.")


# --- دوال التعامل مع قاعدة البيانات (المدير - تبقى كما هي) ---

def get_all_products():
    """ جلب كل المنتجات من قاعدة البيانات """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY created_at DESC")
    products = cursor.fetchall()
    conn.close()
    return products

def add_product(name, sku, quantity, price):
    """ إضافة منتج جديد """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO products (name, sku, quantity, price) VALUES (?, ?, ?, ?)",
                       (name, sku, quantity, price))
        conn.commit()
        return True, "تمت إضافة المنتج بنجاح."
    except sqlite3.IntegrityError:
        return False, f"SKU '{sku}' موجود بالفعل. لا يمكن إضافة المنتج."
    finally:
        conn.close()

def delete_product(product_id):
    """ حذف منتج """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


# --- الواجهة الرسومية (PyQt5 Interface) ---

class InventoryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("برنامج إدارة المخزون (PyQt5)")
        self.setGeometry(100, 100, 900, 600)
        self.initUI()

    def initUI(self):
        # --- التخطيط الرئيسي ---
        main_layout = QVBoxLayout()

        # --- قسم إدخال البيانات ---
        form_layout = QGridLayout()
        
        form_layout.addWidget(QLabel("اسم المنتج:"), 0, 0)
        self.name_entry = QLineEdit()
        form_layout.addWidget(self.name_entry, 0, 1)

        form_layout.addWidget(QLabel("SKU:"), 0, 2)
        self.sku_entry = QLineEdit()
        form_layout.addWidget(self.sku_entry, 0, 3)

        form_layout.addWidget(QLabel("الكمية:"), 1, 0)
        self.quantity_entry = QLineEdit()
        form_layout.addWidget(self.quantity_entry, 1, 1)
        
        form_layout.addWidget(QLabel("السعر:"), 1, 2)
        self.price_entry = QLineEdit()
        form_layout.addWidget(self.price_entry, 1, 3)

        add_button = QPushButton("إضافة منتج")
        add_button.clicked.connect(self.add_item)
        form_layout.addWidget(add_button, 0, 4, 2, 1) # يمتد لصفين
        
        # --- قسم عرض البيانات (الجدول) ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "اسم المنتج", "SKU", "الكمية", "السعر"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # تمديد عمود الاسم
        self.table.setEditTriggers(QTableWidget.NoEditTriggers) # منع التعديل المباشر
        self.table.setSelectionBehavior(QTableWidget.SelectRows) # تحديد الصف بأكمله

        # --- قسم أزرار الإجراءات ---
        actions_layout = QHBoxLayout()
        delete_button = QPushButton("حذف المنتج المحدد")
        delete_button.setStyleSheet("background-color: red; color: white;")
        delete_button.clicked.connect(self.delete_item)
        
        refresh_button = QPushButton("تحديث القائمة")
        refresh_button.clicked.connect(self.populate_table)
        
        actions_layout.addWidget(delete_button)
        actions_layout.addWidget(refresh_button)
        actions_layout.addStretch() # لدفع الأزرار لليسار

        # --- تجميع كل الأجزاء في التخطيط الرئيسي ---
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.table)
        main_layout.addLayout(actions_layout)
        
        self.setLayout(main_layout)

        # تحميل البيانات عند التشغيل
        self.populate_table()

    def populate_table(self):
        """ جلب البيانات من قاعدة البيانات وتعبئة الجدول """
        products = get_all_products()
        self.table.setRowCount(0) # مسح الجدول
        
        for product in products:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            
            # تحويل القيم إلى QTableWidgetItem
            id_item = QTableWidgetItem(str(product['id']))
            name_item = QTableWidgetItem(product['name'])
            sku_item = QTableWidgetItem(product['sku'])
            quantity_item = QTableWidgetItem(str(product['quantity']))
            price_item = QTableWidgetItem(f"{product['price']:.2f}")

            # جعل الأرقام في المنتصف
            id_item.setTextAlignment(Qt.AlignCenter)
            quantity_item.setTextAlignment(Qt.AlignCenter)
            price_item.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row_position, 0, id_item)
            self.table.setItem(row_position, 1, name_item)
            self.table.setItem(row_position, 2, sku_item)
            self.table.setItem(row_position, 3, quantity_item)
            self.table.setItem(row_position, 4, price_item)

    def add_item(self):
        """ إضافة عنصر جديد """
        name = self.name_entry.text()
        sku = self.sku_entry.text()
        quantity = self.quantity_entry.text()
        price = self.price_entry.text()

        if not all([name, sku, quantity, price]):
            QMessageBox.critical(self, "خطأ في الإدخال", "الرجاء تعبئة جميع الحقول.")
            return
        
        try:
            success, message = add_product(name, sku, int(quantity), float(price))
            if success:
                QMessageBox.information(self, "نجاح", message)
                self.clear_entries()
                self.populate_table()
            else:
                QMessageBox.critical(self, "خطأ", message)
        except ValueError:
            QMessageBox.critical(self, "خطأ في الإدخال", "الرجاء إدخال أرقام صحيحة في حقلي الكمية والسعر.")

    def delete_item(self):
        """ حذف العنصر المحدد من الجدول """
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد منتج لحذفه.")
            return

        confirm = QMessageBox.question(self, "تأكيد الحذف", "هل أنت متأكد من حذف المنتج المحدد؟",
                                       QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            product_id = self.table.item(current_row, 0).text()
            delete_product(int(product_id))
            self.populate_table()
            QMessageBox.information(self, "نجاح", "تم حذف المنتج بنجاح.")

    def clear_entries(self):
        """ مسح حقول الإدخال """
        self.name_entry.clear()
        self.sku_entry.clear()
        self.quantity_entry.clear()
        self.price_entry.clear()

if __name__ == '__main__':
    init_db()  # التأكد من تهيئة قاعدة البيانات أولاً
    app = QApplication(sys.argv)
    window = InventoryApp()
    window.show()
    sys.exit(app.exec_())

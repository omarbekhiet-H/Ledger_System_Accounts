import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QTextEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QComboBox, QMessageBox, QDateEdit, QDialog)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QTextDocument
from datetime import datetime

# 🔗 ربط مع المسار الرئيسي
current_dir = os.path.dirname(os.path.abspath(__file__))
database_path = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if database_path not in sys.path:
    sys.path.append(database_path)

# 🔗 الاستيرادات من مدير قاعدة البيانات
from database.manager.inventory.purchase.supply_order_manager import SupplyOrder
from database.manager.inventory.purchase.purchase_request_manager import PurchaseRequest


# نافذة مراجعة أمر التوريد قبل الاعتماد
class SupplyOrderPreviewDialog(QDialog):
    def __init__(self, order_data, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle("مراجعة أمر التوريد")
        self.setGeometry(300, 200, 700, 500)
        self.order_data = order_data
        self.items = items

        layout = QVBoxLayout()

        # تفاصيل الأمر
        details_text = f"""
طلب الشراء: {order_data['request_number']}
المورد: {order_data['supplier_name']}
تاريخ التسليم المتوقع: {order_data['delivery_date']}
الملاحظات: {order_data['notes'] or "-"}
"""
        self.details_label = QLabel(details_text)
        self.details_label.setStyleSheet("font-size: 14px; margin: 10px;")
        layout.addWidget(self.details_label)

        # جدول الأصناف
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(3)
        self.items_table.setHorizontalHeaderLabels(["الصنف", "الكمية", "السعر"])
        self.items_table.setRowCount(len(items))

        for row, item in enumerate(items):
            self.items_table.setItem(row, 0, QTableWidgetItem(item["item_name_ar"]))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(item["quantity"])))
            self.items_table.setItem(row, 2, QTableWidgetItem(str(item["price"])))

        self.items_table.resizeColumnsToContents()
        layout.addWidget(self.items_table)

        # أزرار
        btn_layout = QHBoxLayout()

        approve_btn = QPushButton("✔ اعتماد الأمر")
        approve_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        approve_btn.clicked.connect(self.accept)
        btn_layout.addWidget(approve_btn)

        cancel_btn = QPushButton("✖ إلغاء")
        cancel_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        print_btn = QPushButton("🖨 طباعة")
        print_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        print_btn.clicked.connect(self.print_order)
        btn_layout.addWidget(print_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def print_order(self):
        """طباعة أمر التوريد إلى PDF"""
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName("supply_order.pdf")

        doc = QTextDocument()
        html = f"""
        <h2 style='text-align:center'>أمر التوريد</h2>
        <p><b>طلب الشراء:</b> {self.order_data['request_number']}</p>
        <p><b>المورد:</b> {self.order_data['supplier_name']}</p>
        <p><b>تاريخ التسليم المتوقع:</b> {self.order_data['delivery_date']}</p>
        <p><b>ملاحظات:</b> {self.order_data['notes'] or "-"}</p>
        <h3>الأصناف</h3>
        <table border='1' cellspacing='0' cellpadding='5'>
        <tr><th>الصنف</th><th>الكمية</th><th>السعر</th></tr>
        """
        for item in self.items:
            html += f"<tr><td>{item['item_name_ar']}</td><td>{item['quantity']}</td><td>{item['price']}</td></tr>"
        html += "</table>"

        doc.setHtml(html)
        doc.print_(printer)
        QMessageBox.information(self, "طباعة", "تم إنشاء ملف PDF: supply_order.pdf")


class SupplyOrderUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("نظام إدارة أوامر التوريد")
        self.setGeometry(100, 100, 1000, 700)

        self.supply_order = SupplyOrder()
        self.purchase_request = PurchaseRequest()
        self.init_ui()
        self.load_requests()
        self.load_suppliers()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # 📝 معلومات الأمر
        info_layout = QHBoxLayout()

        left_info = QVBoxLayout()
        self.request_combo = QComboBox()
        self.request_combo.setPlaceholderText("اختر طلب الشراء")
        self.request_combo.currentIndexChanged.connect(self.load_request_items)
        left_info.addWidget(QLabel("طلب الشراء:"))
        left_info.addWidget(self.request_combo)

        self.supplier_combo = QComboBox()
        self.supplier_combo.setPlaceholderText("اختر المورد")
        left_info.addWidget(QLabel("المورد:"))
        left_info.addWidget(self.supplier_combo)

        right_info = QVBoxLayout()
        self.delivery_date = QDateEdit()
        self.delivery_date.setDate(QDate.currentDate().addDays(7))
        self.delivery_date.setCalendarPopup(True)
        self.delivery_date.setMinimumDate(QDate.currentDate())
        right_info.addWidget(QLabel("تاريخ التسليم المتوقع:"))
        right_info.addWidget(self.delivery_date)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("ملاحظات الأمر")
        right_info.addWidget(QLabel("ملاحظات:"))
        right_info.addWidget(self.notes_input)

        info_layout.addLayout(left_info)
        info_layout.addLayout(right_info)
        layout.addLayout(info_layout)

        # 📦 جدول الأصناف
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["ID", "اسم الصنف", "الكمية", "السعر"])
        layout.addWidget(self.items_table)

        # 🔘 أزرار التحكم
        button_layout = QHBoxLayout()

        submit_btn = QPushButton("🚀 إنشاء أمر التوريد")
        submit_btn.clicked.connect(self.submit_order)
        button_layout.addWidget(submit_btn)

        clear_btn = QPushButton("🧹 مسح الكل")
        clear_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(clear_btn)

        layout.addLayout(button_layout)
        central_widget.setLayout(layout)

    def load_requests(self):
        """تحميل طلبات الشراء المعتمدة فقط"""
        try:
            self.purchase_request.cursor.execute("""
                SELECT id, request_number 
                FROM purchase_requests 
                WHERE status = 'approved'
            """)
            requests = self.purchase_request.cursor.fetchall()

            self.request_combo.clear()
            for request_id, request_number in requests:
                self.request_combo.addItem(request_number, request_id)

        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل طلبات الشراء: {e}")

    def load_suppliers(self):
        """تحميل الموردين النشطين"""
        try:
            self.supply_order.cursor.execute("""
                SELECT id, name_ar 
                FROM suppliers 
                WHERE is_active = 1
            """)
            suppliers = self.supply_order.cursor.fetchall()

            self.supplier_combo.clear()
            for supplier_id, supplier_name in suppliers:
                self.supplier_combo.addItem(supplier_name, supplier_id)

        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل الموردين: {e}")

    def load_request_items(self):
        """تحميل أصناف طلب الشراء المحدد"""
        try:
            request_id = self.request_combo.currentData()
            if not request_id:
                self.items_table.setRowCount(0)
                return

            self.supply_order.cursor.execute("""
                SELECT pri.item_id, i.item_name_ar, pri.quantity, pri.unit_price
                FROM purchase_request_items pri
                JOIN items i ON pri.item_id = i.id
                WHERE pri.request_id = ?
            """, (request_id,))

            items = self.supply_order.cursor.fetchall()

            self.items_table.setRowCount(0)
            for item_id, item_name, quantity, price in items:
                row_position = self.items_table.rowCount()
                self.items_table.insertRow(row_position)

                item_id_widget = QTableWidgetItem(str(item_id))
                item_id_widget.setFlags(item_id_widget.flags() & ~Qt.ItemIsEditable)
                self.items_table.setItem(row_position, 0, item_id_widget)

                item_name_widget = QTableWidgetItem(item_name)
                item_name_widget.setFlags(item_name_widget.flags() & ~Qt.ItemIsEditable)
                self.items_table.setItem(row_position, 1, item_name_widget)

                item_quantity_widget = QTableWidgetItem(str(quantity))
                item_quantity_widget.setFlags(item_quantity_widget.flags() & ~Qt.ItemIsEditable)
                self.items_table.setItem(row_position, 2, item_quantity_widget)

                price_widget = QTableWidgetItem(f"{price:.2f}" if price else "0.00")
                self.items_table.setItem(row_position, 3, price_widget)

        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل أصناف الطلب: {e}")

    def submit_order(self):
        """فتح نافذة المراجعة قبل الحفظ"""
        try:
            request_id = self.request_combo.currentData()
            supplier_id = self.supplier_combo.currentData()
            notes = self.notes_input.toPlainText().strip()

            if not request_id or not supplier_id:
                QMessageBox.warning(self, "تحذير", "يرجى اختيار طلب الشراء والمورد")
                return

            delivery_date_str = self.delivery_date.date().toString("yyyy-MM-dd")
            request_number = self.request_combo.currentText()
            supplier_name = self.supplier_combo.currentText()

            items = []
            for row in range(self.items_table.rowCount()):
                items.append({
                    "item_id": int(self.items_table.item(row, 0).text()),
                    "item_name_ar": self.items_table.item(row, 1).text(),
                    "quantity": self.items_table.item(row, 2).text(),
                    "price": self.items_table.item(row, 3).text()
                })

            order_data = {
                "request_id": request_id,
                "request_number": request_number,
                "supplier_id": supplier_id,
                "supplier_name": supplier_name,
                "delivery_date": delivery_date_str,
                "notes": notes
            }

            preview_dialog = SupplyOrderPreviewDialog(order_data, items, self)
            if preview_dialog.exec_() == QDialog.Accepted:
                today = datetime.now().date()
                delivery_dt = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
                delivery_days = (delivery_dt - today).days

                order_id = self.supply_order.create_supply_order(
                    request_id,
                    supplier_id,
                    notes,
                    delivery_days
                )

                for item in items:
                    self.supply_order.update_order_item_price(order_id, item["item_id"], float(item["price"]))

                self.purchase_request.update_status(request_id, "ordered")
                QMessageBox.information(self, "نجاح", f"تم اعتماد وإنشاء أمر التوريد رقم {order_id} بنجاح")

                self.clear_form()
                self.load_requests()

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في إنشاء أمر التوريد: {e}")

    def clear_form(self):
        """مسح النموذج"""
        self.request_combo.setCurrentIndex(-1)
        self.supplier_combo.setCurrentIndex(-1)
        self.delivery_date.setDate(QDate.currentDate().addDays(7))
        self.notes_input.clear()
        self.items_table.setRowCount(0)

    def closeEvent(self, event):
        """إغلاق الاتصال عند إغلاق النافذة"""
        self.supply_order.close()
        self.purchase_request.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = SupplyOrderUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

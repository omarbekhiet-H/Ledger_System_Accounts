import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QTextEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QComboBox, QSpinBox, QMessageBox, QHeaderView, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QTextDocument

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.inventory.purchase.receipt_permit_manager import ReceiptPermit
from database.manager.inventory.purchase.supply_order_manager import SupplyOrder

class ReceiptPermitUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📦 نظام إدارة إذونات الاستلام")
        self.setGeometry(100, 100, 1200, 800)

        self.receipt_permit = ReceiptPermit()
        self.supply_order = SupplyOrder()
        self.current_permit_id = None
        self.init_ui()
        self.load_orders()
        self.load_warehouses()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # 📝 معلومات الإذن
        info_layout = QHBoxLayout()

        left_info = QVBoxLayout()
        self.order_combo = QComboBox()
        self.order_combo.setPlaceholderText("اختر أمر التوريد")
        self.order_combo.currentIndexChanged.connect(self.load_order_items)
        left_info.addWidget(QLabel("أمر التوريد:"))
        left_info.addWidget(self.order_combo)

        self.warehouse_combo = QComboBox()
        self.warehouse_combo.setPlaceholderText("اختر المستودع")
        left_info.addWidget(QLabel("المستودع:"))
        left_info.addWidget(self.warehouse_combo)

        # إضافة معلومات إضافية
        right_info = QVBoxLayout()
        self.permit_number_label = QLabel("رقم إذن الاستلام: -")
        right_info.addWidget(self.permit_number_label)
        
        self.status_label = QLabel("الحالة: غير مكتمل")
        right_info.addWidget(self.status_label)

        info_layout.addLayout(left_info)
        info_layout.addLayout(right_info)
        layout.addLayout(info_layout)

        # معلومات أمر التوريد
        self.order_info_label = QLabel("لم يتم تحديد أمر توريد")
        layout.addWidget(self.order_info_label)

        # 📑 جدول الأصناف
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(8)  # إضافة عمود للتحديد
        self.items_table.setHorizontalHeaderLabels(
            ["تحديد", "ID", "كود الصنف", "اسم الصنف", "الوحدة", "الكمية المطلوبة", "الكمية المستلمة", "ملاحظات"]
        )
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.items_table)

        # 🔘 أزرار التحكم
        button_layout = QHBoxLayout()

        submit_btn = QPushButton("🚀 إنشاء إذن الاستلام")
        submit_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        submit_btn.clicked.connect(self.submit_permit)
        button_layout.addWidget(submit_btn)

        self.complete_btn = QPushButton("✅ إكمال الاستلام")
        self.complete_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.complete_btn.clicked.connect(self.complete_receipt)
        self.complete_btn.setEnabled(False)
        button_layout.addWidget(self.complete_btn)

        print_btn = QPushButton("🖨 طباعة إذن الاستلام")
        print_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        print_btn.clicked.connect(self.print_permit)
        button_layout.addWidget(print_btn)

        clear_btn = QPushButton("🧹 مسح الكل")
        clear_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        clear_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(clear_btn)

        layout.addLayout(button_layout)
        central_widget.setLayout(layout)

    def load_orders(self):
        """تحميل أوامر التوريد"""
        try:
            self.supply_order.cursor.execute(
                "SELECT id, order_number FROM supply_orders WHERE status IN ('pending', 'partially_received')"
            )
            orders = self.supply_order.cursor.fetchall()

            self.order_combo.clear()
            self.order_combo.addItem("اختر أمر التوريد", None)
            for order_id, order_number in orders:
                self.order_combo.addItem(order_number, order_id)

        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل أوامر التوريد: {e}")

    def load_warehouses(self):
        """تحميل المستودعات"""
        try:
            self.receipt_permit.cursor.execute("SELECT id, name_ar FROM warehouses WHERE is_active = 1")
            warehouses = self.receipt_permit.cursor.fetchall()

            self.warehouse_combo.clear()
            self.warehouse_combo.addItem("اختر المستودع", None)
            for warehouse_id, warehouse_name in warehouses:
                self.warehouse_combo.addItem(warehouse_name, warehouse_id)

        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل المستودعات: {e}")

    def load_order_items(self):
        """تحميل أصناف أمر التوريد المحدد"""
        try:
            order_id = self.order_combo.currentData()
            if not order_id:
                self.items_table.setRowCount(0)
                self.order_info_label.setText("لم يتم تحديد أمر توريد")
                return
            self.update_order_info()
        
            # استعلام بديل في حالة عدم وجود received_quantity
            self.supply_order.cursor.execute("""
            SELECT soi.item_id, i.item_code, i.item_name_ar, 
                   soi.quantity as remaining_quantity,  -- استخدام الكمية الكلية مؤقتًا
                u.name_ar as unit_name, u.id as unit_id, i.item_description
            FROM supply_order_items soi
            JOIN items i ON soi.item_id = i.id
            JOIN units u ON soi.unit_id = u.id
            WHERE soi.order_id = ? AND soi.quantity > 0  -- شرط مبسط
            """, (order_id,))

            items = self.supply_order.cursor.fetchall()

            self.items_table.setRowCount(0)
            for item_id, item_code, item_name, remaining_quantity, unit_name, unit_id, description in items:
                row_position = self.items_table.rowCount()
                self.items_table.insertRow(row_position)

                # عمود التحديد
                select_checkbox = QCheckBox()
                select_checkbox.setChecked(True)  # تحديد تلقائي للصنف
                self.items_table.setCellWidget(row_position, 0, select_checkbox)

                self.items_table.setItem(row_position, 1, QTableWidgetItem(str(item_id)))
                self.items_table.setItem(row_position, 2, QTableWidgetItem(item_code))
                self.items_table.setItem(row_position, 3, QTableWidgetItem(item_name))
                self.items_table.setItem(row_position, 4, QTableWidgetItem(unit_name))
                self.items_table.setItem(row_position, 5, QTableWidgetItem(str(remaining_quantity)))

                received_spin = QSpinBox()
                received_spin.setMinimum(0)
                received_spin.setMaximum(remaining_quantity)
                received_spin.setValue(remaining_quantity)  # تعيين القيمة الافتراضية للكمية المتبقية
                received_spin.setProperty("unit_id", unit_id)
                received_spin.setProperty("item_description", description or "")
                self.items_table.setCellWidget(row_position, 6, received_spin)

                notes_edit = QLineEdit()
                notes_edit.setPlaceholderText("ملاحظات الاستلام")
                if description:
                    notes_edit.setToolTip(description)
                self.items_table.setCellWidget(row_position, 7, notes_edit)

            # ضبط عرض الأعمدة
            self.items_table.setColumnWidth(0, 60)   # التحديد
            self.items_table.setColumnWidth(1, 50)   # ID
            self.items_table.setColumnWidth(2, 100)  # كود الصنف
            self.items_table.setColumnWidth(3, 150)  # اسم الصنف
            self.items_table.setColumnWidth(4, 80)   # الوحدة
            self.items_table.setColumnWidth(5, 100)  # الكمية المطلوبة
            self.items_table.setColumnWidth(6, 120)  # الكمية المستلمة
            self.items_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)  # ملاحظات

        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل أصناف الأمر: {e}")

    def submit_permit(self):
        """إنشاء إذن الاستلام"""
        try:
            order_id = self.order_combo.currentData()
            warehouse_id = self.warehouse_combo.currentData()

            if not order_id or not warehouse_id:
                QMessageBox.warning(self, "تحذير", "يرجى اختيار أمر التوريد والمستودع")
                return

            if self.items_table.rowCount() == 0:
                QMessageBox.warning(self, "تحذير", "لا توجد أصناف في أمر التوريد المحدد")
                return

            permit_id = self.receipt_permit.create_receipt_permit(order_id, warehouse_id)
            self.current_permit_id = permit_id
            self.permit_number_label.setText(f"رقم إذن الاستلام: {permit_id}")

            # معالجة الأصناف المحددة فقط
            for row in range(self.items_table.rowCount()):
                checkbox = self.items_table.cellWidget(row, 0)
                if checkbox.isChecked():
                    item_id = int(self.items_table.item(row, 1).text())
                    received_spin = self.items_table.cellWidget(row, 6)
                    notes_edit = self.items_table.cellWidget(row, 7)

                    received_quantity = received_spin.value()  # استخراج القيمة من QSpinBox
                    notes = notes_edit.text().strip()
                    unit_id = received_spin.property("unit_id")

                    if received_quantity > 0:  # فقط إذا كانت الكمية المستلمة أكبر من صفر
                        self.receipt_permit.update_received_quantity(permit_id, item_id, received_quantity, unit_id, notes)

            QMessageBox.information(self, "نجاح", f"تم إنشاء إذن الاستلام رقم {permit_id} بنجاح. يمكنك الآن إكمال الاستلام.")
            self.complete_btn.setEnabled(True)
            self.status_label.setText("الحالة: قيد المعالجة")

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في إنشاء إذن الاستلام: {e}")

    def complete_receipt(self):
        """إكمال عملية الاستلام"""
        try:
            if self.current_permit_id:
                self.receipt_permit.complete_receipt(self.current_permit_id)
                QMessageBox.information(self, "نجاح", f"تم إكمال إذن الاستلام رقم {self.current_permit_id}")
                self.status_label.setText("الحالة: مكتمل")
                self.clear_form()
                self.load_orders()  # إعادة تحميل الأوامر لتحديث القائمة
            else:
                QMessageBox.warning(self, "تحذير", "يجب إنشاء إذن استلام أولاً قبل إكماله.")

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في إكمال الاستلام: {e}")

    def print_permit(self):
        """طباعة إذن الاستلام إلى PDF"""
        try:
            if not self.current_permit_id:
                QMessageBox.warning(self, "تحذير", "لا يوجد إذن استلام للطباعة.")
                return

            self.receipt_permit.cursor.execute("""
                SELECT rp.permit_number, rp.permit_date, so.order_number, w.name_ar
                FROM receipt_permits rp
                JOIN supply_orders so ON rp.supply_order_id = so.id
                JOIN warehouses w ON rp.warehouse_id = w.id
                WHERE rp.id = ?
            """, (self.current_permit_id,))
            permit_info = self.receipt_permit.cursor.fetchone()

            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(f"receipt_permit_{self.current_permit_id}.pdf")

            doc = QTextDocument()
            html = f"""
            <div style='text-align: center; direction: rtl;'>
                <h2>إذن الاستلام</h2>
                <p><b>رقم الإذن:</b> {permit_info[0] if permit_info else self.current_permit_id}</p>
                <p><b>تاريخ الإذن:</b> {permit_info[1] if permit_info else ''}</p>
                <p><b>أمر التوريد:</b> {permit_info[2] if permit_info else self.order_combo.currentText()}</p>
                <p><b>المستودع:</b> {permit_info[3] if permit_info else self.warehouse_combo.currentText()}</p>
                <h3>الأصناف</h3>
                <table border='1' cellspacing='0' cellpadding='5' width='100%' style='border-collapse: collapse;'>
                <tr><th>الصنف</th><th>الوحدة</th><th>المطلوب</th><th>المستلم</th><th>ملاحظات</th></tr>
            """
        
            for row in range(self.items_table.rowCount()):
                checkbox = self.items_table.cellWidget(row, 0)
                if checkbox.isChecked():  # عرض الأصناف المحددة فقط
                    item_name = self.items_table.item(row, 3).text()
                    unit_name = self.items_table.item(row, 4).text()
                    qty_required = self.items_table.item(row, 5).text()
                    
                    # استخراج قيمة QSpinBox للكمية المستلمة
                    qty_received_widget = self.items_table.cellWidget(row, 6)
                    qty_received = qty_received_widget.value() if qty_received_widget else 0
                    
                    notes_widget = self.items_table.cellWidget(row, 7)
                    notes = notes_widget.text() if notes_widget else ""
                    
                    html += f"<tr><td>{item_name}</td><td>{unit_name}</td><td>{qty_required}</td><td>{qty_received}</td><td>{notes}</td></tr>"

            html += """
                </table>
                <br><br>
                <div style='width: 100%; display: flex; justify-content: space-around;'>
                    <div>
                        <p>_________________________</p>
                        <p>المسؤول</p>
                    </div>
                    <div>
                        <p>_________________________</p>
                        <p>المستلم</p>
                    </div>
                </div>
            </div>
            """

            doc.setHtml(html)
            doc.print_(printer)
            QMessageBox.information(self, "طباعة", f"تم إنشاء ملف PDF: receipt_permit_{self.current_permit_id}.pdf")

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في الطباعة: {e}")

    def update_order_info(self):
        """تحديث معلومات أمر التوريد المحدد"""
        order_id = self.order_combo.currentData()
        if order_id:
            try:
                self.supply_order.cursor.execute("""
                    SELECT so.order_number, so.order_date, s.name_ar as supplier_name
                    FROM supply_orders so
                    LEFT JOIN suppliers s ON so.supplier_id = s.id
                    WHERE so.id = ?
                """, (order_id,))
                order_info = self.supply_order.cursor.fetchone()
                
                if order_info:
                    info_text = f"أمر التوريد: {order_info[0]} | التاريخ: {order_info[1]} | المورد: {order_info[2] or 'غير محدد'}"
                    self.order_info_label.setText(info_text)
                else:
                    self.order_info_label.setText("لم يتم تحديد أمر توريد")
            except Exception as e:
                print(f"خطأ في تحميل معلومات الأمر: {e}")
                self.order_info_label.setText("خطأ في تحميل المعلومات")
        else:
            self.order_info_label.setText("لم يتم تحديد أمر توريد")

    def clear_form(self):
        """مسح النموذج"""
        self.order_combo.setCurrentIndex(0)
        self.warehouse_combo.setCurrentIndex(0)
        self.items_table.setRowCount(0)
        self.current_permit_id = None
        self.permit_number_label.setText("رقم إذن الاستلام: -")
        self.status_label.setText("الحالة: غير مكتمل")
        self.complete_btn.setEnabled(False)
        self.order_info_label.setText("لم يتم تحديد أمر توريد")

    def closeEvent(self, event):
        """إغلاق الاتصال عند إغلاق النافذة"""
        self.receipt_permit.close()
        self.supply_order.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = ReceiptPermitUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
import os
import sys
import sqlite3
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QComboBox, QLineEdit, QDateEdit, QTextEdit, QGroupBox,
                             QFormLayout, QTabWidget, QDoubleSpinBox, QListWidget)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QTextDocument

# إصلاح المسارات
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from database.manager.inventory.purchase.inventory_invoice_manager import InventoryInvoice
except ImportError:
    # نسخة احتياطية لأغراض التطوير
    class InventoryInvoice:
        def __init__(self):
            self.conn = sqlite3.connect(':memory:')
            self.cursor = self.conn.cursor()
        
        def create_invoice(self, *args):
            return 1
        
        def add_invoice_item(self, *args):
            pass
        
        def complete_invoice(self, *args):
            pass
        
        def close(self):
            self.conn.close()

class InventoryInvoiceUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', 'Arial'; font-size: 12px; }
            QLabel, QPushButton, QLineEdit, QComboBox, QTableWidget { font-family: 'Segoe UI', 'Arial'; }
        """)
        self.setWindowTitle("🧾 نظام إدارة الفواتير المخزنية")
        self.setGeometry(100, 100, 1400, 900)
        
        self.inventory_invoice = InventoryInvoice()
        self.current_invoice_id = None
        self.init_ui()
        self.load_addition_permits()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        # التبويبات
        self.tabs = QTabWidget()

        self.create_tab = QWidget()
        self.init_create_tab()
        self.tabs.addTab(self.create_tab, "➕ إنشاء فاتورة")

        self.view_tab = QWidget()
        self.init_view_tab()
        self.tabs.addTab(self.view_tab, "👁️ عرض الفواتير")

        main_layout.addWidget(self.tabs)
        central_widget.setLayout(main_layout)

    def init_create_tab(self):
        layout = QHBoxLayout()

        # --- القائمة الجانبية ---
        self.addition_list = QListWidget()
        self.addition_list.setFixedWidth(300)
        self.addition_list.itemClicked.connect(self.on_list_item_clicked)
        layout.addWidget(self.addition_list)

        # --- النموذج الرئيسي ---
        form_layout = QVBoxLayout()

        # معلومات الفاتورة الأساسية
        info_group = QGroupBox("معلومات الفاتورة الأساسية")
        info_layout = QFormLayout()

        self.addition_combo = QComboBox()
        self.addition_combo.setPlaceholderText("اختر إذن الإضافة")
        self.addition_combo.currentIndexChanged.connect(self.load_addition_details)
        info_layout.addRow("رقم إذن الإضافة:", self.addition_combo)

        self.supplier_label = QLabel("سيتم تعبئته تلقائياً")
        info_layout.addRow("المورد:", self.supplier_label)

        self.invoice_date_edit = QDateEdit()
        self.invoice_date_edit.setDate(QDate.currentDate())
        self.invoice_date_edit.setCalendarPopup(True)
        info_layout.addRow("تاريخ الفاتورة:", self.invoice_date_edit)

        self.invoice_number_label = QLabel("سيتم إنشاؤه تلقائياً")
        info_layout.addRow("رقم الفاتورة:", self.invoice_number_label)

        self.invoice_type_combo = QComboBox()
        self.invoice_type_combo.addItems(["شراء", "بيع", "مرتجع"])
        info_layout.addRow("نوع الفاتورة:", self.invoice_type_combo)

        info_group.setLayout(info_layout)
        form_layout.addWidget(info_group)

        # جدول الأصناف
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(10)
        self.items_table.setHorizontalHeaderLabels([
            "كود الصنف", "اسم الصنف", "الوحدة", "الكمية", "سعر الوحدة",
            "الخصم %", "قيمة الخصم", "البونص", "الضريبة %", "الإجمالي"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        form_layout.addWidget(QLabel("أصناف الفاتورة:"))
        form_layout.addWidget(self.items_table)

        # الخصومات والضرائب
        discount_tax_group = QGroupBox("الخصومات والضرائب")
        discount_tax_layout = QFormLayout()
        self.discount_percent_spin = QDoubleSpinBox()
        self.discount_percent_spin.setRange(0, 100)
        self.discount_percent_spin.valueChanged.connect(self.calculate_totals)
        discount_tax_layout.addRow("نسبة الخصم العام %:", self.discount_percent_spin)

        self.discount_amount_spin = QDoubleSpinBox()
        self.discount_amount_spin.setRange(0, 1000000)
        self.discount_amount_spin.valueChanged.connect(self.calculate_totals)
        discount_tax_layout.addRow("مبلغ الخصم العام:", self.discount_amount_spin)

        self.tax_percent_spin = QDoubleSpinBox()
        self.tax_percent_spin.setRange(0, 100)
        self.tax_percent_spin.valueChanged.connect(self.calculate_totals)
        discount_tax_layout.addRow("نسبة الضريبة %:", self.tax_percent_spin)

        self.tax_amount_spin = QDoubleSpinBox()
        self.tax_amount_spin.setRange(0, 1000000)
        self.tax_amount_spin.valueChanged.connect(self.calculate_totals)
        discount_tax_layout.addRow("مبلغ الضريبة:", self.tax_amount_spin)

        discount_tax_group.setLayout(discount_tax_layout)
        form_layout.addWidget(discount_tax_group)

        # الإجماليات
        totals_group = QGroupBox("الإجماليات")
        totals_layout = QFormLayout()
        self.subtotal_label = QLabel("0.00")
        self.total_discount_label = QLabel("0.00")
        self.total_tax_label = QLabel("0.00")
        self.grand_total_label = QLabel("0.00")
        totals_layout.addRow("المجموع الفرعي:", self.subtotal_label)
        totals_layout.addRow("إجمالي الخصومات:", self.total_discount_label)
        totals_layout.addRow("إجمالي الضرائب:", self.total_tax_label)
        totals_layout.addRow("الإجمالي النهائي:", self.grand_total_label)
        totals_group.setLayout(totals_layout)
        form_layout.addWidget(totals_group)

        # ملاحظات
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("ملاحظات حول الفاتورة...")
        form_layout.addWidget(QLabel("ملاحظات:"))
        form_layout.addWidget(self.notes_edit)

        # أزرار التحكم
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 حفظ")
        self.save_btn.clicked.connect(self.save_invoice)
        button_layout.addWidget(self.save_btn)
        
        self.update_btn = QPushButton("✏️ تحديث")
        self.update_btn.clicked.connect(self.update_invoice)
        self.update_btn.setEnabled(False)
        button_layout.addWidget(self.update_btn)
        
        self.complete_btn = QPushButton("✅ إكمال")
        self.complete_btn.clicked.connect(self.complete_invoice)
        self.complete_btn.setEnabled(False)
        button_layout.addWidget(self.complete_btn)
        
        self.print_btn = QPushButton("🖨️ طباعة")
        self.print_btn.clicked.connect(self.print_invoice)
        self.print_btn.setEnabled(False)
        button_layout.addWidget(self.print_btn)
        
        self.export_btn = QPushButton("📊 تصدير")
        self.export_btn.clicked.connect(self.export_to_excel)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)

        form_layout.addLayout(button_layout)
        layout.addLayout(form_layout)
        self.create_tab.setLayout(layout)

    def init_view_tab(self):
        """تبويب عرض الفواتير"""
        layout = QVBoxLayout()
        
        # شريط البحث والتصفية
        filter_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("ابحث برقم الفاتورة أو اسم المورد...")
        self.search_edit.textChanged.connect(self.load_invoices)
        filter_layout.addWidget(QLabel("بحث:"))
        filter_layout.addWidget(self.search_edit)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["جميع الحالات", "مسودة", "مكتملة", "ملغاة"])
        self.status_combo.currentTextChanged.connect(self.load_invoices)
        filter_layout.addWidget(QLabel("الحالة:"))
        filter_layout.addWidget(self.status_combo)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["جميع الأنواع", "شراء", "بيع", "مرتجع"])
        self.type_combo.currentTextChanged.connect(self.load_invoices)
        filter_layout.addWidget(QLabel("النوع:"))
        filter_layout.addWidget(self.type_combo)
        
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.clicked.connect(self.load_invoices)
        filter_layout.addWidget(refresh_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # جدول الفواتير
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(8)
        self.invoices_table.setHorizontalHeaderLabels([
            "رقم الفاتورة", "المورد", "التاريخ", "النوع", "الحالة", 
            "الإجمالي", "ملاحظات", "الإجراءات"
        ])
        self.invoices_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.invoices_table)
        
        self.view_tab.setLayout(layout)
        self.load_invoices()

    def load_addition_permits(self):
        """تحميل إذونات الإضافة المتاحة في ComboBox والقائمة الجانبية"""
        try:
            self.inventory_invoice.cursor.execute("""
                SELECT ap.id, ap.addition_date, s.name_ar, rp.permit_number
                FROM addition_permits ap
                JOIN receipt_permits rp ON ap.receipt_id = rp.id
                JOIN supply_orders so ON rp.supply_order_id = so.id
                JOIN suppliers s ON so.supplier_id = s.id
                WHERE ap.status = 'completed'
                AND ap.id NOT IN (SELECT addition_id FROM inventory_invoices)
                ORDER BY ap.addition_date DESC
            """)
            permits = self.inventory_invoice.cursor.fetchall()

            self.addition_combo.clear()
            self.addition_combo.addItem("اختر إذن الإضافة", None)
            self.addition_list.clear()
            for permit_id, addition_date, supplier_name, receipt_number in permits:
                display_text = f"{permit_id} - {addition_date} - {supplier_name} - {receipt_number}"
                self.addition_combo.addItem(display_text, permit_id)
                self.addition_list.addItem(display_text)

        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل إذونات الإضافة: {e}")

    def on_list_item_clicked(self, item):
        """استدعاء تفاصيل الإذن عند الضغط على القائمة الجانبية"""
        index = self.addition_list.row(item) + 1  # +1 لأن أول عنصر ComboBox هو placeholder
        self.addition_combo.setCurrentIndex(index)

    def load_addition_details(self):
        """تحميل تفاصيل إذن الإضافة المحدد"""
        try:
            addition_id = self.addition_combo.currentData()
            if not addition_id:
                self.clear_addition_details()
                return
            
            # الحصول على معلومات المورد من أمر التوريد
            self.inventory_invoice.cursor.execute("""
                SELECT s.name_ar
                FROM addition_permits ap
                JOIN receipt_permits rp ON ap.receipt_id = rp.id
                JOIN supply_orders so ON rp.supply_order_id = so.id
                JOIN suppliers s ON so.supplier_id = s.id
                WHERE ap.id = ?
            """, (addition_id,))
            supplier_result = self.inventory_invoice.cursor.fetchone()
            
            if supplier_result:
                self.supplier_label.setText(supplier_result[0])
            
            # توليد رقم فاتورة تلقائي
            self.generate_invoice_number()
            
            # تحميل الأصناف
            self.load_addition_items(addition_id)
            
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل تفاصيل إذن الإضافة: {e}")
    
    def clear_addition_details(self):
        """مسح تفاصيل إذن الإضافة"""
        self.supplier_label.setText("سيتم تعبئته تلقائياً")
        self.invoice_number_label.setText("سيتم إنشاؤه تلقائياً")
        self.items_table.setRowCount(0)
        self.calculate_totals()
    
    def generate_invoice_number(self):
        """توليد رقم فاتورة تلقائي"""
        try:
            self.inventory_invoice.cursor.execute("""
                SELECT invoice_number FROM inventory_invoices 
                ORDER BY id DESC LIMIT 1
            """)
            last_invoice = self.inventory_invoice.cursor.fetchone()

            if last_invoice and last_invoice[0]:
                last_number = last_invoice[0].strip()
                if last_number.startswith('INV-') and last_number[4:].isdigit():
                    number = int(last_number[4:]) + 1
                    new_number = f"INV-{number:04d}"
                else:
                    new_number = "INV-0001"
            else:
                new_number = "INV-0001"

            self.invoice_number_label.setText(new_number)

        except Exception as e:
            print(f"خطأ في توليد رقم الفاتورة: {e}")
            QMessageBox.warning(self, "خطأ", f"فشل في توليد رقم الفاتورة: {e}")
            self.invoice_number_label.setText("INV-0001")

    def load_addition_items(self, addition_id):
        """تحميل أصناف إذن الإضافة المحدد"""
        try:
            # تحميل الأصناف
            self.inventory_invoice.cursor.execute("""
                SELECT ai.item_id, i.item_code, i.item_name_ar, u.name_ar, ai.quantity,
                       i.purchase_price, i.sale_price
                FROM addition_items ai
                JOIN items i ON ai.item_id = i.id
                JOIN units u ON ai.unit_id = u.id
                WHERE ai.permit_id = ?
            """, (addition_id,))
            
            items = self.inventory_invoice.cursor.fetchall()
            
            self.items_table.setRowCount(0)
            for item_id, item_code, item_name, unit_name, quantity, purchase_price, sale_price in items:
                row_position = self.items_table.rowCount()
                self.items_table.insertRow(row_position)
                
                # تعبئة البيانات الأساسية
                self.items_table.setItem(row_position, 0, QTableWidgetItem(item_code))
                self.items_table.setItem(row_position, 1, QTableWidgetItem(item_name))
                self.items_table.setItem(row_position, 2, QTableWidgetItem(unit_name))
                self.items_table.setItem(row_position, 3, QTableWidgetItem(str(quantity)))
                
                # سعر الوحدة (استخدم سعر الشراء كقيمة افتراضية)
                price_item = QTableWidgetItem(str(purchase_price))
                self.items_table.setItem(row_position, 4, price_item)
                
                # الخصم %
                discount_item = QTableWidgetItem("0")
                self.items_table.setItem(row_position, 5, discount_item)
                
                # قيمة الخصم
                discount_value_item = QTableWidgetItem("0")
                self.items_table.setItem(row_position, 6, discount_value_item)
                
                # البونص
                bonus_item = QTableWidgetItem("0")
                self.items_table.setItem(row_position, 7, bonus_item)
                
                # الضريبة %
                tax_item = QTableWidgetItem("0")
                self.items_table.setItem(row_position, 8, tax_item)
                
                # الإجمالي
                total = quantity * purchase_price
                total_item = QTableWidgetItem(str(total))
                self.items_table.setItem(row_position, 9, total_item)
            
            # إعادة حساب الإجماليات
            self.calculate_totals()
            
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل أصناف إذن الإضافة: {e}")
    
    def calculate_totals(self):
        """حساب الإجماليات"""
        try:
            subtotal = 0
            total_discount = 0
            total_tax = 0
            
            # حساب إجمالي الأصناف
            for row in range(self.items_table.rowCount()):
                quantity = float(self.items_table.item(row, 3).text() or 0)
                unit_price = float(self.items_table.item(row, 4).text() or 0)
                discount_percent = float(self.items_table.item(row, 5).text() or 0)
                tax_percent = float(self.items_table.item(row, 8).text() or 0)
                
                item_total = quantity * unit_price
                item_discount = item_total * (discount_percent / 100)
                item_after_discount = item_total - item_discount
                item_tax = item_after_discount * (tax_percent / 100)
                
                # تحديث قيم الخصم والضريبة
                self.items_table.item(row, 6).setText(f"{item_discount:.2f}")
                
                # تحديث الإجمالي
                item_final_total = item_after_discount + item_tax
                self.items_table.item(row, 9).setText(f"{item_final_total:.2f}")
                
                subtotal += item_total
                total_discount += item_discount
                total_tax += item_tax
            
            # إضافة الخصم العام والضريبة العامة
            general_discount_percent = self.discount_percent_spin.value()
            general_discount_amount = self.discount_amount_spin.value()
            general_tax_percent = self.tax_percent_spin.value()
            general_tax_amount = self.tax_amount_spin.value()
            
            # تطبيق الخصم العام (أخذ القيمة الأكبر بين النسبة والمبلغ)
            general_discount = max(subtotal * (general_discount_percent / 100), general_discount_amount)
            total_discount += general_discount
            
            # تطبيق الضريبة العامة
            general_tax = max((subtotal - total_discount) * (general_tax_percent / 100), general_tax_amount)
            total_tax += general_tax
            
            # حساب الإجمالي النهائي
            grand_total = subtotal - total_discount + total_tax
            
            # تحديث التسميات
            self.subtotal_label.setText(f"{subtotal:.2f}")
            self.total_discount_label.setText(f"{total_discount:.2f}")
            self.total_tax_label.setText(f"{total_tax:.2f}")
            self.grand_total_label.setText(f"{grand_total:.2f}")
            
        except Exception as e:
            print(f"خطأ في حساب الإجماليات: {e}")
    
    def load_invoices(self):
        """تحميل الفواتير للعرض"""
        try:
            search_text = self.search_edit.text().strip()
            status_filter = self.status_combo.currentText()
            type_filter = self.type_combo.currentText()
            
            query = """
                SELECT ii.id, ii.invoice_number, s.name_ar, ii.invoice_date, 
                       ii.invoice_type, ii.status, ii.total_amount, ii.notes
                FROM inventory_invoices ii
                JOIN suppliers s ON ii.supplier_id = s.id
                WHERE 1=1
            """
            params = []
            
            if search_text:
                query += " AND (ii.invoice_number LIKE ? OR s.name_ar LIKE ?)"
                params.extend([f"%{search_text}%", f"%{search_text}%"])
            
            if status_filter != "جميع الحالات":
                query += " AND ii.status = ?"
                params.append(status_filter)
            
            if type_filter != "جميع الأنواع":
                query += " AND ii.invoice_type = ?"
                params.append(type_filter)
            
            query += " ORDER BY ii.invoice_date DESC"
            
            self.inventory_invoice.cursor.execute(query, params)
            invoices = self.inventory_invoice.cursor.fetchall()
            
            self.invoices_table.setRowCount(len(invoices))
            for row, (invoice_id, invoice_number, supplier_name, invoice_date, 
                     invoice_type, status, total_amount, notes) in enumerate(invoices):
                self.invoices_table.setItem(row, 0, QTableWidgetItem(invoice_number))
                self.invoices_table.setItem(row, 1, QTableWidgetItem(supplier_name))
                self.invoices_table.setItem(row, 2, QTableWidgetItem(invoice_date))
                self.invoices_table.setItem(row, 3, QTableWidgetItem(invoice_type))
                self.invoices_table.setItem(row, 4, QTableWidgetItem(status))
                self.invoices_table.setItem(row, 5, QTableWidgetItem(f"{total_amount:.2f}"))
                self.invoices_table.setItem(row, 6, QTableWidgetItem(notes or ""))
                
                # أزرار الإجراءات
                action_widget = QWidget()
                action_layout = QHBoxLayout()
                action_layout.setContentsMargins(0, 0, 0, 0)
                
                view_btn = QPushButton("عرض")
                view_btn.setStyleSheet("background-color: #2196F3; color: white;")
                view_btn.clicked.connect(lambda checked, id=invoice_id: self.view_invoice(id))
                action_layout.addWidget(view_btn)
                
                edit_btn = QPushButton("تعديل")
                edit_btn.setStyleSheet("background-color: #FF9800; color: white;")
                edit_btn.clicked.connect(lambda checked, id=invoice_id: self.edit_invoice(id))
                action_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("حذف")
                delete_btn.setStyleSheet("background-color: #f44336; color: white;")
                delete_btn.clicked.connect(lambda checked, id=invoice_id: self.delete_invoice(id))
                action_layout.addWidget(delete_btn)
                
                action_widget.setLayout(action_layout)
                self.invoices_table.setCellWidget(row, 7, action_widget)
                
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل الفواتير: {e}")
    
    def save_invoice(self):
        """حفظ الفاتورة"""
        try:
            # التحقق من البيانات المطلوبة
            addition_id = self.addition_combo.currentData()
            invoice_number = self.invoice_number_label.text()
            invoice_date = self.invoice_date_edit.date().toString("yyyy-MM-dd")
            invoice_type = self.invoice_type_combo.currentText()
            notes = self.notes_edit.toPlainText().strip()
            
            if not all([addition_id, invoice_number]):
                QMessageBox.warning(self, "تحذير", "يرجى ملء جميع الحقول المطلوبة")
                return
            
            # الحصول على supplier_id من إذن الإضافة
            self.inventory_invoice.cursor.execute("""
                SELECT so.supplier_id
                FROM addition_permits ap
                JOIN receipt_permits rp ON ap.receipt_id = rp.id
                JOIN supply_orders so ON rp.supply_order_id = so.id
                WHERE ap.id = ?
            """, (addition_id,))
            supplier_result = self.inventory_invoice.cursor.fetchone()
            
            if not supplier_result:
                QMessageBox.warning(self, "تحذير", "لم يتم العثور على المورد")
                return
            
            supplier_id = supplier_result[0]
            
            # حساب الإجماليات
            grand_total = float(self.grand_total_label.text())
            
            # حفظ الفاتورة
            invoice_id = self.inventory_invoice.create_invoice(
                addition_id, supplier_id, invoice_number, invoice_date, 
                invoice_type, grand_total, notes
            )
            self.current_invoice_id = invoice_id
            
            # حفظ الأصناف
            for row in range(self.items_table.rowCount()):
                item_code = self.items_table.item(row, 0).text()
                quantity = float(self.items_table.item(row, 3).text())
                unit_price = float(self.items_table.item(row, 4).text())
                discount_percent = float(self.items_table.item(row, 5).text())
                discount_amount = float(self.items_table.item(row, 6).text())
                bonus = float(self.items_table.item(row, 7).text())
                tax_percent = float(self.items_table.item(row, 8).text())
                total_price = float(self.items_table.item(row, 9).text())
                
                # الحصول على ID الصنف والوحدة
                self.inventory_invoice.cursor.execute("""
                    SELECT ai.item_id, ai.unit_id 
                    FROM addition_items ai
                    JOIN items i ON ai.item_id = i.id
                    WHERE i.item_code = ? AND ai.permit_id = ?
                """, (item_code, addition_id))
                item_result = self.inventory_invoice.cursor.fetchone()
                
                if item_result:
                    item_id, unit_id = item_result
                    self.inventory_invoice.add_invoice_item(
                        invoice_id, item_id, quantity, unit_id, unit_price,
                        discount_percent, discount_amount, bonus, tax_percent, total_price
                    )
            
            QMessageBox.information(self, "نجاح", f"تم حفظ الفاتورة رقم {invoice_number}")
            self.update_btn.setEnabled(True)
            self.complete_btn.setEnabled(True)
            self.print_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self.load_invoices()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في حفظ الفاتورة: {e}")
    
    def update_invoice(self):
        """تحديث الفاتورة"""
        try:
            if not self.current_invoice_id:
                QMessageBox.warning(self, "تحذير", "لا يوجد فاتورة للتحديث")
                return
            
            # هنا يمكنك إضافة منطق التحديث
            QMessageBox.information(self, "نجاح", "تم تحديث الفاتورة")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تحديث الفاتورة: {e}")
    
    def complete_invoice(self):
        """إكمال الفاتورة"""
        try:
            if not self.current_invoice_id:
                QMessageBox.warning(self, "تحذير", "لا يوجد فاتورة لإكمالها")
                return
            
            self.inventory_invoice.complete_invoice(self.current_invoice_id)
            QMessageBox.information(self, "نجاح", "تم إكمال الفاتورة")
            self.clear_form()
            self.load_invoices()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في إكمال الفاتورة: {e}")

    def view_invoice(self, invoice_id):
        """عرض فاتورة"""
        try:
            # الحصول على بيانات الفاتورة
            self.inventory_invoice.cursor.execute("""
                SELECT ii.invoice_number, s.name_ar, ii.invoice_date, ii.invoice_type, 
                       ii.status, ii.total_amount, ii.notes
                FROM inventory_invoices ii
                JOIN suppliers s ON ii.supplier_id = s.id
                WHERE ii.id = ?
            """, (invoice_id,))
            invoice_info = self.inventory_invoice.cursor.fetchone()
            
            if invoice_info:
                msg = f"""
                عرض الفاتورة:
                رقم الفاتورة: {invoice_info[0]}
                المورد: {invoice_info[1]}
                التاريخ: {invoice_info[2]}
                النوع: {invoice_info[3]}
                الحالة: {invoice_info[4]}
                الإجمالي: {invoice_info[5]:.2f}
                الملاحظات: {invoice_info[6] or 'لا توجد'}
                """
                QMessageBox.information(self, "عرض الفاتورة", msg)
            else:
                QMessageBox.warning(self, "خطأ", "لم يتم العثور على الفاتورة")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في عرض الفاتورة: {e}")

    def edit_invoice(self, invoice_id):
        """تعديل فاتورة"""
        try:
            # هنا يمكنك تنفيذ منطق التعديل
            # مثل تحميل بيانات الفاتورة إلى نموذج التعديل
            QMessageBox.information(self, "تعديل", f"سيتم تعديل الفاتورة رقم {invoice_id}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في التعديل: {e}")
    
    def delete_invoice(self, invoice_id):
        """حذف فاتورة"""
        try:
            reply = QMessageBox.question(self, "تأكيد الحذف", 
                                   f"هل أنت متأكد من حذف الفاتورة رقم {invoice_id}؟",
                                   QMessageBox.Yes | QMessageBox.No)
        
            if reply == QMessageBox.Yes:
                # احذف أيضًا الأصناف المرتبطة أولاً
                self.inventory_invoice.cursor.execute(
                    "DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,)
                )
                self.inventory_invoice.cursor.execute(
                    "DELETE FROM inventory_invoices WHERE id = ?", (invoice_id,)
                )
                self.inventory_invoice.conn.commit()
                QMessageBox.information(self, "نجاح", "تم حذف الفاتورة")
                self.load_invoices()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في الحذف: {e}")
    
    def print_invoice(self):
        """طباعة الفاتورة"""
        try:
            if not self.current_invoice_id:
                QMessageBox.warning(self, "تحذير", "لا يوجد فاتورة للطباعة")
                return
        
            # الحصول على بيانات الفاتورة
            self.inventory_invoice.cursor.execute("""
                SELECT ii.invoice_number, s.name_ar, ii.invoice_date, ii.invoice_type, 
                   ii.status, ii.total_amount, ii.notes
                FROM inventory_invoices ii
                JOIN suppliers s ON ii.supplier_id = s.id
                WHERE ii.id = ?
            """, (self.current_invoice_id,))
            invoice_info = self.inventory_invoice.cursor.fetchone()
        
            # الحصول على الأصناف
            self.inventory_invoice.cursor.execute("""
                SELECT i.item_code, i.item_name_ar, u.name_ar, ii.quantity, 
                   ii.unit_price, ii.discount_percent, ii.discount_amount, 
                   ii.bonus, ii.tax_percent, ii.total_price
                FROM invoice_items ii
                JOIN items i ON ii.item_id = i.id
                JOIN units u ON ii.unit_id = u.id
                WHERE ii.invoice_id = ?
            """, (self.current_invoice_id,))
            items = self.inventory_invoice.cursor.fetchall()
        
            # إنشاء محتوى HTML للطباعة مع تصميم عربي محسن
            html = f"""
            <!DOCTYPE html>
            <html dir='rtl'>
            <head>
                <meta charset='UTF-8'>
                <style>
                    body {{
                        font-family: 'Segoe UI', 'Arial', 'Tahoma';
                        margin: 20px;
                        background-color: #f8f9fa;
                    }}
                    .invoice-header {{
                        text-align: center;
                        background-color: #2c3e50;
                        color: white;
                        padding: 20px;
                        border-radius: 10px;
                        margin-bottom: 20px;
                    }}
                    .invoice-details {{
                        background-color: white;
                        padding: 20px;
                        border-radius: 10px;
                        margin-bottom: 20px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    }}
                    .invoice-items {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 20px;
                        background-color: white;
                        border-radius: 10px;
                        overflow: hidden;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    }}
                    .invoice-items th {{
                        background-color: #34495e;
                        color: white;
                        padding: 12px;
                        text-align: center;
                    }}
                    .invoice-items td {{
                        padding: 10px;
                        text-align: center;
                        border-bottom: 1px solid #ddd;
                    }}
                    .invoice-items tr:hover {{
                        background-color: #f5f5f5;
                    }}
                    .invoice-totals {{
                        background-color: #ecf0f1;
                        padding: 15px;
                        border-radius: 10px;
                        margin-bottom: 20px;
                    }}
                    .signature-section {{
                        display: flex;
                        justify-content: space-around;
                        margin-top: 50px;
                    }}
                    .signature {{
                        text-align: center;
                        border-top: 1px solid #000;
                        padding-top: 10px;
                        width: 200px;
                    }}
                </style>
            </head>
            <body>
                <div class='invoice-header'>
                    <h1>فاتورة مخزنية</h1>
                    <h2>رقم: {invoice_info[0]}</h2>
                </div>
            
                <div class='invoice-details'>
                    <table width='100%'>
                        <tr>
                            <td><strong>المورد:</strong> {invoice_info[1]}</td>
                            <td><strong>التاريخ:</strong> {invoice_info[2]}</td>
                        </tr>
                        <tr>
                            <td><strong>النوع:</strong> {invoice_info[3]}</td>
                            <td><strong>الحالة:</strong> {invoice_info[4]}</td>
                        </tr>
                    </table>
                </div>
            
                <h3>الأصناف</h3>
                <table class='invoice-items'>
                    <tr>
                        <th>كود الصنف</th>
                        <th>اسم الصنف</th>
                        <th>الوحدة</th>
                        <th>الكمية</th>
                        <th>سعر الوحدة</th>
                        <th>الخصم %</th>
                        <th>قيمة الخصم</th>
                        <th>البونص</th>
                        <th>الضريبة %</th>
                        <th>الإجمالي</th>
                    </tr>
            """
        
            for item in items:
                html += f"""
                    <tr>
                        <td>{item[0]}</td>
                        <td>{item[1]}</td>
                        <td>{item[2]}</td>
                        <td>{item[3]}</td>
                        <td>{item[4]:.2f}</td>
                        <td>{item[5]:.1f}%</td>
                        <td>{item[6]:.2f}</td>
                        <td>{item[7]}</td>
                        <td>{item[8]:.1f}%</td>
                        <td>{item[9]:.2f}</td>
                    </tr>
                """
        
            html += f"""
                </table>
            
                <div class='invoice-totals'>
                    <h3>الإجماليات</h3>
                    <p><strong>الإجمالي النهائي: {invoice_info[5]:.2f}</strong></p>
                </div>
            
                <div class='notes-section'>
                    <h3>ملاحظات</h3>
                    <p>{invoice_info[6] or 'لا توجد ملاحظات'}</p>
                </div>
            
                <div class='signature-section'>
                    <div class='signature'>توقيع المحاسب</div>
                    <div class='signature'>توقيع المدير</div>
                </div>
            </body>
            </html>
            """
        
            # طباعة المستند
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPrinter.A4)
            printer.setOutputFormat(QPrinter.NativeFormat)
        
            document = QTextDocument()
            document.setHtml(html)
            document.print_(printer)
        
            QMessageBox.information(self, "نجاح", "تم إرسال الفاتورة للطباعة")
        
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في الطباعة: {e}")
    
    def export_to_excel(self):
        """تصدير الفاتورة إلى Excel"""
        try:
            if not self.current_invoice_id:
                QMessageBox.warning(self, "تحذير", "لا يوجد فاتورة للتصدير")
                return
        
            # الحصول على بيانات الفاتورة
            self.inventory_invoice.cursor.execute("""
                SELECT ii.invoice_number, s.name_ar, ii.invoice_date, ii.invoice_type, 
                   ii.status, ii.total_amount, ii.notes
                FROM inventory_invoices ii
                JOIN suppliers s ON ii.supplier_id = s.id
                WHERE ii.id = ?
            """, (self.current_invoice_id,))
            invoice_info = self.inventory_invoice.cursor.fetchone()
        
            # الحصول على الأصناف
            self.inventory_invoice.cursor.execute("""
                SELECT i.item_code, i.item_name_ar, u.name_ar, ii.quantity, 
                   ii.unit_price, ii.discount_percent, ii.discount_amount, 
                   ii.bonus, ii.tax_percent, ii.total_price
                FROM invoice_items ii
                JOIN items i ON ii.item_id = i.id
                JOIN units u ON ii.unit_id = u.id
                WHERE ii.invoice_id = ?
            """, (self.current_invoice_id,))
            items = self.inventory_invoice.cursor.fetchall()
        
            # إنشاء DataFrame
            data = []
            for item in items:
                data.append({
                    'كود الصنف': item[0],
                    'اسم الصنف': item[1],
                    'الوحدة': item[2],
                    'الكمية': item[3],
                    'سعر الوحدة': item[4],
                    'الخصم %': item[5],
                    'قيمة الخصم': item[6],
                    'البونص': item[7],
                    'الضريبة %': item[8],
                    'الإجمالي': item[9]
                })
        
            df = pd.DataFrame(data)
        
            # حفظ في ملف Excel
            file_name = f"invoice_{invoice_info[0]}_{invoice_info[2]}.xlsx"
            df.to_excel(file_name, index=False, engine='openpyxl')
        
            QMessageBox.information(self, "نجاح", f"تم التصدير إلى {file_name}")
        
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في التصدير: {e}")
    
    def clear_form(self):
        """مسح النموذج"""
        self.current_invoice_id = None
        self.addition_combo.setCurrentIndex(0)
        self.invoice_date_edit.setDate(QDate.currentDate())
        self.invoice_type_combo.setCurrentIndex(0)
        self.items_table.setRowCount(0)
        self.discount_percent_spin.setValue(0)
        self.discount_amount_spin.setValue(0)
        self.tax_percent_spin.setValue(0)
        self.tax_amount_spin.setValue(0)
        self.notes_edit.clear()
        self.calculate_totals()
        self.update_btn.setEnabled(False)
        self.complete_btn.setEnabled(False)
        self.print_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
    
    def closeEvent(self, event):
        """إغلاق التطبيق"""
        try:
            self.inventory_invoice.close()
        except:
            pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InventoryInvoiceUI()
    window.show()
    sys.exit(app.exec_())
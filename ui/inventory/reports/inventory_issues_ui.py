import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QDateEdit, QComboBox,
    QPushButton, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QCheckBox
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont, QIcon, QColor

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

class InventoryIssuesUI(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.has_department_column = self.check_department_column_exists()

        self.setWindowTitle("📤 تقرير حركات المنصرف للمخازن")
        self.setWindowIcon(QIcon("inventory_icon.png"))
        self.resize(1800, 800)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.populate_warehouses()
        if self.has_department_column:
            self.populate_departments()
        self.populate_categories()
        self.populate_items()

    def check_department_column_exists(self):
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(items)")
            columns = [column[1] for column in cursor.fetchall()]
            conn.close()
            return 'department_id' in columns
        except:
            return False

    def setup_ui(self):
        font = QFont("Arial", 10)

        # ستايل للفلاتر
        style_groupbox = """
        QGroupBox {
            background-color: #F9F9F9;
            border: 2px solid #2980B9;
            border-radius: 8px;
            margin-top: 5px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top right;
            padding: 0 10px;
            color: #2C3E50;
            font-weight: bold;
            font-size: 10pt;
        }
        """

        # مجموعة فلترة التاريخ
        date_group = QGroupBox("فترة التقرير")
        date_group.setFont(font)
        date_group.setStyleSheet(style_groupbox)
        date_layout = QHBoxLayout()
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setFont(font)
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setFont(font)
        date_layout.addWidget(QLabel("من:"))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("إلى:"))
        date_layout.addWidget(self.end_date)
        date_group.setLayout(date_layout)

        # مجموعة فلترة المخازن
        warehouse_group = QGroupBox("المخزن")
        warehouse_group.setFont(font)
        warehouse_group.setStyleSheet(style_groupbox)
        warehouse_layout = QHBoxLayout()
        self.warehouse_selector = QComboBox()
        self.warehouse_selector.setFont(font)
        self.warehouse_selector.setMinimumWidth(180)
        self.warehouse_selector.setEnabled(False)
        self.all_warehouses_check = QCheckBox("عرض الكل")
        self.all_warehouses_check.setFont(font)
        self.all_warehouses_check.setChecked(True)
        self.all_warehouses_check.stateChanged.connect(self.toggle_warehouse_selector)
        warehouse_layout.addWidget(self.warehouse_selector)
        warehouse_layout.addWidget(self.all_warehouses_check)
        warehouse_group.setLayout(warehouse_layout)

        # مجموعة فلترة الأقسام
        self.department_group = QGroupBox("القسم")
        self.department_group.setFont(font)
        self.department_group.setStyleSheet(style_groupbox)
        department_layout = QHBoxLayout()
        self.department_selector = QComboBox()
        self.department_selector.setFont(font)
        self.department_selector.setMinimumWidth(180)
        self.department_selector.setEnabled(False)
        self.all_departments_check = QCheckBox("عرض الكل")
        self.all_departments_check.setFont(font)
        self.all_departments_check.setChecked(True)
        self.all_departments_check.stateChanged.connect(self.toggle_department_selector)
        department_layout.addWidget(self.department_selector)
        department_layout.addWidget(self.all_departments_check)
        self.department_group.setLayout(department_layout)
        if not self.has_department_column:
            self.department_group.hide()

        # مجموعة فلترة مجموعات الأصناف
        category_group = QGroupBox("مجموعة الصنف")
        category_group.setFont(font)
        category_group.setStyleSheet(style_groupbox)
        category_layout = QHBoxLayout()
        self.category_selector = QComboBox()
        self.category_selector.setFont(font)
        self.category_selector.setMinimumWidth(180)
        self.category_selector.setEnabled(False)
        self.all_categories_check = QCheckBox("عرض الكل")
        self.all_categories_check.setFont(font)
        self.all_categories_check.setChecked(True)
        self.all_categories_check.stateChanged.connect(self.toggle_category_selector)
        category_layout.addWidget(self.category_selector)
        category_layout.addWidget(self.all_categories_check)
        category_group.setLayout(category_layout)

        # مجموعة فلترة الأصناف
        item_group = QGroupBox("الصنف")
        item_group.setFont(font)
        item_group.setStyleSheet(style_groupbox)
        item_layout = QHBoxLayout()
        self.item_selector = QComboBox()
        self.item_selector.setFont(font)
        self.item_selector.setMinimumWidth(180)
        self.item_selector.setEnabled(False)
        self.all_items_check = QCheckBox("عرض الكل")
        self.all_items_check.setFont(font)
        self.all_items_check.setChecked(True)
        self.all_items_check.stateChanged.connect(self.toggle_item_selector)
        item_layout.addWidget(self.item_selector)
        item_layout.addWidget(self.all_items_check)
        item_group.setLayout(item_layout)

        # زر توليد التقرير
        self.generate_btn = QPushButton("📊 توليد التقرير")
        self.generate_btn.setFont(font)
        self.generate_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        self.generate_btn.clicked.connect(self.load_issues_report)

        # زر تصدير
        self.export_btn = QPushButton("📄 تصدير Excel")
        self.export_btn.setFont(font)
        self.export_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        self.export_btn.clicked.connect(self.export_to_excel)

        # زر تحديث
        self.refresh_btn = QPushButton("🔄 تحديث")
        self.refresh_btn.setFont(font)
        self.refresh_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        self.refresh_btn.clicked.connect(self.refresh_data)

        # تنظيم الفلاتر في صف أفقي واحد
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(date_group)
        filters_layout.addWidget(warehouse_group)
        if self.has_department_column:
            filters_layout.addWidget(self.department_group)
        filters_layout.addWidget(category_group)
        filters_layout.addWidget(item_group)
        filters_layout.addStretch()

        # تنظيم الأزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.generate_btn)
        buttons_layout.addWidget(self.export_btn)
        buttons_layout.addWidget(self.refresh_btn)
        buttons_layout.addStretch()

        # جدول النتائج
        self.table = QTableWidget()
        self.table.setFont(font)
        self.table.setColumnCount(14)
        headers = [
            "📅 التاريخ", "🔢 رقم الحركة", "🔁 نوع الحركة",
            "📦 كود الصنف", "📦 اسم الصنف", "📦 الوحدة",
            "🏬 المخزن", "🏢 القسم", "📦 مجموعة الصنف", "⬇️ الكمية",
            "💸 سعر البيع", "💵 إجمالي القيمة", "📄 المستند المرجعي", "📝 الوصف"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setLayoutDirection(Qt.RightToLeft)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #BDC3C7;
                selection-background-color: #3498DB;
                selection-color: white;
            }
            QHeaderView::section {
                background-color: #2C3E50;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
        """)

        # ملخص التقرير
        self.summary_label = QLabel("لم يتم توليد التقرير بعد.")
        self.summary_label.setFont(font)
        self.summary_label.setStyleSheet("font-weight: bold; color: #7F8C8D; padding: 10px;")

        # تجميع الواجهة
        main_layout = QVBoxLayout()
        main_layout.addLayout(filters_layout)
        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(self.summary_label)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)



    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def populate_warehouses(self):
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name_ar FROM warehouses WHERE is_active = 1 ORDER BY name_ar")
            warehouses = cursor.fetchall()
            conn.close()

            self.warehouse_selector.clear()
            self.warehouse_selector.addItem("-- اختر مخزن --", None)
            for warehouse in warehouses:
                self.warehouse_selector.addItem(warehouse['name_ar'], warehouse['id'])
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في تحميل المخازن: {str(e)}")

    def populate_departments(self):
        """تحميل قائمة الأقسام"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name_ar FROM departments WHERE is_active = 1 ORDER BY name_ar")
            departments = cursor.fetchall()
            conn.close()

            self.department_selector.clear()
            self.department_selector.addItem("-- اختر قسم --", None)
            for department in departments:
                self.department_selector.addItem(department['name_ar'], department['id'])
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في تحميل الأقسام: {str(e)}")

    def populate_categories(self):
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name_ar FROM item_categories WHERE is_active = 1 ORDER BY name_ar")
            categories = cursor.fetchall()
            conn.close()

            self.category_selector.clear()
            self.category_selector.addItem("-- اختر مجموعة صنف --", None)
            for category in categories:
                self.category_selector.addItem(category['name_ar'], category['id'])
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في تحميل مجموعات الأصناف: {str(e)}")

    def populate_items(self):
        try:
            conn = self._connect()
            cursor = conn.cursor()
            if self.has_department_column:
                cursor.execute("""
                    SELECT i.id, i.item_code, i.item_name_ar, u.name_ar as unit_name 
                    FROM items i 
                    LEFT JOIN units u ON i.base_unit_id = u.id 
                    WHERE i.is_active = 1 
                    ORDER BY i.item_name_ar
                """)
            else:
                cursor.execute("""
                    SELECT i.id, i.item_code, i.item_name_ar, u.name_ar as unit_name 
                    FROM items i 
                    LEFT JOIN units u ON i.base_unit_id = u.id 
                    WHERE i.is_active = 1 
                    ORDER BY i.item_name_ar
                """)
            items = cursor.fetchall()
            conn.close()

            self.item_selector.clear()
            self.item_selector.addItem("-- اختر صنف --", None)
            for item in items:
                display_text = f"{item['item_name_ar']} ({item['item_code']})"
                if item['unit_name']:
                    display_text += f" - {item['unit_name']}"
                self.item_selector.addItem(display_text, item['id'])
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في تحميل الأصناف: {str(e)}")

    def refresh_data(self):
        self.populate_warehouses()
        if self.has_department_column:
            self.populate_departments()  # إضافة تحديث الأقسام
        self.populate_categories()
        self.populate_items()
        QMessageBox.information(self, "تم التحديث", "تم تحديث قائمة المخازن والأقسام ومجموعات الأصناف والأصناف")

    def toggle_warehouse_selector(self):
        if self.all_warehouses_check.isChecked():
            self.warehouse_selector.setEnabled(False)
        else:
            self.warehouse_selector.setEnabled(True)

    def toggle_department_selector(self):
        """تفعيل/تعطيل فلتر الأقسام"""
        if self.all_departments_check.isChecked():
            self.department_selector.setEnabled(False)
        else:
            self.department_selector.setEnabled(True)

    def toggle_category_selector(self):
        if self.all_categories_check.isChecked():
            self.category_selector.setEnabled(False)
        else:
            self.category_selector.setEnabled(True)

    def toggle_item_selector(self):
        if self.all_items_check.isChecked():
            self.item_selector.setEnabled(False)
        else:
            self.item_selector.setEnabled(True)
            
    def get_transaction_type_arabic(self, trans_type):
        """ترجمة نوع الحركة من الإنجليزية إلى العربية"""
        mapping = {
            "Out": "صرف",
            "Sale": "بيع",
            "Issue": "إصدار",
            "Consumption": "استهلاك",
            "Return_Out": "مرتجع صرف",
            "In": "إدخال",
            "Purchase": "شراء",
            "Return_In": "مرتجع شراء",
        }
        return mapping.get(trans_type, trans_type)


    def load_issues_report(self):
        date_from = self.start_date.date().toString("yyyy-MM-dd")
        date_to = self.end_date.date().toString("yyyy-MM-dd")

        if date_from > date_to:
            QMessageBox.warning(self, "تحذير", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return

        try:
            conn = self._connect()
            cursor = conn.cursor()

            # تحديد معامل التصفية
            warehouse_filter = ""
            department_filter = ""  # إضافة فلتر الأقسام
            category_filter = ""
            item_filter = ""
            params = [date_from, date_to]
        
            if not self.all_warehouses_check.isChecked():
                warehouse_id = self.warehouse_selector.currentData()
                if warehouse_id:
                    warehouse_filter = " AND st.warehouse_id = ?"
                    params.append(warehouse_id)
                else:
                    QMessageBox.warning(self, "تحذير", "يجب اختيار مخزن معين")
                    return

            if self.has_department_column and not self.all_departments_check.isChecked():
                department_id = self.department_selector.currentData()
                if department_id:
                    department_filter = " AND i.department_id = ?"
                    params.append(department_id)
                else:
                    QMessageBox.warning(self, "تحذير", "يجب اختيار قسم معين")
                    return

            if not self.all_categories_check.isChecked():
                category_id = self.category_selector.currentData()
                if category_id:
                    category_filter = " AND i.item_category_id = ?"
                    params.append(category_id)
                else:
                    QMessageBox.warning(self, "تحذير", "يجب اختيار مجموعة صنف معينة")
                    return

            if not self.all_items_check.isChecked():
                item_id = self.item_selector.currentData()
                if item_id:
                    item_filter = " AND st.item_id = ?"
                    params.append(item_id)
                else:
                    QMessageBox.warning(self, "تحذير", "يجب اختيار صنف معين")
                    return

            # تحديث النص لإظهار أن التقرير قيد التحميل
            self.summary_label.setText("جاري تحميل تقرير المنصرف...")
            QApplication.processEvents()  # تحديث الواجهة

            # استعلام لحركات المنصرف مع إضافة اسم القسم ومجموعة الصنف
            if self.has_department_column:
                query = f"""
                SELECT 
                    st.transaction_date,
                    st.transaction_number,
                    st.transaction_type,
                    i.item_code,
                    i.item_name_ar,
                    u.name_ar as unit_name,
                    w.name_ar as warehouse_name,
                    d.name_ar as department_name,  -- اسم القسم
                    ic.name_ar as category_name,   -- اسم مجموعة الصنف
                    st.quantity,
                    st.unit_sale_price,
                    (st.quantity * st.unit_sale_price) as total_value,
                    st.reference_document,
                    st.description
                FROM stock_transactions st
                LEFT JOIN items i ON st.item_id = i.id
                LEFT JOIN units u ON i.base_unit_id = u.id
                LEFT JOIN warehouses w ON st.warehouse_id = w.id
                LEFT JOIN departments d ON i.department_id = d.id  -- الانضمام للجدول departments
                LEFT JOIN item_categories ic ON i.item_category_id = ic.id  -- الانضمام للجدول item_categories
                WHERE st.transaction_date BETWEEN ? AND ?
                AND st.transaction_type IN ('Out', 'Sale', 'Issue', 'Consumption', 'Return_Out')
                {warehouse_filter}
                {department_filter}
                {category_filter}
                {item_filter}
                ORDER BY st.transaction_date DESC, st.transaction_number DESC
                """
            else:
                query = f"""
                SELECT 
                    st.transaction_date,
                    st.transaction_number,
                    st.transaction_type,
                    i.item_code,
                    i.item_name_ar,
                    u.name_ar as unit_name,
                    w.name_ar as warehouse_name,
                    '' as department_name,  -- اسم القسم فارغ
                    ic.name_ar as category_name,   -- اسم مجموعة الصنف
                    st.quantity,
                    st.unit_sale_price,
                    (st.quantity * st.unit_sale_price) as total_value,
                    st.reference_document,
                    st.description
                FROM stock_transactions st
                LEFT JOIN items i ON st.item_id = i.id
                LEFT JOIN units u ON i.base_unit_id = u.id
                LEFT JOIN warehouses w ON st.warehouse_id = w.id
                LEFT JOIN item_categories ic ON i.item_category_id = ic.id  -- الانضمام للجدول item_categories
                WHERE st.transaction_date BETWEEN ? AND ?
                AND st.transaction_type IN ('Out', 'Sale', 'Issue', 'Consumption', 'Return_Out')
                {warehouse_filter}
                {category_filter}
                {item_filter}
                ORDER BY st.transaction_date DESC, st.transaction_number DESC
                """

            cursor.execute(query, params)
            transactions = cursor.fetchall()
            conn.close()

            if not transactions:
                self.table.setRowCount(0)
                self.summary_label.setText("لا توجد حركات منصرف في الفترة المحددة")
                return

            # عرض النتائج في الجدول
            self.table.setRowCount(len(transactions))
            total_quantity = 0
            total_value = 0

            for row_idx, transaction in enumerate(transactions):
                # تعبئة البيانات في الجدول
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(transaction['transaction_date'] or '---')))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(transaction['transaction_number'] or '---')))
            
                # ترجمة نوع الحركة
                trans_type = transaction['transaction_type']
                trans_type_text = self.get_transaction_type_arabic(trans_type)
            
                self.table.setItem(row_idx, 2, QTableWidgetItem(trans_type_text))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(transaction['item_code'] or '---')))
                self.table.setItem(row_idx, 4, QTableWidgetItem(str(transaction['item_name_ar'] or '---')))
                self.table.setItem(row_idx, 5, QTableWidgetItem(str(transaction['unit_name'] or '---')))
                self.table.setItem(row_idx, 6, QTableWidgetItem(str(transaction['warehouse_name'] or '---')))
                self.table.setItem(row_idx, 7, QTableWidgetItem(str(transaction['department_name'] or '---')))  # عرض اسم القسم
                self.table.setItem(row_idx, 8, QTableWidgetItem(str(transaction['category_name'] or '---')))  # عرض اسم مجموعة الصنف
            
                quantity = transaction['quantity'] or 0
                unit_sale_price = transaction['unit_sale_price'] or 0
                total_val = transaction['total_value'] or 0
            
                self.table.setItem(row_idx, 9, QTableWidgetItem(str(quantity)))
                self.table.setItem(row_idx, 10, QTableWidgetItem(f"{unit_sale_price:.2f}"))
                self.table.setItem(row_idx, 11, QTableWidgetItem(f"{total_val:.2f}"))
                self.table.setItem(row_idx, 12, QTableWidgetItem(str(transaction['reference_document'] or '---')))
                self.table.setItem(row_idx, 13, QTableWidgetItem(str(transaction['description'] or '---')))

                # جمع الإجماليات
                total_quantity += quantity
                total_value += total_val

            # إضافة صف الإجمالي
            self.table.insertRow(len(transactions))
            for col in range(14):
                item = QTableWidgetItem()
                if col == 6:
                    item.setText("الإجمالي:")
                elif col == 9:
                    item.setText(str(total_quantity))
                elif col == 11:
                    item.setText(f"{total_value:.2f}")
            
                if col in [6, 9, 11]:
                    item.setBackground(QColor(100, 150, 200))
                    item.setForeground(QColor(255, 255, 255))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
            
                self.table.setItem(len(transactions), col, item)

            # تحديث ملخص التقرير
            warehouse_name = "كل المخازن" if self.all_warehouses_check.isChecked() else self.warehouse_selector.currentText()
            department_name = "كل الأقسام" if self.all_departments_check.isChecked() else self.department_selector.currentText()
            category_name = "كل مجموعات الأصناف" if self.all_categories_check.isChecked() else self.category_selector.currentText()
            item_name = "كل الأصناف" if self.all_items_check.isChecked() else self.item_selector.currentText()
        
            self.summary_label.setText(
                f"حركات المنصرف في {warehouse_name} للقسم {department_name} ومجموعة الصنف {category_name} والصنف {item_name} من {date_from} إلى {date_to} | "
                f"عدد الحركات: {len(transactions)} | الكمية الإجمالية: {total_quantity} | القيمة الإجمالية: {total_value:.2f}"
            )

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل تقرير المنصرف: {str(e)}")
            print(f"Error details: {e}")

    def export_to_excel(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "تحذير", "لا توجد بيانات للتصدير. يرجى توليد التقرير أولاً.")
            return
            
        try:
            import pandas as pd
            
            # جمع البيانات من الجدول
            data = []
            for row in range(self.table.rowCount() - 1):  # استبعاد صف الإجمالي
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            
            # إنشاء DataFrame
            columns = [
                "التاريخ", "رقم الحركة", "نوع الحركة", 
                "كود الصنف", "اسم الصنف", "الوحدة",
                "المخزن", "القسم", "مجموعة الصنف", "الكمية",  # إضافة القسم ومجموعة الصنف
                "سعر البيع", "إجمالي القيمة", "المستند المرجعي", "الوصف"
            ]
            
            df = pd.DataFrame(data, columns=columns)
            
            # حفظ الملف
            date_from = self.start_date.date().toString("yyyy-MM-dd")
            date_to = self.end_date.date().toString("yyyy-MM-dd")
            warehouse_name = "كل_المخازن" if self.all_warehouses_check.isChecked() else self.warehouse_selector.currentText().replace(" ", "_")
            department_name = "كل_الأقسام" if self.all_departments_check.isChecked() else self.department_selector.currentText().replace(" ", "_")
            category_name = "كل_مجموعات_الأصناف" if self.all_categories_check.isChecked() else self.category_selector.currentText().replace(" ", "_")
            item_name = "كل_الأصناف" if self.all_items_check.isChecked() else self.item_selector.currentText().replace(" ", "_")
            
            filename = f"حركات_المنصرف_{warehouse_name}_{department_name}_{category_name}_{item_name}_{date_from}_إلى_{date_to}.xlsx"
            
            df.to_excel(filename, index=False, engine='openpyxl')
            
            QMessageBox.information(self, "تم التصدير", f"تم حفظ الملف: {filename}")
            
        except ImportError:
            QMessageBox.warning(self, "خطأ", "لم يتم تثبيت مكتبة pandas أو openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في التصدير: {str(e)}")

# تشغيل الواجهة
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    window = InventoryIssuesUI("database/inventory.db")
    window.show()
    sys.exit(app.exec_())
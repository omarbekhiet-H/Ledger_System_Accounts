import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QDateEdit, QComboBox,
    QPushButton, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QGroupBox, QCheckBox
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont, QIcon, QColor

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

class InventoryAdditionsUI(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path

        self.setWindowTitle("📥 تقرير حركات الإضافات للمخازن")
        self.setWindowIcon(QIcon("inventory_icon.png"))
        self.resize(1600, 800)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.populate_warehouses()
        self.populate_items()

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
        self.warehouse_selector.setMinimumWidth(200)
        self.warehouse_selector.setEnabled(False)
        self.all_warehouses_check = QCheckBox("عرض الكل")
        self.all_warehouses_check.setFont(font)
        self.all_warehouses_check.setChecked(True)
        self.all_warehouses_check.stateChanged.connect(self.toggle_warehouse_selector)
        warehouse_layout.addWidget(self.warehouse_selector)
        warehouse_layout.addWidget(self.all_warehouses_check)
        warehouse_group.setLayout(warehouse_layout)

        # مجموعة فلترة الأصناف
        item_group = QGroupBox("الصنف")
        item_group.setFont(font)
        item_group.setStyleSheet(style_groupbox)
        item_layout = QHBoxLayout()
        self.item_selector = QComboBox()
        self.item_selector.setFont(font)
        self.item_selector.setMinimumWidth(200)
        self.item_selector.setEnabled(False)
        self.all_items_check = QCheckBox("عرض الكل")
        self.all_items_check.setFont(font)
        self.all_items_check.setChecked(True)
        self.all_items_check.stateChanged.connect(self.toggle_item_selector)
        item_layout.addWidget(self.item_selector)
        item_layout.addWidget(self.all_items_check)
        item_group.setLayout(item_layout)

        # زر توليد التقرير
        self.generate_btn = QPushButton("📊 توليد تقرير الإضافات")
        self.generate_btn.setFont(font)
        self.generate_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        self.generate_btn.clicked.connect(self.load_additions_report)

        # أزرار إضافية
        self.export_btn = QPushButton("📄 تصدير Excel")
        self.export_btn.setFont(font)
        self.export_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        self.export_btn.clicked.connect(self.export_to_excel)

        self.refresh_btn = QPushButton("🔄 تحديث")
        self.refresh_btn.setFont(font)
        self.refresh_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        self.refresh_btn.clicked.connect(self.refresh_data)

        # تنظيم الفلاتر في صف أفقي واحد
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(date_group)
        filters_layout.addWidget(warehouse_group)
        filters_layout.addWidget(item_group)
        filters_layout.addStretch()

        # تنظيم الأزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.generate_btn)
        buttons_layout.addWidget(self.export_btn)
        buttons_layout.addWidget(self.refresh_btn)
        buttons_layout.addStretch()

        # جدول النتائج (بدون تغيير)
        self.table = QTableWidget()
        self.table.setFont(font)
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "📅 التاريخ", "🔢 رقم الحركة", "🔁 نوع الحركة", 
            "📦 كود الصنف", "📦 اسم الصنف", "🏬 المخزن", 
            "⬆️ الكمية", "💰 سعر الشراء", "💵 إجمالي التكلفة",
            "📄 المستند المرجعي", "📝 الوصف"
        ])
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
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #2C3E50;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
        """)

        # مؤشر التحميل والنتائج
        self.summary_label = QLabel("لم يتم توليد التقرير بعد.")
        self.summary_label.setFont(font)
        self.summary_label.setStyleSheet("font-weight: bold; color: #7F8C8D; padding: 10px;")

        # تنظيم الواجهة
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

    def populate_items(self):
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("SELECT id, item_code, item_name_ar FROM items WHERE is_active = 1 ORDER BY item_name_ar")
            items = cursor.fetchall()
            conn.close()

            self.item_selector.clear()
            self.item_selector.addItem("-- اختر صنف --", None)
            for item in items:
                self.item_selector.addItem(f"{item['item_name_ar']} ({item['item_code']})", item['id'])
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في تحميل الأصناف: {str(e)}")

    def refresh_data(self):
        self.populate_warehouses()
        self.populate_items()
        QMessageBox.information(self, "تم التحديث", "تم تحديث قائمة المخازن والأصناف")

    def toggle_warehouse_selector(self):
        if self.all_warehouses_check.isChecked():
            self.warehouse_selector.setEnabled(False)
        else:
            self.warehouse_selector.setEnabled(True)

    def toggle_item_selector(self):
        if self.all_items_check.isChecked():
            self.item_selector.setEnabled(False)
        else:
            self.item_selector.setEnabled(True)

    def load_additions_report(self):
        date_from = self.start_date.date().toString("yyyy-MM-dd")
        date_to = self.end_date.date().toString("yyyy-MM-dd")
    
        if date_from > date_to:
            QMessageBox.warning(self, "تحذير", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return
    
        try:
            conn = self._connect()
            cursor = conn.cursor()

            # تحديد معامل التصفية حسب المخزن
            warehouse_filter = ""
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

            if not self.all_items_check.isChecked():
                item_id = self.item_selector.currentData()
                if item_id:
                    item_filter = " AND st.item_id = ?"
                    params.append(item_id)
                else:
                    QMessageBox.warning(self, "تحذير", "يجب اختيار صنف معين")
                    return

            # تحديث النص لإظهار أن التقرير قيد التحميل
            self.summary_label.setText("جاري تحميل تقرير الإضافات...")
            QApplication.processEvents()  # تحديث الواجهة

            # استعلام لحركات الإضافات (الوارد فقط) - بدون created_by
            query = f"""
            SELECT 
                st.transaction_date,
                st.transaction_number,
                st.transaction_type,
                i.item_code,
                i.item_name_ar,
                w.name_ar as warehouse_name,
                st.quantity,
                st.unit_cost,
                (st.quantity * st.unit_cost) as total_cost,
                st.reference_document,
                st.description
            FROM stock_transactions st
            JOIN items i ON st.item_id = i.id
            LEFT JOIN warehouses w ON st.warehouse_id = w.id
            WHERE st.transaction_date BETWEEN ? AND ?
            AND st.transaction_type IN ('In', 'Purchase', 'Receive', 'Opening Balance', 'Addition', 'Return')
            {warehouse_filter}
            {item_filter}
            ORDER BY st.transaction_date DESC, st.id DESC
            """

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                self.table.setRowCount(0)
                self.summary_label.setText("لا توجد حركات إضافات في الفترة المحددة")
                return

            self.table.setRowCount(len(rows))
            
            total_quantity = 0
            total_cost = 0
            
            for row_num, row in enumerate(rows):
                quantity = row['quantity'] or 0
                unit_cost = row['unit_cost'] or 0
                row_total_cost = row['total_cost'] or 0
                
                total_quantity += quantity
                total_cost += row_total_cost

                self.table.setItem(row_num, 0, QTableWidgetItem(str(row['transaction_date'] or '---')))
                self.table.setItem(row_num, 1, QTableWidgetItem(str(row['transaction_number'] or '---')))
                self.table.setItem(row_num, 2, QTableWidgetItem(self.get_transaction_type_arabic(row['transaction_type'])))
                self.table.setItem(row_num, 3, QTableWidgetItem(str(row['item_code'] or '---')))
                self.table.setItem(row_num, 4, QTableWidgetItem(str(row['item_name_ar'] or '---')))
                self.table.setItem(row_num, 5, QTableWidgetItem(str(row['warehouse_name'] or '---')))
                self.table.setItem(row_num, 6, QTableWidgetItem(str(quantity)))
                self.table.setItem(row_num, 7, QTableWidgetItem(f"{unit_cost:.2f}"))
                self.table.setItem(row_num, 8, QTableWidgetItem(f"{row_total_cost:.2f}"))
                self.table.setItem(row_num, 9, QTableWidgetItem(str(row['reference_document'] or '---')))
                self.table.setItem(row_num, 10, QTableWidgetItem(str(row['description'] or '---')))

            # إضافة صف الإجمالي
            self.table.insertRow(len(rows))
            for col in range(11):
                item = QTableWidgetItem()
                if col == 5:
                    item.setText("الإجمالي:")
                elif col == 6:
                    item.setText(str(total_quantity))
                elif col == 8:
                    item.setText(f"{total_cost:.2f}")
                
                if col in [5, 6, 8]:
                    item.setBackground(QColor(100, 150, 200))
                    item.setForeground(QColor(255, 255, 255))
                    item.setFont(QFont("Arial", 10, QFont.Bold))
                
                self.table.setItem(len(rows), col, item)

            # تحديث ملخص التقرير
            warehouse_name = "كل المخازن" if self.all_warehouses_check.isChecked() else self.warehouse_selector.currentText()
            item_name = "كل الأصناف" if self.all_items_check.isChecked() else self.item_selector.currentText()
            
            self.summary_label.setText(
                f"حركات الإضافات في {warehouse_name} للصنف {item_name} من {date_from} إلى {date_to} | "
                f"عدد الحركات: {len(rows)} | الكمية الإجمالية: {total_quantity} | التكلفة الإجمالية: {total_cost:.2f}"
            )

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل تقرير الإضافات: {str(e)}")
            print(f"Error details: {e}")

    def get_transaction_type_arabic(self, transaction_type):
        """ترجمة نوع الحركة إلى العربية"""
        translations = {
            'In': 'وارد',
            'Purchase': 'شراء',
            'Receive': 'استلام',
            'Opening Balance': 'رصيد افتتاحي',
            'Addition': 'إضافة',
            'Return': 'مرتجع',
            'Out': 'صادر',
            'Sale': 'بيع',
            'Issue': 'صرف',
            'Consumption': 'استهلاك'
        }
        return translations.get(transaction_type, transaction_type)

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
                "كود الصنف", "اسم الصنف", "المخزن", 
                "الكمية", "سعر الشراء", "إجمالي التكلفة",
                "المستند المرجعي", "الوصف"
            ]
            
            df = pd.DataFrame(data, columns=columns)
            
            # حفظ الملف
            date_from = self.start_date.date().toString("yyyy-MM-dd")
            date_to = self.end_date.date().toString("yyyy-MM-dd")
            warehouse_name = "كل_المخازن" if self.all_warehouses_check.isChecked() else self.warehouse_selector.currentText().replace(" ", "_")
            item_name = "كل_الأصناف" if self.all_items_check.isChecked() else self.item_selector.currentText().replace(" ", "_")
            
            filename = f"حركات_الإضافات_{warehouse_name}_{item_name}_{date_from}_إلى_{date_to}.xlsx"
            
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
    window = InventoryAdditionsUI("database/inventory.db")
    window.show()
    sys.exit(app.exec_())
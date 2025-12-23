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

class InventoryBalanceUI(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path

        self.setWindowTitle("📊 تقرير رصيد المخزون")
        self.setWindowIcon(QIcon("inventory_icon.png"))
        self.resize(1400, 800)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.populate_warehouses()

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

        # زر توليد التقرير
        self.generate_btn = QPushButton("📊 توليد التقرير")
        self.generate_btn.setFont(font)
        self.generate_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        self.generate_btn.clicked.connect(self.load_inventory_balance)

        # أزرار إضافية
        self.export_btn = QPushButton("📄 تصدير Excel")
        self.export_btn.setFont(font)
        self.export_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        self.export_btn.clicked.connect(self.export_to_excel)

        self.refresh_btn = QPushButton("🔄 تحديث")
        self.refresh_btn.setFont(font)
        self.refresh_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        self.refresh_btn.clicked.connect(self.populate_warehouses)

        # تنظيم الفلاتر في صف أفقي واحد
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(date_group)
        filters_layout.addWidget(warehouse_group)
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
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "📦 كود الصنف", "📦 اسم الصنف", "🏬 المخزن", 
            "⬆️ الوارد", "⬇️ الصادر", "📊 الرصيد", 
            "💰 متوسط سعر الشراء", "💸 سعر البيع", "💵 إجمالي القيمة"
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

    def toggle_warehouse_selector(self):
        if self.all_warehouses_check.isChecked():
            self.warehouse_selector.setEnabled(False)
        else:
            self.warehouse_selector.setEnabled(True)

    def load_inventory_balance(self):
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
            params = [date_from, date_to]
            
            if not self.all_warehouses_check.isChecked():
                warehouse_id = self.warehouse_selector.currentData()
                if warehouse_id:
                    warehouse_filter = " AND st.warehouse_id = ?"
                    params.append(warehouse_id)
                else:
                    QMessageBox.warning(self, "تحذير", "يجب اختيار مخزن معين")
                    return

            # تحديث النص لإظهار أن التقرير قيد التحميل
            self.summary_label.setText("جاري توليد التقرير...")
            QApplication.processEvents()  # تحديث الواجهة

            # استعلام لرصيد المخزون
            query = f"""
            SELECT 
                i.item_code,
                i.item_name_ar,
                w.name_ar as warehouse_name,
                SUM(CASE 
                    WHEN st.transaction_type IN ('In', 'Purchase', 'Receive', 'Opening Balance') THEN st.quantity 
                    ELSE 0 
                END) as total_in,
                SUM(CASE 
                    WHEN st.transaction_type IN ('Out', 'Sale', 'Issue', 'Consumption') THEN st.quantity 
                    ELSE 0 
                END) as total_out,
                AVG(CASE 
                    WHEN st.transaction_type IN ('In', 'Purchase', 'Receive', 'Opening Balance') THEN st.unit_cost 
                    ELSE NULL 
                END) as avg_cost,
                AVG(CASE 
                    WHEN st.transaction_type IN ('Out', 'Sale', 'Issue', 'Consumption') THEN st.unit_sale_price 
                    ELSE NULL 
                END) as avg_sale_price
            FROM stock_transactions st
            JOIN items i ON st.item_id = i.id
            LEFT JOIN warehouses w ON st.warehouse_id = w.id
            WHERE st.transaction_date BETWEEN ? AND ?
            {warehouse_filter}
            GROUP BY i.id, i.item_code, i.item_name_ar, w.id, w.name_ar
            ORDER BY w.name_ar, i.item_name_ar
            """

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                self.table.setRowCount(0)
                self.summary_label.setText("لا توجد حركات في الفترة المحددة")
                return

            self.table.setRowCount(len(rows))
            
            total_value = 0
            total_balance = 0
            
            for row_num, row in enumerate(rows):
                balance = (row['total_in'] or 0) - (row['total_out'] or 0)
                avg_cost = row['avg_cost'] or 0
                item_value = balance * avg_cost
                
                total_balance += balance
                total_value += item_value

                self.table.setItem(row_num, 0, QTableWidgetItem(str(row['item_code'] or '---')))
                self.table.setItem(row_num, 1, QTableWidgetItem(str(row['item_name_ar'] or '---')))
                self.table.setItem(row_num, 2, QTableWidgetItem(str(row['warehouse_name'] or '---')))
                self.table.setItem(row_num, 3, QTableWidgetItem(str(row['total_in'] or 0)))
                self.table.setItem(row_num, 4, QTableWidgetItem(str(row['total_out'] or 0)))
                self.table.setItem(row_num, 5, QTableWidgetItem(str(balance)))
                self.table.setItem(row_num, 6, QTableWidgetItem(f"{avg_cost:.2f}"))
                self.table.setItem(row_num, 7, QTableWidgetItem(f"{row['avg_sale_price'] or 0:.2f}"))
                self.table.setItem(row_num, 8, QTableWidgetItem(f"{item_value:.2f}"))
                
                # تلوين الصفوف ذات الرصيد المنخفض
                if balance <= 0:
                    for col in range(self.table.columnCount()):
                        item = QTableWidgetItem(str(self.table.item(row_num, col).text()))
                        item.setBackground(QColor(255, 200, 200))
                        self.table.setItem(row_num, col, item)

            # إضافة صف الإجمالي
            self.table.insertRow(len(rows))
            for col in range(9):
                item = QTableWidgetItem()
                if col == 2:
                    item.setText("الإجمالي:")
                elif col == 5:
                    item.setText(str(total_balance))
                elif col == 8:
                    item.setText(f"{total_value:.2f}")
                
                item.setBackground(QColor(100, 150, 200))
                item.setForeground(QColor(255, 255, 255))
                item.setFont(QFont("Arial", 10, QFont.Bold))
                self.table.setItem(len(rows), col, item)

            # تحديث ملخص التقرير
            warehouse_name = "كل المخازن" if self.all_warehouses_check.isChecked() else self.warehouse_selector.currentText()
            self.summary_label.setText(
                f"رصيد المخزون في {warehouse_name} من {date_from} إلى {date_to} | "
                f"عدد الأصناف: {len(rows)} | الرصيد الإجمالي: {total_balance} | القيمة الإجمالية: {total_value:.2f}"
            )

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في توليد التقرير: {str(e)}")
            print(f"Error details: {e}")

    def export_to_excel(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "تحذير", "لا توجد بيانات للتصدير. يرجى توليد التقرير أولاً.")
            return
            
        try:
            import pandas as pd
            from datetime import datetime
            
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
                "كود الصنف", "اسم الصنف", "المخزن", 
                "الوارد", "الصادر", "الرصيد", 
                "متوسط سعر الشراء", "سعر البيع", "إجمالي القيمة"
            ]
            
            df = pd.DataFrame(data, columns=columns)
            
            # حفظ الملف
            date_from = self.start_date.date().toString("yyyy-MM-dd")
            date_to = self.end_date.date().toString("yyyy-MM-dd")
            filename = f"رصيد_المخزون_{date_from}_إلى_{date_to}.xlsx"
            
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
    window = InventoryBalanceUI("database/inventory.db")
    window.show()
    sys.exit(app.exec_())
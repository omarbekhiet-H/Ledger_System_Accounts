import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QDateEdit, QComboBox,
    QPushButton, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QGroupBox, QCheckBox, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont, QIcon, QColor

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

class InventoryCostUI(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path

        self.setWindowTitle("💰 تقرير تكلفة المخزون")
        self.setWindowIcon(QIcon("inventory_icon.png"))
        self.resize(1600, 800)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.populate_warehouses()

    def setup_ui(self):
        font = QFont("Arial", 10)

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
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setFont(font)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setFont(font)
        date_layout.addWidget(QLabel("من:"))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("إلى:"))
        date_layout.addWidget(self.end_date)
        date_group.setLayout(date_layout)

        # مجموعة طرق التقييم (في سطر واحد)
        valuation_group = QGroupBox("طريقة تقييم المخزون")
        valuation_group.setFont(font)
        valuation_group.setStyleSheet(style_groupbox)
        valuation_layout = QHBoxLayout()
        self.valuation_method_group = QButtonGroup(self)

        self.fifo_radio = QRadioButton("FIFO")
        self.fifo_radio.setChecked(True)
        self.valuation_method_group.addButton(self.fifo_radio, 1)

        self.lifo_radio = QRadioButton("LIFO")
        self.valuation_method_group.addButton(self.lifo_radio, 2)

        self.avg_cost_radio = QRadioButton("متوسط مرجح")
        self.valuation_method_group.addButton(self.avg_cost_radio, 3)

        self.standard_cost_radio = QRadioButton("متوسط شراء")
        self.valuation_method_group.addButton(self.standard_cost_radio, 4)

        self.specific_cost_radio = QRadioButton("آخر سعر شراء")
        self.valuation_method_group.addButton(self.specific_cost_radio, 5)

        valuation_layout.addWidget(self.fifo_radio)
        valuation_layout.addWidget(self.lifo_radio)
        valuation_layout.addWidget(self.avg_cost_radio)
        valuation_layout.addWidget(self.standard_cost_radio)
        valuation_layout.addWidget(self.specific_cost_radio)
        valuation_layout.addStretch()
        valuation_group.setLayout(valuation_layout)

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

        # الأزرار
        self.generate_btn = QPushButton("💰 توليد تقرير التكلفة")
        self.generate_btn.setFont(font)
        self.generate_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        self.generate_btn.clicked.connect(self.calculate_inventory_cost)

        self.export_btn = QPushButton("📄 تصدير Excel")
        self.export_btn.setFont(font)
        self.export_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        self.export_btn.clicked.connect(self.export_to_excel)

        self.refresh_btn = QPushButton("🔄 تحديث")
        self.refresh_btn.setFont(font)
        self.refresh_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        self.refresh_btn.clicked.connect(self.populate_warehouses)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.generate_btn)
        buttons_layout.addWidget(self.export_btn)
        buttons_layout.addWidget(self.refresh_btn)
        buttons_layout.addStretch()

        # جدول النتائج
        self.table = QTableWidget()
        self.table.setFont(font)
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "📦 كود الصنف", "📦 اسم الصنف", "🏬 المخزن", 
            "⬆️ الوارد", "⬇️ الصادر", "📊 الرصيد", 
            "💰 سعر التكلفة", "💵 إجمالي التكلفة",
            "💸 سعر البيع", "📈 هامش الربح"
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

        # ملخص
        self.summary_label = QLabel("لم يتم توليد التقرير بعد.")
        self.summary_label.setFont(font)
        self.summary_label.setStyleSheet("font-weight: bold; color: #7F8C8D; padding: 10px;")

        # تنظيم الواجهة
        main_layout = QVBoxLayout()
        main_layout.addWidget(date_group)       # الصف الأول
        main_layout.addWidget(valuation_group) # الصف الثاني
        main_layout.addWidget(warehouse_group) # الصف الثالث
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

    def calculate_inventory_cost(self):
        date_from = self.start_date.date().toString("yyyy-MM-dd")
        date_to = self.end_date.date().toString("yyyy-MM-dd")
    
        if date_from > date_to:
            QMessageBox.warning(self, "تحذير", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return
    
        # تحديد طريقة التقييم المختارة
        method_id = self.valuation_method_group.checkedId()
        method_name = ""
        
        if method_id == 1:
            method_name = "FIFO"
        elif method_id == 2:
            method_name = "LIFO"
        elif method_id == 3:
            method_name = "AVG_COST"
        elif method_id == 4:
            method_name = "AVG_COST"  # استخدام متوسط السعر بدلاً من التكلفة المعيارية
        elif method_id == 5:
            method_name = "SPECIFIC_COST"
    
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
            self.summary_label.setText("جاري حساب تكلفة المخزون...")
            QApplication.processEvents()  # تحديث الواجهة

            # استعلام أساسي للحصول على البيانات (بدون standard_cost)
            base_query = f"""
            SELECT 
                i.id as item_id,
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
            """

            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            
            if not rows:
                self.table.setRowCount(0)
                self.summary_label.setText("لا توجد حركات في الفترة المحددة")
                return

            # حساب التكلفة حسب الطريقة المختارة
            detailed_data = []
            for row in rows:
                item_id = row['item_id']
                balance = (row['total_in'] or 0) - (row['total_out'] or 0)
                
                # حساب سعر التكلفة حسب الطريقة المختارة
                unit_cost = 0
                if method_name == "FIFO":
                    unit_cost = self.calculate_fifo_cost(item_id, date_to, warehouse_filter, params)
                elif method_name == "LIFO":
                    unit_cost = self.calculate_lifo_cost(item_id, date_to, warehouse_filter, params)
                elif method_name == "AVG_COST":
                    unit_cost = row['avg_cost'] or 0
                elif method_name == "SPECIFIC_COST":
                    unit_cost = self.calculate_specific_cost(item_id, date_to, warehouse_filter, params)
                
                # إذا كانت التكلفة صفر، نستخدم متوسط السعر كبديل
                if unit_cost == 0:
                    unit_cost = row['avg_cost'] or 0
                
                total_cost = balance * unit_cost
                avg_sale_price = row['avg_sale_price'] or 0
                profit_margin = avg_sale_price - unit_cost if avg_sale_price > 0 else 0
                
                detailed_data.append({
                    'item_code': row['item_code'],
                    'item_name_ar': row['item_name_ar'],
                    'warehouse_name': row['warehouse_name'],
                    'total_in': row['total_in'] or 0,
                    'total_out': row['total_out'] or 0,
                    'balance': balance,
                    'unit_cost': unit_cost,
                    'total_cost': total_cost,
                    'avg_sale_price': avg_sale_price,
                    'profit_margin': profit_margin
                })

            conn.close()

            # عرض البيانات في الجدول
            self.display_cost_data(detailed_data, method_name)

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في حساب تكلفة المخزون: {str(e)}")
            print(f"Error details: {e}")

    def calculate_fifo_cost(self, item_id, date_to, warehouse_filter, base_params):
        """حساب التكلفة بطريقة الأول وارد أولاً صادر (FIFO)"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            
            # الحصول على الحركات الواردة مرتبة حسب التاريخ (الأقدم أولاً)
            query = f"""
            SELECT unit_cost, quantity, transaction_date
            FROM stock_transactions 
            WHERE item_id = ? 
            AND transaction_date <= ?
            AND transaction_type IN ('In', 'Purchase', 'Receive', 'Opening Balance')
            {warehouse_filter.replace('st.', '')}
            ORDER BY transaction_date ASC, id ASC
            """
            
            params = [item_id, date_to]
            if warehouse_filter:
                # إضافة معاملات المخزن إذا كانت موجودة
                warehouse_params = base_params[2:]
                params.extend(warehouse_params)
                
            cursor.execute(query, params)
            incoming_transactions = cursor.fetchall()
            
            # الحصول على الكمية الصادرة الإجمالية
            query = f"""
            SELECT COALESCE(SUM(quantity), 0) as total_out
            FROM stock_transactions 
            WHERE item_id = ? 
            AND transaction_date <= ?
            AND transaction_type IN ('Out', 'Sale', 'Issue', 'Consumption')
            {warehouse_filter.replace('st.', '')}
            """
            
            cursor.execute(query, params)
            total_out_result = cursor.fetchone()
            total_out = total_out_result['total_out'] if total_out_result else 0
            
            # تطبيق طريقة FIFO
            remaining_out = total_out
            fifo_cost = 0
            
            for transaction in incoming_transactions:
                if remaining_out <= 0:
                    break
                    
                quantity_used = min(transaction['quantity'], remaining_out)
                fifo_cost += quantity_used * (transaction['unit_cost'] or 0)
                remaining_out -= quantity_used
            
            conn.close()
            return fifo_cost / total_out if total_out > 0 else 0
            
        except Exception as e:
            print(f"Error in FIFO calculation: {e}")
            return 0

    def calculate_lifo_cost(self, item_id, date_to, warehouse_filter, base_params):
        """حساب التكلفة بطريقة آخر وارد أولاً صادر (LIFO)"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            
            # الحصول على الحركات الواردة مرتبة حسب التاريخ (الأحدث أولاً)
            query = f"""
            SELECT unit_cost, quantity, transaction_date
            FROM stock_transactions 
            WHERE item_id = ? 
            AND transaction_date <= ?
            AND transaction_type IN ('In', 'Purchase', 'Receive', 'Opening Balance')
            {warehouse_filter.replace('st.', '')}
            ORDER BY transaction_date DESC, id DESC
            """
            
            params = [item_id, date_to]
            if warehouse_filter:
                # إضافة معاملات المخزن إذا كانت موجودة
                warehouse_params = base_params[2:]
                params.extend(warehouse_params)
                
            cursor.execute(query, params)
            incoming_transactions = cursor.fetchall()
            
            # الحصول على الكمية الصادرة الإجمالية
            query = f"""
            SELECT COALESCE(SUM(quantity), 0) as total_out
            FROM stock_transactions 
            WHERE item_id = ? 
            AND transaction_date <= ?
            AND transaction_type IN ('Out', 'Sale', 'Issue', 'Consumption')
            {warehouse_filter.replace('st.', '')}
            """
            
            cursor.execute(query, params)
            total_out_result = cursor.fetchone()
            total_out = total_out_result['total_out'] if total_out_result else 0
            
            # تطبيق طريقة LIFO
            remaining_out = total_out
            lifo_cost = 0
            
            for transaction in incoming_transactions:
                if remaining_out <= 0:
                    break
                    
                quantity_used = min(transaction['quantity'], remaining_out)
                lifo_cost += quantity_used * (transaction['unit_cost'] or 0)
                remaining_out -= quantity_used
            
            conn.close()
            return lifo_cost / total_out if total_out > 0 else 0
            
        except Exception as e:
            print(f"Error in LIFO calculation: {e}")
            return 0

    def calculate_specific_cost(self, item_id, date_to, warehouse_filter, base_params):
        """حساب التكلفة المحددة (آخر سعر شراء)"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            
            query = f"""
            SELECT unit_cost
            FROM stock_transactions 
            WHERE item_id = ? 
            AND transaction_date <= ?
            AND transaction_type IN ('In', 'Purchase', 'Receive')
            {warehouse_filter.replace('st.', '')}
            ORDER BY transaction_date DESC, id DESC
            LIMIT 1
            """
            
            params = [item_id, date_to]
            if warehouse_filter:
                # إضافة معاملات المخزن إذا كانت موجودة
                warehouse_params = base_params[2:]
                params.extend(warehouse_params)
                
            cursor.execute(query, params)
            result = cursor.fetchone()
            conn.close()
            
            return result['unit_cost'] if result and result['unit_cost'] else 0
            
        except Exception as e:
            print(f"Error in specific cost calculation: {e}")
            return 0

    def display_cost_data(self, data, method_name):
        """عرض بيانات التكلفة في الجدول"""
        self.table.setRowCount(len(data))
        
        total_cost = 0
        total_balance = 0
        total_profit_margin = 0
        
        method_display_name = {
            "FIFO": "الأول وارد أولاً صادر",
            "LIFO": "آخر وارد أولاً صادر", 
            "AVG_COST": "متوسط السعر المرجح",
            "SPECIFIC_COST": "آخر سعر شراء"
        }.get(method_name, method_name)
        
        for row_num, row in enumerate(data):
            total_cost += row['total_cost']
            total_balance += row['balance']
            total_profit_margin += row['profit_margin'] * row['balance']
            
            self.table.setItem(row_num, 0, QTableWidgetItem(str(row['item_code'] or '---')))
            self.table.setItem(row_num, 1, QTableWidgetItem(str(row['item_name_ar'] or '---')))
            self.table.setItem(row_num, 2, QTableWidgetItem(str(row['warehouse_name'] or '---')))
            self.table.setItem(row_num, 3, QTableWidgetItem(str(row['total_in'])))
            self.table.setItem(row_num, 4, QTableWidgetItem(str(row['total_out'])))
            self.table.setItem(row_num, 5, QTableWidgetItem(str(row['balance'])))
            self.table.setItem(row_num, 6, QTableWidgetItem(f"{row['unit_cost']:.2f}" if row['unit_cost'] else "0.00"))
            self.table.setItem(row_num, 7, QTableWidgetItem(f"{row['total_cost']:.2f}" if row['total_cost'] else "0.00"))
            self.table.setItem(row_num, 8, QTableWidgetItem(f"{row['avg_sale_price']:.2f}" if row['avg_sale_price'] else "0.00"))
            self.table.setItem(row_num, 9, QTableWidgetItem(f"{row['profit_margin']:.2f}" if row['profit_margin'] else "0.00"))
            
            # تلوين الصفوف ذات الرصيد المنخفض أو التكلفة العالية
            if row['balance'] <= 0:
                for col in range(self.table.columnCount()):
                    item = QTableWidgetItem(str(self.table.item(row_num, col).text()))
                    item.setBackground(QColor(255, 200, 200))
                    self.table.setItem(row_num, col, item)
            elif row['profit_margin'] < 0:
                for col in range(self.table.columnCount()):
                    item = QTableWidgetItem(str(self.table.item(row_num, col).text()))
                    item.setBackground(QColor(255, 230, 200))
                    self.table.setItem(row_num, col, item)

        # إضافة صف الإجمالي
        self.table.insertRow(len(data))
        for col in range(10):
            item = QTableWidgetItem()
            if col == 2:
                item.setText("الإجمالي:")
            elif col == 5:
                item.setText(str(total_balance))
            elif col == 7:
                item.setText(f"{total_cost:.2f}")
            elif col == 9:
                item.setText(f"{total_profit_margin:.2f}")
            
            item.setBackground(QColor(100, 150, 200))
            item.setForeground(QColor(255, 255, 255))
            item.setFont(QFont("Arial", 10, QFont.Bold))
            self.table.setItem(len(data), col, item)

        # تحديث ملخص التقرير
        warehouse_name = "كل المخازن" if self.all_warehouses_check.isChecked() else self.warehouse_selector.currentText()
        date_from = self.start_date.date().toString("yyyy-MM-dd")
        date_to = self.end_date.date().toString("yyyy-MM-dd")
        
        self.summary_label.setText(
            f"تكلفة المخزون في {warehouse_name} من {date_from} إلى {date_to} | "
            f"طريقة التقييم: {method_display_name} | "
            f"عدد الأصناف: {len(data)} | الرصيد الإجمالي: {total_balance} | "
            f"التكلفة الإجمالية: {total_cost:.2f} | هامش الربح الإجمالي: {total_profit_margin:.2f}"
        )

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
                "كود الصنف", "اسم الصنف", "المخزن", 
                "الوارد", "الصادر", "الرصيد", 
                "سعر التكلفة", "إجمالي التكلفة",
                "سعر البيع", "هامش الربح"
            ]
            
            df = pd.DataFrame(data, columns=columns)
            
            # حفظ الملف
            date_from = self.start_date.date().toString("yyyy-MM-dd")
            date_to = self.end_date.date().toString("yyyy-MM-dd")
            method_id = self.valuation_method_group.checkedId()
            method_names = ["FIFO", "LIFO", "AVG_COST", "AVG_COST", "SPECIFIC_COST"]
            method_name = method_names[method_id-1] if 1 <= method_id <= 5 else "UNKNOWN"
            
            filename = f"تكلفة_المخزون_{method_name}_{date_from}_إلى_{date_to}.xlsx"
            
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
    window = InventoryCostUI("database/inventory.db")
    window.show()
    sys.exit(app.exec_())
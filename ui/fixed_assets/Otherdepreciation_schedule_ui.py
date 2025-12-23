# -*- coding: utf-8 -*-
import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox,
    QComboBox, QDateEdit, QHeaderView, QFrame
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor
import csv
from datetime import datetime, timedelta
import calendar

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.db_connection import get_fixed_assets_db_connection

class DepreciationScheduleUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("جدول الإهلاك - نظام الأصول الثابتة")
        self.resize(1600, 800)
        self.years = []
        self.asset_depreciation_data = {}  # لتخزين بيانات الإهلاك لكل أصل
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.setLayoutDirection(Qt.RightToLeft)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        filter_frame = QFrame()
        filter_frame.setFrameStyle(QFrame.Box)
        filter_frame.setLineWidth(1)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setSpacing(10)

        filter_layout.addWidget(QLabel("بحث:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("اكتب اسم الأصل أو الكود أو كود الإهلاك...")
        self.search_input.textChanged.connect(self.load_data)
        self.search_input.setMinimumWidth(200)
        filter_layout.addWidget(self.search_input)

        filter_layout.addWidget(QLabel("من سنة:"))
        self.from_year = QDateEdit()
        self.from_year.setDisplayFormat("yyyy")
        self.from_year.setDate(QDate.currentDate().addYears(-5))
        self.from_year.setCalendarPopup(True)
        self.from_year.dateChanged.connect(self.load_data)
        filter_layout.addWidget(self.from_year)

        filter_layout.addWidget(QLabel("إلى سنة:"))
        self.to_year = QDateEdit()
        self.to_year.setDisplayFormat("yyyy")
        self.to_year.setDate(QDate.currentDate().addYears(5))
        self.to_year.setCalendarPopup(True)
        self.to_year.dateChanged.connect(self.load_data)
        filter_layout.addWidget(self.to_year)

        filter_layout.addWidget(QLabel("وحدة الإهلاك:"))
        self.depreciation_unit_combo = QComboBox()
        self.depreciation_unit_combo.addItems(["سنوي", "نصف سنوي", "ربع سنوي", "شهري"])
        self.depreciation_unit_combo.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.depreciation_unit_combo)

        layout.addWidget(filter_frame)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
                border: 1px solid #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #3daee9;
                color: white;
            }
        """)
        layout.addWidget(self.table)

        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setAlignment(Qt.AlignLeft)

        self.export_csv_btn = QPushButton("📊 تصدير CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)
        btn_layout.addWidget(self.export_csv_btn)

        self.export_excel_btn = QPushButton("💾 تصدير Excel")
        self.export_excel_btn.clicked.connect(self.export_excel)
        btn_layout.addWidget(self.export_excel_btn)

        layout.addWidget(btn_frame)

        self.setLayout(layout)

    def calculate_depreciation_period(self, start_date, end_date, period_start, period_end):
        """حساب عدد الأشهر المستخدمة في الفترة"""
        if start_date > period_end or end_date < period_start:
            return 0.0
        
        effective_start = max(start_date, period_start)
        effective_end = min(end_date, period_end)
        
        if effective_start > effective_end:
            return 0.0
        
        # حساب الفرق بالأشهر بدقة
        total_days = (effective_end - effective_start).days
        months = total_days / 30.0  # تقريباً 30 يوم في الشهر
        
        return max(0.0, months)

    def calculate_straight_line_depreciation(self, cost, salvage, useful_life, period_months):
        """طريقة القسط الثابت"""
        if useful_life <= 0:
            return 0.0
        
        annual_dep = (cost - salvage) / useful_life
        return (annual_dep / 12) * period_months

    def calculate_double_declining_depreciation(self, asset_id, cost, salvage, useful_life, 
                                              period_months, period_start, period_end):
        """طريقة الرصيد المتناقص المزدوج"""
        if useful_life <= 0:
            return 0.0
        
        # الحصول على أو تحديث القيمة الدفترية الحالية للأصل
        if asset_id not in self.asset_depreciation_data:
            self.asset_depreciation_data[asset_id] = {
                'current_book_value': cost,
                'last_period_end': None
            }
        
        asset_data = self.asset_depreciation_data[asset_id]
        current_book_value = asset_data['current_book_value']
        
        # إذا كانت القيمة الدفترية أقل من أو تساوي القيمة التخريدية، لا يوجد إهلاك
        if current_book_value <= salvage:
            return 0.0
        
        # حساب معدل الإهلاك
        rate = 2.0 / useful_life
        
        # حساب الإهلاك للفترة
        dep = current_book_value * rate * (period_months / 12)
        
        # التأكد من أن الإهلاك لا يتجاوز القيمة القابلة للإهلاك
        max_dep = current_book_value - salvage
        actual_dep = min(dep, max_dep)
        
        # تحديث القيمة الدفترية للأصل
        self.asset_depreciation_data[asset_id]['current_book_value'] = current_book_value - actual_dep
        self.asset_depreciation_data[asset_id]['last_period_end'] = period_end
        
        return actual_dep

    def calculate_sum_of_years_depreciation(self, asset_id, cost, salvage, useful_life, 
                                          period_months, period_start, commissioning_date):
        """طريقة مجموع أرقام السنوات"""
        if useful_life <= 0:
            return 0.0
        
        # حساب مجموع أرقام السنوات
        sum_of_years = useful_life * (useful_life + 1) / 2
        
        # حساب عدد السنوات المنقضية منذ بداية التشغيل
        years_passed = self.calculate_years_passed(commissioning_date, period_start)
        
        if years_passed >= useful_life:
            return 0.0
        
        # حساب الكسر المخصص للفترة الحالية
        remaining_life = useful_life - years_passed
        dep_fraction = remaining_life / sum_of_years
        
        # حساب الإهلاك السنوي ثم تحويله إلى الفترة
        annual_dep = dep_fraction * (cost - salvage)
        period_dep = (annual_dep / 12) * period_months
        
        return period_dep

    def calculate_years_passed(self, start_date, current_date):
        """حساب عدد السنوات المنقضية بين تاريخين"""
        if start_date > current_date:
            return 0.0
        
        total_days = (current_date - start_date).days
        return total_days / 365.25  # سنة بمتوسط 365.25 يوم

    def calculate_depreciation(self, asset_id, method_code, cost, salvage, useful_life, 
                             period_months, period_start, period_end, commissioning_date):
        """دالة رئيسية لحساب الإهلاك بناءً على طريقة الإهلاك"""
        if method_code == "straight_line":
            return self.calculate_straight_line_depreciation(cost, salvage, useful_life, period_months)
        
        elif method_code == "double_declining":
            return self.calculate_double_declining_depreciation(
                asset_id, cost, salvage, useful_life, period_months, period_start, period_end
            )
        
        elif method_code == "sum_of_years":
            return self.calculate_sum_of_years_depreciation(
                asset_id, cost, salvage, useful_life, period_months, period_start, commissioning_date
            )
        
        else:
            # الطريقة الافتراضية (القسط الثابت)
            return self.calculate_straight_line_depreciation(cost, salvage, useful_life, period_months)

    def load_data(self):
        search_text = self.search_input.text()
        try:
            conn = get_fixed_assets_db_connection()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
            return
        
        cursor = conn.cursor()

        # 🔹 استعلام الأصول مع بيانات إضافية للإهلاك
        query = """
            SELECT f.id, f.asset_name_ar, f.acquisition_cost, f.salvage_value, 
                   f.current_book_value, f.accumulated_depreciation,
                   f.useful_life_years, f.acquisition_date, f.commissioning_date,
                   c.name_ar as category_name, d.name_ar as depreciation_method,
                   d.code as dep_method_code
            FROM fixed_assets f
            LEFT JOIN fixed_asset_categories c ON f.category_id = c.id
            LEFT JOIN depreciation_methods d ON f.depreciation_method_id = d.id
            WHERE f.is_active=1
        """
        params = ()
        if search_text:
            query += " AND (f.asset_name_ar LIKE ? OR f.asset_code LIKE ?)"
            params = (f"%{search_text}%", f"%{search_text}%")

        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()

        if not records:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        # 🔹 الأعمدة الزمنية حسب وحدة الإهلاك
        unit = self.depreciation_unit_combo.currentText()
        from_year_val = self.from_year.date().year()
        to_year_val = self.to_year.date().year()
        columns = []
        periods = []
        
        for year in range(from_year_val, to_year_val + 1):
            if unit == "سنوي":
                period_start = datetime(year, 1, 1)
                period_end = datetime(year, 12, 31)
                columns.append(str(year))
                periods.append((period_start, period_end))
                
            elif unit == "نصف سنوي":
                period_start1 = datetime(year, 1, 1)
                period_end1 = datetime(year, 6, 30)
                period_start2 = datetime(year, 7, 1)
                period_end2 = datetime(year, 12, 31)
                columns.extend([f"{year} النصف الأول", f"{year} النصف الثاني"])
                periods.extend([(period_start1, period_end1), (period_start2, period_end2)])
                
            elif unit == "ربع سنوي":
                quarters = [
                    (1, 1, 3, 31), (4, 1, 6, 30),
                    (7, 1, 9, 30), (10, 1, 12, 31)
                ]
                for q, (start_month, start_day, end_month, end_day) in enumerate(quarters, 1):
                    period_start = datetime(year, start_month, start_day)
                    period_end = datetime(year, end_month, end_day)
                    columns.append(f"{year} الربع {q}")
                    periods.append((period_start, period_end))
                    
            elif unit == "شهري":
                arabic_months = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                               "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
                for month in range(1, 13):
                    _, last_day = calendar.monthrange(year, month)
                    period_start = datetime(year, month, 1)
                    period_end = datetime(year, month, last_day)
                    columns.append(f"{arabic_months[month-1]} {year}")
                    periods.append((period_start, period_end))

        self.years = columns

        # 🔹 تهيئة الجدول
        fixed_cols = ["الأصل", "مجموعة الأصل", "التكلفة الأصلية", "القيمة التخريدية",
                      "القيمة الدفترية", "الإهلاك المتراكم", "عمر الأصل", "نوع الإهلاك",
                      "تاريخ الشراء", "تاريخ الاستخدام"]
        
        self.table.setColumnCount(len(fixed_cols) + len(self.years))
        headers = fixed_cols + self.years
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(records) + 1)  # +1 للإجمالي

        # تنسيق رأس الجدول
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(10)
        for i in range(self.table.columnCount()):
            item = QTableWidgetItem(headers[i])
            item.setFont(header_font)
            item.setTextAlignment(Qt.AlignCenter)
            item.setBackground(QColor(240, 240, 240))
            self.table.setHorizontalHeaderItem(i, item)

        totals = {
            "acquisition_cost": 0, 
            "salvage_value": 0, 
            "book_value": 0,
            "accumulated_dep": 0
        }
        period_totals = {col: 0 for col in self.years}

        # إعادة تهيئة بيانات الإهلاك
        self.asset_depreciation_data = {}

        for row_idx, row in enumerate(records):
            asset_id = row["id"]
            asset_name = row["asset_name_ar"]
            category = row["category_name"] or ""
            acquisition_cost = row["acquisition_cost"] or 0
            salvage_value = row["salvage_value"] or 0
            book_value = row["current_book_value"] or 0
            accumulated_dep = row["accumulated_depreciation"] or 0
            useful_life = row["useful_life_years"] or 1
            dep_method = row["depreciation_method"] or ""
            dep_method_code = row["dep_method_code"] or ""
            acq_date_str = row["acquisition_date"]
            comm_date_str = row["commissioning_date"] or acq_date_str

            # تحويل التواريخ
            try:
                start_date = datetime.strptime(acq_date_str, "%Y-%m-%d")
                comm_date = datetime.strptime(comm_date_str, "%Y-%m-%d") if comm_date_str else start_date
                end_date = comm_date.replace(year=comm_date.year + useful_life)
            except:
                start_date = datetime.now()
                comm_date = datetime.now()
                end_date = datetime.now().replace(year=datetime.now().year + useful_life)

            # تعبئة البيانات الثابتة
            self.set_table_item(row_idx, 0, asset_name, alignment=Qt.AlignRight)
            self.set_table_item(row_idx, 1, category)
            self.set_table_item(row_idx, 2, f"{acquisition_cost:,.2f}", is_number=True)
            self.set_table_item(row_idx, 3, f"{salvage_value:,.2f}", is_number=True)
            self.set_table_item(row_idx, 4, f"{book_value:,.2f}", is_number=True)
            self.set_table_item(row_idx, 5, f"{accumulated_dep:,.2f}", is_number=True)
            self.set_table_item(row_idx, 6, str(useful_life))
            self.set_table_item(row_idx, 7, dep_method)
            self.set_table_item(row_idx, 8, acq_date_str)
            self.set_table_item(row_idx, 9, comm_date_str)

            # تحديث الإجماليات
            totals["acquisition_cost"] += acquisition_cost
            totals["salvage_value"] += salvage_value
            totals["book_value"] += book_value
            totals["accumulated_dep"] += accumulated_dep

            # حساب الإهلاك لكل فترة
            for col_idx, (period_name, (period_start, period_end)) in enumerate(zip(self.years, periods), start=len(fixed_cols)):
                months_used = self.calculate_depreciation_period(comm_date, end_date, period_start, period_end)
                
                if months_used > 0:
                    # حساب الإهلاك بناءً على طريقة الإهلاك
                    dep_value = self.calculate_depreciation(
                        asset_id=asset_id,
                        method_code=dep_method_code,
                        cost=acquisition_cost,
                        salvage=salvage_value,
                        useful_life=useful_life,
                        period_months=months_used,
                        period_start=period_start,
                        period_end=period_end,
                        commissioning_date=comm_date
                    )
                else:
                    dep_value = 0.0
                
                self.set_table_item(row_idx, col_idx, f"{dep_value:,.2f}", is_number=True)
                period_totals[period_name] += dep_value

        # 🔹 صف الإجمالي
        total_row = len(records)
        self.set_table_item(total_row, 0, "الإجمالي", is_bold=True, background=QColor(220, 220, 220))
        self.set_table_item(total_row, 2, f"{totals['acquisition_cost']:,.2f}", is_number=True, is_bold=True, background=QColor(220, 220, 220))
        self.set_table_item(total_row, 3, f"{totals['salvage_value']:,.2f}", is_number=True, is_bold=True, background=QColor(220, 220, 220))
        self.set_table_item(total_row, 4, f"{totals['book_value']:,.2f}", is_number=True, is_bold=True, background=QColor(220, 220, 220))
        self.set_table_item(total_row, 5, f"{totals['accumulated_dep']:,.2f}", is_number=True, is_bold=True, background=QColor(220, 220, 220))

        for col_idx, period_name in enumerate(self.years, start=len(fixed_cols)):
            self.set_table_item(total_row, col_idx, f"{period_totals[period_name]:,.2f}", 
                               is_number=True, is_bold=True, background=QColor(220, 220, 220))

        # ضبط أبعاد الأعمدة
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def set_table_item(self, row, col, text, is_number=False, is_bold=False, background=None, alignment=Qt.AlignCenter):
        """دالة مساعدة لتعيين عناصر الجدول مع التنسيق"""
        item = QTableWidgetItem(text)
        
        if is_number:
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        if is_bold:
            font = QFont()
            font.setBold(True)
            item.setFont(font)
        
        if background:
            item.setBackground(background)
        
        if alignment:
            item.setTextAlignment(alignment)
        
        self.table.setItem(row, col, item)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "حفظ CSV", "جدول_الإهلاك.csv", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, mode='w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
                    writer.writerow(headers)
                    for row in range(self.table.rowCount()):
                        row_data = []
                        for col in range(self.table.columnCount()):
                            item = self.table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                QMessageBox.information(self, "نجاح", "تم تصدير الجدول إلى CSV بنجاح!")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في التصدير: {str(e)}")

    def export_excel(self):
        try:
            import pandas as pd
            path, _ = QFileDialog.getSaveFileName(self, "حفظ Excel", "جدول_الإهلاك.xlsx", "Excel Files (*.xlsx)")
            if path:
                data = []
                headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
                
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        text = item.text() if item else ""
                        # تحويل الأرقام
                        if col >= 2 and text.replace(',', '').replace('.', '').isdigit():
                            text = float(text.replace(',', ''))
                        row_data.append(text)
                    data.append(row_data)
                
                df = pd.DataFrame(data, columns=headers)
                df.to_excel(path, index=False, engine='openpyxl')
                QMessageBox.information(self, "نجاح", "تم تصدير الجدول إلى Excel بنجاح!")
                
        except ImportError:
            QMessageBox.warning(self, "تحذير", "حزمة pandas غير مثبتة. قم بتثبيتها باستخدام: pip install pandas openpyxl")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في التصدير: {str(e)}")

# ------------------------------------------------------------
# تشغيل التطبيق
# ------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # تحسين المظهر
    window = DepreciationScheduleUI()
    window.show()
    sys.exit(app.exec_())
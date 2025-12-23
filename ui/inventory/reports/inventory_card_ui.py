import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QDateEdit, QComboBox,
    QPushButton, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox,QGroupBox
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont, QIcon

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

class InventoryCardUI(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path

        self.setWindowTitle("📦 كارت حركة صنف")
        self.setWindowIcon(QIcon("inventory_icon.png"))
        self.resize(1400, 700)
        # تعيين اتجاه الواجهة إلى RTL للغة العربية
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
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

        # عناصر الإدخال
        self.item_selector = QComboBox()
        self.item_selector.setFont(font)
        self.item_selector.setMinimumWidth(200)
        self.item_selector.currentIndexChanged.connect(self.on_item_changed)  # تم تغيير الاستدعاء

        self.code_input = QLineEdit()
        self.code_input.setFont(font)
        self.code_input.setReadOnly(True)
        self.code_input.setMinimumWidth(100)

        self.name_label = QLabel("اسم الصنف: ---")
        self.name_label.setFont(font)
        self.name_label.setStyleSheet("font-weight: bold; color: #2C3E50;")

        # التاريخ
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setFont(font)

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setFont(font)

        # زر البحث
        self.search_btn = QPushButton("🔍 عرض التقرير")
        self.search_btn.setFont(font)
        self.search_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        self.search_btn.clicked.connect(self.load_inventory_card)

        # GroupBox للفلاتر
        filters_group = QGroupBox("إعدادات البحث")
        filters_group.setFont(font)
        filters_group.setStyleSheet(style_groupbox)

        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("اسم الصنف:"))
        filters_layout.addWidget(self.item_selector)
        filters_layout.addWidget(QLabel("كود الصنف:"))
        filters_layout.addWidget(self.code_input)
        filters_layout.addWidget(QLabel("من:"))   
        filters_layout.addWidget(self.start_date)
        filters_layout.addWidget(QLabel("إلى:"))  
        filters_layout.addWidget(self.end_date)
        filters_layout.addWidget(self.search_btn)
        filters_group.setLayout(filters_layout)

        # جدول النتائج
        self.table = QTableWidget()
        self.table.setFont(font)
        self.table.setColumnCount(16)
        self.table.setHorizontalHeaderLabels([
            "📅 التاريخ", "🔢 رقم الحركة", "🔁 نوع الحركة", "🏬 المستودع",
            "⬆️ الواردة", "⬇️ المنصرفة", "📊 الرصيد", "💰 سعر الشراء",
            "💸 سعر البيع", "💵 القيمة", "⏳ تاريخ الصلاحية", "📦 رقم الدفعة",
            "🔢 الرقم التسلسلي", "📄 المستند المرجعي", "📝 الوصف", "📦 وصف الصنف"
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

        # تنظيم الواجهة
        main_layout = QVBoxLayout()
        main_layout.addWidget(filters_group)
        main_layout.addWidget(self.name_label)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

    def clear_table(self):
        """مسح محتويات الجدول"""
        self.table.setRowCount(0)
        self.name_label.setText("اسم الصنف: ---")

    def on_item_changed(self):
        """معالج حدث تغيير الصنف المحدد"""
        self.clear_table()
        self.load_item_code()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

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

    def load_item_code(self):
        item_id = self.item_selector.currentData()
        if not item_id:
            self.code_input.clear()
            self.name_label.setText("اسم الصنف: ---")
            return
            
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("SELECT item_code, item_name_ar FROM items WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                self.code_input.setText(row['item_code'])
                self.name_label.setText(f"اسم الصنف: {row['item_name_ar']}")
            else:
                self.code_input.clear()
                self.name_label.setText("اسم الصنف: غير موجود")
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"خطأ في تحميل بيانات الصنف: {str(e)}")

    def load_inventory_card(self):
        item_id = self.item_selector.currentData()
        if not item_id:
            QMessageBox.warning(self, "تحذير", "يجب اختيار صنف أولاً")
            return

        date_from = self.start_date.date().toString("yyyy-MM-dd")
        date_to = self.end_date.date().toString("yyyy-MM-dd")
    
        if date_from > date_to:
            QMessageBox.warning(self, "تحذير", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return
    
        try:
            conn = self._connect()
            cursor = conn.cursor()
            print("Item ID:", item_id)
            print("Date from:", date_from)
            print("Date to:", date_to)

            # التحقق أولاً من وجود حركات للصنف
            check_query = "SELECT COUNT(*) as count FROM stock_transactions WHERE item_id = ?"
            cursor.execute(check_query, (item_id,))
            count_result = cursor.fetchone()
            print("Total movements for item:", count_result['count'])
            if count_result['count'] == 0:
                QMessageBox.information(self, "معلومات", "لا توجد حركات لهذا الصنف")
                conn.close()
                self.clear_table()  # مسح الجدول إذا لم توجد حركات
                return

            # استعلام معدل حسب الجدول الجديد
            query = """
            SELECT
                st.transaction_date,
                st.transaction_number,
                st.transaction_type,
                w.name_ar AS warehouse,
                CASE 
                    WHEN st.transaction_type IN ('In', 'Purchase', 'Receive', 'Opening Balance') THEN st.quantity 
                    ELSE 0 
                END AS qty_in,
                CASE 
                    WHEN st.transaction_type IN ('Out', 'Sale', 'Issue', 'Consumption') THEN st.quantity 
                    ELSE 0 
                END AS qty_out,
                st.unit_cost,
                st.unit_sale_price,
                CASE 
                    WHEN st.transaction_type IN ('In', 'Purchase', 'Receive', 'Opening Balance') THEN st.quantity * COALESCE(st.unit_cost, 0)
                    WHEN st.transaction_type IN ('Out', 'Sale', 'Issue', 'Consumption') THEN st.quantity * COALESCE(st.unit_sale_price, 0)
                    ELSE 0
                END AS total_value,
                st.expiry_date,
                st.batch_number,
                st.serial_number,
                st.reference_document,
                st.description,
                i.item_description,
                i.item_name_ar
            FROM stock_transactions st
            JOIN items i ON st.item_id = i.id
            LEFT JOIN warehouses w ON st.warehouse_id = w.id
            WHERE st.item_id = ?
              AND st.transaction_date BETWEEN ? AND ?
            ORDER BY st.transaction_date ASC, st.id ASC;
            """

            cursor.execute(query, (item_id, date_from, date_to))
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                QMessageBox.information(self, "معلومات", "لا توجد حركات في الفترة المحددة")
                self.clear_table()  # مسح الجدول إذا لم توجد حركات في الفترة المحددة
                return

            self.table.setRowCount(len(rows))
            
            # حساب الرصيد التراكمي
            balance = 0
            for row_num, row in enumerate(rows):
                qty_in = row['qty_in'] or 0
                qty_out = row['qty_out'] or 0
                balance += (qty_in - qty_out)

                self.table.setItem(row_num, 0, QTableWidgetItem(str(row['transaction_date'] or '---')))
                self.table.setItem(row_num, 1, QTableWidgetItem(str(row['transaction_number'] or '---')))
                self.table.setItem(row_num, 2, QTableWidgetItem(str(row['transaction_type'] or '---')))
                self.table.setItem(row_num, 3, QTableWidgetItem(str(row['warehouse'] or '---')))
                self.table.setItem(row_num, 4, QTableWidgetItem(str(qty_in)))
                self.table.setItem(row_num, 5, QTableWidgetItem(str(qty_out)))
                self.table.setItem(row_num, 6, QTableWidgetItem(str(balance)))
                self.table.setItem(row_num, 7, QTableWidgetItem(f"{row['unit_cost']:.2f}" if row['unit_cost'] else "0.00"))
                self.table.setItem(row_num, 8, QTableWidgetItem(f"{row['unit_sale_price']:.2f}" if row['unit_sale_price'] else "0.00"))
                self.table.setItem(row_num, 9, QTableWidgetItem(f"{row['total_value']:.2f}" if row['total_value'] else "0.00"))
                self.table.setItem(row_num, 10, QTableWidgetItem(str(row['expiry_date'] or '---')))
                self.table.setItem(row_num, 11, QTableWidgetItem(str(row['batch_number'] or '---')))
                self.table.setItem(row_num, 12, QTableWidgetItem(str(row['serial_number'] or '---')))
                self.table.setItem(row_num, 13, QTableWidgetItem(str(row['reference_document'] or '---')))
                self.table.setItem(row_num, 14, QTableWidgetItem(str(row['description'] or '---')))
                self.table.setItem(row_num, 15, QTableWidgetItem(str(row['item_description'] or row['item_name_ar'] or '---')))

            # إضافة صف إجمالي
            self.table.insertRow(len(rows))
            total_in = sum(row['qty_in'] or 0 for row in rows)
            total_out = sum(row['qty_out'] or 0 for row in rows)
            
            self.table.setItem(len(rows), 3, QTableWidgetItem("الإجمالي:"))
            self.table.setItem(len(rows), 4, QTableWidgetItem(str(total_in)))
            self.table.setItem(len(rows), 5, QTableWidgetItem(str(total_out)))
            self.table.setItem(len(rows), 6, QTableWidgetItem(str(balance)))
            
            # تلوين صف الإجمالي
            for col in range(self.table.columnCount()):
                item = self.table.item(len(rows), col)
                if item:
                    item.setBackground(QApplication.palette().highlight())
                    item.setForeground(QApplication.palette().highlightedText())

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل كارت المخزون: {str(e)}")
            print(f"Error details: {e}")

# تشغيل الواجهة
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # تعيين اتجاه التطبيق ككل إلى RTL
    app.setLayoutDirection(Qt.RightToLeft)
    window = InventoryCardUI("database/inventory.db")
    window.show()
    sys.exit(app.exec_())
# issue_request_ui.py
import sys
import os
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHBoxLayout,
    QLineEdit, QMessageBox, QComboBox, QDateEdit,
    QHeaderView, QTabWidget, QGroupBox, QGridLayout,
    QDoubleSpinBox, QTextEdit,QCompleter
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon

# --- إعداد المسارات ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)
from database.db_connection import get_inventory_db_connection

class IssueRequest_UI(QWidget):
    def __init__(self, user_id=1, user_name="مدير النظام"):
        super().__init__()
        self.user_id = user_id
        self.user_name = user_name
        self.current_request_id = None
        self.current_request_number = None
        self.selected_item_id = None
        
        # تطبيق اتجاه RTL للواجهة
        self.setLayoutDirection(Qt.RightToLeft)
        
        self.initUI()
        # تفعيل الأزرار يتم بعد اختيار صف
        self.view_details_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.manage_items_btn.setEnabled(False)
        self.approve_btn.setEnabled(False)

    def apply_styles(self):
        """تطبيق QSS مُصحح ومُحسّن."""
        self.setStyleSheet("""
            QWidget {
                font-family: "Arial", "Segoe UI", sans-serif;
                font-size: 13px;
            }
            QLabel#title {
                font-size: 20px;
                font-weight: bold;
                color: #0D47A1;
                text-align: center;
                margin: 10px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #D0D0D0;
                border-radius: 6px;
                margin-top: 10px;
                padding: 8px;
                background-color: #FAFAFA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                right: 10px;
                padding: 0 5px 0 5px;
                color: #0D47A1;
            }
            QPushButton {
                background-color: #1976D2;
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                border: none;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
            QPushButton[role="danger"] { background-color: #C62828; }
            QPushButton[role="danger"]:hover { background-color: #B71C1C; }
            QPushButton[role="success"] { background-color: #2E7D32; }
            QPushButton[role="success"]:hover { background-color: #1B5E20; }
            QPushButton[role="neutral"] { background-color: #455A64; }
            QPushButton[role="neutral"]:hover { background-color: #37474F; }
            QTableWidget {
                gridline-color: #E0E0E0;
                selection-background-color: #BBDEFB;
                alternate-background-color: #FAFAFA;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #E3F2FD;
                padding: 8px;
                border: 1px solid #E0E0E0;
                font-weight: bold;
                text-align: center;
            }
            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QTextEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, 
            QDoubleSpinBox:focus, QTextEdit:focus {
                border: 1px solid #1976D2;
            }
            QTabWidget::pane {
                border: 1px solid #C2C7CB;
                top: -1px;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #E1E1E1;
                border: 1px solid #C4C4C3;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1976D2;
                color: white;
            }
        """)

    def initUI(self):
        """تهيئة واجهة المستخدم"""
        self.setWindowTitle("نظام إدارة المخزون - طلبات الصرف")
        self.setGeometry(100, 50, 1400, 900)
        self.apply_styles()

        # إنشاء التبويبات
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        
        self.requests_tab = QWidget()
        self.items_tab = QWidget()
        self.details_tab = QWidget()

        self.setup_requests_tab()
        self.setup_items_tab()
        self.setup_details_tab()

        self.tabs.addTab(self.requests_tab, "📑 طلبات الصرف")
        self.tabs.addTab(self.items_tab, "📦 إدارة الأصناف")
        self.tabs.addTab(self.details_tab, "🔍 تفاصيل الطلب")

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)
        
        self.load_requests()

    def load_items_for_autocomplete(self):
        """تحميل قائمة الأصناف لتفعيل الإكمال التلقائي"""
        conn = get_inventory_db_connection()
        if not conn:
            return
        try:
            items = conn.execute("SELECT id, item_code, item_name_ar FROM items WHERE is_active = 1").fetchall()
            # نحفظ الأصناف في dict علشان نستخدمها لاحقًا
            self.items_dict = {f"{i['item_code']} - {i['item_name_ar']}": i for i in items}

            completer = QCompleter(list(self.items_dict.keys()))
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)  # 👈 يخلي البحث يظهر حتى لو النص في النص

            # ربط QCompleter بكود واسم الصنف
            self.selected_item_code.setCompleter(completer)
            self.selected_item_name.setCompleter(completer)

            completer.activated.connect(self.on_item_selected_from_completer)
        finally:
            conn.close()


    def on_item_selected_from_completer(self, text):
        """معالجة اختيار صنف من الإكمال التلقائي"""
        item = self.items_dict.get(text)
        if item:
            self.selected_item_id = item["id"]
            self.selected_item_code.setText(item["item_code"])
            self.selected_item_name.setText(item["item_name_ar"])
            # تحميل الوحدات الخاصة بالصنف
            self.load_item_units(self.selected_item_id)



    def setup_requests_tab(self):
        """إعداد تبويب عرض الطلبات"""
        layout = QVBoxLayout(self.requests_tab)
        layout.setAlignment(Qt.AlignRight)
        
        # العنوان
        title = QLabel("📑 إدارة طلبات الصرف")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # جدول الطلبات
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "رقم الطلب", "التاريخ", "الحالة", "القسم", "الغرض", "ملاحظات"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self.on_request_selected)
        layout.addWidget(self.table)

        # نموذج إضافة طلب جديد
        form_group = QGroupBox("إضافة طلب صرف جديد")
        form_layout = QGridLayout(form_group)
        form_layout.setAlignment(Qt.AlignRight)
        
        form_layout.addWidget(QLabel("الغرض:"), 0, 0)
        self.purpose_input = QLineEdit()
        self.purpose_input.setPlaceholderText("الغرض من الطلب")
        form_layout.addWidget(self.purpose_input, 0, 1)
        
        form_layout.addWidget(QLabel("القسم:"), 0, 2)
        self.department_combo = QComboBox()
        self.load_departments()
        form_layout.addWidget(self.department_combo, 0, 3)
        
        form_layout.addWidget(QLabel("التاريخ:"), 1, 0)
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        form_layout.addWidget(self.date_input, 1, 1)
        
        form_layout.addWidget(QLabel("المخزن:"), 1, 2)
        self.warehouse_combo = QComboBox()
        self.load_warehouses()
        form_layout.addWidget(self.warehouse_combo, 1, 3)
        
        form_layout.addWidget(QLabel("ملاحظات:"), 2, 0)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("ملاحظات إضافية")
        form_layout.addWidget(self.notes_input, 2, 1, 1, 3)
        
        add_btn = QPushButton("➕ إضافة طلب جديد")
        add_btn.setProperty("role", "success")
        add_btn.clicked.connect(self.add_issue_request)
        form_layout.addWidget(add_btn, 3, 0, 1, 4)
        
        layout.addWidget(form_group)

        # أزرار التحكم
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignRight)
        
        refresh_btn = QPushButton("🔄 تحديث البيانات")
        refresh_btn.setProperty("role", "neutral")
        refresh_btn.clicked.connect(self.load_requests)
        button_layout.addWidget(refresh_btn)
        
        self.view_details_btn = QPushButton("👁️ عرض التفاصيل")
        self.view_details_btn.clicked.connect(self.show_request_details)
        button_layout.addWidget(self.view_details_btn)
        
        self.delete_btn = QPushButton("🗑️ حذف الطلب")
        self.delete_btn.setProperty("role", "danger")
        self.delete_btn.clicked.connect(self.delete_request)
        button_layout.addWidget(self.delete_btn)
        
        self.manage_items_btn = QPushButton("📦 إدارة الأصناف")
        self.manage_items_btn.clicked.connect(self.switch_to_items_tab)
        button_layout.addWidget(self.manage_items_btn)
        
        self.approve_btn = QPushButton("✅ اعتماد الطلب")
        self.approve_btn.setProperty("role", "success")
        self.approve_btn.clicked.connect(self.approve_request)
        button_layout.addWidget(self.approve_btn)
        
        layout.addLayout(button_layout)

    def setup_items_tab(self):
        """إعداد تبويب إدارة الأصناف"""
        layout = QVBoxLayout(self.items_tab)
        layout.setAlignment(Qt.AlignRight)
        
        # معلومات الطلب المحدد
        self.selected_request_label = QLabel("لم يتم تحديد أي طلب - الرجاء اختيار طلب من تبويب طلبات الصرف")
        self.selected_request_label.setStyleSheet("font-size: 14px; color: #D32F2F; margin: 10px; padding: 8px; background-color: #FFEBEE; border-radius: 4px;")
        self.selected_request_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.selected_request_label)

        # مجموعة البحث
        search_group = QGroupBox("بحث الأصناف")
        search_layout = QHBoxLayout(search_group)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث بكود الصنف أو اسم الصنف...")
        self.search_input.textChanged.connect(self.search_items)
        search_layout.addWidget(self.search_input)
        layout.addWidget(search_group)

        # جدول نتائج البحث
        self.search_table = QTableWidget()
        self.search_table.setColumnCount(6)
        self.search_table.setHorizontalHeaderLabels(["ID", "كود الصنف", "اسم الصنف", "المجموعة", "الوحدة", "الإجراء"])
        self.search_table.setColumnHidden(0, True)
        self.search_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.search_table)

        # مجموعة إضافة الصنف للطلب
        add_group = QGroupBox("إضافة صنف للطلب")
        add_layout = QGridLayout(add_group)
        add_layout.setAlignment(Qt.AlignRight)
        
        add_layout.addWidget(QLabel("كود الصنف:"), 0, 0)
        self.selected_item_code = QLineEdit()
        self.selected_item_code.setPlaceholderText("اكتب كود الصنف...")
        add_layout.addWidget(self.selected_item_code, 0, 1)
       

        #self.selected_item_code.setReadOnly(True)
        #self.selected_item_code.setStyleSheet("background-color: #F5F5F5;")
        #add_layout.addWidget(self.selected_item_code, 0, 1)
        
        add_layout.addWidget(QLabel("اسم الصنف:"), 0, 2)
        self.selected_item_name = QLineEdit()
        self.selected_item_name = QLineEdit()
        self.selected_item_name.setPlaceholderText("اكتب اسم الصنف...")
        add_layout.addWidget(self.selected_item_name, 0, 3)

        #self.selected_item_name.setReadOnly(True)
        #self.selected_item_name.setStyleSheet("background-color: #F5F5F5;")
        #add_layout.addWidget(self.selected_item_name, 0, 3)
        
        # تحميل الأصناف للإكمال التلقائي
        self.load_items_for_autocomplete()

        add_layout.addWidget(QLabel("الكمية:"), 1, 0)
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.1, 99999)
        self.quantity_input.setValue(1.0)
        add_layout.addWidget(self.quantity_input, 1, 1)
        
        add_layout.addWidget(QLabel("الوحدة:"), 1, 2)
        self.unit_combo = QComboBox()
        add_layout.addWidget(self.unit_combo, 1, 3)
        
        add_layout.addWidget(QLabel("التاريخ المطلوب:"), 2, 0)
        self.required_date_input = QDateEdit(QDate.currentDate())
        self.required_date_input.setCalendarPopup(True)
        self.required_date_input.setDisplayFormat("yyyy-MM-dd")
        add_layout.addWidget(self.required_date_input, 2, 1)
        
        add_layout.addWidget(QLabel("ملاحظات:"), 2, 2)
        self.item_notes_input = QLineEdit()
        self.item_notes_input.setPlaceholderText("ملاحظات على الصنف")
        add_layout.addWidget(self.item_notes_input, 2, 3)
        
        add_item_btn = QPushButton("➕ إضافة الصنف للطلب")
        add_item_btn.setProperty("role", "success")
        add_item_btn.clicked.connect(self.add_item_to_request)
        add_layout.addWidget(add_item_btn, 3, 0, 1, 4)
        
        layout.addWidget(add_group)

        # جدول أصناف الطلب
        items_label = QLabel("الأصناف المضافة للطلب:")
        items_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 5px;")
        layout.addWidget(items_label)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(9)
        self.items_table.setHorizontalHeaderLabels(["ID", "كود الصنف", "اسم الصنف", "الكمية", "الوحدة", "الحالة", "ملاحظات", "التاريخ المطلوب", "الإجراءات"])
        self.items_table.setColumnHidden(0, True)
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.items_table)

        # زر العودة
        back_btn = QPushButton("↩ العودة إلى طلبات الصرف")
        back_btn.clicked.connect(self.switch_to_requests_tab)
        layout.addWidget(back_btn)


    def setup_details_tab(self):
        """إعداد تبويب تفاصيل الطلب"""
        layout = QVBoxLayout(self.details_tab)
        layout.setAlignment(Qt.AlignRight)
        
        self.details_request_label = QLabel("لم يتم تحديد أي طلب - الرجاء اختيار طلب من تبويب طلبات الصرف")
        self.details_request_label.setStyleSheet("font-size: 14px; color: #D32F2F; margin: 10px; padding: 8px; background-color: #FFEBEE; border-radius: 4px;")
        self.details_request_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.details_request_label)
        
        # معلومات الطلب
        info_group = QGroupBox("معلومات الطلب")
        info_layout = QGridLayout(info_group)
        info_layout.setAlignment(Qt.AlignRight)
        
        info_layout.addWidget(QLabel("رقم الطلب:"), 0, 0)
        self.details_number = QLineEdit()
        self.details_number.setReadOnly(True)
        self.details_number.setStyleSheet("background-color: #F5F5F5;")
        info_layout.addWidget(self.details_number, 0, 1)
        
        info_layout.addWidget(QLabel("التاريخ:"), 0, 2)
        self.details_date = QLineEdit()
        self.details_date.setReadOnly(True)
        self.details_date.setStyleSheet("background-color: #F5F5F5;")
        info_layout.addWidget(self.details_date, 0, 3)
        
        info_layout.addWidget(QLabel("القسم:"), 1, 0)
        self.details_department = QLineEdit()
        self.details_department.setReadOnly(True)
        self.details_department.setStyleSheet("background-color: #F5F5F5;")
        info_layout.addWidget(self.details_department, 1, 1)
        
        info_layout.addWidget(QLabel("المخزن:"), 1, 2)
        self.details_warehouse = QLineEdit()
        self.details_warehouse.setReadOnly(True)
        self.details_warehouse.setStyleSheet("background-color: #F5F5F5;")
        info_layout.addWidget(self.details_warehouse, 1, 3)
        
        info_layout.addWidget(QLabel("الحالة:"), 2, 0)
        self.details_status = QLineEdit()
        self.details_status.setReadOnly(True)
        self.details_status.setStyleSheet("background-color: #F5F5F5;")
        info_layout.addWidget(self.details_status, 2, 1)
        
        info_layout.addWidget(QLabel("الغرض:"), 2, 2)
        self.details_purpose = QLineEdit()
        self.details_purpose.setReadOnly(True)
        self.details_purpose.setStyleSheet("background-color: #F5F5F5;")
        info_layout.addWidget(self.details_purpose, 2, 3)
        
        layout.addWidget(info_group)

        # جدول الأصناف
        items_label = QLabel("الأصناف في الطلب:")
        items_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 5px;")
        layout.addWidget(items_label)
        
        self.details_items_table = QTableWidget()
        self.details_items_table.setColumnCount(7)
        self.details_items_table.setHorizontalHeaderLabels(["كود الصنف", "اسم الصنف", "الكمية", "الوحدة", "الحالة", "ملاحظات", "التاريخ المطلوب"])
        self.details_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.details_items_table)

        # زر العودة
        back_btn = QPushButton("↩ العودة إلى طلبات الصرف")
        back_btn.clicked.connect(self.switch_to_requests_tab)
        layout.addWidget(back_btn)

    def on_request_selected(self):
        """عند اختيار طلب من الجدول"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.current_request_id = None
            self.current_request_number = None
            self.view_details_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.manage_items_btn.setEnabled(False)
            self.approve_btn.setEnabled(False)
            
            self.selected_request_label.setText("لم يتم تحديد أي طلب - الرجاء اختيار طلب من تبويب طلبات الصرف")
            return

        current_row = selected_items[0].row()
        self.current_request_id = self.table.item(current_row, 0).text()
        self.current_request_number = self.table.item(current_row, 1).text()
        
        self.selected_request_label.setText(f"الطلب المحدد: {self.current_request_number} (ID: {self.current_request_id})")
        self.selected_request_label.setStyleSheet("font-size: 14px; color: #2E7D32; margin: 10px; padding: 8px; background-color: #E8F5E8; border-radius: 4px;")
        
        self.view_details_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.manage_items_btn.setEnabled(True)
        
        # تفعيل زر الاعتماد فقط إذا كان الطلب قيد الانتظار
        status = self.table.item(current_row, 3).text()
        self.approve_btn.setEnabled(status.lower() == "pending")

    def switch_to_items_tab(self):
        """الانتقال إلى تبويب الأصناف"""
        if not self.current_request_id:
            QMessageBox.warning(self, "تحذير", "⚠️ الرجاء اختيار طلب أولاً")
            return
        self.tabs.setCurrentIndex(1)
        self.search_items()
        self.load_request_items()


    def switch_to_requests_tab(self):
        self.tabs.setCurrentIndex(0)

    def search_items(self):
        """بحث الأصناف وعرضها"""
        search_text = self.search_input.text().strip()
        conn = get_inventory_db_connection()
        if not conn: return

        try:
            query = """
                SELECT i.id, i.item_code, i.item_name_ar, ig.name_ar as group_name, u.name_ar as unit_name
                FROM items i
                LEFT JOIN item_groups ig ON i.item_group_id = ig.id
                LEFT JOIN units u ON i.base_unit_id = u.id
                WHERE (i.item_code LIKE ? OR i.item_name_ar LIKE ?) AND i.is_active = 1
                LIMIT 100;
            """
            items = conn.execute(query, (f'%{search_text}%', f'%{search_text}%')).fetchall()
            
            self.search_table.setRowCount(len(items))
            for row, item in enumerate(items):
                self.search_table.setItem(row, 0, QTableWidgetItem(str(item["id"])))
                self.search_table.setItem(row, 1, QTableWidgetItem(item["item_code"]))
                self.search_table.setItem(row, 2, QTableWidgetItem(item["item_name_ar"]))
                self.search_table.setItem(row, 3, QTableWidgetItem(item["group_name"] or ""))
                self.search_table.setItem(row, 4, QTableWidgetItem(item["unit_name"] or ""))
                
                select_btn = QPushButton("➕")
                select_btn.clicked.connect(lambda _, r=row: self.select_item_from_search(r))
                self.search_table.setCellWidget(row, 5, select_btn)
        finally:
            conn.close()

    def select_item_from_search(self, row):
        """اختيار صنف من جدول البحث"""
        self.selected_item_id = int(self.search_table.item(row, 0).text())
        self.selected_item_code.setText(self.search_table.item(row, 1).text())
        self.selected_item_name.setText(self.search_table.item(row, 2).text())
        
        # تحميل الوحدات المتاحة للصنف
        self.load_item_units(self.selected_item_id)

    def load_item_units(self, item_id):
        """تحميل الوحدات المتاحة للصنف"""
        conn = get_inventory_db_connection()
        if not conn: return
        
        try:
            self.unit_combo.clear()
            units = conn.execute("""
                SELECT u.id, u.name_ar 
                FROM item_units iu
                JOIN units u ON iu.unit_id = u.id
                WHERE iu.item_id = ? AND u.is_active = 1
            """, (item_id,)).fetchall()
            
            for unit in units:
                self.unit_combo.addItem(unit["name_ar"], unit["id"])
        finally:
            conn.close()

    def add_item_to_request(self):
        """إضافة الصنف المختار إلى طلب الصرف"""
        if not self.current_request_id or not self.selected_item_id:
            QMessageBox.warning(self, "تحذير", "⚠️ يرجى اختيار طلب وصنف أولاً")
            return
        
        quantity = self.quantity_input.value()
        if quantity <= 0:
            QMessageBox.warning(self, "تحذير", "⚠️ الكمية يجب أن تكون أكبر من صفر")
            return
        
        unit_id = self.unit_combo.currentData()
        if not unit_id:
            QMessageBox.warning(self, "تحذير", "⚠️ يرجى اختيار وحدة")
            return

        required_date = self.required_date_input.date().toString("yyyy-MM-dd") if self.required_date_input.date() else None
        notes = self.item_notes_input.text()

        conn = get_inventory_db_connection()
        if not conn: return

        try:
            conn.execute("""
                INSERT INTO issue_request_items 
                (request_id, item_id, quantity, unit_id, required_date, notes, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
            """, (self.current_request_id, self.selected_item_id, quantity, unit_id, 
                 required_date, notes, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            QMessageBox.information(self, "تم", "✅ تم إضافة الصنف إلى الطلب")
            self.quantity_input.setValue(0.1)
            self.item_notes_input.clear()
            self.load_request_items()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "مكرر", "هذا الصنف موجود بالفعل في الطلب.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {e}")
        finally:
            conn.close()

    def load_request_items(self):
        """تحميل أصناف الطلب المحدد"""
        if not self.current_request_id: return
        conn = get_inventory_db_connection()
        if not conn: return

        try:
            items = conn.execute("""
                SELECT iri.id, i.item_code, i.item_name_ar, iri.quantity, 
                       u.name_ar as unit_name, iri.status, iri.notes, iri.required_date
                FROM issue_request_items iri
                JOIN items i ON iri.item_id = i.id
                LEFT JOIN units u ON iri.unit_id = u.id
                WHERE iri.request_id = ?
            """, (self.current_request_id,)).fetchall()

            self.items_table.setRowCount(len(items))
            for row, item in enumerate(items):
                self.items_table.setItem(row, 0, QTableWidgetItem(str(item["id"])))
                self.items_table.setItem(row, 1, QTableWidgetItem(item["item_code"]))
                self.items_table.setItem(row, 2, QTableWidgetItem(item["item_name_ar"]))
                self.items_table.setItem(row, 3, QTableWidgetItem(str(item["quantity"])))
                self.items_table.setItem(row, 4, QTableWidgetItem(item["unit_name"] or ""))
                self.items_table.setItem(row, 5, QTableWidgetItem(item["status"] or "pending"))
                self.items_table.setItem(row, 6, QTableWidgetItem(item["notes"] or ""))
                self.items_table.setItem(row, 7, QTableWidgetItem(item["required_date"] or ""))
                
                delete_btn = QPushButton("🗑️")
                delete_btn.setProperty("role", "danger")
                delete_btn.clicked.connect(lambda _, item_id=item["id"]: self.delete_request_item(item_id))
                self.items_table.setCellWidget(row, 8, delete_btn)
        finally:
            conn.close()

    def delete_request_item(self, item_id):
        """حذف صنف من الطلب"""
        reply = QMessageBox.question(self, "تأكيد الحذف", "هل أنت متأكد؟", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = get_inventory_db_connection()
            if not conn: return
            try:
                conn.execute("DELETE FROM issue_request_items WHERE id = ?", (item_id,))
                conn.commit()
                self.load_request_items()
            finally:
                conn.close()

    def show_request_details(self):
        """عرض تفاصيل الطلب"""
        if not self.current_request_id:
            QMessageBox.warning(self, "تحذير", "⚠️ الرجاء اختيار طلب أولاً")
            return
        self.tabs.setCurrentIndex(2)
        self.load_request_details()

    def load_request_details(self):
        """تحميل وعرض تفاصيل الطلب"""
        if not self.current_request_id: return
        conn = get_inventory_db_connection()
        if not conn: return

        try:
            request = conn.execute("""
                SELECT ir.*, d.name_ar as department_name, w.name_ar as warehouse_name
                FROM issue_requests ir
                LEFT JOIN departments d ON ir.department_id = d.id
                LEFT JOIN warehouses w ON ir.store_id = w.id
                WHERE ir.id = ?
            """, (self.current_request_id,)).fetchone()

            if request:
                self.details_request_label.setText(f"تفاصيل الطلب: {request['request_number']}")
                self.details_number.setText(request['request_number'])
                self.details_date.setText(request['request_date'])
                self.details_department.setText(request['department_name'] or "غير محدد")
                self.details_warehouse.setText(request['warehouse_name'] or "غير محدد")
                self.details_status.setText(request['status'])
                self.details_purpose.setText(request['purpose'] or "")

            items = conn.execute("""
                SELECT i.item_code, i.item_name_ar, iri.quantity, u.name_ar as unit_name, 
                       iri.status, iri.notes, iri.required_date
                FROM issue_request_items iri
                JOIN items i ON iri.item_id = i.id
                LEFT JOIN units u ON iri.unit_id = u.id
                WHERE iri.request_id = ?
            """, (self.current_request_id,)).fetchall()

            self.details_items_table.setRowCount(len(items))
            for row, item in enumerate(items):
                self.details_items_table.setItem(row, 0, QTableWidgetItem(item["item_code"]))
                self.details_items_table.setItem(row, 1, QTableWidgetItem(item["item_name_ar"]))
                self.details_items_table.setItem(row, 2, QTableWidgetItem(str(item["quantity"])))
                self.details_items_table.setItem(row, 3, QTableWidgetItem(item["unit_name"] or ""))
                self.details_items_table.setItem(row, 4, QTableWidgetItem(item["status"] or "pending"))
                self.details_items_table.setItem(row, 5, QTableWidgetItem(item["notes"] or ""))
                self.details_items_table.setItem(row, 6, QTableWidgetItem(item["required_date"] or ""))
        finally:
            conn.close()

    def load_departments(self):
        """تحميل الأقسام"""
        conn = get_inventory_db_connection()
        if not conn: return
        try:
            departments = conn.execute("SELECT id, name_ar FROM departments WHERE is_active = 1").fetchall()
            self.department_combo.clear()
            self.department_combo.addItem("اختر القسم", -1)
            for dept in departments:
                self.department_combo.addItem(dept["name_ar"], dept["id"])
        finally:
            conn.close()

    def load_warehouses(self):
        """تحميل المخازن"""
        conn = get_inventory_db_connection()
        if not conn: return
        try:
            warehouses = conn.execute("SELECT id, name_ar FROM warehouses WHERE is_active = 1").fetchall()
            self.warehouse_combo.clear()
            self.warehouse_combo.addItem("اختر المخزن", -1)
            for wh in warehouses:
                self.warehouse_combo.addItem(wh["name_ar"], wh["id"])
        finally:
            conn.close()

    def load_requests(self):
        """تحميل جميع طلبات الصرف"""
        conn = get_inventory_db_connection()
        if not conn: return
        try:
            requests = conn.execute("""
                SELECT ir.id, ir.request_number, ir.request_date, ir.status, 
                       d.name_ar as dept_name, ir.purpose, ir.notes
                FROM issue_requests ir
                LEFT JOIN departments d ON ir.department_id = d.id
                ORDER BY ir.created_at DESC
            """).fetchall()

            self.table.setRowCount(len(requests))
            for row, req in enumerate(requests):
                self.table.setItem(row, 0, QTableWidgetItem(str(req["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(req["request_number"]))
                self.table.setItem(row, 2, QTableWidgetItem(req["request_date"]))
                self.table.setItem(row, 3, QTableWidgetItem(req["status"]))
                self.table.setItem(row, 4, QTableWidgetItem(req["dept_name"] or "غير محدد"))
                self.table.setItem(row, 5, QTableWidgetItem(req["purpose"] or ""))
                self.table.setItem(row, 6, QTableWidgetItem(req["notes"] or ""))
        finally:
            conn.close()

    def add_issue_request(self):
        """إضافة طلب صرف جديد"""
        purpose = self.purpose_input.text().strip()
        dept_id = self.department_combo.currentData()
        warehouse_id = self.warehouse_combo.currentData()
        request_date = self.date_input.date().toString("yyyy-MM-dd")
        notes = self.notes_input.toPlainText()

        if dept_id == -1:
            QMessageBox.warning(self, "خطأ", "⚠️ الرجاء اختيار القسم")
            return
        if warehouse_id == -1:
            QMessageBox.warning(self, "خطأ", "⚠️ الرجاء اختيار المخزن")
            return
        if not purpose:
            QMessageBox.warning(self, "خطأ", "⚠️ الرجاء إدخال الغرض من الطلب")
            return

        conn = get_inventory_db_connection()
        if not conn: return

        try:
            cursor = conn.cursor()
            last_req = cursor.execute("SELECT request_number FROM issue_requests ORDER BY id DESC LIMIT 1").fetchone()
            if last_req:
                try:
                    num = int(last_req[0].split('-')[-1]) + 1
                    new_number = f"IR-{datetime.now().year}-{num:04d}"
                except:
                    new_number = f"IR-{datetime.now().year}-0001"
            else:
                new_number = f"IR-{datetime.now().year}-0001"

            cursor.execute("""
                INSERT INTO issue_requests 
                (request_number, request_date, requester_external_id, department_id, store_id, purpose, notes, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (new_number, request_date, str(self.user_id), dept_id, warehouse_id, purpose, notes, "pending", 
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            QMessageBox.information(self, "تم", f"✅ تم إنشاء طلب جديد برقم: {new_number}")
            self.purpose_input.clear()
            self.notes_input.clear()
            self.load_requests()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {e}")
        finally:
            conn.close()

    def delete_request(self):
        """حذف الطلب المحدد"""
        if not self.current_request_id:
            QMessageBox.warning(self, "تحذير", "⚠️ الرجاء اختيار طلب لحذفه")
            return

        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                   f"هل أنت متأكد من حذف الطلب رقم {self.current_request_number}؟", 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = get_inventory_db_connection()
            if not conn: return
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM issue_request_items WHERE request_id = ?", (self.current_request_id,))
                cursor.execute("DELETE FROM issue_requests WHERE id = ?", (self.current_request_id,))
                conn.commit()
                QMessageBox.information(self, "تم", "✅ تم حذف الطلب بنجاح")
                self.load_requests()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ: {e}")
            finally:
                conn.close()

    def approve_request(self):
        """اعتماد الطلب"""
        if not self.current_request_id:
            QMessageBox.warning(self, "تنبيه", "⚠️ الرجاء اختيار طلب أولاً")
            return

        reply = QMessageBox.question(self, "تأكيد الاعتماد", 
                                   f"هل تريد اعتماد الطلب رقم {self.current_request_number}؟", 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        conn = get_inventory_db_connection()
        if not conn: return
        try:
            conn.execute("""
                UPDATE issue_requests 
                SET status = ?, approved_by_external_id = ?, approved_at = ?
                WHERE id = ?
            """, ("approved", str(self.user_id), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.current_request_id))
            conn.commit()
            QMessageBox.information(self, "تم", "✅ تم اعتماد الطلب بنجاح")
            self.load_requests()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {e}")
        finally:
            conn.close()

# --- نقطة تشغيل التطبيق ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IssueRequest_UI()
    window.show()
    sys.exit(app.exec_())
# purchase_request_ui.py
import sys
import os
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHBoxLayout,
    QLineEdit, QMessageBox, QComboBox, QDateEdit,
    QHeaderView, QTabWidget, QGroupBox, QGridLayout,
    QDoubleSpinBox, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# --- إعداد المسارات (يبقى كما هو) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)
from database.db_connection import get_inventory_db_connection


class PurchaseRequest_UI(QWidget):
    def __init__(self, user_id=1, user_name="مدير النظام"):
        super().__init__()
        self.user_id = user_id
        self.user_name = user_name
        self.current_request_id = None
        self.current_request_number = None
        self.selected_item_id = None
        
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
                font-family: "Arial", sans-serif;
                font-size: 13px;
            }
            QLabel#title {
                font-size: 20px;
                font-weight: bold;
                color: #0D47A1;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #D0D0D0;
                border-radius: 6px;
                margin-top: 10px;
                padding: 8px;
            }
            QPushButton {
                background-color: #1976D2;
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1565C0; /* لون أغمق عند المرور */
            }
            QPushButton:disabled {
                background-color: #BDBDBD; /* لون للزر المعطل */
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
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 6px;
                border: 1px solid #E0E0E0;
            }
            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QTextEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)

    def initUI(self):
        """تهيئة واجهة المستخدم"""
        self.setWindowTitle("إدارة طلبات الشراء")
        self.setGeometry(200, 200, 1400, 900)
        self.apply_styles()

        self.tabs = QTabWidget()
        self.requests_tab = QWidget()
        self.items_tab = QWidget()
        self.details_tab = QWidget()

        self.setup_requests_tab()
        self.setup_items_tab()
        self.setup_details_tab()

        self.tabs.addTab(self.requests_tab, "عرض طلبات الشراء")
        self.tabs.addTab(self.items_tab, "إدارة أصناف الطلب")
        self.tabs.addTab(self.details_tab, "تفاصيل الطلب")

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)
        
        self.load_requests()

    def setup_requests_tab(self):
        """إعداد تبويب عرض الطلبات"""
        layout = QVBoxLayout(self.requests_tab)
        title = QLabel("📑 طلبات الشراء")
        title.setObjectName("title")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "رقم الطلب", "التاريخ", "الحالة", "القسم", "ملاحظات"])
        self.table.setColumnHidden(0, True) # إخفاء عمود ID
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self.on_request_selected)
        layout.addWidget(self.table)

        form_group = QGroupBox("إضافة طلب جديد")
        form_layout = QHBoxLayout(form_group)
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("ملاحظات الطلب")
        form_layout.addWidget(self.notes_input)
        self.department_combo = QComboBox()
        self.load_departments()
        form_layout.addWidget(self.department_combo)
        self.date_input = QDateEdit(datetime.now())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        form_layout.addWidget(self.date_input)
        add_btn = QPushButton("➕ إضافة طلب")
        add_btn.setProperty("role", "success")
        add_btn.clicked.connect(self.add_purchase_request)
        form_layout.addWidget(add_btn)
        layout.addWidget(form_group)

        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setProperty("role", "neutral")
        refresh_btn.clicked.connect(self.load_requests)
        button_layout.addWidget(refresh_btn)
        self.view_details_btn = QPushButton("👁️ عرض التفاصيل")
        self.view_details_btn.clicked.connect(self.show_request_details)
        button_layout.addWidget(self.view_details_btn)
        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.setProperty("role", "danger")
        self.delete_btn.clicked.connect(self.delete_request)
        button_layout.addWidget(self.delete_btn)
        self.manage_items_btn = QPushButton("📦 إدارة الأصناف")
        self.manage_items_btn.clicked.connect(self.switch_to_items_tab)
        button_layout.addWidget(self.manage_items_btn)
        self.approve_btn = QPushButton("✅ اعتماد")
        self.approve_btn.setProperty("role", "success")
        self.approve_btn.clicked.connect(self.approve_request)
        button_layout.addWidget(self.approve_btn)
        layout.addLayout(button_layout)

    def setup_items_tab(self):
        """إعداد تبويب إدارة الأصناف"""
        layout = QVBoxLayout(self.items_tab)
        self.selected_request_label = QLabel("لم يتم تحديد أي طلب")
        self.selected_request_label.setStyleSheet("font-size: 14px; color: blue; margin: 5px;")
        layout.addWidget(self.selected_request_label)

        # ... (باقي إعدادات تبويب الأصناف تبقى كما هي) ...
        search_group = QGroupBox("بحث الأصناف")
        search_layout = QHBoxLayout(search_group)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث بكود الصنف أو اسم الصنف...")
        self.search_input.textChanged.connect(self.search_items)
        search_layout.addWidget(self.search_input)
        layout.addWidget(search_group)

        self.search_table = QTableWidget()
        self.search_table.setColumnCount(6)
        self.search_table.setHorizontalHeaderLabels(["ID", "كود الصنف", "اسم الصنف", "المجموعة", "الوحدة", "الإجراء"])
        self.search_table.setColumnHidden(0, True)
        layout.addWidget(self.search_table)

        add_group = QGroupBox("إضافة صنف للطلب")
        add_layout = QGridLayout(add_group)
        add_layout.addWidget(QLabel("كود الصنف:"), 0, 0)
        self.selected_item_code = QLineEdit()
        self.selected_item_code.setReadOnly(True)
        add_layout.addWidget(self.selected_item_code, 0, 1)
        add_layout.addWidget(QLabel("اسم الصنف:"), 0, 2)
        self.selected_item_name = QLineEdit()
        self.selected_item_name.setReadOnly(True)
        add_layout.addWidget(self.selected_item_name, 0, 3)
        add_layout.addWidget(QLabel("الكمية:"), 1, 0)
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.1, 99999)
        add_layout.addWidget(self.quantity_input, 1, 1)
        add_item_btn = QPushButton("➕ إضافة للطلب")
        add_item_btn.setProperty("role", "success")
        add_item_btn.clicked.connect(self.add_item_to_request)
        add_layout.addWidget(add_item_btn, 1, 2, 1, 2)
        layout.addWidget(add_group)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels(["ID", "كود الصنف", "اسم الصنف", "الكمية", "الوحدة", "السعر", "الإجراءات"])
        self.items_table.setColumnHidden(0, True)
        layout.addWidget(self.items_table)

        back_btn = QPushButton("↩ العودة للطلبات")
        back_btn.clicked.connect(self.switch_to_requests_tab)
        layout.addWidget(back_btn)

    def setup_details_tab(self):
        """إعداد تبويب تفاصيل الطلب"""
        layout = QVBoxLayout(self.details_tab)
        self.details_request_label = QLabel("لم يتم تحديد أي طلب")
        layout.addWidget(self.details_request_label)
        
        info_group = QGroupBox("معلومات الطلب")
        info_layout = QGridLayout(info_group)
        info_layout.addWidget(QLabel("رقم الطلب:"), 0, 0)
        self.details_number = QLineEdit()
        self.details_number.setReadOnly(True)
        info_layout.addWidget(self.details_number, 0, 1)
        info_layout.addWidget(QLabel("التاريخ:"), 0, 2)
        self.details_date = QLineEdit()
        self.details_date.setReadOnly(True)
        info_layout.addWidget(self.details_date, 0, 3)
        info_layout.addWidget(QLabel("القسم:"), 1, 0)
        self.details_department = QLineEdit()
        self.details_department.setReadOnly(True)
        info_layout.addWidget(self.details_department, 1, 1)
        info_layout.addWidget(QLabel("الحالة:"), 1, 2)
        self.details_status = QLineEdit()
        self.details_status.setReadOnly(True)
        info_layout.addWidget(self.details_status, 1, 3)
        layout.addWidget(info_group)

        self.details_items_table = QTableWidget()
        self.details_items_table.setColumnCount(6)
        self.details_items_table.setHorizontalHeaderLabels(["كود الصنف", "اسم الصنف", "المجموعة", "الكمية", "الوحدة", "السعر"])
        layout.addWidget(self.details_items_table)

        back_btn = QPushButton("↩ العودة للطلبات")
        back_btn.clicked.connect(self.switch_to_requests_tab)
        layout.addWidget(back_btn)

    def on_request_selected(self):
        """عند اختيار طلب من الجدول، يتم تفعيل الأزرار وتحديث المتغيرات."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.current_request_id = None
            self.current_request_number = None
            self.view_details_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.manage_items_btn.setEnabled(False)
            self.approve_btn.setEnabled(False)
            return

        current_row = selected_items[0].row()
        self.current_request_id = self.table.item(current_row, 0).text()
        self.current_request_number = self.table.item(current_row, 1).text()
        
        self.selected_request_label.setText(f"الطلب المحدد: {self.current_request_number} (ID: {self.current_request_id})")
        
        self.view_details_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.manage_items_btn.setEnabled(True)
        self.approve_btn.setEnabled(True)

    def switch_to_items_tab(self):
        """الانتقال إلى تبويب الأصناف بعد التأكد من اختيار طلب."""
        if not self.current_request_id:
            QMessageBox.warning(self, "تحذير", "⚠️ الرجاء اختيار طلب أولاً")
            return
        self.tabs.setCurrentIndex(1)
        self.search_items()
        self.load_request_items()

    def switch_to_requests_tab(self):
        self.tabs.setCurrentIndex(0)

    def search_items(self):
        """بحث الأصناف وعرضها في جدول البحث."""
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
        """اختيار صنف من جدول البحث وتعبئة بياناته."""
        self.selected_item_id = int(self.search_table.item(row, 0).text())
        self.selected_item_code.setText(self.search_table.item(row, 1).text())
        self.selected_item_name.setText(self.search_table.item(row, 2).text())

    def add_item_to_request(self):
        """إضافة الصنف المختار إلى طلب الشراء الحالي."""
        if not self.current_request_id or not self.selected_item_id:
            QMessageBox.warning(self, "تحذير", "⚠️ يرجى اختيار طلب وصنف أولاً")
            return
        
        quantity = self.quantity_input.value()
        if quantity <= 0:
            QMessageBox.warning(self, "تحذير", "⚠️ الكمية يجب أن تكون أكبر من صفر")
            return

        conn = get_inventory_db_connection()
        if not conn: return

        try:
            # افتراض أن سعر الشراء هو 0 مبدئياً ويمكن تعديله لاحقاً
            unit_price = 0
            total_price = quantity * unit_price

            conn.execute("""
                INSERT INTO purchase_request_items (request_id, item_id, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
            """, (self.current_request_id, self.selected_item_id, quantity, unit_price, total_price))
            conn.commit()
            QMessageBox.information(self, "تم", "✅ تم إضافة الصنف إلى الطلب")
            self.load_request_items()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "مكرر", "هذا الصنف موجود بالفعل في الطلب.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {e}")
        finally:
            conn.close()

    def load_request_items(self):
        """تحميل أصناف الطلب المحدد وعرضها."""
        if not self.current_request_id: return
        conn = get_inventory_db_connection()
        if not conn: return

        try:
            items = conn.execute("""
                SELECT pri.id, i.item_code, i.item_name_ar, pri.quantity, u.name_ar as unit_name, pri.unit_price
                FROM purchase_request_items pri
                JOIN items i ON pri.item_id = i.id
                LEFT JOIN units u ON i.base_unit_id = u.id
                WHERE pri.request_id = ?
            """, (self.current_request_id,)).fetchall()

            self.items_table.setRowCount(len(items))
            for row, item in enumerate(items):
                self.items_table.setItem(row, 0, QTableWidgetItem(str(item["id"])))
                self.items_table.setItem(row, 1, QTableWidgetItem(item["item_code"]))
                self.items_table.setItem(row, 2, QTableWidgetItem(item["item_name_ar"]))
                self.items_table.setItem(row, 3, QTableWidgetItem(str(item["quantity"])))
                self.items_table.setItem(row, 4, QTableWidgetItem(item["unit_name"] or ""))
                self.items_table.setItem(row, 5, QTableWidgetItem(f"{item['unit_price'] or 0:.2f}"))
                
                delete_btn = QPushButton("🗑️")
                delete_btn.setProperty("role", "danger")
                delete_btn.clicked.connect(lambda _, item_id=item["id"]: self.delete_request_item(item_id))
                self.items_table.setCellWidget(row, 6, delete_btn)
        finally:
            conn.close()

    def delete_request_item(self, item_id):
        """حذف صنف من الطلب."""
        reply = QMessageBox.question(self, "تأكيد الحذف", "هل أنت متأكد؟", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = get_inventory_db_connection()
            if not conn: return
            try:
                conn.execute("DELETE FROM purchase_request_items WHERE id = ?", (item_id,))
                conn.commit()
                self.load_request_items()
            finally:
                conn.close()

    def show_request_details(self):
        """عرض تفاصيل الطلب في التبويب المخصص."""
        if not self.current_request_id:
            QMessageBox.warning(self, "تحذير", "⚠️ الرجاء اختيار طلب أولاً")
            return
        self.tabs.setCurrentIndex(2)
        self.load_request_details()

    def load_request_details(self):
        """تحميل وعرض تفاصيل الطلب المحدد."""
        if not self.current_request_id: return
        conn = get_inventory_db_connection()
        if not conn: return

        try:
            request = conn.execute("""
                SELECT pr.*, d.name_ar as department_name
                FROM purchase_requests pr
                LEFT JOIN departments d ON pr.department_id = d.id
                WHERE pr.id = ?
            """, (self.current_request_id,)).fetchone()

            if request:
                self.details_request_label.setText(f"تفاصيل الطلب: {request['request_number']}")
                self.details_number.setText(request['request_number'])
                self.details_date.setText(request['request_date'])
                self.details_department.setText(request['department_name'] or "غير محدد")
                self.details_status.setText(request['status'])

            items = conn.execute("""
                SELECT i.item_code, i.item_name_ar, ig.name_ar as group_name, pri.quantity, u.name_ar as unit_name, pri.unit_price
                FROM purchase_request_items pri
                JOIN items i ON pri.item_id = i.id
                LEFT JOIN item_groups ig ON i.item_group_id = ig.id
                LEFT JOIN units u ON i.base_unit_id = u.id
                WHERE pri.request_id = ?
            """, (self.current_request_id,)).fetchall()

            self.details_items_table.setRowCount(len(items))
            for row, item in enumerate(items):
                self.details_items_table.setItem(row, 0, QTableWidgetItem(item["item_code"]))
                self.details_items_table.setItem(row, 1, QTableWidgetItem(item["item_name_ar"]))
                self.details_items_table.setItem(row, 2, QTableWidgetItem(item["group_name"] or ""))
                self.details_items_table.setItem(row, 3, QTableWidgetItem(str(item["quantity"])))
                self.details_items_table.setItem(row, 4, QTableWidgetItem(item["unit_name"] or ""))
                self.details_items_table.setItem(row, 5, QTableWidgetItem(f"{item['unit_price'] or 0:.2f}"))
        finally:
            conn.close()

    def load_departments(self):
        """تحميل الأقسام من قاعدة البيانات."""
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

    def load_requests(self):
        """تحميل جميع طلبات الشراء وعرضها."""
        conn = get_inventory_db_connection()
        if not conn: return
        try:
            requests = conn.execute("""
                SELECT pr.id, pr.request_number, pr.request_date, pr.status, d.name_ar as dept_name, pr.notes
                FROM purchase_requests pr
                LEFT JOIN departments d ON pr.department_id = d.id
                ORDER BY pr.created_at DESC
            """).fetchall()

            self.table.setRowCount(len(requests))
            for row, req in enumerate(requests):
                self.table.setItem(row, 0, QTableWidgetItem(str(req["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(req["request_number"]))
                self.table.setItem(row, 2, QTableWidgetItem(req["request_date"]))
                self.table.setItem(row, 3, QTableWidgetItem(req["status"]))
                self.table.setItem(row, 4, QTableWidgetItem(req["dept_name"] or "غير محدد"))
                self.table.setItem(row, 5, QTableWidgetItem(req["notes"] or ""))
        finally:
            conn.close()

    def add_purchase_request(self):
        """إضافة طلب شراء جديد."""
        notes = self.notes_input.text()
        dept_id = self.department_combo.currentData()
        request_date = self.date_input.date().toString("yyyy-MM-dd")

        if dept_id == -1:
            QMessageBox.warning(self, "خطأ", "⚠️ الرجاء اختيار القسم")
            return

        conn = get_inventory_db_connection()
        if not conn: return

        try:
            cursor = conn.cursor()
            last_req = cursor.execute("SELECT request_number FROM purchase_requests ORDER BY id DESC LIMIT 1").fetchone()
            if last_req:
                try:
                    num = int(last_req[0].split('-')[-1]) + 1
                    new_number = f"REQ-{datetime.now().year}-{num:04d}"
                except:
                    new_number = f"REQ-{datetime.now().year}-0001"
            else:
                new_number = f"REQ-{datetime.now().year}-0001"

            cursor.execute("""
                INSERT INTO purchase_requests (request_number, request_date, department_id, notes, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (new_number, request_date, dept_id, notes, "pending", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            QMessageBox.information(self, "تم", f"✅ تم إنشاء طلب جديد برقم: {new_number}")
            self.load_requests()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {e}")
        finally:
            conn.close()

    def delete_request(self):
        """حذف الطلب المحدد وجميع الأصناف المرتبطة به."""
        if not self.current_request_id:
            QMessageBox.warning(self, "تحذير", "⚠️ الرجاء اختيار طلب لحذفه")
            return

        reply = QMessageBox.question(self, "تأكيد الحذف", f"هل أنت متأكد من حذف الطلب رقم {self.current_request_number}؟", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = get_inventory_db_connection()
            if not conn: return
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM purchase_request_items WHERE request_id = ?", (self.current_request_id,))
                cursor.execute("DELETE FROM purchase_requests WHERE id = ?", (self.current_request_id,))
                conn.commit()
                QMessageBox.information(self, "تم", "✅ تم حذف الطلب بنجاح")
                self.load_requests()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ: {e}")
            finally:
                conn.close()

    def approve_request(self):
        """اعتماد الطلب وتغيير حالته إلى 'approved'."""
        if not self.current_request_id:
            QMessageBox.warning(self, "تنبيه", "⚠️ الرجاء اختيار طلب أولاً")
            return

        reply = QMessageBox.question(self, "تأكيد الاعتماد", f"هل تريد اعتماد الطلب رقم {self.current_request_number}؟", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        conn = get_inventory_db_connection()
        if not conn: return
        try:
            conn.execute("UPDATE purchase_requests SET status = ? WHERE id = ?", ("approved", self.current_request_id))
            conn.commit()
            QMessageBox.information(self, "تم", "✅ تم اعتماد الطلب بنجاح")
            self.load_requests()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {e}")
        finally:
            conn.close()

# --- نقطة تشغيل التطبيق (للاختبار) ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PurchaseRequest_UI()
    window.show()
    sys.exit(app.exec_())

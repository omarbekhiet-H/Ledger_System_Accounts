# issue_approval_ui.py
# واجهة اعتماد الطلبات — مُعدلة للتوافق الكامل مع schema (تسجيل موافقات + إنشاء إذن مطابق للأعمدة)
import os
import sys
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QLineEdit, QComboBox, QLabel, QMessageBox, QHeaderView,
                             QTextEdit, QGroupBox, QSplitter, QFormLayout, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# إعداد المسارات
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)
from database.db_connection import get_inventory_db_connection


class IssueApprovalUI(QWidget):
    def __init__(self):
        super().__init__()
        self.current_request_id = None
        self.initUI()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { 
                font-family: "Arial", sans-serif; 
                font-size: 13px; 
                background-color: #f5f5f5;
            }
            QGroupBox { 
                font-weight: bold; 
                border: 2px solid #D0D0D0; 
                border-radius: 8px; 
                margin-top: 10px; 
                padding: 10px; 
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: white;
            }
            QPushButton { 
                padding: 10px 15px; 
                border-radius: 6px; 
                border: none; 
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton[role="success"] { background-color: #28a745; color: white; }
            QPushButton[role="danger"] { background-color: #dc3545; color: white; }
            QPushButton[role="warning"] { background-color: #ffc107; color: black; }
            QPushButton[role="neutral"] { background-color: #6c757d; color: white; }
            QPushButton:hover { opacity: 0.9; }
            QPushButton:disabled { background-color: #cccccc; color: #666666; }
            QLineEdit, QComboBox, QTextEdit { 
                padding: 8px; 
                border: 2px solid #ccc; 
                border-radius: 4px; 
                background-color: white;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus { 
                border-color: #007bff; 
            }
            QTableWidget { 
                gridline-color: #E0E0E0; 
                selection-background-color: #BBDEFB;
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 10px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
            QLabel {
                padding: 5px;
                font-weight: bold;
                color: #333;
            }
        """)

    def execute_query(self, query, params=(), fetch="all"):
        """تنفيذ استعلام SQL مع معالجة الأخطاء"""
        conn = get_inventory_db_connection()
        if not conn:
            print("فشل في الاتصال بقاعدة البيانات")
            return None
        
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if fetch.lower() == "all":
                result = [dict(row) for row in cursor.fetchall()]
            elif fetch.lower() == "one":
                row = cursor.fetchone()
                result = dict(row) if row else None
            else:
                result = None
            
            conn.commit()
            return result
        except Exception as e:
            print(f"خطأ في قاعدة البيانات: {e}")
            print(f"الاستعلام: {query}")
            print(f"المعاملات: {params}")
            return None
        finally:
            conn.close()

    def initUI(self):
        self.setLayoutDirection(Qt.RightToLeft)
        self.apply_styles()

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # مجموعة التصفية
        filter_group = QGroupBox("🔍 تصفية الطلبات")
        filter_layout = QHBoxLayout(filter_group)

        filter_layout.addWidget(QLabel("بحث:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("ابحث برقم الطلب، الغرض، القسم...")
        self.search_edit.textChanged.connect(self.load_requests)
        filter_layout.addWidget(self.search_edit)

        filter_layout.addWidget(QLabel("الحالة:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["الكل", "pending", "under_review", "approved", "rejected"])
        self.status_filter.currentTextChanged.connect(self.load_requests)
        filter_layout.addWidget(self.status_filter)

        filter_layout.addWidget(QLabel("القسم:"))
        self.department_filter = QComboBox()
        self.department_filter.currentTextChanged.connect(self.load_requests)
        filter_layout.addWidget(self.department_filter)

        refresh_btn = QPushButton("🔄 تحديث البيانات")
        refresh_btn.setToolTip("تحديث قائمة الطلبات")
        refresh_btn.setProperty("role", "neutral")
        refresh_btn.clicked.connect(self.load_requests)
        filter_layout.addWidget(refresh_btn)

        main_layout.addWidget(filter_group)

        # Splitter للقسمين
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # القسم الأيمن: قائمة الطلبات
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        
        list_title = QLabel("📋 قائمة طلبات الصرف المعلقة")
        list_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0D47A1; margin: 10px;")
        list_title.setAlignment(Qt.AlignCenter)
        list_layout.addWidget(list_title)

        self.requests_table = QTableWidget()
        self.requests_table.setColumnCount(7)
        self.requests_table.setHorizontalHeaderLabels(["ID", "رقم الطلب", "التاريخ", "القسم", "الغرض", "مقدم الطلب", "الحالة"])
        self.requests_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.requests_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.requests_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.requests_table.setColumnHidden(0, True)
        self.requests_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        list_layout.addWidget(self.requests_table)

        # القسم الأيسر: التفاصيل
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)

        # مجموعة تفاصيل الطلب
        details_group = QGroupBox("📄 تفاصيل الطلب المحدد")
        details_form = QFormLayout(details_group)
        details_form.setLabelAlignment(Qt.AlignRight)
        details_form.setSpacing(10)

        self.lbl_request_number = QLabel("---")
        self.lbl_request_date = QLabel("---")
        self.lbl_department = QLabel("---")
        self.lbl_requester = QLabel("---")
        self.lbl_purpose = QLabel("---")
        self.lbl_priority = QLabel("---")
        self.lbl_status = QLabel("---")

        # تنسيق التسميات
        for label in [self.lbl_request_number, self.lbl_request_date, self.lbl_department, 
                     self.lbl_requester, self.lbl_purpose, self.lbl_priority, self.lbl_status]:
            label.setStyleSheet("background-color: #f8f9fa; padding: 8px; border-radius: 4px; border: 1px solid #dee2e6;")
            label.setMinimumHeight(30)

        details_form.addRow("🔢 رقم الطلب:", self.lbl_request_number)
        details_form.addRow("📅 تاريخ الطلب:", self.lbl_request_date)
        details_form.addRow("🏢 القسم:", self.lbl_department)
        details_form.addRow("👤 مقدم الطلب:", self.lbl_requester)
        details_form.addRow("🎯 الغرض من الطلب:", self.lbl_purpose)
        details_form.addRow("⭐ الأولوية:", self.lbl_priority)
        details_form.addRow("📊 الحالة:", self.lbl_status)

        # مجموعة أصناف الطلب
        items_group = QGroupBox("📦 أصناف الطلب")
        items_layout = QVBoxLayout(items_group)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(8)
        self.items_table.setHorizontalHeaderLabels(["ID", "الصنف", "الكمية المطلوبة", "الكمية المعتمدة", "الوحدة", "التكلفة المقدرة", "الحالة", "ملاحظات"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setColumnHidden(0, True)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.items_table.setAlternatingRowColors(True)
        
        items_layout.addWidget(self.items_table)

        # مجموعة إجراءات الاعتماد
        approval_group = QGroupBox("⚡ إجراءات الاعتماد")
        approval_layout = QVBoxLayout(approval_group)
        
        approval_layout.addWidget(QLabel("💬 ملاحظات الاعتماد:"))
        self.comments_edit = QTextEdit()
        self.comments_edit.setPlaceholderText("أضف ملاحظاتك حول الطلب هنا...")
        self.comments_edit.setMaximumHeight(100)
        approval_layout.addWidget(self.comments_edit)

        buttons_layout = QHBoxLayout()
        self.approve_btn = QPushButton("✅ موافقة")
        self.approve_btn.setProperty("role", "success")
        self.approve_btn.clicked.connect(self.approve_request)

        self.reject_btn = QPushButton("❌ رفض")
        self.reject_btn.setProperty("role", "danger")
        self.reject_btn.clicked.connect(self.reject_request)

        self.return_btn = QPushButton("🔄 إرجاع")
        self.return_btn.setProperty("role", "warning")
        self.return_btn.clicked.connect(self.return_request)

        buttons_layout.addWidget(self.approve_btn)
        buttons_layout.addWidget(self.reject_btn)
        buttons_layout.addWidget(self.return_btn)

        approval_layout.addLayout(buttons_layout)

        # إضافة المجموعات إلى التخطيط
        details_layout.addWidget(details_group)
        details_layout.addWidget(items_group)
        details_layout.addWidget(approval_group)

        # إضافة الأقسام إلى الـ Splitter
        splitter.addWidget(details_widget)
        splitter.addWidget(list_widget)
        splitter.setSizes([600, 400])

        main_layout.addWidget(splitter)

        # تحميل البيانات الأولية
        self.load_departments()
        self.load_requests()
        self.toggle_approval_buttons(False)

    def load_departments(self):
        """تحميل الأقسام من قاعدة البيانات"""
        departments = self.execute_query("SELECT id, name_ar FROM departments WHERE is_active = 1")
        self.department_filter.clear()
        self.department_filter.addItem("الكل")
        
        if departments:
            for dept in departments:
                self.department_filter.addItem(dept['name_ar'], dept['id'])

    def load_requests(self):
        """تحميل طلبات الصرف مع التصفية"""
        self.requests_table.setRowCount(0)

        # بناء الاستعلام الأساسي
        query = """
        SELECT 
            ir.id, 
            ir.request_number, 
            ir.request_date, 
            d.name_ar as department, 
            ir.purpose,
            ir.requester_external_id, 
            ir.status 
        FROM issue_requests ir
        LEFT JOIN departments d ON ir.department_id = d.id
        WHERE 1=1
        """

        params = []

        # تطبيق الفلاتر
        if self.status_filter.currentText() != "الكل":
            query += " AND ir.status = ?"
            params.append(self.status_filter.currentText())

        if self.department_filter.currentText() != "الكل" and self.department_filter.currentData():
            query += " AND d.id = ?"
            params.append(self.department_filter.currentData())

        if self.search_edit.text().strip():
            search_text = f"%{self.search_edit.text().strip()}%"
            query += " AND (ir.request_number LIKE ? OR ir.purpose LIKE ? OR d.name_ar LIKE ?)"
            params.extend([search_text, search_text, search_text])

        query += " ORDER BY ir.request_date DESC, ir.id DESC"

        requests = self.execute_query(query, tuple(params))
        
        if requests is None:
            QMessageBox.warning(self, "تحذير", "حدث خطأ في تحميل البيانات")
            return

        self.requests_table.setRowCount(len(requests))
        
        for row, req in enumerate(requests):
            for col, key in enumerate(['id', 'request_number', 'request_date', 'department', 'purpose', 'requester_external_id', 'status']):
                value = req.get(key, '')
                item = QTableWidgetItem(str(value) if value is not None else '')
                item.setTextAlignment(Qt.AlignCenter)
                
                # تلوين الحالة
                if key == 'status':
                    status = str(value).lower()
                    if status == 'pending':
                        item.setBackground(Qt.yellow)
                    elif status == 'under_review':
                        item.setBackground(Qt.blue)
                        item.setForeground(Qt.white)
                    elif status == 'approved':
                        item.setBackground(Qt.green)
                        item.setForeground(Qt.white)
                    elif status == 'rejected':
                        item.setBackground(Qt.red)
                        item.setForeground(Qt.white)
                
                self.requests_table.setItem(row, col, item)

    def on_selection_changed(self, selected, deselected):
        """عند اختيار طلب من الجدول"""
        if not selected.indexes():
            self.clear_details()
            self.toggle_approval_buttons(False)
            return

        row = selected.indexes()[0].row()
        request_id_item = self.requests_table.item(row, 0)  # العمود المخفي ID
        
        if request_id_item:
            self.current_request_id = int(request_id_item.text())
            self.show_full_details(self.current_request_id)

    def show_full_details(self, request_id):
        """عرض التفاصيل الكاملة للطلب المحدد"""
        if not request_id:
            return

        # استعلام محسن للحصول على بيانات الطلب
        query = """
        SELECT 
            ir.id,
            ir.request_number,
            ir.request_date,
            d.name_ar as department_name,
            ir.requester_external_id,
            ir.purpose,
            ir.priority,
            ir.status,
            ir.notes,
            w.name_ar as warehouse_name,
            ir.created_at
        FROM issue_requests ir
        LEFT JOIN departments d ON ir.department_id = d.id
        LEFT JOIN warehouses w ON ir.store_id = w.id
        WHERE ir.id = ?
        """

        req = self.execute_query(query, (request_id,), fetch="one")
        
        if not req:
            QMessageBox.warning(self, "تحذير", "لم يتم العثور على بيانات الطلب")
            return

        # تعبئة البيانات في الواجهة
        self.lbl_request_number.setText(req.get('request_number', '---'))
        self.lbl_request_date.setText(req.get('request_date', '---'))
        self.lbl_department.setText(req.get('department_name', 'غير محدد'))
        self.lbl_requester.setText(req.get('requester_external_id', 'غير محدد'))
        self.lbl_purpose.setText(req.get('purpose', 'غير محدد'))
        self.lbl_priority.setText(req.get('priority', 'عادية'))
        self.lbl_status.setText(req.get('status', 'غير معروف'))

        # تلوين حالة الطلب
        status = req.get('status', '').lower()
        color_map = {
            'pending': '#fff3cd',
            'under_review': '#cce7ff',
            'approved': '#d4edda',
            'rejected': '#f8d7da'
        }
        self.lbl_status.setStyleSheet(f"background-color: {color_map.get(status, '#f8f9fa')}; padding: 8px; border-radius: 4px; border: 1px solid #dee2e6;")

        # تحميل أصناف الطلب
        self.load_request_items(request_id)
        self.toggle_approval_buttons(True)

    def load_request_items(self, request_id):
        """تحميل أصناف الطلب المحدد"""
        self.items_table.setRowCount(0)
        
        query = """
        SELECT 
            iri.id,
            i.item_name_ar,
            iri.quantity,
            iri.approved_quantity,
            u.name_ar as unit_name,
            iri.estimated_cost,
            iri.status,
            iri.notes
        FROM issue_request_items iri
        LEFT JOIN items i ON iri.item_id = i.id
        LEFT JOIN units u ON iri.unit_id = u.id
        WHERE iri.request_id = ?
        ORDER BY iri.id
        """

        items = self.execute_query(query, (request_id,))
        
        if not items:
            # إذا لم توجد أصناف
            self.items_table.setRowCount(1)
            self.items_table.setColumnCount(1)
            no_data_item = QTableWidgetItem("لا توجد أصناف مسجلة لهذا الطلب")
            no_data_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(0, 0, no_data_item)
            return

        # إعادة تعيين الأعمدة إذا كانت مخفية سابقاً
        self.items_table.setColumnCount(8)
        self.items_table.setHorizontalHeaderLabels([
            "ID", "الصنف", "الكمية المطلوبة", "الكمية المعتمدة", 
            "الوحدة", "التكلفة المقدرة", "الحالة", "ملاحظات"
        ])
        self.items_table.setColumnHidden(0, True)
        
        self.items_table.setRowCount(len(items))
        
        for row, item_data in enumerate(items):
            # تعبئة البيانات في الجدول
            columns_data = [
                item_data.get('id', ''),
                item_data.get('item_name_ar', 'غير معروف'),
                str(item_data.get('quantity') or 0),
                str(item_data.get('approved_quantity') or 0),   # 👈 لو فاضي يطلع 0
                item_data.get('unit_name', 'غير محدد'),
                str(item_data.get('estimated_cost') or 0),
                item_data.get('status') or 'pending',           # 👈 افتراض pending لو مفيش
                item_data.get('notes', '')
            ]

            
            for col, data in enumerate(columns_data):
                item = QTableWidgetItem(str(data))
                item.setTextAlignment(Qt.AlignCenter)
                self.items_table.setItem(row, col, item)
                
                # تلوين حالة الصنف
                if col == 6:  # عمود الحالة
                    status = str(data).lower()
                    if status == 'pending':
                        item.setBackground(Qt.yellow)
                    elif status == 'approved':
                        item.setBackground(Qt.green)
                        item.setForeground(Qt.white)
                    elif status == 'rejected':
                        item.setBackground(Qt.red)
                        item.setForeground(Qt.white)

    def approve_request(self):
        """اعتماد الطلب وإنشاء إذن صرف وأصنافه"""
        if not self.current_request_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار طلب أولاً")
            return

        conn = get_inventory_db_connection()
        if not conn:
            return
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()

            # 1️⃣ تحديث حالة الطلب
            cursor.execute("""
                UPDATE issue_requests
                SET status = 'approved', updated_at = ?
                WHERE id = ?
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.current_request_id))

            # جلب بيانات الطلب (لاستخراج القسم والمخزن)
            request = cursor.execute("""
                SELECT id, request_number, department_id, store_id
                FROM issue_requests
                WHERE id = ?
            """, (self.current_request_id,)).fetchone()

            # 2️⃣ إنشاء إذن صرف جديد مربوط بالطلب
            cursor.execute("""
                INSERT INTO issue_permits
                (permit_number, permit_date, warehouse_id, department_id, request_id, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'approved', ?)
            """, (
                f"IP-{datetime.now().year}-{self.current_request_id}",
                datetime.now().strftime("%Y-%m-%d"),
                request['store_id'],
                request['department_id'],
                self.current_request_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            permit_id = cursor.lastrowid

            # 3️⃣ نسخ أصناف الطلب إلى أصناف الإذن
            cursor.execute("""
                INSERT INTO issue_permit_items
                (permit_id, item_id, request_item_id, requested_quantity, issued_quantity, unit_id, unit_cost, status, created_at)
                SELECT ?, iri.item_id, iri.id, iri.quantity, 0, iri.unit_id, 0, 'pending', ?
                FROM issue_request_items iri
                WHERE iri.request_id = ?
            """, (permit_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.current_request_id))

            conn.commit()

            QMessageBox.information(self, "نجاح", "تم اعتماد الطلب وإنشاء إذن الصرف بنجاح")
            self.load_requests()
            self.clear_details()

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الاعتماد: {str(e)}")
        finally:
            conn.close()

    def reject_request(self):
        """رفض الطلب وتحديث حالة الإذن المرتبط إن وجد"""
        if not self.current_request_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار طلب أولاً")
            return

        conn = get_inventory_db_connection()
        if not conn:
            return
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()

            # 1️⃣ تحديث حالة الطلب
            cursor.execute("""
                UPDATE issue_requests
                SET status = 'rejected', updated_at = ?
                WHERE id = ?
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.current_request_id))

            # 2️⃣ إذا كان فيه إذن مرتبط بالطلب ده، نخليه مرفوض/ملغي
            cursor.execute("""
                UPDATE issue_permits
                SET status = 'cancelled', updated_at = ?
                WHERE request_id = ?
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.current_request_id))

            conn.commit()

            QMessageBox.information(self, "نجاح", "تم رفض الطلب وإلغاء الإذن المرتبط به (إن وجد).")
            self.load_requests()
            self.clear_details()

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء رفض الطلب: {str(e)}")
        finally:
            conn.close()

    def return_request(self):
        """إرجاع الطلب للمراجعة"""
        if not self.current_request_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار طلب أولاً.")
            return

        comments = self.comments_edit.toPlainText().strip()
        
        reply = QMessageBox.question(self, "تأكيد الإرجاع", 
                                   "هل تريد إرجاع هذا الطلب للمراجعة؟",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        try:
            self.execute_query(
                "UPDATE issue_requests SET status = 'returned' WHERE id = ?",
                (self.current_request_id,)
            )

            # تسجيل الإرجاع
            self.execute_query(
                """INSERT INTO issue_approvals 
                (request_id, approver_external_id, approval_level, approval_status, approval_date, comments, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (self.current_request_id, 'system', 1, 'returned', 
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 comments or "تم الإرجاع للمراجعة من خلال واجهة الاعتماد",
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )

            QMessageBox.information(self, "نجاح", "🔄 تم إرجاع الطلب للمراجعة بنجاح.")

            self.load_requests()
            self.clear_details()

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الإرجاع: {str(e)}")

    def create_issue_permit(self, request_id):
        """إنشاء إذن صرف بعد الاعتماد"""
        try:
            # الحصول على بيانات الطلب
            request_data = self.execute_query(
                "SELECT request_number, department_id, store_id FROM issue_requests WHERE id = ?",
                (request_id,), fetch="one"
            )

            if not request_data:
                return

            # إنشاء رقم الإذن
            permit_number = f"IP-{datetime.now().strftime('%Y%m%d')}-{request_id:04d}"
            
            # إدخال إذن الصرف
            self.execute_query(
                """INSERT INTO issue_permits 
                (permit_number, permit_date, request_id, warehouse_id, department_id, 
                 issued_by_external_id, status, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (permit_number, datetime.now().strftime("%Y-%m-%d"), request_id,
                 request_data.get('store_id', 0), request_data.get('department_id', 0),
                 'system', 'pending', 'تم الإنشاء تلقائياً بعد اعتماد الطلب',
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )

            print(f"تم إنشاء إذن الصرف: {permit_number}")

        except Exception as e:
            print(f"خطأ في إنشاء إذن الصرف: {e}")

    def toggle_approval_buttons(self, enabled):
        """تفعيل أو تعطيل أزرار الاعتماد"""
        self.approve_btn.setEnabled(enabled)
        self.reject_btn.setEnabled(enabled)
        self.return_btn.setEnabled(enabled)
        self.comments_edit.setEnabled(enabled)

    def clear_details(self):
        """مسح التفاصيل المعروضة"""
        for label in [self.lbl_request_number, self.lbl_request_date, self.lbl_department,
                     self.lbl_requester, self.lbl_purpose, self.lbl_priority, self.lbl_status]:
            label.setText("---")
            label.setStyleSheet("background-color: #f8f9fa; padding: 8px; border-radius: 4px; border: 1px solid #dee2e6;")
        
        self.items_table.setRowCount(0)
        self.comments_edit.clear()
        self.current_request_id = None
        self.toggle_approval_buttons(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    
    font = QFont("Arial", 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)
    
    window = IssueApprovalUI()
    window.setWindowTitle("نظام إدارة المخزون - اعتماد طلبات الصرف")
    window.resize(1400, 900)
    window.show()
    
    sys.exit(app.exec_())
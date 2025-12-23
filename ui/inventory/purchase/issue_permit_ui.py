# issue_permit_ui.py
# واجهة إدارة إذونات الصرف — محدثة لتسجيل عمليات الصرف في issue_transactions وتحديث أصناف الإذن
import sys
import os
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
                             QLabel, QMessageBox, QHeaderView, QTextEdit, QGroupBox, QDateEdit,
                             QSplitter, QFormLayout)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont

# إعداد المسارات
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)
from database.db_connection import get_inventory_db_connection


class IssuePermitUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("نظام إذونات الصرف")
        self.setGeometry(100, 100, 1400, 800)
        self.current_permit_id = None

        self.setLayoutDirection(Qt.RightToLeft)
        self.initUI()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { font-family: "Arial", sans-serif; font-size: 13px; }
            QGroupBox { font-weight: bold; border: 1px solid #D0D0D0; border-radius: 6px; margin-top: 10px; padding: 8px; }
            QPushButton { padding: 8px 12px; border-radius: 6px; border: none; }
            QPushButton[role="success"] { background-color: #28a745; color: white; font-weight: bold; }
            QPushButton[role="danger"] { background-color: #dc3545; color: white; font-weight: bold; }
            QPushButton[role="neutral"] { background-color: #17a2b8; color: white; font-weight: bold; }
            QLineEdit, QComboBox, QTextEdit, QDateEdit { padding: 5px; border: 1px solid #ccc; border-radius: 4px; }
            QTableWidget { gridline-color: #E0E0E0; selection-background-color: #BBDEFB; }
        """)

    def execute_query(self, query, params=(), fetch="all"):
        conn = get_inventory_db_connection()
        if not conn:
            return None
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetch.lower() == "all":
                result = cursor.fetchall()
            elif fetch.lower() == "one":
                result = cursor.fetchone()
            else:
                result = None
            conn.commit()
            return result
        except Exception as e:
            print(f"Database error: {e}")
            return None
        finally:
            conn.close()

    def initUI(self):
        self.apply_styles()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # ======= فلترة =======
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("البحث:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("ابحث برقم الإذن أو الطلب...")
        self.search_edit.textChanged.connect(self.load_permits)
        filter_layout.addWidget(self.search_edit)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["الكل", "pending", "approved", "issued", "completed", "cancelled"])
        self.status_filter.currentTextChanged.connect(self.load_permits)
        filter_layout.addWidget(QLabel("الحالة:"))
        filter_layout.addWidget(self.status_filter)

        self.warehouse_filter = QComboBox()
        self.warehouse_filter.currentTextChanged.connect(self.load_permits)
        filter_layout.addWidget(QLabel("المخزن:"))
        filter_layout.addWidget(self.warehouse_filter)

        filter_btn = QPushButton("🔍 تصفية")
        filter_btn.setProperty("role", "neutral")
        filter_btn.clicked.connect(self.load_permits)
        filter_layout.addWidget(filter_btn)

        main_layout.addLayout(filter_layout)

        # ======= القائمة والتفاصيل =======
        splitter = QSplitter(Qt.Horizontal)

        # القائمة
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.addWidget(QLabel("قائمة إذونات الصرف"))

        self.permits_table = QTableWidget()
        self.permits_table.setColumnCount(8)
        self.permits_table.setHorizontalHeaderLabels([
            "ID", "رقم الإذن", "التاريخ", "المخزن", "القسم", "رقم الطلب", "الحالة", "الإجراءات"
        ])
        self.permits_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.permits_table.setColumnHidden(0, True)
        self.permits_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.permits_table.selectionModel().selectionChanged.connect(self.show_permit_details)

        list_layout.addWidget(self.permits_table)

        # التفاصيل
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)

        details_group = QGroupBox("تفاصيل الإذن")
        details_form = QFormLayout(details_group)

        self.permit_number = QLineEdit()
        self.permit_number.setReadOnly(True)
        self.permit_date = QDateEdit()
        self.permit_date.setDate(QDate.currentDate())
        self.permit_date.setCalendarPopup(True)
        self.warehouse_combo = QComboBox()
        self.department_combo = QComboBox()
        self.request_number = QLineEdit()
        self.request_number.setReadOnly(True)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["pending", "approved", "issued", "completed", "cancelled"])

        details_form.addRow("رقم الإذن:", self.permit_number)
        details_form.addRow("تاريخ الإذن:", self.permit_date)
        details_form.addRow("المخزن:", self.warehouse_combo)
        details_form.addRow("القسم:", self.department_combo)
        details_form.addRow("رقم الطلب:", self.request_number)
        details_form.addRow("الحالة:", self.status_combo)

        details_layout.addWidget(details_group)

        # أصناف الإذن
        items_group = QGroupBox("أصناف الإذن")
        items_layout = QVBoxLayout(items_group)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(8)
        self.items_table.setHorizontalHeaderLabels([
            "ID", "كود الصنف", "اسم الصنف", "الكمية المطلوبة", "الكمية المصروفة", "الوحدة", "التكلفة", "الحالة"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setColumnHidden(0, True)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)

        items_layout.addWidget(self.items_table)
        details_layout.addWidget(items_group)

        # الإجراءات
        actions_group = QGroupBox("إجراءات الصرف")
        actions_layout = QVBoxLayout(actions_group)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("ملاحظات الصرف...")
        self.notes_edit.setMaximumHeight(80)

        buttons_layout = QHBoxLayout()
        self.issue_btn = QPushButton("📦 صرف")
        self.issue_btn.setProperty("role", "neutral")
        self.issue_btn.clicked.connect(self.issue_items)

        self.complete_btn = QPushButton("✅ إكمال")
        self.complete_btn.setProperty("role", "success")
        self.complete_btn.clicked.connect(self.complete_permit)

        self.cancel_btn = QPushButton("❌ إلغاء")
        self.cancel_btn.setProperty("role", "danger")
        self.cancel_btn.clicked.connect(self.cancel_permit)

        buttons_layout.addWidget(self.issue_btn)
        buttons_layout.addWidget(self.complete_btn)
        buttons_layout.addWidget(self.cancel_btn)

        actions_layout.addWidget(self.notes_edit)
        actions_layout.addLayout(buttons_layout)
        details_layout.addWidget(actions_group)

        splitter.addWidget(list_widget)
        splitter.addWidget(details_widget)
        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter)

        self.load_warehouses()
        self.load_departments()
        self.load_permits()
        self.toggle_action_buttons(False)

    # ========== تحميل البيانات ==========
    def load_warehouses(self):
        warehouses = self.execute_query("SELECT id, name_ar FROM warehouses WHERE is_active = 1")
        self.warehouse_filter.clear()
        self.warehouse_filter.addItem("الكل")
        self.warehouse_combo.clear()
        self.warehouse_combo.addItem("-- اختر المخزن --", 0)
        if warehouses:
            for wh in warehouses:
                self.warehouse_filter.addItem(wh['name_ar'])
                self.warehouse_combo.addItem(wh['name_ar'], wh['id'])

    def load_departments(self):
        departments = self.execute_query("SELECT id, name_ar FROM departments WHERE is_active = 1")
        self.department_combo.clear()
        self.department_combo.addItem("-- اختر القسم --", 0)
        if departments:
            for dept in departments:
                self.department_combo.addItem(dept['name_ar'], dept['id'])

    def load_permits(self):
        self.permits_table.setRowCount(0)

        query = """
        SELECT ip.id, ip.permit_number, ip.permit_date, w.name_ar as warehouse,
               d.name_ar as department, ir.request_number, ip.status
        FROM issue_permits ip
        LEFT JOIN warehouses w ON ip.warehouse_id = w.id
        LEFT JOIN departments d ON ip.department_id = d.id
        LEFT JOIN issue_requests ir ON ip.request_id = ir.id
        WHERE 1=1
        """
        params = []
        if self.status_filter.currentText() != "الكل":
            query += " AND ip.status = ?"
            params.append(self.status_filter.currentText())

        if self.warehouse_filter.currentText() != "الكل":
            query += " AND w.name_ar = ?"
            params.append(self.warehouse_filter.currentText())

        if self.search_edit.text():
            query += " AND (ip.permit_number LIKE ? OR ir.request_number LIKE ?)"
            params.extend([f"%{self.search_edit.text()}%", f"%{self.search_edit.text()}%"])

        query += " ORDER BY ip.permit_date DESC"

        permits = self.execute_query(query, tuple(params))
        if not permits:
            return

        self.permits_table.setRowCount(len(permits))
        for row, permit in enumerate(permits):
            for col, data in enumerate(permit):
                item = QTableWidgetItem(str(data))
                item.setTextAlignment(Qt.AlignCenter)
                self.permits_table.setItem(row, col, item)

            status_item = self.permits_table.item(row, 6)
            if status_item:
                if status_item.text() == "pending":
                    status_item.setBackground(Qt.yellow)
                elif status_item.text() == "approved":
                    status_item.setBackground(Qt.cyan)
                elif status_item.text() == "issued":
                    status_item.setBackground(Qt.blue)
                    status_item.setForeground(Qt.white)
                elif status_item.text() == "completed":
                    status_item.setBackground(Qt.green)
                    status_item.setForeground(Qt.white)
                elif status_item.text() == "cancelled":
                    status_item.setBackground(Qt.red)
                    status_item.setForeground(Qt.white)

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            view_btn = QPushButton("👁️ عرض")
            action_layout.addWidget(view_btn)
            action_layout.setContentsMargins(0, 0, 0, 0)
            self.permits_table.setCellWidget(row, 7, action_widget)

    def show_permit_details(self, selected, deselected):
        if not selected.indexes():
            self.clear_details()
            self.toggle_action_buttons(False)
            return

        row = selected.indexes()[0].row()
        permit_id_item = self.permits_table.item(row, 0)
        if not permit_id_item:
            return

        self.current_permit_id = int(permit_id_item.text())
        self.load_permit_details(self.current_permit_id)

    def load_permit_details(self, permit_id):
        """تحميل تفاصيل إذن الصرف (الأصناف)"""
        try:
            items = self.execute_query("""
                SELECT ipi.id, i.item_code, i.item_name_ar,
                       ipi.requested_quantity, ipi.issued_quantity,
                       ipi.status
                FROM issue_permit_items ipi
                JOIN items i ON ipi.item_id = i.id
                WHERE ipi.permit_id = ?
            """, (permit_id,), fetch="all")

            if not items:
                print(f"[DEBUG] لا توجد أصناف للإذن {permit_id}")
            else:
                print(f"[DEBUG] عدد الأصناف المسترجعة للإذن {permit_id}: {len(items)}")

            # تحديث الجدول في الواجهة
            self.items_table.setRowCount(0)
            for row_idx, item in enumerate(items):
                self.items_table.insertRow(row_idx)
                self.items_table.setItem(row_idx, 0, QTableWidgetItem(str(item["item_code"])))
                self.items_table.setItem(row_idx, 1, QTableWidgetItem(str(item["item_name_ar"])))
                self.items_table.setItem(row_idx, 2, QTableWidgetItem(str(item["requested_quantity"])))
                self.items_table.setItem(row_idx, 3, QTableWidgetItem(str(item["issued_quantity"])))
                self.items_table.setItem(row_idx, 4, QTableWidgetItem(str(item["status"])))

        except Exception as e:
            print(f"[ERROR] load_permit_details: {e}")


    def load_permit_items(self, permit_id):
        self.items_table.setRowCount(0)

        permit = self.execute_query(
            "SELECT status, request_id FROM issue_permits WHERE id = ?",
            (permit_id,), fetch="one"
        )
        if not permit:
            return

        if permit["status"] in ("pending", "approved"):
            query = """
            SELECT iri.id, i.item_code, i.item_name_ar,
                    iri.quantity as requested_quantity,
                    COALESCE(iri.issued_quantity, 0) as issued_quantity,
                    u.name_ar as unit_name, 0 as unit_cost, iri.status
                FROM issue_request_items iri
                JOIN items i ON iri.item_id = i.id
                LEFT JOIN units u ON iri.unit_id = u.id
                WHERE iri.request_id = ?
            """
            items = self.execute_query(query, (permit["request_id"],))
        else:  # issued, completed, cancelled
            query = """
            SELECT ipi.id, i.item_code, i.item_name_ar,
               ipi.requested_quantity, ipi.issued_quantity,
               u.name_ar as unit_name, ipi.unit_cost, ipi.status
            FROM issue_permit_items ipi
            JOIN items i ON ipi.item_id = i.id
            LEFT JOIN units u ON ipi.unit_id = u.id
            WHERE ipi.permit_id = ?
            """
        items = self.execute_query(query, (permit_id,))

        if not items:
            print(f"[DEBUG] لا توجد أصناف للإذن {permit_id} بالحالة {permit['status']}")
            return

        # تعبئة الجدول
        self.items_table.setRowCount(len(items))
        for row, item_data in enumerate(items):
            self.items_table.setItem(row, 0, QTableWidgetItem(str(item_data['id'])))
            self.items_table.setItem(row, 1, QTableWidgetItem(item_data.get('item_code', '')))
            self.items_table.setItem(row, 2, QTableWidgetItem(item_data.get('item_name_ar', '')))
            self.items_table.setItem(row, 3, QTableWidgetItem(str(item_data.get('requested_quantity', ''))))
            self.items_table.setItem(row, 4, QTableWidgetItem(str(item_data.get('issued_quantity', ''))))
            self.items_table.setItem(row, 5, QTableWidgetItem(item_data.get('unit_name', '')))
            self.items_table.setItem(row, 6, QTableWidgetItem(str(item_data.get('unit_cost', ''))))
            self.items_table.setItem(row, 7, QTableWidgetItem(item_data.get('status', '')))


    def sync_request_items_to_permit(self, permit_id):
        """ينسخ أصناف الطلب المرتبط إلى permit_items لو مش موجودة"""
        permit = self.execute_query(
            "SELECT request_id, status FROM issue_permits WHERE id = ?",
            (permit_id,), fetch="one"
        )
        if not permit or not permit["request_id"]:
            print(f"[DEBUG] Permit {permit_id} مش لاقي طلب مرتبط")
            return

        print(f"[DEBUG] Permit {permit_id}, status={permit['status']}, request_id={permit['request_id']}")

        # تحقق هل فيه أصناف موجودة بالفعل
        existing = self.execute_query(
            "SELECT COUNT(*) as cnt FROM issue_permit_items WHERE permit_id = ?",
            (permit_id,), fetch="one"
        )

        # انسخ لو مفيش أصناف، والحالة approved أو issued
        if existing and existing["cnt"] == 0 and permit["status"] in ("approved", "issued"):
            conn = get_inventory_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO issue_permit_items 
                        (permit_id, item_id, request_item_id, requested_quantity, issued_quantity, unit_id, unit_cost, status, created_at)
                        SELECT ?, iri.item_id, iri.id, iri.quantity, 0, iri.unit_id, 0, 'pending', ?
                        FROM issue_request_items iri
                        WHERE iri.request_id = ?
                    """, (
                        permit_id,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        permit["request_id"]
                    ))
                    conn.commit()
                    print(f"[DEBUG] تم نسخ أصناف الطلب {permit['request_id']} إلى الإذن {permit_id}")
                except Exception as e:
                    print(f"[ERROR] sync_request_items_to_permit: {e}")
                finally:
                    conn.close()



    # ========== الإجراءات ==========
    def issue_items(self):
        """صرف المواد — يسجل في issue_transactions ويحدث issued_quantity و status"""
        if not self.current_permit_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار إذن أولاً")
            return

        conn = get_inventory_db_connection()
        if not conn:
            return
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            permit_items = cursor.execute("""
                SELECT id, permit_id, item_id, request_item_id, requested_quantity, issued_quantity, unit_id, unit_cost, status
                FROM issue_permit_items
                WHERE permit_id = ?
            """, (self.current_permit_id,)).fetchall()

            if not permit_items:
                QMessageBox.warning(self, "تنبيه", "لا توجد أصناف للصرف في هذا الإذن.")
                return

            for pi in permit_items:
                to_issue = (pi['requested_quantity'] or 0) - (pi['issued_quantity'] or 0)
                if to_issue <= 0:
                    continue

                issued_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                total_cost = (pi['unit_cost'] or 0) * to_issue

                cursor.execute("""
                    INSERT INTO issue_transactions
                    (permit_id, permit_item_id, item_id, quantity, unit_id, unit_cost, total_cost, issued_by_external_id, issued_at, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'issued', ?)
                """, (self.current_permit_id, pi['id'], pi['item_id'], to_issue, pi['unit_id'], pi['unit_cost'], total_cost, 'system', issued_at, issued_at))

                new_issued = (pi['issued_quantity'] or 0) + to_issue
                new_status = 'issued'
                cursor.execute("""
                    UPDATE issue_permit_items SET issued_quantity = ?, status = ?, updated_at = ? WHERE id = ?
                """, (new_issued, new_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pi['id']))

                if pi['request_item_id']:
                    cursor.execute("""
                        UPDATE issue_request_items
                        SET issued_quantity = COALESCE(issued_quantity, 0) + ?, 
                            status = CASE WHEN COALESCE(issued_quantity,0) + ? >= quantity THEN 'completed' ELSE 'partially_issued' END,
                            updated_at = ?
                        WHERE id = ?
                    """, (to_issue, to_issue, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pi['request_item_id']))

            cursor.execute("UPDATE issue_permits SET status = 'issued', issue_date = ?, updated_at = ? WHERE id = ?",
                           (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.current_permit_id))

            cursor.execute("""
                INSERT INTO permit_status_history (permit_id, old_status, new_status, changed_by_external_id, change_reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.current_permit_id, 'pending', 'issued', 'system', self.notes_edit.toPlainText() or 'صرف الأصناف', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            conn.commit()
            QMessageBox.information(self, "نجاح", "تم صرف المواد بنجاح")
            self.load_permits()
            self.load_permit_details(self.current_permit_id)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الصرف: {str(e)}")
        finally:
            conn.close()

    def complete_permit(self):
        if not self.current_permit_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار إذن أولاً")
            return

        try:
            self.execute_query("UPDATE issue_permits SET status = 'completed', updated_at = ? WHERE id = ?",
                               (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.current_permit_id))
            self.execute_query("""
                INSERT INTO permit_status_history (permit_id, old_status, new_status, changed_by_external_id, change_reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.current_permit_id, 'issued', 'completed', 'system', self.notes_edit.toPlainText() or 'اكمال الإذن', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            QMessageBox.information(self, "نجاح", "تم إكمال عملية الصرف بنجاح")
            self.load_permits()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الإكمال: {str(e)}")

    def cancel_permit(self):
        if not self.current_permit_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار إذن أولاً")
            return

        try:
            self.execute_query("UPDATE issue_permits SET status = 'cancelled', updated_at = ? WHERE id = ?",
                               (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.current_permit_id))
            self.execute_query("""
                INSERT INTO permit_status_history (permit_id, old_status, new_status, changed_by_external_id, change_reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.current_permit_id, 'pending', 'cancelled', 'system', self.notes_edit.toPlainText() or 'إلغاء الإذن', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            QMessageBox.information(self, "نجاح", "تم إلغاء الإذن بنجاح")
            self.load_permits()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الإلغاء: {str(e)}")

    def toggle_action_buttons(self, enabled):
        self.issue_btn.setEnabled(enabled)
        self.complete_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(enabled)
        self.notes_edit.setEnabled(enabled)

    def clear_details(self):
        self.permit_number.clear()
        self.request_number.clear()
        self.items_table.setRowCount(0)
        self.notes_edit.clear()
        self.current_permit_id = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    font = QFont("Arial", 10)
    app.setFont(font)
    window = IssuePermitUI()
    window.show()
    sys.exit(app.exec_())

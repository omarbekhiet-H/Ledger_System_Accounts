import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QGroupBox, QLabel, QLineEdit, QComboBox, QTextEdit,
    QDateEdit, QPushButton, QTableWidget, QHeaderView, QTableWidgetItem,
    QDoubleSpinBox, QMessageBox
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont

# ======================
# إعداد مسار المشروع
# ======================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# استيراد دوال الاتصال بقواعد البيانات
from database.db_connection import (
    get_inventory_db_connection,
    get_manufacturing_db_connection
)


class IssueRequestCreate(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("إنشاء طلب صرف أصناف")
        self.setGeometry(200, 200, 1100, 750)
        self.setLayoutDirection(Qt.RightToLeft)

        # خط افتراضي
        font = QFont("Cairo", 11)
        self.setFont(font)

        self.initUI()

    # ======================
    # بناء الواجهة
    # ======================
    def initUI(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(12)

        # -------------------------
        # معلومات الطلب
        # -------------------------
        info_group = QGroupBox("معلومات الطلب")
        info_layout = QFormLayout(info_group)
        info_layout.setLabelAlignment(Qt.AlignRight)

        self.request_number = QLineEdit()
        self.request_number.setReadOnly(True)
        self.request_number.setStyleSheet("background:#f0f0f0;")

        self.request_date = QDateEdit(QDate.currentDate())
        self.request_date.setCalendarPopup(True)

        self.requester_id = QLineEdit()
        self.department_combo = QComboBox()
        self.store_combo = QComboBox()

        self.purpose_edit = QTextEdit()
        self.purpose_edit.setMaximumHeight(70)

        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["low", "normal", "high", "urgent"])

        self.required_date = QDateEdit(QDate.currentDate().addDays(7))
        self.required_date.setCalendarPopup(True)

        info_layout.addRow("رقم الطلب:", self.request_number)
        info_layout.addRow("تاريخ الطلب:", self.request_date)
        info_layout.addRow("رقم مقدم الطلب:", self.requester_id)
        info_layout.addRow("القسم:", self.department_combo)
        info_layout.addRow("المخزن:", self.store_combo)
        info_layout.addRow("الغرض:", self.purpose_edit)
        info_layout.addRow("الأولوية:", self.priority_combo)
        info_layout.addRow("التاريخ المطلوب:", self.required_date)

        main_layout.addWidget(info_group)

        # -------------------------
        # جدول الأصناف
        # -------------------------
        items_group = QGroupBox("أصناف الطلب")
        items_layout = QVBoxLayout(items_group)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "الصنف", "الكمية", "الوحدة", "ملاحظات", "الأولوية", "التاريخ المطلوب"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setStyleSheet("""
            QTableWidget { background:#fff; alternate-background-color:#f9f9f9; }
            QHeaderView::section { background:#2980B9; color:white; padding:5px; }
        """)

        items_layout.addWidget(self.items_table)

        add_item_btn = QPushButton("➕ إضافة صنف")
        add_item_btn.setStyleSheet("padding:6px 12px; background:#27AE60; color:white; font-weight:bold;")
        add_item_btn.clicked.connect(self.add_item_row)
        items_layout.addWidget(add_item_btn, alignment=Qt.AlignLeft)

        main_layout.addWidget(items_group)

        # -------------------------
        # أزرار الحفظ والإلغاء
        # -------------------------
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 حفظ")
        save_btn.setStyleSheet("padding:8px 18px; background:#2980B9; color:white; font-weight:bold;")
        save_btn.clicked.connect(self.save_request)

        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setStyleSheet("padding:8px 18px; background:#E74C3C; color:white; font-weight:bold;")
        cancel_btn.clicked.connect(self.close)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)

        # -------------------------
        # تحميل البيانات الأولية
        # -------------------------
        self.load_departments()
        self.load_warehouses()
        self.generate_request_number()

    # ======================
    # دوال قاعدة البيانات
    # ======================
    def execute_query(self, query, params=(), fetch="all"):
        conn = get_inventory_db_connection()
        if not conn:
            return None
        try:
            cur = conn.cursor()
            cur.execute(query, params)
            if fetch == "all":
                result = cur.fetchall()
            elif fetch == "one":
                result = cur.fetchone()
            else:
                result = None
            conn.commit()
            return result
        except Exception as e:
            print("DB Error:", e)
            return None
        finally:
            conn.close()

    # ======================
    # تحميل بيانات المراجع
    # ======================
    def load_departments(self):
        self.department_combo.clear()
        self.department_combo.addItem("-- اختر القسم --", 0)
        depts = self.execute_query("SELECT id, name_ar FROM departments WHERE is_active=1")
        if depts:
            for d in depts:
                self.department_combo.addItem(d[1], d[0])

    def load_warehouses(self):
        self.store_combo.clear()
        self.store_combo.addItem("-- اختر المخزن --", 0)
        whs = self.execute_query("SELECT id, name_ar FROM warehouses WHERE is_active=1")
        if whs:
            for w in whs:
                self.store_combo.addItem(w[1], w[0])

    def load_items(self, combo: QComboBox):
        combo.clear()
        combo.addItem("-- اختر الصنف --", 0)
        items = self.execute_query("SELECT id, item_name_ar FROM items WHERE is_active=1")
        if items:
            for it in items:
                combo.addItem(it[1], it[0])

    def load_units(self, combo: QComboBox, item_id: int):
        combo.clear()
        combo.addItem("-- اختر الوحدة --", 0)
        if not item_id or item_id == 0:
            return
        units = self.execute_query("""
            SELECT u.id, u.name_ar
            FROM item_units iu
            JOIN units u ON iu.unit_id = u.id
            WHERE iu.item_id=? AND u.is_active=1
        """, (item_id,))
        if units:
            for u in units:
                combo.addItem(u[1], u[0])

    # ======================
    # إضافة صف صنف
    # ======================
    def add_item_row(self):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        item_combo, unit_combo = QComboBox(), QComboBox()
        qty_spin = QDoubleSpinBox()
        #qty_spin = QDoubleSpinBox()
        qty_spin.setMinimum(0)
        qty_spin.setMaximum(10000)
        qty_spin.setSpecialValueText("")   # يخليها تبان فاضية لو القيمة = 0
        qty_spin.setButtonSymbols(QDoubleSpinBox.NoButtons)  # يخفي الأسهم ↑ ↓
        qty_spin.clear()
        #qty_spin.setValue(0)               # خل    # لكن هيظهر كأنه فاضي

        notes_edit = QLineEdit()
        prio = QComboBox(); prio.addItems(["low", "normal", "high", "urgent"])
        rdate = QDateEdit(QDate.currentDate().addDays(7)); rdate.setCalendarPopup(True)

        self.items_table.setCellWidget(row, 0, item_combo)
        self.items_table.setCellWidget(row, 1, qty_spin)
        self.items_table.setCellWidget(row, 2, unit_combo)
        self.items_table.setCellWidget(row, 3, notes_edit)
        self.items_table.setCellWidget(row, 4, prio)
        self.items_table.setCellWidget(row, 5, rdate)

        self.load_items(item_combo)
        item_combo.currentIndexChanged.connect(
            lambda _, icb=item_combo, ucb=unit_combo: self.load_units(ucb, icb.currentData())
        )


    # ======================
    # ترقيم تلقائي
    # ======================
    def generate_request_number(self):
        last = self.execute_query("SELECT request_number FROM issue_requests ORDER BY id DESC LIMIT 1", fetch="one")
        if not last or not last[0]:
            next_num = 1
        else:
            try:
                next_num = int(str(last[0]).split("-")[-1]) + 1
            except:
                next_num = 1
        year = QDate.currentDate().toString("yyyy")
        self.request_number.setText(f"IR-{year}-{str(next_num).zfill(3)}")

    # ======================
    # حفظ الطلب وربطه بالتصنيع
    # ======================
    def save_request(self):
        if self.department_combo.currentData() == 0 or self.store_combo.currentData() == 0:
            QMessageBox.warning(self, "خطأ", "اختر القسم والمخزن")
            return

        try:
            # ====== حفظ في قاعدة بيانات المخازن ======
            self.execute_query("""
                INSERT INTO issue_requests
                (request_number, request_date, requester_external_id, department_id, store_id, purpose, priority, required_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (
                self.request_number.text(),
                self.request_date.date().toString("yyyy-MM-dd"),
                self.requester_id.text(),
                self.department_combo.currentData(),
                self.store_combo.currentData(),
                self.purpose_edit.toPlainText(),
                self.priority_combo.currentText(),
                self.required_date.date().toString("yyyy-MM-dd")
            ))

            last = self.execute_query("SELECT last_insert_rowid()", fetch="one")
            request_id = last[0] if last else None

            # ====== إنشاء Job Order في قاعدة التصنيع ======
            conn_m = get_manufacturing_db_connection()
            cur_m = conn_m.cursor()

            cur_m.execute("""
                INSERT INTO job_orders (job_number, job_title, job_description, job_type, priority, status, request_date, planned_end_date, external_job_id)
                VALUES (?, ?, ?, 'production', ?, 'pending', ?, ?, ?)
            """, (
                f"JOB-{self.request_number.text()}",
                f"طلب صرف {self.request_number.text()}",
                self.purpose_edit.toPlainText(),
                self.priority_combo.currentText(),
                self.request_date.date().toString("yyyy-MM-dd"),
                self.required_date.date().toString("yyyy-MM-dd"),
                request_id
            ))
            job_order_id = cur_m.lastrowid

            # ====== إدخال أصناف الطلب ======
            for r in range(self.items_table.rowCount()):
                item_id = self.items_table.cellWidget(r, 0).currentData()
                qty = self.items_table.cellWidget(r, 1).value()
                unit_id = self.items_table.cellWidget(r, 2).currentData()
                notes = self.items_table.cellWidget(r, 3).text()
                prio = self.items_table.cellWidget(r, 4).currentText()
                rdate = self.items_table.cellWidget(r, 5).date().toString("yyyy-MM-dd")

                if item_id and unit_id:
                    # إدخال في قاعدة المخازن
                    self.execute_query("""
                        INSERT INTO issue_request_items
                        (request_id, item_id, quantity, unit_id, notes, priority, required_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (request_id, item_id, qty, unit_id, notes, prio, rdate))

                    # إدخال في قاعدة التصنيع
                    cur_m.execute("""
                        INSERT INTO job_order_material_requirements
                        (job_order_id, item_id, quantity_required, unit_id, notes, priority, required_date, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
                    """, (job_order_id, item_id, qty, unit_id, notes, prio, rdate))

            conn_m.commit()
            conn_m.close()

            QMessageBox.information(self, "تم", "تم حفظ الطلب وإنشاء أمر تشغيل مرتبط به")
            #self.close()

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحفظ: {e}")


# ======================
# التشغيل
# ======================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    font = QFont("Cairo", 10)
    app.setFont(font)
    w = IssueRequestCreate()
    w.show()
    sys.exit(app.exec_())

# job_order_material_requirements_ui.py
import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QDateEdit, QMessageBox, QCompleter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QColor, QFont


# --- إعداد المسارات ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.db_connection import get_manufacturing_db_connection, get_inventory_db_connection


class JobOrderMaterialRequirements_UI(QWidget):
    def __init__(self, job_order_id=1):
        super().__init__()
        self.job_order_id = job_order_id
        self.selected_item_id = None
        self.editing_id = None
        self.initUI()
        self.load_requirements()

    def initUI(self):
        self.setWindowTitle("متطلبات المواد - أمر تشغيل")
        self.setGeometry(200, 200, 1200, 800)
        self.setLayoutDirection(Qt.RightToLeft)

        layout = QVBoxLayout(self)

        # ===== رأس أمر التشغيل =====
        header_group = QGroupBox("📋 بيانات أمر التشغيل")
        header_layout = QHBoxLayout(header_group)

        lbl_num = QLabel("رقم أمر الشغل:")
        self.job_order_label = QLineEdit(str(self.job_order_id))
        self.job_order_label.setReadOnly(True)

        lbl_date = QLabel("📅 التاريخ:")
        self.job_date_input = QDateEdit(datetime.now())
        self.job_date_input.setCalendarPopup(True)
        self.job_date_input.setDisplayFormat("yyyy-MM-dd")

        header_layout.addWidget(lbl_num)
        header_layout.addWidget(self.job_order_label)
        header_layout.addStretch()
        header_layout.addWidget(lbl_date)
        header_layout.addWidget(self.job_date_input)
        layout.addWidget(header_group)

        # ===== نموذج الإضافة =====
        form_group = QGroupBox("➕ إضافة / تعديل متطلب")
        form_layout = QHBoxLayout(form_group)

        form_layout.addWidget(QLabel("الصنف:"))
        self.item_input = QLineEdit()
        self.item_input.setPlaceholderText("اكتب اسم أو كود الصنف...")
        self.item_input.textChanged.connect(self.search_items)
        self.item_input.editingFinished.connect(self.resolve_item_from_text)
        form_layout.addWidget(self.item_input)

        form_layout.addWidget(QLabel("الوحدة:"))
        self.unit_combo = QComboBox()
        form_layout.addWidget(self.unit_combo)

        form_layout.addWidget(QLabel("الكمية:"))
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("ادخل الكمية")
        self.quantity_input.setValidator(QDoubleValidator(0.0001, 9999999, 3))
        self.quantity_input.setAlignment(Qt.AlignRight)
        form_layout.addWidget(self.quantity_input)

        form_layout.addWidget(QLabel("الأولوية:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["منخفضة", "متوسطة", "عالية"])
        self.priority_combo.setCurrentText("متوسطة")
        form_layout.addWidget(self.priority_combo)

        layout.addWidget(form_group)

        # ===== ملاحظات =====
        notes_group = QGroupBox("📝 ملاحظات")
        notes_layout = QHBoxLayout(notes_group)
        notes_layout.addWidget(QLabel("ملاحظات:"))
        self.notes_input = QLineEdit()
        notes_layout.addWidget(self.notes_input)
        layout.addWidget(notes_group)

        # ===== أزرار =====
        buttons_layout = QHBoxLayout()
        self.clear_btn = QPushButton("🆕 جديد")
        self.clear_btn.setStyleSheet("background-color: #607D8B; color: white; font-size:14px; padding:6px;")
        self.clear_btn.clicked.connect(self.clear_form)
        buttons_layout.addWidget(self.clear_btn)

        self.add_btn = QPushButton("➕ إضافة")
        self.add_btn.setStyleSheet("background-color: green; color: white; font-size:14px; padding:6px;")
        self.add_btn.clicked.connect(self.add_requirement)
        buttons_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("✏️ تعديل")
        self.edit_btn.setStyleSheet("background-color: orange; color: black; font-size:14px; padding:6px;")
        self.edit_btn.clicked.connect(self.prepare_edit)
        buttons_layout.addWidget(self.edit_btn)

        self.save_btn = QPushButton("💾 حفظ")
        self.save_btn.setStyleSheet("background-color: blue; color: white; font-size:14px; padding:6px;")
        self.save_btn.clicked.connect(self.save_edit)
        self.save_btn.setEnabled(False)
        buttons_layout.addWidget(self.save_btn)

        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.setStyleSheet("background-color: red; color: white; font-size:14px; padding:6px;")
        self.delete_btn.clicked.connect(self.delete_requirement)
        buttons_layout.addWidget(self.delete_btn)

        layout.addLayout(buttons_layout)

        # ===== جدول =====
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "كود الصنف", "اسم الصنف", "الكمية", "الوحدة",
            "سعر الوحدة", "القيمة", "الحالة", "الأولوية", "التاريخ"
        ])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setShowGrid(True)
        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
        layout.addWidget(self.table)

    # ------------------ بحث ------------------
    def search_items(self, text):
        text = text.strip()
        if not text:
            return
        conn = get_inventory_db_connection()
        if not conn:
            return
        try:
            rows = conn.execute("""
                SELECT id, item_code, item_name_ar FROM items
                WHERE is_active = 1 AND (item_name_ar LIKE ? OR item_code LIKE ?)
                ORDER BY item_name_ar LIMIT 25
            """, (f"%{text}%", f"%{text}%")).fetchall()
            options = [f"{r['item_code']} - {r['item_name_ar']}" for r in rows]
            if options:
                completer = QCompleter(options, self.item_input)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)
                completer.activated.connect(self.on_completer_activated)
                self.item_input.setCompleter(completer)
        finally:
            conn.close()

    def on_completer_activated(self, text):
        parts = text.split(" - ", 1)
        code = parts[0].strip()
        conn = get_inventory_db_connection()
        if not conn:
            return
        try:
            row = conn.execute("SELECT id FROM items WHERE item_code = ? COLLATE NOCASE LIMIT 1", (code,)).fetchone()
            if row:
                self.selected_item_id = row["id"]
                self.load_item_units(self.selected_item_id)
        finally:
            conn.close()

    def resolve_item_from_text(self):
        text = self.item_input.text().strip()
        if not text:
            return
        parts = text.split(" - ", 1)
        code = parts[0].strip() if len(parts) > 1 else text
        conn = get_inventory_db_connection()
        if not conn:
            return
        try:
            row = conn.execute("""
                SELECT id, item_code, item_name_ar
                FROM items
                WHERE (item_code = ? OR item_name_ar = ?) AND is_active = 1
                LIMIT 1
            """, (code, text)).fetchone()
            if row:
                self.selected_item_id = row["id"]
                self.item_input.setText(f"{row['item_code']} - {row['item_name_ar']}")
                self.load_item_units(self.selected_item_id)
        finally:
            conn.close()

    def load_item_units(self, item_id):
        self.unit_combo.clear()
        conn = get_inventory_db_connection()
        if not conn:
            return
        try:
            units = conn.execute("""
                SELECT u.id, u.name_ar
                FROM item_units iu
                JOIN units u ON iu.unit_id = u.id
                WHERE iu.item_id = ?
            """, (item_id,)).fetchall()
            for u in units:
                self.unit_combo.addItem(u["name_ar"], u["id"])
        finally:
            conn.close()

    # ------------------ إضافة ------------------
    def add_requirement(self):
        if not self.selected_item_id:
            QMessageBox.warning(self, "تنبيه", "اختر صنفًا.")
            return
        if not self.quantity_input.text().strip():
            QMessageBox.warning(self, "تنبيه", "أدخل الكمية.")
            return
        qty = float(self.quantity_input.text())

        conn = get_manufacturing_db_connection()
        if not conn:
            return
        try:
            exists = conn.execute("""
                SELECT id FROM job_order_material_requirements
                WHERE job_order_id = ? AND item_id = ?
            """, (self.job_order_id, self.selected_item_id)).fetchone()
            if exists:
                QMessageBox.warning(self, "تنبيه", "الصنف مكرر.")
                return

            conn.execute("""
                INSERT INTO job_order_material_requirements
                (job_order_id, item_id, unit_id, quantity_required, priority, required_date, notes, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """, (
                self.job_order_id,
                self.selected_item_id,
                self.unit_combo.currentData(),
                qty,
                self.priority_combo.currentText(),
                self.job_date_input.date().toString("yyyy-MM-dd"),
                self.notes_input.text(),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            self.load_requirements()
            self.clear_form()
        finally:
            conn.close()

    # ------------------ تعديل ------------------
    def prepare_edit(self):
        row = self.table.currentRow()
        if row < 0:
            return
        id_item = self.table.item(row, 0)
        if not id_item or not id_item.text().isdigit():
            return
        self.editing_id = int(id_item.text())

        conn = get_manufacturing_db_connection()
        if not conn:
            return
        try:
            r = conn.execute("SELECT * FROM job_order_material_requirements WHERE id = ?", (self.editing_id,)).fetchone()
            if r:
                self.selected_item_id = r["item_id"]
                conn_inv = get_inventory_db_connection()
                if conn_inv:
                    item = conn_inv.execute("SELECT item_code, item_name_ar FROM items WHERE id = ?", (self.selected_item_id,)).fetchone()
                    if item:
                        self.item_input.setText(f"{item['item_code']} - {item['item_name_ar']}")
                    self.load_item_units(self.selected_item_id)
                self.quantity_input.setText(str(r["quantity_required"]))
                self.priority_combo.setCurrentText(r["priority"])
                if r["required_date"]:
                    self.job_date_input.setDate(datetime.strptime(r["required_date"], "%Y-%m-%d"))
                self.notes_input.setText(r["notes"] or "")
                self.add_btn.setEnabled(False)
                self.save_btn.setEnabled(True)
        finally:
            conn.close()

    def save_edit(self):
        if not self.editing_id:
            return
        qty = float(self.quantity_input.text())

        conn = get_manufacturing_db_connection()
        if not conn:
            return
        try:
            conn.execute("""
                UPDATE job_order_material_requirements
                SET item_id = ?, unit_id = ?, quantity_required = ?, priority = ?, required_date = ?, notes = ?
                WHERE id = ?
            """, (
                self.selected_item_id,
                self.unit_combo.currentData(),
                qty,
                self.priority_combo.currentText(),
                self.job_date_input.date().toString("yyyy-MM-dd"),  # ← التصحيح هنا
                self.notes_input.text(),
                self.editing_id
            ))
            conn.commit()
            self.load_requirements()
            self.clear_form()
            self.editing_id = None
            self.add_btn.setEnabled(True)
            self.save_btn.setEnabled(False)
        finally:
            conn.close()

    # ------------------ حذف ------------------
    def delete_requirement(self):
        row = self.table.currentRow()
        if row < 0:
            return
        id_item = self.table.item(row, 0)
        if not id_item or not id_item.text().isdigit():
            return
        req_id = int(id_item.text())
        conn = get_manufacturing_db_connection()
        if not conn:
            return
        try:
            conn.execute("DELETE FROM job_order_material_requirements WHERE id = ?", (req_id,))
            conn.commit()
            self.load_requirements()
            self.clear_form()
        finally:
            conn.close()

    # ------------------ تحميل الجدول ------------------
    def load_requirements(self):
        conn_man = get_manufacturing_db_connection()
        conn_inv = get_inventory_db_connection()
        if not conn_man or not conn_inv:
            return
        try:
            rows = conn_man.execute("""
                SELECT * FROM job_order_material_requirements
                WHERE job_order_id = ?
            """, (self.job_order_id,)).fetchall()

            self.table.setRowCount(0)
            total = 0.0
            for r in rows:
                item = conn_inv.execute("SELECT item_code, item_name_ar, purchase_price FROM items WHERE id = ?", (r["item_id"],)).fetchone()
                unit = conn_inv.execute("SELECT name_ar FROM units WHERE id = ?", (r["unit_id"],)).fetchone()
                price = float(item["purchase_price"]) if item else 0
                value = price * float(r["quantity_required"] or 0)
                total += value

                row = self.table.rowCount()
                self.table.insertRow(row)
                vals = [
                    str(r["id"]),
                    item["item_code"] if item else "",
                    item["item_name_ar"] if item else "",
                    str(r["quantity_required"]),
                    unit["name_ar"] if unit else "",
                    f"{price:,.2f}",
                    f"{value:,.2f}",
                    r["status"],
                    r["priority"],
                    r["required_date"] or ""
                ]
                for col, val in enumerate(vals):
                    cell = QTableWidgetItem(val)
                    cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(row, col, cell)

            # إجمالي
            total_row = self.table.rowCount()
            self.table.insertRow(total_row)
            total_item = QTableWidgetItem(f"{total:,.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            total_item.setFont(QFont("Arial", 11, QFont.Bold))
            total_item.setBackground(QColor(230, 230, 230))
            self.table.setItem(total_row, 6, total_item)
        finally:
            conn_man.close()
            conn_inv.close()

    def on_table_selection_changed(self):
        pass

    def clear_form(self):
        self.item_input.clear()
        self.unit_combo.clear()
        self.quantity_input.clear()
        self.priority_combo.setCurrentText("متوسطة")
        self.notes_input.clear()
        self.editing_id = None
        self.selected_item_id = None
        self.add_btn.setEnabled(True)
        self.save_btn.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JobOrderMaterialRequirements_UI(job_order_id=1)
    window.show()
    sys.exit(app.exec_())

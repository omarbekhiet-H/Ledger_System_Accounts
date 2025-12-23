import sys
import os
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHBoxLayout,
    QLineEdit, QMessageBox, QComboBox, QDateEdit,
    QHeaderView, QGroupBox, QGridLayout, QDoubleSpinBox, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# --- إعداد المسارات ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)
from database.db_connection import get_inventory_db_connection


class JobOrderMaterialIssues_UI(QWidget):
    def __init__(self, job_order_id=None):
        super().__init__()
        self.job_order_id = job_order_id
        self.current_issue_id = None
        self.initUI()
        self.load_issues()

    def initUI(self):
        self.setWindowTitle("إدارة إصدارات المواد - أوامر التشغيل")
        self.setGeometry(180, 180, 1200, 800)
        layout = QVBoxLayout(self)

        title = QLabel("📦 إصدارات المواد")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0D47A1;")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "الصنف", "الكمية", "الوحدة", "التكلفة", "من المخزن",
            "الحالة", "تاريخ الإصدار", "ملاحظات"
        ])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemSelectionChanged.connect(self.on_issue_selected)
        layout.addWidget(self.table)

        form_group = QGroupBox("➕ إصدار جديد")
        form_layout = QGridLayout(form_group)

        form_layout.addWidget(QLabel("الصنف:"), 0, 0)
        self.item_input = QLineEdit()
        form_layout.addWidget(self.item_input, 0, 1)

        form_layout.addWidget(QLabel("الكمية:"), 0, 2)
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.1, 100000)
        form_layout.addWidget(self.quantity_input, 0, 3)

        form_layout.addWidget(QLabel("الوحدة:"), 1, 0)
        self.unit_combo = QComboBox()
        self.load_units()
        form_layout.addWidget(self.unit_combo, 1, 1)

        form_layout.addWidget(QLabel("من مخزن:"), 1, 2)
        self.warehouse_input = QLineEdit()
        form_layout.addWidget(self.warehouse_input, 1, 3)

        form_layout.addWidget(QLabel("ملاحظات:"), 2, 0)
        self.notes_input = QLineEdit()
        form_layout.addWidget(self.notes_input, 2, 1, 1, 3)

        add_btn = QPushButton("➕ إضافة")
        add_btn.clicked.connect(self.add_issue)
        form_layout.addWidget(add_btn, 3, 0, 1, 4)

        layout.addWidget(form_group)

        button_layout = QHBoxLayout()
        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.clicked.connect(self.delete_issue)
        button_layout.addWidget(self.delete_btn)

        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.clicked.connect(self.load_issues)
        button_layout.addWidget(refresh_btn)
        layout.addLayout(button_layout)

    def load_units(self):
        conn = get_inventory_db_connection()
        if not conn: return
        try:
            units = conn.execute("SELECT id, name_ar FROM units WHERE is_active = 1").fetchall()
            self.unit_combo.clear()
            for u in units:
                self.unit_combo.addItem(u["name_ar"], u["id"])
        finally:
            conn.close()

    def load_issues(self):
        if not self.job_order_id: return
        conn = get_inventory_db_connection()
        if not conn: return
        try:
            rows = conn.execute("""
                SELECT i.id, it.item_name_ar, i.quantity_issued, u.name_ar as unit_name,
                       i.total_cost, w.name_ar as warehouse_name, i.consumption_status,
                       i.issued_date, i.notes
                FROM job_order_material_issues i
                JOIN items it ON i.item_id = it.id
                LEFT JOIN units u ON i.unit_id = u.id
                LEFT JOIN warehouses w ON i.issued_from_warehouse_id = w.id
                WHERE i.job_order_id = ?
            """, (self.job_order_id,)).fetchall()
            self.table.setRowCount(len(rows))
            for row, rec in enumerate(rows):
                self.table.setItem(row, 0, QTableWidgetItem(str(rec["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(rec["item_name_ar"]))
                self.table.setItem(row, 2, QTableWidgetItem(str(rec["quantity_issued"])))
                self.table.setItem(row, 3, QTableWidgetItem(rec["unit_name"] or ""))
                self.table.setItem(row, 4, QTableWidgetItem(str(rec["total_cost"] or 0)))
                self.table.setItem(row, 5, QTableWidgetItem(rec["warehouse_name"] or ""))
                self.table.setItem(row, 6, QTableWidgetItem(rec["consumption_status"]))
                self.table.setItem(row, 7, QTableWidgetItem(rec["issued_date"]))
                self.table.setItem(row, 8, QTableWidgetItem(rec["notes"] or ""))
        finally:
            conn.close()

    def add_issue(self):
        if not self.job_order_id:
            QMessageBox.warning(self, "⚠️", "لا يوجد أمر تشغيل محدد")
            return
        item_name = self.item_input.text().strip()
        quantity = self.quantity_input.value()
        unit_id = self.unit_combo.currentData()
        notes = self.notes_input.text()

        conn = get_inventory_db_connection()
        if not conn: return
        try:
            item = conn.execute("SELECT id FROM items WHERE item_name_ar LIKE ? LIMIT 1", (f"%{item_name}%",)).fetchone()
            warehouse = conn.execute("SELECT id FROM warehouses WHERE name_ar LIKE ? LIMIT 1", (f"%{self.warehouse_input.text()}%",)).fetchone()
            if not item or not warehouse:
                QMessageBox.warning(self, "⚠️", "الصنف أو المخزن غير موجود")
                return
            conn.execute("""
                INSERT INTO job_order_material_issues
                (job_order_id, material_requirement_id, item_id, quantity_issued, unit_id,
                 issued_by_external_id, issued_from_warehouse_id, notes, created_at)
                VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?)
            """, (self.job_order_id, item["id"], quantity, unit_id, "user1", warehouse["id"], notes,
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            QMessageBox.information(self, "✅", "تم الإصدار")
            self.load_issues()
        finally:
            conn.close()

    def delete_issue(self):
        if not self.current_issue_id:
            QMessageBox.warning(self, "⚠️", "اختر إصدار أولاً")
            return
        reply = QMessageBox.question(self, "تأكيد", "هل تريد حذف الإصدار؟", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = get_inventory_db_connection()
            if not conn: return
            try:
                conn.execute("DELETE FROM job_order_material_issues WHERE id = ?", (self.current_issue_id,))
                conn.commit()
                self.load_issues()
            finally:
                conn.close()

    def on_issue_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            self.current_issue_id = None
            return
        self.current_issue_id = int(self.table.item(selected[0].row(), 0).text())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JobOrderMaterialIssues_UI(job_order_id=1)
    window.show()
    sys.exit(app.exec_())

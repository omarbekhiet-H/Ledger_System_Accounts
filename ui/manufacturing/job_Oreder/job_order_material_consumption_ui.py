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


class JobOrderMaterialConsumption_UI(QWidget):
    def __init__(self, job_order_id=None):
        super().__init__()
        self.job_order_id = job_order_id
        self.current_cons_id = None
        self.initUI()
        self.load_consumption()

    def initUI(self):
        self.setWindowTitle("إدارة استهلاك المواد - أوامر التشغيل")
        self.setGeometry(200, 200, 1200, 800)
        layout = QVBoxLayout(self)

        title = QLabel("🔥 استهلاك المواد")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #B71C1C;")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "الصنف", "كمية مستخدمة", "الوحدة", "الهالك", "من العملية",
            "المركز", "الجودة", "تاريخ", "ملاحظات"
        ])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemSelectionChanged.connect(self.on_consumption_selected)
        layout.addWidget(self.table)

        form_group = QGroupBox("➕ تسجيل استهلاك")
        form_layout = QGridLayout(form_group)

        form_layout.addWidget(QLabel("الصنف:"), 0, 0)
        self.item_input = QLineEdit()
        form_layout.addWidget(self.item_input, 0, 1)

        form_layout.addWidget(QLabel("كمية مستخدمة:"), 0, 2)
        self.used_input = QDoubleSpinBox()
        self.used_input.setRange(0.1, 100000)
        form_layout.addWidget(self.used_input, 0, 3)

        form_layout.addWidget(QLabel("الوحدة:"), 1, 0)
        self.unit_combo = QComboBox()
        self.load_units()
        form_layout.addWidget(self.unit_combo, 1, 1)

        form_layout.addWidget(QLabel("الهالك:"), 1, 2)
        self.scrap_input = QDoubleSpinBox()
        self.scrap_input.setRange(0, 10000)
        form_layout.addWidget(self.scrap_input, 1, 3)

        form_layout.addWidget(QLabel("الملاحظات:"), 2, 0)
        self.notes_input = QLineEdit()
        form_layout.addWidget(self.notes_input, 2, 1, 1, 3)

        add_btn = QPushButton("➕ إضافة")
        add_btn.clicked.connect(self.add_consumption)
        form_layout.addWidget(add_btn, 3, 0, 1, 4)

        layout.addWidget(form_group)

        button_layout = QHBoxLayout()
        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.clicked.connect(self.delete_consumption)
        button_layout.addWidget(self.delete_btn)

        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.clicked.connect(self.load_consumption)
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

    def load_consumption(self):
        if not self.job_order_id: return
        conn = get_inventory_db_connection()
        if not conn: return
        try:
            rows = conn.execute("""
                SELECT c.id, it.item_name_ar, c.quantity_used, u.name_ar as unit_name,
                       c.quantity_scrapped, c.operation_number, c.work_center,
                       c.quality_status, c.consumed_date, c.notes
                FROM job_order_material_consumption c
                JOIN items it ON c.item_id = it.id
                LEFT JOIN units u ON c.unit_id = u.id
                WHERE c.job_order_id = ?
            """, (self.job_order_id,)).fetchall()
            self.table.setRowCount(len(rows))
            for row, rec in enumerate(rows):
                self.table.setItem(row, 0, QTableWidgetItem(str(rec["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(rec["item_name_ar"]))
                self.table.setItem(row, 2, QTableWidgetItem(str(rec["quantity_used"])))
                self.table.setItem(row, 3, QTableWidgetItem(rec["unit_name"] or ""))
                self.table.setItem(row, 4, QTableWidgetItem(str(rec["quantity_scrapped"] or 0)))
                self.table.setItem(row, 5, QTableWidgetItem(rec["operation_number"] or ""))
                self.table.setItem(row, 6, QTableWidgetItem(rec["work_center"] or ""))
                self.table.setItem(row, 7, QTableWidgetItem(rec["quality_status"] or ""))
                self.table.setItem(row, 8, QTableWidgetItem(rec["consumed_date"]))
                self.table.setItem(row, 9, QTableWidgetItem(rec["notes"] or ""))
        finally:
            conn.close()

    def add_consumption(self):
        if not self.job_order_id:
            QMessageBox.warning(self, "⚠️", "لا يوجد أمر تشغيل محدد")
            return
        item_name = self.item_input.text().strip()
        used_qty = self.used_input.value()
        unit_id = self.unit_combo.currentData()
        scrap = self.scrap_input.value()
        notes = self.notes_input.text()

        conn = get_inventory_db_connection()
        if not conn: return
        try:
            item = conn.execute("SELECT id FROM items WHERE item_name_ar LIKE ? LIMIT 1", (f"%{item_name}%",)).fetchone()
            if not item:
                QMessageBox.warning(self, "⚠️", "لم يتم العثور على الصنف")
                return
            conn.execute("""
                INSERT INTO job_order_material_consumption
                (job_order_id, item_id, quantity_used, unit_id, quantity_scrapped,
                 quality_status, consumed_date, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.job_order_id, item["id"], used_qty, unit_id, scrap, "accepted",
                  datetime.now().strftime("%Y-%m-%d"), notes,
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            QMessageBox.information(self, "✅", "تم التسجيل")
            self.load_consumption()
        finally:
            conn.close()

    def delete_consumption(self):
        if not self.current_cons_id:
            QMessageBox.warning(self, "⚠️", "اختر استهلاك أولاً")
            return
        reply = QMessageBox.question(self, "تأكيد", "هل تريد حذف السجل؟", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = get_inventory_db_connection()
            if not conn: return
            try:
                conn.execute("DELETE FROM job_order_material_consumption WHERE id = ?", (self.current_cons_id,))
                conn.commit()
                self.load_consumption()
            finally:
                conn.close()

    def on_consumption_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            self.current_cons_id = None
            return
        self.current_cons_id = int(self.table.item(selected[0].row(), 0).text())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JobOrderMaterialConsumption_UI(job_order_id=1)
    window.show()
    sys.exit(app.exec_())

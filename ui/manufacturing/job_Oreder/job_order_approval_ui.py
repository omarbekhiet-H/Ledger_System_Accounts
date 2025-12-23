# job_order_approval_ui.py
import sys, os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QGroupBox,
    QHeaderView, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor



# --- إعداد المسارات ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)
from database.db_connection import get_manufacturing_db_connection, get_inventory_db_connection


class JobOrderApprovalUI(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_order_id = None
        self.initUI()
        self.load_orders()

    def initUI(self):
        self.setWindowTitle("📋 اعتماد أوامر التشغيل")
        self.setGeometry(200, 200, 1150, 780)
        self.setLayoutDirection(Qt.RightToLeft)

        layout = QVBoxLayout(self)

        # --- رأس التقرير ---
        header_widget = QFrame()
        header_widget.setStyleSheet("background-color: #007ACC; padding: 14px; border-radius: 8px;")
        header_inner = QHBoxLayout(header_widget)

        self.header_label = QLabel("📋 شاشة اعتماد أوامر التشغيل")
        self.header_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.header_label.setStyleSheet("color: white;")
        self.header_label.setAlignment(Qt.AlignCenter)

        self.date_label = QLabel("📅 ")
        self.date_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.date_label.setStyleSheet("color: white;")
        self.date_label.setAlignment(Qt.AlignRight)

        header_inner.addWidget(self.header_label, stretch=2)
        header_inner.addWidget(self.date_label, stretch=1)
        layout.addWidget(header_widget)

        # --- جدول أوامر التشغيل المعلقة ---
        orders_group = QGroupBox("📝 أوامر التشغيل المعلقة")
        orders_layout = QVBoxLayout(orders_group)

        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(4)
        self.orders_table.setHorizontalHeaderLabels(["رقم الأمر", "عدد الأصناف", "تاريخ الطلب", "تاريخ الاعتماد"])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.orders_table.itemSelectionChanged.connect(self.on_order_selected)

        self.style_table(self.orders_table)
        orders_layout.addWidget(self.orders_table)
        layout.addWidget(orders_group)

        # --- جدول تفاصيل المواد ---
        details_group = QGroupBox("📦 تفاصيل المتطلبات")
        details_layout = QVBoxLayout(details_group)

        self.details_table = QTableWidget()
        self.details_table.setColumnCount(7)
        self.details_table.setHorizontalHeaderLabels([
            "كود الصنف", "اسم الصنف", "الكمية", "الوحدة",
            "الأولوية", "تاريخ الطلب", "تاريخ الاعتماد"
        ])
        self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.style_table(self.details_table)
        details_layout.addWidget(self.details_table)
        layout.addWidget(details_group)

        # --- خط فاصل ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #aaa; margin: 8px;")
        layout.addWidget(line)

        # --- أزرار التحكم ---
        buttons_layout = QHBoxLayout()

        self.approve_btn = QPushButton("✅ اعتماد")
        self.approve_btn.setStyleSheet(self.button_style("#28a745", "white"))
        self.approve_btn.clicked.connect(self.approve_order)
        buttons_layout.addWidget(self.approve_btn)

        self.reject_btn = QPushButton("❌ رفض")
        self.reject_btn.setStyleSheet(self.button_style("#dc3545", "white"))
        self.reject_btn.clicked.connect(self.reject_order)
        buttons_layout.addWidget(self.reject_btn)

        self.return_btn = QPushButton("🔄 إرجاع للتصحيح")
        self.return_btn.setStyleSheet(self.button_style("#ffc107", "black"))
        self.return_btn.clicked.connect(self.return_for_correction)
        buttons_layout.addWidget(self.return_btn)

        layout.addLayout(buttons_layout)

    # ------------------ تنسيق الجداول ------------------
    def style_table(self, table):
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #444;
                font-size: 14px;
                alternate-background-color: #f9f9f9;
                background-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                font-weight: bold;
                font-size: 14px;
                padding: 6px;
                border: 1px solid #aaa;
            }
        """)
        table.setFont(QFont("Arial", 12))
        table.horizontalHeader().setFont(QFont("Arial", 12, QFont.Bold))
        table.verticalHeader().setVisible(False)

    # ------------------ تنسيق الأزرار ------------------
    def button_style(self, bg_color, text_color):
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                padding: 10px 18px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #333;
                color: white;
            }}
        """

    # ------------------ تحميل أوامر التشغيل (pending فقط) ------------------
    def load_orders(self):
        conn = get_manufacturing_db_connection()
        if not conn:
            return
        try:
            rows = conn.execute("""
                SELECT job_order_id,
                       COUNT(*) as items_count,
                       MIN(required_date) as req_date,
                       MAX(approved_date) as app_date
                FROM job_order_material_requirements
                WHERE status = 'pending'
                GROUP BY job_order_id
                ORDER BY job_order_id DESC
            """).fetchall()

            self.orders_table.setRowCount(0)
            for r in rows:
                row = self.orders_table.rowCount()
                self.orders_table.insertRow(row)
                self.orders_table.setItem(row, 0, QTableWidgetItem(str(r["job_order_id"])))
                self.orders_table.setItem(row, 1, QTableWidgetItem(str(r["items_count"])))
                self.orders_table.setItem(row, 2, QTableWidgetItem(r["req_date"] if r["req_date"] else ""))
                self.orders_table.setItem(row, 3, QTableWidgetItem(r["app_date"] if r["app_date"] else ""))
        finally:
            conn.close()

    # ------------------ عند اختيار أمر تشغيل ------------------
    def on_order_selected(self):
        row = self.orders_table.currentRow()
        if row < 0:
            return
        id_cell = self.orders_table.item(row, 0)
        date_cell = self.orders_table.item(row, 2)
        if not id_cell:
            return

        self.selected_order_id = int(id_cell.text())
        self.date_label.setText(f"📅 تاريخ الطلب: {date_cell.text() if date_cell else ''}")
        self.load_order_details(self.selected_order_id)

    # ------------------ تحميل تفاصيل المواد ------------------
    def load_order_details(self, order_id):
        conn_man = get_manufacturing_db_connection()
        conn_inv = get_inventory_db_connection()
        if not conn_man or not conn_inv:
            return
        try:
            rows = conn_man.execute("""
                SELECT item_id, quantity_required, unit_id, priority, required_date, approved_at
                FROM job_order_material_requirements
                WHERE job_order_id = ? AND status = 'pending'
            """, (order_id,)).fetchall()

            self.details_table.setRowCount(0)
            for r in rows:
                item = conn_inv.execute("SELECT item_code, item_name_ar FROM items WHERE id = ?", (r["item_id"],)).fetchone()
                unit = conn_inv.execute("SELECT name_ar FROM units WHERE id = ?", (r["unit_id"],)).fetchone()

                row = self.details_table.rowCount()
                self.details_table.insertRow(row)
                vals = [
                    item["item_code"] if item else "",
                    item["item_name_ar"] if item else "",
                    str(r["quantity_required"]),
                    unit["name_ar"] if unit else "",
                    r["priority"],
                    r["required_date"] or "",
                    r["approved_date"] or ""
                ]
                for col, val in enumerate(vals):
                    cell = QTableWidgetItem(val)
                    cell.setTextAlignment(Qt.AlignCenter)
                    cell.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    self.details_table.setItem(row, col, cell)

                # 🎨 تلوين الصف حسب الأولوية
                if r["priority"] == "عالية":
                    color = QColor(255, 200, 200)  # أحمر فاتح
                elif r["priority"] == "متوسطة":
                    color = QColor(255, 255, 200)  # أصفر فاتح
                else:
                    color = QColor(200, 255, 200)  # أخضر فاتح

                for col in range(self.details_table.columnCount()):
                    self.details_table.item(row, col).setBackground(color)

        finally:
            conn_man.close()
            conn_inv.close()

    # ------------------ اعتماد ------------------
    def approve_order(self):
        if not self.selected_order_id:
            return
        conn = get_manufacturing_db_connection()
        try:
            conn.execute("""
                UPDATE job_order_material_requirements
                SET status = 'reserved', approved_date = ?
                WHERE job_order_id = ? AND status = 'pending'
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.selected_order_id))
            conn.commit()
            QMessageBox.information(self, "تم", "✅ تم اعتماد أمر التشغيل.")
            self.load_orders()
            self.details_table.setRowCount(0)
        finally:
            conn.close()

    # ------------------ رفض ------------------
    def reject_order(self):
        if not self.selected_order_id:
            return
        conn = get_manufacturing_db_connection()
        try:
            conn.execute("""
                UPDATE job_order_material_requirements
                SET status = 'cancelled'
                WHERE job_order_id = ? AND status = 'pending'
            """, (self.selected_order_id,))
            conn.commit()
            QMessageBox.warning(self, "تم", "❌ تم رفض أمر التشغيل.")
            self.load_orders()
            self.details_table.setRowCount(0)
        finally:
            conn.close()

    # ------------------ إرجاع للتصحيح ------------------
    def return_for_correction(self):
        if not self.selected_order_id:
            return
        conn = get_manufacturing_db_connection()
        try:
            conn.execute("""
                UPDATE job_order_material_requirements
                SET status = 'correction'
                WHERE job_order_id = ? AND status = 'pending'
            """, (self.selected_order_id,))
            conn.commit()
            QMessageBox.information(self, "تم", "🔄 تم إرجاع الأمر للتصحيح.")
            self.load_orders()
            self.details_table.setRowCount(0)
        finally:
            conn.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JobOrderApprovalUI()
    window.show()
    sys.exit(app.exec_())

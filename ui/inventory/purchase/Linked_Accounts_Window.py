# -*- coding: utf-8 -*-
import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QComboBox, QTabWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon


class AccountLinkWindow(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.setWindowTitle("🔗 ربط الحسابات مع الموديولات")
        self.setWindowIcon(QIcon("link_icon.png"))
        self.resize(1200, 700)
        self.setLayoutDirection(Qt.RightToLeft)  # واجهة عربية

        # واجهة المستخدم
        self.setup_ui()
        self.load_accounts()
        self.load_module_items()

    # ----------------------------------------------------------------------
    # UI
    # ----------------------------------------------------------------------
    def setup_ui(self):
        layout = QVBoxLayout(self)

        # ---------------- اختيار الحساب والموديول ----------------
        top_layout = QHBoxLayout()
        self.account_combo = QComboBox()
        self.module_combo = QComboBox()
        self.module_combo.addItems(["موردين", "عملاء", "أصول ثابتة"])
        self.relation_combo = QComboBox()
        self.relation_combo.addItems(["main", "extra", "tax", "guarantee", "other"])

        lbl_style = "font-weight:bold; color:#333;"

        lbl_acc = QLabel("الحساب:")
        lbl_acc.setStyleSheet(lbl_style)
        top_layout.addWidget(lbl_acc)
        top_layout.addWidget(self.account_combo)

        lbl_mod = QLabel("الموديول:")
        lbl_mod.setStyleSheet(lbl_style)
        top_layout.addWidget(lbl_mod)
        top_layout.addWidget(self.module_combo)

        lbl_rel = QLabel("نوع العلاقة:")
        lbl_rel.setStyleSheet(lbl_style)
        top_layout.addWidget(lbl_rel)
        top_layout.addWidget(self.relation_combo)

        layout.addLayout(top_layout)

        # ---------------- التبويبات ----------------
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # تبويب اختيار العناصر
        select_tab = QWidget()
        select_layout = QVBoxLayout(select_tab)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["اختيار", "ID", "الاسم", "كود الحساب"])
        self.items_table.setColumnHidden(1, True)
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setStyleSheet("alternate-background-color: #f9f9f9;")
        self.items_table.horizontalHeader().setStyleSheet(
            "QHeaderView::section { background-color:#1976D2; color:white; font-weight:bold; }"
        )
        select_layout.addWidget(self.items_table)

        btns = QHBoxLayout()
        self.check_all_btn = QPushButton("✅ اختيار الكل")
        self.check_all_btn.setStyleSheet(
            "QPushButton {background-color:#2196F3; color:white; border-radius:6px; padding:8px;}"
            "QPushButton:hover {background-color:#1976D2;}"
        )
        self.check_all_btn.clicked.connect(self.select_all)

        self.save_btn = QPushButton("💾 حفظ الربط")
        self.save_btn.setStyleSheet(
            "QPushButton {background-color:#4CAF50; color:white; border-radius:6px; padding:8px; font-weight:bold;}"
            "QPushButton:hover {background-color:#45a049;}"
        )
        self.save_btn.clicked.connect(self.save_links)

        btns.addWidget(self.check_all_btn)
        btns.addStretch()
        btns.addWidget(self.save_btn)
        select_layout.addLayout(btns)

        self.tabs.addTab(select_tab, "📋 اختيار العناصر")

        # تبويب عرض العلاقات الحالية
        links_tab = QWidget()
        links_layout = QVBoxLayout(links_tab)

        self.links_table = QTableWidget()
        self.links_table.setColumnCount(5)
        self.links_table.setHorizontalHeaderLabels(["ID", "العنصر", "كود الحساب", "اسم الحساب", "نوع العلاقة"])
        self.links_table.setColumnHidden(0, True)
        self.links_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.links_table.setAlternatingRowColors(True)
        self.links_table.setStyleSheet("alternate-background-color: #f2f2f2;")
        self.links_table.horizontalHeader().setStyleSheet(
            "QHeaderView::section { background-color:#1976D2; color:white; font-weight:bold; }"
        )
        links_layout.addWidget(self.links_table)

        links_btns = QHBoxLayout()
        self.delete_btn = QPushButton("🗑️ حذف العلاقة المحددة")
        self.delete_btn.setStyleSheet(
            "QPushButton {background-color:#F44336; color:white; border-radius:6px; padding:8px;}"
            "QPushButton:hover {background-color:#d32f2f;}"
        )
        self.delete_btn.clicked.connect(self.delete_link)
        links_btns.addStretch()
        links_btns.addWidget(self.delete_btn)
        links_layout.addLayout(links_btns)

        self.tabs.addTab(links_tab, "🔗 العلاقات الحالية")

        # تحميل العناصر عند تغيير الموديول أو الحساب
        self.module_combo.currentIndexChanged.connect(self.load_module_items)
        self.account_combo.currentIndexChanged.connect(self.load_module_items)

    # ----------------------------------------------------------------------
    # تحميل الحسابات
    # ----------------------------------------------------------------------
    def load_accounts(self):
        self.account_combo.clear()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("ATTACH DATABASE 'database/financials.db' AS fin;")
            cur = conn.cursor()
            cur.execute("""
                SELECT id, acc_code, account_name_ar
                FROM fin.accounts
                WHERE is_active = 1 AND is_final = 1
                ORDER BY acc_code
            """)
            for row in cur.fetchall():
                display = f"{row[1]} - {row[2]}"
                self.account_combo.addItem(display, row[0])

    # ----------------------------------------------------------------------
    # التحقق من وجود جدول
    # ----------------------------------------------------------------------
    def table_exists(self, table_name):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            return cur.fetchone() is not None

    # ----------------------------------------------------------------------
    # جلب IDs المرتبطة
    # ----------------------------------------------------------------------
    def get_linked_items(self, module, account_id):
        if module == "موردين":
            link_table, field = "supplier_accounts", "supplier_id"
        elif module == "عملاء":
            link_table, field = "customer_accounts", "customer_id"
        elif module == "أصول ثابتة":
            link_table, field = "asset_accounts", "asset_id"
        else:
            return set()

        if not self.table_exists(link_table):
            return set()

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT {field} FROM {link_table} WHERE account_id=?", (account_id,))
            return {row[0] for row in cur.fetchall()}

    # ----------------------------------------------------------------------
    # تحميل العناصر حسب الموديول
    # ----------------------------------------------------------------------
    def load_module_items(self):
        module = self.module_combo.currentText()
        account_id = self.account_combo.currentData()
        linked_ids = self.get_linked_items(module, account_id) if account_id else set()

        if module == "موردين":
            query = """
                SELECT s.id, s.name_ar AS name, a.acc_code
                FROM suppliers s
                LEFT JOIN supplier_accounts sa ON sa.supplier_id = s.id
                LEFT JOIN fin.accounts a ON sa.account_id = a.id
                WHERE s.is_active=1
                ORDER BY s.name_ar
            """
        elif module == "عملاء":
            query = """
                SELECT c.id, c.name_ar AS name, a.acc_code
                FROM customers c
                LEFT JOIN customer_accounts ca ON ca.customer_id = c.id
                LEFT JOIN fin.accounts a ON ca.account_id = a.id
                WHERE c.is_active=1
                ORDER BY c.name_ar
            """
        elif module == "أصول ثابتة":
            query = """
                SELECT f.id, f.asset_name AS name, a.acc_code
                FROM fixed_assets f
                LEFT JOIN asset_accounts fa ON fa.asset_id = f.id
                LEFT JOIN fin.accounts a ON fa.account_id = a.id
                WHERE f.is_active=1
                ORDER BY f.asset_name
            """
        else:
            query = ""

        self.items_table.setRowCount(0)
        if not query:
            return

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("ATTACH DATABASE 'database/financials.db' AS fin;")
            cur.execute(query)
            for r, row in enumerate(cur.fetchall()):
                self.items_table.insertRow(r)
                chk = QTableWidgetItem()
                chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                chk.setCheckState(Qt.Checked if row["id"] in linked_ids else Qt.Unchecked)
                self.items_table.setItem(r, 0, chk)
                self.items_table.setItem(r, 1, QTableWidgetItem(str(row["id"])))
                self.items_table.setItem(r, 2, QTableWidgetItem(row["name"]))
                self.items_table.setItem(r, 3, QTableWidgetItem(row["acc_code"] if row["acc_code"] else ""))

        self.show_links()


    # ----------------------------------------------------------------------
    # اختيار الكل
    # ----------------------------------------------------------------------
    def select_all(self):
        all_checked = all(self.items_table.item(r, 0).checkState() == Qt.Checked
                          for r in range(self.items_table.rowCount()))
        new_state = Qt.Unchecked if all_checked else Qt.Checked
        for r in range(self.items_table.rowCount()):
            self.items_table.item(r, 0).setCheckState(new_state)

    # ----------------------------------------------------------------------
    # حفظ الربط
    # ----------------------------------------------------------------------
    def save_links(self):
        account_id = self.account_combo.currentData()
        relation = self.relation_combo.currentText()
        module = self.module_combo.currentText()

        if not account_id:
            QMessageBox.warning(self, "تنبيه", "اختر الحساب أولاً")
            return

        if module == "موردين":
            link_table, field = "supplier_accounts", "supplier_id"
        elif module == "عملاء":
            link_table, field = "customer_accounts", "customer_id"
        elif module == "أصول ثابتة":
            link_table, field = "asset_accounts", "asset_id"
        else:
            QMessageBox.warning(self, "خطأ", "موديول غير معروف")
            return

        if not self.table_exists(link_table):
            QMessageBox.warning(self, "خطأ", f"الجدول {link_table} غير موجود في قاعدة البيانات")
            return

        saved_count, skipped = 0, 0
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            for r in range(self.items_table.rowCount()):
                if self.items_table.item(r, 0).checkState() == Qt.Checked:
                    item_id = int(self.items_table.item(r, 1).text())
                    # تحقق من وجود العلاقة
                    cur.execute(f"SELECT 1 FROM {link_table} WHERE {field}=? AND account_id=?", (item_id, account_id))
                    if cur.fetchone():
                        skipped += 1
                        continue
                    cur.execute(f"""
                        INSERT INTO {link_table} ({field}, account_id, relation_type)
                        VALUES (?, ?, ?)
                    """, (item_id, account_id, relation))
                    saved_count += 1
            conn.commit()

        msg = f"تم ربط {saved_count} عنصر جديد."
        if skipped:
            msg += f"\n{skipped} عنصر كان مرتبط بالفعل."
        QMessageBox.information(self, "تم", msg)

        self.show_links()
        self.load_module_items()

    # ----------------------------------------------------------------------
    # عرض العلاقات الحالية
    # ----------------------------------------------------------------------
    def show_links(self):
        module = self.module_combo.currentText()
        account_id = self.account_combo.currentData()
        if not account_id:
            return

        if module == "موردين":
            link_table, field, name_field, base_table = "supplier_accounts", "supplier_id", "name_ar", "suppliers"
        elif module == "عملاء":
            link_table, field, name_field, base_table = "customer_accounts", "customer_id", "name_ar", "customers"
        elif module == "أصول ثابتة":
            link_table, field, name_field, base_table = "asset_accounts", "asset_id", "asset_name", "fixed_assets"
        else:
            return

        if not self.table_exists(link_table):
            return

        self.links_table.setRowCount(0)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("ATTACH DATABASE 'database/financials.db' AS fin;")
            cur = conn.cursor()
            cur.execute(f"""
                SELECT sa.id AS link_id, s.{name_field} AS item_name,
                       a.acc_code, a.account_name_ar, sa.relation_type
                FROM {link_table} sa
                JOIN {base_table} s ON sa.{field} = s.id
                JOIN fin.accounts a ON sa.account_id = a.id
                WHERE sa.account_id = ?
                ORDER BY s.{name_field}
            """, (account_id,))
            for r, row in enumerate(cur.fetchall()):
                self.links_table.insertRow(r)
                self.links_table.setItem(r, 0, QTableWidgetItem(str(row["link_id"])))
                self.links_table.setItem(r, 1, QTableWidgetItem(row["item_name"]))
                self.links_table.setItem(r, 2, QTableWidgetItem(row["acc_code"]))
                self.links_table.setItem(r, 3, QTableWidgetItem(row["account_name_ar"]))
                self.links_table.setItem(r, 4, QTableWidgetItem(row["relation_type"]))

    # ----------------------------------------------------------------------
    # حذف العلاقة
    # ----------------------------------------------------------------------
    def delete_link(self):
        row = self.links_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "اختر علاقة أولاً")
            return

        link_id = int(self.links_table.item(row, 0).text())
        module = self.module_combo.currentText()

        if module == "موردين":
            link_table = "supplier_accounts"
        elif module == "عملاء":
            link_table = "customer_accounts"
        elif module == "أصول ثابتة":
            link_table = "asset_accounts"
        else:
            return

        if not self.table_exists(link_table):
            QMessageBox.warning(self, "خطأ", f"الجدول {link_table} غير موجود")
            return

        reply = QMessageBox.question(
            self, "تأكيد الحذف", "هل أنت متأكد أنك تريد حذف العلاقة المحددة؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(f"DELETE FROM {link_table} WHERE id=?", (link_id,))
                conn.commit()

            QMessageBox.information(self, "تم", "تم حذف العلاقة بنجاح")
            self.show_links()
            self.load_module_items()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Tahoma", 11)
    app.setFont(font)
    window = AccountLinkWindow("database/inventory.db")
    window.show()
    sys.exit(app.exec_())

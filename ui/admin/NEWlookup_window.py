import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QLineEdit, QLabel, QFormLayout, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from database.manager.admin.NEWlookup_manager import NEWLookupManager as LookupManager
except ImportError:
    class LookupManager:
        def get_all_lookups(self): return []
        def get_lookup_by_id(self, id): return None
        def create_lookup(self, *a, **k): return False, "فشل"
        def update_lookup(self, *a, **k): return False, "فشل"
        def delete_lookup(self, *a, **k): return False, "فشل"

class LookupWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lookup_manager = LookupManager()
        self.initUI()
        self.load_styles() # تحميل التنسيقات
        self.load_lookups()
    
    def initUI(self):
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle("إدارة القيم المرجعية (Lookup)")
        self.resize(750, 500)

        layout = QVBoxLayout(self)

        # 🔎 البحث
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث عن قيمة أو فئة...")
        search_btn = QPushButton("بحث")
        search_btn.setObjectName("searchButton")
        search_btn.clicked.connect(self.search_lookup)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)

        # 📋 الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "القيمة", "الوصف", "الفئة"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        # 🔘 الأزرار
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("➕ إضافة")
        add_btn.setObjectName("saveButton")
        add_btn.clicked.connect(self.add_lookup)

        edit_btn = QPushButton("✏️ تعديل")
        edit_btn.setObjectName("updateButton")
        edit_btn.clicked.connect(self.edit_lookup)

        delete_btn = QPushButton("❌ حذف")
        delete_btn.setObjectName("deleteButton")
        delete_btn.clicked.connect(self.delete_lookup)

        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setObjectName("clearButton")
        refresh_btn.clicked.connect(self.load_lookups)
        
        close_btn = QPushButton("إغلاق")
        close_btn.setObjectName("deleteButton") # لتطبيق اللون الأحمر
        close_btn.clicked.connect(self.close)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch(1)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def load_styles(self):
        """تحميل وتطبيق ملف التنسيق QSS"""
        try:
            style_path = os.path.join(os.path.dirname(__file__), '..', 'styles', 'styles.qss')
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Error loading QSS file: {e}")

    def load_lookups(self):
        lookups = self.lookup_manager.get_all_lookups() or []
        self.table.setRowCount(len(lookups))
        for row, lookup in enumerate(lookups):
            self.table.setItem(row, 0, QTableWidgetItem(str(lookup.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(lookup.get("value", "")))
            self.table.setItem(row, 2, QTableWidgetItem(lookup.get("description", "")))
            self.table.setItem(row, 3, QTableWidgetItem(lookup.get("category", "")))

    def get_selected_lookup_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار عنصر من الجدول")
            return None
        return int(self.table.item(row, 0).text())

    def search_lookup(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            self.load_lookups()
            return

        all_lookups = self.lookup_manager.get_all_lookups() or []
        filtered = [l for l in all_lookups if keyword.lower() in str(l).lower()]
        self.table.setRowCount(len(filtered))
        for row, lookup in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(str(lookup.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(lookup.get("value", "")))
            self.table.setItem(row, 2, QTableWidgetItem(lookup.get("description", "")))
            self.table.setItem(row, 3, QTableWidgetItem(lookup.get("category", "")))

    def add_lookup(self):
        dialog = LookupFormDialog(self.lookup_manager, parent=self)
        if dialog.exec_():
            self.load_lookups()

    def edit_lookup(self):
        lookup_id = self.get_selected_lookup_id()
        if not lookup_id:
            return
        dialog = LookupFormDialog(self.lookup_manager, lookup_id=lookup_id, parent=self)
        if dialog.exec_():
            self.load_lookups()

    def delete_lookup(self):
        lookup_id = self.get_selected_lookup_id()
        if not lookup_id:
            return
        confirm = QMessageBox.question(self, "تأكيد", "هل أنت متأكد من الحذف؟")
        if confirm == QMessageBox.Yes:
            success, msg = self.lookup_manager.delete_lookup(lookup_id)
            QMessageBox.information(self, "الحذف", msg)
            self.load_lookups()


class LookupFormDialog(QDialog):
    def __init__(self, lookup_manager, lookup_id=None, parent=None):
        super().__init__(parent)
        self.lookup_manager = lookup_manager
        self.lookup_id = lookup_id
        self.initUI()
        if lookup_id:
            self.load_lookup_data()

    def initUI(self):
        self.setWindowTitle("إضافة/تعديل قيمة مرجعية")
        self.resize(400, 250)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.value_input = QLineEdit()
        self.desc_input = QLineEdit()
        self.category_input = QLineEdit()

        form.addRow("القيمة:", self.value_input)
        form.addRow("الوصف:", self.desc_input)
        form.addRow("الفئة:", self.category_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_lookup)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_lookup_data(self):
        lookup = self.lookup_manager.get_lookup_by_id(self.lookup_id)
        if lookup:
            self.value_input.setText(lookup.get("value", ""))
            self.desc_input.setText(lookup.get("description", ""))
            self.category_input.setText(lookup.get("category", ""))

    def save_lookup(self):
        value = self.value_input.text().strip()
        desc = self.desc_input.text().strip()
        category = self.category_input.text().strip()

        if not value:
            QMessageBox.warning(self, "خطأ", "القيمة مطلوبة")
            return

        if self.lookup_id:
            success, msg = self.lookup_manager.update_lookup(
                self.lookup_id, value=value, description=desc, category=category
            )
        else:
            success, msg = self.lookup_manager.create_lookup(
                value=value, description=desc, category=category
            )

        if success:
            QMessageBox.information(self, "نجاح", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "خطأ", msg)
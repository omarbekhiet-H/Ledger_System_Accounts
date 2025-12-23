import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QLabel, QLineEdit, QHeaderView, QFormLayout, QCheckBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt

try:
    from database.manager.admin.NEWrole_manager import RoleManager
except Exception:
    class RoleManager:
        def get_all_roles(self): return []
        def create_role(self, *a, **k): return False, "غير مدعوم"
        def update_role(self, *a, **k): return False, "غير مدعوم"
        def delete_role(self, *a, **k): return False, "غير مدعوم"
        def toggle_role_status(self, *a, **k): return False, "غير مدعوم"

class RolesWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.role_manager = RoleManager()
        self._setup_ui()
        self.load_styles() # تم تغيير الاسم وتوحيده
        self.load_roles()

    def load_styles(self):
        # تم تصحيح المسار والاسم
        qss = os.path.join(os.path.dirname(__file__), '..', 'styles', 'styles.qss')
        try:
            with open(qss, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Failed to load styles: {e}")

    def _setup_ui(self):
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle("إدارة الأدوار")
        self.setMinimumSize(820, 520)
        root = QVBoxLayout(self)

        title = QLabel("إدارة الأدوار (Roles)")
        title.setObjectName("windowTitle")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("ابحث باسم الدور، الكود، الوصف…")
        self.search_edit.textChanged.connect(self.apply_filter)
        search_btn = QPushButton("بحث")
        search_btn.setObjectName("searchButton")
        search_btn.clicked.connect(self.apply_filter)
        clear_btn = QPushButton("مسح")
        clear_btn.setObjectName("clearButton")
        clear_btn.clicked.connect(self.clear_filter)
        search_row.addWidget(self.search_edit)
        search_row.addWidget(search_btn)
        search_row.addWidget(clear_btn)
        root.addLayout(search_row)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "كود الدور", "الاسم (عربي)", "الوصف", "الحالة"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        root.addWidget(self.table)

        btns = QHBoxLayout()
        add_btn = QPushButton("إضافة")
        add_btn.setObjectName("saveButton")
        add_btn.clicked.connect(self.add_role)

        edit_btn = QPushButton("تعديل")
        edit_btn.setObjectName("updateButton")
        edit_btn.clicked.connect(self.edit_role)

        toggle_btn = QPushButton("تفعيل/تعطيل")
        toggle_btn.setObjectName("clearButton")
        toggle_btn.clicked.connect(self.toggle_role)

        del_btn = QPushButton("حذف")
        del_btn.setObjectName("deleteButton")
        del_btn.clicked.connect(self.delete_role)
        
        close_btn = QPushButton("إغلاق")
        close_btn.setObjectName("deleteButton")
        close_btn.clicked.connect(self.close)

        btns.addWidget(add_btn)
        btns.addWidget(edit_btn)
        btns.addWidget(toggle_btn)
        btns.addWidget(del_btn)
        btns.addStretch(1)
        btns.addWidget(close_btn)
        root.addLayout(btns)

        self._all_rows_cache = []

    def load_roles(self):
        roles = self.role_manager.get_all_roles() or []
        self._all_rows_cache = roles[:]
        self._render_table(roles)

    def _render_table(self, rows):
        self.table.setRowCount(len(rows))
        for r, role in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(str(role.get("id", ""))))
            self.table.setItem(r, 1, QTableWidgetItem(role.get("role_code", "")))
            self.table.setItem(r, 2, QTableWidgetItem(role.get("name_ar", "") or role.get("name_en", "")))
            self.table.setItem(r, 3, QTableWidgetItem(role.get("description", "") or ""))
            self.table.setItem(r, 4, QTableWidgetItem("نشط" if role.get("is_active") else "معطل"))

    def apply_filter(self):
        txt = (self.search_edit.text() or "").strip().lower()
        if not txt:
            self._render_table(self._all_rows_cache)
            return
        filt = [r for r in self._all_rows_cache if txt in " ".join(str(r.get(k, "")) for k in ("role_code", "name_ar", "name_en", "description")).lower()]
        self._render_table(filt)

    def clear_filter(self):
        self.search_edit.clear()
        self._render_table(self._all_rows_cache)

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "اختر صفاً أولاً.")
            return None
        return int(self.table.item(row, 0).text())

    def add_role(self):
        dlg = _RoleFormDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            ok, msg = self.role_manager.create_role(
                dlg.role_code.text().strip(),
                dlg.name_ar.text().strip(),
                dlg.name_en.text().strip() or None,
                dlg.description.text().strip() or None,
                dlg.active_check.isChecked()
            )
            QMessageBox.information(self, "نتيجة", msg)
            if ok: self.load_roles()

    def edit_role(self):
        rid = self._selected_id()
        if not rid: return
        cur = next((r for r in self._all_rows_cache if r.get("id") == rid), None)
        if not cur:
            QMessageBox.warning(self, "تنبيه", "تعذر إيجاد الدور.")
            return

        dlg = _RoleFormDialog(current=cur, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            ok, msg = self.role_manager.update_role(
                rid,
                role_code=dlg.role_code.text().strip(),
                name_ar=dlg.name_ar.text().strip(),
                name_en=dlg.name_en.text().strip() or None,
                description=dlg.description.text().strip() or None,
                is_active=dlg.active_check.isChecked()
            )
            QMessageBox.information(self, "نتيجة", msg)
            if ok: self.load_roles()

    def toggle_role(self):
        rid = self._selected_id()
        if not rid: return
        ok, msg = self.role_manager.toggle_role_status(rid)
        QMessageBox.information(self, "نتيجة", msg)
        if ok: self.load_roles()

    def delete_role(self):
        rid = self._selected_id()
        if not rid: return
        if QMessageBox.question(self, "تأكيد", "هل تريد حذف هذا الدور؟") == QMessageBox.Yes:
            ok, msg = self.role_manager.delete_role(rid)
            QMessageBox.information(self, "حذف", msg)
            if ok: self.load_roles()


class _RoleFormDialog(QDialog):
    # ... (rest of the class is unchanged)
    def __init__(self, current=None, parent=None):
        super().__init__(parent)
        self._current = current
        self.setWindowTitle("إضافة دور" if current is None else "تعديل دور")
        self.setMinimumWidth(420)
        lay = QVBoxLayout(self)

        form = QFormLayout()
        self.role_code = QLineEdit()
        self.name_ar = QLineEdit()
        self.name_en = QLineEdit()
        self.description = QLineEdit()
        self.active_check = QCheckBox("نشط")

        form.addRow("كود الدور:", self.role_code)
        form.addRow("الاسم (عربي):", self.name_ar)
        form.addRow("الاسم (إنجليزي):", self.name_en)
        form.addRow("الوصف:", self.description)
        form.addRow("الحالة:", self.active_check)
        lay.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setObjectName("saveButton")
        btns.button(QDialogButtonBox.Cancel).setObjectName("deleteButton")
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

        if current:
            self.role_code.setText(current.get("role_code", ""))
            self.name_ar.setText(current.get("name_ar", "") or "")
            self.name_en.setText(current.get("name_en", "") or "")
            self.description.setText(current.get("description", "") or "")
            self.active_check.setChecked(bool(current.get("is_active", 1)))

    def _on_ok(self):
        if not self.role_code.text().strip() or not self.name_ar.text().strip():
            QMessageBox.warning(self, "تنبيه", "كود الدور والاسم العربي حقول إلزامية.")
            return
        self.accept()
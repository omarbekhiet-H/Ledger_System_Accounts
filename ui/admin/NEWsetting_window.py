import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QDialogButtonBox, QFormLayout, QCheckBox
)
from PyQt5.QtCore import Qt

try:
    from database.manager.admin.NEWsettings_manager import SettingManager
except Exception:
    class SettingManager:
        def get_all_settings(self): return []
        def upsert_setting(self, *a, **k): return False, "غير مدعوم"
        def delete_setting(self, *a, **k): return False, "غير مدعوم"

class SettingWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = SettingManager()
        self._setup()
        self.load_styles() # تم تغيير الاسم وتوحيده
        self.load_settings()

    def load_styles(self):
        # تم تصحيح المسار والاسم
        qss = os.path.join(os.path.dirname(__file__), '..', 'styles', 'styles.qss')
        try:
            with open(qss, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Failed to load styles: {e}")


    def _setup(self):
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle("إعدادات النظام")
        self.setMinimumSize(850, 520)
        root = QVBoxLayout(self)

        title = QLabel("إعدادات النظام (Settings)")
        title.setObjectName("windowTitle")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        # بحث وأزرار
        row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("بحث بالمفتاح/القيمة/الوصف...")
        self.search_edit.textChanged.connect(self.apply_filter)
        
        search_btn = QPushButton("بحث")
        search_btn.setObjectName("searchButton")
        search_btn.clicked.connect(self.apply_filter)

        clear_btn = QPushButton("مسح")
        clear_btn.setObjectName("clearButton")
        clear_btn.clicked.connect(self.clear_filter)

        row.addWidget(self.search_edit)
        row.addWidget(search_btn)
        row.addWidget(clear_btn)
        root.addLayout(row)

        # جدول
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "المفتاح", "القيمة", "الوصف", "الحالة"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        root.addWidget(self.table)
        
        # أزرار الإجراءات
        action_layout = QHBoxLayout()
        add_btn = QPushButton("إضافة")
        add_btn.setObjectName("saveButton")
        add_btn.clicked.connect(self.add_setting)

        edit_btn = QPushButton("تعديل")
        edit_btn.setObjectName("updateButton")
        edit_btn.clicked.connect(self.edit_setting)

        del_btn = QPushButton("حذف")
        del_btn.setObjectName("deleteButton")
        del_btn.clicked.connect(self.delete_setting)
        
        close_btn = QPushButton("إغلاق")
        close_btn.setObjectName("deleteButton") # لتطبيق اللون الأحمر
        close_btn.clicked.connect(self.close)
        
        action_layout.addWidget(add_btn)
        action_layout.addWidget(edit_btn)
        action_layout.addWidget(del_btn)
        action_layout.addStretch(1)
        action_layout.addWidget(close_btn)
        root.addLayout(action_layout)


        self._cache = []

    def load_settings(self):
        self._cache = self.manager.get_all_settings() or []
        self._render(self._cache)

    def _render(self, rows):
        self.table.setRowCount(len(rows))
        for i, s in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(s.get("id", ""))))
            self.table.setItem(i, 1, QTableWidgetItem(s.get("key", "") or s.get("setting_key","")))
            self.table.setItem(i, 2, QTableWidgetItem(s.get("value", "") or s.get("setting_value","")))
            self.table.setItem(i, 3, QTableWidgetItem(s.get("description", "") or ""))
            self.table.setItem(i, 4, QTableWidgetItem("نشط" if s.get("is_active", 1) else "معطل"))

    def apply_filter(self):
        txt = (self.search_edit.text() or "").lower().strip()
        if not txt:
            self._render(self._cache)
            return
        rows = [s for s in self._cache if txt in " ".join(str(s.get(k, "")) for k in ("key","setting_key","value","setting_value","description")).lower()]
        self._render(rows)

    def clear_filter(self):
        self.search_edit.clear()
        self._render(self._cache)

    def _selected_id(self):
        r = self.table.currentRow()
        if r < 0:
            QMessageBox.warning(self, "تنبيه", "اختر صفاً أولاً.")
            return None
        return int(self.table.item(r, 0).text())

    def add_setting(self):
        dlg = _SettingForm(self)
        if dlg.exec_() == QDialog.Accepted:
            ok, msg = self.manager.upsert_setting(
                key=dlg.key_edit.text().strip(),
                value=dlg.value_edit.text().strip(),
                description=dlg.desc_edit.text().strip() or None,
                is_active=dlg.active_check.isChecked()
            )
            QMessageBox.information(self, "نتيجة", msg)
            if ok: self.load_settings()

    def edit_setting(self):
        sid = self._selected_id()
        if not sid: return
        cur = next((x for x in self._cache if x.get("id")==sid), None)
        if not cur:
            QMessageBox.warning(self, "تنبيه", "غير موجود.")
            return
        dlg = _SettingForm(self, current=cur)
        if dlg.exec_() == QDialog.Accepted:
            ok, msg = self.manager.upsert_setting(
                id=sid,
                key=dlg.key_edit.text().strip(),
                value=dlg.value_edit.text().strip(),
                description=dlg.desc_edit.text().strip() or None,
                is_active=dlg.active_check.isChecked()
            )
            QMessageBox.information(self, "نتيجة", msg)
            if ok: self.load_settings()

    def delete_setting(self):
        sid = self._selected_id()
        if not sid: return
        if QMessageBox.question(self, "تأكيد", "حذف هذا الإعداد؟") == QMessageBox.Yes:
            ok, msg = self.manager.delete_setting(sid)
            QMessageBox.information(self, "حذف", msg)
            if ok: self.load_settings()


class _SettingForm(QDialog):
    # ... (rest of the class is unchanged)
    def __init__(self, parent=None, current=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة إعداد" if current is None else "تعديل إعداد")
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.key_edit = QLineEdit()
        self.value_edit = QLineEdit()
        self.desc_edit = QLineEdit()
        self.active_check = QCheckBox("نشط")

        form.addRow("المفتاح:", self.key_edit)
        form.addRow("القيمة:", self.value_edit)
        form.addRow("الوصف:", self.desc_edit)
        form.addRow("الحالة:", self.active_check)
        lay.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setObjectName("saveButton")
        btns.button(QDialogButtonBox.Cancel).setObjectName("deleteButton")
        btns.accepted.connect(self._ok)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

        if current:
            self.key_edit.setText(current.get("key", "") or current.get("setting_key",""))
            self.value_edit.setText(current.get("value", "") or current.get("setting_value",""))
            self.desc_edit.setText(current.get("description", "") or "")
            self.active_check.setChecked(bool(current.get("is_active", 1)))

    def _ok(self):
        if not self.key_edit.text().strip():
            QMessageBox.warning(self, "تنبيه", "المفتاح مطلوب.")
            return
        self.accept()
# -*- coding: utf-8 -*-
import sys
import sqlite3
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTreeView, QDialog, QFormLayout, QLineEdit,
    QComboBox, QMessageBox, QLabel, QAction, QMenu, QHeaderView, QCheckBox
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPalette, QColor
from PyQt5.QtCore import Qt, QSortFilterProxyModel

# ------------------------------------------------------------
# تهيئة مسارات المشروع
# ------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# ------------------------------------------------------------
# الاستيراد من المشروع مع بدائل آمنة
# ------------------------------------------------------------
try:
    from database.db_connection import get_financials_db_connection
except Exception as e:
    print(f"⚠️ get_financials_db_connection Import fallback: {e}")
    def get_financials_db_connection():
        # يرجّع None لتشغيل الواجهة حتى لو مفيش قاعدة بيانات جاهزة
        return None

try:
    from database.manager.db_schema_manager import DBSchemaManager
except Exception as e:
    print(f"⚠️ DBSchemaManager Import fallback: {e}")
    class DBSchemaManager:
        def initialize_specific_database(self, name):  # fallback no-op
            print(f"(fallback) Skipping schema init for {name}")

# ------------------------------------------------------------
# أدوات مساعدة
# ------------------------------------------------------------
def load_qss_file(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"⚠️ QSS not loaded from {file_path}: {e}")
        return ""

FALLBACK_QSS = """
/* ==== Base ==== */
QWidget {
    font-family: "Segoe UI", "Noto Sans Arabic", "Inter", "Arial", sans-serif;
    font-size: 10pt;
    color: #2C3E50;
    background-color: #ECF0F1;
}
QMainWindow { background-color: #FFFFFF; }

/* ==== Buttons ==== */
QPushButton {
    background-color: #3498DB; color: white; border: none; border-radius: 6px;
    padding: 6px 12px; font-weight: 600;
}
QPushButton:hover { background-color: #2874A6; }
QPushButton#deleteButton { background-color: #dc3545; }
QPushButton#deleteButton:hover { background-color: #c82333; }
QPushButton#closeButton { background-color: #6c757d; }
QPushButton#closeButton:hover { background-color: #5a6268; }
QPushButton#addButton    { background-color: #28a745; }
QPushButton#addButton:hover { background-color: #218838; }
QPushButton#editButton   { background-color: #ffc107; color: #2C3E50; }
QPushButton#editButton:hover { background-color: #e0a800; }
QPushButton#refreshButton { background-color: #17a2b8; }
QPushButton#refreshButton:hover { background-color: #138496; }

/* ==== TreeView ==== */
QTreeView {
    background: #ffffff;
    alternate-background-color: #F7F9FC;  /* الصفوف المتبادلة */
    border: 1px solid #D7DBDD;
    border-radius: 6px;
}
QHeaderView::section {
    background: #2874A6; color: white; padding: 6px; font-weight: 700;
    border: 1px solid #D7DBDD;
}
QTreeView::item:selected { background: #D6EAF8; color: #1B2631; }
QTreeView::branch:open:has-children { image: none; }
QTreeView::branch:closed:has-children { image: none; }

/* ==== Inputs ==== */
QLineEdit, QComboBox {
    background: #F8F9F9; border: 1px solid #BDC3C7; border-radius: 4px; padding: 4px 6px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #3498DB; background: #EBF5FB;
}
"""

# ------------------------------------------------------------
# إدارة قاعدة البيانات
# ------------------------------------------------------------
class AccountDBManager:
    def __init__(self):
        pass

    def _execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        conn = None
        try:
            conn = get_financials_db_connection()
            if conn is None:
                # تشغيل بدون قاعدة بيانات (عرض فقط)
                return [] if fetch_all else (None if fetch_one else True)

            cursor = conn.cursor()
            cursor.execute(query, params or [])
            conn.commit()

            if fetch_one:
                row = cursor.fetchone()
                if row:
                    columns = [d[0] for d in cursor.description]
                    return dict(zip(columns, row))
                return None
            if fetch_all:
                rows = cursor.fetchall()
                if rows:
                    columns = [d[0] for d in cursor.description]
                    return [dict(zip(columns, r)) for r in rows]
                return []
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ قاعدة البيانات", f"حدث خطأ: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_account_types(self):
        q = "SELECT id, name_ar, account_side FROM account_types WHERE is_active = 1 ORDER BY name_ar"
        return self._execute_query(q, fetch_all=True)

    def get_all_accounts(self):
        q = """
            SELECT a.id, a.acc_code, a.account_name_ar, a.account_name_en,
                   a.account_type_id, at.name_ar AS account_type_name, at.account_side,
                   a.parent_account_id, pa.account_name_ar AS parent_account_name,
                   a.level, a.is_balance_sheet, a.is_final, a.is_active
            FROM accounts a
            JOIN account_types at ON a.account_type_id = at.id
            LEFT JOIN accounts pa ON a.parent_account_id = pa.id
            ORDER BY a.acc_code
        """
        return self._execute_query(q, fetch_all=True)

    def get_accounts_by_type(self, account_type_id):
        q = """
            SELECT a.id, a.acc_code, a.account_name_ar, a.account_name_en,
                   a.account_type_id, at.name_ar AS account_type_name, at.account_side,
                   a.parent_account_id, pa.account_name_ar AS parent_account_name,
                   a.level, a.is_balance_sheet, a.is_final, a.is_active
            FROM accounts a
            JOIN account_types at ON a.account_type_id = at.id
            LEFT JOIN accounts pa ON a.parent_account_id = pa.id
            WHERE a.account_type_id = ?
            ORDER BY a.acc_code
        """
        return self._execute_query(q, (account_type_id,), fetch_all=True)

    def get_account_by_id(self, account_id):
        q = """
            SELECT id, acc_code, account_name_ar, account_name_en,
                   account_type_id, parent_account_id, level, is_balance_sheet, is_final, is_active
            FROM accounts WHERE id = ?
        """
        return self._execute_query(q, (account_id,), fetch_one=True)

    def get_account_by_code(self, acc_code):
        q = "SELECT id, acc_code FROM accounts WHERE acc_code = ?"
        return self._execute_query(q, (acc_code,), fetch_one=True)

    def get_max_child_acc_code(self, parent_account_id):
        if parent_account_id is None:
            q = "SELECT MAX(CAST(acc_code AS INTEGER)) AS max_code FROM accounts WHERE parent_account_id IS NULL"
            r = self._execute_query(q, fetch_one=True)
            return str(r['max_code']) if r and r.get('max_code') is not None else None
        parent = self.get_account_by_id(parent_account_id)
        if not parent:
            return None
        prefix = parent['acc_code']
        q = "SELECT acc_code FROM accounts WHERE parent_account_id = ?"
        rows = self._execute_query(q, (parent_account_id,), fetch_all=True) or []
        max_num, max_len = 0, 0
        for row in rows:
            code = row['acc_code']
            if code.startswith(prefix) and len(code) > len(prefix):
                suf = code[len(prefix):]
                if suf.isdigit():
                    n = int(suf)
                    if n > max_num:
                        max_num, max_len = n, len(suf)
        if max_num > 0:
            target_len = max(max_len, len(str(max_num)), 2)
            return prefix + str(max_num).zfill(target_len)
        return None

    def add_account(self, acc_code, name_ar, name_en, account_type_id, parent_account_id, level, is_balance_sheet, is_final, is_active):
        q = """
            INSERT INTO accounts
            (acc_code, account_name_ar, account_name_en, account_type_id, parent_account_id,
             level, is_balance_sheet, is_final, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        p = (acc_code, name_ar, name_en, account_type_id, parent_account_id, level, is_balance_sheet, is_final, is_active)
        return self._execute_query(q, p)

    def update_account(self, account_id, acc_code, name_ar, name_en, account_type_id, parent_account_id, level, is_balance_sheet, is_final, is_active):
        q = """
            UPDATE accounts SET
                acc_code=?, account_name_ar=?, account_name_en=?, account_type_id=?,
                parent_account_id=?, level=?, is_balance_sheet=?, is_final=?, is_active=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """
        p = (acc_code, name_ar, name_en, account_type_id, parent_account_id, level, is_balance_sheet, is_final, is_active, account_id)
        return self._execute_query(q, p)

    def delete_account(self, account_id):
        r = self._execute_query("SELECT COUNT(*) AS c FROM accounts WHERE parent_account_id=?", (account_id,), fetch_one=True)
        if r and r.get('c', 0) > 0:
            QMessageBox.warning(None, "رفض الحذف", "لا يمكن حذف حساب له حسابات فرعية.")
            return False
        r = self._execute_query("SELECT COUNT(*) AS c FROM journal_entry_lines WHERE account_id=?", (account_id,), fetch_one=True)
        if r and r.get('c', 0) > 0:
            QMessageBox.warning(None, "رفض الحذف", "لا يمكن حذف حساب مرتبط بقيود يومية.")
            return False
        return self._execute_query("DELETE FROM accounts WHERE id=?", (account_id,))

# ------------------------------------------------------------
# نموذج إضافة/تعديل حساب
# ------------------------------------------------------------
class AccountFormDialog(QDialog):
    def __init__(self, db_manager, account_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.account_id = account_id
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle("إضافة حساب" if account_id is None else "تعديل حساب")
        self.setMinimumWidth(420)
        self._build_ui()
        self._load_for_edit()

    def _build_ui(self):
        form = QFormLayout(self)

        self.acc_code = QLineEdit()
        form.addRow("رمز الحساب:", self.acc_code)

        self.name_ar = QLineEdit()
        form.addRow("الاسم (عربي):", self.name_ar)

        self.name_en = QLineEdit()
        form.addRow("الاسم (إنجليزي):", self.name_en)

        self.acc_type = QComboBox()
        self._types_map = {}
        for t in (self.db_manager.get_account_types() or []):
            self.acc_type.addItem(f"{t['name_ar']} ({t['account_side']})", t['id'])
            self._types_map[t['id']] = t['name_ar']
        self.acc_type.currentIndexChanged.connect(self._on_type_change)
        form.addRow("نوع الحساب:", self.acc_type)

        self.parent_acc = QComboBox()
        self.parent_acc.addItem("بدون حساب أب", None)
        self.parent_acc.currentIndexChanged.connect(self._on_parent_change)
        form.addRow("الحساب الأب:", self.parent_acc)

        self.level = QLineEdit(); self.level.setReadOnly(True); self.level.setProperty("readOnly", True)
        form.addRow("المستوى:", self.level)

        self.fs_combo = QComboBox()
        self.fs_combo.addItem("قائمة الميزانية (مركز مالي)", 1)
        self.fs_combo.addItem("قائمة الدخل (أرباح وخسائر)", 0)
        form.addRow("القائمة الختامية:", self.fs_combo)

        self.is_final = QCheckBox("حساب نهائي (يسمح بالحركات المباشرة)")
        form.addRow(self.is_final)

        self.active_combo = QComboBox()
        self.active_combo.addItem("نشط", 1)
        self.active_combo.addItem("غير نشط", 0)
        form.addRow("الحالة:", self.active_combo)

        btns = QHBoxLayout()
        self.save_btn = QPushButton("حفظ"); self.save_btn.setObjectName("addButton")
        self.cancel_btn = QPushButton("إلغاء"); self.cancel_btn.setObjectName("closeButton")
        self.save_btn.clicked.connect(self._save)
        self.cancel_btn.clicked.connect(self.reject)
        btns.addWidget(self.save_btn); btns.addWidget(self.cancel_btn)
        form.addRow(btns)

        self._populate_parents()

    def _load_for_edit(self):
        if not self.account_id:
            self._on_parent_change(0)
            return
        data = self.db_manager.get_account_by_id(self.account_id)
        if not data:
            QMessageBox.warning(self, "خطأ", "تعذر تحميل بيانات الحساب.")
            self.reject()
            return
        self.acc_code.setText(data['acc_code'])
        self.name_ar.setText(data['account_name_ar'])
        self.name_en.setText(data.get('account_name_en') or "")
        # type
        idx = self.acc_type.findData(data['account_type_id'])
        if idx >= 0:
            self.acc_type.setCurrentIndex(idx)
            self._populate_parents(account_type_id=data['account_type_id'])
        # parent
        if data['parent_account_id'] is not None:
            idx = self.parent_acc.findData(data['parent_account_id'])
            if idx >= 0:
                self.parent_acc.setCurrentIndex(idx)
        self.level.setText(str(data['level']))
        self.fs_combo.setCurrentIndex(self.fs_combo.findData(data['is_balance_sheet']))
        self.is_final.setChecked(bool(data['is_final']))
        self.active_combo.setCurrentIndex(self.active_combo.findData(data['is_active']))

        # تقييد التعديل في وضع التحرير
        self.acc_code.setReadOnly(True); self.acc_code.setProperty("readOnly", True)
        self.acc_type.setEnabled(False); self.parent_acc.setEnabled(False)

    def _populate_parents(self, account_type_id=None):
        self.parent_acc.blockSignals(True)
        self.parent_acc.clear()
        self.parent_acc.addItem("بدون حساب أب", None)
        if account_type_id is None and self.acc_type.currentData():
            account_type_id = self.acc_type.currentData()
        rows = self.db_manager.get_accounts_by_type(account_type_id) if account_type_id is not None else self.db_manager.get_all_accounts()
        for r in (rows or []):
            if self.account_id is None or r['id'] != self.account_id:
                if r['is_final'] == 0:
                    self.parent_acc.addItem(f"{r['acc_code']} - {r['account_name_ar']}", r['id'])
        self.parent_acc.blockSignals(False)

    def _on_type_change(self, _):
        self._populate_parents()
        self._on_parent_change(self.parent_acc.currentIndex())

    def _on_parent_change(self, _):
        if self.account_id is not None:
            return
        parent_id = self.parent_acc.currentData()
        if parent_id is None:
            max_code = self.db_manager.get_max_child_acc_code(None)
            if max_code and str(max_code).isdigit():
                try:
                    nxt = int(max_code) + 1
                    #self.acc_code.setText(str(nxt).zfill(4))
                    self.acc_code.setText(str(nxt))

                except ValueError:
                    self.acc_code.setText("1")
            else:
                self.acc_code.setText("1")
            self.level.setText("1")
            self.acc_code.setReadOnly(False); self.acc_code.setProperty("readOnly", False)
        else:
            parent = self.db_manager.get_account_by_id(parent_id)
            if parent:
                prefix = parent['acc_code']
                lvl = int(parent['level']) + 1
                self.level.setText(str(lvl))
                max_child = self.db_manager.get_max_child_acc_code(parent_id)
                if max_child and max_child.startswith(prefix):
                    suf = max_child[len(prefix):]
                    if suf.isdigit():
                        nxt = int(suf) + 1
                        #tgt_len = max(len(suf), len(str(nxt)), 2)
                        #self.acc_code.setText(prefix + str(nxt).zfill(tgt_len))
                        self.acc_code.setText(prefix + str(nxt))

                    else:
                        self.acc_code.setText(prefix + "1")
                else:
                    self.acc_code.setText(prefix + "1")
            self.acc_code.setReadOnly(True); self.acc_code.setProperty("readOnly", True)

    def _save(self):
        acc_code = self.acc_code.text().strip()
        name_ar = self.name_ar.text().strip()
        name_en = self.name_en.text().strip()
        acc_type = self.acc_type.currentData()
        parent_id = self.parent_acc.currentData()
        level = int(self.level.text() or "1")
        is_bs = self.fs_combo.currentData()
        is_final = 1 if self.is_final.isChecked() else 0
        is_active = self.active_combo.currentData()

        if not acc_code or not name_ar or acc_type is None:
            QMessageBox.warning(self, "بيانات ناقصة", "الرجاء ملء رمز الحساب والاسم والنوع.")
            return

        if self.account_id is None:
            if self.db_manager.get_account_by_code(acc_code):
                QMessageBox.warning(self, "رمز مكرر", "رمز الحساب موجود مسبقًا.")
                return
            ok = self.db_manager.add_account(acc_code, name_ar, name_en, acc_type, parent_id, level, is_bs, is_final, is_active)
            if ok:
                QMessageBox.information(self, "نجاح", "تمت إضافة الحساب.")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل إضافة الحساب.")
        else:
            ok = self.db_manager.update_account(self.account_id, acc_code, name_ar, name_en, acc_type, parent_id, level, is_bs, is_final, is_active)
            if ok:
                QMessageBox.information(self, "نجاح", "تم تحديث الحساب.")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل تحديث الحساب.")

# ------------------------------------------------------------
# فلترة مخصصة
# ------------------------------------------------------------
class AccountFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self._search = ""
        self._type_id = None
        self.db_manager = db_manager

    def set_filter_criteria(self, text, type_id):
        self._search = (text or "").lower()
        self._type_id = type_id
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        idx0 = self.sourceModel().index(source_row, 0, source_parent)
        if not idx0.isValid():
            return False
        # فلتر النوع
        if self._type_id is not None:
            acc_id = self.sourceModel().data(idx0, Qt.UserRole)
            data = self.db_manager.get_account_by_id(acc_id)
            if data and data['account_type_id'] != self._type_id:
                return False
        # فلتر النص
        if self._search:
            cols = []
            for c in (0, 1, 2):
                cols.append(str(self.sourceModel().data(self.sourceModel().index(source_row, c, source_parent), Qt.DisplayRole) or "").lower())
            if not any(self._search in s for s in cols):
                return False
        return True

# ------------------------------------------------------------
# نافذة شجرة الحسابات
# ------------------------------------------------------------
class ChartOfAccountsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = AccountDBManager()
        self.current_view_mode = "detailed"  # "tree" or "detailed"
        self._build_ui()
        self._load_accounts()

    def _build_ui(self):
        self.setWindowTitle("إدارة شجرة الحسابات")
        self.setGeometry(100, 100, 1200, 700)
        self.setLayoutDirection(Qt.RightToLeft)
        QApplication.instance().setLayoutDirection(Qt.RightToLeft)

        cw = QWidget(); self.setCentralWidget(cw)
        root = QVBoxLayout(cw)

        # شريط علوي (أزرار)
        tools = QHBoxLayout()

        self.btn_add = QPushButton("إضافة حساب");  self.btn_add.setObjectName("addButton")
        self.btn_add.clicked.connect(self._add_account)
        tools.addWidget(self.btn_add)

        self.btn_edit = QPushButton("تعديل حساب");  self.btn_edit.setObjectName("editButton")
        self.btn_edit.clicked.connect(self._edit_account)
        tools.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("حذف حساب");  self.btn_delete.setObjectName("deleteButton")
        self.btn_delete.clicked.connect(self._delete_account)
        tools.addWidget(self.btn_delete)

        self.btn_refresh = QPushButton("تحديث");     self.btn_refresh.setObjectName("refreshButton")
        self.btn_refresh.clicked.connect(self._load_accounts)
        tools.addWidget(self.btn_refresh)

        self.btn_toggle = QPushButton("عرض كشجرة")
        self.btn_toggle.clicked.connect(self._toggle_view_mode)
        tools.addWidget(self.btn_toggle)

        # زر الإغلاق
        self.btn_close = QPushButton("إغلاق")
        self.btn_close.setObjectName("closeButton")
        self.btn_close.clicked.connect(self.close)
        tools.addWidget(self.btn_close)

        tools.addStretch()
        root.addLayout(tools)

        # منطقة الفلترة
        filters = QHBoxLayout()
        filters.addWidget(QLabel("فلتر النوع:"))
        self.cbo_type = QComboBox()
        self.cbo_type.addItem("جميع الأنواع", None)
        for t in (self.db_manager.get_account_types() or []):
            self.cbo_type.addItem(f"{t['name_ar']} ({t['account_side']})", t['id'])
        self.cbo_type.currentIndexChanged.connect(self._apply_filter)
        filters.addWidget(self.cbo_type)

        filters.addWidget(QLabel("بحث:"))
        self.txt_search = QLineEdit(); self.txt_search.setPlaceholderText("رمز/اسم الحساب…")
        self.txt_search.textChanged.connect(self._apply_filter)
        filters.addWidget(self.txt_search)

        self.btn_clear = QPushButton("مسح الفلترة"); self.btn_clear.setObjectName("closeButton")
        self.btn_clear.clicked.connect(self._clear_filter)
        filters.addWidget(self.btn_clear)

        root.addLayout(filters)

        # العرض الشجري
        self.tree = QTreeView()
        self.tree.setUniformRowHeights(True)
        self.tree.setSortingEnabled(True)
        self.tree.setSelectionMode(QTreeView.SingleSelection)
        self.tree.setEditTriggers(QTreeView.NoEditTriggers)
        self.tree.setAlternatingRowColors(True)  # ✅ تفعيل ألوان الصفوف المتبادلة
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)

        # تعيين لون الصف البديل عبر الـ Palette (بالإضافة لـ QSS)
        pal = self.tree.palette()
        pal.setColor(QPalette.AlternateBase, QColor("#F7F9FC"))
        self.tree.setPalette(pal)

        root.addWidget(self.tree)

        # موديلات البيانات
        self.model = QStandardItemModel()
        self.proxy = AccountFilterProxyModel(self.db_manager)
        self.proxy.setSourceModel(self.model)
        self.tree.setModel(self.proxy)

        # قائمة سياق
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._context_menu)

    # ---------------------------
    # تحميل البيانات وبناء العرض
    # ---------------------------
    def _load_accounts(self):
        self.model.removeRows(0, self.model.rowCount())
        rows = self.db_manager.get_all_accounts() or []

        # رؤوس الأعمدة حسب وضع العرض
        if self.current_view_mode == "detailed":
            self.model.setColumnCount(10)
            headers = [
                "رمز الحساب","الاسم بالعربية","الاسم بالإنجليزية","نوع الحساب",
                "طبيعة الحساب","المستوى","القائمة","الحساب الأب","نهائي؟","الحالة"
            ]
        else:
            self.model.setColumnCount(3)
            headers = ["رمز الحساب","اسم الحساب","نهائي؟"]

        for i, h in enumerate(headers):
            self.model.setHeaderData(i, Qt.Horizontal, h)

        # حفظ العناصر بحسب id لبناء الشجرة
        nodes = {}

        # إنشاء العناصر
        for acc in rows:
            code = QStandardItem(str(acc['acc_code']))
            code.setData(acc['id'], Qt.UserRole)  # ID
            if self.current_view_mode == "detailed":
                items = [
                    code,
                    QStandardItem(str(acc['account_name_ar'] or "")),
                    QStandardItem(str(acc['account_name_en'] or "")),
                    QStandardItem(str(acc['account_type_name'] or "")),
                    QStandardItem(str(acc['account_side'] or "")),
                    QStandardItem(str(acc['level'])),
                    QStandardItem("ميزانية" if acc['is_balance_sheet']==1 else "دخل"),
                    QStandardItem(str(acc['parent_account_name'] or "بدون")),
                    QStandardItem("نعم" if acc['is_final']==1 else "لا"),
                    QStandardItem("نشط" if acc['is_active']==1 else "غير نشط"),
                ]
            else:
                items = [
                    code,
                    QStandardItem(str(acc['account_name_ar'] or "")),
                    QStandardItem("نعم" if acc['is_final']==1 else "لا"),
                ]
            nodes[acc['id']] = items[0]
            # إلحاق للوالد أو جذري
            if acc['parent_account_id'] is None:
                self.model.appendRow(items)
            else:
                parent_item = nodes.get(acc['parent_account_id'])
                if parent_item:
                    parent_item.appendRow(items)
                else:
                    # لو الأب لسه متبنيش، أضفه جذريًا لمنع فقدان الصف
                    self.model.appendRow(items)

        self.tree.expandAll()
        self._apply_filter()

        # أحجام أعمدة مبدئية في العرض التفصيلي
        if self.current_view_mode == "detailed":
            widths = [110, 200, 180, 140, 100, 70, 120, 180, 90, 80]
            for i, w in enumerate(widths):
                self.tree.setColumnWidth(i, w)
        else:
            widths = [150, 350, 100]
            for i, w in enumerate(widths):
                self.tree.setColumnWidth(i, w)

    # ---------------------------
    # الأوامر
    # ---------------------------
    def _toggle_view_mode(self):
        if self.current_view_mode == "detailed":
            self.current_view_mode = "tree"
            self.btn_toggle.setText("عرض كجدول مفصل")
        else:
            self.current_view_mode = "detailed"
            self.btn_toggle.setText("عرض كشجرة")
        self._load_accounts()

    def _selected_account_id(self):
        sel = self.tree.selectedIndexes()
        if not sel:
            return None
        src = self.proxy.mapToSource(sel[0])
        item = self.model.itemFromIndex(src)
        return item.data(Qt.UserRole)

    def _add_account(self):
        dlg = AccountFormDialog(self.db_manager, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_accounts()

    def _edit_account(self):
        acc_id = self._selected_account_id()
        if not acc_id:
            QMessageBox.warning(self, "لا يوجد تحديد", "يرجى اختيار حساب أولاً.")
            return
        dlg = AccountFormDialog(self.db_manager, account_id=acc_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_accounts()

    def _delete_account(self):
        acc_id = self._selected_account_id()
        if not acc_id:
            QMessageBox.warning(self, "لا يوجد تحديد", "يرجى اختيار حساب أولاً.")
            return
        if QMessageBox.question(self, "تأكيد الحذف", "هل تريد حذف الحساب المحدد؟") == QMessageBox.Yes:
            if self.db_manager.delete_account(acc_id):
                QMessageBox.information(self, "تم", "تم حذف الحساب.")
                self._load_accounts()

    def _apply_filter(self):
        txt = self.txt_search.text().strip()
        t_id = self.cbo_type.currentData()
        self.proxy.set_filter_criteria(txt, t_id)
        self.tree.expandAll()

    def _clear_filter(self):
        self.txt_search.clear()
        self.cbo_type.setCurrentIndex(0)
        self.tree.expandAll()

    def _context_menu(self, pos):
        index = self.tree.indexAt(pos)
        if not index.isValid():
            return
        menu = QMenu(self)
        a_edit = QAction("تعديل", self); a_edit.triggered.connect(self._edit_account)
        a_del  = QAction("حذف", self);  a_del.triggered.connect(self._delete_account)
        menu.addAction(a_edit); menu.addAction(a_del)
        menu.exec_(self.tree.viewport().mapToGlobal(pos))

# ------------------------------------------------------------
# نقطة الدخول
# ------------------------------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("ERP - شجرة الحسابات")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")
    app.setLayoutDirection(Qt.RightToLeft)

    # تحميل QSS من المسار + بديل داخلي
    qss_path = os.path.join(current_dir, '..', '..', 'ui', 'styles', 'styles.qss')
    qss = load_qss_file(qss_path)
    if qss:
        app.setStyleSheet(qss)
        print(f"✅ Applied stylesheet: {qss_path}")
    else:
        app.setStyleSheet(FALLBACK_QSS)
        print("⚠️ Using embedded fallback QSS")

    # تهيئة قاعدة بيانات المالية (إن وُجد المُدير)
    try:
        DBSchemaManager().initialize_specific_database('financials')
    except Exception as e:
        print(f"⚠️ Schema init skipped: {e}")

    win = ChartOfAccountsWindow()
    # win.show()  # لو عايز بحجم ثابت
    win.showMaximized()  # ✅ لو عايز ياخذ حجم الشاشة
    sys.exit(app.exec_())

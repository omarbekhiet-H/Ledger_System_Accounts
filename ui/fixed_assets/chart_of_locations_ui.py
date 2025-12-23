# -*- coding: utf-8 -*-
import sys
import sqlite3
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTreeView, QDialog, QFormLayout, QLineEdit,
    QComboBox, QMessageBox, QLabel, QAction, QMenu, QHeaderView,
    QCheckBox, QTextEdit, QSpinBox
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

# استيراد دالة الاتصال بقاعدة بيانات الأصول الثابتة (fallback لو مش موجود)
try:
    from database.db_connection import get_fixed_assets_db_connection
except Exception as e:
    print(f"⚠️ get_fixed_assets_db_connection Import fallback: {e}")
    def get_fixed_assets_db_connection():
        return None

# ------------------------------------------------------------
# إدارة قاعدة البيانات
# ------------------------------------------------------------
class LocationDBManager:
    def __init__(self):
        pass

    def _execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        conn = None
        try:
            conn = get_fixed_assets_db_connection()
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

    def get_max_child_loc_code(self, parent_id):
        """
        يولد كود تلقائيًا بناءً على كود الأب (إذا موجود) أو أعلى كود جذري.
        يعتمد على كون loc_code رقم أو بداية رقمية + suffix رقمي.
        """
        if parent_id is None:
            q = "SELECT MAX(CAST(loc_code AS INTEGER)) AS max_code FROM asset_locations WHERE parent_location_id IS NULL"
            r = self._execute_query(q, fetch_one=True)
            return str(r['max_code']) if r and r.get('max_code') is not None else None

        parent = self.get_location_by_id(parent_id)
        if not parent:
            return None
        prefix = parent.get('loc_code') or ""
        q = "SELECT loc_code FROM asset_locations WHERE parent_location_id = ?"
        rows = self._execute_query(q, (parent_id,), fetch_all=True) or []
        max_num, max_len = 0, 0
        for row in rows:
            code = row.get('loc_code') if isinstance(row, dict) else row[0]
            if not code:
                continue
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

    def get_location_types(self):
        q = "SELECT id, name_ar FROM location_types ORDER BY name_ar"
        return self._execute_query(q, fetch_all=True)

    def get_all_locations(self):
        q = """
            SELECT l.id, l.loc_code, l.location_name_ar, l.location_name_en,
                   l.location_type_id, t.name_ar AS type_name,
                   l.parent_location_id, p.location_name_ar AS parent_name,
                   l.level, l.is_final, l.is_active,
                   l.address, l.phone, l.responsible_person, l.capacity, l.current_usage
            FROM asset_locations l
            LEFT JOIN location_types t ON l.location_type_id = t.id
            LEFT JOIN asset_locations p ON l.parent_location_id = p.id
            ORDER BY l.loc_code
        """
        return self._execute_query(q, fetch_all=True)

    def get_location_by_id(self, loc_id):
        q = "SELECT * FROM asset_locations WHERE id = ?"
        return self._execute_query(q, (loc_id,), fetch_one=True)

    def get_location_by_code(self, code):
        q = "SELECT id, loc_code FROM asset_locations WHERE loc_code = ?"
        return self._execute_query(q, (code,), fetch_one=True)

    def add_location(self, loc_code, name_ar, name_en, type_id, parent_id, level,
                     is_final, address, phone, responsible, capacity, usage, is_active):
        q = """
            INSERT INTO asset_locations
            (loc_code, location_name_ar, location_name_en, location_type_id,
             parent_location_id, level, is_final,
             address, phone, responsible_person, capacity, current_usage,
             is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        p = (loc_code, name_ar, name_en, type_id, parent_id, level, is_final,
             address, phone, responsible, capacity, usage, is_active)
        return self._execute_query(q, p)

    def update_location(self, loc_id, loc_code, name_ar, name_en, type_id, parent_id, level,
                        is_final, address, phone, responsible, capacity, usage, is_active):
        q = """
            UPDATE asset_locations SET
                loc_code=?, location_name_ar=?, location_name_en=?, location_type_id=?,
                parent_location_id=?, level=?, is_final=?,
                address=?, phone=?, responsible_person=?, capacity=?, current_usage=?,
                is_active=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """
        p = (loc_code, name_ar, name_en, type_id, parent_id, level, is_final,
             address, phone, responsible, capacity, usage, is_active, loc_id)
        return self._execute_query(q, p)

    def delete_location(self, loc_id):
        r = self._execute_query("SELECT COUNT(*) AS c FROM asset_locations WHERE parent_location_id=?", (loc_id,), fetch_one=True)
        if r and r.get('c', 0) > 0:
            QMessageBox.warning(None, "رفض الحذف", "لا يمكن حذف موقع له مواقع فرعية.")
            return False
        return self._execute_query("DELETE FROM asset_locations WHERE id=?", (loc_id,))


# ------------------------------------------------------------
# نموذج إضافة/تعديل موقع (بستايل حديث)
# ------------------------------------------------------------
class LocationFormDialog(QDialog):
    def __init__(self, db_manager, loc_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.loc_id = loc_id
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle("إضافة موقع" if loc_id is None else "تعديل موقع")
        self.setMinimumWidth(520)
        self._build_ui()
        self._populate_types()
        self._populate_parents()
        self._load_for_edit()

    def _build_ui(self):
        form = QFormLayout(self)

        self.loc_code = QLineEdit()
        form.addRow("رمز الموقع:", self.loc_code)

        self.name_ar = QLineEdit()
        form.addRow("الاسم (عربي):", self.name_ar)

        self.name_en = QLineEdit()
        form.addRow("الاسم (إنجليزي):", self.name_en)

        self.type = QComboBox()
        form.addRow("نوع الموقع:", self.type)

        self.parent_loc = QComboBox()
        self.parent_loc.addItem("بدون موقع أب", None)
        self.parent_loc.currentIndexChanged.connect(self._on_parent_change)
        form.addRow("الموقع الأب:", self.parent_loc)

        self.level = QLineEdit(); self.level.setReadOnly(True)
        form.addRow("المستوى:", self.level)

        self.is_final = QCheckBox("موقع نهائي (يسمح بالاستخدام المباشر)")
        form.addRow(self.is_final)

        self.address = QTextEdit(); self.address.setFixedHeight(60)
        form.addRow("العنوان:", self.address)

        self.phone = QLineEdit()
        form.addRow("الهاتف:", self.phone)

        self.responsible = QLineEdit()
        form.addRow("المسؤول:", self.responsible)

        self.capacity = QSpinBox(); self.capacity.setMaximum(1000000)
        form.addRow("السعة:", self.capacity)

        self.current_usage = QSpinBox(); self.current_usage.setMaximum(1000000)
        form.addRow("الاستخدام الحالي:", self.current_usage)

        self.active_combo = QComboBox()
        self.active_combo.addItem("نشط", 1)
        self.active_combo.addItem("غير نشط", 0)
        form.addRow("الحالة:", self.active_combo)

        btns = QHBoxLayout()
        self.save_btn = QPushButton("حفظ")
        self.save_btn.setObjectName("primaryButton")
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setObjectName("secondaryButton")
        self.save_btn.clicked.connect(self._save)
        self.cancel_btn.clicked.connect(self.reject)
        btns.addWidget(self.save_btn); btns.addWidget(self.cancel_btn)
        form.addRow(btns)

        # ستايل موحّد للفورم
        self.setStyleSheet("""
            QLabel { font-size: 12px; font-weight: 600; color: #333; }
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                border: 1px solid #d0d7de;
                border-radius: 6px;
                padding: 6px;
                font-size: 12px;
                background: #ffffff;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #2b8cff;
                background-color: #f3f9ff;
            }
            QCheckBox { font-size: 12px; }
            QPushButton#primaryButton {
                background-color: #0078d7; color: white; border-radius: 6px; padding: 6px 14px;
            }
            QPushButton#primaryButton:hover { background-color: #005a9e; }
            QPushButton#secondaryButton {
                background-color: #6c757d; color: white; border-radius: 6px; padding: 6px 14px;
            }
            QPushButton#secondaryButton:hover { background-color: #5a6268; }
        """)

    def _populate_types(self):
        self.type.blockSignals(True)
        self.type.clear()
        types = self.db_manager.get_location_types() or []
        for t in types:
            # تأكد من سلامة البنية
            if isinstance(t, dict):
                name = t.get('name_ar') or str(t.get('id'))
                idv = t.get('id')
            else:
                name = str(t)
                idv = t
            self.type.addItem(name, idv)
        if self.type.count() > 0:
            self.type.setCurrentIndex(0)
        else:
            self.type.addItem("لا توجد أنواع", None)
            self.type.setCurrentIndex(0)
        self.type.blockSignals(False)

    def _populate_parents(self):
        self.parent_loc.blockSignals(True)
        self.parent_loc.clear()
        self.parent_loc.addItem("بدون موقع أب", None)
        rows = self.db_manager.get_all_locations() or []
        for r in rows:
            if self.loc_id is None or r.get('id') != self.loc_id:
                label = f"{r.get('loc_code','')} - {r.get('location_name_ar','')}"
                self.parent_loc.addItem(label, r.get('id'))
        self.parent_loc.setCurrentIndex(0)
        self.parent_loc.blockSignals(False)

    def _on_parent_change(self, _=None):
        # في حالة التعديل لا نغيّر الكود تلقائيًّا
        if self.loc_id is not None:
            return
        parent_id = self.parent_loc.currentData()
        if parent_id is None:
            max_code = self.db_manager.get_max_child_loc_code(None)
            if max_code and str(max_code).isdigit():
                try:
                    nxt = int(max_code) + 1
                    self.loc_code.setText(str(nxt))
                except Exception:
                    self.loc_code.setText("1")
            else:
                self.loc_code.setText("1")
            self.level.setText("1")
            self.loc_code.setReadOnly(False)
        else:
            parent = self.db_manager.get_location_by_id(parent_id)
            if parent:
                prefix = parent.get('loc_code') or ""
                try:
                    lvl = int(parent.get('level', 1)) + 1
                except Exception:
                    lvl = 2
                self.level.setText(str(lvl))
                max_child = self.db_manager.get_max_child_loc_code(parent_id)
                if max_child and max_child.startswith(prefix):
                    suf = max_child[len(prefix):]
                    if suf.isdigit():
                        try:
                            nxt = int(suf) + 1
                            self.loc_code.setText(prefix + str(nxt))
                        except Exception:
                            self.loc_code.setText(prefix + "1")
                    else:
                        self.loc_code.setText(prefix + "1")
                else:
                    self.loc_code.setText(prefix + "1")
            self.loc_code.setReadOnly(True)

    def _load_for_edit(self):
        if not self.loc_id:
            self.level.setText("1")
            return
        data = self.db_manager.get_location_by_id(self.loc_id)
        if not data:
            QMessageBox.warning(self, "خطأ", "تعذر تحميل بيانات الموقع.")
            self.reject()
            return
        self.loc_code.setText(data.get('loc_code') or "")
        self.name_ar.setText(data.get('location_name_ar') or "")
        self.name_en.setText(data.get('location_name_en') or "")
        # إعادة تعبئة القوائم قبل التعيين
        self._populate_types()
        self._populate_parents()
        # نوع الموقع
        target_type_id = data.get('location_type_id')
        if target_type_id is not None:
            idx = self.type.findData(target_type_id)
            if idx >= 0:
                self.type.setCurrentIndex(idx)
        # الموقع الأب
        if data.get('parent_location_id') is not None:
            p_idx = self.parent_loc.findData(data.get('parent_location_id'))
            if p_idx >= 0:
                self.parent_loc.setCurrentIndex(p_idx)
        self.level.setText(str(data.get('level') or "1"))
        self.is_final.setChecked(bool(data.get('is_final')))
        self.address.setPlainText(data.get('address') or "")
        self.phone.setText(data.get('phone') or "")
        self.responsible.setText(data.get('responsible_person') or "")
        try:
            self.capacity.setValue(int(data.get('capacity') or 0))
        except Exception:
            self.capacity.setValue(0)
        try:
            self.current_usage.setValue(int(data.get('current_usage') or 0))
        except Exception:
            self.current_usage.setValue(0)
        aidx = self.active_combo.findData(data.get('is_active'))
        if aidx >= 0:
            self.active_combo.setCurrentIndex(aidx)

    def _save(self):
        code = self.loc_code.text().strip()
        name_ar = self.name_ar.text().strip()
        name_en = self.name_en.text().strip()

        type_id = self.type.currentData()
        if type_id is None and self.type.count() > 0:
            type_id = self.type.itemData(0)

        parent_id = self.parent_loc.currentData()
        if parent_id is None:
            level = 1
        else:
            parent = self.db_manager.get_location_by_id(parent_id)
            try:
                level = int(parent.get('level', 1)) + 1
            except Exception:
                level = 2

        is_final = 1 if self.is_final.isChecked() else 0
        address = self.address.toPlainText().strip()
        phone = self.phone.text().strip()
        responsible = self.responsible.text().strip()
        cap = self.capacity.value()
        usage = self.current_usage.value()
        is_active = self.active_combo.currentData()

        if not code or not name_ar or type_id is None:
            QMessageBox.warning(self, "بيانات ناقصة", "الرجاء ملء رمز الموقع والاسم والنوع.")
            return

        if self.loc_id is None:
            if self.db_manager.get_location_by_code(code):
                QMessageBox.warning(self, "رمز مكرر", "رمز الموقع موجود مسبقًا.")
                return
            ok = self.db_manager.add_location(code, name_ar, name_en, type_id, parent_id,
                                              level, is_final, address, phone, responsible,
                                              cap, usage, is_active)
            if ok:
                QMessageBox.information(self, "نجاح", "تمت إضافة الموقع.")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل إضافة الموقع.")
        else:
            ok = self.db_manager.update_location(self.loc_id, code, name_ar, name_en, type_id, parent_id,
                                                 level, is_final, address, phone, responsible,
                                                 cap, usage, is_active)
            if ok:
                QMessageBox.information(self, "نجاح", "تم تحديث الموقع.")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل تحديث الموقع.")


# ------------------------------------------------------------
# فلترة مخصصة
# ------------------------------------------------------------
class LocationFilterProxyModel(QSortFilterProxyModel):
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
        # فلترة نصية عبر الأعمدة الرئيسية
        if self._search:
            cols = []
            for c in (0, 1, 2, 3):  # رمز، اسم عربي، اسم إنجليزي، النوع
                cols.append(str(self.sourceModel().data(self.sourceModel().index(source_row, c, source_parent), Qt.DisplayRole) or "").lower())
            if not any(self._search in s for s in cols):
                return False
        # فلترة نوع اختيارية (متركزة لو احتجت تضيفها لاحقًا)
        if self._type_id is not None:
            # نحصل على id من الـ item (Qt.UserRole)
            item_index = self.sourceModel().index(source_row, 0, source_parent)
            if item_index.isValid():
                loc_id = self.sourceModel().data(item_index, Qt.UserRole)
                data = self.db_manager.get_location_by_id(loc_id)
                if data and data.get('location_type_id') != self._type_id:
                    return False
        return True


# ------------------------------------------------------------
# نافذة شجرة المواقع (مع تنسيقات حديثة)
# ------------------------------------------------------------
class AssetLocationsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = LocationDBManager()
        self._build_ui()
        self._load_locations()

    def _build_ui(self):
        self.setWindowTitle("إدارة شجرة المواقع")
        self.setGeometry(80, 80, 1300, 780)
        self.setLayoutDirection(Qt.RightToLeft)
        QApplication.instance().setLayoutDirection(Qt.RightToLeft)

        cw = QWidget()
        self.setCentralWidget(cw)
        root = QVBoxLayout(cw)

        # شريط الأدوات
        tools = QHBoxLayout()
        self.btn_add = QPushButton("إضافة موقع"); self.btn_add.clicked.connect(self._add_location)
        self.btn_edit = QPushButton("تعديل موقع"); self.btn_edit.clicked.connect(self._edit_location)
        self.btn_delete = QPushButton("حذف موقع"); self.btn_delete.clicked.connect(self._delete_location)
        self.btn_refresh = QPushButton("تحديث"); self.btn_refresh.clicked.connect(self._load_locations)
        self.btn_close = QPushButton("إغلاق"); self.btn_close.clicked.connect(self.close)

        for b in [self.btn_add, self.btn_edit, self.btn_delete, self.btn_refresh, self.btn_close]:
            b.setObjectName("actionButton")
            tools.addWidget(b)

        tools.addStretch()
        root.addLayout(tools)

        # فلتر وبحث
        filters = QHBoxLayout()
        filters.addWidget(QLabel("بحث:"))
        self.txt_search = QLineEdit(); self.txt_search.setPlaceholderText("رمز/اسم الموقع…")
        self.txt_search.textChanged.connect(self._apply_filter)
        filters.addWidget(self.txt_search)
        root.addLayout(filters)

        # Tree view
        self.tree = QTreeView()
        self.tree.setUniformRowHeights(True)
        self.tree.setSortingEnabled(True)
        self.tree.setSelectionMode(QTreeView.SingleSelection)
        self.tree.setEditTriggers(QTreeView.NoEditTriggers)
        self.tree.setAlternatingRowColors(True)
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)

        # ستايل للـ tree و الأزرار (موحد)
        self.setStyleSheet("""
            /* أزرار الشريط */
            QPushButton#actionButton {
                background-color: #0078d7; color: white; border-radius: 8px; padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton#actionButton:hover { background-color: #005a9e; }
            QPushButton#actionButton:pressed { background-color: #003f6f; }

            /* تصميم الـ TreeView */
            QTreeView {
                background: #ffffff;
                alternate-background-color: #F7F9FC;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #f0f2f5;
                padding: 6px;
                border: 1px solid #e1e4e8;
                font-weight: 700;
            }
        """)
        pal = self.tree.palette()
        pal.setColor(QPalette.AlternateBase, QColor("#F7F9FC"))
        self.tree.setPalette(pal)

        root.addWidget(self.tree)

        # نموذج بيانات وشبكة الفلترة
        self.model = QStandardItemModel()
        self.proxy = LocationFilterProxyModel(self.db_manager)
        self.proxy.setSourceModel(self.model)
        self.tree.setModel(self.proxy)

        # قائمة سياق
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._context_menu)

    def _load_locations(self):
        # تفريغ ثم تعبئة
        self.model.removeRows(0, self.model.rowCount())
        rows = self.db_manager.get_all_locations() or []

        # أعمدة كاملة
        self.model.setColumnCount(12)
        headers = [
            "رمز الموقع", "الاسم بالعربية", "الاسم بالإنجليزية", "النوع",
            "المستوى", "نهائي؟", "الحالة", "العنوان", "الهاتف",
            "المسؤول", "السعة", "الاستخدام الحالي"
        ]
        for i, h in enumerate(headers):
            self.model.setHeaderData(i, Qt.Horizontal, h)

        nodes = {}
        # بناء شجرة عن طريق مسح النتائج واحدة واحدة
        for loc in rows:
            code_item = QStandardItem(str(loc.get('loc_code') or ""))
            code_item.setData(loc.get('id'), Qt.UserRole)
            items = [
                code_item,
                QStandardItem(str(loc.get('location_name_ar') or "")),
                QStandardItem(str(loc.get('location_name_en') or "")),
                QStandardItem(str(loc.get('type_name') or "")),
                QStandardItem(str(loc.get('level') or "")),
                QStandardItem("نعم" if loc.get('is_final') == 1 else "لا"),
                QStandardItem("نشط" if loc.get('is_active') == 1 else "غير نشط"),
                QStandardItem(str(loc.get('address') or "")),
                QStandardItem(str(loc.get('phone') or "")),
                QStandardItem(str(loc.get('responsible_person') or "")),
                QStandardItem(str(loc.get('capacity') or "")),
                QStandardItem(str(loc.get('current_usage') or "")),
            ]
            nodes[loc.get('id')] = items[0]
            if loc.get('parent_location_id') is None:
                self.model.appendRow(items)
            else:
                parent_item = nodes.get(loc.get('parent_location_id'))
                if parent_item:
                    parent_item.appendRow(items)
                else:
                    # لو الوالد غير موجود مؤقتًا أضف جذريًا
                    self.model.appendRow(items)

        # توسيط بعض الأعمدة (المستوى وأعمدة رقمية)
        # ملاحظة: النموذج شجري، لذلك محاذاة الخلايا هنا تعطي نتيجة مبدئية للسطح الأول فقط.
        align_center = [4, 5, 6, 10, 11]
        row_count = max(0, len(rows))
        for r in range(row_count):
            for c in align_center:
                idx = self.model.index(r, c)
                if idx.isValid():
                    self.model.setData(idx, Qt.AlignCenter, Qt.TextAlignmentRole)

        self.tree.expandAll()
        self._apply_filter()

        # ضبط أحجام الأعمدة
        widths = [110, 200, 180, 140, 70, 70, 90, 240, 140, 140, 90, 110]
        for i, w in enumerate(widths):
            try:
                self.tree.setColumnWidth(i, w)
            except Exception:
                pass

    def _selected_location_id(self):
        sel = self.tree.selectedIndexes()
        if not sel:
            return None
        src = self.proxy.mapToSource(sel[0])
        item = self.model.itemFromIndex(src)
        return item.data(Qt.UserRole)

    def _add_location(self):
        dlg = LocationFormDialog(self.db_manager, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_locations()

    def _edit_location(self):
        loc_id = self._selected_location_id()
        if not loc_id:
            QMessageBox.warning(self, "لا يوجد تحديد", "يرجى اختيار موقع أولاً.")
            return
        dlg = LocationFormDialog(self.db_manager, loc_id=loc_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_locations()

    def _delete_location(self):
        loc_id = self._selected_location_id()
        if not loc_id:
            QMessageBox.warning(self, "لا يوجد تحديد", "يرجى اختيار موقع أولاً.")
            return
        if QMessageBox.question(self, "تأكيد الحذف", "هل تريد حذف الموقع المحدد؟") == QMessageBox.Yes:
            if self.db_manager.delete_location(loc_id):
                QMessageBox.information(self, "تم", "تم حذف الموقع.")
                self._load_locations()

    def _apply_filter(self):
        txt = self.txt_search.text().strip()
        self.proxy.set_filter_criteria(txt, None)
        self.tree.expandAll()

    def _context_menu(self, pos):
        index = self.tree.indexAt(pos)
        if not index.isValid():
            return
        menu = QMenu(self)
        a_edit = QAction("تعديل", self); a_edit.triggered.connect(self._edit_location)
        a_del  = QAction("حذف", self);  a_del.triggered.connect(self._delete_location)
        menu.addAction(a_edit); menu.addAction(a_del)
        menu.exec_(self.tree.viewport().mapToGlobal(pos))


# ------------------------------------------------------------
# نقطة الدخول
# ------------------------------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("ERP - شجرة المواقع")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")
    app.setLayoutDirection(Qt.RightToLeft)

    win = AssetLocationsWindow()
    win.showMaximized()
    sys.exit(app.exec_())

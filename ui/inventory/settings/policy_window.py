import os
import sys
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QListWidget, QListWidgetItem,
    QToolBar, QAction, QMessageBox, QCheckBox, QTabWidget, QInputDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QDialogButtonBox,
    QFormLayout, QGroupBox, QStatusBar, QMenuBar, QMenu
)
from PyQt5.QtGui import QFont, QColor, QPalette, QLinearGradient, QIcon, QPixmap
from datetime import datetime

# إعداد المسارات
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.inventory.setting.policy_manager import DBManager

class InventoryTypeDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.setWindowTitle("📦 إدارة أنواع حساب المخزون")
        self.setFixedSize(450, 350)
        self.db = db
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }
            QLabel {
                font-weight: bold;
                color: #2c3e50;
            }
            QListWidget {
                border: 1px solid #e2e8f0;
                border-radius: 5px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # قائمة أنواع المخزون
        self.type_list = QListWidget()
        self.load_inventory_types()
        layout.addWidget(QLabel("أنواع حساب المخزون المتاحة:"))
        layout.addWidget(self.type_list)
        
        # أزرار الإدارة
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ إضافة")
        add_btn.setStyleSheet("background-color: #38a169; color: white;")
        add_btn.clicked.connect(self.add_type)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("🗑️ حذف")
        remove_btn.setStyleSheet("background-color: #e53e3e; color: white;")
        remove_btn.clicked.connect(self.remove_type)
        btn_layout.addWidget(remove_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_inventory_types(self):
        types = self.db.get_inventory_account_types()
        self.type_list.clear()
        self.type_list.addItems(types)

    def add_type(self):
        name, ok = QInputDialog.getText(self, "إضافة نوع", "أدخل اسم نوع حساب المخزون الجديد:")
        if ok and name:
            try:
                self.db.conn.execute(
                    "INSERT INTO inventory_account_types (name) VALUES (?)",
                    (name,)
                )
                self.db.conn.commit()
                self.load_inventory_types()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل إضافة النوع: {str(e)}")

    def remove_type(self):
        selected = self.type_list.currentItem()
        if selected:
            name = selected.text()
            confirm = QMessageBox.question(
                self, "تأكيد الحذف",
                f"هل أنت متأكد من حذف نوع '{name}'؟",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                try:
                    self.db.conn.execute(
                        "DELETE FROM inventory_account_types WHERE name = ?",
                        (name,)
                    )
                    self.db.conn.commit()
                    self.load_inventory_types()
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"فشل حذف النوع: {str(e)}")

class PolicyDetailDialog(QDialog):
    def __init__(self, db, policy):
        super().__init__()
        self.setWindowTitle(f"تفاصيل السياسة: {policy['name']}")
        self.setMinimumSize(800, 650)
        self.db = db
        self.policy = policy
        self.current_user = "admin"
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }
            QGroupBox {
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QLabel {
                font-weight: bold;
                color: #2c3e50;
            }
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 5px;
            }
        """)
        
        self.build_ui()
        self.load_policy_details()

    def build_ui(self):
        layout = QVBoxLayout()
        
        # معلومات السياسة الأساسية
        info_group = QGroupBox("المعلومات الأساسية")
        info_layout = QFormLayout()
        
        self.key_label = QLabel(self.policy['key'])
        info_layout.addRow("المفتاح:", self.key_label)
        
        self.name_input = QLineEdit(self.policy['name'])
        info_layout.addRow("الاسم:", self.name_input)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(["مخزنية", "مالية", "تشغيلية", "مبيعات", "مشتريات"])
        self.category_combo.setCurrentText(self.policy['category'])
        info_layout.addRow("التصنيف:", self.category_combo)
        
        self.description_input = QComboBox()
        self.description_input.addItems(self.db.get_inventory_account_types())
        self.description_input.setCurrentText(self.policy['description'])
        info_layout.addRow("الوصف:", self.description_input)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # إعدادات السياسة
        settings_group = QGroupBox("الإعدادات")
        settings_layout = QFormLayout()
        
        self.editable_check = QCheckBox()
        self.editable_check.setChecked(bool(self.policy['editable']))
        settings_layout.addRow("قابلة للتعديل:", self.editable_check)
        
        self.approval_check = QCheckBox()
        self.approval_check.setChecked(bool(self.policy['requires_approval']))
        settings_layout.addRow("تتطلب موافقة:", self.approval_check)
        
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["عام", "فرع", "قسم", "مستخدم"])
        self.scope_combo.setCurrentText(self.policy['default_scope'])
        settings_layout.addRow("نطاق التطبيق:", self.scope_combo)
        
        self.version_input = QLineEdit(self.policy['version'])
        settings_layout.addRow("الإصدار:", self.version_input)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # الإعدادات التفصيلية
        details_group = QGroupBox("الإعدادات التفصيلية")
        details_layout = QVBoxLayout()
        
        # أزرار إدارة الإعدادات
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ إضافة إعداد")
        add_btn.setStyleSheet("background-color: #4299e1; color: white;")
        add_btn.clicked.connect(self.add_setting)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ تعديل")
        edit_btn.setStyleSheet("background-color: #f6ad55; color: white;")
        edit_btn.clicked.connect(self.edit_setting)
        btn_layout.addWidget(edit_btn)
        
        remove_btn = QPushButton("🗑️ حذف")
        remove_btn.setStyleSheet("background-color: #e53e3e; color: white;")
        remove_btn.clicked.connect(self.remove_setting)
        btn_layout.addWidget(remove_btn)
        
        details_layout.addLayout(btn_layout)
        
        # جدول الإعدادات
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(4)
        self.details_table.setHorizontalHeaderLabels(["ID", "الإعداد", "القيمة", "نوع البيانات"])
        self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.details_table.setSelectionBehavior(QTableWidget.SelectRows)
        details_layout.addWidget(self.details_table)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # أزرار التحكم
        btn_box = QDialogButtonBox()
        save_btn = btn_box.addButton("💾 حفظ", QDialogButtonBox.AcceptRole)
        delete_btn = btn_box.addButton("🗑️ حذف", QDialogButtonBox.DestructiveRole)
        cancel_btn = btn_box.addButton("إلغاء", QDialogButtonBox.RejectRole)
        
        save_btn.setStyleSheet("background-color: #38a169; color: white;")
        delete_btn.setStyleSheet("background-color: #e53e3e; color: white;")
        cancel_btn.setStyleSheet("background-color: #a0aec0; color: white;")
        
        save_btn.clicked.connect(self.save_changes)
        delete_btn.clicked.connect(self.delete_policy)
        cancel_btn.clicked.connect(self.reject)
        
        layout.addWidget(btn_box)
        self.setLayout(layout)

    def load_policy_details(self):
        details = self.db.get_policy_details(self.policy['id'])
        self.details_table.setRowCount(len(details))
        
        for row_idx, detail in enumerate(details):
            self.details_table.setItem(row_idx, 0, QTableWidgetItem(str(detail['id'])))
            self.details_table.setItem(row_idx, 1, QTableWidgetItem(detail['setting_key']))
            self.details_table.setItem(row_idx, 2, QTableWidgetItem(detail['setting_value']))
            self.details_table.setItem(row_idx, 3, QTableWidgetItem(detail['data_type']))

    def add_setting(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة إعداد جديد")
        dialog.setFixedSize(400, 300)
        
        layout = QFormLayout(dialog)
        
        key_input = QLineEdit()
        value_input = QLineEdit()
        type_combo = QComboBox()
        type_combo.addItems(["text", "number", "boolean", "formula"])
        
        layout.addRow("اسم الإعداد:", key_input)
        layout.addRow("القيمة:", value_input)
        layout.addRow("نوع البيانات:", type_combo)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        
        layout.addRow(btn_box)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                self.db.conn.execute("""
                    INSERT INTO policy_details (
                        policy_id, setting_key, setting_value, data_type, created_by, updated_by
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.policy['id'],
                    key_input.text(),
                    value_input.text(),
                    type_combo.currentText(),
                    self.current_user,
                    self.current_user
                ))
                self.db.conn.commit()
                self.load_policy_details()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل إضافة الإعداد: {str(e)}")

    def edit_setting(self):
        selected = self.details_table.currentRow()
        if selected >= 0:
            detail_id = int(self.details_table.item(selected, 0).text())
            current_key = self.details_table.item(selected, 1).text()
            current_value = self.details_table.item(selected, 2).text()
            current_type = self.details_table.item(selected, 3).text()
            
            dialog = QDialog(self)
            dialog.setWindowTitle("تعديل الإعداد")
            dialog.setFixedSize(400, 300)
            
            layout = QFormLayout(dialog)
            
            key_input = QLineEdit(current_key)
            value_input = QLineEdit(current_value)
            type_combo = QComboBox()
            type_combo.addItems(["text", "number", "boolean", "formula"])
            type_combo.setCurrentText(current_type)
            
            layout.addRow("اسم الإعداد:", key_input)
            layout.addRow("القيمة:", value_input)
            layout.addRow("نوع البيانات:", type_combo)
            
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            btn_box.accepted.connect(dialog.accept)
            btn_box.rejected.connect(dialog.reject)
            
            layout.addRow(btn_box)
            
            if dialog.exec_() == QDialog.Accepted:
                try:
                    self.db.conn.execute("""
                        UPDATE policy_details SET
                        setting_key = ?, setting_value = ?, data_type = ?, updated_by = ?, updated_at = ?
                        WHERE id = ?
                    """, (
                        key_input.text(),
                        value_input.text(),
                        type_combo.currentText(),
                        self.current_user,
                        datetime.now(),
                        detail_id
                    ))
                    self.db.conn.commit()
                    self.load_policy_details()
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"فشل تعديل الإعداد: {str(e)}")

    def remove_setting(self):
        selected = self.details_table.currentRow()
        if selected >= 0:
            detail_id = int(self.details_table.item(selected, 0).text())
            setting_name = self.details_table.item(selected, 1).text()
            
            confirm = QMessageBox.question(
                self, "تأكيد الحذف",
                f"هل أنت متأكد من حذف الإعداد '{setting_name}'؟",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                try:
                    self.db.conn.execute(
                        "DELETE FROM policy_details WHERE id = ?",
                        (detail_id,)
                    )
                    self.db.conn.commit()
                    self.load_policy_details()
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"فشل حذف الإعداد: {str(e)}")

    def save_changes(self):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                UPDATE policy_master SET
                name=?, category=?, description=?, editable=?, requires_approval=?,
                default_scope=?, version=?, updated_by=?, updated_at=?
                WHERE id=?
            """, (
                self.name_input.text(),
                self.category_combo.currentText(),
                self.description_input.currentText(),
                int(self.editable_check.isChecked()),
                int(self.approval_check.isChecked()),
                self.scope_combo.currentText(),
                self.version_input.text(),
                self.current_user,
                datetime.now(),
                self.policy['id']
            ))
            self.db.conn.commit()
            QMessageBox.information(self, "تم", "تم تحديث السياسة بنجاح")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحفظ: {str(e)}")

    def delete_policy(self):
        confirm = QMessageBox.question(
            self, "تأكيد الحذف", 
            f"هل أنت متأكد من حذف السياسة '{self.policy['name']}'؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            try:
                self.db.delete_policy(self.policy['id'])
                QMessageBox.information(self, "تم", "تم حذف السياسة بنجاح")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف: {str(e)}")

class PolicyEditor(QDialog):
    def __init__(self, db, policy=None):
        super().__init__()
        self.setWindowTitle("🆕 إضافة سياسة" if not policy else f"✏️ تعديل السياسة: {policy['name']}")
        self.setFixedSize(850, 650)
        self.db = db
        self.policy = policy
        self.current_user = "admin"
        self.settings_data = []
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }
            QGroupBox {
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
                background-color: white;
            }
            QTabWidget::pane {
                border: 1px solid #e2e8f0;
                border-radius: 5px;
            }
            QLabel {
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        
        self.build_ui()
        if policy:
            self.load_policy_data()

    def build_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        
        # تبويب المعلومات الأساسية
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # مجموعة المعلومات الأساسية
        info_group = QGroupBox("المعلومات الأساسية")
        info_layout = QFormLayout()
        
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("مثال: inventory_valuation_method")
        info_layout.addRow("🔑 مفتاح السياسة:", self.key_input)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: سياسة تقييم المخزون")
        info_layout.addRow("📌 اسم السياسة:", self.name_input)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(["مخزنية", "مالية", "تشغيلية", "مبيعات", "مشتريات"])
        info_layout.addRow("📂 نوع السياسة:", self.category_combo)
        
        self.description_input = QComboBox()
        self.description_input.addItems(self.db.get_inventory_account_types())
        info_layout.addRow("📝 الوصف (نوع حساب المخزون):", self.description_input)
        
        info_group.setLayout(info_layout)
        basic_layout.addWidget(info_group)
        
        # مجموعة الإعدادات الإضافية
        settings_group = QGroupBox("الإعدادات الإضافية")
        settings_layout = QFormLayout()
        
        self.editable_check = QCheckBox()
        self.editable_check.setChecked(True)
        settings_layout.addRow("قابلة للتعديل:", self.editable_check)
        
        self.approval_check = QCheckBox()
        settings_layout.addRow("تتطلب موافقة:", self.approval_check)
        
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["عام", "فرع", "قسم", "مستخدم"])
        settings_layout.addRow("نطاق التطبيق:", self.scope_combo)
        
        self.version_input = QLineEdit("1.0")
        settings_layout.addRow("إصدار السياسة:", self.version_input)
        
        settings_group.setLayout(settings_layout)
        basic_layout.addWidget(settings_group)
        
        basic_layout.addStretch()
        self.tabs.addTab(basic_tab, "المعلومات الأساسية")
        
        # تبويب الإعدادات التفصيلية
        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        
        # أزرار إدارة الإعدادات
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ إضافة إعداد")
        add_btn.setStyleSheet("background-color: #4299e1; color: white;")
        add_btn.clicked.connect(self.add_setting)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ تعديل")
        edit_btn.setStyleSheet("background-color: #f6ad55; color: white;")
        edit_btn.clicked.connect(self.edit_setting)
        btn_layout.addWidget(edit_btn)
        
        remove_btn = QPushButton("🗑️ حذف")
        remove_btn.setStyleSheet("background-color: #e53e3e; color: white;")
        remove_btn.clicked.connect(self.remove_setting)
        btn_layout.addWidget(remove_btn)
        
        details_layout.addLayout(btn_layout)
        
        # جدول الإعدادات
        self.settings_table = QTableWidget()
        self.settings_table.setColumnCount(3)
        self.settings_table.setHorizontalHeaderLabels(["الإعداد", "القيمة", "نوع البيانات"])
        self.settings_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.settings_table.setSelectionBehavior(QTableWidget.SelectRows)
        details_layout.addWidget(self.settings_table)
        
        self.tabs.addTab(details_tab, "الإعدادات التفصيلية")
        layout.addWidget(self.tabs)
        
        # أزرار الحفظ والإغلاق
        btn_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btn_box.button(QDialogButtonBox.Save).setText("💾 حفظ")
        btn_box.button(QDialogButtonBox.Cancel).setText("إلغاء")
        btn_box.button(QDialogButtonBox.Save).setStyleSheet("background-color: #38a169; color: white;")
        btn_box.button(QDialogButtonBox.Cancel).setStyleSheet("background-color: #a0aec0; color: white;")
        
        btn_box.accepted.connect(self.save_policy)
        btn_box.rejected.connect(self.reject)
        
        layout.addWidget(btn_box)

    def add_setting(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة إعداد جديد")
        dialog.setFixedSize(400, 300)
        
        layout = QFormLayout(dialog)
        
        key_input = QLineEdit()
        value_input = QLineEdit()
        type_combo = QComboBox()
        type_combo.addItems(["text", "number", "boolean", "formula"])
        
        layout.addRow("اسم الإعداد:", key_input)
        layout.addRow("القيمة:", value_input)
        layout.addRow("نوع البيانات:", type_combo)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        
        layout.addRow(btn_box)
        
        if dialog.exec_() == QDialog.Accepted:
            self.settings_data.append({
                "key": key_input.text(),
                "value": value_input.text(),
                "type": type_combo.currentText()
            })
            self.update_settings_table()

    def edit_setting(self):
        selected = self.settings_table.currentRow()
        if selected >= 0 and selected < len(self.settings_data):
            setting = self.settings_data[selected]
            
            dialog = QDialog(self)
            dialog.setWindowTitle("تعديل الإعداد")
            dialog.setFixedSize(400, 300)
            
            layout = QFormLayout(dialog)
            
            key_input = QLineEdit(setting["key"])
            value_input = QLineEdit(setting["value"])
            type_combo = QComboBox()
            type_combo.addItems(["text", "number", "boolean", "formula"])
            type_combo.setCurrentText(setting["type"])
            
            layout.addRow("اسم الإعداد:", key_input)
            layout.addRow("القيمة:", value_input)
            layout.addRow("نوع البيانات:", type_combo)
            
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            btn_box.accepted.connect(dialog.accept)
            btn_box.rejected.connect(dialog.reject)
            
            layout.addRow(btn_box)
            
            if dialog.exec_() == QDialog.Accepted:
                self.settings_data[selected] = {
                    "key": key_input.text(),
                    "value": value_input.text(),
                    "type": type_combo.currentText()
                }
                self.update_settings_table()

    def remove_setting(self):
        selected = self.settings_table.currentRow()
        if selected >= 0 and selected < len(self.settings_data):
            del self.settings_data[selected]
            self.update_settings_table()

    def update_settings_table(self):
        self.settings_table.setRowCount(len(self.settings_data))
        for row, setting in enumerate(self.settings_data):
            self.settings_table.setItem(row, 0, QTableWidgetItem(setting["key"]))
            self.settings_table.setItem(row, 1, QTableWidgetItem(setting["value"]))
            self.settings_table.setItem(row, 2, QTableWidgetItem(setting["type"]))

    def load_policy_data(self):
        if self.policy:
            self.key_input.setText(self.policy.get('key', ''))
            self.name_input.setText(self.policy.get('name', ''))
            self.category_combo.setCurrentText(self.policy.get('category', 'مخزنية'))
            self.description_input.setCurrentText(self.policy.get('description', 'متوسط التكلفة'))
            self.editable_check.setChecked(bool(self.policy.get('editable', True)))
            self.approval_check.setChecked(bool(self.policy.get('requires_approval', False)))
            self.scope_combo.setCurrentText(self.policy.get('default_scope', 'عام'))
            self.version_input.setText(self.policy.get('version', '1.0'))
            
            # تحميل الإعدادات التفصيلية
            details = self.db.get_policy_details(self.policy['id'])
            self.settings_data = [{
                "key": d['setting_key'],
                "value": d['setting_value'],
                "type": d['data_type']
            } for d in details]
            self.update_settings_table()

    def save_policy(self):
        key = self.key_input.text().strip()
        name = self.name_input.text().strip()
        category = self.category_combo.currentText()
        description = self.description_input.currentText()
        editable = 1 if self.editable_check.isChecked() else 0
        requires_approval = 1 if self.approval_check.isChecked() else 0
        default_scope = self.scope_combo.currentText()
        version = self.version_input.text().strip()

        if not key or not name:
            QMessageBox.warning(self, "⚠️ تنبيه", "يرجى إدخال المفتاح واسم السياسة.")
            return

        try:
            cursor = self.db.conn.cursor()
            
            if self.policy:
                # تحديث السياسة
                cursor.execute("""
                    UPDATE policy_master SET 
                    key=?, name=?, category=?, description=?, editable=?,
                    requires_approval=?, default_scope=?, version=?, updated_by=?, updated_at=?
                    WHERE id=?
                """, (
                    key, name, category, description, editable, requires_approval,
                    default_scope, version, self.current_user, datetime.now(), self.policy['id']
                ))
                policy_id = self.policy['id']
            else:
                # إضافة سياسة جديدة
                cursor.execute("""
                    INSERT INTO policy_master (
                        key, name, category, description, editable, requires_approval,
                        default_scope, version, created_by, updated_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    key, name, category, description, editable, requires_approval,
                    default_scope, version, self.current_user, self.current_user
                ))
                policy_id = cursor.lastrowid
            
            # حفظ الإعدادات التفصيلية
            cursor.execute("DELETE FROM policy_details WHERE policy_id = ?", (policy_id,))
            
            for setting in self.settings_data:
                cursor.execute("""
                    INSERT INTO policy_details (
                        policy_id, setting_key, setting_value, data_type, created_by, updated_by
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    policy_id, setting["key"], setting["value"], setting["type"],
                    self.current_user, self.current_user
                ))
            
            self.db.conn.commit()
            QMessageBox.information(self, "✅ تم", "تم حفظ السياسة بنجاح.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "❌ خطأ", f"حدث خطأ أثناء حفظ السياسة: {str(e)}")

class PolicyViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📋 نظام إدارة السياسات المخزنية")
        self.setGeometry(100, 100, 1100, 750)
        
        # تحسين المظهر العام
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(240, 244, 249))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(248, 250, 252))
        self.setPalette(palette)
        
        self.db = DBManager()
        self.current_user = "admin"
        self.build_ui()

    def build_ui(self):
        # إنشاء شريط القوائم
        menu_bar = QMenuBar(self)
        menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #2c5282;
                color: white;
                padding: 5px;
                font-weight: bold;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QMenuBar::item:selected {
                background-color: #4299e1;
            }
            QMenu {
                background-color: white;
                border: 1px solid #cbd5e0;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 25px 5px 20px;
            }
            QMenu::item:selected {
                background-color: #4299e1;
                color: white;
            }
        """)
        
        # قائمة "الملف"
        file_menu = menu_bar.addMenu("📁 الملف")
        
        add_action = QAction("➕ إضافة سياسة", self)
        add_action.triggered.connect(self.open_add_policy)
        file_menu.addAction(add_action)
        
        refresh_action = QAction("🔄 تحديث البيانات", self)
        refresh_action.triggered.connect(self.load_policies_into_table)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 خروج", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # قائمة "الإعدادات"
        settings_menu = menu_bar.addMenu("⚙️ الإعدادات")
        
        inventory_action = QAction("📦 أنواع المخزون", self)
        inventory_action.triggered.connect(self.open_inventory_types)
        settings_menu.addAction(inventory_action)
        
        self.setMenuBar(menu_bar)
        
        # شريط الأدوات الرئيسي
        main_toolbar = QToolBar("أدوات السياسات")
        main_toolbar.setIconSize(QSize(32, 32))
        main_toolbar.setStyleSheet("""
            QToolBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
                padding: 5px;
            }
            QToolButton {
                padding: 8px 12px;
                border-radius: 5px;
                background-color: #4299e1;
                color: white;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #3182ce;
            }
        """)
        self.addToolBar(main_toolbar)

        # إضافة سياسة جديدة
        add_action = QAction(QIcon.fromTheme("list-add"), "إضافة سياسة", self)
        add_action.triggered.connect(self.open_add_policy)
        main_toolbar.addAction(add_action)
        
        # إدارة أنواع المخزون
        inventory_action = QAction(QIcon.fromTheme("view-list-tree"), "أنواع المخزون", self)
        inventory_action.triggered.connect(self.open_inventory_types)
        main_toolbar.addAction(inventory_action)

        # زر تحديث البيانات
        refresh_action = QAction(QIcon.fromTheme("view-refresh"), "تحديث", self)
        refresh_action.triggered.connect(self.load_policies_into_table)
        main_toolbar.addAction(refresh_action)

        # شريط الحالة
        self.statusBar().showMessage("جاهز")

        # جدول السياسات
        self.policy_table = QTableWidget()
        self.policy_table.setColumnCount(7)
        self.policy_table.setHorizontalHeaderLabels([
            "ID", "الاسم", "التصنيف", "الوصف", "قابلة للتعديل", "الإصدار", "آخر تحديث"
        ])
        self.policy_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.policy_table.horizontalHeader().setStretchLastSection(True)
        self.policy_table.setAlternatingRowColors(True)
        self.policy_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.policy_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                gridline-color: #e2e8f0;
            }
            QHeaderView::section {
                background-color: #4299e1;
                color: white;
                padding: 5px;
                border: none;
            }
        """)
        
        # تحميل البيانات
        self.load_policies_into_table()
        self.policy_table.cellDoubleClicked.connect(self.open_policy_details)
        
        # التنسيق النهائي
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.policy_table)
        self.setCentralWidget(central_widget)

    def load_policies_into_table(self):
        try:
            policies = self.db.get_policies_by_category("مخزنية")
            self.policy_table.setRowCount(len(policies))
            
            for row_idx, policy in enumerate(policies):
                self.policy_table.setItem(row_idx, 0, QTableWidgetItem(str(policy["id"])))
                self.policy_table.setItem(row_idx, 1, QTableWidgetItem(policy["name"]))
                self.policy_table.setItem(row_idx, 2, QTableWidgetItem(policy["category"]))
                self.policy_table.setItem(row_idx, 3, QTableWidgetItem(policy["description"]))
                self.policy_table.setItem(row_idx, 4, QTableWidgetItem("✔" if policy["editable"] else "✖"))
                self.policy_table.setItem(row_idx, 5, QTableWidgetItem(policy["version"]))
                self.policy_table.setItem(row_idx, 6, QTableWidgetItem(policy.get("updated_at", "")))
            
            self.statusBar().showMessage(f"تم تحميل {len(policies)} سياسة")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل السياسات: {str(e)}")
            self.statusBar().showMessage("فشل تحميل البيانات")

    def open_policy_details(self, row, column):
        policy_id = int(self.policy_table.item(row, 0).text())
        policies = self.db.get_policies_by_category("مخزنية")
        selected_policy = next((p for p in policies if p["id"] == policy_id), None)
        
        if selected_policy:
            detail_dialog = PolicyDetailDialog(self.db, selected_policy)
            detail_dialog.exec_()
            self.load_policies_into_table()

    def open_add_policy(self):
        editor = PolicyEditor(self.db)
        if editor.exec_() == QDialog.Accepted:
            self.load_policies_into_table()

    def open_inventory_types(self):
        dialog = InventoryTypeDialog(self.db)
        dialog.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # تحسين الخطوط للعربية
    font = QFont("Arial", 12)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)
    
    # تحميل أيقونات إذا كانت متاحة
    if QIcon.hasThemeIcon("document-save"):
        QIcon.setThemeName("breeze")
    
    viewer = PolicyViewer()
    viewer.show()
    sys.exit(app.exec_())
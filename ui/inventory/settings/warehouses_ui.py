import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, 
    QComboBox, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
# ================================================================
# إعدادات المسارات الأساسية
# ================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..','..','..','..'))
if project_root not in sys.path:
    sys.path.append(project_root)
    
from database.manager.inventory.setting.warehouses_manager import WarehouseManager
from database.manager.inventory.setting.branch_manager import BranchManager
# تم حذف استيراد LocationManager لأنه لم يعد مستخدماً

class WarehousesUI(QWidget):
    def __init__(self, db_path: str):
        super().__init__()
        self.manager = WarehouseManager(db_path)
        self.branch_manager = BranchManager(db_path)
        
        self.setup_ui()
        self.load_branches()
        self.load_warehouses()
        self.setWindowTitle("نظام إدارة المخازن")
        self.setMinimumSize(1000, 600)

    def setup_ui(self):
        # الخط العام
        font = QFont('Arial', 12)
        self.setFont(font)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        self.setLayout(main_layout)

        # --- نموذج الإدخال ---
        form_layout = QHBoxLayout()
        form_layout.setSpacing(15)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("أدخل كود المخزن")
        form_layout.addWidget(QLabel("الكود:"))
        form_layout.addWidget(self.code_input)

        self.name_ar_input = QLineEdit()
        self.name_ar_input.setPlaceholderText("أدخل الاسم العربي")
        form_layout.addWidget(QLabel("الاسم عربي:"))
        form_layout.addWidget(self.name_ar_input)

        self.name_en_input = QLineEdit()
        self.name_en_input.setPlaceholderText("أدخل الاسم الإنجليزي")
        form_layout.addWidget(QLabel("الاسم إنجليزي:"))
        form_layout.addWidget(self.name_en_input)

        self.branch_input = QComboBox()
        self.branch_input.setPlaceholderText("اختر الفرع")
        form_layout.addWidget(QLabel("الفرع:"))
        form_layout.addWidget(self.branch_input)

        main_layout.addLayout(form_layout)

        # --- أزرار التحكم ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        buttons = [
            ("إضافة", self.add_warehouse, "#4CAF50"),
            ("تعديل", self.update_warehouse, "#2196F3"),
            ("حذف", self.delete_warehouse, "#f44336"),
            ("مسح الحقول", self.clear_form, "#607D8B"),
            ("تحديث البيانات", self.refresh_data, "#9C27B0")
        ]

        for text, handler, color in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color}; 
                    color: white; 
                    padding: 8px;
                    border-radius: 5px;
                    min-width: 100px;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                }}
            """)
            btn.setMinimumSize(120, 40)
            btn.clicked.connect(handler)
            button_layout.addWidget(btn)

        main_layout.addLayout(button_layout)

        # --- جدول العرض ---
        self.table = QTableWidget()
        # **تصحيح: تم تغيير عدد الأعمدة إلى 5**
        self.table.setColumnCount(5) 
        # **تصحيح: تم حذف عمود "الموقع"**
        self.table.setHorizontalHeaderLabels(["الكود", "الاسم العربي", "الاسم الإنجليزي", "الفرع", "معرّف"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        # **تصحيح: تعديل مؤشر العمود الأخير**
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        # **إخفاء عمود المعرف (ID) ليكون مخفياً للمستخدم ولكن متاحاً للبرنامج**
        self.table.setColumnHidden(4, True)

        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.cellClicked.connect(self.on_row_selected)
        
        main_layout.addWidget(self.table)

    def load_branches(self):
        """تحميل الفروع فقط"""
        self.branch_input.clear()
        self.branch_input.addItem("-- اختر الفرع --", None)
        branches = self.branch_manager.list_active_branches()
        for branch in branches:
            display_text = f"{branch['name_ar']} ({branch['code']})" if branch.get('code') else branch['name_ar']
            self.branch_input.addItem(display_text, branch["id"])

    def load_warehouses(self):
        """تحميل المخازن في الجدول"""
        self.table.setRowCount(0)
        warehouses = self.manager.list_active_warehouses()
        
        for row_idx, wh in enumerate(warehouses):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(wh.get("code", "")))
            self.table.setItem(row_idx, 1, QTableWidgetItem(wh.get("name_ar", "")))
            self.table.setItem(row_idx, 2, QTableWidgetItem(wh.get("name_en", "")))
            self.table.setItem(row_idx, 3, QTableWidgetItem(wh.get("branch_name", "")))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(wh["id"]))) # المعرف في العمود الخامس (index 4)

    def refresh_data(self):
        """تحديث كافة البيانات"""
        self.load_branches()
        self.load_warehouses()
        self.clear_form()
        QMessageBox.information(self, "تم", "تم تحديث البيانات بنجاح")

    def on_row_selected(self, row: int, _):
        """عند اختيار صف من الجدول"""
        if row < 0:
            return

        # **تصحيح: جلب المعرف من العمود الصحيح (index 4)**
        warehouse_id_item = self.table.item(row, 4)
        if not warehouse_id_item:
            return
            
        warehouse_id = int(warehouse_id_item.text())
        warehouses = self.manager.list_active_warehouses()
        selected_wh = next((wh for wh in warehouses if wh["id"] == warehouse_id), None)
        
        if not selected_wh:
            return

        self.code_input.setText(selected_wh.get("code", ""))
        self.name_ar_input.setText(selected_wh.get("name_ar", ""))
        self.name_en_input.setText(selected_wh.get("name_en", ""))
        
        branch_id = selected_wh.get("branch_id")
        if branch_id:
            branch_idx = self.branch_input.findData(branch_id)
            if branch_idx >= 0:
                self.branch_input.setCurrentIndex(branch_idx)

    def clear_form(self):
        """مسح جميع حقول الإدخال"""
        self.code_input.clear()
        self.name_ar_input.clear()
        self.name_en_input.clear()
        self.branch_input.setCurrentIndex(0)
        # **تصحيح: تم حذف السطر الخاص بـ location_input**
        self.table.clearSelection()

    def validate_inputs(self) -> bool:
        """التحقق من صحة البيانات المدخلة"""
        errors = []
        if not self.code_input.text().strip():
            errors.append("يجب إدخال كود المخزن")
        if not self.name_ar_input.text().strip():
            errors.append("يجب إدخال الاسم العربي للمخزن")
        if self.branch_input.currentIndex() == 0:
            errors.append("يجب اختيار الفرع")
            
        if errors:
            QMessageBox.warning(self, "تنبيه", "\n".join(errors))
            return False
        return True

    def add_warehouse(self):
        """إضافة مخزن جديد"""
        if not self.validate_inputs():
            return

        # **تصحيح: تم حذف location_id من القاموس**
        data = {
            "code": self.code_input.text().strip(),
            "name_ar": self.name_ar_input.text().strip(),
            "name_en": self.name_en_input.text().strip(),
            "branch_id": self.branch_input.currentData()
        }

        if self.manager.warehouse_exists(code=data["code"]):
            QMessageBox.warning(self, "تحذير", "كود المخزن موجود مسبقاً")
            return

        if self.manager.create_warehouse(**data):
            QMessageBox.information(self, "تم", "تمت إضافة المخزن بنجاح")
            self.load_warehouses()
            self.clear_form()
        else:
            QMessageBox.critical(self, "خطأ", "فشل في إضافة المخزن. يرجى التحقق من البيانات")

    def update_warehouse(self):
        """تعديل المخزن المحدد"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار مخزن من الجدول للتعديل")
            return

        if not self.validate_inputs():
            return

        # **تصحيح: جلب المعرف من العمود الصحيح (index 4)**
        warehouse_id = int(self.table.item(selected_row, 4).text())
        # **تصحيح: تم حذف location_id من القاموس**
        data = {
            "code": self.code_input.text().strip(),
            "name_ar": self.name_ar_input.text().strip(),
            "name_en": self.name_en_input.text().strip(),
            "branch_id": self.branch_input.currentData()
        }

        if self.manager.warehouse_exists(code=data["code"], exclude_id=warehouse_id):
            QMessageBox.warning(self, "تحذير", "كود المخزن موجود مسبقاً لمخزن آخر")
            return

        if self.manager.update_warehouse(warehouse_id, **data):
            QMessageBox.information(self, "تم", "تم تعديل بيانات المخزن بنجاح")
            self.load_warehouses()
            self.clear_form()
        else:
            QMessageBox.critical(self, "خطأ", "فشل في تعديل المخزن. يرجى المحاولة مرة أخرى")

    def delete_warehouse(self):
        """حذف المخزن المحدد"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار مخزن من الجدول للحذف")
            return
        # **تصحيح: جلب المعرف من العمود الصحيح (index 4)**
        warehouse_id = int(self.table.item(selected_row, 4).text())
        confirm = QMessageBox.question(
            self, "تأكيد الحذف", "هل أنت متأكد من حذف هذا المخزن؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if self.manager.delete_warehouse(warehouse_id):
                QMessageBox.information(self, "تم", "تم حذف المخزن بنجاح")
                self.load_warehouses()
                self.clear_form()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في حذف المخزن.")
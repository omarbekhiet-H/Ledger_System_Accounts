# ui/admin/NEWpermissions_window.py
import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QComboBox, QLineEdit,
                             QLabel, QMessageBox, QHeaderView, QGroupBox)
from PyQt5.QtCore import Qt

sys.path.append('..')

from database.manager.admin.NEWpermission_manager import NEWPermissionManager

class PermissionsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.permission_manager = NEWPermissionManager()
        self.initUI()
        self.load_styles() # تحميل التنسيقات
        
    def initUI(self):
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle("إدارة الصلاحيات")
        self.setGeometry(100, 100, 900, 600)
        
        layout = QVBoxLayout()
        
        control_group = QGroupBox("إدارة الصلاحيات")
        control_layout = QVBoxLayout()
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("بحث:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث في الصلاحيات...")
        self.search_input.textChanged.connect(self.filter_permissions)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addWidget(QLabel("التصنيف:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("جميع التصنيفات")
        self.category_combo.currentTextChanged.connect(self.filter_permissions)
        filter_layout.addWidget(self.category_combo)
        control_layout.addLayout(filter_layout)
        
        self.permissions_table = QTableWidget()
        self.permissions_table.setColumnCount(6)
        self.permissions_table.setHorizontalHeaderLabels([
            "ID", "كود الصلاحية", "الاسم العربي", "الاسم الإنجليزي", "الوحدة", "الحالة"
        ])
        self.permissions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.permissions_table.setSelectionBehavior(QTableWidget.SelectRows)
        control_layout.addWidget(self.permissions_table)
        
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("إضافة صلاحية")
        add_btn.setObjectName("saveButton")
        add_btn.clicked.connect(self.add_permission)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("تعديل")
        edit_btn.setObjectName("updateButton")
        edit_btn.clicked.connect(self.edit_permission)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("حذف")
        delete_btn.setObjectName("deleteButton")
        delete_btn.clicked.connect(self.delete_permission)
        button_layout.addWidget(delete_btn)
        
        toggle_btn = QPushButton("تفعيل/تعطيل")
        toggle_btn.clicked.connect(self.toggle_permission)
        button_layout.addWidget(toggle_btn)
        
        refresh_btn = QPushButton("تحديث")
        refresh_btn.setObjectName("clearButton")
        refresh_btn.clicked.connect(self.load_permissions)
        button_layout.addWidget(refresh_btn)

        button_layout.addStretch(1)

        close_btn = QPushButton("إغلاق")
        close_btn.setObjectName("deleteButton")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        control_layout.addLayout(button_layout)
        control_group.setLayout(control_layout)
        
        layout.addWidget(control_group)
        self.setLayout(layout)
        
        self.load_permissions()
        self.load_categories()
    
    def load_styles(self):
        """تحميل وتطبيق ملف التنسيق QSS"""
        try:
            style_path = os.path.join(os.path.dirname(__file__), '..', 'styles', 'styles.qss')
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Error loading QSS file: {e}")

    def load_permissions(self):
        """تحميل جميع الصلاحيات"""
        self.all_permissions = self.permission_manager.get_all_permissions()
        self.filter_permissions()
    
    def load_categories(self):
        """تحميل التصنيفات"""
        categories = self.permission_manager.get_permission_categories()
        self.category_combo.clear()
        self.category_combo.addItem("جميع التصنيفات")
        
        for category in categories:
            self.category_combo.addItem(category)
    
    def filter_permissions(self):
        """تصفية الصلاحيات المعروضة"""
        search_text = self.search_input.text().lower()
        selected_category = self.category_combo.currentText()
        
        filtered_permissions = []
        
        for perm in self.all_permissions:
            matches_search = (search_text in perm.get('name_ar', '').lower() or 
                             search_text in perm.get('name_en', '').lower() or 
                             search_text in perm.get('code', '').lower())
            
            if search_text and not matches_search:
                continue
            
            if selected_category != "جميع التصنيفات":
                if perm.get('name_ar', '') != selected_category:
                    continue
            
            filtered_permissions.append(perm)
        
        self.permissions_table.setRowCount(len(filtered_permissions))
        
        for row, perm in enumerate(filtered_permissions):
            self.permissions_table.setItem(row, 0, QTableWidgetItem(str(perm.get('id', ''))))
            self.permissions_table.setItem(row, 1, QTableWidgetItem(perm.get('code', '')))
            self.permissions_table.setItem(row, 2, QTableWidgetItem(perm.get('name_ar', '')))
            self.permissions_table.setItem(row, 3, QTableWidgetItem(perm.get('name_en', '')))
            self.permissions_table.setItem(row, 4, QTableWidgetItem(str(perm.get('module_id', ''))))
            self.permissions_table.setItem(row, 5, QTableWidgetItem("نشط" if perm.get('is_active', False) else "غير نشط"))
    
    def add_permission(self):
        QMessageBox.information(self, "إضافة", "سيتم تنفيذ إضافة صلاحية جديدة")
    
    def edit_permission(self):
        current_row = self.permissions_table.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "تحذير", "يجب اختيار صلاحية للتعديل")
            return
        
        permission_id = int(self.permissions_table.item(current_row, 0).text())
        QMessageBox.information(self, "تعديل", f"سيتم تعديل الصلاحية ذات ID: {permission_id}")
    
    def delete_permission(self):
        current_row = self.permissions_table.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "تحذير", "يجب اختيار صلاحية للحذف")
            return
        
        permission_id = int(self.permissions_table.item(current_row, 0).text())
        permission_name = self.permissions_table.item(current_row, 2).text()
        
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل تريد حذف الصلاحية '{permission_name}'؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "حذف", f"سيتم حذف الصلاحية: {permission_name}")
    
    def toggle_permission(self):
        current_row = self.permissions_table.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "تحذير", "يجب اختيار صلاحية للتفعيل/التعطيل")
            return
        
        permission_name = self.permissions_table.item(current_row, 2).text()
        current_status = self.permissions_table.item(current_row, 5).text()
        
        new_status = "تعطيل" if current_status == "نشط" else "تفعيل"
        QMessageBox.information(self, "تغيير الحالة", f"سيتم {new_status} الصلاحية: {permission_name}")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = PermissionsWindow()
    window.show()
    sys.exit(app.exec_())
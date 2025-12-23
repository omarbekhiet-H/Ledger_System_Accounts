import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, 
                             QLabel, QMessageBox, QHeaderView, QTabWidget, QFormLayout,
                             QGroupBox, QCheckBox, QComboBox, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from database.manager.user_manager import UserManager
from database.manager.permission_manager import PermissionManager

class UserManagementWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_manager = UserManager()
        self.permission_manager = PermissionManager()
        self.current_user_id = None
        self.initUI()
        self.load_users()
    
    def initUI(self):
        self.setWindowTitle("إدارة المستخدمين والصلاحيات")
        self.setGeometry(100, 100, 1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # إنشاء تبويبات
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # تبويب المستخدمين
        users_tab = QWidget()
        users_layout = QVBoxLayout(users_tab)
        tabs.addTab(users_tab, "المستخدمين")
        
        # تبويب الصلاحيات
        permissions_tab = QWidget()
        permissions_layout = QVBoxLayout(permissions_tab)
        tabs.addTab(permissions_tab, "الصلاحيات")
        
        # واجهة المستخدمين
        self.setup_users_ui(users_layout)
        # واجهة الصلاحيات
        self.setup_permissions_ui(permissions_layout)
    
    def setup_users_ui(self, layout):
        # شريط البحث
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث بالاسم أو اسم المستخدم...")
        self.search_input.textChanged.connect(self.search_users)
        search_layout.addWidget(self.search_input)
        
        # زر إضافة مستخدم
        add_btn = QPushButton("إضافة مستخدم جديد")
        add_btn.clicked.connect(self.show_add_user_dialog)
        search_layout.addWidget(add_btn)
        
        layout.addLayout(search_layout)
        
        # جدول المستخدمين
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "اسم المستخدم", "الاسم الكامل", "البريد الإلكتروني", 
            "الهاتف", "الحالة", "الإجراءات"
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.users_table)
    
    def setup_permissions_ui(self, layout):
        permissions_group = QGroupBox("إدارة الصلاحيات")
        permissions_layout = QVBoxLayout(permissions_group)
        
        # اختيار المستخدم
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("اختر المستخدم:"))
        
        self.user_combo = QComboBox()
        self.user_combo.currentIndexChanged.connect(self.load_user_permissions)
        user_layout.addWidget(self.user_combo)
        
        permissions_layout.addLayout(user_layout)
        
        # عرض الصلاحيات
        self.permissions_widget = QWidget()
        self.permissions_layout = QVBoxLayout(self.permissions_widget)
        permissions_layout.addWidget(self.permissions_widget)
        
        # زر الحفظ
        save_btn = QPushButton("حفظ الصلاحيات")
        save_btn.clicked.connect(self.save_user_permissions)
        permissions_layout.addWidget(save_btn)
        
        layout.addWidget(permissions_group)
        self.load_users_combo()
    
    def load_users(self):
        users = self.user_manager.get_all_users()
        self.users_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
            self.users_table.setItem(row, 1, QTableWidgetItem(user['username']))
            self.users_table.setItem(row, 2, QTableWidgetItem(user['full_name']))
            self.users_table.setItem(row, 3, QTableWidgetItem(user['email'] or ''))
            self.users_table.setItem(row, 4, QTableWidgetItem(user['phone'] or ''))
            
            status_item = QTableWidgetItem("نشط" if user['is_active'] else "غير نشط")
            status_item.setForeground(Qt.green if user['is_active'] else Qt.red)
            self.users_table.setItem(row, 5, status_item)
            
            # أزرار الإجراءات
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            
            edit_btn = QPushButton("تعديل")
            edit_btn.clicked.connect(lambda _, uid=user['id']: self.edit_user(uid))
            
            toggle_btn = QPushButton("تفعيل/تعطيل")
            toggle_btn.clicked.connect(lambda _, uid=user['id']: self.toggle_user(uid))
            
            delete_btn = QPushButton("حذف")
            delete_btn.clicked.connect(lambda _, uid=user['id']: self.delete_user(uid))
            
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(toggle_btn)
            action_layout.addWidget(delete_btn)
            
            self.users_table.setCellWidget(row, 6, action_widget)
    
    def search_users(self):
        search_text = self.search_input.text().lower()
        users = self.user_manager.get_all_users()
        
        filtered_users = [
            user for user in users 
            if search_text in user['username'].lower() or 
               search_text in user['full_name'].lower() or
               search_text in (user['email'] or '').lower() or
               search_text in (user['phone'] or '').lower()
        ]
        
        self.users_table.setRowCount(len(filtered_users))
        for row, user in enumerate(filtered_users):
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
            self.users_table.setItem(row, 1, QTableWidgetItem(user['username']))
            # ... نفس باقي الخلايا
    
    def show_add_user_dialog(self):
        dialog = UserDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_users()
    
    def edit_user(self, user_id):
        user = self.user_manager.get_user_by_id(user_id)
        if user:
            dialog = UserDialog(self, user)
            if dialog.exec_() == QDialog.Accepted:
                self.load_users()
    
    def toggle_user(self, user_id):
        success, message = self.user_manager.toggle_user_status(user_id)
        QMessageBox.information(self, "نتيجة العملية", message)
        if success:
            self.load_users()
    
    def delete_user(self, user_id):
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا المستخدم؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.user_manager.delete_user(user_id)
            QMessageBox.information(self, "نتيجة العملية", message)
            if success:
                self.load_users()
                self.load_users_combo()
    
    def load_users_combo(self):
        self.user_combo.clear()
        users = self.user_manager.get_all_users()
        for user in users:
            self.user_combo.addItem(f"{user['full_name']} ({user['username']})", user['id'])
    
    def load_user_permissions(self):
        # مسح الواجهة الحالية
        for i in reversed(range(self.permissions_layout.count())): 
            self.permissions_layout.itemAt(i).widget().setParent(None)
        
        user_id = self.user_combo.currentData()
        if not user_id:
            return
        
        user_permissions = self.user_manager.get_user_permissions(user_id)
        all_permissions = self.permission_manager.get_all_permissions()
        categories = self.permission_manager.get_permission_categories()
        
        for category in categories:
            group = QGroupBox(category)
            group_layout = QVBoxLayout(group)
            
            category_perms = [p for p in all_permissions if p['category'] == category]
            for perm in category_perms:
                checkbox = QCheckBox(perm['description'])
                checkbox.setChecked(perm['code'] in user_permissions)
                checkbox.setProperty('permission_id', perm['id'])
                group_layout.addWidget(checkbox)
            
            self.permissions_layout.addWidget(group)
    
    def save_user_permissions(self):
        user_id = self.user_combo.currentData()
        if not user_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار مستخدم أولاً")
            return
        
        selected_permissions = []
        for i in range(self.permissions_layout.count()):
            group = self.permissions_layout.itemAt(i).widget()
            if isinstance(group, QGroupBox):
                for j in range(group.layout().count()):
                    checkbox = group.layout().itemAt(j).widget()
                    if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                        selected_permissions.append(checkbox.property('permission_id'))
        
        success, message = self.permission_manager.set_user_permissions(user_id, selected_permissions)
        QMessageBox.information(self, "نتيجة العملية", message)

class UserDialog(QDialog):
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self.user_manager = UserManager()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("إضافة مستخدم" if not self.user else "تعديل مستخدم")
        self.setModal(True)
        
        layout = QFormLayout(self)
        
        self.username_input = QLineEdit()
        self.fullname_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.is_active_check = QCheckBox()
        self.is_active_check.setChecked(True)
        
        if self.user:
            self.username_input.setText(self.user['username'])
            self.fullname_input.setText(self.user['full_name'])
            self.email_input.setText(self.user['email'] or '')
            self.phone_input.setText(self.user['phone'] or '')
            self.is_active_check.setChecked(self.user['is_active'])
            self.password_input.setPlaceholderText("اتركه فارغاً للحفاظ على كلمة المرور الحالية")
        
        layout.addRow("اسم المستخدم:", self.username_input)
        layout.addRow("الاسم الكامل:", self.fullname_input)
        layout.addRow("البريد الإلكتروني:", self.email_input)
        layout.addRow("الهاتف:", self.phone_input)
        layout.addRow("كلمة المرور:", self.password_input)
        layout.addRow("نشط:", self.is_active_check)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def accept(self):
        username = self.username_input.text().strip()
        fullname = self.fullname_input.text().strip()
        email = self.email_input.text().strip() or None
        phone = self.phone_input.text().strip() or None
        password = self.password_input.text().strip()
        is_active = self.is_active_check.isChecked()
        
        if not username or not fullname:
            QMessageBox.warning(self, "تحذير", "يرجى ملء الحقول الإلزامية")
            return
        
        if self.user:
            # تحديث المستخدم
            update_data = {
                'username': username,
                'full_name': fullname,
                'email': email,
                'phone': phone,
                'is_active': is_active
            }
            if password:
                update_data['password'] = password
            
            success, message = self.user_manager.update_user(self.user['id'], **update_data)
        else:
            # إنشاء مستخدم جديد
            if not password:
                QMessageBox.warning(self, "تحذير", "كلمة المرور مطلوبة")
                return
            
            success, message = self.user_manager.create_user(
                username, password, fullname, email, phone, is_active
            )
        
        if success:
            super().accept()
        else:
            QMessageBox.critical(self, "خطأ", message)
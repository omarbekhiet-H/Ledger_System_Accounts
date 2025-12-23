import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QLabel, QFormLayout, QStyle, QComboBox
)
from PyQt5.QtCore import Qt

try:
    from database.manager.admin.NEWuser_manager import NEWUserManager
    from .NEWreset_password_window import ResetPasswordWindow
    print("✅ Successfully imported NEWUserManager")
except ImportError as e:
    print(f"❌ Import error: {e}")
    class NEWUserManager:
        def __init__(self, db_path=None): pass
        def get_all_users(self): return []
        def create_user(self, *a, **k): return False, "فشل"
        def update_user(self, *a, **k): return False, "فشل"
        def delete_user(self, *a, **k): return False, "فشل"
        def toggle_user_status(self, *a, **k): return False, "فشل"

    class ResetPasswordWindow(QDialog):
        def __init__(self, user_id=None, parent=None): super().__init__(parent)


class UserManagementWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_manager = NEWUserManager()
        self.initUI()
        self.load_styles() # تحميل التنسيقات
        self.load_users()
    
    def initUI(self):
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle("إدارة المستخدمين")
        self.setFixedSize(800, 550)

        layout = QVBoxLayout(self)

        # ✅ شريط البحث
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث عن مستخدم بالاسم أو البريد...")
        search_btn = QPushButton("🔍 بحث")
        search_btn.setObjectName("searchButton")
        search_btn.clicked.connect(self.filter_users)

        search_layout.addWidget(QLabel("البحث:"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)

        # ✅ الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "اسم المستخدم", "الاسم الكامل", "البريد الإلكتروني", "الحالة"]
        )
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # ✅ الأزرار
        btn_layout = QHBoxLayout()

        add_btn = QPushButton(" إضافة")
        add_btn.setObjectName("saveButton")
        add_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        add_btn.clicked.connect(self.add_user)

        edit_btn = QPushButton(" تعديل")
        edit_btn.setObjectName("updateButton")
        edit_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        edit_btn.clicked.connect(self.edit_user)

        reset_btn = QPushButton(" كلمة مرور")
        reset_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        reset_btn.clicked.connect(self.reset_password)

        toggle_btn = QPushButton(" تفعيل/تعطيل")
        toggle_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        toggle_btn.clicked.connect(self.toggle_status)

        delete_btn = QPushButton(" حذف")
        delete_btn.setObjectName("deleteButton")
        delete_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        delete_btn.clicked.connect(self.delete_user)
        
        close_btn = QPushButton("إغلاق")
        close_btn.setObjectName("deleteButton") # لتطبيق اللون الأحمر
        close_btn.clicked.connect(self.close)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(reset_btn)
        btn_layout.addWidget(toggle_btn)
        btn_layout.addWidget(delete_btn)
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

    def load_users(self):
        users = self.user_manager.get_all_users() or []
        self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(str(user["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(user["username"]))
            self.table.setItem(row, 2, QTableWidgetItem(user.get("full_name") or ""))
            self.table.setItem(row, 3, QTableWidgetItem(user.get("email") or ""))
            self.table.setItem(row, 4, QTableWidgetItem("نشط" if user.get("is_active") else "معطل"))

    def filter_users(self):
        text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def get_selected_user_id(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار مستخدم أولاً")
            return None
        return int(self.table.item(selected, 0).text())

    def add_user(self):
        dialog = UserFormDialog(self.user_manager, parent=self)
        if dialog.exec_():
            self.load_users()

    def edit_user(self):
        user_id = self.get_selected_user_id()
        if not user_id: return
        dialog = UserFormDialog(self.user_manager, user_id=user_id, parent=self)
        if dialog.exec_():
            self.load_users()

    def reset_password(self):
        user_id = self.get_selected_user_id()
        if not user_id: return
        dialog = ResetPasswordWindow(user_id=user_id, parent=self)
        dialog.exec_()

    def toggle_status(self):
        user_id = self.get_selected_user_id()
        if not user_id: return
        success, msg = self.user_manager.toggle_user_status(user_id)
        QMessageBox.information(self, "الحالة", msg)
        self.load_users()

    def delete_user(self):
        user_id = self.get_selected_user_id()
        if not user_id: return
        confirm = QMessageBox.question(self, "تأكيد", "هل أنت متأكد من حذف المستخدم؟")
        if confirm == QMessageBox.Yes:
            success, msg = self.user_manager.delete_user(user_id)
            QMessageBox.information(self, "حذف", msg)
            self.load_users()



class UserFormDialog(QDialog):
    def __init__(self, user_manager, user_id=None, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.user_id = user_id
        self.initUI()
        if user_id:
            self.load_user_data()
    
    def initUI(self):
        self.setWindowTitle("إضافة/تعديل مستخدم")
        self.setFixedSize(400, 350)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # الحقول
        self.username = QLineEdit()
        self.full_name = QLineEdit()
        self.email = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

        # الحقل الجديد: الحالة
        self.status = QComboBox()
        self.status.addItems(["نشط", "معطل"])
        
        form.addRow("اسم المستخدم:", self.username)
        form.addRow("الاسم الكامل:", self.full_name)
        form.addRow("البريد الإلكتروني:", self.email)
        form.addRow("كلمة المرور:", self.password)
        form.addRow("الحالة:", self.status)
        
        layout.addLayout(form)
        
        # الأزرار
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 حفظ")
        save_btn.setObjectName("saveButton")
        save_btn.clicked.connect(self.save_user)
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setObjectName("deleteButton")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def load_user_data(self):
        user = self.user_manager.get_user_by_id(self.user_id)
        if user:
            self.username.setText(user["username"])
            self.full_name.setText(user.get("full_name") or "")
            self.email.setText(user.get("email") or "")
            # ضبط الحالة
            self.status.setCurrentIndex(0 if user.get("is_active") else 1)
    
    def save_user(self):
        username = self.username.text().strip()
        full_name = self.full_name.text().strip()
        email = self.email.text().strip()
        password = self.password.text().strip()
        is_active = True if self.status.currentIndex() == 0 else False
        
        if not username:
            QMessageBox.warning(self, "خطأ", "اسم المستخدم مطلوب")
            return
        
        if self.user_id:
            success, msg = self.user_manager.update_user(
                self.user_id,
                username=username,
                name_ar=full_name,
                email=email,
                is_active=is_active
            )
        else:
            if not password:
                QMessageBox.warning(self, "خطأ", "كلمة المرور مطلوبة للمستخدم الجديد")
                return
            success, msg = self.user_manager.create_user(
                username, password, full_name, email, is_active
            )
        
        if success:
            QMessageBox.information(self, "نجاح", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "خطأ", msg)

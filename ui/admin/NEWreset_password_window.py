import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QMessageBox, QHBoxLayout, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

try:
    from database.manager.admin.NEWuser_manager import NEWUserManager
    print("✅ Successfully imported NEWuser_manager")
except ImportError as e:
    print(f"❌ Import error: {e}")
    class NEWUserManager:
        def __init__(self, db_path=None): pass
        def get_all_users(self): return []
        def get_user_by_id(self, user_id): return None
        def authenticate_user(self, username, password): return False, None, "فشل"
        def change_password(self, user_id, new_password): return False, "فشل"

class ResetPasswordWindow(QDialog):
    def __init__(self, parent=None, user_id=None): # user_id can be passed
        super().__init__(parent)
        self.user_id = user_id
        self.user_manager = NEWUserManager()
        self.initUI()
        self.load_users()
        self.load_styles()
    
    def load_styles(self):
        """تحميل ملف QSS"""
        # تم تصحيح المسار
        qss_path = os.path.join(os.path.dirname(__file__), '..', 'styles', 'styles.qss')
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Failed to load styles: {e}")

    def initUI(self):
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle("إعادة تعيين كلمة المرور")
        self.setFixedSize(420, 360)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("إعادة تعيين كلمة المرور")
        title.setObjectName("windowTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.user_combo = QComboBox()
        self.user_combo.setObjectName("userCombo")
        self.user_combo.currentIndexChanged.connect(self.on_user_selected)
        form_layout.addRow("اختر المستخدم:", self.user_combo)
        
        self.current_password = QLineEdit()
        self.current_password.setPlaceholderText("أدخل كلمة المرور الحالية")
        self.current_password.setEchoMode(QLineEdit.Password)
        self.current_password.setObjectName("currentPassword")
        
        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText("أدخل كلمة المرور الجديدة")
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setObjectName("newPassword")
        
        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("تأكيد كلمة المرور الجديدة")
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setObjectName("confirmPassword")
        self.confirm_password.returnPressed.connect(self.reset_password)
        
        form_layout.addRow("كلمة المرور الحالية:", self.current_password)
        form_layout.addRow("كلمة المرور الجديدة:", self.new_password)
        form_layout.addRow("تأكيد كلمة المرور:", self.confirm_password)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        
        reset_btn = QPushButton("تعيين")
        reset_btn.setObjectName("saveButton")
        reset_btn.clicked.connect(self.reset_password)
        
        # تم تغيير النص إلى "إغلاق"
        close_btn = QPushButton("إغلاق") 
        close_btn.setObjectName("deleteButton")
        close_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(reset_btn)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
    
    def load_users(self):
        """تحميل المستخدمين من قاعدة البيانات"""
        users = self.user_manager.get_all_users() or []
        self.user_combo.clear()
        current_selection_index = -1
        for i, u in enumerate(users):
            display_name = f"{u.get('full_name') or u['username']}"
            self.user_combo.addItem(display_name, u["id"])
            if self.user_id and u["id"] == self.user_id:
                current_selection_index = i
        
        if current_selection_index != -1:
            self.user_combo.setCurrentIndex(current_selection_index)
        elif users:
            self.user_id = users[0]["id"]
    
    def on_user_selected(self, index):
        """تحديث المستخدم المختار"""
        self.user_id = self.user_combo.itemData(index)
    
    def reset_password(self):
        """إعادة تعيين كلمة المرور"""
        current = self.current_password.text().strip()
        new = self.new_password.text().strip()
        confirm = self.confirm_password.text().strip()
        
        if not self.user_id:
            self.show_error("يرجى اختيار مستخدم")
            return
        
        if not current or not new or not confirm:
            self.show_error("يرجى ملء جميع الحقول")
            return
        
        if new != confirm:
            self.show_error("كلمة المرور الجديدة غير متطابقة")
            return
        
        if len(new) < 6:
            self.show_error("كلمة المرور يجب أن تكون 6 أحرف على الأقل")
            return
        
        user = self.user_manager.get_user_by_id(self.user_id)
        if user:
            success, _, _ = self.user_manager.authenticate_user(user['username'], current)
            if not success:
                self.show_error("كلمة المرور الحالية غير صحيحة")
                return
        
        success, message = self.user_manager.change_password(self.user_id, new)
        
        if success:
            QMessageBox.information(self, "نجاح", "تم تغيير كلمة المرور بنجاح")
            self.accept()
        else:
            self.show_error(message)
    
    def show_error(self, message):
        """إظهار رسالة خطأ"""
        self.error_label.setText(message)
        self.error_label.show()
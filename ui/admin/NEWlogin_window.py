# NEWlogin_window.py
import os
import sys
import time
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QCheckBox,
    QApplication, QStyle, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QFont, QPixmap

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

class LoginWindow(QDialog):
    login_success = pyqtSignal(dict)  # إشارة النجاح

    def __init__(self, user_manager, parent=None):  # التعديل هنا
        super().__init__(parent)
        self.user_manager = user_manager  # التعديل هنا
        self.error_label = None
        self.initUI()
        self.load_styles()

    def load_styles(self):
        """تحميل ملف التنسيق QSS"""
        try:
            style_path = os.path.join(os.path.dirname(__file__), '..', 'styles', 'styles.qss')
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"[WARNING] فشل تحميل ملف التنسيق: {e}")

    def initUI(self):
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle("ERP - تسجيل الدخول")
        self.setFixedSize(400, 350)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel("تسجيل الدخول")
        title_label.setObjectName("windowTitle")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        logo_label = QLabel()
        logo_path = os.path.join(project_root, "icons", "logo.png")
        logo_pixmap = QPixmap(logo_path) if os.path.exists(logo_path) else QPixmap()
        if not logo_pixmap.isNull():
            logo_label.setPixmap(
                logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            logo_label.setText("ERP")
            logo_label.setFont(QFont("Arial", 16, QFont.Bold))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.username_combo = QComboBox()
        self.username_combo.setEditable(False)
        self.username_combo.setObjectName("usernameCombo")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("أدخل كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setObjectName("passwordInput")
        self.password_input.textChanged.connect(self.clear_errors)
        self.password_input.returnPressed.connect(self.attempt_login)

        self.load_users()

        self.remember_check = QCheckBox("تذكرني")
        self.remember_check.setChecked(True)
        self.remember_check.setObjectName("rememberCheck")

        form_layout.addRow("اسم المستخدم:", self.username_combo)
        form_layout.addRow("كلمة المرور:", self.password_input)
        form_layout.addRow("", self.remember_check)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        login_btn = QPushButton("تسجيل الدخول")
        login_btn.setObjectName("loginButton")
        login_btn.setIcon(QApplication.style().standardIcon(QStyle.SP_DialogOkButton))
        login_btn.clicked.connect(self.attempt_login)
        login_btn.setDefault(True)

        close_btn = QPushButton("إغلاق")
        close_btn.setObjectName("deleteButton")
        close_btn.setIcon(QApplication.style().standardIcon(QStyle.SP_DialogCancelButton))
        close_btn.clicked.connect(self.reject)

        btn_layout.addWidget(login_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        self.load_saved_credentials()

    def load_users(self):
        """تحميل المستخدمين من UserManager إلى القائمة"""
        self.username_combo.clear()
        try:
            users = self.user_manager.get_all_users()
            if not users:
                self.show_error("⚠ لا توجد حسابات مستخدمين في قاعدة البيانات")
                return
            for user in users:
                display_name = user.get("full_name") or user.get("username")
                self.username_combo.addItem(display_name, user)
        except Exception as e:
            print(f"[ERROR] فشل تحميل المستخدمين: {e}")
            self.show_error("تعذّر تحميل قائمة المستخدمين")

    def load_saved_credentials(self):
        """تحميل بيانات تسجيل الدخول المحفوظة"""
        try:
            settings = QApplication.instance().settings if hasattr(QApplication.instance(), 'settings') else {}
            username = settings.get('remembered_username', '')
            if username:
                index = self.username_combo.findText(username)
                if index >= 0:
                    self.username_combo.setCurrentIndex(index)
                    self.remember_check.setChecked(True)
        except Exception:
            pass

    def save_credentials(self):
        """حفظ بيانات تسجيل الدخول إذا طلب المستخدم ذلك"""
        if self.remember_check.isChecked():
            try:
                if hasattr(QApplication.instance(), 'settings'):
                    QApplication.instance().settings['remembered_username'] = self.username_combo.currentText()
            except Exception:
                pass

    def clear_saved_credentials(self):
        """مسح بيانات تسجيل الدخول المحفوظة"""
        try:
            if hasattr(QApplication.instance(), 'settings'):
                if 'remembered_username' in QApplication.instance().settings:
                    del QApplication.instance().settings['remembered_username']
        except Exception:
            pass

    def clear_errors(self):
        if self.error_label:
            self.error_label.hide()
            self.error_label.clear()

    def attempt_login(self):
        user_data = self.username_combo.currentData()
        if not user_data:
            self.show_error("يرجى اختيار اسم المستخدم")
            return

        username = user_data["username"]
        password = self.password_input.text().strip()

        if not password:
            self.show_error("يرجى إدخال كلمة المرور")
            return

        self.setCursor(Qt.WaitCursor)
        QApplication.processEvents()

        success, user_data, message = self.user_manager.authenticate_user(username, password)

        self.setCursor(Qt.ArrowCursor)

        if success and user_data:
            if self.remember_check.isChecked():
                self.save_credentials()
            else:
                self.clear_saved_credentials()
            self.login_success.emit(user_data)
            self.accept()
        else:
            self.show_error(message)

    def show_error(self, message):
        if self.error_label:
            self.error_label.setText(message)
            self.error_label.show()
            self.shake_window()

    def shake_window(self):
        original_pos = self.pos()
        for i in range(5):
            new_pos = original_pos + QPoint(5 if i % 2 == 0 else -5, 0)
            self.move(new_pos)
            QApplication.processEvents()
            time.sleep(0.05)
        self.move(original_pos)

    def closeEvent(self, event):
        if not self.remember_check.isChecked():
            self.clear_saved_credentials()
        event.accept()

if __name__ == "__main__":
    # كود التجربة إذا شغلت الملف مباشرة
    from database.manager.admin.NEWuser_manager import NEWUserManager
    
    app = QApplication(sys.argv)
    user_manager = NEWUserManager()
    window = LoginWindow(user_manager)
    window.login_success.connect(lambda user_data: print(f"Login successful: {user_data}"))
    window.exec_()
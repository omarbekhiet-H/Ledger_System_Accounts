# ui/auth/login_window.py

import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QApplication, QHBoxLayout, QFrame, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap

# ======================= إعداد المسارات ==========================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# استيراد مدير المستخدمين وملف الاتصال
from database.manager.admin import session


from database.manager.admin.user_manager import UserManager
from database.db_connection import get_financials_db_connection

# ======================= نافذة تسجيل الدخول =======================
class LoginWindow(QWidget):
    # إشارة لإعلام نجاح تسجيل الدخول
    login_successful = pyqtSignal(dict, dict)

    def __init__(self):
        super().__init__()
        self.user_manager = UserManager(get_financials_db_connection)
        self.init_ui()

    def init_ui(self):
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle("تسجيل الدخول")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 450)
        self.setLayoutDirection(Qt.RightToLeft)

        # إنشاء الإطار الرئيسي
        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet("""
            #mainFrame {
                background-color: #ffffff;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
        """)

        # إعداد التخطيط الداخلي
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(40, 40, 40, 30)
        main_layout.setSpacing(25)

        # إضافة عناصر الواجهة
        self.add_logo(main_layout)
        self.add_title(main_layout)
        self.add_username_field(main_layout)
        self.add_password_field(main_layout)
        self.add_remember_me_option(main_layout)
        self.add_login_button(main_layout)
        self.add_forgot_password_link(main_layout)
        self.add_copyright_label(main_layout)

        # وضع الإطار داخل النافذة
        container_layout = QVBoxLayout()
        container_layout.addWidget(main_frame)
        container_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(container_layout)

        # ربط الأحداث
        self.username_input.returnPressed.connect(lambda: self.password_input.setFocus())
        self.password_input.returnPressed.connect(self.login_button.click)

    def add_logo(self, layout):
        logo_layout = QHBoxLayout()
        logo_label = QLabel()
        # شعار افتراضي، يمكن استبداله بصورة حقيقية
        logo_pixmap = QPixmap(100, 100)
        logo_pixmap.fill(Qt.transparent)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("background-color: #3498db; border-radius: 50px;")
        logo_label.setText("LOGO")  # استبداله بصورة
        logo_label.setFont(QFont("Arial", 14, QFont.Bold))
        logo_label.setFixedSize(100, 100)
        logo_layout.addWidget(logo_label, alignment=Qt.AlignCenter)
        layout.addLayout(logo_layout)

    def add_title(self, layout):
        title = QLabel("تسجيل الدخول")
        title.setFont(QFont("Arial", 22, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

    def add_username_field(self, layout):
        field_layout = QVBoxLayout()
        field_layout.setSpacing(5)

        label = QLabel("اسم المستخدم:")
        label.setFont(QFont("Arial", 10, QFont.Bold))
        label.setStyleSheet("color: #555;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("أدخل اسم المستخدم")
        self.username_input.setMinimumHeight(42)
        self.username_input.setStyleSheet(self.get_input_style())

        field_layout.addWidget(label)
        field_layout.addWidget(self.username_input)
        layout.addLayout(field_layout)

    def add_password_field(self, layout):
        field_layout = QVBoxLayout()
        field_layout.setSpacing(5)

        label = QLabel("كلمة المرور:")
        label.setFont(QFont("Arial", 10, QFont.Bold))
        label.setStyleSheet("color: #555;")

        input_layout = QHBoxLayout()

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("أدخل كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(42)
        self.password_input.setStyleSheet(self.get_input_style())

        self.toggle_password = QPushButton()
        self.toggle_password.setIcon(QIcon())  # أيقونة فارغة مؤقتاً
        self.toggle_password.setCheckable(True)
        self.toggle_password.setFixedSize(42, 42)
        self.toggle_password.setStyleSheet(self.get_toggle_button_style())

        self.toggle_password.clicked.connect(self.toggle_password_visibility)

        input_layout.addWidget(self.password_input)
        input_layout.addWidget(self.toggle_password)
        input_layout.setSpacing(0)

        field_layout.addWidget(label)
        field_layout.addLayout(input_layout)
        layout.addLayout(field_layout)

    def add_remember_me_option(self, layout):
        self.remember_me = QCheckBox("تذكر بيانات الدخول")
        self.remember_me.setFont(QFont("Arial", 9))
        self.remember_me.setStyleSheet("""
            QCheckBox {
                color: #555;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border: 1px solid #3498db;
            }
        """)
        layout.addWidget(self.remember_me)

    def add_login_button(self, layout):
        self.login_button = QPushButton("دخول")
        self.login_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.login_button.setMinimumHeight(48)
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.setStyleSheet(self.get_button_style())
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)

    def add_forgot_password_link(self, layout):
        link = QLabel("<a href='#' style='color: #3498db; text-decoration: none;'>نسيت كلمة المرور؟</a>")
        link.setFont(QFont("Arial", 9))
        link.setAlignment(Qt.AlignCenter)
        link.linkActivated.connect(self.show_forgot_password)
        layout.addWidget(link)

    def add_copyright_label(self, layout):
        label = QLabel("© 2023 نظام الإدارة المالية. جميع الحقوق محفوظة.")
        label.setFont(QFont("Arial", 8))
        label.setStyleSheet("color: #95a5a6;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

    def get_input_style(self):
        return """
            QLineEdit {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #ffffff;
            }
        """

    def get_toggle_button_style(self):
        return """
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-left: none;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """

    def get_button_style(self):
        return """
            QPushButton {
                background-color: #3498db;
                color: #fff;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6aa4;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """

    def toggle_password_visibility(self):
        if self.toggle_password.isChecked():
            self.password_input.setEchoMode(QLineEdit.Normal)
            # إزالة أيقونة العين مؤقتاً
            self.toggle_password.setText("إخفاء")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_password.setText("إظهار")

    def show_forgot_password(self):
        QMessageBox.information(
            self,
            "نسيت كلمة المرور",
            "لإعادة تعيين كلمة المرور، يرجى التواصل مع مدير النظام."
        )

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال اسم المستخدم وكلمة المرور.")
            self.username_input.setFocus()
            return

        # وضع حالة الانتظار أثناء التحقق
        self.login_button.setText("جاري التحقق...")
        self.login_button.setEnabled(False)
        QApplication.processEvents()

        try:
            # التحقق من المستخدم
            user_data = self.user_manager.verify_user(username, password)
            if user_data:

                from database.manager.admin import session
                session.set_current_user(user_data)
                print(f"DEBUG: Setting current user: {user_data}")


                permissions = self.user_manager.get_user_permissions(user_data['id'])
                QMessageBox.information(self, "نجاح", f"أهلاً بك، {user_data['full_name']}")
                self.login_successful.emit(user_data, permissions)
                self.close()
            else:
                QMessageBox.critical(self, "فشل الدخول", "اسم المستخدم أو كلمة المرور غير صحيحة.")
                self.password_input.setFocus()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تسجيل الدخول: {str(e)}")
            self.password_input.setFocus()
        finally:
            # إعادة تفعيل الزر
            self.login_button.setText("دخول")
            self.login_button.setEnabled(True)


# ======================= كود التشغيل =======================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # ستايل عام للرسائل
    app.setStyleSheet("""
        QMessageBox {
            font-family: Arial;
            font-size: 12px;
            background-color: #ffffff;
        }
        QMessageBox QLabel {
            color: #2c3e50;
        }
        QMessageBox QPushButton {
            background-color: #3498db;
            color: white;
            border-radius: 5px;
            padding: 5px 15px;
            min-width: 80px;
        }
        QMessageBox QPushButton:hover {
            background-color: #2980b9;
        }
    """)

    login_window = LoginWindow()

    def on_login_success(user, perms):
        print("\n" + "="*30)
        print(">>> تسجيل الدخول ناجح (إشارة استقبال) <<<")
        print("="*30)
        print(f"بيانات المستخدم: {user}")
        print(f"الصلاحيات: {perms}")
        print("="*30 + "\n")
        # يمكن هنا فتح النافذة الرئيسية بعد نجاح الدخول

    login_window.login_successful.connect(on_login_success)
    login_window.show()

    sys.exit(app.exec_())
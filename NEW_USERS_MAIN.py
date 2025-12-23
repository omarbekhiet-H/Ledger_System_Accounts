import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox, QAction, 
                             QToolBar, QStatusBar, QDesktopWidget)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

# إضافة مسار المشروع إلى sys.path
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_path)

from database.manager.admin.NEWuser_manager import NEWUserManager
from ui.admin.NEWlogin_window import LoginWindow
from ui.admin.NEWuser_management import UserManagementWindow
from ui.admin.NEWaudit_window import AuditWindow
from ui.admin.NEWlookup_window import LookupWindow
from ui.admin.NEWpermissions_window import PermissionsWindow
from ui.admin.NEWreset_password_window import ResetPasswordWindow
from ui.admin.NEWroles_window import RolesWindow
from ui.admin.NEWsetting_window import SettingWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_manager = NEWUserManager()
        self.current_user = None
        self.windows = {}  # لتخزين النوافذ المفتوحة
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("نظام ERP المتكامل - الإدارة المالية والمخزون")
        #self.setGeometry(10, 10, 1400, 800)
        #self.center_window()     # استدعاء دالة التوسيط
        screen = QDesktopWidget().availableGeometry()
        width = int(screen.width() * 0.95)
        height = int(screen.height() * 0.95)
        self.resize(width, height)
        self.center_window()
        
        # مركزية النافذة
        self.center_window()
        
        # تحميل الأيقونة إذا كانت موجودة
        if os.path.exists("icons/app_icon.png"):
            self.setWindowIcon(QIcon("icons/app_icon.png"))
        
        # إنشاء القوائم الرئيسية
        self.create_menus()
        
        # إنشاء شريط الأدوات
        self.create_toolbar()
        
        # إنشاء شريط الحالة
        self.statusBar().showMessage("جاهز")
        
        # إظهار نافذة تسجيل الدخول أولاً
        self.show_login()
    
    def center_window(self):
        """مركزية النافذة على الشاشة"""
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def create_menus(self):
        """إنشاء القوائم الرئيسية للتطبيق"""
        menubar = self.menuBar()
        menubar.setLayoutDirection(Qt.RightToLeft)  # عرض القوائم من اليمين
        
        # قائمة الملف
        file_menu = menubar.addMenu("الملف")
        
        logout_action = QAction("تسجيل الخروج", self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)
        
        exit_action = QAction("خروج", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # قائمة الإدارة
        admin_menu = menubar.addMenu("الإدارة")
        
        users_action = QAction("إدارة المستخدمين", self)
        users_action.triggered.connect(self.show_user_management)
        admin_menu.addAction(users_action)
        
        permissions_action = QAction("إدارة الصلاحيات", self)
        permissions_action.triggered.connect(self.show_permissions_management)
        admin_menu.addAction(permissions_action)
        
        roles_action = QAction("إدارة الأدوار", self)
        roles_action.triggered.connect(self.show_roles_management)
        admin_menu.addAction(roles_action)
        
        settings_action = QAction("إعدادات النظام", self)
        settings_action.triggered.connect(self.show_settings)
        admin_menu.addAction(settings_action)
        
        # قائمة البيانات المرجعية
        lookup_menu = menubar.addMenu("البيانات المرجعية")
        
        lookup_action = QAction("إدارة البيانات المرجعية", self)
        lookup_action.triggered.connect(self.show_lookup_management)
        lookup_menu.addAction(lookup_action)
        
        # قائمة المراجعة
        audit_menu = menubar.addMenu("المراجعة")
        
        audit_action = QAction("سجلات المراجعة", self)
        audit_action.triggered.connect(self.show_audit_logs)
        audit_menu.addAction(audit_action)
        
        # قائمة المساعدة
        help_menu = menubar.addMenu("المساعدة")
        
        about_action = QAction("حول النظام", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # قائمة اختبار (للتنمية فقط)
        if __name__ == "__main__":
            test_menu = menubar.addMenu("اختبار الواجهات")
            
            test_all_action = QAction("فتح جميع الواجهات", self)
            test_all_action.triggered.connect(self.open_all_windows)
            test_menu.addAction(test_all_action)
            
            test_login_action = QAction("اختبار تسجيل الدخول", self)
            test_login_action.triggered.connect(self.test_login)
            test_menu.addAction(test_login_action)
    
    def create_toolbar(self):
        """إنشاء شريط الأدوات"""
        toolbar = QToolBar("شريط الأدوات الرئيسي")
        self.addToolBar(Qt.RightToolBarArea, toolbar)  # على اليمين
        
        if os.path.exists("icons/user_management.png"):
            user_tool = QAction(QIcon("icons/user_management.png"), "إدارة المستخدمين", self)
            user_tool.triggered.connect(self.show_user_management)
            toolbar.addAction(user_tool)
        
        if os.path.exists("icons/permissions.png"):
            perm_tool = QAction(QIcon("icons/permissions.png"), "إدارة الصلاحيات", self)
            perm_tool.triggered.connect(self.show_permissions_management)
            toolbar.addAction(perm_tool)
        
        toolbar.addSeparator()
        
        if os.path.exists("icons/logout.png"):
            logout_tool = QAction(QIcon("icons/logout.png"), "تسجيل الخروج", self)
            logout_tool.triggered.connect(self.logout)
            toolbar.addAction(logout_tool)
    
    def show_login(self):
        self.login_window = LoginWindow(self)
        self.login_window.login_success.connect(self.handle_login_success)
        self.login_window.show()
    
    def handle_login_success(self, user_data):
        self.current_user = user_data
        self.statusBar().showMessage(f"مرحباً {user_data['full_name']} - {user_data['username']}")
        self.login_window.close()
        self.check_permissions()
    
    def check_permissions(self):
        pass
    
    def show_user_management(self):
        if self.current_user:
            if 'user_management' not in self.windows:
                self.windows['user_management'] = UserManagementWindow(self)
            self.windows['user_management'].show()
            self.windows['user_management'].raise_()
        else:
            QMessageBox.warning(self, "تحذير", "يجب تسجيل الدخول أولاً")
    
    def show_permissions_management(self):
        if self.current_user:
            if 'permissions' not in self.windows:
                self.windows['permissions'] = PermissionsWindow(self)
            self.windows['permissions'].show()
            self.windows['permissions'].raise_()
        else:
            QMessageBox.warning(self, "تحذير", "يجب تسجيل الدخول أولاً")
    
    def show_roles_management(self):
        if self.current_user:
            if 'roles' not in self.windows:
                self.windows['roles'] = RolesWindow(self)
            self.windows['roles'].show()
            self.windows['roles'].raise_()
        else:
            QMessageBox.warning(self, "تحذير", "يجب تسجيل الدخول أولاً")
    
    def show_settings(self):
        if self.current_user:
            if 'settings' not in self.windows:
                self.windows['settings'] = SettingWindow(self)
            self.windows['settings'].show()
            self.windows['settings'].raise_()
        else:
            QMessageBox.warning(self, "تحذير", "يجب تسجيل الدخول أولاً")
    
    def show_lookup_management(self):
        if self.current_user:
            if 'lookup' not in self.windows:
                self.windows['lookup'] = LookupWindow(self)
            self.windows['lookup'].show()
            self.windows['lookup'].raise_()
        else:
            QMessageBox.warning(self, "تحذير", "يجب تسجيل الدخول أولاً")
    
    def show_audit_logs(self):
        if self.current_user:
            if 'audit' not in self.windows:
                self.windows['audit'] = AuditWindow(self)
            self.windows['audit'].show()
            self.windows['audit'].raise_()
        else:
            QMessageBox.warning(self, "تحذير", "يجب تسجيل الدخول أولاً")
    
    def show_reset_password(self):
        if self.current_user:
            if 'reset_password' not in self.windows:
                self.windows['reset_password'] = ResetPasswordWindow(self)
            self.windows['reset_password'].show()
            self.windows['reset_password'].raise_()
        else:
            QMessageBox.warning(self, "تحذير", "يجب تسجيل الدخول أولاً")
    
    def logout(self):
        reply = QMessageBox.question(
            self, "تسجيل الخروج",
            "هل تريد تسجيل الخروج؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for window in self.windows.values():
                window.close()
            self.windows.clear()
            self.current_user = None
            self.statusBar().showMessage("تم تسجيل الخروج")
            self.show_login()
    
    def show_about(self):
        QMessageBox.about(
            self,
            "حول النظام",
            "نظام ERP المتكامل\n\n"
            "إصدار: 1.0.0\n"
            "التاريخ: 2025\n"
            "نظام متكامل للإدارة المالية والمخزون\n\n"
            "المطور: فريق التطوير"
        )
    
    def open_all_windows(self):
        if not self.current_user:
            QMessageBox.warning(self, "تحذير", "يجب تسجيل الدخول أولاً")
            return
        
        windows_to_open = [
            ('user_management', UserManagementWindow),
            ('permissions', PermissionsWindow),
            ('roles', RolesWindow),
            ('settings', SettingWindow),
            ('lookup', LookupWindow),
            ('audit', AuditWindow),
            ('reset_password', ResetPasswordWindow)
        ]
        
        for window_id, window_class in windows_to_open:
            if window_id not in self.windows:
                self.windows[window_id] = window_class(self)
            self.windows[window_id].show()
        
        self.arrange_windows()
    
    def arrange_windows(self):
        screen_geometry = QDesktopWidget().availableGeometry()
        x, y = 50, 50
        for window in self.windows.values():
            if window.isVisible():
                window.move(x, y)
                window.resize(800, 600)
                x += 30
                y += 30
                if x + 800 > screen_geometry.width():
                    x = 50
                if y + 600 > screen_geometry.height():
                    y = 50
    
    def test_login(self):
        test_user = {
            'id': 1,
            'username': 'admin',
            'full_name': 'مدير النظام',
            'email': 'admin@example.com',
            'phone': '0123456789',
            'is_active': True,
            'created_at': '2024-01-01'
        }
        self.handle_login_success(test_user)
        QMessageBox.information(self, "اختبار", "تم تسجيل الدخول كمدير نظام للاختبار")
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "تأكيد الخروج",
            "هل تريد الخروج من النظام؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for window in self.windows.values():
                window.close()
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    
    app.setApplicationName("نظام ERP المتكامل")
    app.setApplicationVersion("1.0.0")
    app.setStyle('Fusion')
    
    # تحميل ملف التنسيق من ui/styles/styles.qss
    qss_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "ui", "styles", "styles.qss"
    )
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        print("⚠️ ملف styles.qss غير موجود:", qss_path)
    
    main_window = MainWindow()
    main_window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

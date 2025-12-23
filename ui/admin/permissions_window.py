# ui/admin/permissions_window.py

import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QApplication, QCheckBox, QHBoxLayout
)
from PyQt5.QtCore import Qt

# --- إعداد المسارات ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# --- استيراد المدراء ---
from database.manager.admin.user_manager import UserManager
from database.db_connection import get_users_db_connection  # تغيير إلى اتصال المستخدمين

class PermissionsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        print("🔵 تهيئة نافذة الصلاحيات...")
        
        try:
            # استخدام اتصال قاعدة بيانات المستخدمين
            self.user_manager = UserManager(get_users_db_connection)
            print("🟢 تم تهيئة مدير المستخدمين بنجاح")
        except Exception as e:
            print(f"🔴 خطأ في تهيئة مدير المستخدمين: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"تعذر تهيئة مدير المستخدمين: {str(e)}")
            return
        
        self.setWindowTitle("إدارة صلاحيات الأدوار")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(900, 700)
        self.init_ui()
        
        try:
            self.load_permissions()
        except Exception as e:
            print(f"🔴 خطأ في تحميل الصلاحيات: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"تعذر تحميل الصلاحيات: {str(e)}")

    def init_ui(self):
        self.setLayoutDirection(Qt.RightToLeft)
        """تهيئة واجهة المستخدم"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # --- جدول الصلاحيات ---
        self.permissions_table = QTableWidget()
        self.permissions_table.setColumnCount(0)  # سيتم تحديد الأعمدة ديناميكياً
        self.permissions_table.setHorizontalHeaderLabels(["الصلاحية"])
        self.permissions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.permissions_table.verticalHeader().setVisible(False)
        layout.addWidget(self.permissions_table)

        # --- زر الحفظ ---
        save_btn = QPushButton("حفظ التغييرات")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_btn.clicked.connect(self.save_permissions)
        layout.addWidget(save_btn)

    def load_permissions(self):
        """تحميل وعرض مصفوفة الصلاحيات والأدوار"""
        print("🟡 جاري تحميل الصلاحيات...")
        
        try:
            roles = self.user_manager.get_all_roles()
            permissions = self.user_manager.get_all_permissions_matrix()

            if not roles:
                QMessageBox.warning(self, "تحذير", "لا توجد أدوار مسجلة في النظام")
                return
                
            if not permissions:
                QMessageBox.warning(self, "تحذير", "لا توجد صلاحيات مسجلة في النظام")
                return

            # --- إعداد الأعمدة بناءً على الأدوار ---
            self.permissions_table.setColumnCount(len(roles) + 1)
            header_labels = ["الصلاحية"] + [role.get('role_name_ar', role.get('role_name', 'دور')) for role in roles]
            self.permissions_table.setHorizontalHeaderLabels(header_labels)

            # --- إعداد الصفوف بناءً على مفاتيح الصلاحيات ---
            permission_keys = sorted(permissions.keys())
            self.permissions_table.setRowCount(len(permission_keys))

            for row, p_key in enumerate(permission_keys):
                # عرض اسم الصلاحية في العمود الأول
                self.permissions_table.setItem(row, 0, QTableWidgetItem(p_key))
                
                # عرض مربعات الاختيار لكل دور
                for col, role in enumerate(roles, start=1):
                    role_id = role.get('id')
                    if not role_id:
                        continue
                        
                    is_allowed = permissions[p_key].get(role_id, False)
                    
                    checkbox = QCheckBox()
                    checkbox.setChecked(is_allowed)
                    
                    # إنشاء حاوية لتوسيط مربع الاختيار
                    cell_widget = QWidget()
                    cell_layout = QHBoxLayout(cell_widget)
                    cell_layout.addWidget(checkbox)
                    cell_layout.setAlignment(Qt.AlignCenter)
                    cell_layout.setContentsMargins(0, 0, 0, 0)
                    
                    self.permissions_table.setCellWidget(row, col, cell_widget)
            
            print("🟢 تم تحميل الصلاحيات بنجاح")

        except Exception as e:
            print(f"🔴 خطأ في تحميل الصلاحيات: {str(e)}")
            raise

    def save_permissions(self):
        """حفظ التغييرات التي تم إجراؤها على الصلاحيات"""
        try:
            roles = self.user_manager.get_all_roles()
            if not roles:
                QMessageBox.critical(self, "خطأ", "لا توجد أدوار متاحة للحفظ")
                return

            permission_keys = []
            for row in range(self.permissions_table.rowCount()):
                item = self.permissions_table.item(row, 0)
                if item and item.text():
                    permission_keys.append(item.text())

            new_permissions = []
            for row, p_key in enumerate(permission_keys):
                for col, role in enumerate(roles, start=1):
                    role_id = role.get('id')
                    if not role_id:
                        continue
                        
                    cell_widget = self.permissions_table.cellWidget(row, col)
                    if not cell_widget:
                        continue
                        
                    checkbox = cell_widget.layout().itemAt(0).widget()
                    if checkbox:
                        is_allowed = checkbox.isChecked()
                        new_permissions.append((role_id, p_key, 1 if is_allowed else 0))

            if not new_permissions:
                QMessageBox.warning(self, "تحذير", "لا توجد تغييرات لحفظها")
                return

            if self.user_manager.update_role_permissions(new_permissions):
                QMessageBox.information(self, "نجاح", "تم حفظ صلاحيات الأدوار بنجاح")
            else:
                QMessageBox.critical(self, "خطأ", "حدث خطأ أثناء حفظ الصلاحيات")

        except Exception as e:
            print(f"🔴 خطأ أثناء الحفظ: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ غير متوقع: {str(e)}")

def main():
    """الدالة الرئيسية لتشغيل التطبيق"""
    try:
        app = QApplication(sys.argv)
        
        # تعيين ستايل للتطبيق
        app.setStyle('Fusion')
        
        window = PermissionsWindow()
        window.show()
        
        sys.exit(app.exec_())
    except Exception as e:
        print(f"🔴 خطأ جسيم: {str(e)}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    if exit_code != 0:
        input("اضغط Enter للخروج...")  # لمنع إغلاق النافذة فوراً عند الخطأ
    sys.exit(exit_code)
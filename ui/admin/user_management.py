import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QFormLayout,
    QLineEdit, QComboBox, QCheckBox, QApplication, QFrame, QLabel
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QFont, QPalette, QIcon

# =====================================================================
# تصحيح مسار المشروع الجذر
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)
    print(f"DEBUG: Project root set to -> {project_root}")

from database.manager.admin.user_manager import UserManager
from database.db_connection import get_financials_db_connection

class UserManagementWindows(QWidget):
    def __init__(self):
        super().__init__()
        self.user_manager = UserManager(get_financials_db_connection)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle("إدارة المستخدمين")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(900, 650)
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        # الإطار الرئيسي
        self.setStyleSheet("""
            QWidget {
                background-color: #F0F2F5;
                font-family: 'Segoe UI';
            }
            QFrame#main_frame {
                background-color: white;
                border: 3px solid #000000;
                border-radius: 10px;
            }
            QFrame#inner_frame {
                border: 1px solid #E74C3C;
                border-radius: 8px;
                padding: 10px;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #BDC3C7;
                gridline-color: #ECF0F1;
                font-size: 12px;
                selection-background-color: #3498DB;
                selection-color: white;
            }
            QTableWidget QHeaderView::section {
                background-color: #2C3E50;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #1A5276;
            }
            QPushButton#delete_btn {
                background-color: #E74C3C;
            }
            QPushButton#delete_btn:hover {
                background-color: #C0392B;
            }
        """)

        main_frame = QFrame()
        main_frame.setObjectName("main_frame")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.addWidget(main_frame)

        inner_frame = QFrame()
        inner_frame.setObjectName("inner_frame")
        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        frame_layout.addWidget(inner_frame)

        content_layout = QVBoxLayout(inner_frame)
        content_layout.setSpacing(15)

        # شريط العنوان
        title_bar = QFrame()
        title_bar.setStyleSheet("""
            background-color: #2C3E50;
            border-radius: 5px;
            padding: 12px;
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)

        title_label = QLabel("إدارة المستخدمين")
        title_label.setStyleSheet("""
            color: white;
            font-weight: bold;
            font-size: 16px;
            padding-right: 10px;
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        content_layout.addWidget(title_bar)

        # أزرار التحكم
        btn_container = QFrame()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        self.add_btn = QPushButton("إضافة مستخدم جديد")
        self.add_btn.setIcon(QIcon.fromTheme("list-add"))
        self.add_btn.setCursor(Qt.PointingHandCursor)

        self.edit_btn = QPushButton("تعديل المستخدم المحدد")
        self.edit_btn.setIcon(QIcon.fromTheme("document-edit"))
        self.edit_btn.setCursor(Qt.PointingHandCursor)

        self.delete_btn = QPushButton("حذف المستخدم المحدد")
        self.delete_btn.setObjectName("delete_btn")
        self.delete_btn.setIcon(QIcon.fromTheme("edit-delete"))
        self.delete_btn.setCursor(Qt.PointingHandCursor)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()

        content_layout.addWidget(btn_container)

        # جدول المستخدمين
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(["ID", "اسم المستخدم", "الاسم الكامل", "الدور", "الحالة"])
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.users_table.verticalHeader().setVisible(False)
        
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        content_layout.addWidget(self.users_table)

        # ربط الإشارات
        self.add_btn.clicked.connect(self.add_user)
        self.edit_btn.clicked.connect(self.edit_user)
        self.delete_btn.clicked.connect(self.delete_user)

    def load_users(self):
        self.users_table.setRowCount(0)
        users = self.user_manager.get_all_users_with_roles()
        if not users:
            return
            
        for row_num, user_data in enumerate(users):
            self.users_table.insertRow(row_num)
            
            # ID
            item = QTableWidgetItem(str(user_data['id']))
            item.setTextAlignment(Qt.AlignCenter)
            self.users_table.setItem(row_num, 0, item)
            
            # اسم المستخدم
            self.users_table.setItem(row_num, 1, QTableWidgetItem(user_data['username']))
            
            # الاسم الكامل
            self.users_table.setItem(row_num, 2, QTableWidgetItem(user_data['full_name']))
            
            # الدور
            role_item = QTableWidgetItem(user_data['role_name_ar'])
            role_item.setTextAlignment(Qt.AlignCenter)
            self.users_table.setItem(row_num, 3, role_item)
            
            # الحالة
            status = "فعال" if user_data['is_active'] else "معطل"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            if user_data['is_active']:
                status_item.setForeground(QColor('#27AE60'))
            else:
                status_item.setForeground(QColor('#E74C3C'))
            self.users_table.setItem(row_num, 4, status_item)

    def add_user(self):
        dialog = UserDialog(self.user_manager)
        if dialog.exec_() == QDialog.Accepted:
            self.load_users()

    def edit_user(self):
        selected_row = self.users_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "خطأ", "الرجاء تحديد مستخدم لتعديله.")
            return
        
        user_id = int(self.users_table.item(selected_row, 0).text())
        dialog = UserDialog(self.user_manager, user_id=user_id)
        if dialog.exec_() == QDialog.Accepted:
            self.load_users()

    def delete_user(self):
        selected_row = self.users_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "خطأ", "الرجاء تحديد مستخدم لحذفه.")
            return

        user_id = int(self.users_table.item(selected_row, 0).text())
        username = self.users_table.item(selected_row, 1).text()
        
        if username == 'admin':
            QMessageBox.critical(self, "غير مسموح", "لا يمكن حذف مستخدم 'admin' الرئيسي.")
            return

        reply = QMessageBox.question(
            self, 'تأكيد الحذف', 
            f"هل أنت متأكد من أنك تريد حذف المستخدم '{username}'؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.user_manager.delete_user(user_id):
                QMessageBox.information(self, "نجاح", "تم حذف المستخدم بنجاح.")
                self.load_users()
            else:
                QMessageBox.critical(self, "فشل", "فشل حذف المستخدم.")

class UserDialog(QDialog):
    def __init__(self, user_manager, user_id=None, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.user_id = user_id
        self.is_edit_mode = user_id is not None

        self.setWindowTitle("تعديل مستخدم" if self.is_edit_mode else "إضافة مستخدم جديد")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(500)
        self.setup_ui()
        
        if self.is_edit_mode:
            self.load_user_data()

    def setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #F0F2F5;
                font-family: 'Segoe UI';
            }
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
            }
            QLabel {
                font-weight: bold;
                font-size: 13px;
            }
            QLineEdit, QComboBox {
                border: 1px solid #BDC3C7;
                padding: 8px;
                border-radius: 4px;
                min-width: 250px;
                font-size: 13px;
            }
            QCheckBox {
                spacing: 5px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 80px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(15)

        self.username_input = QLineEdit()
        self.full_name_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.role_combo = QComboBox()
        self.is_active_check = QCheckBox("الحساب فعال")

        form_layout.addRow("اسم المستخدم:", self.username_input)
        form_layout.addRow("الاسم الكامل:", self.full_name_input)
        form_layout.addRow("كلمة المرور:", self.password_input)
        form_layout.addRow("الدور:", self.role_combo)
        form_layout.addRow(self.is_active_check)

        roles = self.user_manager.get_all_roles()
        for role in roles:
            self.role_combo.addItem(role['role_name_ar'], role['id'])

        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 10, 0, 0)

        self.save_btn = QPushButton("حفظ")
        self.save_btn.setIcon(QIcon.fromTheme("dialog-ok"))
        self.save_btn.setCursor(Qt.PointingHandCursor)

        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setIcon(QIcon.fromTheme("dialog-cancel"))
        self.cancel_btn.setCursor(Qt.PointingHandCursor)

        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)

        main_layout.addWidget(form_frame)
        main_layout.addWidget(btn_frame)

        self.save_btn.clicked.connect(self.save_user)
        self.cancel_btn.clicked.connect(self.reject)

    def load_user_data(self):
        user_data = self.user_manager.get_user_by_id(self.user_id)
        if user_data:
            self.username_input.setText(user_data['username'])
            self.username_input.setReadOnly(True)
            self.full_name_input.setText(user_data['full_name'])
            self.password_input.setPlaceholderText("اتركه فارغاً لعدم التغيير")
            
            role_index = self.role_combo.findData(user_data['role_id'])
            if role_index >= 0:
                self.role_combo.setCurrentIndex(role_index)
            
            self.is_active_check.setChecked(bool(user_data['is_active']))

    def save_user(self):
        username = self.username_input.text().strip()
        full_name = self.full_name_input.text().strip()
        password = self.password_input.text()
        role_id = self.role_combo.currentData()
        is_active = self.is_active_check.isChecked()

        if not username or not full_name:
            QMessageBox.warning(self, "خطأ", "يجب إدخال اسم المستخدم والاسم الكامل.")
            return

        if not self.is_edit_mode and not password:
            QMessageBox.warning(self, "خطأ", "يجب إدخال كلمة مرور للمستخدم الجديد.")
            return

        if self.is_edit_mode:
            if self.user_manager.update_user(self.user_id, full_name, password, role_id, is_active):
                QMessageBox.information(self, "نجاح", "تم تحديث بيانات المستخدم بنجاح.")
                self.accept()
            else:
                QMessageBox.critical(self, "فشل", "فشل تحديث بيانات المستخدم.")
        else:
            if self.user_manager.add_user(username, password, full_name, role_id, is_active):
                QMessageBox.information(self, "نجاح", "تمت إضافة المستخدم بنجاح.")
                self.accept()
            else:
                QMessageBox.critical(self, "فشل", "فشلت إضافة المستخدم. قد يكون اسم المستخدم موجوداً بالفعل.")

if __name__ == '__main__':
    app = QApplication(sys.argv)

    print("DEBUG: Initializing database for User Management test...")
    conn = get_financials_db_connection()
    if conn:
        try:
            from database.schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT
            from database.schems.default_data.financials_data_population import insert_default_data
            
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
            if not cursor.fetchone():
                print("DEBUG: Database schema not found. Initializing...")
                cursor.executescript(FINANCIALS_SCHEMA_SCRIPT)
                insert_default_data(conn)
                conn.commit()
                print("DEBUG: Database initialized successfully.")
            else:
                print("DEBUG: Database schema exists. Ensuring default data is populated...")
                insert_default_data(conn)
                print("DEBUG: Default data check complete.")
        except Exception as e:
            print(f"CRITICAL ERROR during DB initialization: {e}")
        finally:
            conn.close()

    window = UserManagementWindows()
    window.show()
    sys.exit(app.exec_())
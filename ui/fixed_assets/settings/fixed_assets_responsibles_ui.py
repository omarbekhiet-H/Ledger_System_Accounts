import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QComboBox, QDateEdit,
    QGridLayout, QTabWidget, QTextEdit, QCheckBox, QDialog, QSpinBox, QDoubleSpinBox,
    QGroupBox
)
from PyQt5.QtCore import Qt, QFile, QTextStream
from PyQt5.QtGui import QFont


# =====================================================================
# تصحيح مسار المشروع واستيراد دالة الاتصال
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# استيراد دالة الاتصال بقاعدة بيانات الأصول الثابتة (fallback لو مش موجود)
try:
    from database.db_connection import get_fixed_assets_db_connection
except Exception as e:
    print(f"⚠️ get_fixed_assets_db_connection Import fallback: {e}")
    def get_fixed_assets_db_connection():
        return None


# =====================================================================
# فئة مدير قاعدة البيانات باستخدام النمط الموحد
# =====================================================================
class ResponsiblesDBManager:
    def __init__(self):
        pass

    def _execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """
        دالة تنفيذ الاستعلامات العامة التي يمكن إعادة استخدامها
        """
        conn = None
        try:
            conn = get_fixed_assets_db_connection()
            if conn is None:
                # تشغيل بدون قاعدة بيانات (عرض فقط)
                return [] if fetch_all else (None if fetch_one else True)

            cursor = conn.cursor()
            cursor.execute(query, params or [])
            conn.commit()

            if fetch_one:
                row = cursor.fetchone()
                if row:
                    columns = [d[0] for d in cursor.description]
                    return dict(zip(columns, row))
                return None
            if fetch_all:
                rows = cursor.fetchall()
                if rows:
                    columns = [d[0] for d in cursor.description]
                    return [dict(zip(columns, r)) for r in rows]
                return []
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(None, "خطأ قاعدة البيانات", f"حدث خطأ: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_responsibles(self):
        query = "SELECT * FROM asset_responsibles ORDER BY name_ar"
        return self._execute_query(query, fetch_all=True)

    def search_responsibles(self, search_text):
        query = """SELECT * FROM asset_responsibles 
                   WHERE code LIKE ? OR name_ar LIKE ? OR name_en LIKE ? 
                   OR position LIKE ? OR department LIKE ? OR phone LIKE ? OR email LIKE ?
                   ORDER BY name_ar"""
        params = (f"%{search_text}%", f"%{search_text}%", f"%{search_text}%",
                 f"%{search_text}%", f"%{search_text}%", f"%{search_text}%", f"%{search_text}%")
        return self._execute_query(query, params, fetch_all=True)

    def get_responsible_by_id(self, responsible_id):
        query = "SELECT * FROM asset_responsibles WHERE id = ?"
        return self._execute_query(query, (responsible_id,), fetch_one=True)

    def add_responsible(self, code, name_ar, name_en, position, department, phone, email, is_active):
        query = """INSERT INTO asset_responsibles
                   (code, name_ar, name_en, position, department, phone, email, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        params = (code, name_ar, name_en, position, department, phone, email, 1 if is_active else 0)
        return self._execute_query(query, params)

    def update_responsible(self, responsible_id, code, name_ar, name_en, position, department, phone, email, is_active):
        query = """UPDATE asset_responsibles
                   SET code=?, name_ar=?, name_en=?, position=?, department=?,
                       phone=?, email=?, is_active=?
                   WHERE id=?"""
        params = (code, name_ar, name_en, position, department, phone, email, 1 if is_active else 0, responsible_id)
        return self._execute_query(query, params)

    def delete_responsible(self, responsible_id):
        query = "DELETE FROM asset_responsibles WHERE id = ?"
        return self._execute_query(query, (responsible_id,))

def load_stylesheet():
    """تحميل ملف QSS"""
    try:
        style_path = os.path.join(project_root, "ui", "styles", "styles.qss")
        if os.path.exists(style_path):
            style_file = QFile(style_path)
            if style_file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(style_file)
                style = stream.readAll()
                style_file.close()
                return style
        return ""
    except Exception as e:
        print(f"Error loading stylesheet: {e}")
        return ""


def check_database_connection():
    """التحقق من اتصال قاعدة البيانات"""
    conn = get_fixed_assets_db_connection()
    if conn is None:
        return False
    conn.close()
    return True

class ResponsibleDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.data = data
        self.db_manager = ResponsiblesDBManager()
        self.setWindowTitle("مسؤول" if not self.data else "تعديل مسؤول")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(load_stylesheet())
        self.setup_ui()
        if self.data: 
            self.load_data()

    def setup_ui(self):
        layout = QGridLayout(self)

        self.code_edit = QLineEdit()
        self.name_ar_edit = QLineEdit()
        self.name_en_edit = QLineEdit()
        self.position_edit = QLineEdit()
        self.department_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.status_check = QCheckBox("نشط")
        self.status_check.setChecked(True)

        layout.addWidget(QLabel("الكود:"), 0, 0)
        layout.addWidget(self.code_edit, 0, 1)
        
        layout.addWidget(QLabel("الاسم العربي:"), 1, 0)
        layout.addWidget(self.name_ar_edit, 1, 1)
        
        layout.addWidget(QLabel("الاسم الإنجليزي:"), 2, 0)
        layout.addWidget(self.name_en_edit, 2, 1)
        
        layout.addWidget(QLabel("المنصب:"), 3, 0)
        layout.addWidget(self.position_edit, 3, 1)
        
        layout.addWidget(QLabel("القسم:"), 4, 0)
        layout.addWidget(self.department_edit, 4, 1)
        
        layout.addWidget(QLabel("الهاتف:"), 5, 0)
        layout.addWidget(self.phone_edit, 5, 1)
        
        layout.addWidget(QLabel("البريد الإلكتروني:"), 6, 0)
        layout.addWidget(self.email_edit, 6, 1)
        
        layout.addWidget(QLabel("الحالة:"), 7, 0)
        layout.addWidget(self.status_check, 7, 1)

        btns = QHBoxLayout()
        save_btn = QPushButton("💾 حفظ")
        save_btn.clicked.connect(self.save_data)
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns, 8, 0, 1, 2)

    def load_data(self):
        self.code_edit.setText(self.data.get('code', ''))
        self.name_ar_edit.setText(self.data.get('name_ar', ''))
        self.name_en_edit.setText(self.data.get('name_en', ''))
        self.position_edit.setText(self.data.get('position', ''))
        self.department_edit.setText(self.data.get('department', ''))
        self.phone_edit.setText(self.data.get('phone', ''))
        self.email_edit.setText(self.data.get('email', ''))
        self.status_check.setChecked(bool(self.data.get('is_active', True)))

    def save_data(self):
        code = self.code_edit.text().strip()
        name_ar = self.name_ar_edit.text().strip()
        
        if not code or not name_ar:
            QMessageBox.warning(self, "تنبيه", "الكود والاسم العربي مطلوبان.")
            return
        
        name_en = self.name_en_edit.text().strip()
        position = self.position_edit.text().strip()
        department = self.department_edit.text().strip()
        phone = self.phone_edit.text().strip()
        email = self.email_edit.text().strip()
        is_active = self.status_check.isChecked()
        
        if self.data:
            # تحديث البيانات
            result = self.db_manager.update_responsible(
                self.data['id'], code, name_ar, name_en, position, 
                department, phone, email, is_active
            )
            if result:
                QMessageBox.information(self, "نجاح", "تم تحديث المسؤول بنجاح.")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في تحديث المسؤول.")
        else:
            # إضافة جديدة
            result = self.db_manager.add_responsible(
                code, name_ar, name_en, position, department, phone, email, is_active
            )
            if result:
                QMessageBox.information(self, "نجاح", "تم إضافة المسؤول بنجاح.")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في إضافة المسؤول.")

class ResponsiblesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db_manager = ResponsiblesDBManager()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Buttons layout
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ إضافة مسؤول")
        self.add_btn.clicked.connect(self.add_responsible)
        
        self.edit_btn = QPushButton("✏️ تعديل")
        self.edit_btn.clicked.connect(self.edit_responsible)
        
        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.clicked.connect(self.delete_responsible)
        
        self.refresh_btn = QPushButton("🔄 تحديث")
        self.refresh_btn.clicked.connect(self.load_data)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("بحث...")
        self.search_edit.textChanged.connect(self.search_data)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(QLabel("بحث:"))
        btn_layout.addWidget(self.search_edit)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "الكود", "الاسم العربي", "الاسم الإنجليزي", "المنصب",
            "القسم", "الهاتف", "البريد الإلكتروني", "الحالة"
        ])
        self.table.hideColumn(0)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        layout.addWidget(self.table)

    def load_data(self):
        responsibles = self.db_manager.get_responsibles()
        
        if responsibles is None:
            QMessageBox.warning(self, "تحذير", "❌ لا يمكن الاتصال بقاعدة البيانات")
            self.table.setRowCount(0)
            return
            
        self.table.setRowCount(len(responsibles))
        for row, item in enumerate(responsibles):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get('code', ''))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get('name_ar', ''))))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get('name_en', ''))))
            self.table.setItem(row, 4, QTableWidgetItem(str(item.get('position', ''))))
            self.table.setItem(row, 5, QTableWidgetItem(str(item.get('department', ''))))
            self.table.setItem(row, 6, QTableWidgetItem(str(item.get('phone', ''))))
            self.table.setItem(row, 7, QTableWidgetItem(str(item.get('email', ''))))
            
            status = "نشط" if item.get('is_active') else "غير نشط"
            self.table.setItem(row, 8, QTableWidgetItem(status))
        
        self.table.resizeColumnsToContents()

    def search_data(self):
        search_text = self.search_edit.text().strip()
        if not search_text:
            self.load_data()
            return
            
        responsibles = self.db_manager.search_responsibles(search_text)
        
        if responsibles is None:
            return
            
        self.table.setRowCount(len(responsibles))
        for row, item in enumerate(responsibles):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get('code', ''))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get('name_ar', ''))))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get('name_en', ''))))
            self.table.setItem(row, 4, QTableWidgetItem(str(item.get('position', ''))))
            self.table.setItem(row, 5, QTableWidgetItem(str(item.get('department', ''))))
            self.table.setItem(row, 6, QTableWidgetItem(str(item.get('phone', ''))))
            self.table.setItem(row, 7, QTableWidgetItem(str(item.get('email', ''))))
            
            status = "نشط" if item.get('is_active') else "غير نشط"
            self.table.setItem(row, 8, QTableWidgetItem(status))

    def add_responsible(self):
        dialog = ResponsibleDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()

    def edit_responsible(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "تحذير", "الرجاء اختيار مسؤول للتعديل")
            return
            
        responsible_id = self.table.item(selected_row, 0).text()
        responsible_data = self.db_manager.get_responsible_by_id(responsible_id)
        
        if not responsible_data:
            QMessageBox.warning(self, "تحذير", "❌ لا يمكن تحميل بيانات المسؤول")
            return
            
        dialog = ResponsibleDialog(self, responsible_data)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()

    def delete_responsible(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "تحذير", "الرجاء اختيار مسؤول للحذف")
            return
            
        responsible_id = self.table.item(selected_row, 0).text()
        responsible_name = self.table.item(selected_row, 2).text()
        
        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                   f"هل أنت متأكد من حذف المسؤول '{responsible_name}'؟",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            result = self.db_manager.delete_responsible(responsible_id)
            if result:
                QMessageBox.information(self, "نجاح", "تم حذف المسؤول بنجاح.")
                self.load_data()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في حذف المسؤول.")
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
class DepreciationDBManager:
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

    def get_depreciation_methods(self):
        query = "SELECT * FROM depreciation_methods ORDER BY name_ar"
        return self._execute_query(query, fetch_all=True)

    def search_depreciation_methods(self, search_text):
        query = """SELECT * FROM depreciation_methods 
                   WHERE code LIKE ? OR name_ar LIKE ? OR name_en LIKE ?
                   ORDER BY name_ar"""
        params = (f"%{search_text}%", f"%{search_text}%", f"%{search_text}%")
        return self._execute_query(query, params, fetch_all=True)

    def get_depreciation_method_by_id(self, method_id):
        query = "SELECT * FROM depreciation_methods WHERE id = ?"
        return self._execute_query(query, (method_id,), fetch_one=True)

    def add_depreciation_method(self, code, name_ar, name_en, is_active):
        query = """INSERT INTO depreciation_methods (code, name_ar, name_en, is_active)
                   VALUES (?, ?, ?, ?)"""
        params = (code, name_ar, name_en, 1 if is_active else 0)
        return self._execute_query(query, params)

    def update_depreciation_method(self, method_id, code, name_ar, name_en, is_active):
        query = """UPDATE depreciation_methods 
                   SET code=?, name_ar=?, name_en=?, is_active=?
                   WHERE id=?"""
        params = (code, name_ar, name_en, 1 if is_active else 0, method_id)
        return self._execute_query(query, params)

    def delete_depreciation_method(self, method_id):
        query = "DELETE FROM depreciation_methods WHERE id = ?"
        return self._execute_query(query, (method_id,))
        
def load_stylesheet():
    """تحميل ملف الأنماط من المسار المحدد"""
    try:
        # تحديد المسار الصحيح لملف الأنماط
        style_path = os.path.abspath(os.path.join(current_dir, '..', '..', 'styles', 'styles.qss'))
        
        if os.path.exists(style_path):
            file = QFile(style_path)
            if file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(file)
                style = stream.readAll()
                file.close()
                return style
        else:
            print(f"تحذير: ملف الأنماط غير موجود في: {style_path}")
            return ""
    except Exception as e:
        print(f"خطأ في تحميل ملف الأنماط: {e}")
        return ""

def check_database_connection():
    """التحقق من اتصال قاعدة البيانات"""
    conn = get_fixed_assets_db_connection()
    if conn is None:
        return False
    conn.close()
    return True

class DepreciationMethodDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.data = data
        self.db_manager = DepreciationDBManager()
        self.setWindowTitle("طريقة الإهلاك" if not self.data else "تعديل طريقة الإهلاك")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(load_stylesheet())
        self.setup_ui()
        if self.data: 
            self.load_data()

    def setup_ui(self):
        layout = QGridLayout(self)

        layout.addWidget(QLabel("الكود:"), 0, 0)
        self.code_edit = QLineEdit()
        layout.addWidget(self.code_edit, 0, 1)

        layout.addWidget(QLabel("الاسم العربي:"), 1, 0)
        self.name_ar_edit = QLineEdit()
        layout.addWidget(self.name_ar_edit, 1, 1)

        layout.addWidget(QLabel("الاسم الإنجليزي:"), 2, 0)
        self.name_en_edit = QLineEdit()
        layout.addWidget(self.name_en_edit, 2, 1)

        layout.addWidget(QLabel("الحالة:"), 3, 0)
        self.status_check = QCheckBox("نشط")
        self.status_check.setChecked(True)
        layout.addWidget(self.status_check, 3, 1)

        btns = QHBoxLayout()
        save_btn = QPushButton("💾 حفظ")
        save_btn.clicked.connect(self.save_data)
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns, 4, 0, 1, 2)

    def load_data(self):
        self.code_edit.setText(self.data.get('code', ''))
        self.name_ar_edit.setText(self.data.get('name_ar', ''))
        self.name_en_edit.setText(self.data.get('name_en', ''))
        self.status_check.setChecked(bool(self.data.get('is_active', True)))

    def save_data(self):
        code = self.code_edit.text().strip()
        name_ar = self.name_ar_edit.text().strip()
        name_en = self.name_en_edit.text().strip()
        
        if not code or not name_ar:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال الكود والاسم العربي.")
            return
        
        if self.data:
            # تحديث البيانات
            result = self.db_manager.update_depreciation_method(
                self.data['id'], code, name_ar, name_en, self.status_check.isChecked()
            )
            if result:
                QMessageBox.information(self, "نجاح", "تم تحديث طريقة الإهلاك بنجاح.")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في تحديث طريقة الإهلاك.")
        else:
            # إضافة جديدة
            result = self.db_manager.add_depreciation_method(
                code, name_ar, name_en, self.status_check.isChecked()
            )
            if result:
                QMessageBox.information(self, "نجاح", "تم إضافة طريقة الإهلاك بنجاح.")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في إضافة طريقة الإهلاك.")

class DepreciationMethodsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db_manager = DepreciationDBManager()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Buttons layout
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ إضافة طريقة")
        self.add_btn.clicked.connect(self.add_method)
        
        self.edit_btn = QPushButton("✏️ تعديل")
        self.edit_btn.clicked.connect(self.edit_method)
        
        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.clicked.connect(self.delete_method)
        
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
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "الكود", "الاسم العربي", "الاسم الإنجليزي", "الحالة"])
        self.table.hideColumn(0)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        layout.addWidget(self.table)

    def load_data(self):
        methods = self.db_manager.get_depreciation_methods()
        
        if methods is None:
            QMessageBox.warning(self, "تحذير", "❌ لا يمكن الاتصال بقاعدة البيانات")
            self.table.setRowCount(0)
            return
            
        self.table.setRowCount(len(methods))
        for row, item in enumerate(methods):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get('code', ''))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get('name_ar', ''))))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get('name_en', ''))))
            
            status = "نشط" if item.get('is_active') else "غير نشط"
            self.table.setItem(row, 4, QTableWidgetItem(status))
        
        self.table.resizeColumnsToContents()

    def search_data(self):
        search_text = self.search_edit.text().strip()
        if not search_text:
            self.load_data()
            return
            
        methods = self.db_manager.search_depreciation_methods(search_text)
        
        if methods is None:
            return
            
        self.table.setRowCount(len(methods))
        for row, item in enumerate(methods):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get('code', ''))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get('name_ar', ''))))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get('name_en', ''))))
            
            status = "نشط" if item.get('is_active') else "غير نشط"
            self.table.setItem(row, 4, QTableWidgetItem(status))

    def add_method(self):
        dialog = DepreciationMethodDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()

    def edit_method(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "تحذير", "الرجاء اختيار طريقة إهلاك للتعديل")
            return
            
        method_id = self.table.item(selected_row, 0).text()
        method_data = self.db_manager.get_depreciation_method_by_id(method_id)
        
        if not method_data:
            QMessageBox.warning(self, "تحذير", "❌ لا يمكن تحميل بيانات الطريقة")
            return
            
        dialog = DepreciationMethodDialog(self, method_data)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()

    def delete_method(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "تحذير", "الرجاء اختيار طريقة إهلاك للحذف")
            return
            
        method_id = self.table.item(selected_row, 0).text()
        method_name = self.table.item(selected_row, 2).text()
        
        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                   f"هل أنت متأكد من حذف طريقة الإهلاك '{method_name}'؟",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            result = self.db_manager.delete_depreciation_method(method_id)
            if result:
                QMessageBox.information(self, "نجاح", "تم حذف طريقة الإهلاك بنجاح.")
                self.load_data()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في حذف طريقة الإهلاك.")
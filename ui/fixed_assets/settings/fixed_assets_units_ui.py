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
class UnitsDBManager:
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

    def get_units(self):
        query = "SELECT * FROM measurement_units ORDER BY name_ar"
        return self._execute_query(query, fetch_all=True)

    def search_units(self, search_text):
        query = """SELECT * FROM measurement_units 
                   WHERE code LIKE ? OR name_ar LIKE ? OR name_en LIKE ? OR symbol LIKE ?
                   ORDER BY name_ar"""
        params = (f"%{search_text}%", f"%{search_text}%", f"%{search_text}%", f"%{search_text}%")
        return self._execute_query(query, params, fetch_all=True)

    def get_unit_by_id(self, unit_id):
        query = "SELECT * FROM measurement_units WHERE id = ?"
        return self._execute_query(query, (unit_id,), fetch_one=True)

    def add_unit(self, code, name_ar, name_en, symbol, is_active):
        query = """INSERT INTO measurement_units
                   (code, name_ar, name_en, symbol, is_active)
                   VALUES (?, ?, ?, ?, ?)"""
        params = (code, name_ar, name_en, symbol, 1 if is_active else 0)
        return self._execute_query(query, params)

    def update_unit(self, unit_id, code, name_ar, name_en, symbol, is_active):
        query = """UPDATE measurement_units
                   SET code=?, name_ar=?, name_en=?, symbol=?, is_active=?
                   WHERE id=?"""
        params = (code, name_ar, name_en, symbol, 1 if is_active else 0, unit_id)
        return self._execute_query(query, params)

    def delete_unit(self, unit_id):
        query = "DELETE FROM measurement_units WHERE id = ?"
        return self._execute_query(query, (unit_id,))


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

class UnitDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.data = data
        self.db_manager = UnitsDBManager()
        self.setWindowTitle("وحدة قياس" if not self.data else "تعديل وحدة قياس")
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
        self.symbol_edit = QLineEdit()
        self.status_check = QCheckBox("نشط")
        self.status_check.setChecked(True)

        layout.addWidget(QLabel("الكود:"), 0, 0)
        layout.addWidget(self.code_edit, 0, 1)
        
        layout.addWidget(QLabel("الاسم العربي:"), 1, 0)
        layout.addWidget(self.name_ar_edit, 1, 1)
        
        layout.addWidget(QLabel("الاسم الإنجليزي:"), 2, 0)
        layout.addWidget(self.name_en_edit, 2, 1)
        
        layout.addWidget(QLabel("الرمز:"), 3, 0)
        layout.addWidget(self.symbol_edit, 3, 1)
        
        layout.addWidget(QLabel("الحالة:"), 4, 0)
        layout.addWidget(self.status_check, 4, 1)

        btns = QHBoxLayout()
        save_btn = QPushButton("💾 حفظ")
        save_btn.clicked.connect(self.save_data)
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns, 5, 0, 1, 2)

    def load_data(self):
        self.code_edit.setText(self.data.get('code', ''))
        self.name_ar_edit.setText(self.data.get('name_ar', ''))
        self.name_en_edit.setText(self.data.get('name_en', ''))
        self.symbol_edit.setText(self.data.get('symbol', ''))
        self.status_check.setChecked(bool(self.data.get('is_active', True)))

    def save_data(self):
        code = self.code_edit.text().strip()
        name_ar = self.name_ar_edit.text().strip()
        
        if not code or not name_ar:
            QMessageBox.warning(self, "تنبيه", "الكود والاسم العربي مطلوبان.")
            return
        
        name_en = self.name_en_edit.text().strip()
        symbol = self.symbol_edit.text().strip()
        is_active = self.status_check.isChecked()
        
        if self.data:
            # تحديث البيانات
            result = self.db_manager.update_unit(
                self.data['id'], code, name_ar, name_en, symbol, is_active
            )
            if result:
                QMessageBox.information(self, "نجاح", "تم تحديث وحدة القياس بنجاح.")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في تحديث وحدة القياس.")
        else:
            # إضافة جديدة
            result = self.db_manager.add_unit(
                code, name_ar, name_en, symbol, is_active
            )
            if result:
                QMessageBox.information(self, "نجاح", "تم إضافة وحدة القياس بنجاح.")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في إضافة وحدة القياس.")

class UnitsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db_manager = UnitsDBManager()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Buttons layout
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ إضافة وحدة")
        self.add_btn.clicked.connect(self.add_unit)
        
        self.edit_btn = QPushButton("✏️ تعديل")
        self.edit_btn.clicked.connect(self.edit_unit)
        
        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.clicked.connect(self.delete_unit)
        
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
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "الكود", "الاسم العربي", "الاسم الإنجليزي", "الرمز", "الحالة"
        ])
        self.table.hideColumn(0)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        layout.addWidget(self.table)

    def load_data(self):
        units = self.db_manager.get_units()
        
        if units is None:
            QMessageBox.warning(self, "تحذير", "❌ لا يمكن الاتصال بقاعدة البيانات")
            self.table.setRowCount(0)
            return
            
        self.table.setRowCount(len(units))
        for row, item in enumerate(units):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get('code', ''))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get('name_ar', ''))))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get('name_en', ''))))
            self.table.setItem(row, 4, QTableWidgetItem(str(item.get('symbol', ''))))
            
            status = "نشط" if item.get('is_active') else "غير نشط"
            self.table.setItem(row, 5, QTableWidgetItem(status))
        
        self.table.resizeColumnsToContents()

    def search_data(self):
        search_text = self.search_edit.text().strip()
        if not search_text:
            self.load_data()
            return
            
        units = self.db_manager.search_units(search_text)
        
        if units is None:
            return
            
        self.table.setRowCount(len(units))
        for row, item in enumerate(units):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get('code', ''))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get('name_ar', ''))))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get('name_en', ''))))
            self.table.setItem(row, 4, QTableWidgetItem(str(item.get('symbol', ''))))
            
            status = "نشط" if item.get('is_active') else "غير نشط"
            self.table.setItem(row, 5, QTableWidgetItem(status))

    def add_unit(self):
        dialog = UnitDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()

    def edit_unit(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "تحذير", "الرجاء اختيار وحدة قياس للتعديل")
            return
            
        unit_id = self.table.item(selected_row, 0).text()
        unit_data = self.db_manager.get_unit_by_id(unit_id)
        
        if not unit_data:
            QMessageBox.warning(self, "تحذير", "❌ لا يمكن تحميل بيانات وحدة القياس")
            return
            
        dialog = UnitDialog(self, unit_data)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()

    def delete_unit(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "تحذير", "الرجاء اختيار وحدة قياس للحذف")
            return
            
        unit_id = self.table.item(selected_row, 0).text()
        unit_name = self.table.item(selected_row, 2).text()
        
        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                   f"هل أنت متأكد من حذف وحدة القياس '{unit_name}'؟",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            result = self.db_manager.delete_unit(unit_id)
            if result:
                QMessageBox.information(self, "نجاح", "تم حذف وحدة القياس بنجاح.")
                self.load_data()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في حذف وحدة القياس.")
# -*- coding: utf-8 -*-
# file: fixed_assets_categories_ui.py

import sys
import os
import sqlite3
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, 
                             QHeaderView, QCheckBox, QDialog, QGridLayout, QComboBox,
                             QSpinBox, QDoubleSpinBox)
from PyQt5.QtCore import Qt, QFile, QTextStream

# ------------------------------------------------------------
# تهيئة مسارات المشروع
# ------------------------------------------------------------
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
class CategoriesDBManager:
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

    def get_categories(self):
        query = """SELECT c.*, m.name_ar 
                   FROM fixed_asset_categories c 
                   LEFT JOIN depreciation_methods m ON c.depreciation_method_id = m.id 
                   ORDER BY c.name_ar"""
        return self._execute_query(query, fetch_all=True)

    def search_categories(self, search_text):
        query = """SELECT c.*, m.name_ar 
                   FROM fixed_asset_categories c 
                   LEFT JOIN depreciation_methods m ON c.depreciation_method_id = m.id 
                   WHERE c.code LIKE ? OR c.name_ar LIKE ? OR c.name_en LIKE ? OR m.name_ar LIKE ?
                   ORDER BY c.name_ar"""
        params = (f"%{search_text}%", f"%{search_text}%", f"%{search_text}%", f"%{search_text}%")
        return self._execute_query(query, params, fetch_all=True)

    def get_category_by_id(self, category_id):
        query = "SELECT * FROM fixed_asset_categories WHERE id = ?"
        return self._execute_query(query, (category_id,), fetch_one=True)

    def get_depreciation_methods(self):
        query = "SELECT id, name_ar FROM depreciation_methods WHERE is_active=1"
        return self._execute_query(query, fetch_all=True)

    def add_category(self, code, name_ar, name_en, category_type, depreciation_method_id, useful_life_years, depreciation_rate, is_active):
        query = """INSERT INTO fixed_asset_categories
                   (code, name_ar, name_en, category_type, depreciation_method_id,
                    useful_life_years, depreciation_rate, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        params = (code, name_ar, name_en, category_type, depreciation_method_id, useful_life_years, depreciation_rate, 1 if is_active else 0)
        return self._execute_query(query, params)

    def update_category(self, category_id, code, name_ar, name_en, category_type, depreciation_method_id, useful_life_years, depreciation_rate, is_active):
        query = """UPDATE fixed_asset_categories
                   SET code=?, name_ar=?, name_en=?, category_type=?, 
                       depreciation_method_id=?, useful_life_years=?, 
                       depreciation_rate=?, is_active=?
                   WHERE id=?"""
        params = (code, name_ar, name_en, category_type, depreciation_method_id, useful_life_years, depreciation_rate, 1 if is_active else 0, category_id)
        return self._execute_query(query, params)

    def delete_category(self, category_id):
        query = "DELETE FROM fixed_asset_categories WHERE id = ?"
        return self._execute_query(query, (category_id,))


def load_stylesheet():
    """تحميل ملف الأنماط من المسار المحدد"""
    try:
        # محاولة البحث عن ملف الأنماط في مسارات مختلفة
        possible_paths = [
            os.path.abspath(os.path.join(current_dir, '..', 'styles', 'styles.qss')),
            os.path.abspath(os.path.join(current_dir, '..', '..', 'styles', 'styles.qss')),
            os.path.abspath(os.path.join(current_dir, 'styles.qss'))
        ]
        
        for style_path in possible_paths:
            if os.path.exists(style_path):
                file = QFile(style_path)
                if file.open(QFile.ReadOnly | QFile.Text):
                    stream = QTextStream(file)
                    style = stream.readAll()
                    file.close()
                    return style
        
        print("⚠️ تحذير: لم يتم العثور على ملف الأنماط في أي من المسارات التالية:")
        for path in possible_paths:
            print(f"   - {path}")
        return ""
        
    except Exception as e:
        print(f"❌ خطأ في تحميل ملف الأنماط: {e}")
        return ""

def check_database_connection():
    """التحقق من اتصال قاعدة البيانات"""
    conn = get_fixed_assets_db_connection()
    if conn is None:
        return False
    conn.close()
    return True

class CategoryDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.data = data
        self.db_manager = CategoriesDBManager()
        self.setWindowTitle("تصنيف أصل" if not self.data else "تعديل تصنيف")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(load_stylesheet())
        self.setup_ui()
        self.load_depreciation_methods()
        if self.data: 
            self.load_data()

    def setup_ui(self):
        layout = QGridLayout(self)

        self.code_edit = QLineEdit()
        self.name_ar_edit = QLineEdit()
        self.name_en_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["fixed_asset", "intangible", "other"])
        self.method_combo = QComboBox()
        self.life_spin = QSpinBox()
        self.life_spin.setRange(1, 100)
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(0, 100)
        self.rate_spin.setDecimals(2)
        self.status_check = QCheckBox("نشط")
        self.status_check.setChecked(True)

        layout.addWidget(QLabel("الكود:"), 0, 0)
        layout.addWidget(self.code_edit, 0, 1)
        
        layout.addWidget(QLabel("الاسم العربي:"), 1, 0)
        layout.addWidget(self.name_ar_edit, 1, 1)
        
        layout.addWidget(QLabel("الاسم الإنجليزي:"), 2, 0)
        layout.addWidget(self.name_en_edit, 2, 1)
        
        layout.addWidget(QLabel("النوع:"), 3, 0)
        layout.addWidget(self.type_combo, 3, 1)
        
        layout.addWidget(QLabel("طريقة الإهلاك:"), 4, 0)
        layout.addWidget(self.method_combo, 4, 1)
        
        layout.addWidget(QLabel("العمر (سنة):"), 5, 0)
        layout.addWidget(self.life_spin, 5, 1)
        
        layout.addWidget(QLabel("معدل الإهلاك %:"), 6, 0)
        layout.addWidget(self.rate_spin, 6, 1)
        
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

    def load_depreciation_methods(self):
        methods = self.db_manager.get_depreciation_methods()
        
        if methods is None:
            QMessageBox.warning(self, "تحذير", "لا يمكن الاتصال بقاعدة البيانات")
            return
            
        self.method_combo.clear()
        
        # إضافة خيار افتراضي
        self.method_combo.addItem("-- اختر طريقة --", None)
        
        for method in methods:
            self.method_combo.addItem(method.get('name_ar', ''), method.get('id'))

    def load_data(self):
        try:
            self.code_edit.setText(self.data.get('code', ''))
            self.name_ar_edit.setText(self.data.get('name_ar', ''))
            self.name_en_edit.setText(self.data.get('name_en', ''))
            self.type_combo.setCurrentText(self.data.get('category_type', 'fixed_asset'))
            self.life_spin.setValue(int(self.data.get('useful_life_years', 1)))
            self.rate_spin.setValue(float(self.data.get('depreciation_rate', 0)))
            self.status_check.setChecked(bool(self.data.get('is_active', True)))
            
            # Set depreciation method
            method_id = self.data.get('depreciation_method_id')
            if method_id:
                for i in range(self.method_combo.count()):
                    if self.method_combo.itemData(i) == method_id:
                        self.method_combo.setCurrentIndex(i)
                        break
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل البيانات: {str(e)}")

    def save_data(self):
        code = self.code_edit.text().strip()
        name_ar = self.name_ar_edit.text().strip()
        
        if not code or not name_ar:
            QMessageBox.warning(self, "تنبيه", "الكود والاسم العربي مطلوبان.")
            return
        
        name_en = self.name_en_edit.text().strip()
        category_type = self.type_combo.currentText()
        method_id = self.method_combo.currentData()
        useful_life = self.life_spin.value()
        depreciation_rate = self.rate_spin.value()
        is_active = self.status_check.isChecked()
        
        if self.data:
            # تحديث البيانات
            result = self.db_manager.update_category(
                self.data['id'], code, name_ar, name_en, category_type, 
                method_id, useful_life, depreciation_rate, is_active
            )
            if result:
                QMessageBox.information(self, "نجاح", "تم تحديث التصنيف بنجاح.")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في تحديث التصنيف.")
        else:
            # إضافة جديدة
            result = self.db_manager.add_category(
                code, name_ar, name_en, category_type, method_id, 
                useful_life, depreciation_rate, is_active
            )
            if result:
                QMessageBox.information(self, "نجاح", "تم إضافة التصنيف بنجاح.")
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في إضافة التصنيف.")

class CategoriesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db_manager = CategoriesDBManager()
        self.setup_ui()
        
        # التحقق من اتصال قاعدة البيانات أولاً
        if not check_database_connection():
            QMessageBox.critical(self, "خطأ", "فشل في الاتصال بقاعدة البيانات. يرجى التحقق من الإعدادات.")
        else:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Buttons layout
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ إضافة تصنيف")
        self.add_btn.clicked.connect(self.add_category)
        
        self.edit_btn = QPushButton("✏️ تعديل")
        self.edit_btn.clicked.connect(self.edit_category)
        
        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.clicked.connect(self.delete_category)
        
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
            "ID", "الكود", "الاسم العربي", "الاسم الإنجليزي", "النوع", 
            "طريقة الإهلاك", "العمر (سنوات)", "معدل الإهلاك %", "الحالة"
        ])
        self.table.hideColumn(0)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        layout.addWidget(self.table)

    def load_data(self):
        categories = self.db_manager.get_categories()
        
        if categories is None:
            QMessageBox.warning(self, "تحذير", "لا يمكن الاتصال بقاعدة البيانات")
            self.table.setRowCount(0)
            return
            
        self.table.setRowCount(len(categories))
        for row, item in enumerate(categories):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get('code', ''))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get('name_ar', ''))))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get('name_en', ''))))
            self.table.setItem(row, 4, QTableWidgetItem(str(item.get('category_type', ''))))
            self.table.setItem(row, 5, QTableWidgetItem(str(item.get('name_ar', ''))))  # طريقة الإهلاك
            self.table.setItem(row, 6, QTableWidgetItem(str(item.get('useful_life_years', ''))))
            self.table.setItem(row, 7, QTableWidgetItem(str(item.get('depreciation_rate', ''))))
            
            status = "نشط" if item.get('is_active') else "غير نشط"
            self.table.setItem(row, 8, QTableWidgetItem(status))
        
        self.table.resizeColumnsToContents()

    def search_data(self):
        search_text = self.search_edit.text().strip()
        if not search_text:
            self.load_data()
            return
            
        categories = self.db_manager.search_categories(search_text)
        
        if categories is None:
            return
            
        self.table.setRowCount(len(categories))
        for row, item in enumerate(categories):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get('code', ''))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get('name_ar', ''))))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get('name_en', ''))))
            self.table.setItem(row, 4, QTableWidgetItem(str(item.get('category_type', ''))))
            self.table.setItem(row, 5, QTableWidgetItem(str(item.get('name_ar', ''))))  # طريقة الإهلاك
            self.table.setItem(row, 6, QTableWidgetItem(str(item.get('useful_life_years', ''))))
            self.table.setItem(row, 7, QTableWidgetItem(str(item.get('depreciation_rate', ''))))
            
            status = "نشط" if item.get('is_active') else "غير نشط"
            self.table.setItem(row, 8, QTableWidgetItem(status))

    def add_category(self):
        dialog = CategoryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()

    def edit_category(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "تحذير", "الرجاء اختيار تصنيف للتعديل")
            return
            
        category_id = self.table.item(selected_row, 0).text()
        category_data = self.db_manager.get_category_by_id(category_id)
        
        if not category_data:
            QMessageBox.warning(self, "تحذير", "❌ لا يمكن تحميل بيانات التصنيف")
            return
            
        dialog = CategoryDialog(self, category_data)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()

    def delete_category(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "تحذير", "الرجاء اختيار تصنيف للحذف")
            return
            
        category_id = self.table.item(selected_row, 0).text()
        category_name = self.table.item(selected_row, 2).text()
        
        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                   f"هل أنت متأكد من حذف التصنيف '{category_name}'؟",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            result = self.db_manager.delete_category(category_id)
            if result:
                QMessageBox.information(self, "نجاح", "تم حذف التصنيف بنجاح")
                self.load_data()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في حذف التصنيف")

# اختبار التشغيل المستقل
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # التحقق من اتصال قاعدة البيانات أولاً
    if not check_database_connection():
        print("❌ فشل في الاتصال بقاعدة البيانات. يرجى التحقق من الإعدادات.")
    else:
        window = CategoriesTab()
        window.setWindowTitle("إدارة تصنيفات الأصول")
        window.resize(1000, 600)
        window.show()
    
    sys.exit(app.exec_())
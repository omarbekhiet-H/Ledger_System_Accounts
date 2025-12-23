# -*- coding: utf-8 -*-
# file: fixed_assets_settings_ui.py

import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QComboBox, QDateEdit,
    QGridLayout, QGroupBox, QTabWidget, QTextEdit, QCheckBox, QSpacerItem, QSizePolicy,
    QTreeWidget, QTreeWidgetItem, QAbstractItemView, QDialog, QSpinBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QDate, QFile, QTextStream
from PyQt5.QtGui import QFont, QIcon, QPixmap


# =====================================================================
# تصحيح مسار المشروع الجذر لتمكين الاستيراد الصحيح
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..')) 
if project_root not in sys.path:
    sys.path.append(project_root)

from database.db_connection import get_fixed_assets_db_connection

def load_stylesheet():
    """تحميل ملف الأنماط من المسار المحدد"""
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

class RTLDialog(QDialog):
    """فئة أساسية للحوارات مع دعم اللغة العربية من اليمين لليسار"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(load_stylesheet())

class DepreciationMethodDialog(RTLDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.data = data
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("طريقة الإهلاك" if not self.data else "تعديل طريقة الإهلاك")
        self.setFixedSize(450, 350)
        
        layout = QGridLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Code
        layout.addWidget(QLabel("الكود:"), 0, 0, Qt.AlignRight)
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("أدخل كود طريقة الإهلاك")
        layout.addWidget(self.code_edit, 0, 1)
        
        # Arabic Name
        layout.addWidget(QLabel("الاسم العربي:"), 1, 0, Qt.AlignRight)
        self.name_ar_edit = QLineEdit()
        self.name_ar_edit.setPlaceholderText("أدخل الاسم العربي")
        layout.addWidget(self.name_ar_edit, 1, 1)
        
        # English Name
        layout.addWidget(QLabel("الاسم الإنجليزي:"), 2, 0, Qt.AlignRight)
        self.name_en_edit = QLineEdit()
        self.name_en_edit.setPlaceholderText("أدخل الاسم الإنجليزي")
        layout.addWidget(self.name_en_edit, 2, 1)
        
        # Status
        self.status_check = QCheckBox("نشط")
        self.status_check.setChecked(True)
        layout.addWidget(QLabel("الحالة:"), 3, 0, Qt.AlignRight)
        layout.addWidget(self.status_check, 3, 1, Qt.AlignLeft)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("💾 حفظ")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_data)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout, 4, 0, 1, 2)
        
        self.setLayout(layout)
        
        # Load data if editing
        if self.data:
            self.load_data()
    
    def load_data(self):
        self.code_edit.setText(self.data[1])
        self.name_ar_edit.setText(self.data[2])
        self.name_en_edit.setText(self.data[3])
        self.status_check.setChecked(self.data[4] == 'نشط')
    
    def save_data(self):
        code = self.code_edit.text().strip()
        name_ar = self.name_ar_edit.text().strip()
        name_en = self.name_en_edit.text().strip()
        
        if not code:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال الكود")
            return
        
        if not name_ar:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال الاسم العربي")
            return
        
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            
            if self.data:
                # Update
                cursor.execute("""
                    UPDATE depreciation_methods 
                    SET code=?, name_ar=?, name_en=?, is_active=?
                    WHERE id=?
                """, (code, name_ar, name_en, 1 if self.status_check.isChecked() else 0, self.data[0]))
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO depreciation_methods (code, name_ar, name_en, is_active)
                    VALUES (?, ?, ?, ?)
                """, (code, name_ar, name_en, 1 if self.status_check.isChecked() else 0))
            
            conn.commit()
            self.accept()
            QMessageBox.information(self, "نجاح", "تم حفظ البيانات بنجاح")
            
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "خطأ", "الكود أو الاسم موجود مسبقاً")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في الحفظ: {e}")
        finally:
            if conn:
                conn.close()

class CategoryDialog(RTLDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.data = data
        self.depreciation_methods = []
        self.setup_ui()
        self.load_depreciation_methods()
        
    def setup_ui(self):
        self.setWindowTitle("تصنيف الأصول" if not self.data else "تعديل تصنيف الأصول")
        self.setFixedSize(550, 500)
        
        layout = QGridLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Code
        layout.addWidget(QLabel("الكود:"), 0, 0, Qt.AlignRight)
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("أدخل كود التصنيف")
        layout.addWidget(self.code_edit, 0, 1)
        
        # Arabic Name
        layout.addWidget(QLabel("الاسم العربي:"), 1, 0, Qt.AlignRight)
        self.name_ar_edit = QLineEdit()
        self.name_ar_edit.setPlaceholderText("أدخل الاسم العربي")
        layout.addWidget(self.name_ar_edit, 1, 1)
        
        # English Name
        layout.addWidget(QLabel("الاسم الإنجليزي:"), 2, 0, Qt.AlignRight)
        self.name_en_edit = QLineEdit()
        self.name_en_edit.setPlaceholderText("أدخل الاسم الإنجليزي")
        layout.addWidget(self.name_en_edit, 2, 1)
        
        # Category Type
        layout.addWidget(QLabel("نوع التصنيف:"), 3, 0, Qt.AlignRight)
        self.type_combo = QComboBox()
        self.type_combo.addItems(['fixed_asset', 'intangible', 'other'])
        layout.addWidget(self.type_combo, 3, 1)
        
        # Depreciation Method
        layout.addWidget(QLabel("طريقة الإهلاك:"), 4, 0, Qt.AlignRight)
        self.method_combo = QComboBox()
        layout.addWidget(self.method_combo, 4, 1)
        
        # Useful Life
        layout.addWidget(QLabel("العمر الإفتراضي (سنوات):"), 5, 0, Qt.AlignRight)
        self.life_spin = QSpinBox()
        self.life_spin.setRange(1, 100)
        self.life_spin.setValue(5)
        layout.addWidget(self.life_spin, 5, 1)
        
        # Depreciation Rate
        layout.addWidget(QLabel("معدل الإهلاك (%):"), 6, 0, Qt.AlignRight)
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(0, 100)
        self.rate_spin.setValue(20.0)
        self.rate_spin.setDecimals(2)
        layout.addWidget(self.rate_spin, 6, 1)
        
        # Status
        self.status_check = QCheckBox("نشط")
        self.status_check.setChecked(True)
        layout.addWidget(QLabel("الحالة:"), 7, 0, Qt.AlignRight)
        layout.addWidget(self.status_check, 7, 1, Qt.AlignLeft)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("💾 حفظ")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_data)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout, 8, 0, 1, 2)
        
        self.setLayout(layout)
        
        # Load data if editing
        if self.data:
            self.load_data()
    
    def load_depreciation_methods(self):
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, name_ar FROM depreciation_methods WHERE is_active = 1")
            self.depreciation_methods = cursor.fetchall()
            
            self.method_combo.clear()
            for method_id, method_name in self.depreciation_methods:
                self.method_combo.addItem(method_name, method_id)
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل طرق الإهلاك: {e}")
        finally:
            if conn:
                conn.close()
    
    def load_data(self):
        self.code_edit.setText(self.data[1])
        self.name_ar_edit.setText(self.data[2])
        self.name_en_edit.setText(self.data[3])
        self.type_combo.setCurrentText(self.data[4])
        
        # Set depreciation method
        for idx in range(self.method_combo.count()):
            if self.method_combo.itemText(idx) == self.data[5]:
                self.method_combo.setCurrentIndex(idx)
                break
        
        self.life_spin.setValue(int(self.data[6]))
        self.rate_spin.setValue(float(self.data[7]))
        self.status_check.setChecked(self.data[8] == 'نشط')
    
    def save_data(self):
        code = self.code_edit.text().strip()
        name_ar = self.name_ar_edit.text().strip()
        name_en = self.name_en_edit.text().strip()
        
        if not code:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال الكود")
            return
        
        if not name_ar:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال الاسم العربي")
            return
        
        method_id = self.method_combo.currentData()
        if not method_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار طريقة إهلاك")
            return
        
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            
            if self.data:
                # Update
                cursor.execute("""
                    UPDATE fixed_asset_categories 
                    SET code=?, name_ar=?, name_en=?, category_type=?, 
                        depreciation_method_id=?, useful_life_years=?, depreciation_rate=?, is_active=?
                    WHERE id=?
                """, (code, name_ar, name_en, self.type_combo.currentText(),
                      method_id, self.life_spin.value(), self.rate_spin.value(),
                      1 if self.status_check.isChecked() else 0, self.data[0]))
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO fixed_asset_categories 
                    (code, name_ar, name_en, category_type, depreciation_method_id, 
                     useful_life_years, depreciation_rate, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (code, name_ar, name_en, self.type_combo.currentText(),
                      method_id, self.life_spin.value(), self.rate_spin.value(),
                      1 if self.status_check.isChecked() else 0))
            
            conn.commit()
            self.accept()
            QMessageBox.information(self, "نجاح", "تم حفظ البيانات بنجاح")
            
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "خطأ", "الكود أو الاسم موجود مسبقاً")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في الحفظ: {e}")
        finally:
            if conn:
                conn.close()

class LocationDialog(RTLDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.data = data
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("موقع الأصول" if not self.data else "تعديل موقع الأصول")
        self.setFixedSize(450, 400)
        
        layout = QGridLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Code
        layout.addWidget(QLabel("الكود:"), 0, 0, Qt.AlignRight)
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("أدخل كود الموقع")
        layout.addWidget(self.code_edit, 0, 1)
        
        # Arabic Name
        layout.addWidget(QLabel("الاسم العربي:"), 1, 0, Qt.AlignRight)
        self.name_ar_edit = QLineEdit()
        self.name_ar_edit.setPlaceholderText("أدخل الاسم العربي")
        layout.addWidget(self.name_ar_edit, 1, 1)
        
        # English Name
        layout.addWidget(QLabel("الاسم الإنجليزي:"), 2, 0, Qt.AlignRight)
        self.name_en_edit = QLineEdit()
        self.name_en_edit.setPlaceholderText("أدخل الاسم الإنجليزي")
        layout.addWidget(self.name_en_edit, 2, 1)
        
        # Description
        layout.addWidget(QLabel("الوصف:"), 3, 0, Qt.AlignRight)
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText("أدخل وصف الموقع")
        layout.addWidget(self.desc_edit, 3, 1)
        
        # Status
        self.status_check = QCheckBox("نشط")
        self.status_check.setChecked(True)
        layout.addWidget(QLabel("الحالة:"), 4, 0, Qt.AlignRight)
        layout.addWidget(self.status_check, 4, 1, Qt.AlignLeft)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("💾 حفظ")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_data)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout, 5, 0, 1, 2)
        
        self.setLayout(layout)
        
        # Load data if editing
        if self.data:
            self.load_data()
    
    def load_data(self):
        self.code_edit.setText(self.data[1])
        self.name_ar_edit.setText(self.data[2])
        self.name_en_edit.setText(self.data[3])
        self.desc_edit.setText(self.data[4])
        self.status_check.setChecked(self.data[5] == 'نشط')
    
    def save_data(self):
        code = self.code_edit.text().strip()
        name_ar = self.name_ar_edit.text().strip()
        name_en = self.name_en_edit.text().strip()
        description = self.desc_edit.toPlainText().strip()
        
        if not code:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال الكود")
            return
        
        if not name_ar:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال الاسم العربي")
            return
        
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            
            if self.data:
                # Update
                cursor.execute("""
                    UPDATE asset_locations 
                    SET code=?, name_ar=?, name_en=?, description=?, is_active=?
                    WHERE id=?
                """, (code, name_ar, name_en, description, 
                      1 if self.status_check.isChecked() else 0, self.data[0]))
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO asset_locations (code, name_ar, name_en, description, is_active)
                    VALUES (?, ?, ?, ?, ?)
                """, (code, name_ar, name_en, description, 
                      1 if self.status_check.isChecked() else 0))
            
            conn.commit()
            self.accept()
            QMessageBox.information(self, "نجاح", "تم حفظ البيانات بنجاح")
            
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "خطأ", "الكود أو الاسم موجود مسبقاً")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في الحفظ: {e}")
        finally:
            if conn:
                conn.close()

class ResponsibleDialog(RTLDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.data = data
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("مسؤول الأصول" if not self.data else "تعديل مسؤول الأصول")
        self.setFixedSize(500, 450)
        
        layout = QGridLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Arabic Name
        layout.addWidget(QLabel("الاسم العربي:"), 0, 0, Qt.AlignRight)
        self.name_ar_edit = QLineEdit()
        self.name_ar_edit.setPlaceholderText("أدخل الاسم العربي")
        layout.addWidget(self.name_ar_edit, 0, 1)
        
        # English Name
        layout.addWidget(QLabel("الاسم الإنجليزي:"), 1, 0, Qt.AlignRight)
        self.name_en_edit = QLineEdit()
        self.name_en_edit.setPlaceholderText("أدخل الاسم الإنجليزي")
        layout.addWidget(self.name_en_edit, 1, 1)
        
        # Department
        layout.addWidget(QLabel("القسم:"), 2, 0, Qt.AlignRight)
        self.dept_edit = QLineEdit()
        self.dept_edit.setPlaceholderText("أدخل اسم القسم")
        layout.addWidget(self.dept_edit, 2, 1)
        
        # Phone
        layout.addWidget(QLabel("الهاتف:"), 3, 0, Qt.AlignRight)
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("أدخل رقم الهاتف")
        layout.addWidget(self.phone_edit, 3, 1)
        
        # Email
        layout.addWidget(QLabel("البريد الإلكتروني:"), 4, 0, Qt.AlignRight)
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("أدخل البريد الإلكتروني")
        layout.addWidget(self.email_edit, 4, 1)
        
        # Status
        self.status_check = QCheckBox("نشط")
        self.status_check.setChecked(True)
        layout.addWidget(QLabel("الحالة:"), 5, 0, Qt.AlignRight)
        layout.addWidget(self.status_check, 5, 1, Qt.AlignLeft)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("💾 حفظ")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_data)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout, 6, 0, 1, 2)
        
        self.setLayout(layout)
        
        # Load data if editing
        if self.data:
            self.load_data()
    
    def load_data(self):
        self.name_ar_edit.setText(self.data[1])
        self.name_en_edit.setText(self.data[2])
        self.dept_edit.setText(self.data[3])
        self.phone_edit.setText(self.data[4])
        self.email_edit.setText(self.data[5])
        self.status_check.setChecked(self.data[6] == 'نشط')
    
    def save_data(self):
        name_ar = self.name_ar_edit.text().strip()
        name_en = self.name_en_edit.text().strip()
        department = self.dept_edit.text().strip()
        phone = self.phone_edit.text().strip()
        email = self.email_edit.text().strip()
        
        if not name_ar:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال الاسم العربي")
            return
        
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            
            if self.data:
                # Update
                cursor.execute("""
                    UPDATE asset_responsibles 
                    SET name_ar=?, name_en=?, department=?, phone=?, email=?, is_active=?
                    WHERE id=?
                """, (name_ar, name_en, department, phone, email, 
                      1 if self.status_check.isChecked() else 0, self.data[0]))
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO asset_responsibles (name_ar, name_en, department, phone, email, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name_ar, name_en, department, phone, email, 
                      1 if self.status_check.isChecked() else 0))
            
            conn.commit()
            self.accept()
            QMessageBox.information(self, "نجاح", "تم حفظ البيانات بنجاح")
            
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "خطأ", "البيانات موجودة مسبقاً")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في الحفظ: {e}")
        finally:
            if conn:
                conn.close()

class FixedAssetsSettingsUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("إعدادات الأصول الثابتة")
        self.setGeometry(100, 100, 1200, 800)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.load_data()
        self.apply_styles()
        
    def apply_styles(self):
        """تطبيق الأنماط على الواجهة"""
        self.setStyleSheet(load_stylesheet())
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Header
        header_label = QLabel("إعدادات الأصول الثابتة")
        header_label.setObjectName("headerLabel")
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabWidget")
        
        # Create tabs
        self.depreciation_tab = QWidget()
        self.categories_tab = QWidget()
        self.locations_tab = QWidget()
        self.responsibles_tab = QWidget()
        
        # Add tabs
        self.tab_widget.addTab(self.depreciation_tab, "🏷️ طرق الإهلاك")
        self.tab_widget.addTab(self.categories_tab, "📁 تصنيفات الأصول")
        self.tab_widget.addTab(self.locations_tab, "📍 مواقع الأصول")
        self.tab_widget.addTab(self.responsibles_tab, "👥 المسؤولين")
        
        # Setup each tab
        self.setup_depreciation_tab()
        self.setup_categories_tab()
        self.setup_locations_tab()
        self.setup_responsibles_tab()
        
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)
        
    def setup_depreciation_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Table
        self.depreciation_table = QTableWidget()
        self.depreciation_table.setColumnCount(5)
        self.depreciation_table.setHorizontalHeaderLabels(['ID', 'الكود', 'الاسم العربي', 'الاسم الإنجليزي', 'الحالة'])
        self.depreciation_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.depreciation_table.setAlternatingRowColors(True)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_dep_btn = QPushButton("➕ إضافة")
        self.add_dep_btn.setObjectName("successButton")
        self.add_dep_btn.clicked.connect(self.add_depreciation_method)
        
        self.edit_dep_btn = QPushButton("✏️ تعديل")
        self.edit_dep_btn.setObjectName("warningButton")
        self.edit_dep_btn.clicked.connect(self.edit_depreciation_method)
        
        self.delete_dep_btn = QPushButton("🗑️ حذف")
        self.delete_dep_btn.setObjectName("dangerButton")
        self.delete_dep_btn.clicked.connect(self.delete_depreciation_method)
        
        self.refresh_dep_btn = QPushButton("🔄 تحديث")
        self.refresh_dep_btn.setObjectName("infoButton")
        self.refresh_dep_btn.clicked.connect(self.load_depreciation_methods)
        
        button_layout.addWidget(self.add_dep_btn)
        button_layout.addWidget(self.edit_dep_btn)
        button_layout.addWidget(self.delete_dep_btn)
        button_layout.addWidget(self.refresh_dep_btn)
        button_layout.addStretch()
        
        layout.addWidget(self.depreciation_table)
        layout.addLayout(button_layout)
        self.depreciation_tab.setLayout(layout)
        
    def setup_categories_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Table
        self.categories_table = QTableWidget()
        self.categories_table.setColumnCount(9)
        self.categories_table.setHorizontalHeaderLabels([
            'ID', 'الكود', 'الاسم العربي', 'الاسم الإنجليزي', 'النوع', 
            'طريقة الإهلاك', 'العمر الإفتراضي', 'معدل الإهلاك', 'الحالة'
        ])
        self.categories_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.categories_table.setAlternatingRowColors(True)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_cat_btn = QPushButton("➕ إضافة")
        self.add_cat_btn.setObjectName("successButton")
        self.add_cat_btn.clicked.connect(self.add_category)
        
        self.edit_cat_btn = QPushButton("✏️ تعديل")
        self.edit_cat_btn.setObjectName("warningButton")
        self.edit_cat_btn.clicked.connect(self.edit_category)
        
        self.delete_cat_btn = QPushButton("🗑️ حذف")
        self.delete_cat_btn.setObjectName("dangerButton")
        self.delete_cat_btn.clicked.connect(self.delete_category)
        
        self.refresh_cat_btn = QPushButton("🔄 تحديث")
        self.refresh_cat_btn.setObjectName("infoButton")
        self.refresh_cat_btn.clicked.connect(self.load_categories)
        
        button_layout.addWidget(self.add_cat_btn)
        button_layout.addWidget(self.edit_cat_btn)
        button_layout.addWidget(self.delete_cat_btn)
        button_layout.addWidget(self.refresh_cat_btn)
        button_layout.addStretch()
        
        layout.addWidget(self.categories_table)
        layout.addLayout(button_layout)
        self.categories_tab.setLayout(layout)
        
    def setup_locations_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Table
        self.locations_table = QTableWidget()
        self.locations_table.setColumnCount(6)
        self.locations_table.setHorizontalHeaderLabels([
            'ID', 'الكود', 'الاسم العربي', 'الاسم الإنجليزي', 'الوصف', 'الحالة'
        ])
        self.locations_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.locations_table.setAlternatingRowColors(True)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_loc_btn = QPushButton("➕ إضافة")
        self.add_loc_btn.setObjectName("successButton")
        self.add_loc_btn.clicked.connect(self.add_location)
        
        self.edit_loc_btn = QPushButton("✏️ تعديل")
        self.edit_loc_btn.setObjectName("warningButton")
        self.edit_loc_btn.clicked.connect(self.edit_location)
        
        self.delete_loc_btn = QPushButton("🗑️ حذف")
        self.delete_loc_btn.setObjectName("dangerButton")
        self.delete_loc_btn.clicked.connect(self.delete_location)
        
        self.refresh_loc_btn = QPushButton("🔄 تحديث")
        self.refresh_loc_btn.setObjectName("infoButton")
        self.refresh_loc_btn.clicked.connect(self.load_locations)
        
        button_layout.addWidget(self.add_loc_btn)
        button_layout.addWidget(self.edit_loc_btn)
        button_layout.addWidget(self.delete_loc_btn)
        button_layout.addWidget(self.refresh_loc_btn)
        button_layout.addStretch()
        
        layout.addWidget(self.locations_table)
        layout.addLayout(button_layout)
        self.locations_tab.setLayout(layout)
        
    def setup_responsibles_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Table
        self.responsibles_table = QTableWidget()
        self.responsibles_table.setColumnCount(7)
        self.responsibles_table.setHorizontalHeaderLabels([
            'ID', 'الاسم العربي', 'الاسم الإنجليزي', 'القسم', 'الهاتف', 'البريد الإلكتروني', 'الحالة'
        ])
        self.responsibles_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.responsibles_table.setAlternatingRowColors(True)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_resp_btn = QPushButton("➕ إضافة")
        self.add_resp_btn.setObjectName("successButton")
        self.add_resp_btn.clicked.connect(self.add_responsible)
        
        self.edit_resp_btn = QPushButton("✏️ تعديل")
        self.edit_resp_btn.setObjectName("warningButton")
        self.edit_resp_btn.clicked.connect(self.edit_responsible)
        
        self.delete_resp_btn = QPushButton("🗑️ حذف")
        self.delete_resp_btn.setObjectName("dangerButton")
        self.delete_resp_btn.clicked.connect(self.delete_responsible)
        
        self.refresh_resp_btn = QPushButton("🔄 تحديث")
        self.refresh_resp_btn.setObjectName("infoButton")
        self.refresh_resp_btn.clicked.connect(self.load_responsibles)
        
        button_layout.addWidget(self.add_resp_btn)
        button_layout.addWidget(self.edit_resp_btn)
        button_layout.addWidget(self.delete_resp_btn)
        button_layout.addWidget(self.refresh_resp_btn)
        button_layout.addStretch()
        
        layout.addWidget(self.responsibles_table)
        layout.addLayout(button_layout)
        self.responsibles_tab.setLayout(layout)
        
    def load_data(self):
        self.load_depreciation_methods()
        self.load_categories()
        self.load_locations()
        self.load_responsibles()
        
    def load_depreciation_methods(self):
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, code, name_ar, name_en, 
                       CASE WHEN is_active = 1 THEN 'نشط' ELSE 'غير نشط' END as status
                FROM depreciation_methods
                ORDER BY id
            """)
            
            rows = cursor.fetchall()
            self.depreciation_table.setRowCount(len(rows))
            
            for row_idx, row_data in enumerate(rows):
                for col_idx, col_data in enumerate(row_data):
                    item = QTableWidgetItem(str(col_data))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.depreciation_table.setItem(row_idx, col_idx, item)
                    
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل البيانات: {e}")
        finally:
            if conn:
                conn.close()


    def load_categories(self):
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT c.id, c.code, c.name_ar, c.name_en, c.category_type,
                       COALESCE(m.name_ar, ''), c.useful_life_years, c.depreciation_rate,
                       CASE WHEN c.is_active = 1 THEN 'نشط' ELSE 'غير نشط' END as status
                FROM fixed_asset_categories c
                LEFT JOIN depreciation_methods m ON c.depreciation_method_id = m.id
                ORDER BY c.id
            """)
            
            rows = cursor.fetchall()
            self.categories_table.setRowCount(len(rows))
            
            for row_idx, row_data in enumerate(rows):
                for col_idx, col_data in enumerate(row_data):
                    item = QTableWidgetItem(str(col_data))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.categories_table.setItem(row_idx, col_idx, item)
                    
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل البيانات: {e}")
        finally:
            if conn:
                conn.close()
    
    def load_locations(self):
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, code, name_ar, name_en, description,
                       CASE WHEN is_active = 1 THEN 'نشط' ELSE 'غير نشط' END as status
                FROM asset_locations
                ORDER BY id
            """)
            
            rows = cursor.fetchall()
            self.locations_table.setRowCount(len(rows))
            
            for row_idx, row_data in enumerate(rows):
                for col_idx, col_data in enumerate(row_data):
                    item = QTableWidgetItem(str(col_data))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.locations_table.setItem(row_idx, col_idx, item)
                    
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل البيانات: {e}")
        finally:
            if conn:
                conn.close()
    
    def load_responsibles(self):
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name_ar, name_en, department, phone, email,
                       CASE WHEN is_active = 1 THEN 'نشط' ELSE 'غير نشط' END as status
                FROM asset_responsibles
                ORDER BY id
            """)
            
            rows = cursor.fetchall()
            self.responsibles_table.setRowCount(len(rows))
            
            for row_idx, row_data in enumerate(rows):
                for col_idx, col_data in enumerate(row_data):
                    item = QTableWidgetItem(str(col_data))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.responsibles_table.setItem(row_idx, col_idx, item)
                    
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", "خطأ في تحميل البيانات: {e}")
        finally:
            if conn:
                conn.close()
    
    def add_depreciation_method(self):
        dialog = DepreciationMethodDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_depreciation_methods()
    
    def edit_depreciation_method(self):
        selected = self.depreciation_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار طريقة إهلاك للتعديل")
            return
        
        row = selected[0].row()
        data = []
        for col in range(5):
            data.append(self.depreciation_table.item(row, col).text())
        
        dialog = DepreciationMethodDialog(self, data)
        if dialog.exec_() == QDialog.Accepted:
            self.load_depreciation_methods()
    
    def delete_depreciation_method(self):
        selected = self.depreciation_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار طريقة إهلاك للحذف")
            return
        
        reply = QMessageBox.question(self, "تأكيد", 
                                    "هل أنت متأكد من حذف طريقة الإهلاك المحددة؟",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_fixed_assets_db_connection()
                cursor = conn.cursor()
                
                item_id = self.depreciation_table.item(selected[0].row(), 0).text()
                cursor.execute("DELETE FROM depreciation_methods WHERE id = ?", (item_id,))
                conn.commit()
                
                QMessageBox.information(self, "نجاح", "تم حذف طريقة الإهلاك بنجاح")
                self.load_depreciation_methods()
                
            except sqlite3.Error as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في الحذف: {e}")
            finally:
                if conn:
                    conn.close()
    
    def add_category(self):
        dialog = CategoryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_categories()
    
    def edit_category(self):
        selected = self.categories_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار تصنيف للتعديل")
            return
        
        row = selected[0].row()
        data = []
        for col in range(9):
            data.append(self.categories_table.item(row, col).text())
        
        dialog = CategoryDialog(self, data)
        if dialog.exec_() == QDialog.Accepted:
            self.load_categories()
    
    def delete_category(self):
        selected = self.categories_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار تصنيف للحذف")
            return
        
        reply = QMessageBox.question(self, "تأكيد", 
                                    "هل أنت متأكد من حذف التصنيف المحدد؟",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_fixed_assets_db_connection()
                cursor = conn.cursor()
                
                item_id = self.categories_table.item(selected[0].row(), 0).text()
                cursor.execute("DELETE FROM fixed_asset_categories WHERE id = ?", (item_id,))
                conn.commit()
                
                QMessageBox.information(self, "نجاح", "تم حذف التصنيف بنجاح")
                self.load_categories()
                
            except sqlite3.Error as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في الحذف: {e}")
            finally:
                if conn:
                    conn.close()
    
    def add_location(self):
        dialog = LocationDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_locations()
    
    def edit_location(self):
        selected = self.locations_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار موقع للتعديل")
            return
        
        row = selected[0].row()
        data = []
        for col in range(6):
            data.append(self.locations_table.item(row, col).text())
        
        dialog = LocationDialog(self, data)
        if dialog.exec_() == QDialog.Accepted:
            self.load_locations()
    
    def delete_location(self):
        selected = self.locations_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار موقع للحذف")
            return
        
        reply = QMessageBox.question(self, "تأكيد", 
                                    "هل أنت متأكد من حذف الموقع المحدد؟",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_fixed_assets_db_connection()
                cursor = conn.cursor()
                
                item_id = self.locations_table.item(selected[0].row(), 0).text()
                cursor.execute("DELETE FROM asset_locations WHERE id = ?", (item_id,))
                conn.commit()
                
                QMessageBox.information(self, "نجاح", "تم حذف الموقع بنجاح")
                self.load_locations()
                
            except sqlite3.Error as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في الحذف: {e}")
            finally:
                if conn:
                    conn.close()
    
    def add_responsible(self):
        dialog = ResponsibleDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_responsibles()
    
    def edit_responsible(self):
        selected = self.responsibles_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار مسؤول للتعديل")
            return
        
        row = selected[0].row()
        data = []
        for col in range(7):
            data.append(self.responsibles_table.item(row, col).text())
        
        dialog = ResponsibleDialog(self, data)
        if dialog.exec_() == QDialog.Accepted:
            self.load_responsibles()
    
    def delete_responsible(self):
        selected = self.responsibles_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار مسؤول للحذف")
            return
        
        reply = QMessageBox.question(self, "تأكيد", 
                                    "هل أنت متأكد من حذف المسؤول المحدد؟",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_fixed_assets_db_connection()
                cursor = conn.cursor()
                
                item_id = self.responsibles_table.item(selected[0].row(), 0).text()
                cursor.execute("DELETE FROM asset_responsibles WHERE id = ?", (item_id,))
                conn.commit()
                
                QMessageBox.information(self, "نجاح", "تم حذف المسؤول بنجاح")
                self.load_responsibles()
                
            except sqlite3.Error as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في الحذف: {e}")
            finally:
                if conn:
                    conn.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FixedAssetsSettingsUI()
    window.show()
    sys.exit(app.exec_())
# -*- coding: utf-8 -*-
# file: fixed_asset_card_ui.py

import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QComboBox, QDateEdit,
    QGridLayout, QTabWidget, QTextEdit, QCheckBox, QDialog, QSpinBox, QDoubleSpinBox,
    QGroupBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPixmap

# =====================================================================
# تصحيح مسار المشروع الجذر لتمكين الاستيراد الصحيح
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..')) 
if project_root not in sys.path:
    sys.path.append(project_root)

from database.db_connection import get_fixed_assets_db_connection

class FixedAssetCardUI(QWidget):
    def __init__(self, asset_id=None):
        super().__init__()
        self.asset_id = asset_id
        self.setWindowTitle("بطاقة أصل ثابت جديد" if not asset_id else "تعديل بطاقة أصل ثابت")
        self.setGeometry(100, 100, 1000, 800)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.apply_styles()
        
        if asset_id:
            self.load_asset_data()
    
    def apply_styles(self):
        """🎨 تطبيق أنماط عصرية على الواجهة"""
        self.setStyleSheet("""
            QWidget {
            font-family: 'Segoe UI', Tahoma, Arial;
            font-size: 12px;
            background-color: #f5f7fa;
        }

        QLabel {
            color: #2c3e50;
            font-weight: 600;
            font-size: 13px;
        }

        QLineEdit, QComboBox, QDateEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
            border: 1px solid #dcdde1;
            border-radius: 6px;
            padding: 6px 8px;
            background-color: #ffffff;
            selection-background-color: #3498db;
        }

        QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus,
        QSpinBox:focus, QDoubleSpinBox:focus {
            border: 2px solid #2980b9;
            background-color: #ecf6fd;
        }

        QPushButton {
            border: none;
            border-radius: 6px;
            padding: 8px 18px;
            font-weight: bold;
            font-size: 13px;
            transition: all 0.3s ease;
        }

        QPushButton#primaryButton {
            background-color: #3498db;
            color: white;
        }
        QPushButton#primaryButton:hover {
            background-color: #2980b9;
        }
        QPushButton#primaryButton:pressed {
            background-color: #1f6391;
        }

        QPushButton#secondaryButton {
            background-color: #7f8c8d;
            color: white;
        }
        QPushButton#secondaryButton:hover {
            background-color: #636e72;
        }
        QPushButton#secondaryButton:pressed {
            background-color: #2d3436;
        }

        QTabWidget::pane {
            border: 1px solid #dfe6e9;
            border-radius: 8px;
            padding: 6px;
            background: #ffffff;
        }

        QTabBar::tab {
            background: #ecf0f1;
            border: 1px solid #bdc3c7;
            border-bottom: none;
            padding: 8px 16px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            font-weight: bold;
            min-width: 120px;
        }
        QTabBar::tab:selected {
            background: #ffffff;
            color: #2980b9;
            border: 2px solid #3498db;
            border-bottom: none;
        }
        QTabBar::tab:hover {
            background: #dfe6e9;
        }

        QGroupBox {
            font-weight: bold;
            font-size: 13px;
            border: 1px solid #dcdde1;
            border-radius: 8px;
            margin-top: 12px;
            padding: 12px;
            background-color: #ffffff;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top right;
            padding: 0 12px;
            color: #3498db;
            background-color: transparent;
        }
    """)

    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("بطاقة الأصل الثابت")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # Add save, delete, disable, cancel buttons
        self.save_btn = QPushButton("💾 حفظ")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.save_asset)

        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.setObjectName("secondaryButton")
        self.delete_btn.clicked.connect(self.delete_asset)

        self.toggle_btn = QPushButton("🚫 تعطيل/تفعيل")
        self.toggle_btn.setObjectName("secondaryButton")
        self.toggle_btn.clicked.connect(self.toggle_asset_status)

        self.cancel_btn = QPushButton("❌ إلغاء")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.clicked.connect(self.close)

        header_layout.addWidget(self.save_btn)
        header_layout.addWidget(self.delete_btn)
        header_layout.addWidget(self.toggle_btn)
        header_layout.addWidget(self.cancel_btn)

        main_layout.addLayout(header_layout)

        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Basic info tab
        self.basic_info_tab = QWidget()
        self.setup_basic_info_tab()
        
        # Financial info tab
        self.financial_info_tab = QWidget()
        self.setup_financial_info_tab()
        
        # Additional info tab
        self.additional_info_tab = QWidget()
        self.setup_additional_info_tab()
        
        self.tabs.addTab(self.basic_info_tab, "المعلومات الأساسية")
        self.tabs.addTab(self.financial_info_tab, "المعلومات المالية")
        self.tabs.addTab(self.additional_info_tab, "معلومات إضافية")
        
        main_layout.addWidget(self.tabs)
        
        self.setLayout(main_layout)
    
    def setup_basic_info_tab(self):
        layout = QGridLayout(self.basic_info_tab)
        layout.setSpacing(10)
        
        # Row 0
        layout.addWidget(QLabel("كود الأصل:"), 0, 0)
        self.asset_code_edit = QLineEdit()
        layout.addWidget(self.asset_code_edit, 0, 1)
        
        layout.addWidget(QLabel("الاسم العربي:"), 0, 2)
        self.asset_name_ar_edit = QLineEdit()
        layout.addWidget(self.asset_name_ar_edit, 0, 3)
        
        # Row 1
        layout.addWidget(QLabel("الاسم الإنجليزي:"), 1, 0)
        self.asset_name_en_edit = QLineEdit()
        layout.addWidget(self.asset_name_en_edit, 1, 1)
        
        layout.addWidget(QLabel("التصنيف:"), 1, 2)
        self.category_combo = QComboBox()
        self.load_categories()
        layout.addWidget(self.category_combo, 1, 3)
        
        # Row 2
        layout.addWidget(QLabel("الوصف:"), 2, 0)
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        layout.addWidget(self.description_edit, 2, 1, 1, 3)
        
        # Row 3
        layout.addWidget(QLabel("الوحدة:"), 3, 0)
        self.unit_combo = QComboBox()
        self.load_units()
        layout.addWidget(self.unit_combo, 3, 1)
        
        layout.addWidget(QLabel("الكمية:"), 3, 2)
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(999999)
        layout.addWidget(self.quantity_spin, 3, 3)
        
        # Row 4
        layout.addWidget(QLabel("تاريخ الشراء:"), 4, 0)
        self.acquisition_date_edit = QDateEdit()
        self.acquisition_date_edit.setDate(QDate.currentDate())
        self.acquisition_date_edit.setCalendarPopup(True)
        self.acquisition_date_edit.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(self.acquisition_date_edit, 4, 1)
        
        layout.addWidget(QLabel("تاريخ الاستخدام:"), 4, 2)
        self.commissioning_date_edit = QDateEdit()
        self.commissioning_date_edit.setDate(QDate.currentDate())
        self.commissioning_date_edit.setCalendarPopup(True)
        self.commissioning_date_edit.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(self.commissioning_date_edit, 4, 3)
        
        # Row 5
        layout.addWidget(QLabel("طريقة الإهلاك:"), 5, 0)
        self.depreciation_method_combo = QComboBox()
        self.load_depreciation_methods()
        layout.addWidget(self.depreciation_method_combo, 5, 1)
        
        layout.addWidget(QLabel("الحالة:"), 5, 2)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["نشط", "معطل", "مسحوب", "مباع", "مستبعد"])
        layout.addWidget(self.status_combo, 5, 3)
        
        # Add stretch to push everything to the top
        layout.setRowStretch(6, 1)
    
    def setup_financial_info_tab(self):
        layout = QGridLayout(self.financial_info_tab)
        layout.setSpacing(10)
        
        # Row 0
        layout.addWidget(QLabel("سعر الوحدة:"), 0, 0)
        self.unit_price_spin = QDoubleSpinBox()
        self.unit_price_spin.setMinimum(0)
        self.unit_price_spin.setMaximum(99999999)
        self.unit_price_spin.setDecimals(2)
        self.unit_price_spin.valueChanged.connect(self.calculate_costs)
        layout.addWidget(self.unit_price_spin, 0, 1)
        
        layout.addWidget(QLabel("التكلفة الإجمالية:"), 0, 2)
        self.acquisition_cost_edit = QLineEdit()
        self.acquisition_cost_edit.setReadOnly(True)
        layout.addWidget(self.acquisition_cost_edit, 0, 3)
        
        # Row 1
        layout.addWidget(QLabel("القيمة التخريدية:"), 1, 0)
        self.salvage_value_spin = QDoubleSpinBox()
        self.salvage_value_spin.setMinimum(0)
        self.salvage_value_spin.setMaximum(99999999)
        self.salvage_value_spin.setDecimals(2)
        layout.addWidget(self.salvage_value_spin, 1, 1)
        
        layout.addWidget(QLabel("معدل الإهلاك %:"), 1, 2)
        self.depreciation_rate_spin = QDoubleSpinBox()
        self.depreciation_rate_spin.setMinimum(0)
        self.depreciation_rate_spin.setMaximum(100)
        self.depreciation_rate_spin.setDecimals(2)
        layout.addWidget(self.depreciation_rate_spin, 1, 3)
        
        # Row 2
        layout.addWidget(QLabel("العمر الإنتاجي (سنوات):"), 2, 0)
        self.useful_life_spin = QSpinBox()
        self.useful_life_spin.setMinimum(1)
        self.useful_life_spin.setMaximum(100)
        layout.addWidget(self.useful_life_spin, 2, 1)
        
        layout.addWidget(QLabel("مجمع الإهلاك:"), 2, 2)
        self.accumulated_depreciation_spin = QDoubleSpinBox()
        self.accumulated_depreciation_spin.setMinimum(0)
        self.accumulated_depreciation_spin.setMaximum(99999999)
        self.accumulated_depreciation_spin.setDecimals(2)
        layout.addWidget(self.accumulated_depreciation_spin, 2, 3)
        
        # Row 3
        layout.addWidget(QLabel("صافي القيمة الدفترية:"), 3, 0)
        self.current_book_value_edit = QLineEdit()
        self.current_book_value_edit.setReadOnly(True)
        layout.addWidget(self.current_book_value_edit, 3, 1)
        
        # Add stretch
        layout.setRowStretch(4, 1)
    
    def setup_additional_info_tab(self):
        layout = QGridLayout(self.additional_info_tab)
        layout.setSpacing(10)
        
        # Row 0
        layout.addWidget(QLabel("الموقع:"), 0, 0)
        self.location_combo = QComboBox()
        self.load_locations()
        layout.addWidget(self.location_combo, 0, 1)
        
        layout.addWidget(QLabel("المسؤول:"), 0, 2)
        self.responsible_combo = QComboBox()
        self.load_responsibles()
        layout.addWidget(self.responsible_combo, 0, 3)
        
        # Row 1
        layout.addWidget(QLabel("المورد:"), 1, 0)
        self.supplier_edit = QLineEdit()
        layout.addWidget(self.supplier_edit, 1, 1)
        
        layout.addWidget(QLabel("رقم الفاتورة:"), 1, 2)
        self.invoice_number_edit = QLineEdit()
        layout.addWidget(self.invoice_number_edit, 1, 3)
        
        # Row 2
        layout.addWidget(QLabel("تاريخ انتهاء الضمان:"), 2, 0)
        self.warranty_end_date_edit = QDateEdit()
        self.warranty_end_date_edit.setCalendarPopup(True)
        self.warranty_end_date_edit.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(self.warranty_end_date_edit, 2, 1)
        
        layout.addWidget(QLabel("رقم التسلسلي:"), 2, 2)
        self.serial_number_edit = QLineEdit()
        layout.addWidget(self.serial_number_edit, 2, 3)
        
        # Row 3
        layout.addWidget(QLabel("النموذج:"), 3, 0)
        self.model_edit = QLineEdit()
        layout.addWidget(self.model_edit, 3, 1)
        
        layout.addWidget(QLabel("العلامة التجارية:"), 3, 2)
        self.brand_edit = QLineEdit()
        layout.addWidget(self.brand_edit, 3, 3)
        
        # Row 4
        layout.addWidget(QLabel("ملاحظات:"), 4, 0)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        layout.addWidget(self.notes_edit, 4, 1, 1, 3)
        
        # Add stretch
        layout.setRowStretch(5, 1)
    
    def load_categories(self):
        """تحميل التصنيفات"""
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name_ar FROM fixed_asset_categories WHERE is_active = 1 ORDER BY name_ar")
            categories = cursor.fetchall()
            
            self.category_combo.clear()
            for category_id, name_ar in categories:
                self.category_combo.addItem(name_ar, category_id)
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل التصنيفات: {e}")
        finally:
            if conn:
                conn.close()
    
    def load_units(self):
        """تحميل وحدات القياس"""
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name_ar FROM measurement_units WHERE is_active = 1 ORDER BY name_ar")
            units = cursor.fetchall()
            
            self.unit_combo.clear()
            for unit_id, name_ar in units:
                self.unit_combo.addItem(name_ar, unit_id)
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل وحدات القياس: {e}")
        finally:
            if conn:
                conn.close()
    
    def load_depreciation_methods(self):
        """تحميل طرق الإهلاك"""
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name_ar FROM depreciation_methods WHERE is_active = 1 ORDER BY name_ar")
            methods = cursor.fetchall()
            
            self.depreciation_method_combo.clear()
            for method_id, name_ar in methods:
                self.depreciation_method_combo.addItem(name_ar, method_id)
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل طرق الإهلاك: {e}")
        finally:
            if conn:
                conn.close()
    
    def load_locations(self):
        """تحميل المواقع"""
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, location_name_ar FROM asset_locations WHERE is_active = 1 ORDER BY location_name_ar")
            locations = cursor.fetchall()
            
            self.location_combo.clear()
            self.location_combo.addItem("-- اختر موقع --", None)
            for location_id, name_ar in locations:
                self.location_combo.addItem(name_ar, location_id)
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل المواقع: {e}")
        finally:
            if conn:
                conn.close()
    
    def load_responsibles(self):
        """تحميل المسؤولين"""
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name_ar FROM asset_responsibles WHERE is_active = 1 ORDER BY name_ar")
            responsibles = cursor.fetchall()
            
            self.responsible_combo.clear()
            self.responsible_combo.addItem("-- اختر مسؤول --", None)
            for responsible_id, name_ar in responsibles:
                self.responsible_combo.addItem(name_ar, responsible_id)
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل المسؤولين: {e}")
        finally:
            if conn:
                conn.close()
    
    def calculate_costs(self):
        """حساب التكاليف تلقائياً"""
        try:
            quantity = self.quantity_spin.value()
            unit_price = self.unit_price_spin.value()
            total_cost = quantity * unit_price
            self.acquisition_cost_edit.setText(f"{total_cost:,.2f}")
            
            # Calculate current book value
            accumulated_dep = self.accumulated_depreciation_spin.value()
            book_value = total_cost - accumulated_dep
            self.current_book_value_edit.setText(f"{book_value:,.2f}")
            
        except Exception as e:
            print(f"Error in calculate_costs: {e}")
    
    def load_asset_data(self):
        """تحميل بيانات الأصل إذا كان في وضع التعديل"""
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM fixed_assets WHERE id = ?
            """, (self.asset_id,))
            
            asset = cursor.fetchone()
            
            if asset:
                # Basic info
                self.asset_code_edit.setText(asset[1] if asset[1] else "")
                self.asset_name_ar_edit.setText(asset[2] if asset[2] else "")
                self.asset_name_en_edit.setText(asset[3] if asset[3] else "")
                self.description_edit.setText(asset[4] if asset[4] else "")
                
                # Set category
                if asset[5]:  # category_id
                    for i in range(self.category_combo.count()):
                        if self.category_combo.itemData(i) == asset[5]:
                            self.category_combo.setCurrentIndex(i)
                            break
                
                # Set unit
                if asset[6]:  # unit_type
                    for i in range(self.unit_combo.count()):
                        if self.unit_combo.itemData(i) == asset[6]:
                            self.unit_combo.setCurrentIndex(i)
                            break
                
                self.quantity_spin.setValue(asset[7] if asset[7] else 1)
                
                # Dates
                if asset[8]:  # acquisition_date
                    self.acquisition_date_edit.setDate(QDate.fromString(asset[8], "yyyy-MM-dd"))
                if asset[9]:  # commissioning_date
                    self.commissioning_date_edit.setDate(QDate.fromString(asset[9], "yyyy-MM-dd"))
                
                # Set depreciation method
                if asset[10]:  # depreciation_method_id
                    for i in range(self.depreciation_method_combo.count()):
                        if self.depreciation_method_combo.itemData(i) == asset[10]:
                            self.depreciation_method_combo.setCurrentIndex(i)
                            break
                
                # Financial info
                self.unit_price_spin.setValue(asset[11] if asset[11] else 0.0)
                self.acquisition_cost_edit.setText(f"{asset[12]:,.2f}" if asset[12] else "0.00")
                self.salvage_value_spin.setValue(asset[13] if asset[13] else 0.0)
                self.depreciation_rate_spin.setValue(asset[14] if asset[14] else 0.0)
                self.useful_life_spin.setValue(asset[15] if asset[15] else 1)
                self.accumulated_depreciation_spin.setValue(asset[16] if asset[16] else 0.0)
                self.current_book_value_edit.setText(f"{asset[17]:,.2f}" if asset[17] else "0.00")
                
                # Status
                status_map = {"active": "نشط", "inactive": "معطل", "retired": "مسحوب", 
                             "sold": "مباع", "disposed": "مستبعد"}
                current_status = status_map.get(asset[18], "نشط")
                self.status_combo.setCurrentText(current_status)
                
                # Additional info
                # Set location
                if asset[19]:  # location_id
                    for i in range(self.location_combo.count()):
                        if self.location_combo.itemData(i) == asset[19]:
                            self.location_combo.setCurrentIndex(i)
                            break
                
                # Set responsible
                if asset[20]:  # responsible_id
                    for i in range(self.responsible_combo.count()):
                        if self.responsible_combo.itemData(i) == asset[20]:
                            self.responsible_combo.setCurrentIndex(i)
                            break
                
                self.supplier_edit.setText(asset[21] if asset[21] else "")
                self.invoice_number_edit.setText(asset[22] if asset[22] else "")
                
                if asset[23]:  # warranty_end_date
                    self.warranty_end_date_edit.setDate(QDate.fromString(asset[23], "yyyy-MM-dd"))
                
                self.serial_number_edit.setText(asset[24] if asset[24] else "")
                self.model_edit.setText(asset[25] if asset[25] else "")
                self.brand_edit.setText(asset[26] if asset[26] else "")
                self.notes_edit.setText(asset[27] if asset[27] else "")
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل بيانات الأصل: {e}")
        finally:
            if conn:
                conn.close()
    
    def save_asset(self):
        """حفظ بيانات الأصل"""
        # Validate required fields
        if not self.asset_code_edit.text().strip():
            QMessageBox.warning(self, "تحذير", "يرجى إدخال كود الأصل")
            return
        
        if not self.asset_name_ar_edit.text().strip():
            QMessageBox.warning(self, "تحذير", "يرجى إدخال الاسم العربي للأصل")
            return
        
        if not self.category_combo.currentData():
            QMessageBox.warning(self, "تحذير", "يرجى اختيار تصنيف للأصل")
            return
        
        # Prepare data
        asset_data = {
            'asset_code': self.asset_code_edit.text().strip(),
            'asset_name_ar': self.asset_name_ar_edit.text().strip(),
            'asset_name_en': self.asset_name_en_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'category_id': self.category_combo.currentData(),
            'unit_type': self.unit_combo.currentData(),
            'quantity': self.quantity_spin.value(),
            'acquisition_date': self.acquisition_date_edit.date().toString("yyyy-MM-dd"),
            'commissioning_date': self.commissioning_date_edit.date().toString("yyyy-MM-dd"),
            'depreciation_method_id': self.depreciation_method_combo.currentData(),
            'unit_price': self.unit_price_spin.value(),
            'acquisition_cost': float(self.acquisition_cost_edit.text().replace(',', '') or 0),
            'salvage_value': self.salvage_value_spin.value(),
            'depreciation_rate': self.depreciation_rate_spin.value(),
            'useful_life_years': self.useful_life_spin.value(),
            'accumulated_depreciation': self.accumulated_depreciation_spin.value(),
            'current_book_value': float(self.current_book_value_edit.text().replace(',', '') or 0),
            'status': self.status_combo.currentText(),
            'location_id': self.location_combo.currentData(),
            'responsible_id': self.responsible_combo.currentData(),
            'supplier': self.supplier_edit.text().strip(),
            'invoice_number': self.invoice_number_edit.text().strip(),
            'warranty_end_date': self.warranty_end_date_edit.date().toString("yyyy-MM-dd") if self.warranty_end_date_edit.date() > QDate(2000, 1, 1) else None,
            'serial_number': self.serial_number_edit.text().strip(),
            'model': self.model_edit.text().strip(),
            'brand': self.brand_edit.text().strip(),
            'notes': self.notes_edit.toPlainText().strip()
        }
        
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            
            if self.asset_id:
                # Update existing asset
                query = """
                    UPDATE fixed_assets SET
                        asset_code=?, asset_name_ar=?, asset_name_en=?, description=?,
                        category_id=?, unit_type=?, quantity=?, acquisition_date=?,
                        commissioning_date=?, depreciation_method_id=?, unit_price=?,
                        acquisition_cost=?, salvage_value=?, depreciation_rate=?,
                        useful_life_years=?, accumulated_depreciation=?, current_book_value=?,
                        status=?, location_id=?, responsible_id=?, supplier=?,
                        invoice_number=?, warranty_end_date=?, serial_number=?,
                        model=?, brand=?, notes=?
                    WHERE id=?
                """
                params = (
                    asset_data['asset_code'], asset_data['asset_name_ar'], asset_data['asset_name_en'],
                    asset_data['description'], asset_data['category_id'], asset_data['unit_type'],
                    asset_data['quantity'], asset_data['acquisition_date'], asset_data['commissioning_date'],
                    asset_data['depreciation_method_id'], asset_data['unit_price'], asset_data['acquisition_cost'],
                    asset_data['salvage_value'], asset_data['depreciation_rate'], asset_data['useful_life_years'],
                    asset_data['accumulated_depreciation'], asset_data['current_book_value'], asset_data['status'],
                    asset_data['location_id'], asset_data['responsible_id'], asset_data['supplier'],
                    asset_data['invoice_number'], asset_data['warranty_end_date'], asset_data['serial_number'],
                    asset_data['model'], asset_data['brand'], asset_data['notes'], self.asset_id
                )
            else:
                # Insert new asset
                query = """
                    INSERT INTO fixed_assets (
                        asset_code, asset_name_ar, asset_name_en, description,
                        category_id, unit_type, quantity, acquisition_date,
                        commissioning_date, depreciation_method_id, unit_price,
                        acquisition_cost, salvage_value, depreciation_rate,
                        useful_life_years, accumulated_depreciation, current_book_value,
                        status, location_id, responsible_id, supplier,
                        invoice_number, warranty_end_date, serial_number,
                        model, brand, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    asset_data['asset_code'], asset_data['asset_name_ar'], asset_data['asset_name_en'],
                    asset_data['description'], asset_data['category_id'], asset_data['unit_type'],
                    asset_data['quantity'], asset_data['acquisition_date'], asset_data['commissioning_date'],
                    asset_data['depreciation_method_id'], asset_data['unit_price'], asset_data['acquisition_cost'],
                    asset_data['salvage_value'], asset_data['depreciation_rate'], asset_data['useful_life_years'],
                    asset_data['accumulated_depreciation'], asset_data['current_book_value'], asset_data['status'],
                    asset_data['location_id'], asset_data['responsible_id'], asset_data['supplier'],
                    asset_data['invoice_number'], asset_data['warranty_end_date'], asset_data['serial_number'],
                    asset_data['model'], asset_data['brand'], asset_data['notes']
                )
            
            cursor.execute(query, params)
            conn.commit()
            
            QMessageBox.information(self, "نجاح", "تم حفظ بيانات الأصل بنجاح")
            self.close()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في حفظ البيانات: {e}")
        finally:
            if conn:
                conn.close()
    def delete_asset(self):
        """حذف الأصل"""
        if not self.asset_id:
            QMessageBox.warning(self, "تنبيه", "لا يوجد أصل محدد للحذف")
            return

        confirm = QMessageBox.question(
            self, "تأكيد الحذف", "هل أنت متأكد من حذف هذا الأصل؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                conn = get_fixed_assets_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM fixed_assets WHERE id=?", (self.asset_id,))
                conn.commit()
                QMessageBox.information(self, "نجاح", "تم حذف الأصل بنجاح")
                self.close()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "خطأ", f"فشل حذف الأصل: {e}")
            finally:
                if conn:
                    conn.close()

    def toggle_asset_status(self):
        """تفعيل أو تعطيل الأصل"""
        if not self.asset_id:
            QMessageBox.warning(self, "تنبيه", "لا يوجد أصل محدد للتعطيل/التفعيل")
            return

        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT is_active FROM fixed_assets WHERE id=?", (self.asset_id,))
            row = cursor.fetchone()
            if not row:
                QMessageBox.warning(self, "خطأ", "الأصل غير موجود")
                return

            current_status = row[0]
            new_status = 0 if current_status == 1 else 1

            cursor.execute("UPDATE fixed_assets SET is_active=? WHERE id=?", (new_status, self.asset_id))
            conn.commit()

            state_text = "تم التعطيل" if new_status == 0 else "تم التفعيل"
            QMessageBox.information(self, "نجاح", f"{state_text} بنجاح")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"فشل التغيير: {e}")
        finally:
            if conn:
                conn.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FixedAssetCardUI()
    window.show()
    sys.exit(app.exec_())
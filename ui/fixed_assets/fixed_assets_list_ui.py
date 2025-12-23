# -*- coding: utf-8 -*-
# file: fixed_assets_list_ui.py

import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QComboBox, QDateEdit,
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

class FixedAssetsListUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("سجل الأصول الثابتة")
        self.setGeometry(100, 100, 1600, 800)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.apply_styles()
        self.load_assets_data()
        
    def apply_styles(self):
        """تطبيق الأنماط على الواجهة"""
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial;
                font-size: 11px;
            }
            
            QLabel {
                color: #2c3e50;
                font-weight: bold;
            }
            
            QLineEdit, QComboBox, QDateEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
            }
            
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 2px solid #3498db;
            }
            
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            
            QPushButton#primaryButton {
                background-color: #3498db;
                color: white;
            }
            
            QPushButton#primaryButton:hover {
                background-color: #2980b9;
            }
            
            QPushButton#secondaryButton {
                background-color: #95a5a6;
                color: white;
            }
            
            QPushButton#secondaryButton:hover {
                background-color: #7f8c8d;
            }
            
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #ecf0f1;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: #3498db;
                color: white;
                border-radius: 4px;
            }
            
            QTableWidget {
                gridline-color: #bdc3c7;
                border: 1px solid #bdc3c7;
            }
            
            QTableWidget::item {
                padding: 6px;
            }
            
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: 1px solid #2c3e50;
                font-weight: bold;
            }
        """)
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        header_label = QLabel("سجل الأصول الثابتة")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px;
            }
        """)
        
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Add new asset button
        self.new_asset_btn = QPushButton("➕ أصل جديد")
        self.new_asset_btn.setObjectName("primaryButton")
        self.new_asset_btn.clicked.connect(self.open_new_asset_form)
        header_layout.addWidget(self.new_asset_btn)
        
        main_layout.addLayout(header_layout)
        
        # Search Group - تمت إضافة خلية البحث
        search_group = QGroupBox("خيارات البحث")
        search_layout = QVBoxLayout(search_group)
        
        # First row: Date range search
        date_search_layout = QHBoxLayout()
        
        date_search_layout.addWidget(QLabel("من تاريخ:"))
        self.from_date_edit = QDateEdit()
        self.from_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.from_date_edit.setCalendarPopup(True)
        self.from_date_edit.setDisplayFormat("yyyy-MM-dd")
        date_search_layout.addWidget(self.from_date_edit)
        
        date_search_layout.addWidget(QLabel("إلى تاريخ:"))
        self.to_date_edit = QDateEdit()
        self.to_date_edit.setDate(QDate.currentDate())
        self.to_date_edit.setCalendarPopup(True)
        self.to_date_edit.setDisplayFormat("yyyy-MM-dd")
        date_search_layout.addWidget(self.to_date_edit)
        
        date_search_layout.addStretch()
        
        # Second row: Text search and buttons
        text_search_layout = QHBoxLayout()
        
        text_search_layout.addWidget(QLabel("بحث بالاسم أو الكود:"))
        self.search_text_edit = QLineEdit()
        self.search_text_edit.setPlaceholderText("أدخل كود أو اسم الأصل للبحث...")
        self.search_text_edit.textChanged.connect(self.search_assets)
        text_search_layout.addWidget(self.search_text_edit)
        
        search_btn = QPushButton("بحث")
        search_btn.setObjectName("primaryButton")
        search_btn.clicked.connect(self.search_assets)
        text_search_layout.addWidget(search_btn)
        
        reset_btn = QPushButton("إعادة تعيين")
        reset_btn.setObjectName("secondaryButton")
        reset_btn.clicked.connect(self.reset_search)
        text_search_layout.addWidget(reset_btn)
        
        export_btn = QPushButton("📊 تصدير")
        export_btn.setObjectName("secondaryButton")
        export_btn.clicked.connect(self.export_data)
        text_search_layout.addWidget(export_btn)
        
        text_search_layout.addStretch()
        
        search_layout.addLayout(date_search_layout)
        search_layout.addLayout(text_search_layout)
        
        main_layout.addWidget(search_group)
        
        # Create table widget مع الترتيب الجديد للأعمدة
        self.assets_table = QTableWidget()
        self.assets_table.setColumnCount(17)  # زيادة عدد الأعمدة
        
        # الترتيب الجديد للأعمدة حسب المتطلبات
        self.assets_table.setHorizontalHeaderLabels([
            "ID",  # عمود مخفي لتخزين معرف الأصل
            "كود الأصل", 
            "الاسم العربي", 
            "التصنيف",
            "طريقة الإهلاك",
            "الوحدة",
            "الكمية", 
            "سعر الوحدة",
            "التكلفة",
            "القيمة التخريدية",
            "مجمع الإهلاك", 
            "صافي القيمة الدفترية",
            "تاريخ الشراء", 
            "تاريخ الاستخدام", 
            "الموقع", 
            "الحالة", 
            "المسؤول"
        ])
        
        # إخفاء عمود ID
        self.assets_table.hideColumn(0)
        
        # Set column widths حسب الترتيب الجديد
        self.assets_table.setColumnWidth(1, 100)   # كود الأصل
        self.assets_table.setColumnWidth(2, 150)   # الاسم العربي
        self.assets_table.setColumnWidth(3, 120)   # التصنيف
        self.assets_table.setColumnWidth(4, 120)   # طريقة الإهلاك
        self.assets_table.setColumnWidth(5, 80)    # الوحدة
        self.assets_table.setColumnWidth(6, 80)    # الكمية
        self.assets_table.setColumnWidth(7, 100)   # سعر الوحدة
        self.assets_table.setColumnWidth(8, 100)   # التكلفة
        self.assets_table.setColumnWidth(9, 100)   # القيمة التخريدية
        self.assets_table.setColumnWidth(10, 100)  # مجمع الإهلاك
        self.assets_table.setColumnWidth(11, 120)  # صافي القيمة الدفترية
        self.assets_table.setColumnWidth(12, 100)  # تاريخ الشراء
        self.assets_table.setColumnWidth(13, 100)  # تاريخ الاستخدام
        self.assets_table.setColumnWidth(14, 120)  # الموقع
        self.assets_table.setColumnWidth(15, 100)  # الحالة
        self.assets_table.setColumnWidth(16, 120)  # المسؤول
        
        # Enable sorting
        self.assets_table.setSortingEnabled(True)
        
        # Enable selection
        self.assets_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.assets_table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Connect double click signal
        self.assets_table.doubleClicked.connect(self.edit_asset)
        
        # Add table to layout
        main_layout.addWidget(self.assets_table)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("عدد الأصول: 0")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        main_layout.addLayout(status_layout)
        
        self.setLayout(main_layout)
    
    def load_assets_data(self):
        """تحميل بيانات الأصول في الجدول"""
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            
            # Query to get all assets with related information حسب الترتيب الجديد
            cursor.execute("""
                SELECT 
                    fa.id,
                    fa.asset_code,
                    fa.asset_name_ar,
                    cat.name_ar as category_name,
                    dm.name_ar as depreciation_method,
                    fa.unit_type,
                    fa.quantity,
                    fa.unit_price,
                    fa.acquisition_cost,
                    fa.salvage_value,
                    fa.accumulated_depreciation,
                    fa.current_book_value,
                    fa.acquisition_date,
                    fa.commissioning_date as usage_date,
                    loc.location_name_ar as location_name,
                    fa.status,
                    resp.name_ar as responsible_name
                FROM fixed_assets fa
                LEFT JOIN fixed_asset_categories cat ON fa.category_id = cat.id
                LEFT JOIN depreciation_methods dm ON fa.depreciation_method_id = dm.id
                LEFT JOIN asset_locations loc ON fa.location_id = loc.id
                LEFT JOIN asset_responsibles resp ON fa.responsible_id = resp.id
                ORDER BY fa.acquisition_date DESC
            """)
            
            assets = cursor.fetchall()
            
            self.assets_table.setRowCount(len(assets))
            
            for row, asset in enumerate(assets):
                for col, value in enumerate(asset):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    
                    # Format numeric columns حسب الترتيب الجديد
                    if col in [6, 7, 8, 9, 10, 11]:  # الكمية، سعر الوحدة، التكلفة، القيمة التخريدية، مجمع الإهلاك، صافي القيمة
                        try:
                            numeric_value = float(value) if value is not None else 0.0
                            if col in [6]:  # الكمية
                                item.setText(f"{numeric_value:,.0f}")
                            else:  # القيم المالية
                                item.setText(f"{numeric_value:,.2f}")
                            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        except (ValueError, TypeError):
                            pass
                    
                    self.assets_table.setItem(row, col, item)
            
            self.status_label.setText(f"عدد الأصول: {len(assets)}")
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل بيانات الأصول: {e}")
        finally:
            if conn:
                conn.close()
    
    def search_assets(self):
        """بحث الأصول حسب نطاق التاريخ والنص"""
        from_date = self.from_date_edit.date().toString("yyyy-MM-dd")
        to_date = self.to_date_edit.date().toString("yyyy-MM-dd")
        search_text = self.search_text_edit.text().strip()
        
        try:
            conn = get_fixed_assets_db_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    fa.id,
                    fa.asset_code,
                    fa.asset_name_ar,
                    cat.name_ar as category_name,
                    dm.name_ar as depreciation_method,
                    fa.unit_type,
                    fa.quantity,
                    fa.unit_price,
                    fa.acquisition_cost,
                    fa.salvage_value,
                    fa.accumulated_depreciation,
                    fa.current_book_value,
                    fa.acquisition_date,
                    fa.commissioning_date as usage_date,
                    loc.location_name_ar as location_name,
                    fa.status,
                    resp.name_ar as responsible_name
                FROM fixed_assets fa
                LEFT JOIN fixed_asset_categories cat ON fa.category_id = cat.id
                LEFT JOIN depreciation_methods dm ON fa.depreciation_method_id = dm.id
                LEFT JOIN asset_locations loc ON fa.location_id = loc.id
                LEFT JOIN asset_responsibles resp ON fa.responsible_id = resp.id
                WHERE fa.acquisition_date BETWEEN ? AND ?
            """
            
            params = [from_date, to_date]
            
            if search_text:
                query += " AND (fa.asset_code LIKE ? OR fa.asset_name_ar LIKE ?)"
                params.extend([f"%{search_text}%", f"%{search_text}%"])
            
            query += " ORDER BY fa.acquisition_date DESC"
            
            cursor.execute(query, params)
            
            assets = cursor.fetchall()
            
            self.assets_table.setRowCount(len(assets))
            
            for row, asset in enumerate(assets):
                for col, value in enumerate(asset):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    
                    # Format numeric columns
                    if col in [6, 7, 8, 9, 10, 11]:
                        try:
                            numeric_value = float(value) if value is not None else 0.0
                            if col in [6]:  # الكمية
                                item.setText(f"{numeric_value:,.0f}")
                            else:  # القيم المالية
                                item.setText(f"{numeric_value:,.2f}")
                            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        except (ValueError, TypeError):
                            pass
                    
                    self.assets_table.setItem(row, col, item)
            
            self.status_label.setText(f"عدد الأصول: {len(assets)}")
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في البحث: {e}")
        finally:
            if conn:
                conn.close()
    
    def reset_search(self):
        """إعادة تعيين البحث وعرض جميع البيانات"""
        self.from_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.to_date_edit.setDate(QDate.currentDate())
        self.search_text_edit.clear()
        self.load_assets_data()
    
    def export_data(self):
        """تصدير البيانات إلى ملف"""
        # يمكن تطوير هذه الوظيفة لاحقاً
        QMessageBox.information(self, "تصدير", "سيتم تطوير وظيفة التصدير في المستقبل")
    
    def open_new_asset_form(self):
        """فتح نموذج إضافة أصل جديد"""
        from fixed_asset_card_ui import FixedAssetCardUI
        self.asset_form = FixedAssetCardUI()
        self.asset_form.show()
    
    def edit_asset(self, index):
        """تحرير الأصل المحدد"""
        row = index.row()
        asset_id = self.assets_table.item(row, 0).text()  # العمود الأول (مخفي) يحتوي على ID
        
        from fixed_asset_card_ui import FixedAssetCardUI
        self.asset_form = FixedAssetCardUI(asset_id=int(asset_id))
        self.asset_form.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FixedAssetsListUI()
    window.show()
    sys.exit(app.exec_())
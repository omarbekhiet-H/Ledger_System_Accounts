import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
# إعداد المسارات
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.inventory.setting.locations_manager import LocationManager

class LocationsUI(QWidget):
    def __init__(self, db_path: str):
        super().__init__()
        self.manager = LocationManager(db_path)
        self.setup_ui()
        self.load_locations()
        self.setWindowTitle("إدارة المخازن")
        self.setMinimumSize(800, 500)
        self.setFont(QFont('Arial', 12))

    def setup_ui(self):
        # إطار رئيسي مزدوج اللون
        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet("""
            #mainFrame {
                background-color: #FFFFFF;
                border: 3px solid #000000;
                border-radius: 10px;
                padding: 2px;
            }
            #mainFrame::before {
                content: "";
                position: absolute;
                top: 2px;
                left: 2px;
                right: 2px;
                bottom: 2px;
                border: 1px solid #FF0000;
                border-radius: 7px;
                pointer-events: none;
            }
        """)
        
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(main_frame)
        self.layout().setContentsMargins(0, 0, 0, 0)
        
        # شريط العنوان مع زر الإغلاق
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setStyleSheet("""
            #titleBar {
                background-color: #2C3E50;
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
                padding: 5px;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 5, 5, 5)

        # عنوان النافذة
        title_label = QLabel("إدارة المخازن")
        title_label.setStyleSheet("""
            color: white;
            font-weight: bold;
            font-size: 16px;
        """)

        # زر إغلاق النافذة
        close_btn = QPushButton("X")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            #closeButton {
                background-color: #E74C3C;
                color: white;
                border-radius: 15px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            #closeButton:hover {
                background-color: #C0392B;
            }
        """)
        close_btn.clicked.connect(self.close)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        main_layout.addWidget(title_bar)
        
        # مجموعة بيانات الإدخال
        form_group = QGroupBox("بيانات المخزن")
        form_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                right: 10px;
                padding: 0 5px;
            }
        """)
        form_layout = QHBoxLayout(form_group)
        form_layout.setContentsMargins(10, 15, 10, 10)
        
        # حقول الإدخال
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("أدخل كود الموقع")
        self.code_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        
        self.name_ar_input = QLineEdit()
        self.name_ar_input.setPlaceholderText("أدخل اسم الموقع")
        self.name_ar_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        
        # تسميات الحقول
        form_layout.addWidget(QLabel("كود الموقع:"))
        form_layout.addWidget(self.code_input)
        form_layout.addWidget(QLabel("اسم الموقع:"))
        form_layout.addWidget(self.name_ar_input)
        
        main_layout.addWidget(form_group)
        
        # أزرار التحكم
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 10)
        
        buttons = [
            ("إضافة", self.add_location, "#4CAF50"),
            ("تعديل", self.update_location, "#2196F3"),
            ("حذف", self.delete_location, "#f44336"),
            ("مسح الحقول", self.clear_inputs, "#607D8B"),
            ("تحديث", self.load_locations, "#9C27B0")
        ]

        for text, handler, color in buttons:
            btn = QPushButton(text)
            btn.setObjectName("controlButton")
            btn.setStyleSheet(f"""
                #controlButton {{
                    background-color: {color};
                    color: white;
                    font-weight: bold;
                    border-radius: 5px;
                    padding: 8px 16px;
                    border: none;
                    min-width: 100px;
                    min-height: 35px;
                }}
                #controlButton:hover {{
                    background-color: {'#45a049' if color == '#4CAF50' else 
                                     '#0b7dda' if color == '#2196F3' else 
                                     '#d32f2f' if color == '#f44336' else 
                                     '#757575' if color == '#607D8B' else 
                                     '#7b1fa2'};
                }}
            """)
            btn.clicked.connect(handler)
            button_layout.addWidget(btn)
        
        main_layout.addWidget(button_container)
        
        # مجموعة جدول البيانات
        table_group = QGroupBox("قائمة المخازن")
        table_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                right: 10px;
                padding: 0 5px;
            }
        """)
        table_layout = QVBoxLayout(table_group)
        table_layout.setContentsMargins(10, 15, 10, 10)
        
        # جدول العرض
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["كود الموقع", "اسم الموقع", "معرّف"])
        
        # تنسيق الجدول
        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #2C3E50;
                color: white;
                padding: 5px;
                font-weight: bold;
                border: none;
            }
        """)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #BDC3C7;
                gridline-color: #BDC3C7;
                selection-background-color: #3498DB;
                selection-color: white;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        
        # تحسين عرض الجدول
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # الكود
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # الاسم
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # المعرف
        
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.cellClicked.connect(self.on_row_selected)
        
        table_layout.addWidget(self.table)
        main_layout.addWidget(table_group)

    def load_locations(self):
        """تحميل المواقع وعرضها"""
        self.table.setRowCount(0)
        locations = self.manager.list_active_locations()
        for row_idx, loc in enumerate(locations):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(loc["code"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(loc["location_name_ar"]))
            
            id_item = QTableWidgetItem(str(loc["id"]))
            id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row_idx, 2, id_item)
            
            # تلوين الصفوف الزوجية
            if row_idx % 2 == 0:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row_idx, col)
                    if item:
                        item.setBackground(QColor(236, 240, 241))

    def on_row_selected(self, row, _):
        """عند اختيار صف من الجدول"""
        if row < 0:
            return

        self.code_input.setText(self.table.item(row, 0).text())
        self.name_ar_input.setText(self.table.item(row, 1).text())

    def clear_inputs(self):
        """مسح جميع حقول الإدخال"""
        self.code_input.clear()
        self.name_ar_input.clear()
        self.table.clearSelection()

    def validate_inputs(self):
        """التحقق من صحة البيانات المدخلة"""
        if not self.code_input.text().strip():
            QMessageBox.warning(self, "تنبيه", "يجب إدخال كود الموقع")
            return False
        if not self.name_ar_input.text().strip():
            QMessageBox.warning(self, "تنبيه", "يجب إدخال اسم الموقع")
            return False
        return True

    def add_location(self):
        """إضافة موقع جديد"""
        if not self.validate_inputs():
            return

        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()

        if self.manager.location_exists(code):
            QMessageBox.warning(self, "تحذير", "كود الموقع موجود مسبقاً")
            return

        if self.manager.create_location(code, name_ar):
            QMessageBox.information(self, "تم", "تمت إضافة الموقع بنجاح")
            self.clear_inputs()
            self.load_locations()
        else:
            QMessageBox.critical(self, "خطأ", "فشل في إضافة الموقع")

    def update_location(self):
        """تعديل الموقع المحدد"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار موقع للتعديل")
            return

        if not self.validate_inputs():
            return

        location_id = int(self.table.item(selected, 2).text())
        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()

        if self.manager.location_exists(code, exclude_id=location_id):
            QMessageBox.warning(self, "تحذير", "كود الموقع موجود مسبقاً لموقع آخر")
            return

        if self.manager.update_location(location_id, code, name_ar):
            QMessageBox.information(self, "تم", "تم تعديل الموقع بنجاح")
            self.clear_inputs()
            self.load_locations()
        else:
            QMessageBox.critical(self, "خطأ", "فشل في تعديل الموقع")

    def delete_location(self):
        """حذف الموقع المحدد"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار موقع للحذف")
            return

        location_id = int(self.table.item(selected, 2).text())
        confirm = QMessageBox.question(
            self, 
            "تأكيد الحذف", 
            "هل أنت متأكد من حذف هذا الموقع؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            if self.manager.delete_location(location_id):
                QMessageBox.information(self, "تم", "تم حذف الموقع بنجاح")
                self.clear_inputs()
                self.load_locations()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في حذف الموقع")
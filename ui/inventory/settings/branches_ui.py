import os
import sys
import csv
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, 
    QComboBox, QFileDialog, QHeaderView, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

# إعداد المسارات
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.inventory.setting.branch_manager import BranchManager
from database.manager.inventory.setting.locations_manager import LocationManager

class BranchesUI(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.manager = BranchManager(db_path)
        self.location_manager = LocationManager(db_path)
        self.current_branch_id = None
        
        self.setup_ui()
        self.load_locations()
        self.load_branches()

    def setup_ui(self):
        self.setWindowTitle("الاقسام و الادارات")
        self.setGeometry(100, 100, 1000, 600)
        
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
        title_label = QLabel("إدارة الأقسام والإدارات")
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
        
        # مجموعة إدخال البيانات
        form_group = QGroupBox("بيانات القسم/الإدارة")
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
        form_layout = QVBoxLayout(form_group)
        
        # حاوية لحقول الإدخال
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        
        # حقول الإدخال
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("كود الفرع")
        self.code_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        
        self.name_ar_input = QLineEdit()
        self.name_ar_input.setPlaceholderText("الاسم العربي")
        self.name_ar_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        
        self.name_en_input = QLineEdit()
        self.name_en_input.setPlaceholderText("الاسم الإنجليزي")
        self.name_en_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        
        self.location_input = QComboBox()
        self.location_input.setPlaceholderText("اختر الموقع")
        self.location_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        
        # تسميات الحقول
        input_layout.addWidget(QLabel("الكود:"))
        input_layout.addWidget(self.code_input)
        input_layout.addWidget(QLabel("الاسم عربي:"))
        input_layout.addWidget(self.name_ar_input)
        input_layout.addWidget(QLabel("الاسم إنجليزي:"))
        input_layout.addWidget(self.name_en_input)
        input_layout.addWidget(QLabel("الموقع:"))
        input_layout.addWidget(self.location_input)
        
        form_layout.addWidget(input_container)
        main_layout.addWidget(form_group)
        
        # أزرار التحكم
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 10)
        
        self.add_btn = QPushButton("إضافة")
        self.add_btn.setObjectName("controlButton")
        self.add_btn.setStyleSheet("""
            #controlButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px 16px;
                border: none;
            }
            #controlButton:hover {
                background-color: #45a049;
            }
        """)
        self.add_btn.clicked.connect(self.add_branch)
        
        self.update_btn = QPushButton("تعديل")
        self.update_btn.setObjectName("controlButton")
        self.update_btn.setStyleSheet("""
            #controlButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px 16px;
                border: none;
            }
            #controlButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.update_btn.clicked.connect(self.update_branch)
        self.update_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("حذف")
        self.delete_btn.setObjectName("controlButton")
        self.delete_btn.setStyleSheet("""
            #controlButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px 16px;
                border: none;
            }
            #controlButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_branch)
        self.delete_btn.setEnabled(False)
        
        self.clear_btn = QPushButton("مسح النموذج")
        self.clear_btn.setObjectName("controlButton")
        self.clear_btn.setStyleSheet("""
            #controlButton {
                background-color: #9E9E9E;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px 16px;
                border: none;
            }
            #controlButton:hover {
                background-color: #757575;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_form)
        
        self.export_btn = QPushButton("تصدير CSV")
        self.export_btn.setObjectName("controlButton")
        self.export_btn.setStyleSheet("""
            #controlButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px 16px;
                border: none;
            }
            #controlButton:hover {
                background-color: #e68a00;
            }
        """)
        self.export_btn.clicked.connect(self.export_csv)
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.update_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.export_btn)
        
        main_layout.addWidget(button_container)
        
        # مجموعة البحث والعرض
        table_group = QGroupBox("قائمة الأقسام والإدارات")
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
        
        # مربع البحث
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث بالاسم أو الكود...")
        self.search_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        self.search_input.textChanged.connect(self.load_branches)
        
        search_layout.addWidget(QLabel("بحث:"))
        search_layout.addWidget(self.search_input)
        table_layout.addWidget(search_container)
        
        # جدول الفروع
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "الكود", "الاسم العربي", "الاسم الإنجليزي", 
            "الموقع", "تاريخ الإنشاء", "معرف"
        ])
        
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
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellClicked.connect(self.load_selected_branch)
        
        table_layout.addWidget(self.table)
        main_layout.addWidget(table_group)

    def load_locations(self):
        """تحميل قائمة المواقع"""
        self.location_input.clear()
        self.location_input.addItem("اختر الموقع", None)
        
        locations = self.location_manager.list_active_locations()
        for loc in locations:
            self.location_input.addItem(loc["location_name_ar"], loc["id"])

    def load_branches(self):
        """تحميل الفروع في الجدول"""
        self.table.setRowCount(0)
        search_term = self.search_input.text().strip()
        
        if search_term:
            branches = self.manager.search_branches(search_term)
        else:
            branches = self.manager.list_active_branches()
        
        for row_idx, branch in enumerate(branches):
            self.table.insertRow(row_idx)
            
            self.table.setItem(row_idx, 0, QTableWidgetItem(branch["code"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(branch["name_ar"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(branch.get("name_en", "")))
            self.table.setItem(row_idx, 3, QTableWidgetItem(branch.get("location_name", "")))
            self.table.setItem(row_idx, 4, QTableWidgetItem(branch.get("created_at", "")))
            
            # تخزين ID في العمود الأخير مخفي
            id_item = QTableWidgetItem(str(branch["id"]))
            id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row_idx, 5, id_item)
            
            # تلوين الصفوف الزوجية
            if row_idx % 2 == 0:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row_idx, col)
                    item.setBackground(QColor(236, 240, 241))

    def load_selected_branch(self, row, column):
        """تحميل بيانات الفرع المحدد في النموذج"""
        self.current_branch_id = int(self.table.item(row, 5).text())
        
        self.code_input.setText(self.table.item(row, 0).text())
        self.name_ar_input.setText(self.table.item(row, 1).text())
        self.name_en_input.setText(self.table.item(row, 2).text())
        
        # تحديد الموقع في الكومبو بوكس
        location_name = self.table.item(row, 3).text()
        idx = self.location_input.findText(location_name)
        if idx >= 0:
            self.location_input.setCurrentIndex(idx)
        
        # تفعيل أزرار التعديل والحذف
        self.update_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.add_btn.setEnabled(False)

    def clear_form(self):
        """مسح النموذج وإعادة الضبط"""
        self.current_branch_id = None
        self.code_input.clear()
        self.name_ar_input.clear()
        self.name_en_input.clear()
        self.location_input.setCurrentIndex(0)
        
        # إعادة ضبط الأزرار
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.add_btn.setEnabled(True)
        
        # إلغاء تحديد الصف في الجدول
        self.table.clearSelection()

    def validate_form(self):
        """التحقق من صحة بيانات النموذج"""
        if not self.code_input.text().strip():
            QMessageBox.warning(self, "خطأ", "يرجى إدخال كود الفرع")
            return False
            
        if not self.name_ar_input.text().strip():
            QMessageBox.warning(self, "خطأ", "يرجى إدخال الاسم العربي")
            return False
            
        if not self.location_input.currentData():
            QMessageBox.warning(self, "خطأ", "يرجى اختيار الموقع")
            return False
            
        return True

    def add_branch(self):
        """إضافة فرع جديد"""
        if not self.validate_form():
            return
            
        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()
        location_id = self.location_input.currentData()
        
        # ========== التعديل هنا ==========
        # استخدام الدالة الجديدة التي ترجع معرف الفرع بدلاً من True/False
        branch_id = self.manager.create_branch(code, name_ar, name_en, location_id)
        
        if branch_id:
            QMessageBox.information(self, "نجاح", "تمت إضافة الفرع بنجاح")
            self.load_branches()
            self.clear_form()
        else:
            # لا داعي لعرض رسالة خطأ هنا لأن الدالة create_branch تعرض الرسائل بنفسها
            pass
        # ========== نهاية التعديل ==========

    def update_branch(self):
        """تحديث بيانات الفرع"""
        if not self.validate_form() or not self.current_branch_id:
            return
            
        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()
        location_id = self.location_input.currentData()
        
        # ========== التعديل هنا ==========
        # التحقق من عدم تكرار الكود (مع استثناء الفرع الحالي)
        if self.manager.branch_exists(code, self.current_branch_id):
            QMessageBox.warning(self, "خطأ", "كود الفرع موجود مسبقاً في فرع آخر")
            return
            
        if self.manager.update_branch(self.current_branch_id, code, name_ar, name_en, location_id):
            QMessageBox.information(self, "نجاح", "تم تحديث الفرع بنجاح")
            self.load_branches()
            self.clear_form()
        else:
            # لا داعي لعرض رسالة خطأ هنا لأن الدالة update_branch تعرض الرسائل بنفسها
            pass
        # ========== نهاية التعديل ==========

    def delete_branch(self):
        """حذف الفرع المحدد"""
        if not self.current_branch_id:
            return
            
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا الفرع؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # ========== التعديل هنا ==========
            if self.manager.delete_branch(self.current_branch_id):
                QMessageBox.information(self, "نجاح", "تم حذف الفرع بنجاح")
                self.load_branches()
                self.clear_form()
            else:
                # لا داعي لعرض رسالة خطأ هنا لأن الدالة delete_branch تعرض الرسائل بنفسها
                pass
            # ========== نهاية التعديل ==========

    def export_csv(self):
        """تصدير البيانات إلى ملف CSV"""
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ ملف CSV",
            "", "ملفات CSV (*.csv)"
        )
        
        if not path:
            return
            
        try:
            with open(path, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                
                # كتابة العناوين
                headers = [
                    "الكود", "الاسم العربي", "الاسم الإنجليزي",
                    "الموقع", "تاريخ الإنشاء"
                ]
                writer.writerow(headers)
                
                # كتابة البيانات
                for row in range(self.table.rowCount()):
                    row_data = [
                        self.table.item(row, col).text() 
                        for col in range(self.table.columnCount()-1)  # استبعاد عمود المعرف
                    ]
                    writer.writerow(row_data)
                    
            QMessageBox.information(self, "نجاح", "تم تصدير البيانات بنجاح")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تصدير البيانات: {str(e)}")
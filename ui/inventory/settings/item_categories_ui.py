import os
import sys
import csv
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QComboBox, 
    QFileDialog, QHeaderView, QGroupBox, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

# إعداد المسارات
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.inventory.setting.item_categories_manager import ItemCategoryManager

class ItemCategoriesUI(QWidget):
    def __init__(self, db_path: str):
        super().__init__()
        self.manager = ItemCategoryManager(db_path)
        self.current_category_id = None
        
        self.setup_ui()
        self.load_categories()
        self.setMinimumSize(1000, 600)
        self.setWindowTitle("إدارة مجموعات الأصناف")

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
        title_label = QLabel("إدارة مجموعات الأصناف")
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
        form_group = QGroupBox("بيانات المجموعة")
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
        form_layout.setContentsMargins(10, 15, 10, 10)
        form_layout.setSpacing(5)  # تقليل المسافة بين العناصر
        
        # حاوية لحقول الإدخال
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)
        
        # حقول الإدخال
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("كود المجموعة")
        self.code_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        
        self.name_ar_input = QLineEdit()
        self.name_ar_input.setPlaceholderText("الاسم العربي")
        self.name_ar_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        
        self.name_en_input = QLineEdit()
        self.name_en_input.setPlaceholderText("الاسم الإنجليزي")
        self.name_en_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        
        self.parent_input = QComboBox()
        self.parent_input.setPlaceholderText("اختر الفئة الأب")
        self.parent_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        
        # تسميات الحقول
        input_layout.addWidget(QLabel("الكود:"))
        input_layout.addWidget(self.code_input)
        input_layout.addWidget(QLabel("الاسم عربي:"))
        input_layout.addWidget(self.name_ar_input)
        input_layout.addWidget(QLabel("الاسم إنجليزي:"))
        input_layout.addWidget(self.name_en_input)
        input_layout.addWidget(QLabel("الفئة الأب:"))
        input_layout.addWidget(self.parent_input)
        
        form_layout.addWidget(input_container)
        
        # حاوية للوصف (بدون مسافة علوية)
        description_container = QWidget()
        description_layout = QHBoxLayout(description_container)
        description_layout.setContentsMargins(0, 0, 0, 0)  # لا توجد مسافة علوية
        description_layout.setSpacing(10)
        
        # حقل الوصف
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("الوصف (اختياري)")
        self.description_input.setMaximumHeight(40)
        self.description_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        
        description_layout.addWidget(QLabel("الوصف:"))
        description_layout.addWidget(self.description_input)
        
        form_layout.addWidget(description_container)
        
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
        self.add_btn.clicked.connect(self.add_category)
        
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
        self.update_btn.clicked.connect(self.update_category)
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
        self.delete_btn.clicked.connect(self.delete_category)
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
        table_group = QGroupBox("قائمة المجموعات")
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
        
        # مربع البحث
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 10)
        search_layout.setSpacing(10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث بالاسم أو الكود...")
        self.search_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        self.search_input.textChanged.connect(self.load_categories)
        
        search_layout.addWidget(QLabel("بحث:"))
        search_layout.addWidget(self.search_input)
        table_layout.addWidget(search_container)
        
        # جدول المجموعات
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "الكود", "الاسم العربي", "الاسم الإنجليزي", 
            "الفئة الأب", "الوصف", "معرف"
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
        self.table.cellClicked.connect(self.load_selected_category)
        
        table_layout.addWidget(self.table)
        main_layout.addWidget(table_group)

    def load_categories(self):
        """تحميل الفئات في الجدول"""
        self.table.setRowCount(0)
        self.parent_input.clear()
        self.parent_input.addItem("بدون فئة أب", None)
        
        search_term = self.search_input.text().strip()
        
        if search_term:
            categories = self.manager.search_categories(search_term)
        else:
            categories = self.manager.list_active_categories()
        
        # تعبئة قائمة الفئات الأب
        for cat in categories:
            display_text = f"{cat['name_ar']} ({cat['code']})" if cat['code'] else cat['name_ar']
            self.parent_input.addItem(display_text, cat["id"])
        
        for row_idx, category in enumerate(categories):
            self.table.insertRow(row_idx)
            
            self.table.setItem(row_idx, 0, QTableWidgetItem(category["code"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(category["name_ar"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(category.get("name_en", "")))
            self.table.setItem(row_idx, 3, QTableWidgetItem(category.get("parent_name", "بدون")))
            self.table.setItem(row_idx, 4, QTableWidgetItem(category.get("description", "")))
            
            # تخزين ID في العمود الأخير مخفي
            id_item = QTableWidgetItem(str(category["id"]))
            id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row_idx, 5, id_item)
            
            # تلوين الصفوف الزوجية
            if row_idx % 2 == 0:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row_idx, col)
                    item.setBackground(QColor(236, 240, 241))

    def load_selected_category(self, row, column):
        """تحميل بيانات الفئة المحددة في النموذج"""
        self.current_category_id = int(self.table.item(row, 5).text())
        
        self.code_input.setText(self.table.item(row, 0).text())
        self.name_ar_input.setText(self.table.item(row, 1).text())
        self.name_en_input.setText(self.table.item(row, 2).text())
        self.description_input.setPlainText(self.table.item(row, 4).text())
        
        # تحديد الفئة الأب في الكومبو بوكس
        parent_name = self.table.item(row, 3).text()
        if parent_name != "بدون":
            idx = self.parent_input.findText(parent_name, Qt.MatchContains)
            if idx >= 0:
                self.parent_input.setCurrentIndex(idx)
        else:
            self.parent_input.setCurrentIndex(0)
        
        # تفعيل أزرار التعديل والحذف
        self.update_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.add_btn.setEnabled(False)

    def clear_form(self):
        """مسح النموذج وإعادة الضبط"""
        self.current_category_id = None
        self.code_input.clear()
        self.name_ar_input.clear()
        self.name_en_input.clear()
        self.description_input.clear()
        self.parent_input.setCurrentIndex(0)
        
        # إعادة ضبط الأزرار
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.add_btn.setEnabled(True)
        
        # إلغاء تحديد الصف في الجدول
        self.table.clearSelection()

    def validate_form(self):
        """التحقق من صحة بيانات النموذج"""
        if not self.code_input.text().strip():
            QMessageBox.warning(self, "خطأ", "يرجى إدخال كود المجموعة")
            return False
            
        if not self.name_ar_input.text().strip():
            QMessageBox.warning(self, "خطأ", "يرجى إدخال الاسم العربي")
            return False
            
        return True

    def add_category(self):
        """إضافة فئة جديدة"""
        if not self.validate_form():
            return
            
        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()
        description = self.description_input.toPlainText().strip()
        parent_id = self.parent_input.currentData()
        
        if self.manager.category_exists(code):
            QMessageBox.warning(self, "خطأ", "كود المجموعة موجود مسبقاً")
            return
            
        if self.manager.create_category(code, name_ar, name_en, parent_id, description):
            QMessageBox.information(self, "نجاح", "تمت إضافة المجموعة بنجاح")
            self.load_categories()
            self.clear_form()
        else:
            QMessageBox.critical(self, "خطأ", "فشل في إضافة المجموعة")

    def update_category(self):
        """تحديث بيانات الفئة"""
        if not self.validate_form() or not self.current_category_id:
            return
            
        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()
        description = self.description_input.toPlainText().strip()
        parent_id = self.parent_input.currentData()
        
        if self.manager.category_exists(code, self.current_category_id):
            QMessageBox.warning(self, "خطأ", "كود المجموعة موجود مسبقاً في فئة أخرى")
            return
            
        if self.manager.update_category(self.current_category_id, code, name_ar, name_en, parent_id, description):
            QMessageBox.information(self, "نجاح", "تم تحديث المجموعة بنجاح")
            self.load_categories()
            self.clear_form()
        else:
            QMessageBox.critical(self, "خطأ", "فشل في تحديث المجموعة")

    def delete_category(self):
        """حذف الفئة المحددة"""
        if not self.current_category_id:
            return
            
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            "هل أنت متأكد من حذف هذه الفئة؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.manager.delete_category(self.current_category_id):
                QMessageBox.information(self, "نجاح", "تم حذف الفئة بنجاح")
                self.load_categories()
                self.clear_form()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في حذف الفئة")

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
                    "الكود", "الاسم العربي", "الاسم الإنجليزi",
                    "الفئة الأب", "الوصف"
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

if __name__ == '__main__':
    # المسار إلى قاعدة البيانات
    db_path = os.path.join(project_root, 'database', 'database.db')
    
    # تهيئة التطبيق
    app = QApplication(sys.argv)
    
    # إنشاء نسخة من الواجهة
    window = ItemCategoriesUI(db_path)
    
    # إظهار النافذة
    window.show()
    
    # بدء تشغيل حلقة الأحداث
    sys.exit(app.exec_())
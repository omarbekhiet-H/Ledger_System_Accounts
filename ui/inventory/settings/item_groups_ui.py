import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QComboBox, 
    QFileDialog, QHeaderView, QGroupBox
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import csv

# إعداد المسارات
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.inventory.setting.item_groups_manager import ItemGroupManager
from database.manager.inventory.setting.item_categories_manager import ItemCategoryManager

class ItemGroupsUI(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.manager = ItemGroupManager(db_path)
        self.category_manager = ItemCategoryManager(db_path)
        self.setWindowTitle("إدارة فئات الأصناف")
        self.setGeometry(100, 100, 1000, 650)
        self.setup_ui()
        self.load_groups()
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
        title_label = QLabel("إدارة فئات الأصناف")
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
        form_group = QGroupBox("بيانات الفئة")
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
        self.code_input.setPlaceholderText("أدخل الكود")
        self.code_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        
        self.name_ar_input = QLineEdit()
        self.name_ar_input.setPlaceholderText("أدخل الاسم العربي")
        self.name_ar_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        
        self.name_en_input = QLineEdit()
        self.name_en_input.setPlaceholderText("أدخل الاسم الإنجليزي")
        self.name_en_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        
        self.category_input = QComboBox()
        self.category_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        
        # تسميات الحقول
        input_layout.addWidget(QLabel("الكود:"))
        input_layout.addWidget(self.code_input)
        input_layout.addWidget(QLabel("الاسم عربي:"))
        input_layout.addWidget(self.name_ar_input)
        input_layout.addWidget(QLabel("الاسم إنجليزي:"))
        input_layout.addWidget(self.name_en_input)
        input_layout.addWidget(QLabel("الفئة:"))
        input_layout.addWidget(self.category_input)
        
        form_layout.addWidget(input_container)
        
        # حقل الوصف
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("أدخل الوصف (اختياري)")
        self.description_input.setMaximumHeight(80)
        self.description_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        form_layout.addWidget(QLabel("الوصف:"))
        form_layout.addWidget(self.description_input)
        
        main_layout.addWidget(form_group)
        
        # مجموعة البحث والفلترة
        filter_group = QGroupBox("فلترة البيانات")
        filter_group.setStyleSheet("""
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
        filter_layout = QHBoxLayout(filter_group)
        
        # فلترة وبحث
        self.filter_category_input = QComboBox()
        self.filter_category_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        self.filter_category_input.currentIndexChanged.connect(self.load_groups)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث بالاسم...")
        self.search_input.setStyleSheet("padding: 5px; border: 1px solid #BDC3C7;")
        self.search_input.textChanged.connect(self.load_groups)
        
        filter_layout.addWidget(QLabel("فلترة حسب الفئة:"))
        filter_layout.addWidget(self.filter_category_input)
        filter_layout.addWidget(QLabel("بحث:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addStretch()
        
        main_layout.addWidget(filter_group)
        
        # أزرار التحكم
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 10)
        
        buttons = [
            ("إضافة", self.add_group, "#4CAF50"),
            ("تعديل", self.update_group, "#2196F3"),
            ("حذف", self.delete_group, "#f44336"),
            ("مسح النموذج", self.clear_form, "#607D8B"),
            ("تصدير CSV", self.export_csv, "#FF9800"),
            ("تحديث", self.load_groups, "#9C27B0")
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
                                     '#e68a00' if color == '#FF9800' else 
                                     '#7b1fa2'};
                }}
            """)
            btn.clicked.connect(handler)
            button_layout.addWidget(btn)
        
        main_layout.addWidget(button_container)
        
        # مجموعة جدول البيانات
        table_group = QGroupBox("قائمة الفئات")
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
        
        # جدول العرض
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["الكود", "الاسم", "الفئة", "الوصف", "معرّف"])
        
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
        
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.cellClicked.connect(self.load_selected_group)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        
        table_layout.addWidget(self.table)
        main_layout.addWidget(table_group)

    def load_groups(self):
        self.table.setRowCount(0)
        self.category_input.clear()
        self.filter_category_input.blockSignals(True)
        self.filter_category_input.clear()
        self.filter_category_input.blockSignals(False)

        categories = self.category_manager.list_active_categories()
        self.filter_category_input.addItem("عرض الكل", None)

        for cat in categories:
            self.category_input.addItem(cat["name_ar"], cat["id"])
            self.filter_category_input.addItem(cat["name_ar"], cat["id"])

        selected_category_id = self.filter_category_input.currentData()
        search_text = self.search_input.text().strip()

        if selected_category_id:
            groups = self.manager.list_groups_by_category(selected_category_id)
        else:
            groups = self.manager.list_active_groups()

        # تطبيق البحث
        if search_text:
            groups = [g for g in groups if search_text in g["name_ar"]]

        for row_idx, grp in enumerate(groups):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(grp["code"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(grp["name_ar"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(grp.get("category_name", "")))
            self.table.setItem(row_idx, 3, QTableWidgetItem(grp.get("description", "")))
            
            id_item = QTableWidgetItem(str(grp["id"]))
            id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(row_idx, 4, id_item)
            
            # تلوين الصفوف الزوجية
            if row_idx % 2 == 0:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row_idx, col)
                    item.setBackground(QColor(236, 240, 241))

    def load_selected_group(self, row, column):
        self.code_input.setText(self.table.item(row, 0).text())
        self.name_ar_input.setText(self.table.item(row, 1).text())
        self.description_input.setText(self.table.item(row, 3).text())
        group_id = int(self.table.item(row, 4).text())
        group = self.manager.get_group_by_id(group_id)
        self.name_en_input.setText(group.get("name_en", ""))
        idx = self.category_input.findData(group["category_id"])
        if idx >= 0:
            self.category_input.setCurrentIndex(idx)

    def clear_form(self):
        self.code_input.clear()
        self.name_ar_input.clear()
        self.name_en_input.clear()
        self.description_input.clear()
        self.category_input.setCurrentIndex(-1)
        self.table.clearSelection()

    def add_group(self):
        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()
        category_id = self.category_input.currentData()
        description = self.description_input.toPlainText().strip()

        if not code or not name_ar or not category_id:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال الكود والاسم واختيار الفئة.")
            return

        # التحقق من التكرار
        if self.manager.group_exists(code):
            QMessageBox.warning(self, "موجود مسبقًا", "الكود مستخدم من قبل.")
            return

        success = self.manager.create_group(code, name_ar, name_en, category_id, description)
        if success:
            QMessageBox.information(self, "تم", "تمت إضافة المجموعة بنجاح.")
            self.load_groups()
            self.clear_form()
        else:
            QMessageBox.critical(self, "خطأ", "فشل في إضافة المجموعة.")

    def update_group(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار مجموعة للتعديل.")
            return

        group_id = int(self.table.item(selected, 4).text())
        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()
        category_id = self.category_input.currentData()
        description = self.description_input.toPlainText().strip()

        success = self.manager.update_group(group_id, code, name_ar, name_en, category_id, description)
        if success:
            QMessageBox.information(self, "تم", "تم تعديل المجموعة بنجاح.")
            self.load_groups()
            self.clear_form()
        else:
            QMessageBox.critical(self, "خطأ", "فشل في تعديل المجموعة.")

    def delete_group(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار مجموعة للحذف.")
            return

        group_id = int(self.table.item(selected, 4).text())
        confirm = QMessageBox.question(self, "تأكيد", "هل أنت متأكد من حذف المجموعة؟")
        if confirm == QMessageBox.Yes:
            success = self.manager.delete_group(group_id)
            if success:
                QMessageBox.information(self, "تم", "تم حذف المجموعة.")
                self.load_groups()
                self.clear_form()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في حذف المجموعة.")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "حفظ الملف", "", "CSV Files (*.csv)")
        if not path:
            return

        try:
            with open(path, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(["الكود", "الاسم", "الفئة", "الوصف", "معرّف"])
                for row in range(self.table.rowCount()):
                    row_data = [self.table.item(row, col).text() for col in range(self.table.columnCount())]
                    writer.writerow(row_data)

            QMessageBox.information(self, "تم", "تم تصدير البيانات بنجاح.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تصدير الملف: {str(e)}")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    db_path = "database/inventory.db"  # تأكد أن هذا المسار صحيح وموجود
    app = QApplication(sys.argv)
    window = ItemGroupsUI(db_path)
    window.show()
    sys.exit(app.exec_())
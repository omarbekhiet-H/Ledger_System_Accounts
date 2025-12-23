# ui/admin/NEWlookup_window.py

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QComboBox, QLineEdit,
                             QLabel, QMessageBox, QHeaderView, QSplitter, QGroupBox)
from PyQt5.QtCore import Qt

# إضافة المسار للوحدات المحلية
sys.path.append('..')

from database.manager.admin.NEWlookup_manager import NEWLookupManager

class LookupWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lookup_manager = NEWLookupManager()
        self.lookup_manager.init_table()  # تهيئة الجدول إذا لم يكن موجوداً
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("إدارة البيانات المرجعية")
        self.setGeometry(100, 100, 1000, 600)
        
        layout = QVBoxLayout()
        
        # قسم الفئات والقيم
        main_group = QGroupBox("إدارة البيانات المرجعية")
        main_layout = QVBoxLayout()
        
        # عناصر التحكم للإضافة
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("الفئة:"))
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("أدخل اسم الفئة")
        controls_layout.addWidget(self.category_input)
        
        controls_layout.addWidget(QLabel("الكود:"))
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("أدخل الكود")
        controls_layout.addWidget(self.code_input)
        
        controls_layout.addWidget(QLabel("القيمة (عربي):"))
        self.value_ar_input = QLineEdit()
        self.value_ar_input.setPlaceholderText("أدخل القيمة العربية")
        controls_layout.addWidget(self.value_ar_input)
        
        controls_layout.addWidget(QLabel("القيمة (إنجليزي):"))
        self.value_en_input = QLineEdit()
        self.value_en_input.setPlaceholderText("أدخل القيمة الإنجليزية")
        controls_layout.addWidget(self.value_en_input)
        
        add_btn = QPushButton("إضافة")
        add_btn.clicked.connect(self.add_lookup_value)
        controls_layout.addWidget(add_btn)
        
        main_layout.addLayout(controls_layout)
        
        # عناصر التحكم للبحث والتصفية
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("بحث:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث في القيم...")
        self.search_input.textChanged.connect(self.filter_data)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addWidget(QLabel("الفئة:"))
        self.category_filter = QComboBox()
        self.category_filter.currentTextChanged.connect(self.filter_data)
        filter_layout.addWidget(self.category_filter)
        
        filter_layout.addWidget(QLabel("الحالة:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["جميع", "نشط", "غير نشط"])
        self.status_filter.currentTextChanged.connect(self.filter_data)
        filter_layout.addWidget(self.status_filter)
        
        main_layout.addLayout(filter_layout)
        
        # جدول البيانات
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "الفئة", "الكود", "القيمة العربية", "القيمة الإنجليزية", "الحالة"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        main_layout.addWidget(self.table)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        
        edit_btn = QPushButton("تعديل")
        edit_btn.clicked.connect(self.edit_lookup_value)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("حذف")
        delete_btn.clicked.connect(self.delete_lookup_value)
        button_layout.addWidget(delete_btn)
        
        toggle_btn = QPushButton("تفعيل/تعطيل")
        toggle_btn.clicked.connect(self.toggle_lookup_value)
        button_layout.addWidget(toggle_btn)
        
        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self.load_data)
        button_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(button_layout)
        main_group.setLayout(main_layout)
        
        layout.addWidget(main_group)
        self.setLayout(layout)
        
        # تحميل البيانات الأولية
        self.load_data()
    
    def load_data(self):
        """تحميل البيانات الأولية"""
        self.load_categories()
        self.load_lookup_values()
    
    def load_categories(self):
        """تحميل قائمة الفئات"""
        # جلب جميع القيم لاستخراج الفئات الفريدة
        all_values = self.lookup_manager.get_all(only_active=False)
        categories = set()
        
        for value in all_values:
            categories.add(value['category'])
        
        self.category_filter.clear()
        self.category_filter.addItem("جميع الفئات")
        
        for category in sorted(categories):
            self.category_filter.addItem(category)
    
    def load_lookup_values(self):
        """تحميل القيم المرجعية"""
        # جلب جميع القيم (سيتم تصفيتها لاحقاً)
        self.all_values = self.lookup_manager.get_all(only_active=False)
        self.filter_data()
    
    def filter_data(self):
        """تصفية البيانات المعروضة"""
        search_text = self.search_input.text().lower()
        selected_category = self.category_filter.currentText()
        selected_status = self.status_filter.currentText()
        
        filtered_values = []
        
        for value in self.all_values:
            # التصفية حسب البحث
            matches_search = (search_text in value['category'].lower() or 
                             search_text in value['code'].lower() or 
                             search_text in value['value_ar'].lower() or 
                             (value['value_en'] and search_text in value['value_en'].lower()))
            
            if search_text and not matches_search:
                continue
            
            # التصفية حسب الفئة
            if selected_category != "جميع الفئات" and value['category'] != selected_category:
                continue
            
            # التصفية حسب الحالة
            if selected_status == "نشط" and not value['is_active']:
                continue
            if selected_status == "غير نشط" and value['is_active']:
                continue
            
            filtered_values.append(value)
        
        # عرض البيانات في الجدول
        self.table.setRowCount(len(filtered_values))
        
        for row, value in enumerate(filtered_values):
            self.table.setItem(row, 0, QTableWidgetItem(str(value['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(value['category']))
            self.table.setItem(row, 2, QTableWidgetItem(value['code']))
            self.table.setItem(row, 3, QTableWidgetItem(value['value_ar']))
            self.table.setItem(row, 4, QTableWidgetItem(value['value_en'] or ''))
            self.table.setItem(row, 5, QTableWidgetItem("نشط" if value['is_active'] else "غير نشط"))
    
    def add_lookup_value(self):
        """إضافة قيمة مرجعية جديدة"""
        category = self.category_input.text().strip()
        code = self.code_input.text().strip()
        value_ar = self.value_ar_input.text().strip()
        value_en = self.value_en_input.text().strip() or None
        
        if not all([category, code, value_ar]):
            QMessageBox.warning(self, "تحذير", "يجب إدخال الفئة والكود والقيمة العربية")
            return
        
        success, message = self.lookup_manager.add(category, code, value_ar, value_en)
        
        if success:
            QMessageBox.information(self, "نجاح", message)
            # مسح الحقول
            self.category_input.clear()
            self.code_input.clear()
            self.value_ar_input.clear()
            self.value_en_input.clear()
            # إعادة تحميل البيانات
            self.load_data()
        else:
            QMessageBox.critical(self, "خطأ", message)
    
    def edit_lookup_value(self):
        """تعديل قيمة مرجعية"""
        current_row = self.table.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "تحذير", "يجب اختيار قيمة للتعديل")
            return
        
        value_id = int(self.table.item(current_row, 0).text())
        
        # فتح نافذة التعديل (يمكن تطويرها لاحقاً)
        from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("تعديل قيمة مرجعية")
        layout = QFormLayout()
        
        # الحصول على البيانات الحالية
        current_data = self.lookup_manager.get_by_id(value_id)
        if not current_data:
            QMessageBox.critical(self, "خطأ", "لم يتم العثور على القيمة")
            return
        
        # حقول التعديل
        category_edit = QLineEdit(current_data['category'])
        code_edit = QLineEdit(current_data['code'])
        value_ar_edit = QLineEdit(current_data['value_ar'])
        value_en_edit = QLineEdit(current_data['value_en'] or '')
        
        layout.addRow("الفئة:", category_edit)
        layout.addRow("الكود:", code_edit)
        layout.addRow("القيمة العربية:", value_ar_edit)
        layout.addRow("القيمة الإنجليزية:", value_en_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            updates = {
                'category': category_edit.text().strip(),
                'code': code_edit.text().strip(),
                'value_ar': value_ar_edit.text().strip(),
                'value_en': value_en_edit.text().strip() or None
            }
            
            success, message = self.lookup_manager.update(value_id, **updates)
            
            if success:
                QMessageBox.information(self, "نجاح", message)
                self.load_data()
            else:
                QMessageBox.critical(self, "خطأ", message)
    
    def delete_lookup_value(self):
        """حذف قيمة مرجعية"""
        current_row = self.table.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "تحذير", "يجب اختيار قيمة للحذف")
            return
        
        value_id = int(self.table.item(current_row, 0).text())
        value_name = self.table.item(current_row, 3).text()
        
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل تريد حذف القيمة '{value_name}'؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.lookup_manager.delete(value_id)
            
            if success:
                QMessageBox.information(self, "نجاح", message)
                self.load_data()
            else:
                QMessageBox.critical(self, "خطأ", message)
    
    def toggle_lookup_value(self):
        """تفعيل/تعطيل قيمة مرجعية"""
        current_row = self.table.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "تحذير", "يجب اختيار قيمة للتفعيل/التعطيل")
            return
        
        value_id = int(self.table.item(current_row, 0).text())
        value_name = self.table.item(current_row, 3).text()
        current_status = self.table.item(current_row, 5).text()
        
        new_status = "تعطيل" if current_status == "نشط" else "تفعيل"
        
        reply = QMessageBox.question(
            self, f"تأكيد {new_status}",
            f"هل تريد {new_status} القيمة '{value_name}'؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.lookup_manager.toggle_status(value_id)
            
            if success:
                QMessageBox.information(self, "نجاح", message)
                self.load_data()
            else:
                QMessageBox.critical(self, "خطأ", message)
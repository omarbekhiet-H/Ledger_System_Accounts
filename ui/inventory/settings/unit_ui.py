import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,QGroupBox,QGridLayout,QHeaderView,
    QHeaderView,QInputDialog,QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

# تصحيح مسار المشروع الجذر لتمكين الاستيراد الصحيح
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.inventory.setting.item_manager import ItemsManager
from database.manager.inventory.setting.item_categories_manager import ItemCategoryManager
from database.manager.inventory.setting.item_units_manager import ItemUnitManager


class UnitsUI(QWidget):
    def __init__(self, db_path: str):
        super().__init__()
        self.manager = ItemUnitManager(db_path)  # تغيير الاسم ليطابق المدير
        self.setup_ui()
        self.load_units()
        self.setWindowTitle("نظام إدارة الوحدات")
        self.setMinimumSize(1000, 600)
        self.setWindowIcon(QIcon("icons/units.png"))  # إضافة أيقونة إذا وجدت

    def load_categories(self):
        """تحميل الفئات من جدول الفئات وعرضها في واجهة الوحدات"""
        try:
            categories = self.category_manager.list_active_categories()
            self.category_combo.clear()
            for category in categories:
                self.category_combo.addItem(category["name_ar"], category["id"])  # يعرض الاسم العربي
            print("الفئات المحملة:", categories)  # لأغراض Debug
            # يمكنك استخدام هذه البيانات في الواجهة (مثل ComboBox)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل الفئات: {str(e)}")    

    def setup_ui(self):
        # الخط العام
        font = QFont('Arial', 12)
        self.setFont(font)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        self.setLayout(main_layout)

        # --- نموذج الإدخال ---
        form_group = QGroupBox("بيانات الوحدة")
        form_layout = QGridLayout()
        form_group.setLayout(form_layout)

        # حقول الإدخال
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("أدخل كود الوحدة (مثل: UNT-001)")
        self.name_ar_input = QLineEdit()
        self.name_ar_input.setPlaceholderText("أدخل الاسم العربي")
        self.name_en_input = QLineEdit()
        self.name_en_input.setPlaceholderText("أدخل الاسم الإنجليزي")

        form_layout.addWidget(QLabel("الكود (*):"), 0, 0)
        form_layout.addWidget(self.code_input, 0, 1)
        form_layout.addWidget(QLabel("الاسم العربي (*):"), 1, 0)
        form_layout.addWidget(self.name_ar_input, 1, 1)
        form_layout.addWidget(QLabel("الاسم الإنجليزي:"), 2, 0)
        form_layout.addWidget(self.name_en_input, 2, 1)

        main_layout.addWidget(form_group)

        # --- أزرار التحكم ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        buttons = [
            ("إضافة", self.add_unit, "#4CAF50", "icons/add.png"),
            ("تعديل", self.update_unit, "#2196F3", "icons/edit.png"),
            ("حذف", self.delete_unit, "#f44336", "icons/delete.png"),
            ("مسح", self.clear_form, "#607D8B", "icons/clear.png"),
            ("بحث", self.search_units, "#FF9800", "icons/search.png"),
            ("تحديث", self.load_units, "#9C27B0", "icons/refresh.png")
        ]

        for text, handler, color, icon in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color}; 
                    color: white; 
                    padding: 8px 12px;
                    border-radius: 4px;
                    min-width: 100px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                }}
                QPushButton:disabled {{
                    background-color: #cccccc;
                }}
            """)
            btn.setMinimumSize(120, 40)
            try:
                btn.setIcon(QIcon(icon))
            except:
                pass
            btn.clicked.connect(handler)
            button_layout.addWidget(btn)

        main_layout.addLayout(button_layout)

        # --- جدول العرض ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["الكود", "الاسم العربي", "الاسم الإنجليزي", "معرّف"])
        self.table.setColumnHidden(3, True)  # إخفاء عمود المعرف
        
        # تحسين عرض الجدول
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # الكود
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # الاسم العربي
        header.setSectionResizeMode(2, QHeaderView.Stretch)          # الاسم الإنجليزي
        
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.cellClicked.connect(self.on_row_selected)
        
        main_layout.addWidget(self.table)

    # إضافة حقل اختيار الفئة
        self.category_combo = QComboBox()
        self.category_combo.setPlaceholderText("اختر الفئة")
        form_layout.addWidget(QLabel("الفئة:"), 3, 0)
        form_layout.addWidget(self.category_combo, 3, 1)    

    def load_units(self):
        """تحميل الوحدات وعرضها في الجدول"""
        self.table.setRowCount(0)
        try:
            units = self.manager.list_active_units()
            
            for row_idx, unit in enumerate(units):
                self.table.insertRow(row_idx)
                
                # إضافة البيانات مع محاذاة للنص العربي
                code_item = QTableWidgetItem(unit["code"])
                code_item.setTextAlignment(Qt.AlignCenter)
                
                name_ar_item = QTableWidgetItem(unit["name_ar"])
                name_ar_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                name_en_item = QTableWidgetItem(unit.get("name_en", ""))
                name_en_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                
                id_item = QTableWidgetItem(str(unit["id"]))
                id_item.setTextAlignment(Qt.AlignCenter)
                
                self.table.setItem(row_idx, 0, code_item)
                self.table.setItem(row_idx, 1, name_ar_item)
                self.table.setItem(row_idx, 2, name_en_item)
                self.table.setItem(row_idx, 3, id_item)
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل البيانات: {str(e)}")

    def search_units(self):
        """بحث الوحدات حسب الاسم أو الكود"""
        search_text, ok = QInputDialog.getText(
            self, 
            "بحث عن وحدات", 
            "أدخل نص البحث (اسم أو كود):"
        )
        
        if ok and search_text:
            self.table.setRowCount(0)
            units = self.manager.search_units(search_text)
            
            for row_idx, unit in enumerate(units):
                self.table.insertRow(row_idx)
                self.table.setItem(row_idx, 0, QTableWidgetItem(unit["code"]))
                self.table.setItem(row_idx, 1, QTableWidgetItem(unit["name_ar"]))
                self.table.setItem(row_idx, 2, QTableWidgetItem(unit.get("name_en", "")))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(unit["id"])))

    def on_row_selected(self, row: int, _):
        """عند اختيار صف من الجدول"""
        if row < 0:
            return

        # ملء الحقول بالبيانات المحددة
        self.code_input.setText(self.table.item(row, 0).text())
        self.name_ar_input.setText(self.table.item(row, 1).text())
        self.name_en_input.setText(self.table.item(row, 2).text())

    def clear_form(self):
        """مسح جميع حقول الإدخال"""
        self.code_input.clear()
        self.name_ar_input.clear()
        self.name_en_input.clear()
        self.table.clearSelection()

    def validate_inputs(self) -> bool:
        """التحقق من صحة البيانات المدخلة"""
        errors = []
        
        if not self.code_input.text().strip():
            errors.append("يجب إدخال كود الوحدة")
        
        if not self.name_ar_input.text().strip():
            errors.append("يجب إدخال الاسم العربي للوحدة")
            
        if errors:
            QMessageBox.warning(self, "تنبيه", "\n".join(errors))
            return False
            
        return True

    def add_unit(self):
        """إضافة وحدة جديدة"""
        if not self.validate_inputs():
            return

        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()
        category_id = self.category_combo.currentData()  # الحصول على ID الفئة المحددة

        if self.manager.unit_exists(code):
            QMessageBox.warning(self, "تحذير", "كود الوحدة موجود مسبقاً")
            return

        if self.manager.create_unit(code, name_ar, name_en, category_id):  # تأكد أن الدالة تدخل categor
            QMessageBox.information(self, "تم", "تمت إضافة الوحدة بنجاح")
            self.load_units()
            self.clear_form()
        else:
            QMessageBox.critical(self, "خطأ", "فشل في إضافة الوحدة. قد يكون الكود مكرراً")

    def update_unit(self):
        """تعديل الوحدة المحددة"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار وحدة من الجدول للتعديل")
            return

        if not self.validate_inputs():
            return

        unit_id = int(self.table.item(selected_row, 3).text())
        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()

        if self.manager.unit_exists(code, exclude_id=unit_id):
            QMessageBox.warning(self, "تحذير", "كود الوحدة موجود مسبقاً لوحدة أخرى")
            return

        if self.manager.update_unit(unit_id, code, name_ar, name_en):
            QMessageBox.information(self, "تم", "تم تعديل الوحدة بنجاح")
            self.load_units()
            self.clear_form()
        else:
            QMessageBox.critical(self, "خطأ", "فشل في تعديل الوحدة. قد يكون الكود مكرراً")

    def delete_unit(self):
        """حذف الوحدة المحددة"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار وحدة من الجدول للحذف")
            return

        unit_id = int(self.table.item(selected_row, 3).text())
        confirm = QMessageBox.question(
            self, 
            "تأكيد الحذف", 
            "هل أنت متأكد من حذف هذه الوحدة؟\nهذا الإجراء لا يمكن التراجع عنه.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            if self.manager.delete_unit(unit_id):
                QMessageBox.information(self, "تم", "تم حذف الوحدة بنجاح")
                self.load_units()
                self.clear_form()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في حذف الوحدة")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    #window = UnitsUI("path/to/your/database.db")  # استبدل بمسار قاعدة البيانات الفعلي
    window = UnitsUI("database/inventory.db")  # أو المسار الصحيح لقاعدة البيانات

    window.show()
    sys.exit(app.exec_())
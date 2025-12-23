import sqlite3
import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDateEdit, QComboBox, QGroupBox, QGridLayout, QSizePolicy,
    QAbstractItemView, QApplication, QStyle
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QIcon

# =====================================================================
# تصحيح مسار المشروع الجذر لتمكين الاستيراد الصحيح
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import necessary managers
from database.manager.financial_lookups_manager import FinancialLookupsManager
from database.db_connection import get_financials_db_connection

# سيتم تهيئة مخطط قاعدة البيانات مباشرةً باستخدام FINANCIALS_SCHEMA_SCRIPT
from database.schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT

# =====================================================================
# Helper function to load QSS files
# =====================================================================
def load_qss_file(file_path):
    """Loads a QSS file and returns its content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: QSS file not found at {file_path}")
        return None
    except Exception as e:
        print(f"ERROR: Could not load QSS file {file_path}: {e}")
        return None


class CostCentersManagementWindow(QWidget):
    def __init__(self, lookup_manager=None):
        super().__init__()
        self.lookup_manager = lookup_manager if lookup_manager else FinancialLookupsManager(get_financials_db_connection)
        self.current_cost_center_id = None

        self.setWindowTitle("إدارة مراكز التكلفة")
        self.setLayoutDirection(Qt.RightToLeft)
        QApplication.instance().setLayoutDirection(Qt.RightToLeft) # Apply RTL to the whole application
        self.init_ui()
        self.load_cost_centers()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("إدارة مراكز التكلفة")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        # تم إزالة: title_label.setStyleSheet("color: #333;") ليتم التحكم بها من QSS الخارجي
        main_layout.addWidget(title_label)

        form_group_box = QGroupBox("بيانات مركز التكلفة")
        form_layout = QGridLayout(form_group_box)
        form_group_box.setLayoutDirection(Qt.RightToLeft)

        self.code_input = QLineEdit()
        self.name_ar_input = QLineEdit()
        self.name_en_input = QLineEdit()
        self.description_input = QLineEdit()
        self.parent_cost_center_combo = QComboBox()
        self.parent_cost_center_combo.addItem("اختر مركز تكلفة أب", None)

        self.is_active_combo = QComboBox()
        self.is_active_combo.addItem("نشط", 1)
        self.is_active_combo.addItem("غير نشط", 0)

        # أول ثلاثة حقول في سطر واحد (السطر 0)
        form_layout.addWidget(QLabel("الكود:"), 0, 0) # تسمية الكود في العمود 0 من السطر 0
        form_layout.addWidget(self.code_input, 0, 1) # حقل الكود في العمود 1 من السطر 0

        form_layout.addWidget(QLabel("الاسم (عربي):"), 0, 2) # تسمية الاسم العربي في العمود 2 من السطر 0
        form_layout.addWidget(self.name_ar_input, 0, 3) # حقل الاسم العربي في العمود 3 من السطر 0

        form_layout.addWidget(QLabel("الاسم (إنجليزي):"), 0, 4) # تسمية الاسم الإنجليزي في العمود 4 من السطر 0
        form_layout.addWidget(self.name_en_input, 0, 5) # حقل الاسم الإنجليزي في العمود 5 من السطر 0

        # باقي الحقول في سطر واحد (السطر 1)
        form_layout.addWidget(QLabel("الوصف:"), 1, 0) # تسمية الوصف في العمود 0 من السطر 1
        form_layout.addWidget(self.description_input, 1, 1) # حقل الوصف في العمود 1 من السطر 1

        form_layout.addWidget(QLabel("المركز الأب:"), 1, 2) # تسمية المركز الأب في العمود 2 من السطر 1
        form_layout.addWidget(self.parent_cost_center_combo, 1, 3) # حقل المركز الأب في العمود 3 من السطر 1

        form_layout.addWidget(QLabel("الحالة:"), 1, 4) # تسمية الحالة في العمود 4 من السطر 1
        form_layout.addWidget(self.is_active_combo, 1, 5) # حقل الحالة في العمود 5 من السطر 1

        main_layout.addWidget(form_group_box)

        buttons_layout = QHBoxLayout()

        self.add_btn = QPushButton("إضافة")
        self.add_btn.setObjectName("addButton")
        self.add_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton)) # تم التعديل
        buttons_layout.addWidget(self.add_btn)

        self.update_btn = QPushButton("تحديث")
        self.update_btn.setObjectName("updateButton")
        self.update_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton)) # تم التعديل
        buttons_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("حذف / تعطيل")
        self.delete_btn.setObjectName("deleteButton")
        self.delete_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton)) # تم التعديل
        buttons_layout.addWidget(self.delete_btn)

        self.clear_btn = QPushButton("مسح")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload)) # تم التعديل
        buttons_layout.addWidget(self.clear_btn)

        main_layout.addLayout(buttons_layout)

        self.cost_centers_table = QTableWidget()
        self.cost_centers_table.setColumnCount(7)
        self.cost_centers_table.setHorizontalHeaderLabels([
            "المعرف", "الكود", "الاسم (عربي)", "الاسم (إنجليزي)", "الوصف", "المركز الأب", "الحالة"
        ])
        self.cost_centers_table.setColumnHidden(0, True) # تم التأكد من إخفاء عمود المعرف
        self.cost_centers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.cost_centers_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # كود
        self.cost_centers_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # الاسم العربي
        self.cost_centers_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch) # الاسم الإنجليزي
        self.cost_centers_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch) # الوصف
        self.cost_centers_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # المركز الأب
        self.cost_centers_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents) # الحالة


        self.cost_centers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cost_centers_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        main_layout.addWidget(self.cost_centers_table)

        self.add_btn.clicked.connect(self.add_cost_center)
        self.update_btn.clicked.connect(self.update_cost_center)
        self.delete_btn.clicked.connect(self.delete_cost_center)
        self.clear_btn.clicked.connect(self.clear_form)
        self.cost_centers_table.itemSelectionChanged.connect(self.display_selected_cost_center)

        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.populate_parent_cost_centers_combo()

    def populate_parent_cost_centers_combo(self):
        self.parent_cost_center_combo.clear()
        self.parent_cost_center_combo.addItem("اختر مركز تكلفة أب", None)

        all_cost_centers = self.lookup_manager.get_all_cost_centers()
        if all_cost_centers:
            for cc in all_cost_centers:
                if self.current_cost_center_id is None or cc['id'] != self.current_cost_center_id:
                    self.parent_cost_center_combo.addItem(cc['name_ar'], cc['id'])

    def load_cost_centers(self):
        self.cost_centers_table.setRowCount(0)

        cost_centers = self.lookup_manager.get_all_cost_centers()
        if cost_centers:
            for i, cc in enumerate(cost_centers):
                self.cost_centers_table.insertRow(i)
                self.cost_centers_table.setItem(i, 0, QTableWidgetItem(str(cc['id'])))
                self.cost_centers_table.setItem(i, 1, QTableWidgetItem(cc['code']))
                self.cost_centers_table.setItem(i, 2, QTableWidgetItem(cc['name_ar']))
                self.cost_centers_table.setItem(i, 3, QTableWidgetItem(cc['name_en'] if cc['name_en'] else ""))
                self.cost_centers_table.setItem(i, 4, QTableWidgetItem(cc['description'] if cc['description'] else ""))

                parent_name = ""
                parent_id = cc['parent_cost_center_id']
                if parent_id:
                    parent_cc = self.lookup_manager.get_cost_center_by_id(parent_id)
                    if parent_cc:
                        parent_name = parent_cc['name_ar']
                self.cost_centers_table.setItem(i, 5, QTableWidgetItem(parent_name))
                self.cost_centers_table.setItem(i, 6, QTableWidgetItem("نشط" if cc['is_active'] == 1 else "غير نشط"))
        self.clear_form()

    def add_cost_center(self):
        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()
        description = self.description_input.text().strip()
        parent_id = self.parent_cost_center_combo.currentData()
        is_active = self.is_active_combo.currentData()

        if not code or not name_ar:
            QMessageBox.warning(self, "بيانات ناقصة", "الكود والاسم العربي مطلوبان.")
            return

        success = self.lookup_manager.add_cost_center(
            code=code,
            name_ar=name_ar,
            name_en=name_en if name_en else None,
            description=description if description else None,
            parent_id=parent_id,
            is_active=is_active
        )

        if success:
            QMessageBox.information(self, "نجاح", "تمت إضافة مركز التكلفة بنجاح.")
            self.load_cost_centers()
        else:
            QMessageBox.critical(self, "خطأ", "فشل إضافة مركز التكلفة. قد يكون الكود موجوداً بالفعل.")

    def update_cost_center(self):
        if self.current_cost_center_id is None:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد مركز تكلفة لتعديله.")
            return

        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        name_en = self.name_en_input.text().strip()
        description = self.description_input.text().strip()
        parent_id = self.parent_cost_center_combo.currentData()
        is_active = self.is_active_combo.currentData()

        if not code or not name_ar:
            QMessageBox.warning(self, "بيانات ناقصة", "الكود والاسم العربي مطلوبان.")
            return

        if parent_id == self.current_cost_center_id:
            QMessageBox.warning(self, "خطأ في المركز الأب", "لا يمكن أن يكون مركز التكلفة الأب هو نفسه مركز التكلفة الحالي.")
            return

        data = {
            'code': code,
            'name_ar': name_ar,
            'name_en': name_en if name_en else None,
            'description': description if description else None,
            'parent_cost_center_id': parent_id,
            'is_active': is_active
        }

        success = self.lookup_manager.update_cost_center(self.current_cost_center_id, data)

        if success:
            QMessageBox.information(self, "نجاح", "تم تحديث مركز التكلفة بنجاح.")
            self.load_cost_centers()
        else:
            QMessageBox.critical(self, "خطأ", "فشل تحديث مركز التكلفة. قد يكون الكود موجوداً بالفعل أو لا يوجد تغيير.")

    def delete_cost_center(self):
        if self.current_cost_center_id is None:
            QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد مركز تكلفة لحذفه/تعطيله.")
            return

        selected_row = self.cost_centers_table.currentRow()
        if selected_row >= 0:
            cost_center_name = self.cost_centers_table.item(selected_row, 2).text()

            reply = QMessageBox.question(self, "تأكيد الحذف/التعطيل",
                                         f"هل أنت متأكد أنك تريد حذف/تعطيل مركز التكلفة '{cost_center_name}'؟\n(سيتم تعطيل مركز التكلفة بدلاً من حذفه فعلياً)",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                success = self.lookup_manager.deactivate_cost_center(self.current_cost_center_id)
                if success:
                    QMessageBox.information(self, "نجاح", "تم تعطيل مركز التكلفة بنجاح.")
                    self.load_cost_centers()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل تعطيل مركز التكلفة.")

    def display_selected_cost_center(self):
        selected_row = self.cost_centers_table.currentRow()
        if selected_row >= 0:
            self.current_cost_center_id = int(self.cost_centers_table.item(selected_row, 0).text())
            cost_center = self.lookup_manager.get_cost_center_by_id(self.current_cost_center_id)
            if cost_center:
                self.code_input.setText(cost_center['code'])
                self.name_ar_input.setText(cost_center['name_ar'])
                self.name_en_input.setText(cost_center['name_en'] if cost_center['name_en'] else "")
                self.description_input.setText(cost_center['description'] if cost_center['description'] else "")

                parent_id = cost_center['parent_cost_center_id']
                if parent_id is not None:
                    index = self.parent_cost_center_combo.findData(parent_id)
                    if index != -1:
                        self.parent_cost_center_combo.setCurrentIndex(index)
                    else:
                        self.parent_cost_center_combo.setCurrentIndex(0)
                else:
                    self.parent_cost_center_combo.setCurrentIndex(0)

                index_active = self.is_active_combo.findData(cost_center['is_active'])
                if index_active != -1:
                    self.is_active_combo.setCurrentIndex(index_active)

                self.add_btn.setEnabled(False)
                self.update_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)

                self.code_input.setReadOnly(True)
                self.code_input.setProperty("readOnly", True)
        else:
            self.clear_form()

    def clear_form(self):
        self.current_cost_center_id = None
        self.code_input.clear()
        self.name_ar_input.clear()
        self.name_en_input.clear()
        self.description_input.clear()
        self.parent_cost_center_combo.setCurrentIndex(0)
        self.is_active_combo.setCurrentIndex(0)
        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

        self.code_input.setReadOnly(False)
        self.code_input.setProperty("readOnly", False)

        self.cost_centers_table.blockSignals(True)
        self.cost_centers_table.clearSelection()
        self.cost_centers_table.blockSignals(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Database initialization
    try:
        conn = get_financials_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='currencies';")
                table_exists = cursor.fetchone()

                if not table_exists:
                    print("Financials DB schema not found. Initializing...")
                    cursor.executescript(FINANCIALS_SCHEMA_SCRIPT)
                    conn.commit()
                    print("Financials DB schema initialized.")
                else:
                    print("Financials DB already exists and schema is present. Skipping initialization.")
            except sqlite3.Error as e:
                QMessageBox.critical(None, "خطأ في قاعدة البيانات", f"فشل التحقق أو تهيئة المخطط: {e}")
                sys.exit(1)
            finally:
                conn.close()
        else:
            QMessageBox.critical(None, "خطأ في الاتصال", "فشل الاتصال بقاعدة البيانات المالية.")
            sys.exit(1)

    except Exception as e:
        QMessageBox.critical(None, "خطأ في تشغيل التطبيق", f"حدث خطأ غير متوقع أثناء تهيئة التطبيق: {e}")
        sys.exit(1)

    # Load and apply QSS stylesheet
    qss_file_path = os.path.join(project_root, 'ui', 'styles', 'styles.qss')
    app_stylesheet = load_qss_file(qss_file_path)
    if app_stylesheet:
        app.setStyleSheet(app_stylesheet)
        print("DEBUG: Applied DFD-001 stylesheet.")
    else:
        print("WARNING: Failed to load stylesheet. UI might not be consistent.")


    test_lookup_manager = FinancialLookupsManager(get_financials_db_connection)
    window = CostCentersManagementWindow(lookup_manager=test_lookup_manager)
    window.showMaximized() # تم التعديل
    sys.exit(app.exec_())
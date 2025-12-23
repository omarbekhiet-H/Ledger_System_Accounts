import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QMessageBox, QCompleter, QDateEdit, QFrame,
    QGroupBox, QTextEdit, QGridLayout, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer

# 🟢 إضافة مسار المشروع الجذري
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# ------------------------------------------------------------
# استيراد دوال اتصال قواعد البيانات
# ------------------------------------------------------------
from database.db_connection import get_manufacturing_db_connection, get_inventory_db_connection, get_financials_db_connection, get_users_db_connection

# ------------------------------------------------------------
# أدوات مساعدة - معدلة للتعامل مع كائنات الاتصال
# ------------------------------------------------------------
def fetch_all(connection_func, query, params=()):
    """دالة معدلة للتعامل مع كائنات الاتصال مباشرة"""
    try:
        # الحصول على كائن الاتصال من الدالة
        conn = connection_func()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, params)
        result = cur.fetchall()
        conn.close()
        return result
    except Exception as e:
        print(f"DB Error [{connection_func.__name__}]: {e}")
        return []

def execute_query(connection_func, query, params=()):
    """دالة لتنفيذ استعلامات التعديل (INSERT, UPDATE, DELETE)"""
    try:
        # الحصول على كائن الاتصال من الدالة
        conn = connection_func()
        cur = conn.cursor()
        cur.execute(query, params)
        lastrowid = cur.lastrowid
        conn.commit()
        conn.close()
        return lastrowid
    except Exception as e:
        print(f"DB Error [{connection_func.__name__}]: {e}")
        return None

def get_next_job_number():
    """الحصول على رقم الأمر التالي"""
    rows = fetch_all(get_manufacturing_db_connection, "SELECT MAX(id) as last_id FROM job_orders")
    last_id = rows[0]["last_id"] if rows and rows[0]["last_id"] else 0
    return f"JO-{last_id+1:04d}"

def get_table_columns(connection_func, table_name):
    """الحصول على أسماء أعمدة جدول معين"""
    try:
        conn = connection_func()
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cur.fetchall()]
        conn.close()
        return columns
    except Exception as e:
        print(f"Error getting columns for {table_name}: {e}")
        return []

# ------------------------------------------------------------
# صنف مخصص لـ QLineEdit للتنقل بـ Enter
# ------------------------------------------------------------
class EnterLineEdit(QLineEdit):
    enterPressed = pyqtSignal()
    tabPressed = pyqtSignal()
    
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.enterPressed.emit()
        elif event.key() == Qt.Key_Tab:
            self.tabPressed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

# ------------------------------------------------------------
# نافذة البحث عن أوامر التشغيل
# ------------------------------------------------------------
class SearchOrderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("بحث عن أوامر التشغيل")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        self.selected_order_id = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # عناصر البحث
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("كلمة البحث:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث برقم الأمر أو اسم العميل أو الوصف...")
        search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("🔍 بحث")
        self.search_btn.clicked.connect(self.search_orders)
        search_layout.addWidget(self.search_btn)

        layout.addLayout(search_layout)

        # جدول النتائج
        self.results_table = QTableWidget(0, 5)
        self.results_table.setHorizontalHeaderLabels(["رقم الأمر", "العميل", "التاريخ", "الحالة", "الإجمالي"])
        self.results_table.doubleClicked.connect(self.select_order)
        layout.addWidget(self.results_table)

        # أزرار
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        
    def search_orders(self):
        search_text = self.search_input.text().strip()
        if not search_text:
            QMessageBox.warning(self, "تحذير", "الرجاء إدخال كلمة للبحث")
            return

        try:
            query = """
                SELECT jo.id, jo.job_number, c.name_ar as customer, jo.request_date as order_date, 
                       jo.status, jo.estimated_cost as grand_total 
                FROM job_orders jo 
                LEFT JOIN customers c ON jo.customer_id = c.id 
                WHERE jo.job_number LIKE ? OR c.name_ar LIKE ? OR jo.job_description LIKE ?
                ORDER BY jo.request_date DESC
            """
            params = (f'%{search_text}%', f'%{search_text}%', f'%{search_text}%')
            results = fetch_all(get_manufacturing_db_connection, query, params)

            self.results_table.setRowCount(0)
            for row_data in results:
                row = self.results_table.rowCount()
                self.results_table.insertRow(row)
                self.results_table.setItem(row, 0, QTableWidgetItem(str(row_data['job_number'])))
                self.results_table.setItem(row, 1, QTableWidgetItem(str(row_data['customer'] or 'غير محدد')))
                self.results_table.setItem(row, 2, QTableWidgetItem(str(row_data['order_date'])))
                self.results_table.setItem(row, 3, QTableWidgetItem(str(row_data['status'])))
                self.results_table.setItem(row, 4, QTableWidgetItem(str(row_data['grand_total'] or '0.00')))

            if len(results) == 0:
                QMessageBox.information(self, "نتائج البحث", "لم يتم العثور على نتائج مطابقة")

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء البحث: {str(e)}")
    
    def select_order(self):
        current_row = self.results_table.currentRow()
        if current_row >= 0:
            order_number = self.results_table.item(current_row, 0).text()
            self.selected_order_id = order_number
            self.accept()

# ------------------------------------------------------------
# نافذة أوامر التشغيل
# ------------------------------------------------------------
class JobOrderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("نظام إدارة أوامر التشغيل - Job Order Planning")
        self.setMinimumSize(1400, 800)
        self.setLayoutDirection(Qt.RightToLeft)
        
        # إزالة خاصية transform من الـ StyleSheet لتجنب التحذيرات
        self.apply_styles()

        self.current_job_id = None
        self.init_ui()

    def apply_styles(self):
        """تطبيق التنسيقات البصرية - معدل بدون خاصية transform"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
                font-family: 'Segoe UI', 'Tahoma', 'Arial';
            }
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #333;
                padding: 5px;
            }
            QLineEdit, QDateEdit, QComboBox {
                font-size: 12px;
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: white;
                min-height: 25px;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus {
                border-color: #4CAF50;
                background-color: #f9fff9;
            }
            QPushButton {
                font-size: 12px;
                font-weight: bold;
                padding: 10px 15px;
                border: none;
                border-radius: 5px;
                min-width: 80px;
                min-height: 35px;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
            #save_btn {
                background-color: #4CAF50;
                color: white;
            }
            #update_btn {
                background-color: #2196F3;
                color: white;
            }
            #delete_btn {
                background-color: #f44336;
                color: white;
            }
            #search_btn {
                background-color: #FF9800;
                color: white;
            }
            #clear_btn {
                background-color: #607D8B;
                color: white;
            }
            #print_btn {
                background-color: #9C27B0;
                color: white;
            }
            .add_btn {
                background-color: #607D8B;
                color: white;
                font-size: 11px;
                padding: 6px 10px;
                min-height: 30px;
            }
            .remove_btn {
                background-color: #F44336;
                color: white;
                font-size: 11px;
                padding: 6px 10px;
                min-height: 30px;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
                font-size: 11px;
                selection-background-color: #e3f2fd;
                alternate-background-color: #f9f9f9;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #bbdefb;
                color: #000;
            }
            QHeaderView::section {
                background-color: #37474F;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
                font-size: 11px;
            }
            QTabWidget::pane {
                border: 2px solid #C2C7CB;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #E1E1E1;
                color: #333;
                padding: 8px 15px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #BDBDBD;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #BDBDBD;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #FAFAFA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
            }
        """)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # عنوان الشاشة
        title_label = QLabel("نظام إدارة أوامر التشغيل - Job Order Planning")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2E7D32;
                padding: 15px;
                background-color: #E8F5E9;
                border-radius: 10px;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(title_label)

        # مجموعة البيانات الأساسية
        basic_info_group = QGroupBox("البيانات الأساسية لأمر التشغيل")
        basic_layout = QGridLayout(basic_info_group)
        
        # الصف الأول من البيانات الأساسية
        basic_layout.addWidget(QLabel("رقم الأمر:"), 0, 0)
        self.job_number = QLineEdit(get_next_job_number())
        self.job_number.setReadOnly(True)
        self.job_number.setStyleSheet("background-color: #FFF3E0; font-weight: bold;")
        basic_layout.addWidget(self.job_number, 0, 1)

        basic_layout.addWidget(QLabel("العميل:"), 0, 2)
        self.customer = EnterLineEdit()
        self.customer.setPlaceholderText("اكتب كود أو اسم العميل...")
        self.setup_customer_autocomplete()
        self.customer.enterPressed.connect(lambda: self.focus_next_widget(self.customer))
        basic_layout.addWidget(self.customer, 0, 3)

        basic_layout.addWidget(QLabel("التاريخ:"), 0, 4)
        self.order_date = QDateEdit(QDate.currentDate())
        self.order_date.setCalendarPopup(True)
        self.order_date.setDisplayFormat("dd/MM/yyyy")
        basic_layout.addWidget(self.order_date, 0, 5)

        # وصف الأمر
        basic_layout.addWidget(QLabel("وصف الأمر:"), 1, 0)
        self.order_description = QTextEdit()
        self.order_description.setMaximumHeight(60)
        self.order_description.setPlaceholderText("أدخل وصفاً مفصلاً لأمر التشغيل...")
        basic_layout.addWidget(self.order_description, 1, 1, 1, 5)

        main_layout.addWidget(basic_info_group)

        # التبويبات
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: 2px solid #C2C7CB; }")

        # تبويب المواد
        materials_tab = QWidget()
        materials_layout = QVBoxLayout(materials_tab)
        
        materials_header = QLabel("إدارة المواد الخام والمستلزمات")
        materials_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #D32F2F; padding: 10px;")
        materials_layout.addWidget(materials_header)
        
        self.items_table = QTableWidget(0, 7)
        self.items_table.setHorizontalHeaderLabels(["كود المادة", "اسم المادة", "الوحدة", "الكمية", "سعر الوحدة", "الإجمالي", "ملاحظات"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # تحديد عرض الأعمدة
        self.items_table.setColumnWidth(0, 120)  # كود المادة
        self.items_table.setColumnWidth(1, 200)  # اسم المادة
        self.items_table.setColumnWidth(2, 80)   # الوحدة
        self.items_table.setColumnWidth(3, 100)  # الكمية
        self.items_table.setColumnWidth(4, 120)  # السعر
        self.items_table.setColumnWidth(5, 120)  # الإجمالي
        self.items_table.setColumnWidth(6, 150)  # ملاحظات
        materials_layout.addWidget(self.items_table)
        
        # أزرار المواد
        materials_buttons = QHBoxLayout()
        add_item_btn = QPushButton("➕ إضافة مادة جديدة")
        add_item_btn.setObjectName("add_btn")
        add_item_btn.clicked.connect(self.add_item_row)
        materials_buttons.addWidget(add_item_btn)

        remove_item_btn = QPushButton("🗑️ حذف المادة المحددة")
        remove_item_btn.setObjectName("remove_btn")
        remove_item_btn.clicked.connect(self.remove_item_row)
        materials_buttons.addWidget(remove_item_btn)

        materials_buttons.addStretch()
        materials_layout.addLayout(materials_buttons)
        
        self.tabs.addTab(materials_tab, "📦 المواد والمستلزمات")

        # تبويب العمالة
        labor_tab = QWidget()
        labor_layout = QVBoxLayout(labor_tab)
        
        labor_header = QLabel("إدارة العمالة والتكلفة البشرية")
        labor_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976D2; padding: 10px;")
        labor_layout.addWidget(labor_header)
        
        self.labor_table = QTableWidget(0, 6)
        self.labor_table.setHorizontalHeaderLabels(["كود الموظف", "اسم الموظف", "المسمى الوظيفي", "عدد الساعات", "أجر الساعة", "التكلفة الإجمالية"])
        self.labor_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.labor_table.setColumnWidth(0, 120)  # كود الموظف
        self.labor_table.setColumnWidth(1, 200)  # اسم الموظف
        self.labor_table.setColumnWidth(2, 150)  # المسمى الوظيفي
        self.labor_table.setColumnWidth(3, 100)  # الساعات
        self.labor_table.setColumnWidth(4, 120)  # أجر الساعة
        self.labor_table.setColumnWidth(5, 150)  # التكلفة
        labor_layout.addWidget(self.labor_table)
        
        # أزرار العمالة
        labor_buttons = QHBoxLayout()
        add_labor_btn = QPushButton("➕ إضافة عامل جديد")
        add_labor_btn.setObjectName("add_btn")
        add_labor_btn.clicked.connect(self.add_labor_row)
        labor_buttons.addWidget(add_labor_btn)

        remove_labor_btn = QPushButton("🗑️ حذف العامل المحدد")
        remove_labor_btn.setObjectName("remove_btn")
        remove_labor_btn.clicked.connect(self.remove_labor_row)
        labor_buttons.addWidget(remove_labor_btn)

        labor_buttons.addStretch()
        labor_layout.addLayout(labor_buttons)
        
        self.tabs.addTab(labor_tab, "👥 العمالة والتكلفة البشرية")

        # تبويب المصروفات
        costs_tab = QWidget()
        costs_layout = QVBoxLayout(costs_tab)
        
        costs_header = QLabel("إدارة المصروفات والتكاليف الإضافية")
        costs_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #7B1FA2; padding: 10px;")
        costs_layout.addWidget(costs_header)
        
        self.costs_table = QTableWidget(0, 5)
        self.costs_table.setHorizontalHeaderLabels(["كود الحساب", "اسم الحساب", "الوصف", "المبلغ", "العملة"])
        self.costs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.costs_table.setColumnWidth(0, 120)  # كود الحساب
        self.costs_table.setColumnWidth(1, 200)  # اسم الحساب
        self.costs_table.setColumnWidth(2, 200)  # الوصف
        self.costs_table.setColumnWidth(3, 150)  # المبلغ
        self.costs_table.setColumnWidth(4, 80)   # العملة
        costs_layout.addWidget(self.costs_table)
        
        # أزرار المصروفات
        costs_buttons = QHBoxLayout()
        add_cost_btn = QPushButton("➕ إضافة مصروف جديد")
        add_cost_btn.setObjectName("add_btn")
        add_cost_btn.clicked.connect(self.add_cost_row)
        costs_buttons.addWidget(add_cost_btn)

        remove_cost_btn = QPushButton("🗑️ حذف المصروف المحدد")
        remove_cost_btn.setObjectName("remove_btn")
        remove_cost_btn.clicked.connect(self.remove_cost_row)
        costs_buttons.addWidget(remove_cost_btn)

        costs_buttons.addStretch()
        costs_layout.addLayout(costs_buttons)
        
        self.tabs.addTab(costs_tab, "💰 المصروفات والتكاليف")

        main_layout.addWidget(self.tabs)

        # منطقة الإجمالي والأزرار
        footer_frame = QFrame()
        footer_frame.setFrameShape(QFrame.StyledPanel)
        footer_layout = QHBoxLayout(footer_frame)
        
        # الإجماليات
        totals_group = QGroupBox("الإجماليات")
        totals_layout = QGridLayout(totals_group)
        
        totals_layout.addWidget(QLabel("إجمالي المواد:"), 0, 0)
        self.materials_total = QLabel("0.00")
        self.materials_total.setStyleSheet("font-weight: bold; color: #D32F2F; font-size: 13px;")
        totals_layout.addWidget(self.materials_total, 0, 1)
        
        totals_layout.addWidget(QLabel("إجمالي العمالة:"), 0, 3)
        self.labor_total = QLabel("0.00")
        self.labor_total.setStyleSheet("font-weight: bold; color: #1976D2; font-size: 13px;")
        totals_layout.addWidget(self.labor_total, 0, 4)
        
        totals_layout.addWidget(QLabel("إجمالي المصروفات:"), 0, 5)
        self.costs_total = QLabel("0.00")
        self.costs_total.setStyleSheet("font-weight: bold; color: #7B1FA2; font-size: 13px;")
        totals_layout.addWidget(self.costs_total, 0, 6)
        
        totals_layout.addWidget(QLabel("الإجمالي الكلي:"), 0, 7)
        self.grand_total = QLabel("0.00")
        self.grand_total.setStyleSheet("font-weight: bold; color: #2E7D32; font-size: 16px; background-color: #E8F5E9; padding: 5px; border-radius: 3px;")
        totals_layout.addWidget(self.grand_total, 0, 8)
        
        footer_layout.addWidget(totals_group)
        footer_layout.addStretch()

        # أزرار التحكم
        buttons_layout = QVBoxLayout()
        
        self.save_btn = QPushButton("💾 حفظ الأمر")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.clicked.connect(self.save_order)
        buttons_layout.addWidget(self.save_btn)

        self.update_btn = QPushButton("✏️ تعديل الأمر")
        self.update_btn.setObjectName("update_btn")
        self.update_btn.clicked.connect(self.update_order)
        buttons_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("🗑️ حذف الأمر")
        self.delete_btn.setObjectName("delete_btn")
        self.delete_btn.clicked.connect(self.delete_order)
        buttons_layout.addWidget(self.delete_btn)

        self.search_btn = QPushButton("🔍 بحث عن أمر")
        self.search_btn.setObjectName("search_btn")
        self.search_btn.clicked.connect(self.search_order)
        buttons_layout.addWidget(self.search_btn)

        self.clear_btn = QPushButton("🗑️ مسح النموذج")
        self.clear_btn.setObjectName("clear_btn")
        self.clear_btn.clicked.connect(self.clear_form)
        buttons_layout.addWidget(self.clear_btn)

        self.print_btn = QPushButton("🖨️ طباعة الأمر")
        self.print_btn.setObjectName("print_btn")
        self.print_btn.clicked.connect(self.print_order)
        buttons_layout.addWidget(self.print_btn)

        footer_layout.addLayout(buttons_layout)
        main_layout.addWidget(footer_frame)

        # إضافة صفوف افتراضية
        QTimer.singleShot(100, self.add_initial_rows)

        # اختبار الاتصال بقواعد البيانات وفحص الهياكل
        self.test_database_connections_and_structures()

    def add_initial_rows(self):
        """إضافة صفوف افتراضية عند بدء التشغيل"""
        self.add_item_row()
        self.add_labor_row()
        self.add_cost_row()
        self.calculate_totals()

    def test_database_connections_and_structures(self):
        """اختبار الاتصال بجميع قواعد البيانات وفحص هياكل الجداول"""
        databases = [
            ("التصنيع", get_manufacturing_db_connection, "job_orders"),
            ("المخزون", get_inventory_db_connection, "customers"),
            ("المخزون", get_inventory_db_connection, "items"),
            ("المستخدمين", get_users_db_connection, "users"),
            ("المالية", get_financials_db_connection, "accounts")
        ]
        
        for db_name, db_func, table_name in databases:
            try:
                conn = db_func()
                cur = conn.cursor()
                
                # فحص وجود الجدول
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                table_exists = cur.fetchone() is not None
                
                if table_exists:
                    # فحص أعمدة الجدول
                    columns = get_table_columns(db_func, table_name)
                    print(f"✅ جدول {table_name} في {db_name}: {columns}")
                else:
                    print(f"❌ جدول {table_name} غير موجود في {db_name}")
                
                conn.close()
                
            except Exception as e:
                print(f"❌ خطأ في فحص جدول {table_name} في {db_name}: {e}")

    def focus_next_widget(self, current_widget):
        """الانتقال للعنصر التالي عند الضغط على Enter"""
        focus_widget = current_widget
        if hasattr(focus_widget, 'focusNextChild'):
            focus_widget.focusNextChild()
        else:
            # البحث عن العنصر التالي يدوياً
            all_widgets = self.findChildren((QLineEdit, QComboBox, QDateEdit, QTextEdit))
            try:
                current_index = all_widgets.index(focus_widget)
                next_index = (current_index + 1) % len(all_widgets)
                all_widgets[next_index].setFocus()
            except ValueError:
                pass

    # ------------------------------------------------
    # AutoComplete - معدلة بناءً على الهياكل الفعلية
    # ------------------------------------------------
    def setup_customer_autocomplete(self):
        try:
            rows = fetch_all(get_inventory_db_connection, "SELECT id, name_ar, customer_code FROM customers WHERE is_active=1")
            if rows:
                names = [f"{r['customer_code']} - {r['name_ar']}" for r in rows]
                completer = QCompleter(names)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)
                completer.setCompletionMode(QCompleter.PopupCompletion)
                self.customer.setCompleter(completer)
            else:
                print("⚠️ لا توجد بيانات عملاء متاحة للبحث التلقائي")
        except Exception as e:
            print(f"❌ خطأ في إعداد البحث التلقائي للعملاء: {e}")

    #def setup_item_autocomplete(self, editor):
    #    try:
    #        rows = fetch_all(get_inventory_db_connection, "SELECT id, item_code, item_name_ar FROM items WHERE is_active=1")
    #        codes = [f"{r['item_code']} - {r['item_name_ar']}" for r in rows] if rows else []
    #        completer = QCompleter(codes)
    #        completer.setCaseSensitivity(False)
    #        completer.setFilterMode(Qt.MatchContains)
    #        completer.setCompletionMode(QCompleter.PopupCompletion)
    #        editor.setCompleter(completer)
    #    except Exception as e:
    #        print(f"Error setting up item autocomplete: {e}")


    def setup_item_autocomplete(self, editor):
        """إعداد البحث التلقائي للأصناف بناءً على الهيكل الفعلي"""
        try:
            # فحص أعمدة جدول الأصناف أولاً
            item_columns = get_table_columns(get_inventory_db_connection, "items")
            print(f"أعمدة جدول الأصناف: {item_columns}")
            
            # بناء الاستعلام بناءً على الأعمدة المتاحة
            code_column = "item_code" if "item_code" in item_columns else "code" if "code" in item_columns else item_columns[0] if item_columns else "id"
            name_column = "item_name_ar" if "item_name_ar" in item_columns else "item_name" if "item_name" in item_columns else "name_ar" if "name_ar" in item_columns else "name" if "name" in item_columns else item_columns[1] if len(item_columns) > 1 else "name"
            unit_column = "unit_name" if "unit_name" in item_columns else "unit" if "unit" in item_columns else item_columns[2] if len(item_columns) > 2 else "unit"
            
            query = f"SELECT {code_column}, {name_column}, {unit_column} FROM items WHERE is_active=1"
            print(f"استعلام الأصناف: {query}")
            
            rows = fetch_all(get_inventory_db_connection, query)
            
            items_data = {}
            for r in rows:
                code = r[code_column] if code_column in r.keys() else 'غير معروف'
                name = r[name_column] if name_column in r.keys() else 'غير معروف'
                unit = r[unit_column] if unit_column in r.keys() else 'وحدة'
                
                display_text = f"{code} - {name}"
                items_data[display_text] = {'name': name, 'unit': unit}
            
            if items_data:
                completer = QCompleter(list(items_data.keys()))
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)
                completer.setCompletionMode(QCompleter.PopupCompletion)
                
                def on_completion(text):
                    if text in items_data:
                        for row in range(self.items_table.rowCount()):
                            if self.items_table.cellWidget(row, 0) == editor:
                                self.items_table.setItem(row, 1, QTableWidgetItem(items_data[text]['name']))
                                self.items_table.setItem(row, 2, QTableWidgetItem(items_data[text]['unit']))
                                break
                
                editor.textChanged.connect(lambda: QTimer.singleShot(300, lambda: on_completion(editor.text())))
                editor.setCompleter(completer)
                print(f"✅ تم إعداد البحث التلقائي للأصناف ({len(items_data)} صنف)")
            else:
                print("⚠️ لا توجد بيانات أصناف متاحة للبحث التلقائي")
                
        except Exception as e:
            print(f"❌ خطأ في إعداد البحث التلقائي للأصناف: {e}")

    def setup_user_autocomplete(self, editor):
        """إعداد البحث التلقائي للموظفين بناءً على الهيكل الفعلي"""
        try:
            # فحص أعمدة جدول المستخدمين أولاً
            user_columns = get_table_columns(get_users_db_connection, "users")
            print(f"أعمدة جدول المستخدمين: {user_columns}")
            
            # بناء الاستعلام بناءً على الأعمدة المتاحة
            code_column = "username" if "username" in user_columns else "user_code" if "user_code" in user_columns else user_columns[0] if user_columns else "id"
            name_column = "name_ar" if "name_ar" in user_columns else "full_name" if "full_name" in user_columns else "name" if "name" in user_columns else user_columns[1] if len(user_columns) > 1 else "name"
            title_column = "job_title" if "job_title" in user_columns else "role" if "role" in user_columns else user_columns[2] if len(user_columns) > 2 else "position"
            
            query = f"SELECT {code_column}, {name_column}, {title_column} FROM users WHERE is_active=1"
            print(f"استعلام المستخدمين: {query}")
            
            rows = fetch_all(get_users_db_connection, query)
            
            users_data = {}
            for r in rows:
                username = r[code_column] if code_column in r.keys() else 'غير معروف'
                name = r[name_column] if name_column in r.keys() else 'غير معروف'
                job_title = r[title_column] if title_column in r.keys() else 'موظف'
                
                display_text = f"{username} - {name}"
                users_data[display_text] = {'name': name, 'job_title': job_title}
            
            if users_data:
                completer = QCompleter(list(users_data.keys()))
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)
                completer.setCompletionMode(QCompleter.PopupCompletion)
                
                def on_completion(text):
                    if text in users_data:
                        for row in range(self.labor_table.rowCount()):
                            if self.labor_table.cellWidget(row, 0) == editor:
                                self.labor_table.setItem(row, 1, QTableWidgetItem(users_data[text]['name']))
                                self.labor_table.setItem(row, 2, QTableWidgetItem(users_data[text]['job_title']))
                                break
                
                editor.textChanged.connect(lambda: QTimer.singleShot(300, lambda: on_completion(editor.text())))
                editor.setCompleter(completer)
                print(f"✅ تم إعداد البحث التلقائي للموظفين ({len(users_data)} موظف)")
            else:
                print("⚠️ لا توجد بيانات مستخدمين متاحة للبحث التلقائي")
                
        except Exception as e:
            print(f"❌ خطأ في إعداد البحث التلقائي للموظفين: {e}")

    def setup_account_autocomplete(self, editor):
        """إعداد البحث التلقائي للحسابات بناءً على الهيكل الفعلي"""
        try:
            # فحص أعمدة جدول الحسابات أولاً
            account_columns = get_table_columns(get_financials_db_connection, "accounts")
            print(f"أعمدة جدول الحسابات: {account_columns}")
            
            # بناء الاستعلام بناءً على الأعمدة المتاحة
            code_column = "acc_code" if "acc_code" in account_columns else "account_code" if "account_code" in account_columns else "code" if "code" in account_columns else account_columns[0] if account_columns else "id"
            name_column = "account_name_ar" if "account_name_ar" in account_columns else "account_name" if "account_name" in account_columns else "name_ar" if "name_ar" in account_columns else "name" if "name" in account_columns else account_columns[1] if len(account_columns) > 1 else "name"
            
            query = f"SELECT {code_column}, {name_column} FROM accounts WHERE is_active=1"
            print(f"استعلام الحسابات: {query}")
            
            rows = fetch_all(get_financials_db_connection, query)
            
            accounts_data = {}
            for r in rows:
                acc_code = r[code_column] if code_column in r.keys() else 'غير معروف'
                account_name = r[name_column] if name_column in r.keys() else 'غير معروف'
                
                display_text = f"{acc_code} - {account_name}"
                accounts_data[display_text] = {'name': account_name, 'currency': 'د.ع'}  # عملة افتراضية
            
            if accounts_data:
                completer = QCompleter(list(accounts_data.keys()))
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)
                completer.setCompletionMode(QCompleter.PopupCompletion)
                
                def on_completion(text):
                    if text in accounts_data:
                        for row in range(self.costs_table.rowCount()):
                            if self.costs_table.cellWidget(row, 0) == editor:
                                self.costs_table.setItem(row, 1, QTableWidgetItem(accounts_data[text]['name']))
                                self.costs_table.setItem(row, 4, QTableWidgetItem(accounts_data[text]['currency']))
                                break
                
                editor.textChanged.connect(lambda: QTimer.singleShot(300, lambda: on_completion(editor.text())))
                editor.setCompleter(completer)
                print(f"✅ تم إعداد البحث التلقائي للحسابات ({len(accounts_data)} حساب)")
            else:
                print("⚠️ لا توجد بيانات حسابات متاحة للبحث التلقائي")
                
        except Exception as e:
            print(f"❌ خطأ في إعداد البحث التلقائي للحسابات: {e}")

    # ------------------------------------------------
    # باقي الدوال تبقى كما هي بدون تغيير
    # (إدارة الصفوف، العمليات الحسابية، وظائف الأزرار)
    # ------------------------------------------------

    def add_item_row(self):
        """إضافة صف جديد لجدول المواد"""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        # خلية كود المادة (مع AutoComplete)
        code_editor = EnterLineEdit()
        code_editor.setPlaceholderText("اكتب كود المادة...")
        self.setup_item_autocomplete(code_editor)
        code_editor.enterPressed.connect(lambda: self.focus_next_table_cell(self.items_table, row, 1))
        self.items_table.setCellWidget(row, 0, code_editor)
        
        # الخلايا الأخرى
        for i in range(1, 7):
            item = QTableWidgetItem("")
            if i == 3:  # خلية الكمية
                item.setText("1")
            elif i == 4 or i == 5:  # خلايا السعر والإجمالي
                item.setText("0.00")
            self.items_table.setItem(row, i, item)
        
        # جعل خلية الكمية قابلة للتحرير
        qty_widget = EnterLineEdit("1")
        qty_widget.textChanged.connect(self.calculate_totals)
        qty_widget.enterPressed.connect(lambda: self.focus_next_table_cell(self.items_table, row, 4))
        self.items_table.setCellWidget(row, 3, qty_widget)
        
        # جعل خلية السعر قابلة للتحرير
        price_widget = EnterLineEdit("0.00")
        price_widget.textChanged.connect(self.calculate_totals)
        price_widget.enterPressed.connect(lambda: self.focus_next_table_cell(self.items_table, row, 6))
        self.items_table.setCellWidget(row, 4, price_widget)
        
        # خلية الملاحظات
        notes_widget = EnterLineEdit()
        notes_widget.enterPressed.connect(lambda: self.add_item_row() if row == self.items_table.rowCount()-1 else 
                                         self.focus_next_table_cell(self.items_table, row+1, 0))
        self.items_table.setCellWidget(row, 6, notes_widget)

    def remove_item_row(self):
        """حذف صف من جدول المواد"""
        row = self.items_table.currentRow()
        if row >= 0:
            self.items_table.removeRow(row)
            self.calculate_totals()

    def add_labor_row(self):
        """إضافة صف جديد لجدول العمالة"""
        row = self.labor_table.rowCount()
        self.labor_table.insertRow(row)
        
        # خلية كود الموظف (مع AutoComplete)
        code_editor = EnterLineEdit()
        code_editor.setPlaceholderText("اكتب كود الموظف...")
        self.setup_user_autocomplete(code_editor)
        code_editor.enterPressed.connect(lambda: self.focus_next_table_cell(self.labor_table, row, 3))
        self.labor_table.setCellWidget(row, 0, code_editor)
        
        # الخلايا الأخرى
        for i in range(1, 6):
            item = QTableWidgetItem("")
            if i == 3:  # خلية الساعات
                item.setText("8")
            elif i == 4 or i == 5:  # خلايا الأجر والتكلفة
                item.setText("0.00")
            self.labor_table.setItem(row, i, item)
        
        # جعل خلية الساعات قابلة للتحرير
        hours_widget = EnterLineEdit("8")
        hours_widget.textChanged.connect(self.calculate_totals)
        hours_widget.enterPressed.connect(lambda: self.focus_next_table_cell(self.labor_table, row, 4))
        self.labor_table.setCellWidget(row, 3, hours_widget)
        
        # جعل خلية الأجر قابلة للتحرير
        rate_widget = EnterLineEdit("0.00")
        rate_widget.textChanged.connect(self.calculate_totals)
        rate_widget.enterPressed.connect(lambda: self.focus_next_table_cell(self.labor_table, row, 5))
        self.labor_table.setCellWidget(row, 4, rate_widget)

    def remove_labor_row(self):
        """حذف صف من جدول العمالة"""
        row = self.labor_table.currentRow()
        if row >= 0:
            self.labor_table.removeRow(row)
            self.calculate_totals()

    def add_cost_row(self):
        """إضافة صف جديد لجدول المصروفات"""
        row = self.costs_table.rowCount()
        self.costs_table.insertRow(row)
        
        # خلية كود الحساب (مع AutoComplete)
        code_editor = EnterLineEdit()
        code_editor.setPlaceholderText("اكتب كود الحساب...")
        self.setup_account_autocomplete(code_editor)
        code_editor.enterPressed.connect(lambda: self.focus_next_table_cell(self.costs_table, row, 2))
        self.costs_table.setCellWidget(row, 0, code_editor)
        
        # الخلايا الأخرى
        for i in range(1, 5):
            item = QTableWidgetItem("")
            if i == 3:  # خلية المبلغ
                item.setText("0.00")
            self.costs_table.setItem(row, i, item)
        
        # جعل خلية المبلغ قابلة للتحرير
        amount_widget = EnterLineEdit("0.00")
        amount_widget.textChanged.connect(self.calculate_totals)
        amount_widget.enterPressed.connect(lambda: self.focus_next_table_cell(self.costs_table, row, 4))
        self.costs_table.setCellWidget(row, 3, amount_widget)

    def remove_cost_row(self):
        """حذف صف من جدول المصروفات"""
        row = self.costs_table.currentRow()
        if row >= 0:
            self.costs_table.removeRow(row)
            self.calculate_totals()

    def focus_next_table_cell(self, table, current_row, next_column):
        """الانتقال للخلية التالية في الجدول"""
        if next_column < table.columnCount():
            # إذا كانت الخلية تحتوي على widget
            widget = table.cellWidget(current_row, next_column)
            if widget:
                widget.setFocus()
                if isinstance(widget, QLineEdit):
                    widget.selectAll()
            else:
                # إذا كانت خلية عادية
                item = table.item(current_row, next_column)
                if item:
                    table.setCurrentItem(item)
        else:
            # إذا كنا في آخر عمود، ننتقل للصف التالي
            if current_row + 1 < table.rowCount():
                widget = table.cellWidget(current_row + 1, 0)
                if widget:
                    widget.setFocus()
                else:
                    table.setCurrentCell(current_row + 1, 0)
            else:
                # إذا كنا في آخر صف، نضيف صف جديد
                if table == self.items_table:
                    self.add_item_row()
                elif table == self.labor_table:
                    self.add_labor_row()
                elif table == self.costs_table:
                    self.add_cost_row()
                
                # التركيز على الصف الجديد
                QTimer.singleShot(100, lambda: self.focus_next_table_cell(table, current_row + 1, 0))

    def calculate_totals(self):
        """حساب الإجماليات"""
        try:
            # حساب إجمالي المواد
            materials_total = 0.0
            for row in range(self.items_table.rowCount()):
                qty_widget = self.items_table.cellWidget(row, 3)
                price_widget = self.items_table.cellWidget(row, 4)
                if qty_widget and price_widget:
                    try:
                        qty = float(qty_widget.text() or 0)
                        price = float(price_widget.text() or 0)
                        total = qty * price
                        materials_total += total
                        # تحديث خلية الإجمالي
                        total_item = self.items_table.item(row, 5)
                        if total_item:
                            total_item.setText(f"{total:.2f}")
                    except ValueError:
                        pass
            
            # حساب إجمالي العمالة
            labor_total = 0.0
            for row in range(self.labor_table.rowCount()):
                hours_widget = self.labor_table.cellWidget(row, 3)
                rate_widget = self.labor_table.cellWidget(row, 4)
                if hours_widget and rate_widget:
                    try:
                        hours = float(hours_widget.text() or 0)
                        rate = float(rate_widget.text() or 0)
                        total = hours * rate
                        labor_total += total
                        # تحديث خلية التكلفة
                        cost_item = self.labor_table.item(row, 5)
                        if cost_item:
                            cost_item.setText(f"{total:.2f}")
                    except ValueError:
                        pass
            
            # حساب إجمالي المصروفات
            costs_total = 0.0
            for row in range(self.costs_table.rowCount()):
                amount_widget = self.costs_table.cellWidget(row, 3)
                if amount_widget:
                    try:
                        amount = float(amount_widget.text() or 0)
                        costs_total += amount
                    except ValueError:
                        pass
            
            # تحديث العرض
            self.materials_total.setText(f"{materials_total:,.2f}")
            self.labor_total.setText(f"{labor_total:,.2f}")
            self.costs_total.setText(f"{costs_total:,.2f}")
            grand_total = materials_total + labor_total + costs_total
            self.grand_total.setText(f"{grand_total:,.2f}")
            
        except Exception as e:
            print(f"Error calculating totals: {e}")

    # ------------------------------------------------
    # وظائف الأزرار الرئيسية - مفعلة بالكامل
    # ------------------------------------------------
    def save_order(self):
        """حفظ أمر التشغيل الجديد - متوافق مع الهيكل الفعلي"""
        try:
            job_num = self.job_number.text().strip()
            cust = self.customer.text().strip()
            date = self.order_date.date().toString("yyyy-MM-dd")
            description = self.order_description.toPlainText().strip()

            if not cust:
                QMessageBox.warning(self, "خطأ", "الرجاء اختيار العميل")
                self.customer.setFocus()
                return

            # حساب الإجماليات
            materials_total = float(self.materials_total.text().replace(',', '') or 0)
            labor_total = float(self.labor_total.text().replace(',', '') or 0)
            costs_total = float(self.costs_total.text().replace(',', '') or 0)
            grand_total = materials_total + labor_total + costs_total

            # استخراج معرف العميل من النص
            customer_id = self.extract_customer_id(cust)

            # حفظ الأمر الأساسي (متوافق مع الهيكل الفعلي)
            last_id = execute_query(
                get_manufacturing_db_connection,
                """INSERT INTO job_orders (
                    job_number, job_title, job_description, job_type, priority, status,
                    customer_id, request_date, planned_start_date, planned_end_date,
                    estimated_cost, external_system
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    job_num,  # job_number
                    f"أمر تشغيل {job_num}",  # job_title
                    description,  # job_description
                    "تصنيع",  # job_type
                    "medium",  # priority
                    "planned",  # status
                    customer_id,  # customer_id
                    date,  # request_date
                    date,  # planned_start_date
                    self.calculate_end_date(date),  # planned_end_date
                    grand_total,  # estimated_cost
                    "job_order_planning_system"  # external_system
                )
            )

            if last_id is not None:
                self.current_job_id = last_id
            
                # حفظ التفاصيل في الجداول المرتبطة
                self.save_order_details(last_id)
            
                QMessageBox.information(self, "تم الحفظ", f"تم حفظ أمر التشغيل {job_num} بنجاح")
                # تحديث رقم الأمر التالي
                self.job_number.setText(get_next_job_number())
            else:
                QMessageBox.critical(self, "خطأ", "فشل في حفظ أمر التشغيل")

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحفظ: {str(e)}")
    def save_order_details(self, job_order_id):
        """حفظ تفاصيل أمر التشغيل في الجداول المرتبطة"""
        try:
            # حفظ المواد في جدول job_order_material_requirements
            for row in range(self.items_table.rowCount()):
                code_widget = self.items_table.cellWidget(row, 0)
                qty_widget = self.items_table.cellWidget(row, 3)
                price_widget = self.items_table.cellWidget(row, 4)
            
                if code_widget and qty_widget and price_widget:
                    item_code = code_widget.text().strip()
                    if item_code:
                        # البحث عن معرف المادة
                        item_rows = fetch_all(get_inventory_db_connection,
                                            "SELECT id FROM items WHERE item_code = ?", 
                                            (item_code.split(' - ')[0],))
                        if item_rows:
                            item_id = item_rows[0]['id']
                        
                            # البحث عن معرف الوحدة
                            unit_item = self.items_table.item(row, 2)
                            unit_id = self.get_unit_id(unit_item.text() if unit_item else "وحدة")
                        
                            execute_query(
                                get_manufacturing_db_connection,
                                """INSERT INTO job_order_material_requirements 
                                (job_order_id, item_id, quantity_required, unit_id, estimated_cost, status)
                                VALUES (?, ?, ?, ?, ?, ?)""",
                                (
                                    job_order_id,
                                    item_id,
                                    float(qty_widget.text() or 0),
                                    unit_id,
                                    float(price_widget.text() or 0) * float(qty_widget.text() or 0),
                                    "pending"
                                )
                            )

            # حفظ العمالة في جدول job_order_labor
            for row in range(self.labor_table.rowCount()):
                code_widget = self.labor_table.cellWidget(row, 0)
                hours_widget = self.labor_table.cellWidget(row, 3)
                rate_widget = self.labor_table.cellWidget(row, 4)
            
                if code_widget and hours_widget and rate_widget:
                    employee_code = code_widget.text().strip()
                    if employee_code:
                        execute_query(
                            get_manufacturing_db_connection,
                            """INSERT INTO job_order_labor 
                            (job_order_id, external_employee_id, role, assigned_hours, hourly_rate, labor_cost)
                            VALUES (?, ?, ?, ?, ?, ?)""",
                            (
                                job_order_id,
                                employee_code.split(' - ')[0],
                                self.labor_table.item(row, 2).text() if self.labor_table.item(row, 2) else "عامل",
                                float(hours_widget.text() or 0),
                                float(rate_widget.text() or 0),
                                float(hours_widget.text() or 0) * float(rate_widget.text() or 0)
                            )
                        )

            # حفظ المصروفات في جدول job_order_additional_costs
            for row in range(self.costs_table.rowCount()):
                code_widget = self.costs_table.cellWidget(row, 0)
                amount_widget = self.costs_table.cellWidget(row, 3)
            
                if code_widget and amount_widget:
                    account_code = code_widget.text().strip()
                    if account_code:
                        execute_query(
                            get_manufacturing_db_connection,
                            """INSERT INTO job_order_additional_costs 
                            (job_order_id, cost_type, cost_description, amount, currency)
                            VALUES (?, ?, ?, ?, ?)""",
                            (
                                job_order_id,
                                "مصروف إضافي",
                                self.costs_table.item(row, 2).text() if self.costs_table.item(row, 2) else "مصروف",
                                float(amount_widget.text() or 0),
                                "د.ع"
                            )
                        )
                    
        except Exception as e:
            print(f"خطأ في حفظ التفاصيل: {e}")

    def get_unit_id(self, unit_name):
        """الحصول على معرف الوحدة من اسمها"""
        try:
            rows = fetch_all(get_inventory_db_connection,
                           "SELECT id FROM units WHERE name_ar = ? OR name_en = ?", 
                           (unit_name, unit_name))
            if rows:
                return rows[0]['id']
            return 1  # قيمة افتراضية
        except:
            return 1
    

    def extract_customer_id(self, customer_text):
        """استخراج معرف العميل من النص"""
        try:
            # إذا كان النص يحتوي على كود العميل (مثل: CUST-001 - اسم العميل)
            if ' - ' in customer_text:
                code_part = customer_text.split(' - ')[0]
                # البحث عن العميل في قاعدة البيانات باستخدام customer_code
                rows = fetch_all(get_inventory_db_connection,
                               "SELECT id FROM customers WHERE customer_code = ? OR name_ar LIKE ?", 
                               (code_part, f'%{customer_text}%'))
                if rows:
                    return rows[0]['id']
        
            # إذا لم يتم العثور، استخدام قيمة افتراضية
            return None
        except:
            return None

    def calculate_end_date(self, start_date):
        """حساب تاريخ الانتهاء المتوقع (تاريخ البداية + 7 أيام)"""
        from datetime import datetime, timedelta
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = start + timedelta(days=7)
        return end.strftime("%Y-%m-%d")
    
    def update_order(self):
        """تعديل أمر التشغيل المحدد - متوافق مع الهيكل الفعلي"""
        if not self.current_job_id:
            QMessageBox.warning(self, "تحذير", "لا يوجد أمر للتعديل. الرجاء البحث عن أمر أولاً.")
            return
    
        try:
            job_num = self.job_number.text().strip()
            cust = self.customer.text().strip()
            date = self.order_date.date().toString("yyyy-MM-dd")
            description = self.order_description.toPlainText().strip()

            if not cust:
                QMessageBox.warning(self, "خطأ", "الرجاء اختيار العميل")
                return

            # حساب الإجماليات
            materials_total = float(self.materials_total.text().replace(',', '') or 0)
            labor_total = float(self.labor_total.text().replace(',', '') or 0)
            costs_total = float(self.costs_total.text().replace(',', '') or 0)
            grand_total = materials_total + labor_total + costs_total

            # استخراج معرف العميل من النص
            customer_id = self.extract_customer_id(cust)

            # تحديث الأمر (متوافق مع الهيكل الفعلي)
            result = execute_query(
                get_manufacturing_db_connection,
                """UPDATE job_orders SET 
                    job_title=?, job_description=?, customer_id=?, request_date=?, 
                    planned_end_date=?, estimated_cost=?
                    WHERE id=?""",
                (
                    f"أمر تشغيل {job_num}",
                    description,
                    customer_id,
                    date,
                    self.calculate_end_date(date),
                    grand_total,
                    self.current_job_id
                )
            )

            if result is not None:
                # حذف التفاصيل القديمة وإعادة حفظها
                self.delete_order_details(self.current_job_id)
                self.save_order_details(self.current_job_id)
            
                QMessageBox.information(self, "تم التعديل", f"تم تعديل أمر التشغيل {job_num} بنجاح")
            else:
                QMessageBox.critical(self, "خطأ", "فشل في تعديل أمر التشغيل")

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء التعديل: {str(e)}")

    def delete_order_details(self, job_order_id):
        """حذف تفاصيل أمر التشغيل من الجداول المرتبطة"""
        tables_to_delete = [
            "job_order_material_requirements",
            "job_order_labor", 
            "job_order_additional_costs"
        ]
    
        for table in tables_to_delete:
            execute_query(get_manufacturing_db_connection,
                    f"DELETE FROM {table} WHERE job_order_id = ?",
                    (job_order_id,))
            
    def delete_order(self):
        """حذف أمر التشغيل المحدد"""
        if not self.current_job_id:
            QMessageBox.warning(self, "تحذير", "لا يوجد أمر للحذف. الرجاء البحث عن أمر أولاً.")
            return
    
        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                   "هل أنت متأكد من حذف هذا الأمر؟\nهذا الإجراء لا يمكن التراجع عنه.",
                                   QMessageBox.Yes | QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            try:
                # الحذف من الجداول المرتبطة أولاً (بسبب القيود المرجعية)
                tables_to_delete = [
                    "job_order_material_requirements",
                    "job_order_labor", 
                    "job_order_additional_costs"
                ]
            
                for table in tables_to_delete:
                    execute_query(get_manufacturing_db_connection,
                                f"DELETE FROM {table} WHERE job_order_id = ?",
                                (self.current_job_id,))
            
                # ثم حذف الأمر الرئيسي
                result = execute_query(
                    get_manufacturing_db_connection,
                    "DELETE FROM job_orders WHERE id = ?",
                    (self.current_job_id,)
                )
            
                if result is not None:
                    QMessageBox.information(self, "تم الحذف", "تم حذف الأمر بنجاح")
                    self.clear_form()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل في حذف الأمر")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف: {str(e)}")

    def search_order(self):
        """البحث عن أوامر التشغيل"""
        dialog = SearchOrderDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_order_id:
            self.load_order(dialog.selected_order_id)

    def load_order(self, order_number):
        """تحميل بيانات أمر التشغيل - متوافق مع الهيكل الفعلي"""
        try:
            rows = fetch_all(get_manufacturing_db_connection,
                           """SELECT jo.*, c.name_ar as customer_name, c.customer_code 
                           FROM job_orders jo 
                           LEFT JOIN customers c ON jo.customer_id = c.id 
                           WHERE jo.job_number = ?""", (order_number,))
        
            if rows:
                order_data = rows[0]
                self.current_job_id = order_data['id']
                self.job_number.setText(order_data['job_number'])
            
                # عرض اسم العميل
                customer_display = f"{order_data.get('customer_code', '')} - {order_data.get('customer_name', '')}" if order_data.get('customer_name') else "عميل غير محدد"
                self.customer.setText(customer_display)
            
                self.order_date.setDate(QDate.fromString(order_data['request_date'], "yyyy-MM-dd"))
                self.order_description.setPlainText(order_data['job_description'] or "")
            
                # تحميل التفاصيل من الجداول المرتبطة
                self.load_order_details(order_data['id'])
            
                QMessageBox.information(self, "تم التحميل", f"تم تحميل أمر التشغيل {order_number} بنجاح")
            else:
                QMessageBox.warning(self, "تحذير", "لم يتم العثور على الأمر المطلوب")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل البيانات: {str(e)}")

    def load_order_details(self, job_order_id):
        """تحميل تفاصيل أمر التشغيل من الجداول المرتبطة"""
        try:
            # تحميل المواد
            materials = fetch_all(get_manufacturing_db_connection,
                                """SELECT jomr.*, i.item_code, i.item_name_ar, u.name_ar as unit_name
                                FROM job_order_material_requirements jomr
                                LEFT JOIN items i ON jomr.item_id = i.id
                                LEFT JOIN units u ON jomr.unit_id = u.id
                                WHERE jomr.job_order_id = ?""", (job_order_id,))
        
            self.items_table.setRowCount(0)
            for material in materials:
                row = self.items_table.rowCount()
                self.items_table.insertRow(row)
            
                # كود المادة
                code_editor = EnterLineEdit(f"{material['item_code']} - {material['item_name_ar']}")
                self.setup_item_autocomplete(code_editor)
                self.items_table.setCellWidget(row, 0, code_editor)
            
                # اسم المادة
                self.items_table.setItem(row, 1, QTableWidgetItem(material['item_name_ar']))
                # الوحدة
                self.items_table.setItem(row, 2, QTableWidgetItem(material['unit_name']))
                # الكمية
                qty_widget = EnterLineEdit(str(material['quantity_required']))
                qty_widget.textChanged.connect(self.calculate_totals)
                self.items_table.setCellWidget(row, 3, qty_widget)
                # السعر
                unit_price = material['estimated_cost'] / material['quantity_required'] if material['quantity_required'] > 0 else 0
                price_widget = EnterLineEdit(f"{unit_price:.2f}")
                price_widget.textChanged.connect(self.calculate_totals)
                self.items_table.setCellWidget(row, 4, price_widget)
                # الإجمالي
                self.items_table.setItem(row, 5, QTableWidgetItem(f"{material['estimated_cost']:.2f}"))
                # ملاحظات
                self.items_table.setItem(row, 6, QTableWidgetItem(material.get('notes', '')))
        
            # تحميل العمالة (بنفس المنطق)
            labor = fetch_all(get_manufacturing_db_connection,
                             "SELECT * FROM job_order_labor WHERE job_order_id = ?", (job_order_id,))
        
            self.labor_table.setRowCount(0)

            for labor_data in labor:
                row = self.labor_table.rowCount()
                self.labor_table.insertRow(row)
            
                # كود الموظف
                code_editor = EnterLineEdit(labor_data.get('external_employee_id', ''))
                self.setup_user_autocomplete(code_editor)
                self.labor_table.setCellWidget(row, 0, code_editor)
            
                # اسم الموظف
                self.labor_table.setItem(row, 1, QTableWidgetItem(labor_data.get('role', '')))
                # المسمى الوظيفي
                self.labor_table.setItem(row, 2, QTableWidgetItem(labor_data.get('role', '')))
                # الساعات
                hours_widget = EnterLineEdit(str(labor_data.get('assigned_hours', 0)))
                hours_widget.textChanged.connect(self.calculate_totals)
                self.labor_table.setCellWidget(row, 3, hours_widget)
                # أجر الساعة
                rate_widget = EnterLineEdit(f"{labor_data.get('hourly_rate', 0):.2f}")
                rate_widget.textChanged.connect(self.calculate_totals)
                self.labor_table.setCellWidget(row, 4, rate_widget)
                # التكلفة
                self.labor_table.setItem(row, 5, QTableWidgetItem(f"{labor_data.get('labor_cost', 0):.2f}"))
    
            # تحميل المصروفات - مكتمل الآن
            costs = fetch_all(get_manufacturing_db_connection,
                         "SELECT * FROM job_order_additional_costs WHERE job_order_id = ?", (job_order_id,))
        
            self.costs_table.setRowCount(0)
            for cost_data in costs:
                row = self.costs_table.rowCount()
                self.costs_table.insertRow(row)
            
                # كود الحساب
                code_editor = EnterLineEdit(cost_data.get('cost_type', ''))
                self.setup_account_autocomplete(code_editor)
                self.costs_table.setCellWidget(row, 0, code_editor)
            
                # اسم الحساب
                self.costs_table.setItem(row, 1, QTableWidgetItem(cost_data.get('cost_type', '')))
                # الوصف
                self.costs_table.setItem(row, 2, QTableWidgetItem(cost_data.get('cost_description', '')))
                # المبلغ
                amount_widget = EnterLineEdit(f"{cost_data.get('amount', 0):.2f}")
                amount_widget.textChanged.connect(self.calculate_totals)
                self.costs_table.setCellWidget(row, 3, amount_widget)
                # العملة
                self.costs_table.setItem(row, 4, QTableWidgetItem(cost_data.get('currency', 'د.ع')))
        
            # حساب الإجماليات
            self.calculate_totals()
    
        except Exception as e:
            print(f"خطأ في تحميل التفاصيل: {e}")

    def clear_form(self):
        """مسح النموذج وإعادة تعيينه"""
        reply = QMessageBox.question(self, "تأكيد المسح", 
                                   "هل أنت متأكد من مسح جميع البيانات؟\nسيتم فقدان جميع البيانات غير المحفوظة.",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.current_job_id = None
            self.job_number.setText(get_next_job_number())
            self.customer.clear()
            self.order_date.setDate(QDate.currentDate())
            self.order_description.clear()
            
            # مسح الجداول
            self.items_table.setRowCount(0)
            self.labor_table.setRowCount(0)
            self.costs_table.setRowCount(0)
            
            # إضافة صفوف جديدة
            self.add_initial_rows()
            
            QMessageBox.information(self, "تم المسح", "تم مسح النموذج بنجاح")

    def print_order(self):
        """طباعة أمر التشغيل"""
        if not self.current_job_id:
            QMessageBox.warning(self, "تحذير", "لا يوجد أمر للطباعة. الرجاء حفظ أو تحميل أمر أولاً.")
            return
        
        try:
            # إنشاء محتوى التقرير
            job_num = self.job_number.text().strip()
            cust = self.customer.text().strip()
            date = self.order_date.date().toString("dd/MM/yyyy")
            description = self.order_description.toPlainText().strip()
            
            report_content = f"""
            تقرير أمر التشغيل
            =================
            
            رقم الأمر: {job_num}
            العميل: {cust}
            التاريخ: {date}
            الوصف: {description}
            
            الإجماليات:
            - المواد: {self.materials_total.text()}
            - العمالة: {self.labor_total.text()}
            - المصروفات: {self.costs_total.text()}
            - الإجمالي الكلي: {self.grand_total.text()}
            
            تم إنشاء التقرير في: {QDate.currentDate().toString("dd/MM/yyyy")}
            """
            
            QMessageBox.information(self, "طباعة الأمر", 
                                  f"سيتم طباعة أمر التشغيل {job_num}\n\n{report_content}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الطباعة: {str(e)}")

# ------------------------------------------------------------
# تشغيل التطبيق
# ------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # تعيين الخط العام للتطبيق
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    win = JobOrderWindow()
    win.show()
    sys.exit(app.exec_())
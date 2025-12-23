# ui/financial/journal_entry_report_ui.py

import sqlite3
import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDateEdit, QGroupBox, QGridLayout, QApplication, QStyle,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate, QVariant # Added QVariant for setData
from PyQt5.QtGui import QFont, QColor

# =====================================================================
# تصحيح مسار المشروع الجذر لتمكين الاستيراد الصحيح
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..')) 
if project_root not in sys.path:
    sys.path.append(project_root)

# استيراد المدراء الضروريين
from database.manager.financial.journal_entry_manager import JournalEntryManager
from database.db_connection import get_financials_db_connection 
# استيراد دالة تعبئة البيانات الافتراضية ومخطط قاعدة البيانات
from database.schems.default_data.financials_data_population import insert_default_data
from database.schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT 


# =====================================================================
# Helper function to load QSS files (moved here for general use)
# =====================================================================
def load_qss_file(file_path):
    """Loads content from a QSS file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: QSS file not found at {file_path}")
        return ""
    except Exception as e:
        print(f"ERROR: Could not load QSS file {file_path}: {e}")
        return ""


class JournalEntryReportWindow(QWidget):
    def __init__(self, journal_manager=None):
        super().__init__()
        self.journal_manager = journal_manager if journal_manager else JournalEntryManager(get_financials_db_connection)

        self.setWindowTitle("تقرير قيود اليومية")
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        # self.apply_styles() # تم إزالة استدعاء دالة apply_styles هنا للاعتماد على الأنماط الشاملة


    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20) # إضافة هوامش
        main_layout.setSpacing(15) # زيادة المسافات بين العناصر

        # العنوان
        title_label = QLabel("تقرير قيود اليومية")
        title_label.setFont(QFont("Arial", 18, QFont.Bold)) # حجم أكبر
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("windowTitle") # إضافة اسم كائن لسهولة التحديد في QSS
        # title_label.setStyleSheet("color: #2C3E50; margin-bottom: 20px;") # تم نقل النمط إلى QSS
        main_layout.addWidget(title_label)

        # مجموعة خيارات التقرير
        controls_group = QGroupBox("خيارات التقرير")
        controls_group.setLayoutDirection(Qt.RightToLeft)
        controls_layout = QGridLayout(controls_group)
        controls_layout.setSpacing(10) # مسافات داخل المجموعة
        controls_group.setObjectName("controlsGroupBox") # إضافة اسم كائن لسهولة التحديد في QSS
        # تم نقل أنماط QGroupBox إلى QSS
        # controls_group.setStyleSheet("""
        #     QGroupBox {
        #         border: 1px solid #BDC3C7;
        #         border-radius: 8px;
        #         margin-top: 15px;
        #         padding: 15px;
        #         font-size: 11pt;
        #         font-weight: bold;
        #         color: #34495E;
        #     }
        #     QGroupBox::title {
        #         subcontrol-origin: margin;
        #         subcontrol-position: top center;
        #         padding: 0 10px;
        #     }
        # """)

        # نطاق التاريخ
        controls_layout.addWidget(QLabel("من تاريخ:"), 0, 0)
        self.start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1)) # افتراضي: شهر سابق
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        controls_layout.addWidget(self.start_date_edit, 0, 1)

        controls_layout.addWidget(QLabel("إلى تاريخ:"), 0, 2) # في نفس السطر
        self.end_date_edit = QDateEdit(QDate.currentDate()) # افتراضي: اليوم
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        controls_layout.addWidget(self.end_date_edit, 0, 3) # في نفس السطر

        # زر توليد التقرير (تحت التاريخ مباشرة)
        self.generate_report_btn = QPushButton("توليد التقرير")
        self.generate_report_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton)) 
        self.generate_report_btn.clicked.connect(self.generate_report)
        self.generate_report_btn.setObjectName("generateReportButton") # إضافة اسم كائن لسهولة التحديد في QSS
        controls_layout.addWidget(self.generate_report_btn, 1, 0, 1, 4) # الصف 1، العمود 0، يمتد على صف واحد و 4 أعمدة

        # ضبط تمدد الأعمدة في الـ GridLayout
        controls_layout.setColumnStretch(1, 1) 
        controls_layout.setColumnStretch(3, 1) 

        main_layout.addWidget(controls_group)

        # جدول التقرير
        self.report_table = QTableWidget()
        self.report_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.report_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.report_table.setAlternatingRowColors(True)
        self.report_table.setObjectName("reportTable") # إضافة اسم كائن لسهولة التحديد في QSS
        # 14 عموداً: رقم القيد، التاريخ، الوصف (القيد)، نوع الحركة، العملة،
        # الحساب، المدين، الدائن، رقم المستند (البند)، نوع المستند (البند)،
        # مركز التكلفة، نوع الضرائب، ملاحظات (البند)، الحالة
        self.report_table.setColumnCount(14) 
        self.report_table.setHorizontalHeaderLabels([
            "رقم القيد", "التاريخ", "الوصف (القيد)", "نوع الحركة", "العملة", 
            "الحساب", "مدين", "دائن", # المدين والدائن بعد الحساب
            "رقم المستند (البند)", "نوع المستند (البند)", "مركز التكلفة", "نوع الضرائب", # رقم المستند قبل نوع المستند
            "ملاحظات (البند)", "الحالة"
        ])
        
        # ضبط حجم الأعمدة (التهيئة الأولية)
        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # رقم القيد
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # التاريخ
        header.setSectionResizeMode(2, QHeaderView.Stretch)         # الوصف (القيد) - يتمدد
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # نوع الحركة
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # العملة
        header.setSectionResizeMode(5, QHeaderView.Stretch)         # الحساب - يتمدد
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents) # مدين
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents) # دائن
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents) # رقم المستند (البند)
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents) # نوع المستند (البند)
        header.setSectionResizeMode(10, QHeaderView.ResizeToContents) # مركز التكلفة
        header.setSectionResizeMode(11, QHeaderView.ResizeToContents) # نوع الضرائب
        header.setSectionResizeMode(12, QHeaderView.Stretch)        # ملاحظات (البند) - يتمدد
        header.setSectionResizeMode(13, QHeaderView.ResizeToContents) # الحالة

        # تعيين الحد الأدنى للعرض للأعمدة الرقمية لضمان القراءة
        for col in [6, 7]: # مدين, دائن
            header.setMinimumSectionSize(100)


        main_layout.addWidget(self.report_table)

    # تم إزالة دالة apply_styles هنا للاعتماد على الأنماط الشاملة
    # def apply_styles(self):
    #     # أنماط CSS متناسقة مع الواجهات الأخرى
    #     self.setStyleSheet("""
    #         QWidget { 
    #             background-color: #F4F6F6; 
    #             font-family: 'Segoe UI', Arial, sans-serif; 
    #             font-size: 10pt; 
    #             color: #2C3E50; 
    #         }
    #         QLabel { 
    #             color: #34495E; 
    #             font-weight: bold; 
    #             margin-bottom: 3px; 
    #         }
    #         QLineEdit, QDateEdit, QComboBox { 
    #             border: 1px solid #BDC3C7; 
    #             border-radius: 5px; 
    #             padding: 8px; 
    #             background-color: white; 
    #             color: #2C3E50; 
    #             selection-background-color: #AAB7B8;
    #         }
    #         QLineEdit:focus, QComboBox:focus {
    #             border: 1px solid #3498DB;
    #         }
    #         QTableWidget { 
    #             background-color: white; 
    #             border: 1px solid #BDC3C7; 
    #             border-radius: 8px; 
    #             gridline-color: #E5E8E8; 
    #             alternate-background-color: #F8F9F9; 
    #             color: #2C3E50; 
    #             font-size: 9pt;
    #         }
    #         QHeaderView::section { 
    #             background-color: #34495E; 
    #             color: white; 
    #             padding: 8px; 
    #             border: 1px solid #BDC3C7; 
    #             font-weight: bold; 
    #             text-align: center; 
    #         }
    #         QTableWidget::item { 
    #             padding: 7px; 
    #             text-align: right; 
    #             color: #2C3E50; 
    #         }
    #         QTableWidget::item:selected { 
    #             background-color: #D6EAF8; 
    #             color: #2C3E50; 
    #             font-weight: bold;
    #         }
    #         QGroupBox { 
    #             font-weight: bold; 
    #             margin-top: 10px; 
    #             border: 1px solid #AAB7B8; 
    #             border-radius: 8px; 
    #             padding-top: 20px; 
    #             padding-left: 10px; 
    #             padding-right: 10px; 
    #             background-color: #ECF0F1; 
    #         }
    #         QGroupBox::title { 
    #             subcontrol-origin: margin; 
    #             subcontrol-position: top center; 
    #             padding: 0 10px; 
    #             background-color: #34495E; 
    #             color: white; 
    #             border-radius: 5px;
    #         }
    #         QPushButton {
    #             background-color: #007bff;
    #             color: white;
    #             border: 1px solid #007bff;
    #             border-radius: 8px;
    #             padding: 8px 15px;
    #             font-size: 14px;
    #             min-width: 80px;
    #             font-weight: 500;
    #             text-align: center; 
    #             qproperty-iconSize: 16px 16px;
    #         }
    #         QPushButton:hover {
    #             background-color: #0056b3;
    #             border-color: #0056b3;
    #         }
    #         QPushButton:pressed {
    #             background-color: #004085;
    #         }
    #         /* Style for the totals row using custom UserData property */
    #         QTableWidget::item[UserData="total-row"] {
    #             background-color: #D4EDDA; /* Light green for totals */
    #             font-weight: bold;
    #             color: #155724; /* Dark green text */
    #             border-top: 3px double #34495E; /* Double line border */
    #         }
    #         /* Ensure regular items don't have this border */
    #         QTableWidget::item:not([UserData="total-row"]) {
    #             border-top: none;
    #         }
    #     """)

    def add_numeric_item(self, row, col, value, alignment=Qt.AlignRight):
        """Adds a numeric item to the table with appropriate formatting and alignment"""
        item = QTableWidgetItem(f"{value:,.2f}")
        item.setTextAlignment(alignment | Qt.AlignVCenter)
        self.report_table.setItem(row, col, item)
        return item

    def generate_report(self):
        """يولد تقرير قيود اليومية للفترة الزمنية المحددة."""
        self.report_table.setRowCount(0) # مسح الجدول قبل التوليد
        
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

        journal_entries_data = self.journal_manager.get_journal_entries_in_range(start_date, end_date)

        if not journal_entries_data:
            QMessageBox.information(self, "لا توجد بيانات", "لا توجد قيود يومية في الفترة المحددة.")
            return

        current_entry_id = None
        row_idx = 0
        total_report_debit = 0.0
        total_report_credit = 0.0

        for item in journal_entries_data:
            # إذا كان قيد جديد، أضف صفاً فاصلاً (اختياري) أو قم بتمييزه
            if item['entry_id'] != current_entry_id:
                if current_entry_id is not None:
                    # إضافة صف فارغ للفصل بين القيود
                    self.report_table.insertRow(row_idx)
                    for col in range(self.report_table.columnCount()):
                        empty_item = QTableWidgetItem("")
                        empty_item.setBackground(QColor("#F0F0F0")) # لون خلفية فاتح جداً للفصل
                        self.report_table.setItem(row_idx, col, empty_item)
                    row_idx += 1

                current_entry_id = item['entry_id']
                
                # إضافة صف لرأس القيد
                self.report_table.insertRow(row_idx)
                # تعيين العناصر أولاً قبل محاولة تلوينها
                self.report_table.setItem(row_idx, 0, QTableWidgetItem(item['entry_number']))
                self.report_table.setItem(row_idx, 1, QTableWidgetItem(item['entry_date']))
                self.report_table.setItem(row_idx, 2, QTableWidgetItem(item['entry_description']))
                self.report_table.setItem(row_idx, 3, QTableWidgetItem(item['transaction_type_name']))
                #self.report_table.setItem(row_idx, 4, QTableWidgetItem(item['currency_code']))
                
                # إجمالي المدين والدائن للقيد (في صف الرأس) - الآن في الأعمدة 6 و 7
                self.add_numeric_item(row_idx, 6, item['total_debit']) # عمود المدين
                self.add_numeric_item(row_idx, 7, item['total_credit']) # عمود الدائن

                self.report_table.setItem(row_idx, 13, QTableWidgetItem(item['status'])) # عمود الحالة
                
                # تلوين صف رأس القيد
                for col in range(self.report_table.columnCount()):
                    if self.report_table.item(row_idx, col) is not None:
                        self.report_table.item(row_idx, col).setBackground(QColor("#E0E6F0")) # لون خلفية فاتح
                        self.report_table.item(row_idx, col).setFont(QFont("Arial", 9, QFont.Bold))
                
                # دمج الخلايا الفارغة في صف الرأس
                # دمج الأعمدة من 5 (الحساب) إلى 5 (الحساب)
                self.report_table.setSpan(row_idx, 5, 1, 1) 
                # دمج الأعمدة من 8 (رقم المستند البند) إلى 12 (ملاحظات البند)
                self.report_table.setSpan(row_idx, 8, 1, 5) 

                row_idx += 1

            # إضافة صف لبند القيد
            self.report_table.insertRow(row_idx)
            # تفاصيل البند
            self.report_table.setItem(row_idx, 5, QTableWidgetItem(f"{item['acc_code']} - {item['account_name_ar']}")) # الحساب
            
            # المدين والدائن بعد اسم الحساب
            self.add_numeric_item(row_idx, 6, item['debit']) # مدين
            self.add_numeric_item(row_idx, 7, item['credit']) # دائن

            # رقم المستند قبل نوع المستند
            self.report_table.setItem(row_idx, 8, QTableWidgetItem(item['line_document_number'] if item['line_document_number'] else "")) # رقم المستند (البند)
            self.report_table.setItem(row_idx, 9, QTableWidgetItem(item['line_document_type_name'] if item['line_document_type_name'] else "")) # نوع المستند (البند)
            self.report_table.setItem(row_idx, 10, QTableWidgetItem(item['line_cost_center_name'] if item['line_cost_center_name'] else "")) # مركز التكلفة
            self.report_table.setItem(row_idx, 11, QTableWidgetItem(item['line_tax_type_name'] if item['line_tax_type_name'] else "")) # نوع الضرائب

            self.report_table.setItem(row_idx, 12, QTableWidgetItem(item['line_notes'] if item['line_notes'] else "")) # ملاحظات البند
            
            # دمج الخلايا الفارغة في صف البند
            self.report_table.setSpan(row_idx, 0, 1, 5) # دمج من رقم القيد إلى العملة
            self.report_table.setSpan(row_idx, 13, 1, 1) # الحالة (فارغة لبنود القيد)

            total_report_debit += item['debit']
            total_report_credit += item['credit']
            row_idx += 1
        
        # إضافة صف الإجماليات النهائية
        self.add_totals_row(total_report_debit, total_report_credit, row_idx)

        # إعادة ضبط حجم الأعمدة بناءً على المحتوى
        self.report_table.resizeColumnsToContents()
        
        # إعادة تطبيق وضع التمدد للأعمدة المرنة بعد resizeColumnsToContents
        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch) # الوصف (القيد)
        header.setSectionResizeMode(5, QHeaderView.Stretch) # الحساب
        header.setSectionResizeMode(12, QHeaderView.Stretch) # ملاحظات (البند)

    def add_totals_row(self, total_debit, total_credit, row_idx):
        """Adds a new row to the table to display totals for debit and credit."""
        self.report_table.insertRow(row_idx)

        # دمج الخلايا لعنوان "الإجمالي"
        # سيتم دمج الخلايا من العمود 0 (رقم القيد) حتى العمود 5 (الحساب)
        self.report_table.setSpan(row_idx, 0, 1, 6) 
        
        total_label_item = QTableWidgetItem("الإجمالي")
        total_label_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        total_label_item.setFont(QFont("Arial", 10, QFont.Bold))
        total_label_item.setData(Qt.UserRole, QVariant("total-row")) # Custom data for QSS styling
        self.report_table.setItem(row_idx, 0, total_label_item)

        # إضافة إجمالي المدين والدائن تحت أعمدتهما مباشرة
        # المدين في العمود 6، الدائن في العمود 7
        self.add_numeric_item(row_idx, 6, total_debit, alignment=Qt.AlignRight).setData(Qt.UserRole, QVariant("total-row"))
        self.add_numeric_item(row_idx, 7, total_credit, alignment=Qt.AlignRight).setData(Qt.UserRole, QVariant("total-row"))
        
        # دمج الخلايا المتبقية في صف الإجماليات
        # من العمود 8 (رقم المستند البند) حتى العمود 13 (الحالة)
        self.report_table.setSpan(row_idx, 8, 1, 6) 


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # تهيئة مخطط قاعدة البيانات وتعبئة بيانات افتراضية للاختبار
    conn = None # Initialize conn to None
    try:
        print("DEBUG: Attempting to get financials DB connection...")
        conn = get_financials_db_connection()
        if conn:
            print("DEBUG: Connection to financials DB successful.")
            try:
                cursor = conn.cursor()
                # التحقق من وجود جدول journal_entries بشكل خاص
                print("DEBUG: Checking for 'journal_entries' table existence...")
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='journal_entries';")
                journal_entries_table_exists = cursor.fetchone() 
                
                if not journal_entries_table_exists: 
                    print("Financials DB schema (journal_entries table) not found. Initializing full schema...")
                    cursor.executescript(FINANCIALS_SCHEMA_SCRIPT)
                    conn.commit()
                    print("Financials DB schema initialized.")
                    
                    # تعبئة بيانات افتراضية بعد التهيئة مباشرة
                    try:
                        print("DEBUG: Attempting to insert default data...")
                        insert_default_data(conn)
                        print("Default lookups, accounts, and dummy journal entries populated.")
                    except Exception as e: 
                        print(f"WARNING: Error populating default data after schema init: {e}.")
                        print("Please ensure database/schems/default_data/financials_data_population.py is correctly implemented.")
                        import traceback
                        traceback.print_exc() # Print full traceback
                else:
                    print("Financials DB (journal_entries table) already exists. Ensuring default data is present.")
                    # إذا كانت الجداول موجودة، تأكد من أن البيانات الافتراضية موجودة أيضاً
                    # هذا يضمن أن البيانات التجريبية موجودة حتى لو لم يتم حذف DB في كل مرة
                    try:
                        print("DEBUG: Ensuring default data is present (INSERT OR IGNORE)...")
                        insert_default_data(conn) # حاول تعبئة البيانات الافتراضية (ستتجاهل الموجود)
                        print("Ensured default data is present (INSERT OR IGNORE).")
                    except Exception as e:
                        print(f"WARNING: Error ensuring default data is present: {e}")
                        import traceback
                        traceback.print_exc() # Print full traceback

            except sqlite3.Error as e:
                QMessageBox.critical(None, "خطأ في قاعدة البيانات", f"فشل التحقق أو تهيئة المخطط: {e}")
                print(f"ERROR: SQLite error during schema check/init: {e}")
                import traceback
                traceback.print_exc() # Print full traceback
                sys.exit(1)
            finally:
                if conn:
                    conn.close()
                    print("DEBUG: Connection closed after schema/data check.")
        else:
            QMessageBox.critical(None, "خطأ في الاتصال", "فشل الاتصال بقاعدة البيانات المالية.")
            print("ERROR: Failed to get financials DB connection.")
            sys.exit(1)
                
    except Exception as e:
        QMessageBox.critical(None, "خطأ في تشغيل التطبيق", f"حدث خطأ غير متوقع أثناء تهيئة التطبيق: {e}")
        print(f"CRITICAL ERROR: Unhandled exception during app initialization: {e}")
        import traceback
        traceback.print_exc() # Print full traceback
        sys.exit(1)

    # تحديد مسار ملف QSS
    # بافتراض أن styles.qss موجود في my_erp_projects/ui/styles/
    qss_file_path = os.path.join(project_root, 'ui', 'styles', 'styles.qss')

    # تحميل وتطبيق ملف QSS
    app_stylesheet = load_qss_file(qss_file_path)
    if app_stylesheet:
        app.setStyleSheet(app_stylesheet)
        print("DEBUG: Applied DFD-001 stylesheet.")
    else:
        print("WARNING: Failed to load stylesheet. UI might not be consistent.")

    print("DEBUG: Initializing JournalManager...")
    try:
        test_journal_manager = JournalEntryManager(get_financials_db_connection)
        print("DEBUG: JournalManager initialized successfully.")
    except Exception as e:
        QMessageBox.critical(None, "خطأ في تهيئة المدير", f"فشل تهيئة JournalManager: {e}")
        print(f"ERROR: Failed to initialize JournalManager: {e}")
        import traceback
        traceback.print_exc() # Print full traceback
        sys.exit(1)
    
    print("DEBUG: Creating and showing JournalEntryReportWindow...")
    try:
        window = JournalEntryReportWindow(journal_manager=test_journal_manager)
        window.showMaximized() # عرض النافذة بأقصى حجم
        print("DEBUG: Window shown. Starting application event loop...")
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, "خطأ في عرض الواجهة", f"حدث خطأ غير متوقع أثناء عرض الواجهة: {e}")
        print(f"ERROR: Unhandled exception during window display or event loop: {e}")
        import traceback
        traceback.print_exc() # Print full traceback
        sys.exit(1)

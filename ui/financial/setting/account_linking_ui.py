# -*- coding: utf-8 -*-
import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QComboBox, QDateEdit,
    QGridLayout, QGroupBox, QTabWidget, QTextEdit, QCheckBox, QSpacerItem, QSizePolicy,
    QTreeWidget, QTreeWidgetItem, QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QIcon

class Supplierswindow(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.current_supplier_id = None
        self.setWindowTitle("نظام إدارة الموردين")
        self.setWindowIcon(QIcon("supplier_icon.png"))
        self.setMinimumSize(1200, 700)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.load_suppliers()
        self.load_accounts_tree()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # شريط البحث والإجراءات
        actions_layout = QHBoxLayout()
        
        # حقل البحث
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث باسم المورد، الرقم الضريبي، الهاتف...")
        self.search_input.setMinimumHeight(35)
        self.search_input.textChanged.connect(self.search_suppliers)
        
        # أزرار الإجراءات
        self.add_btn = QPushButton("إضافة مورد جديد")
        self.add_btn.setIcon(QIcon("add_icon.png"))
        self.add_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.add_btn.clicked.connect(self.add_new_supplier)
        
        self.edit_btn = QPushButton("تعديل المحدد")
        self.edit_btn.setIcon(QIcon("edit_icon.png"))
        self.edit_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        self.edit_btn.clicked.connect(self.edit_selected_supplier)
        self.edit_btn.setEnabled(False)
        
        self.deactivate_btn = QPushButton("إيقاف المحدد")
        self.deactivate_btn.setIcon(QIcon("deactivate_icon.png"))
        self.deactivate_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        self.deactivate_btn.clicked.connect(self.deactivate_supplier)
        self.deactivate_btn.setEnabled(False)
        
        self.close_btn = QPushButton("إغلاق")
        self.close_btn.setIcon(QIcon("close_icon.png"))
        self.close_btn.setStyleSheet("background-color: #F44336; color: white; padding: 8px;")
        self.close_btn.clicked.connect(self.close)
        
        actions_layout.addWidget(self.search_input)
        actions_layout.addWidget(self.add_btn)
        actions_layout.addWidget(self.edit_btn)
        actions_layout.addWidget(self.deactivate_btn)
        actions_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(actions_layout)
        
        # جدول الموردين
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "اسم المورد", "الرقم الضريبي", "جهة الاتصال", 
            "الهاتف", "البريد الإلكتروني", "العنوان", "الحالة"
        ])
        self.table.setColumnHidden(0, True)  # إخفاء عمود ID
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellClicked.connect(self.supplier_selected)
        
        main_layout.addWidget(self.table)
        
        # منطقة تفاصيل المورد (ستظهر عند التحديد)
        self.details_group = QGroupBox("تفاصيل المورد")
        self.details_group.setVisible(False)
        self.setup_details_form()
        main_layout.addWidget(self.details_group)

    def setup_details_form(self):
        form_layout = QVBoxLayout(self.details_group)
        
        # تبويبات التفاصيل
        self.tabs = QTabWidget()
        
        # تبويب المعلومات الأساسية
        basic_tab = QWidget()
        basic_layout = QGridLayout(basic_tab)
        basic_layout.setSpacing(10)
        basic_layout.setContentsMargins(10, 10, 10, 10)
        
        # الصف 1
        basic_layout.addWidget(QLabel("اسم المورد:"), 0, 0)
        self.name_input = QLineEdit()
        basic_layout.addWidget(self.name_input, 0, 1)
        
        basic_layout.addWidget(QLabel("الرقم الضريبي:"), 0, 2)
        self.tax_input = QLineEdit()
        basic_layout.addWidget(self.tax_input, 0, 3)
        
        # الصف 2
        basic_layout.addWidget(QLabel("جهة الاتصال:"), 1, 0)
        self.contact_input = QLineEdit()
        basic_layout.addWidget(self.contact_input, 1, 1)
        
        basic_layout.addWidget(QLabel("الهاتف:"), 1, 2)
        self.phone_input = QLineEdit()
        basic_layout.addWidget(self.phone_input, 1, 3)
        
        # الصف 3
        basic_layout.addWidget(QLabel("البريد الإلكتروني:"), 2, 0)
        self.email_input = QLineEdit()
        basic_layout.addWidget(self.email_input, 2, 1)
        
        basic_layout.addWidget(QLabel("الموقع الإلكتروني:"), 2, 2)
        self.website_input = QLineEdit()
        basic_layout.addWidget(self.website_input, 2, 3)
        
        # الصف 4
        basic_layout.addWidget(QLabel("العنوان:"), 3, 0)
        self.address_input = QLineEdit()
        basic_layout.addWidget(self.address_input, 3, 1, 1, 3)
        
        # الصف 5
        basic_layout.addWidget(QLabel("البلد:"), 4, 0)
        self.country_input = QLineEdit()
        basic_layout.addWidget(self.country_input, 4, 1)
        
        basic_layout.addWidget(QLabel("المدينة:"), 4, 2)
        self.city_input = QLineEdit()
        basic_layout.addWidget(self.city_input, 4, 3)
        
        # الصف 6
        basic_layout.addWidget(QLabel("الرمز البريدي:"), 5, 0)
        self.postal_input = QLineEdit()
        basic_layout.addWidget(self.postal_input, 5, 1)
        
        basic_layout.addWidget(QLabel("فئة التوريد:"), 5, 2)
        self.category_input = QComboBox()
        self.category_input.addItems(["مواد خام", "معدات", "خدمات", "منتجات تامة"])
        basic_layout.addWidget(self.category_input, 5, 3)
        
        self.tabs.addTab(basic_tab, "المعلومات الأساسية")
        
        # تبويب المعلومات المالية
        financial_tab = QWidget()
        financial_layout = QGridLayout(financial_tab)
        financial_layout.setSpacing(10)
        financial_layout.setContentsMargins(10, 10, 10, 10)
        
        # الصف 1
        financial_layout.addWidget(QLabel("طريقة الدفع المفضلة:"), 0, 0)
        self.payment_method_input = QComboBox()
        self.payment_method_input.addItems(["تحويل بنكي", "شيك", "نقدي", "أجل"])
        financial_layout.addWidget(self.payment_method_input, 0, 1)
        
        financial_layout.addWidget(QLabel("شروط الدفع:"), 0, 2)
        self.payment_terms_input = QLineEdit()
        financial_layout.addWidget(self.payment_terms_input, 0, 3)
        
        # الصف 2
        financial_layout.addWidget(QLabel("الحد الائتماني:"), 1, 0)
        self.credit_input = QLineEdit()
        self.credit_input.setPlaceholderText("0.00")
        financial_layout.addWidget(self.credit_input, 1, 1)
        
        # إزالة حقل العملة تماماً
        financial_layout.addWidget(QLabel(""), 1, 2)  # تسمية فارغة
        financial_layout.addWidget(QLabel(""), 1, 3)  # حقل فارغ
        
        # الصف 3
        financial_layout.addWidget(QLabel("تاريخ بدء العقد:"), 2, 0)
        self.contract_start_input = QDateEdit()
        self.contract_start_input.setCalendarPopup(True)
        self.contract_start_input.setDate(QDate.currentDate())
        financial_layout.addWidget(self.contract_start_input, 2, 1)
        
        financial_layout.addWidget(QLabel("تاريخ نهاية العقد:"), 2, 2)
        self.contract_end_input = QDateEdit()
        self.contract_end_input.setCalendarPopup(True)
        self.contract_end_input.setDate(QDate.currentDate().addYears(1))
        financial_layout.addWidget(self.contract_end_input, 2, 3)
        
        # الصف 4
        financial_layout.addWidget(QLabel("التقييم:"), 3, 0)
        self.rating_input = QComboBox()
        self.rating_input.addItems(["", "⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"])
        financial_layout.addWidget(self.rating_input, 3, 1)
        
        self.tabs.addTab(financial_tab, "المعلومات المالية")
        
        # تبويب سياسات المخزون
        inventory_tab = QWidget()
        inventory_layout = QGridLayout(inventory_tab)
        inventory_layout.setSpacing(10)
        inventory_layout.setContentsMargins(10, 10, 10, 10)
        
        # الصف 1
        inventory_layout.addWidget(QLabel("الحد الأدنى للمخزون:"), 0, 0)
        self.min_stock_input = QLineEdit()
        self.min_stock_input.setPlaceholderText("0")
        inventory_layout.addWidget(self.min_stock_input, 0, 1)
        
        inventory_layout.addWidget(QLabel("زمن التسليم (أيام):"), 0, 2)
        self.lead_time_input = QLineEdit()
        self.lead_time_input.setPlaceholderText("0")
        inventory_layout.addWidget(self.lead_time_input, 0, 3)
        
        # الصف 2
        inventory_layout.addWidget(QLabel("طريقة الاتصال المفضلة:"), 1, 0)
        self.contact_method_input = QComboBox()
        self.contact_method_input.addItems(["بريد إلكتروني", "هاتف", "واتساب", "زيارة"])
        inventory_layout.addWidget(self.contact_method_input, 1, 1)
        
        inventory_layout.addWidget(QLabel("اللغة:"), 1, 2)
        self.language_input = QComboBox()
        self.language_input.addItems(["العربية", "الإنجليزية", "الفرنسية", "أخرى"])
        inventory_layout.addWidget(self.language_input, 1, 3)
        
        self.tabs.addTab(inventory_tab, "سياسات المخزون")
        
        notes_tab = QWidget()
        notes_layout = QVBoxLayout(notes_tab)
        notes_layout.setContentsMargins(10, 10, 10, 10)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("أدخل أي ملاحظات إضافية عن المورد...")
        notes_layout.addWidget(self.notes_input)
        
        # خيارات الحالة
        status_layout = QHBoxLayout()
        
        self.active_check = QCheckBox("نشط")
        self.active_check.setChecked(True)
        # تنسيق واضح لمربعات الاختيار
        checkbox_style = """
            QCheckBox {
                spacing: 8px;
                font-weight: bold;
                color: #333;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border: 2px solid #666;
                border-radius: 4px;
                background: #f8f8f8;
            }
            QCheckBox::indicator:checked {
                background: #4CAF50;
                border: 2px solid #4CAF50;
            }
            QCheckBox::indicator:unchecked:hover {
                border: 2px solid #444;
                background: #eee;
            }
            QCheckBox:disabled {
                color: #999;
            }
        """
        self.active_check.setStyleSheet(checkbox_style)
        status_layout.addWidget(self.active_check)
        
        self.verified_check = QCheckBox("تم التحقق")
        self.verified_check.setStyleSheet(checkbox_style)
        status_layout.addWidget(self.verified_check)
        
        status_layout.addStretch()
        notes_layout.addLayout(status_layout)
        
        self.tabs.addTab(notes_tab, "ملاحظات")
        
        # تبويب الحسابات المرتبطة
        accounts_tab = QWidget()
        accounts_layout = QVBoxLayout(accounts_tab)

        # شجرة الحسابات
        self.accounts_tree = QTreeWidget()
        self.accounts_tree.setHeaderLabels(["الكود", "اسم الحساب"])
        # === تعديل: تغيير نمط الاختيار إلى مفرد ===
        self.accounts_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        accounts_layout.addWidget(self.accounts_tree)

        # جدول الحسابات المرتبطة (لعرض الحساب الذي تم إنشاؤه)
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(3)
        self.accounts_table.setHorizontalHeaderLabels(["ID", "كود الحساب", "اسم الحساب"])
        self.accounts_table.setColumnHidden(0, True)
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        accounts_layout.addWidget(self.accounts_table)

        # === تعديل: تغيير الأزرار لتناسب الوظيفة الجديدة ===
        accounts_btns = QHBoxLayout()
        self.create_account_btn = QPushButton("إنشاء وربط حساب فرعي للمورد تحت الحساب المختار")
        self.create_account_btn.setStyleSheet("background-color: #007BFF; color: white; font-weight: bold; padding: 8px;")
        self.create_account_btn.clicked.connect(self.create_and_link_supplier_account)
        accounts_btns.addWidget(self.create_account_btn)
        accounts_layout.addLayout(accounts_btns)

        self.tabs.addTab(accounts_tab, "إنشاء وربط الحساب")

        form_layout.addWidget(self.tabs)
        
        # أزرار الحفظ والإلغاء
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setStyleSheet("background-color: #F44336; color: white; padding: 8px;")
        self.cancel_btn.clicked.connect(self.cancel_edit)
        buttons_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("حفظ التغييرات")
        self.save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.save_btn.clicked.connect(self.save_supplier)
        buttons_layout.addWidget(self.save_btn)
        
        form_layout.addLayout(buttons_layout)

    def load_suppliers(self):
        self.table.setRowCount(0)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM suppliers WHERE is_active = 1 ORDER BY name_ar")
            
            for row_num, row in enumerate(cursor.fetchall()):
                self.table.insertRow(row_num)
                self.table.setItem(row_num, 0, QTableWidgetItem(str(row["id"])))
                self.table.setItem(row_num, 1, QTableWidgetItem(row["name_ar"]))
                self.table.setItem(row_num, 2, QTableWidgetItem(row["tax_number"] or ""))
                self.table.setItem(row_num, 3, QTableWidgetItem(row["contact_person"] or ""))
                self.table.setItem(row_num, 4, QTableWidgetItem(row["phone"] or ""))
                self.table.setItem(row_num, 5, QTableWidgetItem(row["email"] or ""))
                self.table.setItem(row_num, 6, QTableWidgetItem(row["address"] or ""))
                status_item = QTableWidgetItem("نشط")
                status_item.setForeground(Qt.darkGreen)
                self.table.setItem(row_num, 7, status_item)

    def search_suppliers(self):
        search_term = self.search_input.text().strip()
        if not search_term:
            self.load_suppliers()
            return
            
        self.table.setRowCount(0)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM suppliers 
                WHERE (name_ar LIKE ? OR tax_number LIKE ? OR contact_person LIKE ? OR phone LIKE ?)
                AND is_active = 1 
                ORDER BY name_ar
            """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            
            for row_num, row in enumerate(cursor.fetchall()):
                self.table.insertRow(row_num)
                self.table.setItem(row_num, 0, QTableWidgetItem(str(row["id"])))
                self.table.setItem(row_num, 1, QTableWidgetItem(row["name_ar"]))
                self.table.setItem(row_num, 2, QTableWidgetItem(row["tax_number"] or ""))
                self.table.setItem(row_num, 3, QTableWidgetItem(row["contact_person"] or ""))
                self.table.setItem(row_num, 4, QTableWidgetItem(row["phone"] or ""))
                self.table.setItem(row_num, 5, QTableWidgetItem(row["email"] or ""))
                self.table.setItem(row_num, 6, QTableWidgetItem(row["address"] or ""))
                status_item = QTableWidgetItem("نشط")
                status_item.setForeground(Qt.darkGreen)
                self.table.setItem(row_num, 7, status_item)

    def supplier_selected(self, row, column):
        self.edit_btn.setEnabled(True)
        self.deactivate_btn.setEnabled(True)
        supplier_id = int(self.table.item(row, 0).text())
        self.current_supplier_id = supplier_id
        self.show_supplier_details(supplier_id)

    def show_supplier_details(self, supplier_id):
        self.details_group.setVisible(True)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
            row = cursor.fetchone()
            if row:
                self.name_input.setText(row["name_ar"])
                self.tax_input.setText(row["tax_number"] or "")
                self.contact_input.setText(row["contact_person"] or "")
                self.phone_input.setText(row["phone"] or "")
                self.email_input.setText(row["email"] or "")
                self.website_input.setText(row["website"] or "")
                self.address_input.setText(row["address"] or "")
                self.country_input.setText(row["country"] or "")
                self.city_input.setText(row["city"] or "")
                self.postal_input.setText(row["postal_code"] or "")
                category_index = self.category_input.findText(row["supply_category"] or "")
                if category_index >= 0: self.category_input.setCurrentIndex(category_index)
                method_index = self.payment_method_input.findText(row["payment_method"] or "")
                if method_index >= 0: self.payment_method_input.setCurrentIndex(method_index)
                self.payment_terms_input.setText(row["payment_terms"] or "")
                self.credit_input.setText(str(row["credit_limit"] or ""))
                if row["contract_start_date"]: self.contract_start_input.setDate(QDate.fromString(row["contract_start_date"], "yyyy-MM-dd"))
                if row["contract_end_date"]: self.contract_end_input.setDate(QDate.fromString(row["contract_end_date"], "yyyy-MM-dd"))
                rating = row["rating"] or 0
                self.rating_input.setCurrentIndex(min(rating, self.rating_input.count() - 1)) if rating > 0 else self.rating_input.setCurrentIndex(0)
                self.min_stock_input.setText(str(row["minimum_stock_level"] or ""))
                self.lead_time_input.setText(str(row["lead_time"] or ""))
                contact_index = self.contact_method_input.findText(row["preferred_contact_method"] or "")
                if contact_index >= 0: self.contact_method_input.setCurrentIndex(contact_index)
                lang_index = self.language_input.findText(row["language"] or "")
                if lang_index >= 0: self.language_input.setCurrentIndex(lang_index)
                self.notes_input.setPlainText(row["notes"] or "")
                self.active_check.setChecked(row["is_active"] == 1)
                self.verified_check.setChecked(row["is_verified"] == 1)
                self.show_supplier_accounts(supplier_id)

    def add_new_supplier(self):
        self.details_group.setVisible(True)
        self.clear_form()
        self.current_supplier_id = None
        self.tabs.setCurrentIndex(0)
        self.name_input.setFocus()

    def edit_selected_supplier(self):
        if self.current_supplier_id:
            self.tabs.setCurrentIndex(0)
            self.name_input.setFocus()

    def deactivate_supplier(self):
        if not self.current_supplier_id: return
        reply = QMessageBox.question(self, "تأكيد الإيقاف", "هل أنت متأكد أنك تريد إيقاف هذا المورد؟", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE suppliers SET is_active = 0 WHERE id = ?", (self.current_supplier_id,))
                conn.commit()
            self.load_suppliers()
            self.details_group.setVisible(False)
            self.current_supplier_id = None
            self.edit_btn.setEnabled(False)
            self.deactivate_btn.setEnabled(False)
            QMessageBox.information(self, "تم الإيقاف", "تم إيقاف المورد بنجاح")

    def save_supplier(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "بيانات ناقصة", "اسم المورد مطلوب")
            self.name_input.setFocus()
            return
            
        data = {
            "name_ar": self.name_input.text().strip(), "tax_number": self.tax_input.text().strip(),
            "contact_person": self.contact_input.text().strip(), "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(), "website": self.website_input.text().strip(),
            "address": self.address_input.text().strip(), "country": self.country_input.text().strip(),
            "city": self.city_input.text().strip(), "postal_code": self.postal_input.text().strip(),
            "supply_category": self.category_input.currentText(), "payment_method": self.payment_method_input.currentText(),
            "payment_terms": self.payment_terms_input.text().strip(), "credit_limit": float(self.credit_input.text() or 0),
            "contract_start_date": self.contract_start_input.date().toString("yyyy-MM-dd"),
            "contract_end_date": self.contract_end_input.date().toString("yyyy-MM-dd"),
            "rating": self.rating_input.currentIndex(), "minimum_stock_level": int(self.min_stock_input.text() or 0),
            "lead_time": int(self.lead_time_input.text() or 0),
            "preferred_contact_method": self.contact_method_input.currentText(), "language": self.language_input.currentText(),
            "notes": self.notes_input.toPlainText().strip(), "is_active": 1 if self.active_check.isChecked() else 0,
            "is_verified": 1 if self.verified_check.isChecked() else 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if self.current_supplier_id:
                    query = """
                        UPDATE suppliers SET
                            name_ar = ?, tax_number = ?, contact_person = ?, phone = ?, email = ?, website = ?, 
                            address = ?, country = ?, city = ?, postal_code = ?, supply_category = ?, 
                            payment_terms = ?, credit_limit = ?, contract_start_date = ?, contract_end_date = ?, 
                            rating = ?, minimum_stock_level = ?, lead_time = ?, preferred_contact_method = ?, 
                            language = ?, notes = ?, is_active = ?, is_verified = ?, payment_method = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """
                    params = list(data.values()) + [self.current_supplier_id]
                    cursor.execute(query, tuple(params))
                    action = "تحديث"
                else:
                    query = f"INSERT INTO suppliers ({', '.join(data.keys())}) VALUES ({', '.join(['?'] * len(data))})"
                    cursor.execute(query, tuple(data.values()))
                    self.current_supplier_id = cursor.lastrowid
                    action = "إضافة"
                
                conn.commit()
                # === تعديل: تم حذف استدعاء دالة الحفظ القديمة من هنا ===
                # self.save_supplier_accounts()

            self.load_suppliers()
            QMessageBox.information(self, "تم الحفظ", f"تم {action} المورد بنجاح")
            
            if self.current_supplier_id:
                for row in range(self.table.rowCount()):
                    if int(self.table.item(row, 0).text()) == self.current_supplier_id:
                        self.table.selectRow(row)
                        self.supplier_selected(row, 0)
                        break
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الحفظ", f"حدث خطأ أثناء حفظ البيانات:\n{str(e)}")

    def cancel_edit(self):
        if self.current_supplier_id:
            self.show_supplier_details(self.current_supplier_id)
        else:
            self.details_group.setVisible(False)
            self.clear_form()

    def clear_form(self):
        for widget in self.details_group.findChildren(QLineEdit): widget.clear()
        for widget in self.details_group.findChildren(QComboBox): widget.setCurrentIndex(0)
        self.notes_input.clear()
        self.contract_start_input.setDate(QDate.currentDate())
        self.contract_end_input.setDate(QDate.currentDate().addYears(1))
        self.active_check.setChecked(True)
        self.verified_check.setChecked(False)
        self.accounts_table.setRowCount(0)
    
    # ---------------- الحسابات (منطق جديد ومُحسّن) ----------------

    def load_accounts_tree(self):
        """تحميل شجرة الحسابات من قاعدة البيانات المالية"""
        self.accounts_tree.clear()
        try:
            with sqlite3.connect("database/financials.db") as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM accounts WHERE is_active=1 ORDER BY acc_code")
                accounts = cursor.fetchall()

            tree_data = {}
            for acc in accounts: tree_data.setdefault(acc["parent_account_id"], []).append(acc)

            def add_children(parent_item, parent_id):
                for acc in tree_data.get(parent_id, []):
                    item = QTreeWidgetItem([acc["acc_code"], acc["account_name_ar"]])
                    item.setData(0, Qt.UserRole, acc["id"])
                    parent_item.addChild(item)
                    add_children(item, acc["id"])

            for acc in tree_data.get(None, []):
                root_item = QTreeWidgetItem([acc["acc_code"], acc["account_name_ar"]])
                root_item.setData(0, Qt.UserRole, acc["id"])
                self.accounts_tree.addTopLevelItem(root_item)
                add_children(root_item, acc["id"])
            self.accounts_tree.expandAll()
        except Exception as e:
            QMessageBox.warning(self, "تحذير", f"خطأ في تحميل شجرة الحسابات: {str(e)}")

    # === دالة جديدة: لإنشاء وربط حساب المورد تلقائياً ===
    def create_and_link_supplier_account(self):
        # 1. التحقق من وجود مورد محدد واسم له
        if not self.current_supplier_id or not self.name_input.text().strip():
            QMessageBox.warning(self, "خطأ", "يجب أولاً حفظ معلومات المورد الأساسية (خاصة الاسم).")
            return

        # 2. التحقق من اختيار حساب أب من الشجرة
        selected_items = self.accounts_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "خطأ", "الرجاء اختيار 'حساب أب' من الشجرة أولاً (مثل حساب الموردين).")
            return
        
        parent_item = selected_items[0]
        parent_id = parent_item.data(0, Qt.UserRole)
        parent_code = parent_item.text(0)

        try:
            with sqlite3.connect("database/financials.db") as conn:
                cursor = conn.cursor()

                # 3. البحث عن آخر كود حساب فرعي لنفس الأب
                cursor.execute("SELECT MAX(acc_code) FROM accounts WHERE parent_account_id = ?", (parent_id,))
                last_code = cursor.fetchone()[0]

                # 4. إنشاء الكود الجديد
                if last_code:
                    # إذا كان الكود الحالي رقمي، نزيده بمقدار 1
                    try:
                        new_acc_code = str(int(last_code) + 1)
                    except ValueError:
                        # إذا لم يكن رقمي، نضيف 01 في النهاية
                        new_acc_code = last_code + "01"
                else:
                    new_acc_code = parent_code + "01"

                # 5. تجهيز بيانات الحساب الجديد
                new_account_name = self.name_input.text().strip()
                
                # حساب مستوى الحساب الجديد
                cursor.execute("SELECT level FROM accounts WHERE id = ?", (parent_id,))
                parent_level = cursor.fetchone()[0]
                new_level = parent_level + 1
                
                # حساب مسار الحساب الجديد
                cursor.execute("SELECT account_path FROM accounts WHERE id = ?", (parent_id,))
                parent_path = cursor.fetchone()[0]
                new_account_path = f"{parent_path}/{new_account_name}" if parent_path else new_account_name

                # 6. إضافة الحساب الجديد إلى جدول الحسابات
                cursor.execute("""
                    INSERT INTO accounts 
                    (acc_code, account_name_ar, parent_account_id, is_final, is_active, level, account_path, account_type_id) 
                    VALUES (?, ?, ?, 1, 1, ?, ?, ?)
                """, (new_acc_code, new_account_name, parent_id, new_level, new_account_path, 5))  # 5 هو نوع حساب الموردين

                new_account_id = cursor.lastrowid
                conn.commit()

            # 7. ربط الحساب الجديد بالمورد
            with sqlite3.connect(self.db_path) as conn_inv:
                cursor_inv = conn_inv.cursor()
                cursor_inv.execute("DELETE FROM supplier_accounts WHERE supplier_id=?", (self.current_supplier_id,))
                cursor_inv.execute("INSERT INTO supplier_accounts (supplier_id, account_id) VALUES (?, ?)", (self.current_supplier_id, new_account_id))
                conn_inv.commit()

            QMessageBox.information(self, "نجاح", f"تم إنشاء الحساب '{new_acc_code} - {new_account_name}' وربطه بالمورد بنجاح.")

            # 8. تحديث الواجهة
            self.load_accounts_tree()
            self.show_supplier_accounts(self.current_supplier_id)

        except Exception as e:
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"حدث خطأ أثناء إنشاء الحساب: \n{e}")



















    def show_supplier_accounts(self, supplier_id):
        """عرض الحسابات المرتبطة بمورد"""
        self.accounts_table.setRowCount(0)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                conn.execute("ATTACH DATABASE 'database/financials.db' AS fin;")
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.id AS account_id, a.acc_code, a.account_name_ar
                    FROM supplier_accounts sa
                    JOIN fin.accounts a ON sa.account_id = a.id
                    WHERE sa.supplier_id = ? ORDER BY a.acc_code
                """, (supplier_id,))
            
                for row_num, row in enumerate(cursor.fetchall()):
                    self.accounts_table.insertRow(row_num)
                    self.accounts_table.setItem(row_num, 0, QTableWidgetItem(str(row["account_id"])))
                    self.accounts_table.setItem(row_num, 1, QTableWidgetItem(row["acc_code"]))
                    self.accounts_table.setItem(row_num, 2, QTableWidgetItem(row["account_name_ar"]))
        except Exception as e:
            QMessageBox.warning(self, "تحذير", f"خطأ في تحميل الحسابات المرتبطة: {str(e)}")

    def save_supplier_accounts(self):
        """
        === ملاحظة: هذه الدالة لم تعد مستخدمة بشكل فعال ===
        المنطق الجديد في create_and_link_supplier_account يقوم بالربط مباشرة.
        نتركها فارغة لتجنب أي أخطاء محتملة لو تم استدعاؤها.
        """
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Arial", 10)
    app.setFont(font)
    
    # تأكد من أن المسار صحيح وأن الملفات موجودة
    # 예: "database/inventory.db", "database/financials.db"
    window = Supplierswindow("database/inventory.db")
    window.show()
    sys.exit(app.exec_())
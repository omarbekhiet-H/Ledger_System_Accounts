# -*- coding: utf-8 -*-
import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QComboBox, QDateEdit,
    QGridLayout, QGroupBox, QTabWidget, QTextEdit, QCheckBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QIcon

class CustomersWindow(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.current_customer_id = None
        self.setWindowTitle("نظام إدارة العملاء")
        self.setWindowIcon(QIcon("customer_icon.png"))
        self.setMinimumSize(1200, 700)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.load_customers()
        self.load_accounts_list()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # شريط البحث والإجراءات
        actions_layout = QHBoxLayout()
        
        # حقل البحث
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث باسم العميل، الرقم الضريبي، الهاتف...")
        self.search_input.setMinimumHeight(35)
        self.search_input.textChanged.connect(self.search_customers)
        
        # أزرار الإجراءات
        self.add_btn = QPushButton("إضافة عميل جديد")
        self.add_btn.setIcon(QIcon("add_icon.png"))
        self.add_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.add_btn.clicked.connect(self.add_new_customer)
        
        self.edit_btn = QPushButton("تعديل المحدد")
        self.edit_btn.setIcon(QIcon("edit_icon.png"))
        self.edit_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        self.edit_btn.clicked.connect(self.edit_selected_customer)
        self.edit_btn.setEnabled(False)
        
        self.deactivate_btn = QPushButton("إيقاف المحدد")
        self.deactivate_btn.setIcon(QIcon("deactivate_icon.png"))
        self.deactivate_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        self.deactivate_btn.clicked.connect(self.deactivate_customer)
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
        
        # جدول العملاء
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "اسم العميل", "الرقم الضريبي", "جهة الاتصال", 
            "الهاتف", "البريد الإلكتروني", "العنوان", "الحالة"
        ])
        self.table.setColumnHidden(0, True)  # إخفاء عمود ID
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellClicked.connect(self.customer_selected)
        
        main_layout.addWidget(self.table)
        
        # منطقة تفاصيل العميل (ستظهر عند التحديد)
        self.details_group = QGroupBox("تفاصيل العميل")
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
        basic_layout.addWidget(QLabel("اسم العميل:"), 0, 0)
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
        
        basic_layout.addWidget(QLabel("فئة العميل:"), 5, 2)
        self.category_input = QComboBox()
        self.category_input.addItems(["تجزئة", "جملة", "شركة", "فرد"])
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
        self.payment_method_input.addItems(["نقدي", "بطاقة ائتمان", "تحويل بنكي", "أجل"])
        financial_layout.addWidget(self.payment_method_input, 0, 1)
        
        financial_layout.addWidget(QLabel("شروط الدفع:"), 0, 2)
        self.payment_terms_input = QLineEdit()
        financial_layout.addWidget(self.payment_terms_input, 0, 3)
        
        # الصف 2
        financial_layout.addWidget(QLabel("الحد الائتماني:"), 1, 0)
        self.credit_input = QLineEdit()
        self.credit_input.setPlaceholderText("0.00")
        financial_layout.addWidget(self.credit_input, 1, 1)
        
        # إزالة حقل العملة
        financial_layout.addWidget(QLabel("تاريخ بدء التعامل:"), 1, 2)
        self.contract_start_input = QDateEdit()
        self.contract_start_input.setCalendarPopup(True)
        self.contract_start_input.setDate(QDate.currentDate())
        financial_layout.addWidget(self.contract_start_input, 1, 3)
        
        # الصف 3
        financial_layout.addWidget(QLabel("آخر تاريخ شراء:"), 2, 0)
        self.contract_end_input = QDateEdit()
        self.contract_end_input.setCalendarPopup(True)
        self.contract_end_input.setDate(QDate.currentDate())
        financial_layout.addWidget(self.contract_end_input, 2, 1)
        
        financial_layout.addWidget(QLabel("التقييم:"), 2, 2)
        self.rating_input = QComboBox()
        self.rating_input.addItems(["", "⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"])
        financial_layout.addWidget(self.rating_input, 2, 3)
        
        self.tabs.addTab(financial_tab, "المعلومات المالية")
        
        # تبويب التفضيلات
        preferences_tab = QWidget()
        preferences_layout = QGridLayout(preferences_tab)
        preferences_layout.setSpacing(10)
        preferences_layout.setContentsMargins(10, 10, 10, 10)
        
        # الصف 1
        preferences_layout.addWidget(QLabel("طريقة الاتصال المفضلة:"), 0, 0)
        self.contact_method_input = QComboBox()
        self.contact_method_input.addItems(["بريد إلكتروني", "هاتف", "واتساب", "رسالة نصية"])
        preferences_layout.addWidget(self.contact_method_input, 0, 1)
        
        preferences_layout.addWidget(QLabel("اللغة:"), 0, 2)
        self.language_input = QComboBox()
        self.language_input.addItems(["العربية", "الإنجليزية", "الفرنسية", "أخرى"])
        preferences_layout.addWidget(self.language_input, 0, 3)
        
        # الصف 2
        preferences_layout.addWidget(QLabel("سياسة الخصم:"), 1, 0)
        self.discount_policy_input = QComboBox()
        self.discount_policy_input.addItems(["لا يوجد", "حسب الكمية", "موسمي", "خاص"])
        preferences_layout.addWidget(self.discount_policy_input, 1, 1)
        
        preferences_layout.addWidget(QLabel("نسبة الخصم %:"), 1, 2)
        self.discount_percent_input = QLineEdit()
        self.discount_percent_input.setPlaceholderText("0")
        preferences_layout.addWidget(self.discount_percent_input, 1, 3)
        
        self.tabs.addTab(preferences_tab, "التفضيلات")
        
        # تبويب ملاحظات
        notes_tab = QWidget()
        notes_layout = QVBoxLayout(notes_tab)
        notes_layout.setContentsMargins(10, 10, 10, 10)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("أدخل أي ملاحظات إضافية عن العميل...")
        notes_layout.addWidget(self.notes_input)
        
        # خيارات الحالة
        status_layout = QHBoxLayout()
        
        self.active_check = QCheckBox("نشط")
        self.active_check.setChecked(True)
        status_layout.addWidget(self.active_check)
        
        self.verified_check = QCheckBox("تم التحقق")
        status_layout.addWidget(self.verified_check)
        
        status_layout.addStretch()
        notes_layout.addLayout(status_layout)
        
        self.tabs.addTab(notes_tab, "ملاحظات")
        
        # تبويب الحسابات المرتبطة
        accounts_tab = QWidget()
        accounts_layout = QVBoxLayout(accounts_tab)

        self.accounts_combo = QComboBox()
        accounts_layout.addWidget(self.accounts_combo)

        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(3)
        self.accounts_table.setHorizontalHeaderLabels(["ID", "كود الحساب", "اسم الحساب"])
        self.accounts_table.setColumnHidden(0, True)
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        accounts_layout.addWidget(self.accounts_table)

        accounts_btns = QHBoxLayout()
        self.add_account_btn = QPushButton("إضافة حساب")
        self.add_account_btn.clicked.connect(self.add_account_to_customer)
        self.remove_account_btn = QPushButton("حذف الحساب المحدد")
        self.remove_account_btn.clicked.connect(self.remove_selected_account)
        accounts_btns.addWidget(self.add_account_btn)
        accounts_btns.addWidget(self.remove_account_btn)
        accounts_layout.addLayout(accounts_btns)

        self.tabs.addTab(accounts_tab, "الحسابات المرتبطة")

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
        self.save_btn.clicked.connect(self.save_customer)
        buttons_layout.addWidget(self.save_btn)
        
        form_layout.addLayout(buttons_layout)

    def load_customers(self):
        self.table.setRowCount(0)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
        
            # الحصول على الأعمدة المتاحة في الجدول
            cursor.execute("PRAGMA table_info(customers)")
            available_columns = [column[1] for column in cursor.fetchall()]
        
            # بناء الاستعلام بشكل آمن بناءً على الأعمدة المتاحة
            select_fields = ["id", "name_ar", "contact_person", "phone", "email", "address", "is_active"]
            if "tax_number" in available_columns:
                select_fields.append("tax_number")
        
            query = f"SELECT {', '.join(select_fields)} FROM customers WHERE is_active = 1 ORDER BY name_ar"
            cursor.execute(query)
        
            for row_num, row in enumerate(cursor.fetchall()):
                self.table.insertRow(row_num)
            
                # إضافة البيانات إلى الجدول
                self.table.setItem(row_num, 0, QTableWidgetItem(str(row["id"])))
                self.table.setItem(row_num, 1, QTableWidgetItem(row["name_ar"]))
            
                # التعامل مع tax_number إذا كان موجوداً
                tax_number = ""
                if "tax_number" in available_columns:
                    tax_number = row["tax_number"] or "" if row["tax_number"] is not None else ""
                self.table.setItem(row_num, 2, QTableWidgetItem(tax_number))
            
                self.table.setItem(row_num, 3, QTableWidgetItem(row["contact_person"] or ""))
                self.table.setItem(row_num, 4, QTableWidgetItem(row["phone"] or ""))
                self.table.setItem(row_num, 5, QTableWidgetItem(row["email"] or ""))
                self.table.setItem(row_num, 6, QTableWidgetItem(row["address"] or ""))
            
                # عرض حالة العميل
                status_item = QTableWidgetItem("نشط")
                status_item.setForeground(Qt.darkGreen)
                self.table.setItem(row_num, 7, status_item)
                
    def search_customers(self):
        search_term = self.search_input.text().strip()
        if not search_term:
            self.load_customers()
            return
        
        self.table.setRowCount(0)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
        
            # التحقق من وجود الأعمدة
            cursor.execute("PRAGMA table_info(customers)")
            columns = [column[1] for column in cursor.fetchall()]
        
            query = """
                SELECT * FROM customers 
                WHERE (name_ar LIKE ? OR contact_person LIKE ? OR phone LIKE ?)
                AND is_active = 1 
                ORDER BY name_ar
            """
            cursor.execute(query, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        
            for row_num, row in enumerate(cursor.fetchall()):
                self.table.insertRow(row_num)
                self.table.setItem(row_num, 0, QTableWidgetItem(str(row["id"])))
                self.table.setItem(row_num, 1, QTableWidgetItem(row["name_ar"]))
            
                # التعامل مع tax_number
                try:
                    tax_number = row["tax_number"] or ""
                except (KeyError, IndexError):
                    tax_number = ""
                self.table.setItem(row_num, 2, QTableWidgetItem(tax_number))
            
                self.table.setItem(row_num, 3, QTableWidgetItem(row["contact_person"] or ""))
                self.table.setItem(row_num, 4, QTableWidgetItem(row["phone"] or ""))
                self.table.setItem(row_num, 5, QTableWidgetItem(row["email"] or ""))
                self.table.setItem(row_num, 6, QTableWidgetItem(row["address"] or ""))
            
                status_item = QTableWidgetItem("نشط")
                status_item.setForeground(Qt.darkGreen)
                self.table.setItem(row_num, 7, status_item)

    def customer_selected(self, row, column):
        self.edit_btn.setEnabled(True)
        self.deactivate_btn.setEnabled(True)
        
        # الحصول على معرف العميل
        customer_id = int(self.table.item(row, 0).text())
        self.current_customer_id = customer_id
        
        # عرض تفاصيل العميل
        self.show_customer_details(customer_id)

    def show_customer_details(self, customer_id):
        self.details_group.setVisible(True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
            row = cursor.fetchone()
            
            if row:
                # تعبئة حقول المعلومات الأساسية
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
                
                # تعيين فئة العميل
                category_index = self.category_input.findText(row["customer_category"] or "")
                if category_index >= 0:
                    self.category_input.setCurrentIndex(category_index)
                
                # تعبئة حقول المعلومات المالية
                method_index = self.payment_method_input.findText(row["payment_method"] or "")
                if method_index >= 0:
                    self.payment_method_input.setCurrentIndex(method_index)
                
                self.payment_terms_input.setText(row["payment_terms"] or "")
                self.credit_input.setText(str(row["credit_limit"] or ""))
                
                # تواريخ التعامل
                if row["contract_start_date"]:
                    self.contract_start_input.setDate(QDate.fromString(row["contract_start_date"], "yyyy-MM-dd"))
                if row["last_purchase_date"]:
                    self.contract_end_input.setDate(QDate.fromString(row["last_purchase_date"], "yyyy-MM-dd"))
                
                # التقييم
                rating = row["rating"] or 0
                if rating > 0:
                    self.rating_input.setCurrentIndex(min(rating, self.rating_input.count() - 1))
                else:
                    self.rating_input.setCurrentIndex(0)
                
                # تعبئة حقول التفضيلات
                contact_index = self.contact_method_input.findText(row["preferred_contact_method"] or "")
                if contact_index >= 0:
                    self.contact_method_input.setCurrentIndex(contact_index)
                
                lang_index = self.language_input.findText(row["language"] or "")
                if lang_index >= 0:
                    self.language_input.setCurrentIndex(lang_index)
                
                policy_index = self.discount_policy_input.findText(row["discount_policy"] or "")
                if policy_index >= 0:
                    self.discount_policy_input.setCurrentIndex(policy_index)
                
                self.discount_percent_input.setText(str(row["discount_percentage"] or ""))
                
                # الملاحظات
                self.notes_input.setPlainText(row["notes"] or "")
                
                # خيارات الحالة
                self.active_check.setChecked(row["is_active"] == 1)
                self.verified_check.setChecked(row["is_verified"] == 1)
                
                self.show_customer_accounts(customer_id)

    def add_new_customer(self):
        self.details_group.setVisible(True)
        self.clear_form()
        self.current_customer_id = None
        self.tabs.setCurrentIndex(0)
        self.name_input.setFocus()

    def edit_selected_customer(self):
        if self.current_customer_id:
            self.tabs.setCurrentIndex(0)
            self.name_input.setFocus()

    def deactivate_customer(self):
        if not self.current_customer_id:
            return
            
        reply = QMessageBox.question(
            self, "تأكيد الإيقاف", 
            "هل أنت متأكد أنك تريد إيقاف هذا العميل؟ لن يظهر في القائمة بعد الآن.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE customers SET is_active = 0 WHERE id = ?", (self.current_customer_id,))
                conn.commit()
            
            self.load_customers()
            self.details_group.setVisible(False)
            self.current_customer_id = None
            self.edit_btn.setEnabled(False)
            self.deactivate_btn.setEnabled(False)
            
            QMessageBox.information(self, "تم الإيقاف", "تم إيقاف العميل بنجاح")

    def save_customer(self):
        # التحقق من البيانات المطلوبة
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "بيانات ناقصة", "اسم العميل مطلوب")
            self.name_input.setFocus()
            return
            
        # تجميع البيانات
        data = {
            "name_ar": self.name_input.text().strip(),
            "tax_number": self.tax_input.text().strip(),
            "contact_person": self.contact_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "website": self.website_input.text().strip(),
            "address": self.address_input.text().strip(),
            "country": self.country_input.text().strip(),
            "city": self.city_input.text().strip(),
            "postal_code": self.postal_input.text().strip(),
            "customer_category": self.category_input.currentText(),
            "payment_method": self.payment_method_input.currentText(),
            "payment_terms": self.payment_terms_input.text().strip(),
            "credit_limit": float(self.credit_input.text() or 0),
            "contract_start_date": self.contract_start_input.date().toString("yyyy-MM-dd"),
            "last_purchase_date": self.contract_end_input.date().toString("yyyy-MM-dd"),
            "rating": self.rating_input.currentIndex(),
            "preferred_contact_method": self.contact_method_input.currentText(),
            "language": self.language_input.currentText(),
            "discount_policy": self.discount_policy_input.currentText(),
            "discount_percentage": float(self.discount_percent_input.text() or 0),
            "notes": self.notes_input.toPlainText().strip(),
            "is_active": 1 if self.active_check.isChecked() else 0,
            "is_verified": 1 if self.verified_check.isChecked() else 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if self.current_customer_id:
                    # تحديث العميل الموجود
                    query = """
                        UPDATE customers SET
                            name_ar = ?, tax_number = ?, contact_person = ?, phone = ?,
                            email = ?, website = ?, address = ?, country = ?, city = ?,
                            postal_code = ?, customer_category = ?, payment_terms = ?,
                            credit_limit = ?, contract_start_date = ?,
                            last_purchase_date = ?, rating = ?, preferred_contact_method = ?,
                            language = ?, discount_policy = ?, discount_percentage = ?,
                            notes = ?, is_active = ?, is_verified = ?, payment_method = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """
                    cursor.execute(query, (
                        data["name_ar"], data["tax_number"], data["contact_person"], data["phone"],
                        data["email"], data["website"], data["address"], data["country"], data["city"],
                        data["postal_code"], data["customer_category"], data["payment_terms"],
                        data["credit_limit"], data["contract_start_date"],
                        data["last_purchase_date"], data["rating"], data["preferred_contact_method"],
                        data["language"], data["discount_policy"], data["discount_percentage"],
                        data["notes"], data["is_active"], data["is_verified"], data["payment_method"],
                        self.current_customer_id
                    ))
                    action = "تحديث"
                else:
                    # إضافة عميل جديد
                    query = """
                        INSERT INTO customers (
                            name_ar, tax_number, contact_person, phone, email, website, 
                            address, country, city, postal_code, customer_category, 
                            payment_terms, credit_limit, contract_start_date, 
                            last_purchase_date, rating, preferred_contact_method, language, 
                            discount_policy, discount_percentage, notes, is_active, is_verified,
                            payment_method
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(query, (
                        data["name_ar"], data["tax_number"], data["contact_person"], data["phone"],
                        data["email"], data["website"], data["address"], data["country"], data["city"],
                        data["postal_code"], data["customer_category"], data["payment_terms"],
                        data["credit_limit"], data["contract_start_date"],
                        data["last_purchase_date"], data["rating"], data["preferred_contact_method"],
                        data["language"], data["discount_policy"], data["discount_percentage"],
                        data["notes"], data["is_active"], data["is_verified"], data["payment_method"]
                    ))
                    self.current_customer_id = cursor.lastrowid
                    action = "إضافة"
                
                conn.commit()
                # حفظ الحسابات المرتبطة
                self.save_customer_accounts()

            # تحديث الواجهة
            self.load_customers()
            QMessageBox.information(self, "تم الحفظ", f"تم {action} العميل بنجاح")
            
            # إذا كان جديداً، نحدده في الجدول
            if self.current_customer_id:
                for row in range(self.table.rowCount()):
                    if int(self.table.item(row, 0).text()) == self.current_customer_id:
                        self.table.selectRow(row)
                        self.customer_selected(row, 0)
                        break
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الحفظ", f"حدث خطأ أثناء حفظ البيانات:\n{str(e)}")

    def cancel_edit(self):
        if self.current_customer_id:
            self.show_customer_details(self.current_customer_id)
        else:
            self.details_group.setVisible(False)
            self.clear_form()

    def clear_form(self):
        # مسح جميع الحقول
        self.name_input.clear()
        self.tax_input.clear()
        self.contact_input.clear()
        self.phone_input.clear()
        self.email_input.clear()
        self.website_input.clear()
        self.address_input.clear()
        self.country_input.clear()
        self.city_input.clear()
        self.postal_input.clear()
        self.category_input.setCurrentIndex(0)
        self.payment_method_input.setCurrentIndex(0)
        self.payment_terms_input.clear()
        self.credit_input.clear()
        self.contract_start_input.setDate(QDate.currentDate())
        self.contract_end_input.setDate(QDate.currentDate())
        self.rating_input.setCurrentIndex(0)
        self.contact_method_input.setCurrentIndex(0)
        self.language_input.setCurrentIndex(0)
        self.discount_policy_input.setCurrentIndex(0)
        self.discount_percent_input.clear()
        self.notes_input.clear()
        self.active_check.setChecked(True)
        self.verified_check.setChecked(False)
        self.accounts_table.setRowCount(0)

    # ---------------- الحسابات ----------------
    def load_accounts_list(self):
        self.accounts_combo.clear()
        with sqlite3.connect(self.db_path) as conn:
            # ربط قاعدة البيانات المالية
            conn.execute("ATTACH DATABASE 'database/financials.db' AS fin;")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, acc_code, account_name_ar
                FROM fin.accounts
                WHERE is_active = 1 AND is_final = 1
                ORDER BY acc_code
            """)
            for row in cursor.fetchall():
                display_text = f"{row[1]} - {row[2]}"   # الكود + الاسم
                self.accounts_combo.addItem(display_text, row[0])

    def add_account_to_customer(self):
        """إضافة حساب للعميل الحالي"""
        if not self.current_customer_id:
            QMessageBox.warning(self, "تنبيه", "اختر عميل أولاً")
            return

        acc_text = self.accounts_combo.currentText()
        if not acc_text:
            return

        # الكود + الاسم جاي من الكمبوبوكس
        acc_id = self.accounts_combo.currentData()
        acc_code = acc_text.split(" - ")[0]
        acc_name = acc_text.split(" - ")[1] if " - " in acc_text else ""

        # تحقق لو الحساب مضاف مسبقًا
        for row in range(self.accounts_table.rowCount()):
            if int(self.accounts_table.item(row, 0).text()) == acc_id:
                QMessageBox.information(self, "تنبيه", "هذا الحساب مضاف بالفعل")
                return

        row_num = self.accounts_table.rowCount()
        self.accounts_table.insertRow(row_num)

        # ID (مخفي)
        self.accounts_table.setItem(row_num, 0, QTableWidgetItem(str(acc_id)))

        # كود الحساب
        self.accounts_table.setItem(row_num, 1, QTableWidgetItem(acc_code))

        # اسم الحساب
        self.accounts_table.setItem(row_num, 2, QTableWidgetItem(acc_name))

    def remove_selected_account(self):
        """إزالة الحساب المحدد من الجدول (محليًا فقط)"""
        selected = self.accounts_table.currentRow()
        if selected >= 0:
            self.accounts_table.removeRow(selected)

    def show_customer_accounts(self, customer_id):
        """عرض الحسابات المرتبطة بعميل"""
        self.accounts_table.setRowCount(0)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("ATTACH DATABASE 'database/financials.db' AS fin;")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.id AS account_id, a.acc_code, a.account_name_ar
                FROM customer_accounts ca
                JOIN fin.accounts a ON ca.account_id = a.id
                WHERE ca.customer_id = ?
                ORDER BY a.acc_code
            """, (customer_id,))
        
            for row_num, row in enumerate(cursor.fetchall()):
                self.accounts_table.insertRow(row_num)

                # ID (مخفي)
                self.accounts_table.setItem(row_num, 0, QTableWidgetItem(str(row["account_id"])))

                # كود الحساب
                self.accounts_table.setItem(row_num, 1, QTableWidgetItem(row["acc_code"]))

                # اسم الحساب
                self.accounts_table.setItem(row_num, 2, QTableWidgetItem(row["account_name_ar"]))

    def save_customer_accounts(self):
        """حفظ الحسابات المرتبطة بعميل معين في جدول customer_accounts"""
        if not self.current_customer_id:
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # نحذف كل القديم ونخزن الجديد
            cursor.execute("DELETE FROM customer_accounts WHERE customer_id=?", (self.current_customer_id,))
        
            for row in range(self.accounts_table.rowCount()):
                acc_id = int(self.accounts_table.item(row, 0).text())
                cursor.execute(
                    "INSERT OR IGNORE INTO customer_accounts (customer_id, account_id) VALUES (?, ?)",
                    (self.current_customer_id, acc_id)
                )
            conn.commit()

        # بعد الحفظ نعيد التحميل عشان يظهر الاسم
        self.show_customer_accounts(self.current_customer_id)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # تعيين خط عربي افتراضي
    font = QFont("Arial", 10)
    app.setFont(font)
    
    window = CustomersWindow("database/inventory.db")
    window.show()
    sys.exit(app.exec_())
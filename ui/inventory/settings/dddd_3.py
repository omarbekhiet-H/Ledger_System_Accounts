import sqlite3
import sys
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, 
    QPushButton, QComboBox, QMessageBox, QHeaderView, QDoubleSpinBox, QSplitter, 
    QGroupBox, QApplication, QWidget, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor

# تطبيق تنسيق عربي عام للتطبيق
def setup_arabic_style(app):
    # تعيين خط عربي افتراضي
    font = QFont("Arial", 10)
    font.setBold(False)
    app.setFont(font)
    
    # تلوين التطبيق بألوان مناسبة للواجهة العربية
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.Highlight, QColor(76, 163, 224))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

# ==============================
# نافذة اختيار الحساب من الشجرة
# ==============================
class AccountTreeDialog(QDialog):
    def __init__(self, financials_db, account_type_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"اختيار حساب ({account_type_name})")
        self.resize(700, 800)
        self.selected_account = None
        self.financials_db = financials_db
        self.account_type_name = account_type_name
        
        # تطبيق التنسيق العربي
        self.setLayoutDirection(Qt.RightToLeft)
        self.setup_ui()
        self.load_accounts()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignRight)
        
        # إطار البحث
        search_frame = QFrame()
        search_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        search_frame.setStyleSheet("background-color: #f8f9fa; padding: 5px;")
        search_layout = QHBoxLayout(search_frame)
        
        search_label = QLabel("بحث:")
        search_label.setStyleSheet("font-weight: bold; color: #2d3748;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث باسم الحساب أو الكود...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #cbd5e0;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #4299e1;
            }
        """)
        self.search_input.textChanged.connect(self.filter_accounts)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        main_layout.addWidget(search_frame)
        
        # شجرة الحسابات
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["الكود", "اسم الحساب", "النوع"])
        self.tree.setColumnWidth(0, 120)
        self.tree.setColumnWidth(1, 350)
        self.tree.setColumnWidth(2, 150)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: white;
                alternate-background-color: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #edf2f7;
            }
            QTreeWidget::item:selected {
                background-color: #4299e1;
                color: white;
            }
        """)
        self.tree.itemDoubleClicked.connect(self.select_account)
        main_layout.addWidget(self.tree, 1)

        # أزرار التحديد والإلغاء
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setAlignment(Qt.AlignRight)
        
        select_btn = QPushButton("✅ تحديد")
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #38a169;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2f855a;
            }
        """)
        select_btn.clicked.connect(self.accept_selection)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e53e3e;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c53030;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(select_btn)
        button_layout.addWidget(cancel_btn)
        main_layout.addWidget(button_frame)

        self.all_accounts = []

    def load_accounts(self):
        try:
            conn = sqlite3.connect(self.financials_db)
            cur = conn.cursor()
            
            type_mapping = {
                "أصول": "الأصول",
                "التزامات": "الخصوم", 
                "حقوق ملكية": "حقوق الملكية",
                "إيرادات": "الإيرادات",
                "مصروفات": "المصروفات"
            }
            
            db_type_name = type_mapping.get(self.account_type_name, self.account_type_name)
            
            cur.execute("SELECT id, name_ar FROM account_types WHERE name_ar = ? AND is_active = 1", (db_type_name,))
            account_type = cur.fetchone()
            
            if account_type:
                account_type_id, account_type_name_db = account_type
                cur.execute("""
                    SELECT a.id, a.acc_code, a.account_name_ar, t.name_ar as type_name
                    FROM accounts a
                    JOIN account_types t ON a.account_type_id = t.id
                    WHERE a.is_active = 1 AND a.account_type_id = ?
                    ORDER BY a.acc_code
                """, (account_type_id,))
                self.all_accounts = cur.fetchall()
            else:
                cur.execute("""
                    SELECT a.id, a.acc_code, a.account_name_ar, t.name_ar as type_name
                    FROM accounts a
                    JOIN account_types t ON a.account_type_id = t.id
                    WHERE a.is_active = 1
                    ORDER BY a.acc_code
                """)
                self.all_accounts = cur.fetchall()
            
            conn.close()
            self.populate_tree(self.all_accounts)
            
        except sqlite3.Error as e:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ في تحميل الحسابات: {str(e)}")

    def populate_tree(self, accounts):
        self.tree.clear()
        for account in accounts:
            if len(account) >= 4:
                account_id, acc_code, account_name, type_name = account
                item = QTreeWidgetItem([acc_code, account_name, type_name])
                item.setData(0, Qt.UserRole, account_id)
                self.tree.addTopLevelItem(item)

    def filter_accounts(self):
        search_text = self.search_input.text().lower()
        if not search_text:
            self.populate_tree(self.all_accounts)
            return
            
        filtered = []
        for account in self.all_accounts:
            if len(account) >= 4:
                account_id, acc_code, account_name, type_name = account
                if (search_text in str(acc_code).lower() or 
                    search_text in str(account_name).lower() or 
                    search_text in str(type_name).lower()):
                    filtered.append(account)
                    
        self.populate_tree(filtered)

    def accept_selection(self):
        current_item = self.tree.currentItem()
        if current_item:
            self.select_account(current_item)
        else:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار حساب من القائمة")

    def select_account(self, item):
        self.selected_account = {
            "id": item.data(0, Qt.UserRole),
            "code": item.text(0),
            "name": item.text(1),
            "type": item.text(2),
        }
        self.accept()


class AdvancedInventoryAccountsMappingDialog(QDialog):
    def __init__(self, financials_db, parent=None):
        super().__init__(parent)
        self.financials_db = financials_db
        self.setWindowTitle("نظام متقدم لربط الحركات المخزنية بالحسابات")
        self.resize(1400, 800)
        
        # تطبيق التنسيق العربي
        self.setLayoutDirection(Qt.RightToLeft)
        
        self.mapping_data = {}
        self.current_action_id = None
        self.setup_ui()
        self.load_existing_mappings()
        
    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setAlignment(Qt.AlignRight)
        
        # Splitter لتقسيم الشاشة
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #cbd5e0; }")
        
         # الجانب الأيسر: قائمة الحركات
        left_widget = QWidget()
        left_widget.setStyleSheet("background-color: #f8fafc; padding: 10px;")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setAlignment(Qt.AlignRight)
        
        title_label = QLabel("الحركات المخزنية:")
        title_label.setStyleSheet("""
            QLabel {
                font-weight: bold; 
                font-size: 14px; 
                color: #2d3748; 
                margin-bottom: 10px;
                padding: 5px;
                background-color: #e2e8f0;
                border-radius: 4px;
            }
        """)
        left_layout.addWidget(title_label)
        
        # إطار للجدول
        table_frame = QFrame()
        table_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        table_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
            }
        """)
        table_layout = QVBoxLayout(table_frame)
        
        self.actions_table = QTableWidget()
        self.actions_table.setColumnCount(2)
        self.actions_table.setHorizontalHeaderLabels(["الحركة", "عدد البنود"])
        self.actions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.actions_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #e2e8f0;
                border: none;
                border-radius: 4px;
                font-family: 'Segoe UI', Arial;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #edf2f7;
                text-align: right;
            }
            QTableWidget::item:selected {
                background-color: #4299e1;
                color: white;
            }
            QHeaderView::section {
                background-color: #4a5568;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }
        """)

        self.actions_table.cellClicked.connect(self.on_action_selected)
        table_layout.addWidget(self.actions_table)
        
        left_layout.addWidget(table_frame)
        # الجانب الأيمن: تفاصيل القيد المحاسبي
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setAlignment(Qt.AlignRight)
        
        # معلومات الحركة
        self.action_info = QLabel("اختر حركة لعرض تفاصيلها")
        self.action_info.setStyleSheet("""
            QLabel {
                background-color: #ebf8ff;
                padding: 15px;
                border-radius: 6px;
                border: 1px solid #bee3f8;
                font-weight: bold;
                color: #2b6cb0;
            }
        """)
        right_layout.addWidget(self.action_info)  

        # جدول بنود القيد (المدين)
    
        debit_group = QGroupBox("الطرف المدين")
        debit_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #fc8181;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: #fed7d7;
                color: #c53030;
            }
        """)
        debit_layout = QVBoxLayout(debit_group)
        
        self.debit_table = QTableWidget()
        self.debit_table.setColumnCount(4)
        self.debit_table.setHorizontalHeaderLabels(["الحساب", "المبلغ", "النسبة %", "الإجراء"])
        self.debit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.debit_table.setStyleSheet("""
            QTableWidget {
                background-color: #fff5f5;
                gridline-color: #fed7d7;
            }
        """)
        debit_layout.addWidget(self.debit_table)
        
        # أزرار إدارة البنود المدين
        debit_buttons = QHBoxLayout()
        debit_buttons.setAlignment(Qt.AlignRight)
        add_debit_btn = QPushButton("➕ إضافة بند مدين")
        add_debit_btn.setStyleSheet("""
            QPushButton {
                background-color: #fc8181;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f56565;
            }
        """)
        add_debit_btn.clicked.connect(self.add_debit_row)
        debit_buttons.addWidget(add_debit_btn)
        debit_layout.addLayout(debit_buttons)
        
        right_layout.addWidget(debit_group)
        
        # جدول بنود القيد (الدائن)
        credit_group = QGroupBox("الطرف الدائن")
        credit_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #68d391;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: #c6f6d5;
                color: #2f855a;
            }
        """)
        credit_layout = QVBoxLayout(credit_group)
        
        self.credit_table = QTableWidget()
        self.credit_table.setColumnCount(4)
        self.credit_table.setHorizontalHeaderLabels(["الحساب", "المبلغ", "النسبة %", "الإجراء"])
        self.credit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.credit_table.setStyleSheet("""
            QTableWidget {
                background-color: #f0fff4;
                gridline-color: #c6f6d5;
            }
        """)
        credit_layout.addWidget(self.credit_table)
        
        # أزرار إدارة البنود الدائن
        credit_buttons = QHBoxLayout()
        credit_buttons.setAlignment(Qt.AlignRight)
        add_credit_btn = QPushButton("➕ إضافة بند دائن")
        add_credit_btn.setStyleSheet("""
            QPushButton {
                background-color: #68d391;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #48bb78;
            }
        """)
        add_credit_btn.clicked.connect(self.add_credit_row)
        credit_buttons.addWidget(add_credit_btn)
        credit_layout.addLayout(credit_buttons)
        
        right_layout.addWidget(credit_group)
        
        # معلومات التوازن
        self.balance_info = QLabel("المجموع المدين: 0 | المجموع الدائن: 0 | الفرق: 0")
        self.balance_info.setStyleSheet("""
            QLabel {
                background-color: #edf2f7;
                padding: 15px;
                border-radius: 6px;
                border: 1px solid #e2e8f0;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        right_layout.addWidget(self.balance_info)
        
        # أزرار الحفظ
        save_buttons = QHBoxLayout()
        save_buttons.setAlignment(Qt.AlignRight)
        
        save_btn = QPushButton("💾 حفظ القيد")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4299e1;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3182ce;
            }
        """)
        save_btn.clicked.connect(self.save_current_mapping)
        
        cancel_btn = QPushButton("🚫 إلغاء")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #a0aec0;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #718096;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        save_buttons.addWidget(save_btn)
        save_buttons.addWidget(cancel_btn)
        right_layout.addLayout(save_buttons)
        
        # إضافة الأجزاء إلى splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 1100])
        
        main_layout.addWidget(splitter)
        
        # تحميل الحركات
        self.load_actions()
        
    def load_actions(self):
        """تحميل أنواع الحركات المخزنية"""
        self.inventory_actions = [
            {"id": "receipt", "name": "إذن الاستلام"},
            {"id": "addition", "name": "إذن الإضافة"},
            {"id": "invoice", "name": "استلام الفاتورة"},
            {"id": "return", "name": "مرتجعات المشتريات"},
            {"id": "cash_payment", "name": "السداد النقدي"},
            {"id": "bank_payment", "name": "السداد البنكي"},
            {"id": "payment_with_tax", "name": "سداد مع ضرائب"},
            {"id": "payment_with_discount", "name": "سداد مع خصم"},
            {"id": "payment_with_bonus", "name": "سداد مع مكافأة"}
        ]
        
        self.actions_table.setRowCount(len(self.inventory_actions))
        
        for row, action in enumerate(self.inventory_actions):
            self.actions_table.setItem(row, 0, QTableWidgetItem(action["name"]))
            self.actions_table.setItem(row, 1, QTableWidgetItem("0 بند"))
            
    def on_action_selected(self, row, col):
        """عند اختيار حركة من القائمة"""
        self.current_action_id = self.inventory_actions[row]["id"]
        action_name = self.inventory_actions[row]["name"]
        
        self.action_info.setText(f"تفاصيل القيد المحاسبي لحركة: {action_name}")
        
        # تحميل بيانات القيد إذا كانت موجودة
        self.load_action_mapping(self.current_action_id)
        
        # تحديث معلومات التوازن
        self.update_balance_info()
        
    def load_action_mapping(self, action_id):
        """تحميل بيانات القيد المحاسبي لحركة معينة"""
        # مسح الجداول الحالية
        self.debit_table.setRowCount(0)
        self.credit_table.setRowCount(0)
        
        if action_id in self.mapping_data:
            # تحميل بنود المدين
            for debit_item in self.mapping_data[action_id].get("debit", []):
                self.add_debit_row(debit_item)
            
            # تحميل بنود الدائن
            for credit_item in self.mapping_data[action_id].get("credit", []):
                self.add_credit_row(credit_item)
        else:
            # إضافة صفوف افتراضية للحركات الأساسية
            if action_id == "receipt":
                self.add_debit_row({"account_id": None, "amount": 0, "percentage": 100})
                self.add_credit_row({"account_id": None, "amount": 0, "percentage": 100})
            elif action_id == "payment_with_tax":
                # مثال لسداد مع ضرائب: المبلغ الأساسي + الضريبة
                self.add_debit_row({"account_id": None, "amount": 0, "percentage": 85, "description": "المبلغ الأساسي"})
                self.add_debit_row({"account_id": None, "amount": 0, "percentage": 15, "description": "الضريبة"})
                self.add_credit_row({"account_id": None, "amount": 0, "percentage": 100})
        
    def add_debit_row(self, item_data=None):
        """إضافة بند جديد إلى الطرف المدين"""
        row = self.debit_table.rowCount()
        self.debit_table.insertRow(row)
        
        # حساب المدين
        account_combo = QComboBox()
        account_combo.setMinimumWidth(250)
        self.fill_account_combo(account_combo)
        if item_data and item_data.get("account_id"):
            self.select_account_in_combo(account_combo, item_data["account_id"])
        self.debit_table.setCellWidget(row, 0, account_combo)
        
        # المبلغ
        amount_spin = QDoubleSpinBox()
        amount_spin.setRange(0, 999999999)
        amount_spin.setDecimals(2)
        amount_spin.setSuffix(" جنيه")
        amount_spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
        if item_data:
            amount_spin.setValue(item_data.get("amount", 0))
        amount_spin.valueChanged.connect(self.update_balance_info)
        self.debit_table.setCellWidget(row, 1, amount_spin)
        
        # النسبة
        percent_spin = QDoubleSpinBox()
        percent_spin.setRange(0, 100)
        percent_spin.setDecimals(2)
        percent_spin.setSuffix(" %")
        percent_spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
        if item_data:
            percent_spin.setValue(item_data.get("percentage", 0))
        percent_spin.valueChanged.connect(self.update_balance_info)
        self.debit_table.setCellWidget(row, 2, percent_spin)
        
        # زر الحذف
        delete_btn = QPushButton("🗑️")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #fc8181;
                color: white;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #f56565;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_row(self.debit_table, row))
        self.debit_table.setCellWidget(row, 3, delete_btn)
        
    def add_credit_row(self, item_data=None):
        """إضافة بند جديد إلى الطرف الدائن"""
        row = self.credit_table.rowCount()
        self.credit_table.insertRow(row)
        
        # حساب الدائن
        account_combo = QComboBox()
        account_combo.setMinimumWidth(250)
        self.fill_account_combo(account_combo)
        if item_data and item_data.get("account_id"):
            self.select_account_in_combo(account_combo, item_data["account_id"])
        self.credit_table.setCellWidget(row, 0, account_combo)
        
        # المبلغ
        amount_spin = QDoubleSpinBox()
        amount_spin.setRange(0, 999999999)
        amount_spin.setDecimals(2)
        amount_spin.setSuffix(" جنيه")
        amount_spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
        if item_data:
            amount_spin.setValue(item_data.get("amount", 0))
        amount_spin.valueChanged.connect(self.update_balance_info)
        self.credit_table.setCellWidget(row, 1, amount_spin)
        
        # النسبة
        percent_spin = QDoubleSpinBox()
        percent_spin.setRange(0, 100)
        percent_spin.setDecimals(2)
        percent_spin.setSuffix(" %")
        percent_spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
        if item_data:
            percent_spin.setValue(item_data.get("percentage", 0))
        percent_spin.valueChanged.connect(self.update_balance_info)
        self.credit_table.setCellWidget(row, 2, percent_spin)
        
        # زر الحذف
        delete_btn = QPushButton("🗑️")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #68d391;
                color: white;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #48bb78;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_row(self.credit_table, row))
        self.credit_table.setCellWidget(row, 3, delete_btn)
        
    def fill_account_combo(self, combo):
        """ملء QComboBox بالحسابات المتاحة"""
        try:
            conn = sqlite3.connect(self.financials_db)
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, acc_code, account_name_ar 
                FROM accounts 
                WHERE is_active = 1 
                ORDER BY acc_code
            """)
            
            accounts = cur.fetchall()
            
            combo.clear()
            combo.addItem("-- اختر حساب --", None)
            
            for acc_id, acc_code, acc_name in accounts:
                combo.addItem(f"[{acc_code}] {acc_name}", acc_id)
            
            conn.close()
            
        except sqlite3.Error as e:
            print(f"خطأ في تحميل الحسابات: {str(e)}")
    
    def select_account_in_combo(self, combo, account_id):
        """اختيار حساب معين في QComboBox"""
        for i in range(combo.count()):
            if combo.itemData(i) == account_id:
                combo.setCurrentIndex(i)
                break
    
    def delete_row(self, table, row):
        """حذف صف من الجدول"""
        table.removeRow(row)
        self.update_balance_info()
    
    def update_balance_info(self):
        """تحديث معلومات التوازن بين المدين والدائن"""
        total_debit = 0
        total_credit = 0
        
        # حساب المجموع المدين
        for row in range(self.debit_table.rowCount()):
            amount_spin = self.debit_table.cellWidget(row, 1)
            if amount_spin:
                total_debit += amount_spin.value()
        
        # حساب المجموع الدائن
        for row in range(self.credit_table.rowCount()):
            amount_spin = self.credit_table.cellWidget(row, 1)
            if amount_spin:
                total_credit += amount_spin.value()
        
        # تحديث معلومات التوازن
        difference = total_debit - total_credit
        status_color = "green" if difference == 0 else "red"
        
        self.balance_info.setText(
            f"المجموع المدين: {total_debit:,.2f} | "
            f"المجموع الدائن: {total_credit:,.2f} | "
            f"الفرق: <span style='color: {status_color}; font-weight: bold;'>{difference:,.2f}</span>"
        )
    
    def save_current_mapping(self):
        """حفظ القيد المحاسبي الحالي"""
        if not self.current_action_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار حركة أولاً")
            return
        
        # التحقق من التوازن
        total_debit = sum(self.debit_table.cellWidget(row, 1).value() 
                         for row in range(self.debit_table.rowCount()))
        total_credit = sum(self.credit_table.cellWidget(row, 1).value() 
                          for row in range(self.credit_table.rowCount()))
        
        if total_debit != total_credit:
            reply = QMessageBox.question(self, "تحذير", 
                                        "المجموع المدين لا يساوي المجموع الدائن. هل تريد المتابعة؟",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        # جمع بيانات المدين
        debit_items = []
        for row in range(self.debit_table.rowCount()):
            account_combo = self.debit_table.cellWidget(row, 0)
            amount_spin = self.debit_table.cellWidget(row, 1)
            percent_spin = self.debit_table.cellWidget(row, 2)
            
            debit_items.append({
                "account_id": account_combo.currentData(),
                "account_name": account_combo.currentText(),
                "amount": amount_spin.value(),
                "percentage": percent_spin.value()
            })
        
        # جمع بيانات الدائن
        credit_items = []
        for row in range(self.credit_table.rowCount()):
            account_combo = self.credit_table.cellWidget(row, 0)
            amount_spin = self.credit_table.cellWidget(row, 1)
            percent_spin = self.credit_table.cellWidget(row, 2)
            
            credit_items.append({
                "account_id": account_combo.currentData(),
                "account_name": account_combo.currentText(),
                "amount": amount_spin.value(),
                "percentage": percent_spin.value()
            })
        
        # حفظ البيانات
        self.mapping_data[self.current_action_id] = {
            "debit": debit_items,
            "credit": credit_items
        }
        
        # حفظ في قاعدة البيانات
        self.save_to_database()
        
        QMessageBox.information(self, "نجاح", "تم حفظ القيد المحاسبي بنجاح")
    
    def save_to_database(self):
        """حفظ جميع الإعدادات في قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.financials_db)
            cur = conn.cursor()
            
            # إنشاء الجدول إذا لم يكن موجوداً
            cur.execute("""
                CREATE TABLE IF NOT EXISTS advanced_inventory_mapping (
                    action_id TEXT,
                    side TEXT,
                    account_id INTEGER,
                    amount REAL,
                    percentage REAL,
                    PRIMARY KEY (action_id, side, account_id)
                )
            """)
            
            # حذف الإعدادات القديمة
            cur.execute("DELETE FROM advanced_inventory_mapping")
            
            # إضافة الإعدادات الجديدة
            for action_id, mapping in self.mapping_data.items():
                for debit_item in mapping.get("debit", []):
                    if debit_item["account_id"]:
                        cur.execute("""
                            INSERT INTO advanced_inventory_mapping (action_id, side, account_id, amount, percentage)
                            VALUES (?, 'debit', ?, ?, ?)
                        """, (action_id, debit_item["account_id"], debit_item["amount"], debit_item["percentage"]))
                
                for credit_item in mapping.get("credit", []):
                    if credit_item["account_id"]:
                        cur.execute("""
                            INSERT INTO advanced_inventory_mapping (action_id, side, account_id, amount, percentage)
                            VALUES (?, 'credit', ?, ?, ?)
                        """, (action_id, credit_item["account_id"], credit_item["amount"], credit_item["percentage"]))
            
            conn.commit()
            conn.close()
            
        except sqlite3.Error as e:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ في حفظ الإعدادات: {str(e)}")
    
    def load_existing_mappings(self):
        """تحميل الإعدادات الحالية من قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.financials_db)
            cur = conn.cursor()
            
            # جلب الإعدادات الحالية
            cur.execute("SELECT action_id, side, account_id, amount, percentage FROM advanced_inventory_mapping")
            rows = cur.fetchall()
            
            for action_id, side, account_id, amount, percentage in rows:
                if action_id not in self.mapping_data:
                    self.mapping_data[action_id] = {"debit": [], "credit": []}
                
                item = {
                    "account_id": account_id,
                    "amount": amount,
                    "percentage": percentage
                }
                
                if side == "debit":
                    self.mapping_data[action_id]["debit"].append(item)
                else:
                    self.mapping_data[action_id]["credit"].append(item)
            
            conn.close()
            
        except sqlite3.Error as e:
            print(f"لم يتم العثور على إعدادات سابقة: {str(e)}")

# تشغيل النافذة
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # تطبيق التنسيق العربي
    setup_arabic_style(app)
    
    # مسارات قواعد البيانات
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    financials_db = os.path.join(project_root, "database", "financials.db")
    
    dialog = AdvancedInventoryAccountsMappingDialog(financials_db)
    dialog.exec_()
    
    sys.exit(app.exec_())
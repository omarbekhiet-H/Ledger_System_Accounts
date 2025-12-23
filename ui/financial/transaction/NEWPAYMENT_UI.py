import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QGroupBox, QGridLayout, QDateEdit, QCompleter
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QPalette, QColor


# --- Database Path ---
project_root = os.getcwd()
DB_PATH = os.path.join(project_root, 'database', 'financials.db')


def ensure_columns():
    """التأكد من وجود الأعمدة doc_type و doc_number"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("PRAGMA table_info(cash_bank_transactions)")
            cols = [row[1] for row in c.fetchall()]
            if "doc_type" not in cols:
                c.execute("ALTER TABLE cash_bank_transactions ADD COLUMN doc_type TEXT")
            if "doc_number" not in cols:
                c.execute("ALTER TABLE cash_bank_transactions ADD COLUMN doc_number TEXT")
            conn.commit()
    except Exception as e:
        print("Error ensuring columns:", e)


class CashPaymentVoucher(QMainWindow):
    def __init__(self, db_path=DB_PATH):
        super().__init__()
        self.db_path = db_path
        self.current_voucher_id = None
        self.all_rows = []  # نخزن البيانات كاملة للبحث

        # إنشاء مجلد database إذا لم يكن موجوداً
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        if not os.path.exists(self.db_path):
            QMessageBox.critical(self, "خطأ", f"قاعدة البيانات غير موجودة:\n{self.db_path}")
            # سنقوم بإنشاء الجدول إذا لم يكن موجوداً
            self.create_table()
            
        ensure_columns()
        self.initUI()
        self.load_data()
        self.new_voucher()
        
    def create_table(self):
        """إنشاء جدول إذا لم يكن موجوداً"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('''
                    CREATE TABLE IF NOT EXISTS cash_bank_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        transaction_number TEXT NOT NULL,
                        transaction_date TEXT NOT NULL,
                        cash_chest_id INTEGER,
                        transaction_type TEXT,
                        description TEXT,
                        amount REAL,
                        doc_type TEXT,
                        doc_number TEXT
                    )
                ''')
                
                # إنشاء جدول الحسابات إذا لم يكن موجوداً
                c.execute('''
                    CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        acc_code TEXT NOT NULL,
                        account_name_ar TEXT NOT NULL,
                        parent_account_id INTEGER,
                        is_final INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1
                    )
                ''')
                
                # إضافة بعض الحسابات الافتراضية إذا كان الجدول فارغاً
                c.execute("SELECT COUNT(*) FROM accounts")
                if c.fetchone()[0] == 0:
                    # إضافة الخزنة الرئيسية
                    c.execute("INSERT INTO accounts (acc_code, account_name_ar, is_final, is_active) VALUES ('111', 'الخزنة الرئيسية', 1, 1)")
                    # إضافة بعض الحسابات الأخرى
                    accounts = [
                        ('101', 'النقدية في الصندوق', 1, 1),
                        ('201', 'الموردين', 1, 1),
                        ('301', 'المصروفات العمومية', 1, 1),
                        ('401', 'المبيعات', 1, 1)
                    ]
                    for acc_code, name, is_final, is_active in accounts:
                        c.execute("INSERT INTO accounts (acc_code, account_name_ar, is_final, is_active) VALUES (?, ?, ?, ?)", 
                                 (acc_code, name, is_final, is_active))
                
                conn.commit()
        except Exception as e:
            print("Error creating table:", e)

    def initUI(self):
        self.setWindowTitle("إيصال صرف نقدي")
        self.setGeometry(200, 200, 950, 700)
        self.setLayoutDirection(Qt.RightToLeft)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        title_label = QLabel("إيصالات الصرف النقدي")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        main_layout.addWidget(title_label)

        # --- بيانات أساسية ---
        basic_group = QGroupBox("البيانات الأساسية")
        grid = QGridLayout(basic_group)

        self.voucher_number = QLineEdit(readOnly=True)
        ro_palette = QPalette()
        ro_palette.setColor(QPalette.Base, QColor(240, 240, 240))
        self.voucher_number.setPalette(ro_palette)

        self.voucher_date = QDateEdit(QDate.currentDate(), calendarPopup=True, displayFormat="yyyy-MM-dd")
        self.cash_chests = QComboBox()

        # الحساب المدين مع فلترة
        self.debit_account_input = QLineEdit()
        self.debit_account_input.setPlaceholderText("ابحث بالكود أو الاسم")
        self.debit_account = QComboBox()

        # نوع المستند
        self.doc_type_combo = QComboBox()
        self.doc_number = QLineEdit()

        self.amount = QLineEdit()
        self.description = QLineEdit()

        grid.addWidget(QLabel("رقم الإيصال:"), 0, 0)
        grid.addWidget(self.voucher_number, 0, 1)
        grid.addWidget(QLabel("التاريخ:"), 0, 2)
        grid.addWidget(self.voucher_date, 0, 3)

        grid.addWidget(QLabel("الخزنة:"), 1, 0)
        grid.addWidget(self.cash_chests, 1, 1, 1, 3)

        grid.addWidget(QLabel("الحساب المدين:"), 2, 0)
        grid.addWidget(self.debit_account_input, 2, 1)
        grid.addWidget(self.debit_account, 2, 2, 1, 2)

        grid.addWidget(QLabel("المبلغ:"), 3, 0)
        grid.addWidget(self.amount, 3, 1, 1, 3)

        grid.addWidget(QLabel("نوع المستند:"), 4, 0)
        grid.addWidget(self.doc_type_combo, 4, 1, 1, 3)

        grid.addWidget(QLabel("رقم المستند:"), 5, 0)
        grid.addWidget(self.doc_number, 5, 1, 1, 3)

        grid.addWidget(QLabel("البيان:"), 6, 0)
        grid.addWidget(self.description, 6, 1, 1, 3)

        main_layout.addWidget(basic_group)

        # --- أزرار ---
        btn_layout = QHBoxLayout()
        self.new_btn = QPushButton("جديد")
        self.new_btn.clicked.connect(self.new_voucher)
        self.save_btn = QPushButton("حفظ")
        self.save_btn.clicked.connect(self.save_voucher)
        self.edit_btn = QPushButton("تعديل")
        self.edit_btn.clicked.connect(self.edit_voucher)
        self.delete_btn = QPushButton("حذف")
        self.delete_btn.clicked.connect(self.delete_voucher)
        for b in (self.new_btn, self.save_btn, self.edit_btn, self.delete_btn):
            btn_layout.addWidget(b)
        main_layout.addLayout(btn_layout)

        # --- مربع بحث ---
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("بحث:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث برقم الإيصال، التاريخ، نوع المستند، البيان...")
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # --- جدول ---
        self.voucher_table = QTableWidget(columnCount=9)
        self.voucher_table.setHorizontalHeaderLabels(
            ["ID", "رقم الإيصال", "التاريخ", "الخزنة", "الحساب المدين",
             "المبلغ", "نوع المستند", "رقم المستند", "البيان"]
        )
        self.voucher_table.setColumnHidden(0, True)
        self.voucher_table.cellClicked.connect(self.select_voucher)
        main_layout.addWidget(self.voucher_table)

    def load_data(self):
        """تحميل بيانات الخزن والحسابات"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                # الخزن من شجرة الحسابات (كود 111)
                self.cash_chests.clear()
                c.execute("""
                    SELECT id, acc_code, account_name_ar 
                    FROM accounts 
                    WHERE is_final = 1 AND is_active = 1
                    ORDER BY acc_code
                """)
                cash_accounts = c.fetchall()
                if not cash_accounts:
                    # إذا لم توجد حسابات، نضيف خيار افتراضي
                    self.cash_chests.addItem("لا توجد خزن", -1)
                else:
                    for acc_id, code, name in cash_accounts:
                        self.cash_chests.addItem(f"{code} - {name}", acc_id)

                # الحسابات (مدين) مع فلترة
                self.debit_account.clear()
                c.execute("SELECT id, acc_code, account_name_ar FROM accounts WHERE is_final=1 AND is_active=1 ORDER BY acc_code")
                accounts = c.fetchall()
                for acc_id, code, name in accounts:
                    self.debit_account.addItem(f"{code} - {name}", acc_id)

                completer = QCompleter([f"{code} - {name}" for _, code, name in accounts])
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                self.debit_account_input.setCompleter(completer)
                self.debit_account_input.textEdited.connect(self.filter_accounts)
                self.debit_account.currentIndexChanged.connect(self.update_account_input)

                # تحميل أنواع المستندات
                self.doc_type_combo.clear()
                # قائمة افتراضية لأنواع المستندات
                doc_types = [
                    (1, '01', 'فاتورة'),
                    (2, '02', 'إيصال'),
                    (3, '03', 'شيك'),
                    (4, '04', 'سند دفع'),
                    (5, '05', 'أمر صرف')
                ]
                for doc_id, code, name in doc_types:
                    self.doc_type_combo.addItem(f"{code} - {name}", doc_id)

            self.load_vouchers()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def filter_accounts(self, text):
        """فلترة الحسابات عند الكتابة في حقل البحث"""
        if not text:
            # إذا كان الحقل فارغاً، نعرض كل الحسابات
            self.load_accounts()
            return
            
        # نبحث في النص المعروض في الكمبوبوكس
        for i in range(self.debit_account.count()):
            if text.lower() in self.debit_account.itemText(i).lower():
                self.debit_account.setCurrentIndex(i)
                return
                
        # إذا لم نجد تطابقاً، نعرض أول عنصر
        if self.debit_account.count() > 0:
            self.debit_account.setCurrentIndex(0)

    def load_accounts(self):
        """إعادة تحميل كل الحسابات"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                self.debit_account.clear()
                c.execute("SELECT id, acc_code, account_name_ar FROM accounts WHERE is_final=1 AND is_active=1 ORDER BY acc_code")
                accounts = c.fetchall()
                for acc_id, code, name in accounts:
                    self.debit_account.addItem(f"{code} - {name}", acc_id)
        except sqlite3.Error as e:
            print("Error loading accounts:", e)
                
    def update_account_input(self, index):
        """تغيير النص عند اختيار حساب من الكمبوبوكس"""
        if index >= 0:
            self.debit_account_input.setText(self.debit_account.itemText(index))

    def load_vouchers(self):
        """تحميل الإيصالات السابقة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT cbt.id, cbt.transaction_number, cbt.transaction_date,
                        (SELECT account_name_ar FROM accounts WHERE id=cbt.cash_chest_id) as chest_name,
                        (SELECT account_name_ar FROM accounts WHERE id=(
                            SELECT account_id FROM transaction_details 
                            WHERE transaction_id=cbt.id AND debit>0 LIMIT 1
                        )) as debit_acc,
                        cbt.amount,
                        cbt.doc_type,
                        cbt.doc_number,
                        cbt.description
                    FROM cash_bank_transactions cbt
                    WHERE cbt.transaction_type = 'صرف نقدي'
                    ORDER BY transaction_date DESC
                """)

                self.all_rows = c.fetchall()  # نخزن نسخة كاملة
                self.populate_table(self.all_rows)
        except sqlite3.Error as e:
            # إذا كان الجدول غير موجود، ننشئه
            if "no such table" in str(e):
                self.create_table()
                self.all_rows = []
                self.populate_table(self.all_rows)
            else:
                QMessageBox.critical(self, "خطأ", str(e))

    def populate_table(self, rows):
        self.voucher_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val else "")
                self.voucher_table.setItem(r, c_idx, item)
                
        # تعديل عرض الأعمدة لتناسب المحتوى
        self.voucher_table.resizeColumnsToContents()

    def filter_table(self, text):
        if not text:
            self.populate_table(self.all_rows)
            return
        filtered = [row for row in self.all_rows if any(text.lower() in str(col).lower() for col in row)]
        self.populate_table(filtered)

    def select_voucher(self, row, column):
        """تحميل بيانات إيصال مختار للفورم"""
        try:
            self.current_voucher_id = int(self.voucher_table.item(row, 0).text())
            self.voucher_number.setText(self.voucher_table.item(row, 1).text())
            self.voucher_date.setDate(QDate.fromString(self.voucher_table.item(row, 2).text(), "yyyy-MM-dd"))
            
            # تحديد الخزنة
            chest_text = self.voucher_table.item(row, 3).text()
            for i in range(self.cash_chests.count()):
                if chest_text in self.cash_chests.itemText(i):
                    self.cash_chests.setCurrentIndex(i)
                    break
                    
            # تحديد الحساب المدين
            debit_text = self.voucher_table.item(row, 4).text()
            self.debit_account_input.setText(debit_text)
            for i in range(self.debit_account.count()):
                if debit_text in self.debit_account.itemText(i):
                    self.debit_account.setCurrentIndex(i)
                    break
                    
            self.amount.setText(self.voucher_table.item(row, 5).text())
            
            # تحديد نوع المستند
            doc_type_text = self.voucher_table.item(row, 6).text()
            for i in range(self.doc_type_combo.count()):
                if doc_type_text in self.doc_type_combo.itemText(i):
                    self.doc_type_combo.setCurrentIndex(i)
                    break
                    
            self.doc_number.setText(self.voucher_table.item(row, 7).text())
            self.description.setText(self.voucher_table.item(row, 8).text())
        except Exception as e:
            print("Error selecting voucher:", e)

    def new_voucher(self):
        self.current_voucher_id = None
        self.voucher_number.setText(self.generate_next_number())
        self.amount.clear()
        self.description.clear()
        self.doc_number.clear()
        self.voucher_date.setDate(QDate.currentDate())
        if self.cash_chests.count() > 0:
            self.cash_chests.setCurrentIndex(0)
        if self.debit_account.count() > 0:
            self.debit_account.setCurrentIndex(0)
        if self.doc_type_combo.count() > 0:
            self.doc_type_combo.setCurrentIndex(0)
        self.debit_account_input.clear()

    def generate_next_number(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT MAX(CAST(transaction_number AS INTEGER)) FROM cash_bank_transactions")
                res = c.fetchone()
                last_num = res[0] if res and res[0] is not None else 0
                return str(int(last_num) + 1)
        except Exception as e:
            print("Error in generate_next_number:", e)
            return "1"

    def save_voucher(self):
        try:
            amount = float(self.amount.text())
        except:
            QMessageBox.warning(self, "خطأ", "أدخل مبلغ صحيح")
            return

        if not self.cash_chests.currentData() or self.cash_chests.currentData() == -1:
            QMessageBox.warning(self, "خطأ", "يرجى اختيار الخزنة")
            return
            
        if not self.debit_account.currentData():
            QMessageBox.warning(self, "خطأ", "يرجى اختيار الحساب المدين")
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                if self.current_voucher_id:  # تعديل
                    c.execute("""
                        UPDATE cash_bank_transactions 
                        SET transaction_date=?, cash_chest_id=?, description=?, 
                            amount=?, doc_type=?, doc_number=?
                        WHERE id=?
                    """, (self.voucher_date.date().toString("yyyy-MM-dd"),
                          self.cash_chests.currentData(),
                          self.description.text(),
                          amount,
                          self.doc_type_combo.currentText(),
                          self.doc_number.text(),
                          self.current_voucher_id))
                else:  # جديد
                    c.execute("""
                        INSERT INTO cash_bank_transactions 
                        (transaction_number, transaction_date, cash_chest_id, 
                         transaction_type, description, amount, doc_type, doc_number)
                        VALUES (?, ?, ?, 'صرف نقدي', ?, ?, ?, ?)
                    """, (self.voucher_number.text(),
                          self.voucher_date.date().toString("yyyy-MM-dd"),
                          self.cash_chests.currentData(),
                          self.description.text(), amount,
                          self.doc_type_combo.currentText(), self.doc_number.text()))
                conn.commit()
            self.load_vouchers()
            self.new_voucher()
            QMessageBox.information(self, "تم", "تم حفظ الإيصال بنجاح")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def edit_voucher(self):
        if not self.current_voucher_id:
            QMessageBox.warning(self, "خطأ", "اختر إيصال للتعديل")
            return
        self.save_voucher()

    def delete_voucher(self):
        if not self.current_voucher_id:
            QMessageBox.warning(self, "خطأ", "اختر إيصال أولاً")
            return
            
        reply = QMessageBox.question(self, "تأكيد", "هل أنت متأكد من حذف هذا الإيصال؟",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    c = conn.cursor()
                    c.execute("DELETE FROM cash_bank_transactions WHERE id=?", (self.current_voucher_id,))
                    conn.commit()
                self.load_vouchers()
                self.new_voucher()
                QMessageBox.information(self, "تم", "تم حذف الإيصال بنجاح")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "خطأ", str(e))


def main():
    app = QApplication(sys.argv)
    win = CashPaymentVoucher()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
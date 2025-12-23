import os
import sys
import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QFrame, QTableWidget, QTableWidgetItem, QMessageBox, QComboBox,
    QFileDialog, QHeaderView, QGroupBox, QApplication, QDialog, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

# ==============================
# نافذة اختيار الحساب من الشجرة
# ==============================
class AccountTreeDialog(QDialog):
    def __init__(self, financials_db, account_type_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"اختيار حساب ({account_type_name})")
        self.resize(600, 700)
        self.selected_account = None
        self.financials_db = financials_db
        self.account_type_name = account_type_name

        layout = QVBoxLayout(self)
        
        # إضافة حقل البحث
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث باسم الحساب أو الكود...")
        self.search_input.textChanged.connect(self.filter_accounts)
        search_layout.addWidget(QLabel("بحث:"))
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["كود", "اسم الحساب", "النوع"])
        self.tree.setColumnWidth(0, 100)
        self.tree.setColumnWidth(1, 300)
        self.tree.setColumnWidth(2, 150)
        self.tree.itemDoubleClicked.connect(self.select_account)
        layout.addWidget(self.tree)

        # أزرار التحديد والإلغاء
        button_layout = QHBoxLayout()
        select_btn = QPushButton("تحديد")
        select_btn.clicked.connect(self.accept_selection)
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(select_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.all_accounts = []
        self.load_accounts()

    def load_accounts(self):
        try:
            conn = sqlite3.connect(self.financials_db)
            cur = conn.cursor()
            
            # خريطة لتطابق أسماء الأنواع بين الواجهة وقاعدة البيانات
            type_mapping = {
                "أصول": "الأصول",
                "التزامات": "الخصوم", 
                "حقوق ملكية": "حقوق الملكية",
                "إيرادات": "الإيرادات",
                "مصروفات": "المصروفات"
            }
            
            # الحصول على اسم النوع المقابل من قاعدة البيانات
            db_type_name = type_mapping.get(self.account_type_name, self.account_type_name)
            
            # البحث عن نوع الحساب في جدول account_types
            cur.execute("SELECT id, name_ar FROM account_types WHERE name_ar = ? AND is_active = 1", (db_type_name,))
            account_type = cur.fetchone()
            
            if account_type:
                account_type_id, account_type_name_db = account_type
                print(f"تم العثور على نوع الحساب: {account_type_name_db} (ID: {account_type_id})")
                
                # جلب الحسابات من هذا النوع
                cur.execute("""
                    SELECT a.id, a.acc_code, a.account_name_ar, t.name_ar as type_name
                    FROM accounts a
                    JOIN account_types t ON a.account_type_id = t.id
                    WHERE a.is_active = 1 AND a.account_type_id = ?
                    ORDER BY a.acc_code
                """, (account_type_id,))
                
                self.all_accounts = cur.fetchall()
            else:
                print(f"لم يتم العثور على نوع الحساب '{db_type_name}' في جدول account_types")
                # جلب جميع الحسابات النشطة
                cur.execute("""
                    SELECT a.id, a.acc_code, a.account_name_ar, t.name_ar as type_name
                    FROM accounts a
                    JOIN account_types t ON a.account_type_id = t.id
                    WHERE a.is_active = 1
                    ORDER BY a.acc_code
                """)
                self.all_accounts = cur.fetchall()
            
            conn.close()
            
            print(f"تم تحميل {len(self.all_accounts)} حساب من نوع '{self.account_type_name}'")
            self.populate_tree(self.all_accounts)
            
        except sqlite3.Error as e:
            print(f"خطأ في تحميل الحسابات: {str(e)}")
            QMessageBox.warning(self, "خطأ", f"حدث خطأ في تحميل الحسابات: {str(e)}")

    def populate_tree(self, accounts):
        self.tree.clear()
        for account in accounts:
            if len(account) >= 4:
                account_id, acc_code, account_name, type_name = account
                item = QTreeWidgetItem([acc_code, account_name, type_name])
                item.setData(0, Qt.UserRole, account_id)
                self.tree.addTopLevelItem(item)
            else:
                print(f"بيانات حساب غير مكتملة: {account}")

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


# ==============================
# واجهة إدارة مجموعات الأصناف
# ==============================
class ItemCategoriesUI(QWidget):
    def __init__(self, inventory_db, financials_db):
        super().__init__()
        self.inventory_db = inventory_db
        self.financials_db = financials_db
        self.setWindowTitle("إدارة مجموعات الأصناف - مع حسابات مستقلة")
        self.resize(1500, 1000)
        self.current_category_id = None
        self.account_mappings = {}  # لتخزين ربط الحسابات

        self.setup_ui()
        self.load_categories()
        self.load_parent_categories()

    def setup_ui(self):
        self.setFont(QFont("Arial", 11))

        main_layout = QVBoxLayout(self)

        # تبويب للتنقل بين البيانات والحسابات
        self.tab_widget = QTabWidget()
        
        # تبويب البيانات الأساسية
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # مجموعة بيانات المجموعة
        form_group = QGroupBox("بيانات المجموعة")
        form_layout = QVBoxLayout(form_group)

        # الحقول الأساسية
        row1 = QHBoxLayout()
        self.code_input = QLineEdit()
        self.name_ar_input = QLineEdit()
        self.name_en_input = QLineEdit()
        self.parent_input = QComboBox()

        row1.addWidget(QLabel("الكود:"))
        row1.addWidget(self.code_input)
        row1.addWidget(QLabel("الاسم (ع):"))
        row1.addWidget(self.name_ar_input)
        row1.addWidget(QLabel("الاسم (En):"))
        row1.addWidget(self.name_en_input)
        row1.addWidget(QLabel("الفئة الأب:"))
        row1.addWidget(self.parent_input)

        form_layout.addLayout(row1)

        # حقل الوصف
        desc_layout = QHBoxLayout()
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("الوصف (اختياري)")
        desc_layout.addWidget(QLabel("الوصف:"))
        desc_layout.addWidget(self.desc_input)
        form_layout.addLayout(desc_layout)

        basic_layout.addWidget(form_group)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        buttons = [
            ("إضافة", self.add_category, "#4CAF50"),
            ("تعديل", self.update_category, "#2196F3"),
            ("حذف", self.delete_category, "#f44336"),
            ("مسح", self.clear_form, "#607D8B"),
            ("تحديث", self.load_categories, "#9C27B0")
        ]

        for text, handler, color in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(f"background-color: {color}; color: white; padding: 8px;")
            btn.clicked.connect(handler)
            button_layout.addWidget(btn)

        basic_layout.addLayout(button_layout)

        # ==============================
        # جدول عرض المجموعات
        # ==============================
        table_group = QGroupBox("قائمة المجموعات")
        table_layout = QVBoxLayout(table_group)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["الكود", "الاسم", "الفئة الأب", "الوصف", "معرف", "الحسابات"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellClicked.connect(self.on_row_selected)
        table_layout.addWidget(self.table)

        basic_layout.addWidget(table_group)
        
        # تبويب الحسابات المستقلة
        accounts_tab = QWidget()
        accounts_layout = QVBoxLayout(accounts_tab)
        
        # مجموعة الحسابات المستقلة
        independent_accounts_group = QGroupBox("الحسابات المستقلة للمجموعة")
        independent_layout = QVBoxLayout(independent_accounts_group)
        
        self.account_fields = {}
        # أنواع الحسابات المطلوبة لكل مجموعة مخازن
        account_types = [
            ("حساب المخزون", "مخزون"),
            ("حساب المشتريات", "مشتريات"),
            ("حساب المبيعات", "مبيعات"),
            ("حساب مردودات المشتريات", "مردودات مشتريات"),
            ("حساب مردودات المبيعات", "مردودات مبيعات"),
            ("حساب مسموحات المشتريات", "مسموحات مشتريات"),
            ("حساب مسموحات المبيعات", "مسموحات مبيعات"),
            ("حساب تكلفة المبيعات", "تكلفة مبيعات"),
            ("حساب مصاريف النقل", "مصاريف نقل"),
            ("حساب خصم مكتسب", "خصم مكتسب"),
            ("حساب خصم مسموح", "خصم مسموح")
        ]
        
        for display_name, account_key in account_types:
            row = QHBoxLayout()
            lbl = QLabel(display_name + ":")
            edit = QLineEdit()
            edit.setReadOnly(True)
            btn = QPushButton("...")
            btn.setFixedWidth(40)
            btn.clicked.connect(lambda _, tp=display_name, e=edit: self.open_account_tree(tp, e))
            
            # زر إزالة الربط
            remove_btn = QPushButton("×")
            remove_btn.setFixedWidth(30)
            remove_btn.setStyleSheet("color: red; font-weight: bold;")
            remove_btn.clicked.connect(lambda _, e=edit, k=account_key: self.clear_account_field(e, k))
            
            row.addWidget(lbl)
            row.addWidget(edit)
            row.addWidget(btn)
            row.addWidget(remove_btn)
            independent_layout.addLayout(row)
            self.account_fields[account_key] = edit

        accounts_layout.addWidget(independent_accounts_group)
        
        # إضافة التبويبات
        self.tab_widget.addTab(basic_tab, "البيانات الأساسية")
        self.tab_widget.addTab(accounts_tab, "الحسابات المستقلة")
        
        main_layout.addWidget(self.tab_widget)

    def clear_account_field(self, field, account_key):
        """مسح حقل حساب معين"""
        field.clear()
        if account_key in self.account_mappings:
            del self.account_mappings[account_key]

    def load_parent_categories(self):
        """تحميل الفئات الأب للقائمة المنسدلة"""
        self.parent_input.clear()
        self.parent_input.addItem("بدون فئة أب", None)
        
        try:
            conn = sqlite3.connect(self.inventory_db)
            cur = conn.cursor()
            
            # التحقق من وجود جدول item_categories
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='item_categories'")
            if not cur.fetchone():
                QMessageBox.warning(self, "تحذير", "جدول item_categories غير موجود في قاعدة البيانات")
                return
            
            cur.execute("SELECT id, code, name_ar FROM item_categories WHERE is_active = 1 ORDER BY name_ar")
            categories = cur.fetchall()
            
            for cat_id, code, name_ar in categories:
                self.parent_input.addItem(f"{name_ar} ({code})", cat_id)
                
        except sqlite3.Error as e:
            QMessageBox.warning(self, "تحذير", f"خطأ في تحميل الفئات: {str(e)}")
        finally:
            if conn:
                conn.close()

    def open_account_tree(self, account_type, field):
        dlg = AccountTreeDialog(self.financials_db, account_type, self)
        if dlg.exec_() == QDialog.Accepted and dlg.selected_account:
            acc = dlg.selected_account
            field.setText(f"[{acc['code']}] {acc['name']}")
            # حفظ الربط - استخدام اسم الحساب كـ key
            for key, field_obj in self.account_fields.items():
                if field_obj == field:
                    self.account_mappings[key] = acc['id']
                    break

    def load_categories(self):
        self.table.setRowCount(0)
        try:
            conn = sqlite3.connect(self.inventory_db)
            cur = conn.cursor()
            
            # التحقق من وجود جدول item_categories
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='item_categories'")
            if not cur.fetchone():
                QMessageBox.warning(self, "تحذير", "جدول item_categories غير موجود في قاعدة البيانات")
                return
            
            cur.execute("""
                SELECT c.id, c.code, c.name_ar, c.description, 
                       p.name_ar as parent_name,
                       (SELECT COUNT(*) FROM category_accounts WHERE category_id = c.id) as accounts_count
                FROM item_categories c
                LEFT JOIN item_categories p ON c.parent_id = p.id
                WHERE c.is_active = 1
                ORDER BY c.code
            """)
            rows = cur.fetchall()
            
            for row in rows:
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)
                
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(row[1])))  # الكود
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(row[2])))  # الاسم
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(row[4] or "—")))  # الفئة الأب
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(row[3] or "")))  # الوصف
                self.table.setItem(row_idx, 4, QTableWidgetItem(str(row[0])))  # المعرف
                self.table.setItem(row_idx, 5, QTableWidgetItem(f"{row[5]} حساب" if row[5] > 0 else "بدون حسابات"))  # عدد الحسابات

        except sqlite3.Error as e:
            QMessageBox.warning(self, "تحذير", f"خطأ في تحميل البيانات: {str(e)}")
        finally:
            if conn:
                conn.close()

    def on_row_selected(self, row, col):
        """عند اختيار صف من الجدول"""
        if row >= 0:
            try:
                self.current_category_id = int(self.table.item(row, 4).text())
                self.code_input.setText(self.table.item(row, 0).text())
                self.name_ar_input.setText(self.table.item(row, 1).text())
                self.desc_input.setText(self.table.item(row, 3).text() if self.table.item(row, 3) else "")
                
                # تحميل بيانات الحسابات المرتبطة لهذه الفئة
                self.load_account_links()
                
                # التبديل إلى تبويب الحسابات
                self.tab_widget.setCurrentIndex(1)
                
            except Exception as e:
                print(f"خطأ في تحميل بيانات الصف: {e}")

    def load_account_links(self):
        """تحميل الحسابات المرتبطة بالفئة المحددة"""
        if not self.current_category_id:
            return
            
        try:
            conn = sqlite3.connect(self.inventory_db)
            cur = conn.cursor()
            
            # إنشاء جدول category_accounts إذا لم يكن موجوداً
            cur.execute("""
                CREATE TABLE IF NOT EXISTS category_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER,
                    account_type TEXT,
                    account_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES item_categories (id)
                )
            """)
            
            # جلب الحسابات المرتبطة
            cur.execute("""
                SELECT account_type, account_id 
                FROM category_accounts 
                WHERE category_id = ?
            """, (self.current_category_id,))
            
            accounts = cur.fetchall()
            
            # مسح الحقول الحالية
            for field in self.account_fields.values():
                field.clear()
            self.account_mappings.clear()
            
            # تعبئة الحقول بالبيانات
            for account_type, account_id in accounts:
                if account_type in self.account_fields:
                    try:
                        fin_conn = sqlite3.connect(self.financials_db)
                        fin_cur = fin_conn.cursor()
                        fin_cur.execute("SELECT acc_code, account_name_ar FROM accounts WHERE id = ?", (account_id,))
                        account_data = fin_cur.fetchone()
                        if account_data:
                            self.account_fields[account_type].setText(f"[{account_data[0]}] {account_data[1]}")
                            self.account_mappings[account_type] = account_id
                        fin_conn.close()
                    except Exception as e:
                        print(f"خطأ في تحميل بيانات الحساب: {e}")
            
        except sqlite3.Error as e:
            print(f"خطأ في تحميل الحسابات المرتبطة: {str(e)}")
        finally:
            if conn:
                conn.close()

    def clear_form(self):
        """مسح جميع الحقول"""
        self.code_input.clear()
        self.name_ar_input.clear()
        self.name_en_input.clear()
        self.desc_input.clear()
        self.parent_input.setCurrentIndex(0)
        for field in self.account_fields.values():
            field.clear()
        self.current_category_id = None
        self.account_mappings.clear()
        self.tab_widget.setCurrentIndex(0)

    def add_category(self):
        """إضافة فئة جديدة"""
        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        
        if not code or not name_ar:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال الكود والاسم العربي")
            return
            
        try:
            conn = sqlite3.connect(self.inventory_db)
            cur = conn.cursor()
            
            # التحقق من عدم تكرار الكود
            cur.execute("SELECT id FROM item_categories WHERE code = ?", (code,))
            if cur.fetchone():
                QMessageBox.warning(self, "تحذير", "الكود موجود مسبقاً")
                return
            
            parent_id = self.parent_input.currentData()
            
            cur.execute("""
                INSERT INTO item_categories (code, name_ar, name_en, description, parent_id, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (code, name_ar, self.name_en_input.text().strip(), 
                 self.desc_input.text().strip(), parent_id))
            
            category_id = cur.lastrowid
            
            # حفظ الحسابات المرتبطة إذا وجدت
            if self.account_mappings:
                for account_type, account_id in self.account_mappings.items():
                    cur.execute("""
                        INSERT INTO category_accounts (category_id, account_type, account_id)
                        VALUES (?, ?, ?)
                    """, (category_id, account_type, account_id))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "نجاح", "تم إضافة الفئة بنجاح")
            self.load_categories()
            self.clear_form()
            
        except sqlite3.Error as e:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء الإضافة: {str(e)}")

    def update_category(self):
        """تعديل الفئة المحددة"""
        if not self.current_category_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار فئة للتعديل")
            return
            
        code = self.code_input.text().strip()
        name_ar = self.name_ar_input.text().strip()
        
        if not code or not name_ar:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال الكود والاسم العربي")
            return
            
        try:
            conn = sqlite3.connect(self.inventory_db)
            cur = conn.cursor()
            
            # التحقق من عدم تكرار الكود (باستثناء الفئة الحالية)
            cur.execute("SELECT id FROM item_categories WHERE code = ? AND id != ?", 
                       (code, self.current_category_id))
            if cur.fetchone():
                QMessageBox.warning(self, "تحذير", "الكود موجود مسبقاً")
                return
            
            parent_id = self.parent_input.currentData()
            
            cur.execute("""
                UPDATE item_categories 
                SET code = ?, name_ar = ?, name_en = ?, description = ?, parent_id = ?
                WHERE id = ?
            """, (code, name_ar, self.name_en_input.text().strip(), 
                 self.desc_input.text().strip(), parent_id, self.current_category_id))
            
            # تحديث الحسابات المرتبطة
            cur.execute("DELETE FROM category_accounts WHERE category_id = ?", 
                       (self.current_category_id,))
            
            for account_type, account_id in self.account_mappings.items():
                cur.execute("""
                    INSERT INTO category_accounts (category_id, account_type, account_id)
                    VALUES (?, ?, ?)
                """, (self.current_category_id, account_type, account_id))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "نجاح", "تم تعديل الفئة بنجاح")
            self.load_categories()
            
        except sqlite3.Error as e:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء التعديل: {str(e)}")

    def delete_category(self):
        """حذف الفئة المحددة"""
        if not self.current_category_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار فئة للحذف")
            return
            
        reply = QMessageBox.question(self, "تأكيد", 
                                    "هل أنت متأكد من حذف هذه الفئة؟",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(self.inventory_db)
                cur = conn.cursor()
                
                # حذف نهائي أو تعطيل (حسب متطلبات النظام)
                cur.execute("UPDATE item_categories SET is_active = 0 WHERE id = ?", 
                           (self.current_category_id,))
                
                # حذف الحسابات المرتبطة
                cur.execute("DELETE FROM category_accounts WHERE category_id = ?", 
                           (self.current_category_id,))
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "نجاح", "تم حذف الفئة بنجاح")
                self.load_categories()
                self.clear_form()
                
            except sqlite3.Error as e:
                QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء الحذف: {str(e)}")


# ==============================
# تشغيل التطبيق
# ==============================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    inventory_db = os.path.join(project_root, "database", "inventory.db")
    financials_db = os.path.join(project_root, "database", "financials.db")

    # إذا كانت قاعدة البيانات المالية غير موجودة، استخدم inventory.db
    if not os.path.exists(financials_db):
        financials_db = inventory_db

    window = ItemCategoriesUI(inventory_db, financials_db)
    window.show()
    sys.exit(app.exec_())
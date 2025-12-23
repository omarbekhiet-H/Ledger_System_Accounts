# ui/admin/company_settings_ui.py

import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QGroupBox, QGridLayout, QApplication, QStyle,
    QLineEdit, QComboBox, QTabWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# --- تصحيح مسار المشروع الجذر ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# --- استيراد الوحدات المطلوبة ---
# نستورد هذه فقط لاستخدامها في كود الاختبار المستقل
from ui.styles.report_styles import ReportStyles

from database.manager.admin.company_manager import CompanySettingsManager
from database.manager.account_manager import AccountManager
from database.db_connection import get_financials_db_connection

class CompanySettingsWindow(QWidget):
    # ====================================================================
    # الخطوة 1: تعديل دالة __init__ لتستقبل المدراء كوسائط
    # ====================================================================
    #def __init__(self, account_manager, lookup_manager, **kwargs):
    def __init__(self, settings_manager, account_manager, parent=None):
        super().__init__(parent)
        ReportStyles.apply_style(self, 'full')

        # ====================================================================
        # الخطوة 2: استخدام المدراء الذين تم تمريرهم من النافذة الرئيسية
        # ====================================================================
        self.settings_manager = settings_manager  # lookup_manager هو المسؤول عن الإعدادات
        self.account_manager = account_manager
        
        self.setWindowTitle("إعدادات الشركة الشاملة")
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.populate_all_comboboxes()
        self.load_all_settings()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # إنشاء وإضافة التبويبات
        self.create_info_tab()
        self.create_accounting_tab()
        self.create_tax_tab()
        self.create_closing_tab()

        # زر الحفظ
        self.save_btn = QPushButton("حفظ جميع الإعدادات")
        self.save_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.save_btn.clicked.connect(self.save_all_settings)
        main_layout.addWidget(self.save_btn, 0, Qt.AlignLeft)

    def create_info_tab(self):
        """إنشاء تبويب معلومات الشركة."""
        tab = QWidget()
        layout = QGridLayout(tab)
        
        self.settings_widgets = {} # قاموس لتخزين كل عناصر الإدخال

        # تعريف الحقول
        fields = {
            'company_name_ar': "اسم الشركة (عربي):", 'company_name_en': "اسم الشركة (إنجليزي):",
            'company_address': "العنوان:", 'company_phone': "الهاتف:",
            'company_email': "البريد الإلكتروني:", 'company_website': "الموقع الإلكتروني:",
            'company_tax_id': "الرقم الضريبي:", 'company_cr_number': "رقم السجل التجاري:"
        }
        
        row = 0
        for key, label in fields.items():
            self.settings_widgets[key] = QLineEdit()
            layout.addWidget(QLabel(label), row, 0)
            layout.addWidget(self.settings_widgets[key], row, 1)
            row += 1
            
        layout.setRowStretch(row, 1)
        self.tabs.addTab(tab, "معلومات الشركة")

    def create_accounting_tab(self):
        """إنشاء تبويب الإعدادات المحاسبية."""
        tab = QWidget()
        layout = QGridLayout(tab)

        # تعريف الحقول
        fields = {
            'retained_earnings_account_id': "حساب الأرباح المحتجزة:",
            'income_summary_account_id': "حساب ملخص الدخل:",
            'default_cash_chest_id': "حساب الصندوق الافتراضي:",
            'default_bank_account_id': "حساب البنك الافتراضي:"
        }
        
        row = 0
        for key, label in fields.items():
            self.settings_widgets[key] = QComboBox()
            layout.addWidget(QLabel(label), row, 0)
            layout.addWidget(self.settings_widgets[key], row, 1)
            row += 1

        layout.setRowStretch(row, 1)
        self.tabs.addTab(tab, "الإعدادات المحاسبية")

    def create_tax_tab(self):
        """إنشاء تبويب إعدادات الضرائب."""
        tab = QWidget()
        layout = QGridLayout(tab)

        self.settings_widgets['income_tax_rate'] = QLineEdit()
        self.settings_widgets['income_tax_account_id'] = QComboBox()
        self.settings_widgets['tax_payable_account_id'] = QComboBox()

        layout.addWidget(QLabel("نسبة ضريبة الدخل (%):"), 0, 0)
        layout.addWidget(self.settings_widgets['income_tax_rate'], 0, 1)
        layout.addWidget(QLabel("حساب مصروف ضريبة الدخل:"), 1, 0)
        layout.addWidget(self.settings_widgets['income_tax_account_id'], 1, 1)
        layout.addWidget(QLabel("حساب ضرائب مستحقة الدفع:"), 2, 0)
        layout.addWidget(self.settings_widgets['tax_payable_account_id'], 2, 1)

        layout.setRowStretch(3, 1)
        self.tabs.addTab(tab, "إعدادات الضرائب")

    def create_closing_tab(self):
        """إنشاء تبويب إعدادات الإقفال السنوي."""
        tab = QWidget()
        layout = QGridLayout(tab)

        self.settings_widgets['legal_reserve_rate'] = QLineEdit()
        self.settings_widgets['legal_reserve_account_id'] = QComboBox()

        layout.addWidget(QLabel("نسبة الاحتياطي القانوني (%):"), 0, 0)
        layout.addWidget(self.settings_widgets['legal_reserve_rate'], 0, 1)
        layout.addWidget(QLabel("حساب الاحتياطي القانوني:"), 1, 0)
        layout.addWidget(self.settings_widgets['legal_reserve_account_id'], 1, 1)

        layout.setRowStretch(2, 1)
        self.tabs.addTab(tab, "إعدادات الإقفال")

    def populate_all_comboboxes(self):
        """تعبئة كل القوائم المنسدلة بالبيانات المناسبة."""
        try:
            equity_accounts = self.account_manager.get_accounts_by_type_code('EQUITY')
            expense_accounts = self.account_manager.get_accounts_by_type_code('EXPENSE')
            liability_accounts = self.account_manager.get_accounts_by_type_code('LIABILITY')
            
            self.populate_combo(self.settings_widgets['retained_earnings_account_id'], equity_accounts)
            self.populate_combo(self.settings_widgets['income_summary_account_id'], equity_accounts)
            self.populate_combo(self.settings_widgets['legal_reserve_account_id'], equity_accounts)
            self.populate_combo(self.settings_widgets['income_tax_account_id'], expense_accounts)
            self.populate_combo(self.settings_widgets['tax_payable_account_id'], liability_accounts)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل بيانات الحسابات: {e}")

    def populate_combo(self, combo, accounts):
        """دالة مساعدة لتعبئة قائمة منسدلة بالحسابات."""
        combo.clear()
        combo.addItem("اختر حساب...", None)
        if accounts:
            for acc in accounts:
                combo.addItem(f"{acc['acc_code']} - {acc['account_name_ar']}", acc['id'])

    def load_all_settings(self):
        """تحميل كل الإعدادات من قاعدة البيانات وعرضها."""
        try:
            settings = self.settings_manager.get_all_settings()
            for key, widget in self.settings_widgets.items():
                value = settings.get(key)
                if isinstance(widget, QLineEdit):
                    widget.setText(str(value) if value is not None else '')
                elif isinstance(widget, QComboBox):
                    if value is not None:
                        # تأكد من أن القيمة عدد صحيح قبل البحث
                        try:
                            index = widget.findData(int(value))
                            if index != -1:
                                widget.setCurrentIndex(index)
                        except (ValueError, TypeError):
                            # تجاهل القيم غير الصحيحة
                            pass
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل الإعدادات: {e}")

    def save_all_settings(self):
        """جمع كل البيانات من الواجهة وحفظها."""
        settings_to_save = {}
        for key, widget in self.settings_widgets.items():
            value = None
            value_type = 'string' # افتراضي
            if isinstance(widget, QLineEdit):
                value = widget.text()
                value_type = 'string'
            elif isinstance(widget, QComboBox):
                value = widget.currentData()
                value_type = 'integer'
            
            # تأكد من أن القيمة ليست None قبل إضافتها
            if value is not None:
                settings_to_save[key] = {'value': value, 'type': value_type}
        
        try:
            success = self.settings_manager.save_settings(settings_to_save)
            if success:
                QMessageBox.information(self, "نجاح", "تم حفظ جميع الإعدادات بنجاح.")
            else:
                QMessageBox.warning(self, "فشل", "فشل حفظ الإعدادات. قد تكون هناك مشكلة في الاتصال بقاعدة البيانات.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ فادح", f"حدث خطأ أثناء الحفظ: {e}")

# ====================================================================
# الخطوة 3: تحديث كود التشغيل المستقل للاختبار
# ====================================================================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # عند الاختبار المستقل، نحن بحاجة لإنشاء المدراء يدوياً
    test_account_manager = AccountManager(get_financials_db_connection)
    # نفترض أن CompanySettingsManager هو المسؤول عن الإعدادات
    test_settings_manager = CompanySettingsManager(get_financials_db_connection)

    # إنشاء وعرض النافذة، مع تمرير المدراء المؤقتين لها
    window = CompanySettingsWindow(
        account_manager=test_account_manager, 
        lookup_manager=test_settings_manager
    )
    window.show()
    sys.exit(app.exec_())

# ui/financial/closing_steps_dialog.py

import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QLineEdit, QCheckBox, QFormLayout, QStyle
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ClosingStepsDialog(QDialog):
    def __init__(self, year_id, year_name, end_date, journal_manager, settings_manager, parent=None):
        super().__init__(parent)
        self.year_id = year_id
        self.year_name = year_name
        self.end_date = end_date
        self.journal_manager = journal_manager
        self.settings_manager = settings_manager

        self.setWindowTitle(f"معالج إقفال السنة المالية: {year_name}")
        self.setMinimumWidth(500)
        self.setLayoutDirection(Qt.RightToLeft)

        self.pre_tax_profit = 0.0
        self.tax_amount = 0.0
        self.reserve_amount = 0.0
        self.net_profit_after_tax = 0.0

        self.init_ui()
        self.start_step_1()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.profit_label = QLabel("يتم الآن حساب الربح قبل الضريبة...")
        self.tax_checkbox = QCheckBox("حساب وتكوين قيد ضريبة الدخل")
        self.tax_rate_label = QLabel("نسبة الضريبة (%):")
        self.tax_rate_value = QLabel("0.0")
        self.tax_amount_label = QLabel("قيمة الضريبة:")
        self.tax_amount_value = QLabel("0.0")

        self.reserve_checkbox = QCheckBox("حساب وتكوين قيد الاحتياطي القانوني")
        self.reserve_rate_label = QLabel("نسبة الاحتياطي (%):")
        self.reserve_rate_value = QLabel("10.0") # يمكن جلبها من الإعدادات
        self.reserve_amount_label = QLabel("قيمة الاحتياطي:")
        self.reserve_amount_value = QLabel("0.0")

        self.final_profit_label = QLabel("صافي الربح النهائي (للترحيل):")
        self.final_profit_value = QLabel("0.0")

        # إضافة العناصر إلى التخطيط مع إخفائها مبدئياً
        self.form_layout.addRow(self.profit_label)
        self.form_layout.addRow(self.tax_checkbox)
        self.form_layout.addRow(self.tax_rate_label, self.tax_rate_value)
        self.form_layout.addRow(self.tax_amount_label, self.tax_amount_value)
        self.form_layout.addRow(self.reserve_checkbox)
        self.form_layout.addRow(self.reserve_rate_label, self.reserve_rate_value)
        self.form_layout.addRow(self.reserve_amount_label, self.reserve_amount_value)
        self.form_layout.addRow(self.final_profit_label, self.final_profit_value)

        self.main_layout.addLayout(self.form_layout)

        # أزرار التحكم
        self.buttons_layout = QHBoxLayout()
        self.execute_button = QPushButton("تنفيذ الإقفال النهائي")
        self.cancel_button = QPushButton("إلغاء")
        self.buttons_layout.addWidget(self.execute_button)
        self.buttons_layout.addWidget(self.cancel_button)
        self.main_layout.addLayout(self.buttons_layout)

        self.execute_button.clicked.connect(self.execute_final_closing)
        self.cancel_button.clicked.connect(self.reject)
        
        # ربط الأحداث
        self.tax_checkbox.stateChanged.connect(self.update_calculations)
        self.reserve_checkbox.stateChanged.connect(self.update_calculations)

    def start_step_1(self):
        """الخطوة الأولى: حساب الربح قبل الضريبة وعرضه."""
        self.pre_tax_profit = self.journal_manager.calculate_net_income(self.end_date)
        self.profit_label.setText(f"تم حساب الربح قبل الضريبة: <b>{self.pre_tax_profit:,.2f}</b>")
        
        # جلب نسبة الضريبة من الإعدادات
        tax_rate = self.settings_manager.get_setting('income_tax_rate', 0.0)
        self.tax_rate_value.setText(f"{tax_rate:.2f}%")
        
        self.update_calculations()

    def update_calculations(self):
        """تحديث الحسابات عند تغيير أي خيار."""
        # حساب الضريبة
        if self.tax_checkbox.isChecked():
            tax_rate = float(self.tax_rate_value.text().replace('%', '')) / 100
            self.tax_amount = self.pre_tax_profit * tax_rate if self.pre_tax_profit > 0 else 0.0
            self.net_profit_after_tax = self.pre_tax_profit - self.tax_amount
        else:
            self.tax_amount = 0.0
            self.net_profit_after_tax = self.pre_tax_profit

        self.tax_amount_value.setText(f"<b>{self.tax_amount:,.2f}</b>")

        # حساب الاحتياطي
        if self.reserve_checkbox.isChecked():
            reserve_rate = float(self.reserve_rate_value.text().replace('%', '')) / 100
            # الاحتياطي يحسب من صافي الربح بعد الضريبة
            self.reserve_amount = self.net_profit_after_tax * reserve_rate if self.net_profit_after_tax > 0 else 0.0
        else:
            self.reserve_amount = 0.0
        
        self.reserve_amount_value.setText(f"<b>{self.reserve_amount:,.2f}</b>")

        # حساب صافي الربح النهائي
        final_profit = self.net_profit_after_tax - self.reserve_amount
        self.final_profit_value.setText(f"<b style='color:green;'>{final_profit:,.2f}</b>")

    def execute_final_closing(self):
        """تنفيذ عملية الإقفال النهائية بالخيارات المحددة."""
        closing_options = {
            'create_tax_entry': self.tax_checkbox.isChecked(),
            'create_reserve_entry': self.reserve_checkbox.isChecked()
        }
        
        success, message = self.journal_manager.create_year_end_closing_entry(
            self.year_id, 
            self.end_date,
            closing_options
        )

        if success:
            QMessageBox.information(self, "نجاح", f"تم إقفال السنة المالية '{self.year_name}' بنجاح.\n{message}")
            self.accept() # لإغلاق النافذة بنجاح
        else:
            QMessageBox.critical(self, "فشل الإقفال", f"فشل إقفال السنة المالية.\nالسبب: {message}")

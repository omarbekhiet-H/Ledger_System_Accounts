# ui/admin/NEWaudit_window.py

import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QComboBox, QLineEdit,
                             QLabel, QMessageBox, QHeaderView, QGroupBox, QDateEdit)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

# إضافة المسار للوحدات المحلية
sys.path.append('..')

from database.manager.admin.NEWaudit_manager import NEWAuditManager

class AuditWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.audit_manager = NEWAuditManager()
        self.audit_manager.init_table()
        self.initUI()
        self.load_styles() # تحميل التنسيقات
        
    def initUI(self):
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle("سجلات المراجعة والتدقيق")
        self.setGeometry(100, 100, 1200, 700)
        
        layout = QVBoxLayout()
        
        # مجموعة عناصر التحكم
        control_group = QGroupBox("تصفية سجلات التدقيق")
        control_layout = QVBoxLayout()
        
        # عناصر التصفية
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("بحث:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث في الإجراءات أو التفاصيل...")
        self.search_input.textChanged.connect(self.filter_logs)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addWidget(QLabel("الكيان:"))
        self.entity_combo = QComboBox()
        self.entity_combo.addItem("جميع الكيانات")
        self.entity_combo.currentTextChanged.connect(self.filter_logs)
        filter_layout.addWidget(self.entity_combo)
        
        filter_layout.addWidget(QLabel("من تاريخ:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-7))
        self.from_date.setCalendarPopup(True)
        self.from_date.dateChanged.connect(self.filter_logs)
        filter_layout.addWidget(self.from_date)
        
        filter_layout.addWidget(QLabel("إلى تاريخ:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        self.to_date.dateChanged.connect(self.filter_logs)
        filter_layout.addWidget(self.to_date)
        
        control_layout.addLayout(filter_layout)
        
        # أزرار التحميل والتصدير
        button_layout = QHBoxLayout()
        
        load_btn = QPushButton("تحميل السجلات")
        load_btn.clicked.connect(self.load_audit_logs)
        button_layout.addWidget(load_btn)
        
        export_btn = QPushButton("تصدير إلى Excel")
        export_btn.clicked.connect(self.export_to_excel)
        button_layout.addWidget(export_btn)
        
        clear_btn = QPushButton("مسح السجلات القديمة")
        clear_btn.clicked.connect(self.clear_old_logs)
        button_layout.addWidget(clear_btn)

        button_layout.addStretch(1) # لإضافة مسافة مرنة

        close_btn = QPushButton("إغلاق")
        close_btn.setObjectName("deleteButton") # لتطبيق اللون الأحمر
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        control_layout.addLayout(button_layout)
        control_group.setLayout(control_layout)
        
        # مجموعة عرض السجلات
        logs_group = QGroupBox("سجلات التدقيق")
        logs_layout = QVBoxLayout()
        
        # جدول سجلات التدقيق
        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(8)
        self.audit_table.setHorizontalHeaderLabels([
            "ID", "المستخدم", "الإجراء", "الكيان", "معرف الكيان", "التفاصيل", "عنوان IP", "التاريخ والوقت"
        ])
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.audit_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        self.audit_table.setColumnWidth(0, 50)
        self.audit_table.setColumnWidth(1, 100)
        self.audit_table.setColumnWidth(2, 150)
        self.audit_table.setColumnWidth(3, 100)
        self.audit_table.setColumnWidth(4, 80)
        self.audit_table.setColumnWidth(5, 250)
        self.audit_table.setColumnWidth(6, 120)
        self.audit_table.setColumnWidth(7, 150)
        
        logs_layout.addWidget(self.audit_table)
        
        # معلومات السجل المحدد
        detail_layout = QHBoxLayout()
        detail_layout.addWidget(QLabel("التفاصيل الكاملة:"))
        self.detail_text = QLineEdit()
        self.detail_text.setReadOnly(True)
        detail_layout.addWidget(self.detail_text)
        
        logs_layout.addLayout(detail_layout)
        logs_group.setLayout(logs_layout)
        
        layout.addWidget(control_group)
        layout.addWidget(logs_group)
        
        self.setLayout(layout)
        
        self.audit_table.itemSelectionChanged.connect(self.show_log_details)
        
        self.load_audit_logs()
        self.load_entities()

    def load_styles(self):
        """تحميل وتطبيق ملف التنسيق QSS"""
        try:
            # تحديد المسار النسبي لملف التنسيق
            style_path = os.path.join(os.path.dirname(__file__), '..', 'styles', 'styles.qss')
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Error loading QSS file: {e}")

    def load_audit_logs(self):
        """تحميل سجلات التدقيق"""
        self.all_logs = self.audit_manager.get_all(limit=500)
        self.filter_logs()
    
    def load_entities(self):
        """تحميل قائمة الكيانات"""
        entities = set()
        for log in self.all_logs:
            if log['entity']:
                entities.add(log['entity'])
        
        self.entity_combo.clear()
        self.entity_combo.addItem("جميع الكيانات")
        
        for entity in sorted(entities):
            self.entity_combo.addItem(entity)
    
    def filter_logs(self):
        """تصفية السجلات المعروضة"""
        search_text = self.search_input.text().lower()
        selected_entity = self.entity_combo.currentText()
        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")
        
        filtered_logs = []
        
        for log in self.all_logs:
            matches_search = (search_text in (log.get('action') or '').lower() or 
                             search_text in (log.get('details') or '').lower() or 
                             search_text in (log.get('entity') or '').lower())
            
            if search_text and not matches_search:
                continue
            
            if selected_entity != "جميع الكيانات" and log.get('entity') != selected_entity:
                continue
            
            log_date = log['created_at'].split(' ')[0] if log['created_at'] else ''
            if log_date < from_date or log_date > to_date:
                continue
            
            filtered_logs.append(log)
        
        self.audit_table.setRowCount(len(filtered_logs))
        
        for row, log in enumerate(filtered_logs):
            self.audit_table.setItem(row, 0, QTableWidgetItem(str(log.get('id', ''))))
            self.audit_table.setItem(row, 1, QTableWidgetItem(str(log.get('user_id', '') or 'غير معروف')))
            self.audit_table.setItem(row, 2, QTableWidgetItem(log.get('action', '')))
            self.audit_table.setItem(row, 3, QTableWidgetItem(log.get('entity', '') or ''))
            self.audit_table.setItem(row, 4, QTableWidgetItem(str(log.get('entity_id', '') or '')))
            self.audit_table.setItem(row, 5, QTableWidgetItem(log.get('details', '') or ''))
            self.audit_table.setItem(row, 6, QTableWidgetItem(log.get('ip_address', '') or ''))
            self.audit_table.setItem(row, 7, QTableWidgetItem(log.get('created_at', '')))
    
    def show_log_details(self):
        """عرض تفاصيل السجل المحدد"""
        current_row = self.audit_table.currentRow()
        if current_row >= 0:
            details = self.audit_table.item(current_row, 5).text()
            self.detail_text.setText(details)
        else:
            self.detail_text.clear()
    
    def export_to_excel(self):
        """تصدير السجلات إلى Excel"""
        QMessageBox.information(self, "تصدير", "سيتم تنفيذ التصدير إلى Excel")
    
    def clear_old_logs(self):
        """مسح السجلات القديمة"""
        reply = QMessageBox.question(
            self, "مسح السجلات",
            "هل تريد مسح السجلات الأقدم من 30 يوماً؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "مسح", "سيتم مسح السجلات القديمة")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = AuditWindow()
    window.show()
    sys.exit(app.exec_())
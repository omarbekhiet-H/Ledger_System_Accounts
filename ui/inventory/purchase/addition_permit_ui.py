import os
import sys
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QComboBox, QLineEdit, QDateEdit, QTextEdit, QGroupBox,
                             QFormLayout, QTabWidget)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QTextDocument, QIcon

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.inventory.purchase.addition_permit_manager import AdditionPermit

class AdditionPermitUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📦 نظام إدارة إذونات الإضافة")
        self.setGeometry(100, 100, 1200, 800)
        
        self.addition_permit = AdditionPermit()
        self.current_permit_id = None
        self.init_ui()
        self.load_receipt_permits()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        # إنشاء تبويبات للواجهة
        self.tabs = QTabWidget()
        
        # تبويب إناذن الإضافة
        self.create_tab = QWidget()
        self.init_create_tab()
        self.tabs.addTab(self.create_tab, "➕ إنشاء إذن إضافة")
        
        # تبويب عرض الإذونات
        self.view_tab = QWidget()
        self.init_view_tab()
        self.tabs.addTab(self.view_tab, "👁️ عرض الإذونات")
        
        main_layout.addWidget(self.tabs)
        central_widget.setLayout(main_layout)
    
    def init_create_tab(self):
        layout = QVBoxLayout()
        
        # معلومات إذن الاستلام
        receipt_group = QGroupBox("معلومات إذن الاستلام")
        receipt_layout = QFormLayout()
        
        self.receipt_combo = QComboBox()
        self.receipt_combo.setPlaceholderText("اختر إذن الاستلام")
        receipt_layout.addRow("رقم إذن الاستلام:", self.receipt_combo)
        
        self.receipt_date_edit = QDateEdit()
        self.receipt_date_edit.setDate(QDate.currentDate())
        self.receipt_date_edit.setCalendarPopup(True)
        self.receipt_date_edit.setEnabled(False)
        receipt_layout.addRow("تاريخ الإذن:", self.receipt_date_edit)
        
        receipt_group.setLayout(receipt_layout)
        layout.addWidget(receipt_group)
        
        # جدول الأصناف
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "كود الصنف", "اسم الصنف", "الوحدة", "الكمية المستلمة", "الكمية المضافة", "ملاحظات"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("الأصناف:"))
        layout.addWidget(self.items_table)
        
        # ملاحظات
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("ملاحظات حول إذن الإضافة...")
        layout.addWidget(QLabel("ملاحظات:"))
        layout.addWidget(self.notes_edit)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 حفظ")
        self.save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.save_btn.clicked.connect(self.save_addition)
        button_layout.addWidget(self.save_btn)
        
        self.update_btn = QPushButton("🔄 تحديث")
        self.update_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.update_btn.clicked.connect(self.update_addition)
        self.update_btn.setEnabled(False)
        button_layout.addWidget(self.update_btn)
        
        self.complete_btn = QPushButton("✅ إكمال")
        self.complete_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        self.complete_btn.clicked.connect(self.complete_addition)
        self.complete_btn.setEnabled(False)
        button_layout.addWidget(self.complete_btn)
        
        self.print_btn = QPushButton("🖨️ طباعة")
        self.print_btn.setStyleSheet("background-color: #607D8B; color: white; font-weight: bold;")
        self.print_btn.clicked.connect(self.print_addition)
        self.print_btn.setEnabled(False)
        button_layout.addWidget(self.print_btn)
        
        self.export_btn = QPushButton("📊 تصدير إكسل")
        self.export_btn.setStyleSheet("background-color: #009688; color: white; font-weight: bold;")
        self.export_btn.clicked.connect(self.export_to_excel)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)
        
        self.clear_btn = QPushButton("🧹 مسح")
        self.clear_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.clear_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_btn)
        
        layout.addLayout(button_layout)
        self.create_tab.setLayout(layout)
        
        # ربط حدث تغيير إذن الاستلام
        self.receipt_combo.currentIndexChanged.connect(self.load_receipt_items)
    
    def init_view_tab(self):
        layout = QVBoxLayout()
        
        # أدوات البحث والتصفية
        filter_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("ابحث برقم الإذن أو التاريخ...")
        filter_layout.addWidget(self.search_edit)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["جميع الحالات", "معلق", "مكتمل", "ملغى"])
        filter_layout.addWidget(self.status_combo)
        
        search_btn = QPushButton("🔍 بحث")
        search_btn.clicked.connect(self.load_addition_permits)
        filter_layout.addWidget(search_btn)
        
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.clicked.connect(self.load_addition_permits)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        # جدول عرض الإذونات
        self.permits_table = QTableWidget()
        self.permits_table.setColumnCount(6)
        self.permits_table.setHorizontalHeaderLabels([
            "رقم الإذن", "رقم إذن الاستلام", "التاريخ", "الحالة", "الملاحظات", "الإجراءات"
        ])
        self.permits_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.permits_table)
        
        self.view_tab.setLayout(layout)
        
        # تحميل البيانات أول مرة
        self.load_addition_permits()
    
    def load_receipt_permits(self):
        """تحميل إذونات الاستلام المتاحة"""
        try:
            self.addition_permit.cursor.execute("""
                SELECT id, permit_number, permit_date 
                FROM receipt_permits 
                WHERE status = 'completed'
                ORDER BY permit_date DESC
            """)
            permits = self.addition_permit.cursor.fetchall()
            
            self.receipt_combo.clear()
            self.receipt_combo.addItem("اختر إذن الاستلام", None)
            for permit_id, permit_number, permit_date in permits:
                self.receipt_combo.addItem(f"{permit_number} - {permit_date}", permit_id)
                
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل إذونات الاستلام: {e}")
    
    def load_receipt_items(self):
        """تحميل أصناف إذن الاستلام المحدد"""
        try:
            receipt_id = self.receipt_combo.currentData()
            if not receipt_id:
                self.items_table.setRowCount(0)
                return
            
            # تحميل معلومات إذن الاستلام
            self.addition_permit.cursor.execute("""
                SELECT permit_date FROM receipt_permits WHERE id = ?
            """, (receipt_id,))
            receipt_info = self.addition_permit.cursor.fetchone()
            if receipt_info:
                self.receipt_date_edit.setDate(QDate.fromString(receipt_info[0], "yyyy-MM-dd"))
            
            # تحميل الأصناف
            self.addition_permit.cursor.execute("""
                SELECT ri.item_id, i.item_code, i.item_name_ar, u.name_ar, ri.received_quantity
                FROM receipt_permit_items ri
                JOIN items i ON ri.item_id = i.id
                JOIN units u ON ri.unit_id = u.id
                WHERE ri.receipt_permit_id = ?
            """, (receipt_id,))
            
            items = self.addition_permit.cursor.fetchall()
            
            self.items_table.setRowCount(0)
            for item_id, item_code, item_name, unit_name, received_qty in items:
                row_position = self.items_table.rowCount()
                self.items_table.insertRow(row_position)
                
                self.items_table.setItem(row_position, 0, QTableWidgetItem(item_code))
                self.items_table.setItem(row_position, 1, QTableWidgetItem(item_name))
                self.items_table.setItem(row_position, 2, QTableWidgetItem(unit_name))
                self.items_table.setItem(row_position, 3, QTableWidgetItem(str(received_qty)))
                
                # حقل الكمية المضافة
                add_qty_item = QTableWidgetItem(str(received_qty))
                self.items_table.setItem(row_position, 4, add_qty_item)
                
                # حقل الملاحظات
                notes_item = QTableWidgetItem("")
                self.items_table.setItem(row_position, 5, notes_item)
                
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل أصناف إذن الاستلام: {e}")
    
    def load_addition_permits(self):
        """تحميل إذونات الإضافة للعرض"""
        try:
            search_text = self.search_edit.text().strip()
            status_filter = self.status_combo.currentText()
            
            query = """
                SELECT ap.id, rp.permit_number, ap.addition_date, ap.status, ap.notes
                FROM addition_permits ap
                JOIN receipt_permits rp ON ap.receipt_id = rp.id
                WHERE 1=1
            """
            params = []
            
            if search_text:
                query += " AND (rp.permit_number LIKE ? OR ap.addition_date LIKE ?)"
                params.extend([f"%{search_text}%", f"%{search_text}%"])
            
            if status_filter != "جميع الحالات":
                query += " AND ap.status = ?"
                params.append(status_filter)
            
            query += " ORDER BY ap.addition_date DESC"
            
            self.addition_permit.cursor.execute(query, params)
            permits = self.addition_permit.cursor.fetchall()
            
            self.permits_table.setRowCount(len(permits))
            for row, (permit_id, receipt_number, addition_date, status, notes) in enumerate(permits):
                self.permits_table.setItem(row, 0, QTableWidgetItem(str(permit_id)))
                self.permits_table.setItem(row, 1, QTableWidgetItem(receipt_number))
                self.permits_table.setItem(row, 2, QTableWidgetItem(addition_date))
                self.permits_table.setItem(row, 3, QTableWidgetItem(status))
                self.permits_table.setItem(row, 4, QTableWidgetItem(notes or ""))
                
                # أزرار الإجراءات
                action_widget = QWidget()
                action_layout = QHBoxLayout()
                action_layout.setContentsMargins(0, 0, 0, 0)
                
                view_btn = QPushButton("عرض")
                view_btn.setStyleSheet("background-color: #2196F3; color: white;")
                view_btn.clicked.connect(lambda _, id=permit_id: self.view_permit(id))
                action_layout.addWidget(view_btn)
                
                edit_btn = QPushButton("تعديل")
                edit_btn.setStyleSheet("background-color: #FF9800; color: white;")
                edit_btn.clicked.connect(lambda _, id=permit_id: self.edit_permit(id))
                action_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("حذف")
                delete_btn.setStyleSheet("background-color: #f44336; color: white;")
                delete_btn.clicked.connect(lambda _, id=permit_id: self.delete_permit(id))
                action_layout.addWidget(delete_btn)
                
                action_widget.setLayout(action_layout)
                self.permits_table.setCellWidget(row, 5, action_widget)
                
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل إذونات الإضافة: {e}")
    
    def save_addition(self):
        """حفظ إذن الإضافة"""
        try:
            receipt_id = self.receipt_combo.currentData()
            if not receipt_id:
                QMessageBox.warning(self, "تحذير", "يرجى اختيار إذن استلام")
                return
            
            notes = self.notes_edit.toPlainText().strip()
            
            # حفظ إذن الإضافة
            permit_id = self.addition_permit.create_addition_permit(receipt_id, notes)
            self.current_permit_id = permit_id
            
            # حفظ الأصناف
            for row in range(self.items_table.rowCount()):
                item_code = self.items_table.item(row, 0).text()
                add_quantity = float(self.items_table.item(row, 4).text())
                item_notes = self.items_table.item(row, 5).text()
                
                # الحصول على ID الصنف
                self.addition_permit.cursor.execute(
                    "SELECT id FROM items WHERE item_code = ?", (item_code,)
                )
                item_result = self.addition_permit.cursor.fetchone()
                if item_result:
                    item_id = item_result[0]
                    self.addition_permit.add_addition_item(permit_id, item_id, add_quantity, item_notes)
            
            QMessageBox.information(self, "نجاح", f"تم حفظ إذن الإضافة رقم {permit_id}")
            self.update_btn.setEnabled(True)
            self.complete_btn.setEnabled(True)
            self.print_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self.load_addition_permits()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في حفظ إذن الإضافة: {e}")
    
    def update_addition(self):
        """تحديث إذن الإضافة"""
        try:
            if not self.current_permit_id:
                QMessageBox.warning(self, "تحذير", "لا يوجد إذن إضافة للتحديث")
                return
            
            notes = self.notes_edit.toPlainText().strip()
            
            # تحديث الملاحظات
            self.addition_permit.cursor.execute(
                "UPDATE addition_permits SET notes = ? WHERE id = ?",
                (notes, self.current_permit_id)
            )
            self.addition_permit.conn.commit()
            
            # تحديث الأصناف (هنا يمكنك إضافة منطق التحديث حسب احتياجك)
            
            QMessageBox.information(self, "نجاح", "تم تحديث إذن الإضافة")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تحديث إذن الإضافة: {e}")
    
    def complete_addition(self):
        """إكمال إذن الإضافة"""
        try:
            if not self.current_permit_id:
                QMessageBox.warning(self, "تحذير", "لا يوجد إذن إضافة لإكماله")
                return
            
            self.addition_permit.complete_addition(self.current_permit_id)
            QMessageBox.information(self, "نجاح", "تم إكمال إذن الإضافة")
            self.clear_form()
            self.load_addition_permits()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في إكمال إذن الإضافة: {e}")
    
    def print_addition(self):
        """طباعة إذن الإضافة"""
        try:
            if not self.current_permit_id:
                QMessageBox.warning(self, "تحذير", "لا يوجد إذن إضافة للطباعة")
                return
            
            # الحصول على بيانات الإذن
            self.addition_permit.cursor.execute("""
                SELECT ap.id, rp.permit_number, ap.addition_date, ap.status, ap.notes
                FROM addition_permits ap
                JOIN receipt_permits rp ON ap.receipt_id = rp.id
                WHERE ap.id = ?
            """, (self.current_permit_id,))
            permit_info = self.addition_permit.cursor.fetchone()
            
            # الحصول على الأصناف
            self.addition_permit.cursor.execute("""
                SELECT i.item_code, i.item_name_ar, u.name_ar, ai.quantity, ai.notes
                FROM addition_items ai
                JOIN items i ON ai.item_id = i.id
                JOIN units u ON ai.unit_id = u.id
                WHERE ai.permit_id = ?
            """, (self.current_permit_id,))
            items = self.addition_permit.cursor.fetchall()
            
            # إنشاء محتوى HTML للطباعة
            html = f"""
            <div style='text-align: center; direction: rtl; font-family: Arial;'>
                <h1>إذن الإضافة رقم {permit_info[0]}</h1>
                <p><strong>رقم إذن الاستلام:</strong> {permit_info[1]}</p>
                <p><strong>تاريخ الإضافة:</strong> {permit_info[2]}</p>
                <p><strong>الحالة:</strong> {permit_info[3]}</p>
                
                <h3>الأصناف</h3>
                <table border='1' cellspacing='0' cellpadding='5' width='100%' style='border-collapse: collapse;'>
                <tr>
                    <th>كود الصنف</th>
                    <th>اسم الصنف</th>
                    <th>الوحدة</th>
                    <th>الكمية</th>
                    <th>ملاحظات</th>
                </tr>
            """
            
            for item_code, item_name, unit_name, quantity, notes in items:
                html += f"""
                <tr>
                    <td>{item_code}</td>
                    <td>{item_name}</td>
                    <td>{unit_name}</td>
                    <td>{quantity}</td>
                    <td>{notes or ''}</td>
                </tr>
                """
            
            html += """
                </table>
                <br>
                <p><strong>ملاحظات:</strong> {}</p>
                <br><br>
                <div style='width: 100%; display: flex; justify-content: space-around;'>
                    <div>
                        <p>_________________________</p>
                        <p>المسؤول</p>
                    </div>
                    <div>
                        <p>_________________________</p>
                        <p>المستلم</p>
                    </div>
                </div>
            </div>
            """.format(permit_info[4] or "لا توجد ملاحظات")
            
            # الطباعة إلى PDF
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(f"addition_permit_{self.current_permit_id}.pdf")
            
            doc = QTextDocument()
            doc.setHtml(html)
            doc.print_(printer)
            
            QMessageBox.information(self, "طباعة", f"تم إنشاء ملف PDF: addition_permit_{self.current_permit_id}.pdf")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في الطباعة: {e}")
    
    def export_to_excel(self):
        """تصدير البيانات إلى إكسل"""
        try:
            if not self.current_permit_id:
                QMessageBox.warning(self, "تحذير", "لا يوجد إذن إضافة للتصدير")
                return
            
            # الحصول على بيانات الإذن
            self.addition_permit.cursor.execute("""
                SELECT ap.id, rp.permit_number, ap.addition_date, ap.status, ap.notes
                FROM addition_permits ap
                JOIN receipt_permits rp ON ap.receipt_id = rp.id
                WHERE ap.id = ?
            """, (self.current_permit_id,))
            permit_info = self.addition_permit.cursor.fetchone()
            
            # الحصول على الأصناف
            self.addition_permit.cursor.execute("""
                SELECT i.item_code, i.item_name_ar, u.name_ar, ai.quantity, ai.notes
                FROM addition_items ai
                JOIN items i ON ai.item_id = i.id
                JOIN units u ON ai.unit_id = u.id
                WHERE ai.permit_id = ?
            """, (self.current_permit_id,))
            items = self.addition_permit.cursor.fetchall()
            
            # إنشاء DataFrame للبيانات
            data = {
                'رقم إذن الإضافة': [permit_info[0]],
                'رقم إذن الاستلام': [permit_info[1]],
                'تاريخ الإضافة': [permit_info[2]],
                'الحالة': [permit_info[3]],
                'ملاحظات': [permit_info[4] or '']
            }
            permit_df = pd.DataFrame(data)
            
            items_data = []
            for item_code, item_name, unit_name, quantity, notes in items:
                items_data.append({
                    'كود الصنف': item_code,
                    'اسم الصنف': item_name,
                    'الوحدة': unit_name,
                    'الكمية': quantity,
                    'ملاحظات': notes or ''
                })
            items_df = pd.DataFrame(items_data)
            
            # التصدير إلى إكسل
            filename = f"addition_permit_{self.current_permit_id}.xlsx"
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                permit_df.to_excel(writer, sheet_name='معلومات الإذن', index=False)
                items_df.to_excel(writer, sheet_name='الأصناف', index=False)
            
            QMessageBox.information(self, "تصدير", f"تم التصدير إلى ملف: {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في التصدير: {e}")
    
    def view_permit(self, permit_id):
        """عرض إذن إضافة"""
        try:
            # هنا يمكنك تنفيذ منطق عرض التفاصيل
            QMessageBox.information(self, "عرض", f"عرض إذن الإضافة رقم {permit_id}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في العرض: {e}")
    
    def edit_permit(self, permit_id):
        """تعديل إذن إضافة"""
        try:
            # هنا يمكنك تنفيذ منطق التعديل
            QMessageBox.information(self, "تعديل", f"تعديل إذن الإضافة رقم {permit_id}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في التعديل: {e}")
    
    def delete_permit(self, permit_id):
        """حذف إذن إضافة"""
        try:
            reply = QMessageBox.question(self, "تأكيد الحذف", 
                                       "هل أنت متأكد من حذف إذن الإضافة؟",
                                       QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.addition_permit.cursor.execute(
                    "DELETE FROM addition_permits WHERE id = ?", (permit_id,)
                )
                self.addition_permit.conn.commit()
                QMessageBox.information(self, "نجاح", "تم حذف إذن الإضافة")
                self.load_addition_permits()
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في الحذف: {e}")
    
    def clear_form(self):
        """مسح النموذج"""
        self.receipt_combo.setCurrentIndex(0)
        self.receipt_date_edit.setDate(QDate.currentDate())
        self.items_table.setRowCount(0)
        self.notes_edit.clear()
        self.current_permit_id = None
        self.update_btn.setEnabled(False)
        self.complete_btn.setEnabled(False)
        self.print_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
    
    def closeEvent(self, event):
        """إغلاق الاتصال عند إغلاق النافذة"""
        self.addition_permit.close()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = AdditionPermitUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
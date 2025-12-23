# ui/Audit/subsidiary_ledger_report_ui.py

import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDateEdit, QComboBox, QGridLayout,
    QApplication, QStyle, QAbstractItemView, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate, QVariant
from PyQt5.QtGui import QFont, QColor, QBrush

# --- مسار المشروع الجذر ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# استيراد الانماط
from ui.styles.report_styles import ReportStyles

# Import managers with fallback in case اسم الملف اختلف
from database.manager.account_manager import AccountManager
try:
    from database.manager.financial.Ledger_financial_report_manager import FinancialReportManager
except Exception:
    try:
        from database.manager.financial.Ledger_financial_report_manager import FinancialReportManager
    except Exception:
        # آخر ملاذ: حاول استيراد من المسار الأعلى إن لزم
        from database.manager.financial.Ledger_financial_report_manager import FinancialReportManager

from database.db_connection import get_financials_db_connection
from database.schems.default_data.financials_data_population import insert_default_data
from database.schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT


class SubsidiaryLedgerReportWindow(QWidget):
    """
    نافذة تقرير الكشف التحليلي (Subsidiary Ledger).
    - يدعم فلترة بالتواريخ
    - فلتر: كل / المسددة / غير المسددة (matching by document number)
    - البحث عن حساب بواسطة الكود (باستخدام editingFinished لعدم إعطاء تحذيرات أثناء الكتابة)
    - تلوين الصفوف: أخضر للمطابقة (matched)، أحمر لغير المطابقة (unmatched)
    """

    def __init__(self, account_manager=None, financial_report_manager=None):
        super().__init__()

        self.accounts_manager = account_manager or AccountManager(get_financials_db_connection)
        self.financial_report_manager = financial_report_manager or FinancialReportManager(get_financials_db_connection)

        # بيانات التقرير الجاهزة للعرض
        self.all_journal_items_with_balance = []
        self.opening_balance = 0.0
        self.selected_account_id = None

        self.setWindowTitle("كشف حساب تحليلي")
        self.setLayoutDirection(Qt.RightToLeft)

        self.init_ui()
        self.apply_styles()
        self.resize(1000, 700)

    # --------------------- أدوات مساعدة للبحث عن الحساب ---------------------
    def _find_account_by_code(self, code):
        """حاول عدة دوال في AccountManager ثم اجتث كل الحسابات كحل أخير."""
        if not code:
            return None

        candidates = [
            'get_final_account_by_code',
            'get_account_by_code',
            'get_account_by_acc_code',
            'get_account_by_accode',
            'get_account_by_code_exact',
        ]
        for name in candidates:
            func = getattr(self.accounts_manager, name, None)
            if callable(func):
                try:
                    acc = func(code)
                    if acc:
                        return acc
                except Exception:
                    # تجاهل الأخطاء وجرب القادم
                    pass

        # كحل أخير: جرب المسح بين كل الحسابات
        try:
            all_accounts = self.accounts_manager.get_all_accounts()
            for acc in all_accounts:
                if str(acc.get('acc_code', '')).strip() == str(code).strip():
                    return acc
                # بعض الأنظمة تخزن الكود في حقل مختلف:
                if str(acc.get('acc_code', '')).strip() == str(code).strip():
                    return acc
        except Exception:
            pass

        return None

    # --------------------- واجهة المستخدم ---------------------
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        # عنوان
        title_label = ReportStyles.create_title_label("كشف حساب تحليلي")
        main_layout.addWidget(title_label)

        # مجموعة الضوابط
        controls_group = ReportStyles.create_group_box("خيارات التقرير")
        controls_group.setLayoutDirection(Qt.RightToLeft)
        controls_layout = QGridLayout(controls_group)
        controls_layout.setSpacing(8)

        # رمز الحساب
        controls_layout.addWidget(QLabel("رمز الحساب:"), 0, 0)
        self.account_code_input = QLineEdit()
        self.account_code_input.setPlaceholderText("أدخل رمز الحساب ثم اضغط Enter أو غادر الحقل")
        # مهم: استخدام editingFinished حتى لا يظهر التحذير أثناء الكتابة
        self.account_code_input.editingFinished.connect(self.update_account_name_from_code)
        controls_layout.addWidget(self.account_code_input, 0, 1)

        # اسم الحساب
        controls_layout.addWidget(QLabel("اسم الحساب:"), 0, 2)
        self.account_name_display = QLineEdit()
        self.account_name_display.setReadOnly(True)
        self.account_name_display.setProperty("class", "read-only-input")
        controls_layout.addWidget(self.account_name_display, 0, 3)

        # تواريخ
        controls_layout.addWidget(QLabel("من تاريخ:"), 1, 0)
        self.start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        controls_layout.addWidget(self.start_date_edit, 1, 1)

        controls_layout.addWidget(QLabel("إلى تاريخ:"), 1, 2)
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        controls_layout.addWidget(self.end_date_edit, 1, 3)

        # فلترة العرض
        controls_layout.addWidget(QLabel("عرض:"), 2, 0)
        self.view_filter_combo = QComboBox()
        self.view_filter_combo.addItem("كل الحركات", "all")
        self.view_filter_combo.addItem("المستندات المسددة", "matched")
        self.view_filter_combo.addItem("المستندات غير المسددة", "unmatched")
        self.view_filter_combo.currentIndexChanged.connect(self.display_report)
        controls_layout.addWidget(self.view_filter_combo, 2, 1)

        # زر توليد التقرير
        self.generate_report_btn = QPushButton("توليد التقرير")
        self.generate_report_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.generate_report_btn.clicked.connect(self.generate_report)
        controls_layout.addWidget(self.generate_report_btn, 3, 0, 1, 4)

        # توزيع الأعمدة
        controls_layout.setColumnStretch(1, 1)
        controls_layout.setColumnStretch(3, 1)
        main_layout.addWidget(controls_group)

        # جدول النتائج
        self.report_table = QTableWidget()
        ReportStyles.style_table(self.report_table)
        self.report_table.setColumnCount(9)
        self.report_table.setHorizontalHeaderLabels([
            "التاريخ", "رقم القيد", "الوصف", "نوع المستند", "رقم المستند",
            "مدين", "دائن", "الرصيد", "ملاحظات"
        ])
        self.report_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.report_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        header = self.report_table.horizontalHeader()
        # مرن لضبط العرض
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        for col in [5, 6, 7, 8]:
            header.setSectionResizeMode(col, QHeaderView.Stretch)
            header.setMinimumSectionSize(90)

        main_layout.addWidget(self.report_table)

        # ملخص الرصيد النهائي
        self.balance_label = QLabel("الرصيد النهائي للحساب: 0.00")
        self.balance_label.setFont(ReportStyles.get_font('subtitle'))
        self.balance_label.setAlignment(Qt.AlignRight)
        self.balance_label.setProperty("class", "balance-label")
        main_layout.addWidget(self.balance_label)

        # حفظ instance
        self.setLayout(main_layout)

    def apply_styles(self):
        ReportStyles.apply_style(self)
        extra = """
            QLineEdit[readOnly="true"], QLineEdit.read-only-input {
                background-color: #ECF0F1;
                border: 1px solid #BDC3C7;
            }
            QLabel.balance-label {
                color: #2980B9;
                font-weight: bold;
                padding: 6px;
                background-color: #E8F4FC;
                border-radius: 5px;
                border: 1px solid #BDC3C7;
            }
        """
        self.setStyleSheet(self.styleSheet() + extra)

    # --------------------- التعامل مع كود الحساب ---------------------
    def update_account_name_from_code(self):
        """
        يتم استدعاء هذه الدالة عند انتهاء التحرير (editingFinished).
        لا تظهر الرسائل أثناء كتابة المستخدم، فقط بعد انتهاء الإدخال.
        """
        account_code = self.account_code_input.text().strip()
        if not account_code:
            self.selected_account_id = None
            self.account_name_display.clear()
            return

        acc = self._find_account_by_code(account_code)
        if not acc:
            self.selected_account_id = None
            self.account_name_display.setText("لم يتم العثور على الحساب")
            return

        # تحقق من is_final إن وجد
        is_final = acc.get('is_final', None)
        name = acc.get('account_name_ar') or acc.get('account_name_en') or acc.get('name') or acc.get('username') or ''
        if is_final is None:
            # لا يوجد حقل is_final — اعتبر صالح
            self.selected_account_id = acc.get('id')
            self.account_name_display.setText(str(name))
            return

        try:
            if int(is_final) == 1:
                self.selected_account_id = acc.get('id')
                self.account_name_display.setText(str(name))
            else:
                QMessageBox.warning(self, "تحذير", "يجب إدخال رمز حساب نهائي")
                self.selected_account_id = None
                self.account_name_display.setText("حساب غير نهائي")
        except Exception:
            # لو لم نستطع تحويل is_final، خذ الافتراضي
            self.selected_account_id = acc.get('id')
            self.account_name_display.setText(str(name))

    # --------------------- توليد التقرير واحتساب الأرصدة ---------------------
    def generate_report(self):
        """يجلب البنود من FinancialReportManager ويحسب أرصدة التشغيل."""
        self.report_table.setRowCount(0)
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

        if self.selected_account_id is None:
            QMessageBox.warning(self, "اختيار ناقص", "الرجاء اختيار حساب نهائي صالح.")
            return

        try:
            # رصيد افتتاحي لليوم السابق لبداية النطاق
            from datetime import datetime, timedelta
            opening_balance_date = datetime.strptime(start_date, "%Y-%m-%d").date() - timedelta(days=1)
            opening_date_str = opening_balance_date.strftime("%Y-%m-%d")

            # get_account_balance_up_to_date قد يعيد tuple (debit, credit, final_balance)
            try:
                _, _, self.opening_balance = self.accounts_manager.get_account_balance_up_to_date(self.selected_account_id, opening_date_str)
            except Exception:
                # بعض نسخ AccountManager قد ترجع فقط قيمة واحدة
                try:
                    self.opening_balance = self.accounts_manager.get_account_balance_up_to_date(self.selected_account_id, opening_date_str)
                except Exception:
                    self.opening_balance = 0.0

            # جلب البنود
            all_items = self.financial_report_manager.get_journal_entries_for_account_in_range(
                self.selected_account_id, start_date, end_date
            )

            # debug
            print(f"DEBUG: Retrieved {len(all_items) if all_items is not None else 0} items for account {self.selected_account_id} between {start_date} and {end_date}")

            # حساب الرصيد الجاري
            self.all_journal_items_with_balance = []
            running_balance = self.opening_balance or 0.0

            # نضمن أن الترتيب ثابت (entry_date, entry_number, line_id إن وجد)
            sorted_items = sorted(all_items or [], key=lambda x: (
                str(x.get('entry_date', '')), str(x.get('entry_number', '')), int(x.get('line_id', 0) or 0)
            ))

            for item in sorted_items:
                debit = item.get('debit') or 0.0
                credit = item.get('credit') or 0.0
                # بعض القيم قد تأتي كسلاسل
                try:
                    debit = float(debit)
                except Exception:
                    debit = 0.0
                try:
                    credit = float(credit)
                except Exception:
                    credit = 0.0

                running_balance += (debit - credit)
                itm = dict(item)  # clone
                itm['running_balance'] = running_balance
                # normalize keys fallback
                itm.setdefault('entry_description', itm.get('description') or itm.get('entry_description') or '')
                itm.setdefault('line_document_number', itm.get('line_document_number') or itm.get('document_number') or '')
                itm.setdefault('line_document_type_name', itm.get('line_document_type_name') or itm.get('transaction_type_name') or '')
                itm.setdefault('line_notes', itm.get('line_notes') or itm.get('notes') or '')
                self.all_journal_items_with_balance.append(itm)

            # default filter = all
            self.view_filter_combo.setCurrentIndex(0)
            self.display_report()

        except Exception as e:
            print(f"Error in generate_report: {e}")
            QMessageBox.critical(self, "خطأ في جلب البيانات", f"حدث خطأ أثناء توليد التقرير:\n{e}")

    # --------------------- عرض النتائج + فلترة matched/unmatched ---------------------
    def display_report(self):
        """
        يعرض self.all_journal_items_with_balance في الجدول
        يدعم view_filter: all / matched / unmatched
        التعريف: group by document number (line_document_number) => matched إذا مجموع المدين = مجموع الدائن تقريباً
        """
        self.report_table.setRowCount(0)
        view_filter = self.view_filter_combo.currentData() or "all"

        # جمع حسب رقم المستند
        if view_filter == "all":
            items_to_show = list(self.all_journal_items_with_balance)
        else:
            document_groups = {}
            items_without_doc = []
            for itm in self.all_journal_items_with_balance:
                doc = (itm.get('line_document_number') or '').strip()
                if not doc:
                    items_without_doc.append(itm)
                    continue
                g = document_groups.setdefault(doc, {'debit': 0.0, 'credit': 0.0, 'items': []})
                g['debit'] += float(itm.get('debit') or 0.0)
                g['credit'] += float(itm.get('credit') or 0.0)
                g['items'].append(itm)

            items_to_show = []
            for doc, g in document_groups.items():
                matched = abs(g['debit'] - g['credit']) < 0.01
                if view_filter == "matched" and matched:
                    items_to_show.extend(g['items'])
                elif view_filter == "unmatched" and not matched:
                    items_to_show.extend(g['items'])
            if view_filter == "unmatched":
                # أيضاً عرض البنود التي ليس لها رقم مستند ضمن unmatched
                items_to_show.extend(items_without_doc)

        # صف رصيد افتتاحي
        self.report_table.insertRow(0)
        opening_item = QTableWidgetItem("الرصيد الافتتاحي")
        opening_item.setTextAlignment(Qt.AlignCenter)
        self.report_table.setItem(0, 2, opening_item)
        self.add_numeric_item(0, 7, self.opening_balance or 0.0)
        self.report_table.setSpan(0, 0, 1, 2)
        self.report_table.setSpan(0, 3, 1, 4)

        # فرز العناصر للعرض
        sorted_items = sorted(items_to_show, key=lambda x: (str(x.get('entry_date', '')), str(x.get('entry_number', ''))))

        total_debit = 0.0
        total_credit = 0.0

        for idx, itm in enumerate(sorted_items, start=1):
            self.report_table.insertRow(idx)

            entry_date = str(itm.get('entry_date') or '')
            entry_number = str(itm.get('entry_number') or '')
            description = str(itm.get('entry_description') or '')
            doc_type = str(itm.get('line_document_type_name') or '')
            doc_number = str(itm.get('line_document_number') or '')
            notes = str(itm.get('line_notes') or '')
            debit = float(itm.get('debit') or 0.0)
            credit = float(itm.get('credit') or 0.0)
            running = float(itm.get('running_balance') or 0.0)

            # وضع القيم في الجدول
            self.report_table.setItem(idx, 0, QTableWidgetItem(entry_date))
            self.report_table.setItem(idx, 1, QTableWidgetItem(entry_number))
            self.report_table.setItem(idx, 2, QTableWidgetItem(description))
            self.report_table.setItem(idx, 3, QTableWidgetItem(doc_type))
            self.report_table.setItem(idx, 4, QTableWidgetItem(doc_number))
            self.add_numeric_item(idx, 5, debit)
            self.add_numeric_item(idx, 6, credit)
            self.add_numeric_item(idx, 7, running)
            self.report_table.setItem(idx, 8, QTableWidgetItem(notes))

            total_debit += debit
            total_credit += credit

            # تلوين الصفوف: إذا doc_number موجود، اعرف إذا matched أم لا
            if doc_number:
                # حساب المطابقة السريعة لهذا المستند ضمن المجموعة (إعادة استخدام الطريقة أعلاه)
                # هنا نتحقق من فرق الدائن/المدين في المستند
                # للحصول على القيمة بدقة، نأخذ نفس document_groups logic أو حساب سريع:
                # (سهل ومنخفض التكلفة: نعيد احتساب لمستند واحد)
                doc_debit = 0.0
                doc_credit = 0.0
                for candidate in self.all_journal_items_with_balance:
                    if str(candidate.get('line_document_number') or '') == doc_number:
                        doc_debit += float(candidate.get('debit') or 0.0)
                        doc_credit += float(candidate.get('credit') or 0.0)
                matched = abs(doc_debit - doc_credit) < 0.01
                if matched:
                    self._set_row_color(idx, QColor(220, 255, 220))  # أخضر فاتح
                else:
                    self._set_row_color(idx, QColor(255, 230, 230))  # أحمر فاتح
            else:
                # بدون رقم مستند نضع لون محايد
                pass

        # إضافة صف الإجماليات
        self.add_totals_row(total_debit, total_credit)

        final_balance = (self.all_journal_items_with_balance[-1]['running_balance']
                         if self.all_journal_items_with_balance else self.opening_balance)
        self.balance_label.setText(f"الرصيد النهائي للحساب: {final_balance:,.2f}")

        # تحسين التوزيع
        self.report_table.resizeColumnsToContents()
        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(8, QHeaderView.Stretch)

    # --------------------- أدوات مساعدة للعرض ---------------------
    def add_numeric_item(self, row, col, value):
        """أدخل قيمة رقمية منسقة في خلية."""
        try:
            val = float(value or 0.0)
        except Exception:
            val = 0.0
        item = QTableWidgetItem(f"{val:,.2f}")
        item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.report_table.setItem(row, col, item)
        return item

    def add_totals_row(self, total_debit, total_credit):
        """أضف صف الإجماليات في أسفل الجدول."""
        row = self.report_table.rowCount()
        self.report_table.insertRow(row)
        # اجمع الخانات اليسارية
        total_item = QTableWidgetItem("الإجماليات")
        total_item.setTextAlignment(Qt.AlignCenter)
        total_item.setFont(ReportStyles.get_font('table_header'))
        self.report_table.setSpan(row, 0, 1, 5)
        self.report_table.setItem(row, 0, total_item)
        self.add_numeric_item(row, 5, total_debit)
        self.add_numeric_item(row, 6, total_credit)
        self.report_table.setSpan(row, 7, 1, 2)

    def _set_row_color(self, row_idx, qcolor: QColor):
        """لون كامل الصف بلون محدد."""
        brush = QBrush(qcolor)
        for col in range(self.report_table.columnCount()):
            item = self.report_table.item(row_idx, col)
            if item is None:
                item = QTableWidgetItem("")
                self.report_table.setItem(row_idx, col, item)
            item.setBackground(brush)

    # --------------------- event filter (اختياري لتحسين واجهة المستخدم) ---------------------
    def eventFilter(self, obj, event):
        try:
            if event.type() == event.KeyPress and event.key() == Qt.Key_Return:
                if isinstance(obj, (QLineEdit, QDateEdit, QComboBox)):
                    self.focusNextChild()
                    return True
        except Exception:
            pass
        return super().eventFilter(obj, event)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # تأكد من تهيئة قاعدة البيانات إذا لم تكن موجودة (للاختبار)
    conn = get_financials_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='journal_entries';")
            if not cursor.fetchone():
                cursor.executescript(FINANCIALS_SCHEMA_SCRIPT)
                conn.commit()
                try:
                    insert_default_data(conn)
                except Exception as e:
                    print(f"WARNING: insert_default_data failed: {e}")
        finally:
            conn.close()

    window = SubsidiaryLedgerReportWindow()
    window.show()
    sys.exit(app.exec_())

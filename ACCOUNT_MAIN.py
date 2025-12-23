import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QTabWidget, QToolButton,
    QStyle, QScrollArea, QToolBar, QMenu, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor,QPixmap

# ================================================================
# إعدادات المسارات الأساسية
# ================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# ================================================================
# استيراد وحدات الواجهة
# ================================================================
from ui.admin.login_window import LoginWindow
from ui.admin.user_management import UserManagementWindows
#from ui.admin.permissions_window import PermissionsWindow
#from ui.admin.company_settings_ui import CompanySettingsWindow

from ui.financial.ChartOfAccount_ui import ChartOfAccountsWindow

from ui.financial.setting.cost_centers_ui import CostCentersManagementWindow
from ui.financial.setting.document_types_ui import DocumentTypesManagementWindow
from ui.financial.setting.tax_types_ui import TaxTypesManagementWindow
from ui.financial.setting.currencies_ui import CurrenciesManagementWindow
from ui.financial.setting.transaction_types_ui import TransactionTypesWindow
from ui.financial.setting.bank_accounts_ui import BankAccountsManagementWindow
from ui.financial.setting.cash_chests_ui import CashChestsManagementWindow


from ui.financial.journal_entry_ui import JournalEntryManagementWindow

from ui.financial.opening_journal_entry_window_tree import OpeningJournalEntryWindow
from ui.audit.journal_audit_ui import JournalAuditReportWindow
from ui.financial.transaction.Cash_payment_ui import CashPaymentVoucherApp
from ui.financial.transaction.Cash_receipt_ui import CashReceiptVoucherApp

from ui.financial.reports.cash_report_ui import CashMovementReportApp
from ui.financial.reports.subsidiary_ledger_report_ui import SubsidiaryLedgerReportWindow
from ui.financial.reports.general_ledger_report_ui import GeneralLedgerReportWindow
from ui.financial.reports.balance_sheet_report_ui import BalanceSheetReportWindow
from ui.financial.reports.income_statement_report_ui import IncomeStatementReportWindow
from ui.financial.reports.trial_balance_report_ui import TrialBalanceReportWindow
from ui.financial.reports.journal_entry_reports_ui import JournalEntryReportWindow
from ui.financial.reports.journal_entry_full_details_ui import JournalEntryDetailedReportWindow
from ui.financial.reports.UNBALANEjournal_entry_ui import UnBlanceJournalEntryDetailedReportWindow

from ui.tools.backup_manager import BackupManagerWindow
from ui.financial.financial_periods_ui import FinancialPeriodsWindow

from database.db_connection import get_financials_db_connection

# ================================================================
# ApplicationController: يدير تدفق التطبيق
# ================================================================
class ApplicationController:
    def __init__(self):
        self.main_window = None
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.show_main_window)

    def start(self):
        self.login_window.show()

    def show_main_window(self, user_data, permissions):
        self.main_window = AccountingERP(user_data, permissions)
        self.main_window.showMaximized()
        self.login_window.close()

# ================================================================
# AccountingERP: النافذة الرئيسية للتطبيق
# ================================================================
class AccountingERP(QMainWindow):
    def __init__(self, user_data, permissions):
        super().__init__()
        self.current_user = user_data
        self.permissions = permissions
        print("DEBUG: MainWindow opened for user:", self.current_user['username'])
        print("DEBUG: User Permissions:", self.permissions)
        
        self.setup_main_window()
        self.create_user_toolbar()
        self.setup_main_layout()
        self.apply_styles()
        self.setup_ui()
        self.setup_screens()
        self.connect_signals()
        self.show_dashboard()

    def setup_main_window(self):
        """تهيئة إعدادات النافذة الرئيسية"""
        self.setWindowTitle("نظام ERP المحاسبي")
        self.setMinimumSize(1200, 800)
        self.setLayoutDirection(Qt.RightToLeft)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

    def create_user_toolbar(self):
        """إنشاء شريط أدوات للمستخدم في الأعلى"""
        self.user_toolbar = QToolBar()
        self.user_toolbar.setObjectName("userToolbar")
        self.addToolBar(Qt.TopToolBarArea, self.user_toolbar)
        self.user_toolbar.setMovable(False)
        self.user_toolbar.setFloatable(False)
        self.user_toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # إضافة مساحة فارغة لدفع العناصر لليمين
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.user_toolbar.addWidget(spacer)
        
        # زر المستخدم
        user_btn = QToolButton()
        user_btn.setText(f"مرحباً، {self.current_user['full_name']} ({self.current_user['username']})")
        user_btn.setIcon(QIcon(":/icons/user"))
        user_btn.setPopupMode(QToolButton.InstantPopup)
        
        # قائمة المستخدم
        user_menu = QMenu()
        user_menu.addAction(QIcon(":/icons/password"), "تغيير كلمة المرور", self.change_password)
        user_menu.addAction(QIcon(":/icons/logout"), "تسجيل الخروج", self.logout)
        user_btn.setMenu(user_menu)
        
        self.user_toolbar.addWidget(user_btn)

    def setup_main_layout(self):
        """تهيئة التخطيط الرئيسي"""
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # القائمة الجانبية
        self.side_menu_container = QWidget()
        self.side_menu_container.setObjectName("sideMenu")
        self.side_menu_scroll_area = QScrollArea()
        self.side_menu_scroll_area.setWidgetResizable(True)
        self.side_menu_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.side_menu_scroll_area.setWidget(self.side_menu_container)
        
        self.side_menu_layout = QVBoxLayout(self.side_menu_container)
        self.side_menu_layout.setContentsMargins(5, 10, 5, 10)
        self.side_menu_layout.setSpacing(3)
        
        self.main_layout.addWidget(self.side_menu_scroll_area, 1)

        # منطقة المحتوى
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(10)
        self.main_layout.addLayout(self.content_layout, 4)

    def apply_styles(self):
        """تطبيق التنسيقات البصرية"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F0F2F5;
            }
            
            #userToolbar {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E0E0E0;
                padding: 5px;
            }
            
            #sideMenu {
                background-color: #34495E;
            }
            
            QToolButton {
                color: #2C3E50;
                font-weight: bold;
                padding: 5px 10px;
                border: none;
                font-size: 12px;
            }
            
            QToolButton:hover {
                background-color: #ECF0F1;
                border-radius: 4px;
            }
            
            QTabWidget::pane { 
                border: 1px solid #BDC3C7; 
                border-radius: 8px; 
                padding: 5px; 
                background-color: white; 
            }
            
            QTabBar::tab { 
                background-color: #E0E4EB; 
                color: #2C3E50; 
                padding: 10px 25px 10px 15px; 
                border-top-left-radius: 8px; 
                border-top-right-radius: 8px; 
                border: 1px solid #BDC3C7; 
                border-bottom: none; 
                margin-right: 2px; 
            }
            
            QTabBar::tab:selected { 
                background-color: #FFFFFF; 
                color: #34495E; 
                font-weight: bold; 
                border-top: 2px solid #3498DB; 
                padding-top: 8px; 
            }
            
            QTabBar::tab:hover { 
                background-color: #D3D7DD; 
            }
            
            QScrollArea { 
                border: none; 
            }
        """)

    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        # --- قسم الادارة العامة ---
        self.add_menu_section("الإدارة العامة", [
            #("إضافة مستخدم", LoginWindow, "#8BC34A"),
            ("بيانات المستخدمين", UserManagementWindows, "#4CAF50"),
            #("الصلاحيات", PermissionsWindow, "#FFC107")
            #("بيانات الشركة", CompanySettingsWindow, "#BDFF07")

        ])

        # --- قسم الحسابات العامة ---
        self.add_menu_section("الحسابات العامة", [
            ("شجرة الحسابات", ChartOfAccountsWindow, "#8BC34A"),
            ("مراكز التكلفة", CostCentersManagementWindow, "#4CAF50"),
            ("أنواع المستندات", DocumentTypesManagementWindow, "#FFC107"),
            ("أنواع العملات", CurrenciesManagementWindow, "#E207FF"),
            ("الضرائب", TaxTypesManagementWindow, "#8BC34A"),
            ("انواع المعاملات ", TransactionTypesWindow, "#4A70C3")
        ])

        # --- قسم العملاء والموردين ---
        self.add_menu_section("العملاء والموردين", [
            ("الحسابات البنكية", BankAccountsManagementWindow, "#03A9F4"),
            ("الصناديق النقدية", CashChestsManagementWindow, "#F44336"),
            ("تقارير النقدية", CashMovementReportApp, "#F44336")

        ])

        # --- قسم المحاسبة ---
        self.add_menu_section("المحاسبة", [
            ("القيود اليومية", JournalEntryManagementWindow, "#673AB7"),
            ("القيود الافتتاحية", OpeningJournalEntryWindow, "#9C27B0"),
            ("مراجعة القيود", JournalAuditReportWindow, "#4027B0"),
            ("حركات صرف النقدية بالقيود", CashPaymentVoucherApp, "#B02772"),
            ("حركات استلام النقدية بالقيود", CashReceiptVoucherApp, "#27B027")


        ])

        # --- قسم التقارير ---
        self.add_menu_section("التقارير", [
            ("تقرير الأستاذ المساعد", SubsidiaryLedgerReportWindow, "#009688"),
            ("تقرير الأستاذ العام", GeneralLedgerReportWindow, "#00BCD4"),
            ("تقرير ميزان المراجعة", TrialBalanceReportWindow, "#3F51B5"),
            ("تقرير الميزانية العمومية", BalanceSheetReportWindow, "#2196F3"),
            ("تقرير قائمة الدخل", IncomeStatementReportWindow, "#4CAF50"),
            ("تقرير بالقيود", JournalEntryReportWindow, "#4CAF50"),
            ("تقرير تفصيلية", JournalEntryDetailedReportWindow, "#4CAF50"),
            ("تقرير القيود غير المتزنة", UnBlanceJournalEntryDetailedReportWindow, "#AF4C51"),
        ])

        # --- قسم الإعدادات ---
        self.add_menu_section("الإعدادات", [
            ("النسخ الاحتياطي", BackupManagerWindow, "#607D8B"),
             ("الاقفال السنوى و الاحتياطي", FinancialPeriodsWindow, "#062C3F"),

           
        ])

        self.side_menu_layout.addStretch(1)

    def add_menu_section(self, title, buttons):
        """إضافة قسم في القائمة الجانبية"""
        header = self.create_section_header(title)
        self.side_menu_layout.addWidget(header)
        
        section_widget = QWidget()
        section_widget.setObjectName("menuSection")
        section_layout = QVBoxLayout(section_widget)
        section_layout.setContentsMargins(10, 0, 0, 5)
        section_layout.setSpacing(3)
        
        for btn_text, window_class, color in buttons:
            btn = self.create_menu_button(btn_text, color)
            btn.setProperty("window_class", window_class)
            btn.clicked.connect(self.on_menu_button_clicked)
            section_layout.addWidget(btn)
        
        self.side_menu_layout.addWidget(section_widget)
        header.toggled.connect(section_widget.setVisible)
        section_widget.setVisible(False)

    def create_section_header(self, text, initial_checked=False):
        """إنشاء رأس قسم في القائمة الجانبية"""
        header_button = QToolButton()
        header_button.setText(text)
        header_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        header_button.setArrowType(Qt.RightArrow if not initial_checked else Qt.DownArrow)
        header_button.setCheckable(True)
        header_button.setChecked(initial_checked)
        header_button.setStyleSheet("""
            QToolButton { 
                border: none; 
                font-weight: bold; 
                color: white; 
                padding: 8px; 
                text-align: right; 
                font-size: 13px;
            } 
            QToolButton:hover {
                background-color: #2C3E50;
            }
            QToolButton:checked { 
                background-color: #2C3E50; 
            }
        """)
        header_button.toggled.connect(
            lambda checked: header_button.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
        )
        return header_button

    def create_menu_button(self, text, color):
        """إنشاء زر في القائمة الجانبية"""
        button = QPushButton(text)
        button.setObjectName("menuButton")
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color}; 
                color: white; 
                border-radius: 5px; 
                padding: 8px; 
                text-align: right; 
                border: none;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color, 20)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 30)};
            }}
        """)
        return button

    
    def darken_color(self, hex_color, percent):
        """تغميق اللون بنسبة معينة"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(max(0, int(c * (100 - percent) / 100)) for c in rgb)
        return f'#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}'

    def setup_screens(self):
        """إعداد شاشات التبويبات"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabs")
        self.content_layout.addWidget(self.tab_widget)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.setLayoutDirection(Qt.RightToLeft)

        # شاشة الترحيب/لوحة التحكم
        self.dashboard_window = QWidget()
        self.dashboard_window.setObjectName("dashboard")
        dashboard_layout = QVBoxLayout(self.dashboard_window)
        
        # صورة الترحيب
        welcome_image = QLabel()
        welcome_image.setAlignment(Qt.AlignCenter)
        welcome_image.setPixmap(QPixmap(":/images/welcome").scaled(400, 400, Qt.KeepAspectRatio))
        
        # نص الترحيب
        welcome_label = QLabel(f"مرحباً بك {self.current_user['full_name']} في نظام ERP المحاسبي")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2C3E50;
            margin: 20px;
        """)
        
        # إضافة العناصر إلى لوحة التحكم
        dashboard_layout.addStretch(1)
        dashboard_layout.addWidget(welcome_image)
        dashboard_layout.addWidget(welcome_label)
        dashboard_layout.addStretch(1)
        
        self.tab_widget.addTab(self.dashboard_window, "لوحة التحكم")

    def connect_signals(self):
        """ربط الإشارات"""
        pass

    def on_menu_button_clicked(self):
        """معالجة النقر على أزرار القائمة"""
        button = self.sender()
        if button:
            window_class = button.property("window_class")
            if window_class:
                self.show_screen(button.text(), window_class)

    def show_screen(self, screen_name, window_class=None):
        print(f"DEBUG: Attempting to show screen: {screen_name}")

        """عرض شاشة معينة"""
        # البحث إذا كانت الشاشة مفتوحة بالفعل
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == screen_name:
                self.tab_widget.setCurrentIndex(i)
                print(f"DEBUG: Screen {screen_name} already open, switching to tab")

                return
        
        # إنشاء نافذة جديدة إذا لم تكن مفتوحة
        if window_class:
            print(f"DEBUG: Creating new instance of {window_class.__name__}")

            screen_widget = window_class()
            index = self.tab_widget.addTab(screen_widget, screen_name)
            self.tab_widget.setCurrentIndex(index)
            print(f"DEBUG: Successfully opened {screen_name} in tab {index}")

        else:
            print(f"DEBUG: No window class specified for {screen_name}")

            QMessageBox.warning(self, "خطأ", f"الشاشة '{screen_name}' غير معرفة.")

    def show_dashboard(self):
        """عرض لوحة التحكم"""
        self.tab_widget.setCurrentIndex(0)

    def close_tab(self, index):
        """إغلاق تبويب"""
        if index > 0:  # لا تسمح بإغلاق تبويب لوحة التحكم
            widget = self.tab_widget.widget(index)
            self.tab_widget.removeTab(index)
            widget.deleteLater()

    def change_password(self):
        """تغيير كلمة مرور المستخدم"""
        QMessageBox.information(self, "تغيير كلمة المرور", "سيتم فتح نافذة تغيير كلمة المرور")

    def logout(self):
        """تسجيل خروج المستخدم"""
        reply = QMessageBox.question(
            self, "تسجيل الخروج",
            "هل أنت متأكد من تسجيل الخروج؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    print("DEBUG: Main app started. Initializing database...")
    conn = get_financials_db_connection()
    if conn:
        try:
            from database.schems.financials_schema import FINANCIALS_SCHEMA_SCRIPT
            from database.schems.default_data.financials_data_population import insert_default_data
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
            if not cursor.fetchone():
                print("DEBUG: 'users' table not found. Initializing full database schema and data...")
                cursor.executescript(FINANCIALS_SCHEMA_SCRIPT)
                insert_default_data(conn)
                conn.commit()
                print("DEBUG: Database initialized successfully.")
            else:
                print("DEBUG: Database already exists.")
        except Exception as e:
            print(f"CRITICAL ERROR during DB initialization in main_app: {e}")
        finally:
            conn.close()

    controller = ApplicationController()
    controller.start()
    
    sys.exit(app.exec_())
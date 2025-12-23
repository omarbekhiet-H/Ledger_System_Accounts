import sys
import os
import inspect
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QTabWidget, QToolButton,
    QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# ================================================================
# إعدادات المسارات ودالة تحميل التنسيق
# ================================================================
try:
    project_root = os.path.dirname(os.path.abspath(__file__))
except NameError:
    project_root = os.getcwd()

if project_root not in sys.path:
    sys.path.append(project_root)

DB_PATH = os.path.join(project_root, "database", "inventory.db")

def load_stylesheet():
    try:
        style_path = os.path.join(project_root, "style.qss")
        with open(style_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print("تحذير: ملف التنسيق style.qss غير موجود.")
        return ""

# ================================================================
# استيراد واجهات المخازن
# ================================================================
try:
    from ui.inventory.purchase.purchase_request_ui import PurchaseRequest_UI
    PURCHASE_REQUEST_AVAILABLE = True
except ImportError:
    PURCHASE_REQUEST_AVAILABLE = False

try:
    from ui.inventory.purchase.supply_order_ui import SupplyOrderUI
    SUPPLY_ORDER_AVAILABLE = True
except ImportError:
    SUPPLY_ORDER_AVAILABLE = False

try:
    from ui.inventory.purchase.receipt_permit_ui import ReceiptPermitUI
    RECEIPT_PERMIT_AVAILABLE = True
except ImportError:
    RECEIPT_PERMIT_AVAILABLE = False

try:
    from ui.inventory.purchase.addition_permit_ui import AdditionPermitUI
    ADDITION_PERMIT_AVAILABLE = True
except ImportError:
    ADDITION_PERMIT_AVAILABLE = False

try:
    from ui.inventory.purchase.inventory_invoice_ui import InventoryInvoiceUI
    INVENTORY_INVOICE_AVAILABLE = True
except ImportError:
    INVENTORY_INVOICE_AVAILABLE = False

# --- الصرف والمبيعات ---
try:
    from ui.inventory.purchase.issue_requests_actions import IssueRequestManage
    ISSUE_REQUESTS_AVAILABLE = True
except ImportError:
    ISSUE_REQUESTS_AVAILABLE = False

try:
    from ui.inventory.purchase.issue_request_create import IssueRequestCreate
    ISSUE_REQUEST_CREATE_AVAILABLE = True
except ImportError:
    ISSUE_REQUEST_CREATE_AVAILABLE = False

try:
    from ui.inventory.purchase.issue_permit_ui import IssuePermitUI
    ISSUE_PERMIT_AVAILABLE = True
except ImportError:
    ISSUE_PERMIT_AVAILABLE = False

try:
    from ui.inventory.purchase.issue_approval_ui import IssueApprovalUI
    ISSUE_APPROVAL_AVAILABLE = True
except ImportError:
    ISSUE_APPROVAL_AVAILABLE = False

# --- التقارير ---
try:
    from ui.inventory.reports.inventory_balance_ui import InventoryBalanceUI
    INVENTORY_BALANCE_AVAILABLE = True
except ImportError:
    INVENTORY_BALANCE_AVAILABLE = False

try:
    from ui.inventory.reports.inventory_card_ui import InventoryCardUI
    INVENTORY_CARD_AVAILABLE = True
except ImportError:
    INVENTORY_CARD_AVAILABLE = False

try:
    from ui.inventory.reports.inventory_additions_ui import InventoryAdditionsUI
    INVENTORY_ADDITIONS_AVAILABLE = True
except ImportError:
    INVENTORY_ADDITIONS_AVAILABLE = False

try:
    from ui.inventory.reports.inventory_issues_ui import InventoryIssuesUI
    INVENTORY_ISSUES_AVAILABLE = True
except ImportError:
    INVENTORY_ISSUES_AVAILABLE = False

try:
    from ui.inventory.reports.inventory_cost_ui import InventoryCostUI
    INVENTORY_COST_AVAILABLE = True
except ImportError:
    INVENTORY_COST_AVAILABLE = False

# --- الإعدادات ---
try:
    from ui.inventory.settings.items_ui import ItemsUI
    ITEMS_AVAILABLE = True
except ImportError:
    ITEMS_AVAILABLE = False

#try:
#    from ui.inventory.settings.item_groups_ui import ItemGroupsUI
#    ITEM_GROUPS_AVAILABLE = True
#except ImportError:
#    ITEM_GROUPS_AVAILABLE = False

try:
    from ui.inventory.settings.item_categories_ui import ItemCategoriesUI
    ITEM_CATEGORIES_AVAILABLE = True
except ImportError:
    ITEM_CATEGORIES_AVAILABLE = False

try:
    from ui.inventory.settings.locations_ui import LocationsUI
    LOCATIONS_AVAILABLE = True
except ImportError:
    LOCATIONS_AVAILABLE = False

try:
    from ui.inventory.settings.branches_ui import BranchesUI
    BRANCHES_AVAILABLE = True
except ImportError:
    BRANCHES_AVAILABLE = False

try:
    from ui.inventory.purchase.suppliers_window_ui import Supplierswindow
    SUPPLIERS_AVAILABLE = True
except ImportError:
    SUPPLIERS_AVAILABLE = False

try:
    from ui.inventory.purchase.customer_window_ui import CustomersWindow
    CUSTOMERS_AVAILABLE = True
except ImportError:
    CUSTOMERS_AVAILABLE = False

try:
    from ui.inventory.purchase.department_return_ui import DepartmentReturnUI
    DEPT_RETURN_AVAILABLE = True
except ImportError:
    DEPT_RETURN_AVAILABLE = False

try:
    from ui.inventory.purchase.supplier_return_ui import SupplierReturnUI
    SUPPLIER_RETURN_AVAILABLE = True
except ImportError:
    SUPPLIER_RETURN_AVAILABLE = False

# ================================================================
# Placeholder للواجهات غير المتوفرة
# ================================================================
class PlaceholderWindow(QWidget):
    def __init__(self, title="واجهة غير متوفرة"):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel(f"'{title}'\n\nهذه الواجهة غير متوفرة حالياً أو حدث خطأ أثناء تحميلها.")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #7f8c8d;")
        layout.addWidget(label)

# ================================================================
# النافذة الرئيسية
# ================================================================
class InventoryMainWindow(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.current_user = user_data
        self.db_path = DB_PATH
        
        self.setWindowTitle("نظام إدارة المخازن المتكامل")
        self.setMinimumSize(1366, 768)
        self.setLayoutDirection(Qt.RightToLeft)
        
        self.setup_main_layout()
        self.create_side_menu()
        self.apply_styles()
        self.show_dashboard()

    def setup_main_layout(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        side_menu_scroll = QScrollArea()
        side_menu_scroll.setWidgetResizable(True)
        side_menu_scroll.setFixedWidth(250)
        side_menu_scroll.setObjectName("sideMenuScroll")
        
        self.side_menu_container = QWidget()
        self.side_menu_container.setObjectName("sideMenu")
        self.side_menu_layout = QVBoxLayout(self.side_menu_container)
        self.side_menu_layout.setContentsMargins(5, 10, 5, 10)
        self.side_menu_layout.setSpacing(5)
        
        side_menu_scroll.setWidget(self.side_menu_container)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        self.main_layout.addWidget(side_menu_scroll)
        self.main_layout.addWidget(self.tab_widget, 1)

    def create_side_menu(self):
        # استيراد داخلي لتجنب circular import
        try:
            from ui.inventory.purchase.department_transfer_ui import DepartmentTransferUI
            DEPT_TRANSFER_AVAILABLE = True
        except ImportError:
            DEPT_TRANSFER_AVAILABLE = False

        # --- قسم المشتريات ---
        self.add_menu_section("🛒 المشتريات", [
            ("طلبات الشراء", PurchaseRequest_UI if PURCHASE_REQUEST_AVAILABLE else None),
            ("أوامر التوريد", SupplyOrderUI if SUPPLY_ORDER_AVAILABLE else None),
            ("إذن استلام", ReceiptPermitUI if RECEIPT_PERMIT_AVAILABLE else None),
            ("إذن إضافة", AdditionPermitUI if ADDITION_PERMIT_AVAILABLE else None),
            ("فاتورة مخزنية", InventoryInvoiceUI if INVENTORY_INVOICE_AVAILABLE else None),
        ])

        # --- المبيعات والصرف ---
        self.add_menu_section("📦 المبيعات والصرف", [
            ("إدارة طلبات الصرف", IssueRequestManage if ISSUE_REQUESTS_AVAILABLE else None),
            ("إنشاء طلب صرف", IssueRequestCreate if ISSUE_REQUEST_CREATE_AVAILABLE else None),
            ("اعتماد الصرف", IssueApprovalUI if ISSUE_APPROVAL_AVAILABLE else None),
            ("إذن صرف", IssuePermitUI if ISSUE_PERMIT_AVAILABLE else None),
        ])

        # --- التحويلات والارتجاع ---
        self.add_menu_section("🔄 التحويلات والارتجاع", [
            ("تحويل بين الأقسام", DepartmentTransferUI if DEPT_TRANSFER_AVAILABLE else None),
            ("ارتجاع من قسم", DepartmentReturnUI if DEPT_RETURN_AVAILABLE else None),
            ("ارتجاع إلى مورد", SupplierReturnUI if SUPPLIER_RETURN_AVAILABLE else None),
        ])

        # --- التقارير ---
        self.add_menu_section("📊 التقارير", [
            ("رصيد المخزون", InventoryBalanceUI if INVENTORY_BALANCE_AVAILABLE else None),
            ("كارت الصنف", InventoryCardUI if INVENTORY_CARD_AVAILABLE else None),
            ("حركات الإضافة", InventoryAdditionsUI if INVENTORY_ADDITIONS_AVAILABLE else None),
            ("حركات الصرف", InventoryIssuesUI if INVENTORY_ISSUES_AVAILABLE else None),
            ("تكلفة المخزون", InventoryCostUI if INVENTORY_COST_AVAILABLE else None),
        ])

        # --- الإعدادات ---
        self.add_menu_section("⚙️ الإعدادات", [
            ("إدارة الأصناف", ItemsUI if ITEMS_AVAILABLE else None),
        #    ("مجموعات الأصناف", ItemGroupsUI if ITEM_GROUPS_AVAILABLE else None),
            ("فئات الأصناف", ItemCategoriesUI if ITEM_CATEGORIES_AVAILABLE else None),
            ("المواقع", LocationsUI if LOCATIONS_AVAILABLE else None),
            ("الفروع", BranchesUI if BRANCHES_AVAILABLE else None),
            ("الموردين", Supplierswindow if SUPPLIERS_AVAILABLE else None),
            ("العملاء", CustomersWindow if CUSTOMERS_AVAILABLE else None),
        ])

        self.side_menu_layout.addStretch(1)

    def add_menu_section(self, title, buttons_config):
        header_button = QToolButton()
        header_button.setText(title)
        header_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        header_button.setArrowType(Qt.RightArrow)
        header_button.setCheckable(True)
        header_button.setObjectName("sectionHeader")
        self.side_menu_layout.addWidget(header_button)

        section_widget = QWidget()
        section_layout = QVBoxLayout(section_widget)
        section_layout.setContentsMargins(15, 0, 0, 5)
        section_layout.setSpacing(3)
        
        for btn_text, window_class in buttons_config:
            btn = QPushButton(btn_text)
            btn.setProperty("window_class", window_class)
            btn.clicked.connect(self.on_menu_button_clicked)
            section_layout.addWidget(btn)
        
        section_widget.setVisible(False)
        self.side_menu_layout.addWidget(section_widget)

        header_button.toggled.connect(
            lambda checked: (
                section_widget.setVisible(checked),
                header_button.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
            )
        )

    def apply_styles(self):
        self.setStyleSheet(load_stylesheet())
        self.central_widget.setStyleSheet("""
            #sideMenuScroll { border: none; }
            #sideMenu { background-color: #2c3e50; }
            #sectionHeader {
                width: 100%;
                border: none;
                color: white;
                padding: 8px;
                text-align: right;
                font-size: 15px;
                font-weight: bold;
            }
            #sectionHeader:checked { background-color: #34495e; }
            #sideMenu QPushButton {
                background-color: #34495e;
                color: #ecf0f1;
                border: none;
                padding: 8px;
                text-align: right;
                font-size: 13px;
                border-radius: 4px;
            }
            #sideMenu QPushButton:hover { background-color: #4a6572; }
            QTabBar::close-button { qproperty-icon: url(none); }
            QTabBar::close-button:hover {
                background-color: #e74c3c;
                border-radius: 7px;
            }
        """)

    def on_menu_button_clicked(self):
        button = self.sender()
        window_class = button.property("window_class")
        screen_name = button.text()

        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == screen_name:
                self.tab_widget.setCurrentIndex(i)
                return

        if window_class:
            try:
                sig = inspect.signature(window_class.__init__)
                params = sig.parameters
                kwargs = {}
                if 'db_path' in params:
                    kwargs['db_path'] = self.db_path
                if 'user_data' in params:
                    kwargs['user_data'] = getattr(self, 'current_user', None)
                screen_widget = window_class(**kwargs)
                index = self.tab_widget.addTab(screen_widget, screen_name)
                self.tab_widget.setCurrentIndex(index)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "خطأ في التشغيل",
                    f"فشل في فتح واجهة '{screen_name}':\n\n{e}"
                )
        else:
            placeholder = PlaceholderWindow(screen_name)
            index = self.tab_widget.addTab(placeholder, screen_name)
            self.tab_widget.setCurrentIndex(index)

    def show_dashboard(self):
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)
        welcome_label = QLabel(f"مرحباً بك، {self.current_user['full_name']}!\n\nنظام إدارة المخازن جاهز للعمل.")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(welcome_label)
        self.tab_widget.addTab(dashboard_widget, "🏠 لوحة التحكم")

    def close_tab(self, index):
        if self.tab_widget.tabText(index) == "🏠 لوحة التحكم":
            return
        widget = self.tab_widget.widget(index)
        if widget:
            self.tab_widget.removeTab(index)
            widget.deleteLater()

# ================================================================
# نقطة انطلاق البرنامج
# ================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))
    
    current_user_data = {'username': 'admin', 'full_name': 'مدير النظام'}
    
    if not os.path.exists(DB_PATH):
        QMessageBox.critical(None, "خطأ فادح", f"ملف قاعدة البيانات غير موجود في المسار:\n{DB_PATH}")
        sys.exit(1)

    main_window = InventoryMainWindow(current_user_data)
    main_window.showMaximized()
    
    sys.exit(app.exec_())

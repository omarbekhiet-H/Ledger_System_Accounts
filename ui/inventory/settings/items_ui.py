import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QComboBox,
    QHeaderView, QDoubleSpinBox, QCheckBox, QGridLayout, QGroupBox,
    QScrollArea, QApplication, QSizePolicy, QDateEdit, QSpinBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QIcon
#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#
# تصحيح مسار المشروع لضمان استيراد الوحدات بشكل صحيح
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.inventory.setting.item_manager import ItemsManager
from database.manager.inventory.setting.item_categories_manager import ItemCategoryManager
from database.manager.inventory.setting.item_units_manager import ItemUnitManager
#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#
class ItemsUI(QWidget):
    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
        self.manager = ItemsManager(db_path)
        self.category_manager = ItemCategoryManager(db_path)
        self.unit_manager = ItemUnitManager(db_path)
        
        self.selected_item_id = None
        self.available_units = []
        self.parent_categories = []
        
        self.setup_ui()
        self.load_combobox_data()
        self.load_main_table()
        self.setup_connections()
        self.setWindowTitle("إدارة الأصناف")
        self.setWindowIcon(QIcon("item_icon.png"))
        self.setLayoutDirection(Qt.RightToLeft)
        self.apply_styles()
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)
#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                font-family: Arial;
                font-size: 10px;
            }
            #mainFrame {
                background-color: #FFFFFF;
                border: 2px solid #CCCCCC;
                border-radius: 8px;
            }
            #titleBar {
                background-color: #2C3E50;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 5px;
            }
            QLabel { 
                font-weight: bold; 
                color: #333;
                font-size: 11px;
            }
            QLineEdit, QComboBox, QDoubleSpinBox, QDateEdit { 
                background-color: white; 
                border: 1px solid #BDC3C7;
                padding: 4px;
                min-height: 25px;
                border-radius: 3px;
                font-size: 11px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 15px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 12px;
                min-width: 70px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton#delete_button { background-color: #f44336; }
            QPushButton#delete_button:hover { background-color: #d32f2f; }
            QPushButton#update_button { background-color: #2196F3; }
            QPushButton#update_button:hover { background-color: #0b7dda; }
            QPushButton#clear_button { background-color: #607D8B; }
            QPushButton#clear_button:hover { background-color: #757575; }
            QGroupBox {
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #BDC3C7;
                gridline-color: #BDC3C7;
                selection-background-color: #3498DB;
                selection-color: white;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #2C3E50;
                color: white;
                padding: 4px;
                font-weight: bold;
                border: none;
                font-size: 11px;
            }
            QScrollArea {
                border: none;
            }
            QCheckBox {
                font-size: 11px;
            }
        """)
#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#
    def setup_ui(self):
        # إطار رئيسي
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # شريط العنوان مع زر الإغلاق
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(35)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 5, 10, 5)

        # عنوان النافذة
        title_label = QLabel("إدارة الأصناف")
        title_label.setStyleSheet("""
            color: white;
            font-weight: bold;
            font-size: 14px;
        """)

        # زر إغلاق النافذة
        close_btn = QPushButton("X")
        close_btn.setFixedSize(25, 25)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border-radius: 12px;
                font-weight: bold;
                font-size: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        close_btn.clicked.connect(self.close)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        main_layout.addWidget(title_bar)
        
        # Main content area
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(5)
        
        # Left Panel - Form
        left_panel = QWidget()
        left_panel.setMaximumWidth(400)
        form_layout = QVBoxLayout(left_panel)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(5)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumWidth(400)
        form_container = QWidget()
        form_container_layout = QVBoxLayout(form_container)
        form_container_layout.setContentsMargins(5, 5, 5, 5)
        form_container_layout.setSpacing(5)
        
        # Parent Category Group
        parent_group = QGroupBox("التصنيف الأب")
        parent_layout = QGridLayout(parent_group)
        parent_layout.setContentsMargins(8, 15, 8, 8)
        parent_layout.setVerticalSpacing(5)
        
        self.parent_category_combo = QComboBox()
        
        parent_layout.addWidget(QLabel("التصنيف الأب (*):"), 0, 0)
        parent_layout.addWidget(self.parent_category_combo, 0, 1)
        
        # Basic Info Group
        basic_info_group = QGroupBox("المعلومات الأساسية")
        basic_layout = QGridLayout(basic_info_group)
        basic_layout.setContentsMargins(8, 15, 8, 8)
        basic_layout.setVerticalSpacing(5)
        
        self.item_code_input = QLineEdit()
        self.item_code_input.setReadOnly(True)
        self.item_name_ar_input = QLineEdit()
        self.item_type_combo = QComboBox()
        self.item_type_combo.addItems(['مخزون', 'خدمة', 'أصل ثابت', 'مصنع'])
        self.category_combo = QComboBox()
        
        basic_layout.addWidget(QLabel("كود الصنف (*):"), 0, 0)
        basic_layout.addWidget(self.item_code_input, 0, 1)
        basic_layout.addWidget(QLabel("اسم الصنف (*):"), 1, 0)
        basic_layout.addWidget(self.item_name_ar_input, 1, 1)
        basic_layout.addWidget(QLabel("نوع الصنف (*):"), 2, 0)
        basic_layout.addWidget(self.item_type_combo, 2, 1)
        basic_layout.addWidget(QLabel("التصنيف الفرعي:"), 3, 0)
        basic_layout.addWidget(self.category_combo, 3, 1)
        
        # Units Group
        units_group = QGroupBox("الوحدات والتحويل")
        units_layout = QGridLayout(units_group)
        units_layout.setContentsMargins(8, 15, 8, 8)
        units_layout.setVerticalSpacing(5)
        
        self.main_unit_combo = QComboBox()
        self.medium_unit_combo = QComboBox()
        self.small_unit_combo = QComboBox()
        self.main_to_medium_factor = QDoubleSpinBox()
        self.main_to_medium_factor.setDecimals(0)
        self.main_to_medium_factor.setValue(1)
        self.medium_to_small_factor = QDoubleSpinBox()
        self.medium_to_small_factor.setDecimals(0)
        self.medium_to_small_factor.setValue(1)
        
        units_layout.addWidget(QLabel("الوحدة الكبرى (*):"), 0, 0)
        units_layout.addWidget(self.main_unit_combo, 0, 1)
        units_layout.addWidget(QLabel("الوحدة المتوسطة:"), 1, 0)
        units_layout.addWidget(self.medium_unit_combo, 1, 1)
        units_layout.addWidget(QLabel("معامل التحويل (ك->م):"), 2, 0)
        units_layout.addWidget(self.main_to_medium_factor, 2, 1)
        units_layout.addWidget(QLabel("الوحدة الصغرى:"), 3, 0)
        units_layout.addWidget(self.small_unit_combo, 3, 1)
        units_layout.addWidget(QLabel("معامل التحويل (م->ص):"), 4, 0)
        units_layout.addWidget(self.medium_to_small_factor, 4, 1)
        
        # Stock Limits Group
        stock_group = QGroupBox("حدود المخزون")
        stock_layout = QGridLayout(stock_group)
        stock_layout.setContentsMargins(8, 15, 8, 8)
        stock_layout.setVerticalSpacing(5)

        self.min_stock_input = QDoubleSpinBox()
        self.min_stock_input.setDecimals(0)
        self.min_stock_input.setValue(0)

        self.max_stock_input = QDoubleSpinBox()
        self.max_stock_input.setDecimals(0)
        self.max_stock_input.setValue(0)

        self.reorder_point_input = QDoubleSpinBox()
        self.reorder_point_input.setDecimals(0)
        self.reorder_point_input.setValue(0)
        
        stock_layout.addWidget(QLabel("الحد الأدنى:"), 0, 0)
        stock_layout.addWidget(self.min_stock_input, 0, 1)
        stock_layout.addWidget(QLabel("الحد الأقصى:"), 1, 0)
        stock_layout.addWidget(self.max_stock_input, 1, 1)
        stock_layout.addWidget(QLabel("نقطة إعادة الطلب:"), 2, 0)
        stock_layout.addWidget(self.reorder_point_input, 2, 1)
        
        # Expiry Group
        expiry_group = QGroupBox("تاريخ الصلاحية")
        expiry_layout = QGridLayout(expiry_group)
        expiry_layout.setContentsMargins(8, 15, 8, 8)
        expiry_layout.setVerticalSpacing(5)
        
        self.has_expiry_check = QCheckBox("له صلاحية")
        self.expiry_date_input = QDateEdit()
        self.expiry_date_input.setDate(QDate.currentDate())
        self.expiry_date_input.setCalendarPopup(True)
        self.expiry_date_input.setEnabled(False)
        
        self.has_expiry_check.stateChanged.connect(
            lambda: self.expiry_date_input.setEnabled(self.has_expiry_check.isChecked()))
        
        expiry_layout.addWidget(self.has_expiry_check, 0, 0, 1, 2)
        expiry_layout.addWidget(QLabel("تاريخ الانتهاء:"), 1, 0)
        expiry_layout.addWidget(self.expiry_date_input, 1, 1)
        
        # Pricing Group
        pricing_group = QGroupBox("التسعير")
        pricing_layout = QGridLayout(pricing_group)
        pricing_layout.setContentsMargins(8, 15, 8, 8)
        pricing_layout.setVerticalSpacing(5)
        
        self.cost_price_input = QDoubleSpinBox()
        self.cost_price_input.setRange(0, 9999999.99)
        self.cost_price_input.setDecimals(2)
        self.cost_price_input.setValue(0.0)
        self.sale_price_input = QDoubleSpinBox()
        self.sale_price_input.setRange(0, 9999999.99)
        self.sale_price_input.setDecimals(2)
        self.sale_price_input.setValue(0.0)
        
        pricing_layout.addWidget(QLabel("سعر التكلفة:"), 0, 0)
        pricing_layout.addWidget(self.cost_price_input, 0, 1)
        pricing_layout.addWidget(QLabel("سعر البيع:"), 1, 0)
        pricing_layout.addWidget(self.sale_price_input, 1, 1)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(5)
        self.add_button = QPushButton("إضافة")
        self.update_button = QPushButton("تعديل")
        self.update_button.setObjectName("update_button")
        self.delete_button = QPushButton("حذف")
        self.delete_button.setObjectName("delete_button")
        self.clear_button = QPushButton("مسح")
        self.clear_button.setObjectName("clear_button")
        
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.update_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.clear_button)
        
        # Assemble form
        form_container_layout.addWidget(parent_group)
        form_container_layout.addWidget(basic_info_group)
        form_container_layout.addWidget(units_group)
        form_container_layout.addWidget(stock_group)
        form_container_layout.addWidget(expiry_group)
        form_container_layout.addWidget(pricing_group)
        form_container_layout.addStretch()
        form_container_layout.addLayout(buttons_layout)
        
        scroll_area.setWidget(form_container)
        form_layout.addWidget(scroll_area)
        
        # Right Panel - Items Table
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        
        # Search Panel
        search_panel = QWidget()
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(0, 0, 0, 0)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث باسم الصنف أو الكود...")
        search_button = QPushButton("بحث")
        search_button.setFixedWidth(80)
        search_button.clicked.connect(self.search_items)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(13)
        self.items_table.setHorizontalHeaderLabels([
            "ID", "الكود", "الاسم", "النوع", "التصنيف", 
            "الوحدة", "سعر البيع", "سعر التكلفة", "الحد الأدنى",
            "الحد الأقصى", "نقطة إعادة الطلب", "صلاحية", "حركات"
        ])
        self.items_table.setColumnHidden(0, True)  # Hide ID column
        self.items_table.setColumnHidden(12, True)  # Hide movements column
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setSelectionMode(QTableWidget.SingleSelection)
        
        right_layout.addWidget(QLabel("قائمة الأصناف:"))
        right_layout.addWidget(search_panel)
        right_layout.addWidget(self.items_table)
        
        content_layout.addWidget(left_panel)
        content_layout.addWidget(right_panel)
        main_layout.addWidget(content_widget)
#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#
    def setup_connections(self):
        self.add_button.clicked.connect(self.add_item)
        self.update_button.clicked.connect(self.update_item)
        self.delete_button.clicked.connect(self.delete_item)
        self.clear_button.clicked.connect(self.clear_form)
        self.parent_category_combo.currentIndexChanged.connect(self.on_parent_category_changed)
        self.items_table.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.search_input.textChanged.connect(self.search_items)
        # تفعيل عند النقر على خلايا الجدول
        self.items_table.cellClicked.connect(self.on_item_selected)
    
    def on_item_selection_changed(self):
        selected_items = self.items_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            self.load_item_details(row)
    
    def on_parent_category_changed(self):
        parent_id = self.parent_category_combo.currentData()
        self.load_subcategories(parent_id)
        self.generate_item_code()

    def load_combobox_data(self):
        # Load parent categories
        self.parent_category_combo.clear()
        self.parent_category_combo.addItem("-- اختر تصنيف أب --", None)
        self.parent_categories = self.category_manager.list_parent_categories()
        for cat in self.parent_categories:
            self.parent_category_combo.addItem(cat['name_ar'], cat['id'])
        
        # Load units
        self.available_units = self.unit_manager.list_active_units()
        for combo in [self.main_unit_combo, self.medium_unit_combo, self.small_unit_combo]:
            combo.clear()
            combo.addItem("-- اختر وحدة --", None)
            for unit in self.available_units:
                combo.addItem(unit['name_ar'], unit['id'])

    def load_subcategories(self, parent_id=None):
        self.category_combo.clear()
        self.category_combo.addItem("-- اختر تصنيف فرعي --", None)
        if parent_id:
            categories = self.category_manager.list_subcategories(parent_id)
            for cat in categories:
                self.category_combo.addItem(cat['name_ar'], cat['id'])

    def generate_item_code(self):
        try:
            parent_id = self.parent_category_combo.currentData()
            if not parent_id:
                return
                
            last_code = self.manager.get_last_item_code(parent_id)
            
            if last_code:
                try:
                    prefix, num = last_code.split('-')
                    new_num = int(num) + 1
                    new_code = f"{prefix}-{new_num:03d}"
                except:
                    new_code = f"{parent_id:03d}-01"
            else:
                new_code = f"{parent_id:03d}-01"
                
            self.item_code_input.setText(new_code)
            
        except Exception as e:
            QMessageBox.warning(self, "تحذير", f"خطأ في توليد الكود: {str(e)}")

    def load_main_table(self):
        self.items_table.setRowCount(0)
        items = self.manager.list_items_with_movements()
        self.populate_table(items)

    def populate_table(self, items):
        self.items_table.setRowCount(0)
        for row, item in enumerate(items):
            self.items_table.insertRow(row)
            
            # Set data for each column
            self.items_table.setItem(row, 0, QTableWidgetItem(str(item['id'])))
            self.items_table.setItem(row, 1, QTableWidgetItem(item['item_code']))
            self.items_table.setItem(row, 2, QTableWidgetItem(item['item_name_ar']))
            self.items_table.setItem(row, 3, QTableWidgetItem(item['item_type']))
            self.items_table.setItem(row, 4, QTableWidgetItem(item.get('category_name', '')))
            self.items_table.setItem(row, 5, QTableWidgetItem(item.get('unit_name', '')))
            
            # Format prices
            sale_price = QTableWidgetItem(f"{item.get('sale_price', 0):.2f}")
            sale_price.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setItem(row, 6, sale_price)
            
            cost_price = QTableWidgetItem(f"{item.get('cost_price', 0):.2f}")
            cost_price.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setItem(row, 7, cost_price)
            
            # Stock limits
            min_stock = QTableWidgetItem(f"{item.get('min_stock_limit', 0):.0f}")
            min_stock.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setItem(row, 8, min_stock)
            
            max_stock = QTableWidgetItem(f"{item.get('max_stock_limit', 0):.0f}")
            max_stock.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setItem(row, 9, max_stock)
            
            reorder = QTableWidgetItem(f"{item.get('reorder_point', 0):.0f}")
            reorder.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setItem(row, 10, reorder)
            
            # Expiry info
            expiry_text = "نعم" if item.get('has_expiry', False) else "لا"
            self.items_table.setItem(row, 11, QTableWidgetItem(expiry_text))
            
            # Movements info (hidden)
            self.items_table.setItem(row, 12, QTableWidgetItem(str(item.get('movement_count', 0))))
            
            # تلوين الصفوف الزوجية
            if row % 2 == 0:
                for col in range(self.items_table.columnCount()):
                    item_widget = self.items_table.item(row, col)
                    if item_widget:
                        item_widget.setBackground(QColor(245, 245, 245))

    def on_item_selected(self, row, column):
        self.load_item_details(row)

    def load_item_details(self, row):
        try:
            self.selected_item_id = int(self.items_table.item(row, 0).text())
            print(f"Selected Item ID: {self.selected_item_id}")  # إضافة هنا
            item_details = self.manager.get_item_details(self.selected_item_id)
            print(f"Item Details: {item_details}")  # إضافة هنا
            if not item_details:
                QMessageBox.warning(self, "تحذير", "لم يتم العثور على تفاصيل الصنف")
                return
            
            # تعطيل زر الإضافة وتفعيل أزرار التعديل والحذف
            self.add_button.setEnabled(False)
            self.update_button.setEnabled(True)
            self.delete_button.setEnabled(True)
        
            # Set basic info
            self.item_code_input.setText(item_details.get('item_code', ''))
            self.item_name_ar_input.setText(item_details.get('item_name_ar', ''))
        
            # Set item type
            item_type = item_details.get('item_type', 'مخزون')
            print(f"Item Type from details: {item_type}")  # إضافة هنا
            index = self.item_type_combo.findText(item_type)
            if index >= 0:
                self.item_type_combo.setCurrentIndex(index)
        
            # التعامل مع التصنيفات إذا كانت متوفرة، أو استخدام قيم افتراضية
            parent_id = item_details.get('parent_category_id')
            print(f"Parent Category ID: {parent_id}")  # إضافة هنا
            if parent_id:
                idx = self.parent_category_combo.findData(parent_id)
                if idx >= 0:
                    self.parent_category_combo.setCurrentIndex(idx)
                    self.load_subcategories(parent_id)
        
            cat_id = item_details.get('category_id')
            if cat_id:
                idx = self.category_combo.findData(cat_id)
                if idx >= 0:
                    self.category_combo.setCurrentIndex(idx)
        
        # باقي الكود كما هو...
        # Set units info
            units = item_details.get('units', [])
            print(f"Units list: {units}")  # إضافة هنا

            for unit in units:
                if unit.get('is_main'):
                    idx = self.main_unit_combo.findData(unit['unit_id'])
                    if idx >= 0:
                        self.main_unit_combo.setCurrentIndex(idx)
                elif unit.get('is_medium'):
                    idx = self.medium_unit_combo.findData(unit['unit_id'])
                    if idx >= 0:
                        self.medium_unit_combo.setCurrentIndex(idx)
                    self.main_to_medium_factor.setValue(unit.get('conversion_factor', 1.0))
                elif unit.get('is_small'):
                    idx = self.small_unit_combo.findData(unit['unit_id'])
                    if idx >= 0:
                        self.small_unit_combo.setCurrentIndex(idx)
                    self.medium_to_small_factor.setValue(unit.get('conversion_factor', 1.0))
        
            # Set stock limits
            self.min_stock_input.setValue(float(item_details.get('min_stock_limit', 0.0)))
            self.max_stock_input.setValue(float(item_details.get('max_stock_limit', 0.0)))
            self.reorder_point_input.setValue(float(item_details.get('reorder_point', 0.0)))
        
            # Set pricing
            self.cost_price_input.setValue(float(item_details.get('cost_price', 0.0)))
            self.sale_price_input.setValue(float(item_details.get('sale_price', 0.0)))
        
            # Set expiry
            has_expiry = item_details.get('has_expiry', False)
            print(f"Has Expiry: {has_expiry}")  # إضافة هنا
            print(f"Expiry Date: {item_details.get('expiry_date')}")  # إضافة هنا

            self.has_expiry_check.setChecked(bool(has_expiry))
            if has_expiry and item_details.get('expiry_date'):
                try:
                    self.expiry_date_input.setDate(QDate.fromString(item_details['expiry_date'], Qt.ISODate))
                except:
                    self.expiry_date_input.setDate(QDate.currentDate())
    
        except Exception as e:
            print(f"Error in load_item_details: {e}")
            QMessageBox.warning(self, "خطأ", f"حدث خطأ في تحميل البيانات: {str(e)}")

    def set_category_combo(self, cat_id):
        """تعيين التصنيف الفرعي بعد التأكد من تحميله"""
        idx = self.category_combo.findData(cat_id)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)

    def add_item(self):
        if not self.validate_inputs():
            return
            
        try:
            # Prepare item data
            item_data = {
                'item_code': self.item_code_input.text(),
                'item_name_ar': self.item_name_ar_input.text(),
                'item_type': self.item_type_combo.currentText(),
                'parent_category_id': self.parent_category_combo.currentData(),
                'category_id': self.category_combo.currentData(),
                'cost_price': self.cost_price_input.value(),
                'sale_price': self.sale_price_input.value(),
                'min_stock_limit': self.min_stock_input.value(),
                'max_stock_limit': self.max_stock_input.value(),
                'reorder_point': self.reorder_point_input.value(),
                'has_expiry': self.has_expiry_check.isChecked(),
                'expiry_date': self.expiry_date_input.date().toString(Qt.ISODate) 
                            if self.has_expiry_check.isChecked() else None
            }
            
            # Prepare units data
            units_data = []
            main_unit_id = self.main_unit_combo.currentData()
            if main_unit_id:
                units_data.append({
                    'unit_id': main_unit_id,
                    'is_main': True,
                    'conversion_factor': 1.0
                })
                
                medium_unit_id = self.medium_unit_combo.currentData()
                if medium_unit_id:
                    units_data.append({
                        'unit_id': medium_unit_id,
                        'is_medium': True,
                        'conversion_factor': self.main_to_medium_factor.value()
                    })
                    
                    small_unit_id = self.small_unit_combo.currentData()
                    if small_unit_id:
                        units_data.append({
                            'unit_id': small_unit_id,
                            'is_small': True,
                            'conversion_factor': self.medium_to_small_factor.value()
                        })
            
            # Save to database
            if self.manager.create_item(item_data, units_data):
                QMessageBox.information(self, "نجاح", "تمت إضافة الصنف بنجاح")
                self.load_main_table()
                self.clear_form()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في إضافة الصنف")
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {str(e)}")

    def update_item(self):
        if not self.selected_item_id:
            QMessageBox.warning(self, "تحذير", "يجب اختيار صنف للتعديل")
            return
            
        if self.has_movements():
            QMessageBox.warning(self, "تحذير", "لا يمكن تعديل صنف له حركات")
            return
            
        if not self.validate_inputs():
            return
            
        try:
            item_data = {
                'item_name_ar': self.item_name_ar_input.text(),
                'item_type': self.item_type_combo.currentText(),
                'parent_category_id': self.parent_category_combo.currentData(),
                'category_id': self.category_combo.currentData(),
                'cost_price': self.cost_price_input.value(),
                'sale_price': self.sale_price_input.value(),
                'min_stock_limit': self.min_stock_input.value(),
                'max_stock_limit': self.max_stock_input.value(),
                'reorder_point': self.reorder_point_input.value(),
                'has_expiry': self.has_expiry_check.isChecked(),
                'expiry_date': self.expiry_date_input.date().toString(Qt.ISODate) 
                            if self.has_expiry_check.isChecked() else None
            }
            
            units_data = []
            main_unit_id = self.main_unit_combo.currentData()
            if main_unit_id:
                units_data.append({
                    'unit_id': main_unit_id,
                    'is_main': True,
                    'conversion_factor': 1.0
                })
                
                medium_unit_id = self.medium_unit_combo.currentData()
                if medium_unit_id:
                    units_data.append({
                        'unit_id': medium_unit_id,
                        'is_medium': True,
                        'conversion_factor': self.main_to_medium_factor.value()
                    })
                    
                    small_unit_id = self.small_unit_combo.currentData()
                    if small_unit_id:
                        units_data.append({
                            'unit_id': small_unit_id,
                            'is_small': True,
                            'conversion_factor': self.medium_to_small_factor.value()
                        })
            
            if self.manager.update_item(self.selected_item_id, item_data, units_data):
                QMessageBox.information(self, "نجاح", "تم تعديل الصنف بنجاح")
                self.load_main_table()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في تعديل الصنف")
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ: {str(e)}")

    def delete_item(self):
        if not self.selected_item_id:
            QMessageBox.warning(self, "تحذير", "يجب اختيار صنف للحذف")
            return
            
        if self.has_movements():
            QMessageBox.warning(self, "تحذير", "لا يمكن حذف صنف له حركات")
            return
            
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا الصنف؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.manager.delete_item(self.selected_item_id):
                    QMessageBox.information(self, "نجاح", "تم حذف الصنف بنجاح")
                    self.load_main_table()
                    self.clear_form()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل في حذف الصنف")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ: {str(e)}")

    def search_items(self):
        search_term = self.search_input.text().strip()
        if not search_term:
            self.load_main_table()
            return
            
        try:
            # البحث يدوياً في البيانات المحملة
            all_items = self.manager.list_items_with_movements()
            filtered_items = []
            
            for item in all_items:
                if (search_term.lower() in item['item_name_ar'].lower() or 
                    search_term.lower() in item['item_code'].lower() or
                    search_term.lower() in item.get('category_name', '').lower()):
                    filtered_items.append(item)
            
            self.populate_table(filtered_items)
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء البحث: {str(e)}")

    def has_movements(self):
        current_row = self.items_table.currentRow()
        if current_row >= 0:
            movement_count = int(self.items_table.item(current_row, 12).text())
            return movement_count > 0
        return False

    def validate_inputs(self):
        if not self.parent_category_combo.currentData():
            QMessageBox.warning(self, "تحذير", "يجب اختيار تصنيف أب")
            return False
            
        if not self.item_code_input.text():
            QMessageBox.warning(self, "تحذير", "يجب إدخال كود الصنف")
            return False
            
        if not self.item_name_ar_input.text():
            QMessageBox.warning(self, "تحذير", "يجب إدخال اسم الصنف")
            return False
            
        if not self.main_unit_combo.currentData():
            QMessageBox.warning(self, "تحذير", "يجب اختيار وحدة كبرى")
            return False
            
        return True

    def clear_form(self):
        self.selected_item_id = None
        self.add_button.setEnabled(True)
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        
        self.parent_category_combo.setCurrentIndex(0)
        self.item_code_input.clear()
        self.item_name_ar_input.clear()
        self.item_type_combo.setCurrentIndex(0)
        self.category_combo.setCurrentIndex(0)
        self.main_unit_combo.setCurrentIndex(0)
        self.medium_unit_combo.setCurrentIndex(0)
        self.small_unit_combo.setCurrentIndex(0)
        self.main_to_medium_factor.setValue(1.0)
        self.medium_to_small_factor.setValue(1.0)
        self.min_stock_input.setValue(0.0)
        self.max_stock_input.setValue(0.0)
        self.reorder_point_input.setValue(0.0)
        self.cost_price_input.setValue(0.0)
        self.sale_price_input.setValue(0.0)
        self.has_expiry_check.setChecked(False)
        self.expiry_date_input.setDate(QDate.currentDate())
        self.items_table.clearSelection()
        self.search_input.clear()
#═════════════════════════════════════════════════════════════════════════════════════════════════════════════════#
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set Arabic font
    font = QFont()
    font.setFamily("Arial")
    font.setPointSize(10)
    app.setFont(font)
    
    window = ItemsUI("database/inventory.db")
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec_())
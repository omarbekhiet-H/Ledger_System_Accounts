from PyQt5.QtGui import QFont, QColor, QIcon
from PyQt5.QtWidgets import QApplication, QStyle
from PyQt5.QtCore import Qt
import os

class ERPTheme:
    """كلاس شامل لإدارة التنسيقات والأيقونات في نظام ERP"""
    
    # ============= إعدادات التطبيق العامة =============
    @staticmethod
    def setup_app_theme(app):
        """تهيئة إعدادات التطبيق العامة"""
        app.setStyle("Fusion")
        app.setLayoutDirection(Qt.RightToLeft)
        app.setFont(ERPTheme.get_font())
        
        # تحميل ملف الأنماط إذا وجد
        style_path = os.path.join("ui", "themes", "erp_style.qss")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())

    # ============= إدارة الخطوط =============
    @staticmethod
    def get_font(size=12, bold=False, italic=False, family="Arial"):
        """إرجاع خط مخصص"""
        font = QFont(family, size)
        font.setBold(bold)
        font.setItalic(italic)
        return font

    # ============= إدارة الألوان =============
    @staticmethod
    def get_colors(context="default"):
        """إرجاع مجموعة ألوان حسب السياق"""
        colors = {
            "default": {
                "primary": QColor(53, 53, 53),
                "secondary": QColor(35, 35, 35),
                "text": QColor(255, 255, 255),
                "highlight": QColor(42, 130, 218),
            },
            "financial": {
                "debit": QColor(220, 53, 69),
                "credit": QColor(40, 167, 69),
                "balance": QColor(255, 193, 7),
            },
            "inventory": {
                "in_stock": QColor(40, 167, 69),
                "low_stock": QColor(255, 193, 7),
                "out_of_stock": QColor(220, 53, 69),
            },
            "status": {
                "active": QColor(40, 167, 69),
                "inactive": QColor(108, 117, 125),
                "pending": QColor(255, 193, 7),
                "rejected": QColor(220, 53, 69),
            }
        }
        return colors.get(context, colors["default"])

    # ============= إدارة الأيقونات =============
    @staticmethod
    def get_icon(icon_name, size=None):
        """إرجاع أيقونة حسب الاسم"""
        icons = {
            # أيقونات عامة
            "add": QApplication.style().standardIcon(QStyle.SP_FileDialogNewFolder),
            "edit": QApplication.style().standardIcon(QStyle.SP_FileDialogDetailedView),
            "delete": QApplication.style().standardIcon(QStyle.SP_TrashIcon),
            "save": QApplication.style().standardIcon(QStyle.SP_DialogSaveButton),
            "refresh": QApplication.style().standardIcon(QStyle.SP_BrowserReload),
            "search": QApplication.style().standardIcon(QStyle.SP_FileDialogStart),
            "print": QApplication.style().standardIcon(QStyle.SP_FileDialogContentsView),
            "export": QApplication.style().standardIcon(QStyle.SP_ArrowDown),
            "import": QApplication.style().standardIcon(QStyle.SP_ArrowUp),
            
            # أيقونات المالية
            "journal": QIcon(":/icons/journal.png"),
            "invoice": QIcon(":/icons/invoice.png"),
            "payment": QIcon(":/icons/payment.png"),
            "receipt": QIcon(":/icons/receipt.png"),
            
            # أيقونات المخازن
            "inventory": QIcon(":/icons/inventory.png"),
            "product": QIcon(":/icons/product.png"),
            "warehouse": QIcon(":/icons/warehouse.png"),
            "barcode": QIcon(":/icons/barcode.png"),
            
            # أيقونات الموارد البشرية
            "employee": QIcon(":/icons/employee.png"),
            "department": QIcon(":/icons/department.png"),
            "attendance": QIcon(":/icons/attendance.png"),
            "payroll": QIcon(":/icons/payroll.png"),
            
            # أيقونات العملاء والموردين
            "customer": QIcon(":/icons/customer.png"),
            "supplier": QIcon(":/icons/supplier.png"),
            "contact": QIcon(":/icons/contact.png"),
            
            # أيقونات التقارير
            "report": QIcon(":/icons/report.png"),
            "dashboard": QIcon(":/icons/dashboard.png"),
            "chart": QIcon(":/icons/chart.png"),
            
            # أيقونات النظام
            "settings": QIcon(":/icons/settings.png"),
            "user": QIcon(":/icons/user.png"),
            "logout": QIcon(":/icons/logout.png"),
            "help": QIcon(":/icons/help.png"),
        }
        
        icon = icons.get(icon_name, QIcon())
        if size and not icon.isNull():
            icon = icon.pixmap(size, size).toImage()
        return icon

    # ============= أنماط الويدجات =============
    @staticmethod
    def get_button_style(color="primary", size="medium"):
        """إرجاع ستايل زر مخصص"""
        sizes = {
            "small": "padding: 4px 8px; font-size: 10px;",
            "medium": "padding: 6px 12px; font-size: 12px;",
            "large": "padding: 8px 16px; font-size: 14px;"
        }
        
        colors = ERPTheme.get_colors()
        color = colors.get(color, colors["primary"])
        
        return f"""
            QPushButton {{
                background-color: {color.name()};
                color: white;
                border: none;
                {sizes.get(size, sizes["medium"])}
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {color.lighter(120).name()};
            }}
            QPushButton:disabled {{
                background-color: {color.darker(150).name()};
            }}
        """

    @staticmethod
    def get_table_style():
        """إرجاع ستايل الجداول"""
        return """
            QTableView {
                gridline-color: #e0e0e0;
                alternate-background-color: #f5f5f5;
            }
            QHeaderView::section {
                background-color: #607d8b;
                color: white;
                padding: 4px;
            }
        """

    # ============= أنماط خاصة بوحدات ERP =============
    @staticmethod
    def get_financial_status_style(status):
        """إرجاع تنسيقات حالة القيود المالية"""
        status_styles = {
            "draft": {"color": QColor(108, 117, 125), "bg": QColor(248, 249, 250)},
            "posted": {"color": QColor(40, 167, 69), "bg": QColor(220, 255, 220)},
            "canceled": {"color": QColor(220, 53, 69), "bg": QColor(255, 220, 220)},
            "under_review": {"color": QColor(255, 193, 7), "bg": QColor(255, 255, 220)},
        }
        return status_styles.get(status.lower(), {"color": Qt.black, "bg": Qt.white})

    @staticmethod
    def get_inventory_status_style(quantity, threshold=10):
        """إرجاع تنسيقات حالة المخزون"""
        if quantity <= 0:
            return {"color": QColor(220, 53, 69), "bg": QColor(255, 220, 220)}
        elif quantity <= threshold:
            return {"color": QColor(255, 193, 7), "bg": QColor(255, 255, 220)}
        else:
            return {"color": QColor(40, 167, 69), "bg": QColor(220, 255, 220)}
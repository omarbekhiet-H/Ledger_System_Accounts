# ui/styles/report_styles.py

from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGroupBox, QLabel, QTableWidget, QPushButton

class ReportStyles:
    """
    كلاس يحتوي على الأنماط الموحدة لجميع تقارير النظام
    """
    
    # ===== الألوان الأساسية =====
    COLORS = {
        'primary': '#3498db',      # أزرق رئيسي
        'primary_dark': '#2980b9',  # أزرق غامق
        'primary_light': '#d4e6f7', # أزرق فاتح
        'secondary': '#2ecc71',     # أخضر ثانوي
        'danger': '#e74c3c',        # أحضر خطأ
        'warning': '#f39c12',       # أصفر تحذير
        'light': '#ecf0f1',         # خلفية فاتحة
        'dark': '#2c3e50',          # نص غامق
        'white': '#ffffff',         # أبيض
        'gray': '#95a5a6',         # رمادي
    }

    # ===== الخطوط =====
    FONTS = {
        'title': QFont('Arial', 18, QFont.Bold),
        'subtitle': QFont('Arial', 14, QFont.Bold),
        'body': QFont('Arial', 12),
        'table_header': QFont('Arial', 10, QFont.Bold),
        'table_content': QFont('Arial', 10),
    }

    # ===== الأنماط الأساسية =====
    BASE_STYLE = f"""
        /* النافذة الرئيسية */
        QWidget {{
            background-color: {COLORS['light']};
            font-family: Arial;
            color: {COLORS['dark']};
        }}

        /* العناوين */
        .title-label {{
            font-size: 18px;
            font-weight: bold;
            color: {COLORS['dark']};
            margin-bottom: 15px;
        }}

        /* المجموعات */
        .group-box {{
            border: 2px solid {COLORS['primary']};
            border-radius: 10px;
            margin-top: 10px;
            background-color: {COLORS['white']};
        }}

        .group-box::title {{
            color: {COLORS['primary']};
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 10px;
            font-weight: bold;
        }}
    """

    # ===== أنماط الجداول =====
    TABLE_STYLE = f"""
        QTableWidget {{
            background-color: {COLORS['white']};
            border: 1px solid #dddddd;
            gridline-color: #eeeeee;
            alternate-background-color: {COLORS['primary_light']};
            selection-background-color: {COLORS['primary']};
            selection-color: {COLORS['white']};
        }}

        QHeaderView::section {{
            background-color: {COLORS['primary']};
            color: {COLORS['white']};
            padding: 5px;
            border: none;
            font-weight: bold;
        }}

        QTableWidget::item {{
            padding: 5px;
        }}
    """
    

    # ===== أنماط الأزرار =====
    BUTTON_STYLE = f"""
        QPushButton {{
            background-color: {COLORS['primary']};
            color: {COLORS['white']};
            border-radius: 6px;
            padding: 8px 16px;
            min-width: 100px;
            border: none;
            font-weight: bold;
        }}

        QPushButton:hover {{
            background-color: {COLORS['primary_dark']};
        }}

        QPushButton:pressed {{
            background-color: {COLORS['primary_dark']};
            padding-top: 9px;
            padding-bottom: 7px;
        }}

        QPushButton:disabled {{
            background-color: {COLORS['gray']};
            color: {COLORS['light']};
        }}
    """

    @classmethod
    def get_style(cls, style_name):
        """إرجاع النمط المطلوب حسب الاسم"""
        styles = {
            'base': cls.BASE_STYLE,
            'table': cls.TABLE_STYLE,
            'button': cls.BUTTON_STYLE,
            'full': cls.BASE_STYLE + cls.TABLE_STYLE + cls.BUTTON_STYLE
        }
        return styles.get(style_name, '')

    @classmethod
    def get_color(cls, color_name):
        """إرجاع اللون المطلوب حسب الاسم"""
        return cls.COLORS.get(color_name, '#000000')

    @classmethod
    def get_font(cls, font_name):
        """إرجاع الخط المطلوب حسب الاسم"""
        return cls.FONTS.get(font_name, QFont('Arial', 10))

    @classmethod
    def apply_style(cls, widget, style_type='full'):
        """تطبيق النمط على الويدجت"""
        widget.setStyleSheet(cls.get_style(style_type))

    @classmethod
    def style_table(cls, table_widget):
        """تطبيق تنسيق الجدول مع إعدادات إضافية"""
        cls.apply_style(table_widget, 'table')
        table_widget.setAlternatingRowColors(True)
        table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        table_widget.setSelectionMode(QTableWidget.SingleSelection)
        table_widget.horizontalHeader().setHighlightSections(False)
        table_widget.verticalHeader().setVisible(False)

    @classmethod
    def create_title_label(cls, text):
        """إنشاء عنوان مع التنسيق المحدد"""
        label = QLabel(text)
        label.setFont(cls.get_font('title'))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"color: {cls.get_color('dark')}; margin-bottom: 15px;")
        return label

    @classmethod
    def create_group_box(cls, title):
        """إنشاء مجموعة مع التنسيق المحدد"""
        group = QGroupBox(title)
        group.setFont(cls.get_font('subtitle'))
        cls.apply_style(group, 'base')
        return group
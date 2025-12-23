import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QComboBox, QDateEdit,
    QGridLayout, QTabWidget, QTextEdit, QCheckBox, QDialog, QSpinBox, QDoubleSpinBox,
    QGroupBox
)
from PyQt5.QtCore import Qt, QFile, QTextStream
from PyQt5.QtGui import QFont

# =====================================================================
# إصلاح مسار وحدة database أولاً
# =====================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))

# إضافة مسار المشروع إلى sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)  # استخدام insert(0) بدلاً من append

# إضافة مسار database بشكل صريح
database_path = os.path.join(project_root, 'database')
if database_path not in sys.path:
    sys.path.insert(0, database_path)

print(f"📁 مسار المشروع: {project_root}")
print(f"📁 مسار قاعدة البيانات: {database_path}")
print(f"📋 مسارات Python: {sys.path}")

# الآن استيراد دالة الاتصال
try:
    from database.db_connection import get_fixed_assets_db_connection
    print("✅ تم استيراد دالة الاتصال بنجاح")
except Exception as e:
    print(f"⚠️ get_fixed_assets_db_connection Import fallback: {e}")
    
    # دالة احتياطية محسنة
    def get_fixed_assets_db_connection():
        try:
            # إنشاء اتصال مباشر بقاعدة البيانات
            db_path = os.path.join(database_path, 'fixed_assets.db')
            print(f"🔗 محاولة الاتصال بـ: {db_path}")
            
            # التأكد من وجود المجلد
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            conn = sqlite3.connect(db_path)
            print("✅ تم الاتصال بقاعدة البيانات بنجاح")
            return conn
        except Exception as e:
            print(f"❌ فشل في الاتصال بقاعدة البيانات: {e}")
            QMessageBox.critical(None, "خطأ", f"❌ فشل في الاتصال بقاعدة البيانات: {e}")
            return None


def load_stylesheet():
    """تحميل ملف QSS"""
    try:
        # محاولة البحث عن ملف الأنماط في مسارات مختلفة
        possible_paths = [
            os.path.abspath(os.path.join(current_dir, '..', 'styles', 'styles.qss')),
            os.path.abspath(os.path.join(current_dir, '..', '..', 'styles', 'styles.qss')),
            os.path.abspath(os.path.join(current_dir, 'styles.qss'))
        ]
        
        for style_path in possible_paths:
            if os.path.exists(style_path):
                file = QFile(style_path)
                if file.open(QFile.ReadOnly | QFile.Text):
                    stream = QTextStream(file)
                    style = stream.readAll()
                    file.close()
                    return style
        
        print("⚠️ تحذير: لم يتم العثور على ملف الأنماط في أي من المسارات التالية:")
        for path in possible_paths:
            print(f"   - {path}")
        return ""
        
    except Exception as e:
        print(f"❌ خطأ في تحميل ملف الأنماط: {e}")
        return ""

# استيراد التبويبات المعدلة
try:
    from fixed_assets_depreciation_ui import DepreciationMethodsTab
    from fixed_assets_categories_ui import CategoriesTab
    from fixed_assets_locations_ui import AssetLocationsWindow
    from fixed_assets_responsibles_ui import ResponsiblesTab
    from fixed_assets_units_ui import UnitsTab
except ImportError as e:
    print(f"❌ خطأ في استيراد التبويبات: {e}")
    
    # إنشاء فئات بديلة في حالة فشل الاستيراد
    class DepreciationMethodsTab(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout()
            label = QLabel("لا يمكن تحميل تبويب طرق الإهلاك")
            layout.addWidget(label)
            self.setLayout(layout)
    
    class CategoriesTab(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout()
            label = QLabel("لا يمكن تحميل تبويب التصنيفات")
            layout.addWidget(label)
            self.setLayout(layout)
    
    class AssetLocationsWindow(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout()
            label = QLabel("لا يمكن تحميل تبويب المواقع")
            layout.addWidget(label)
            self.setLayout(layout)
    
    class ResponsiblesTab(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout()
            label = QLabel("لا يمكن تحميل تبويب المسؤولين")
            layout.addWidget(label)
            self.setLayout(layout)
    
    class UnitsTab(QWidget):
        def __init__(self):
            super().__init__()
            layout = QVBoxLayout()
            label = QLabel("لا يمكن تحميل تبويب وحدات القياس")
            layout.addWidget(label)
            self.setLayout(layout)

class FixedAssetsSettingsMain(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("إعدادات الأصول الثابتة")
        self.setGeometry(100, 100, 1200, 700)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(load_stylesheet())
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("إعدادات الأصول الثابتة")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        try:
            # إنشاء التبويبات مع معالجة الأخطاء
            self.dep_method_tab = DepreciationMethodsTab()
            self.categories_tab = CategoriesTab()
            
            # تحويل نافذة المواقع إلى تبويب
            self.locations_tab = QWidget()
            locations_layout = QVBoxLayout()
            self.locations_window = AssetLocationsWindow()
            locations_layout.addWidget(self.locations_window)
            self.locations_tab.setLayout(locations_layout)
            
            self.responsibles_tab = ResponsiblesTab()
            self.units_tab = UnitsTab()
            
            self.tabs.addTab(self.dep_method_tab, "طرق الإهلاك")
            self.tabs.addTab(self.categories_tab, "التصنيفات")
            self.tabs.addTab(self.locations_tab, "المواقع")
            self.tabs.addTab(self.responsibles_tab, "المسؤولين")
            self.tabs.addTab(self.units_tab, "وحدات القياس")
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء التبويبات: {e}")
            error_widget = QWidget()
            error_layout = QVBoxLayout()
            error_label = QLabel(f"خطأ في تحميل الإعدادات: {str(e)}")
            error_layout.addWidget(error_label)
            error_widget.setLayout(error_layout)
            self.tabs.addTab(error_widget, "خطأ")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # التحقق من اتصال قاعدة البيانات
    conn = get_fixed_assets_db_connection()
    if conn is None:
        print("⚠️ تحذير: لا يمكن الاتصال بقاعدة البيانات. سيتم العمل في وضع العرض فقط.")
        # يمكنك عرض رسالة للمستخدم هنا إذا أردت
    else:
        conn.close()
    
    window = FixedAssetsSettingsMain()
    window.show()
    sys.exit(app.exec_())
# my_erp_projects/database/populate_single_db_for_testing.py

import sys
import os

# إضافة المسار الجذر للمشروع لتمكين الاستيراد الصحيح
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.db_schema_manager import DBSchemaManager
from PyQt5.QtWidgets import QApplication # ضروري إذا كانت هناك رسائل QMessageBox تظهر

if __name__ == '__main__':
    # تهيئة QApplication لضمان عمل رسائل QMessageBox بشكل صحيح
    # لا نحتاج إلى app.exec_() هنا لأننا لا نشغل تطبيق GUI كاملاً
    app = QApplication(sys.argv)

    schema_manager = DBSchemaManager()

    print("--- خيارات تعبئة قاعدة البيانات الفردية للاختبار ---")
    print("1. تهيئة Financials DB (الحسابات العامة)")
    print("2. تهيئة Inventory DB (المخازن)")
    print("3. تهيئة Fixed Assets DB (الأصول الثابتة)")
    print("4. تهيئة Users DB (إدارة المستخدمين)")
    print("أدخل رقم الخيار الذي تريد اختباره (أو 0 للخروج):")

    while True:
        choice = input("خيارك: ")
        if choice == '1':
            print("\nبدء تهيئة Financials DB...")
            schema_manager.initialize_specific_database('financials')
            break
        elif choice == '2':
            print("\nبدء تهيئة Inventory DB...")
            schema_manager.initialize_specific_database('inventory')
            break
        elif choice == '3':
            print("\nبدء تهيئة Fixed Assets DB...")
            schema_manager.initialize_specific_database('fixed_assets')
            break
        elif choice == '4':
            print("\nبدء تهيئة Users DB...")
            schema_manager.initialize_specific_database('users')
            break
        elif choice == '0':
            print("الخروج.")
            break
        else:
            print("خيار غير صالح. الرجاء إدخال رقم من 0 إلى 4.")

    # إزالة هذا السطر: sys.exit(app.exec_())
    # السكريبت سينتهي تلقائياً بعد انتهاء حلقة while.
    # إذا ظهرت أي QMessageBox، فإنها ستكون حوارية (modal) وستغلق قبل أن يستمر الكود.
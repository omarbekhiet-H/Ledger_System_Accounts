# database/connection_utils.py

from PyQt5.QtWidgets import QMessageBox

def show_error_message(title="خطأ", message="حدث خطأ غير متوقع."):
    """
    تعرض رسالة خطأ قياسية باستخدام QMessageBox.
    """
    QMessageBox.critical(None, title, message)

# يمكنك إضافة أي دوال مساعدة أخرى هنا حسب الحاجة
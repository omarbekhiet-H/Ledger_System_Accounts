import os
import sys
from PyQt5.QtWidgets import QApplication, QTabWidget
import sys

# ================================================================
# إعدادات المسارات الأساسية
# ================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..','..','..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# استيراد واجهات المستخدم من ملفاتها
from ui.inventory.purchase.inventory_cycle_ui import PurchaseRequestUI
#from ui.inventory.purchase.purchase_order_ui import PurchaseOrderUI
#from ui.inventory.purchase.purchase_invoice_ui import PurchaseInvoiceUI

def main():
    app = QApplication(sys.argv)
    db_path = "database/inventory.db"
    
    # إنشاء النافذة الرئيسية
    window = QTabWidget()
    window.setWindowTitle("نظام إدارة المشتريات والمخازن")
    
    # إضافة الواجهات كألسنة
    window.addTab(PurchaseRequestUI(db_path), "طلب الاحتياجات")
    #window.addTab(PurchaseOrderUI(db_path), "أوامر الشراء")
    #window.addTab(PurchaseInvoiceUI(db_path), "فواتير الشراء")
    
    window.resize(1280, 720)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.manager.inventory.purchase.purchase_request_manager import PurchaseRequest
from database.manager.inventory.purchase.supply_order_manager import SupplyOrder
from database.manager.inventory.purchase.receipt_permit_manager import ReceiptPermit
from database.manager.inventory.purchase.addition_permit_manager import AdditionPermit
from database.manager.inventory.purchase.inventory_invoice_manager import InventoryInvoice

class PurchaseWorkflow:
    def __init__(self):
        pass

    def run_complete_workflow(self, requester_id, department_id, supplier_id, warehouse_id, items):
        """تشغيل سير العمل الكامل"""
        try:
            print("=" * 50)
            print("بدء سير العمل الكامل للمشتريات")
            print("=" * 50)

            # 1. إنشاء طلب شراء
            print("\n1. إنشاء طلب الشراء...")
            pr = PurchaseRequest()
            request_id = pr.create_request(requester_id, department_id, "طلب شراء تلقائي عبر النظام")

            for item_id, quantity, unit_price in items:
                pr.add_request_item(request_id, item_id, quantity, unit_price)
            
            # يجب وجود دالة لتغيير حالة الطلب إلى 'approved' ليظهر في شاشة أمر التوريد
            # pr.update_status(request_id, 'approved')
            pr.close()

            # 2. إنشاء أمر توريد
            print("\n2. إنشاء أمر التوريد...")
            so = SupplyOrder()
            # تعديل مقترح: إضافة وسيطات تتوافق مع تعريف الدالة
            order_id = so.create_supply_order(request_id, supplier_id, "أمر توريد تلقائي عبر النظام", 7) # 7 أيام تسليم افتراضية
            so.close()

            # 3. إنشاء إذن استلام
            print("\n3. إنشاء إذن الاستلام...")
            rp = ReceiptPermit()
            permit_id = rp.create_receipt_permit(order_id, warehouse_id)

            # تحديث الكميات المستلمة
            for item_id, quantity, _ in items:
                # تعديل مقترح: إضافة وسيط الملاحظات ليتوافق مع تعريف الدالة
                rp.update_received_quantity(permit_id, item_id, quantity, "استلام تلقائي")

            rp.complete_receipt(permit_id)
            rp.close()

            # 4. إنشاء إذن إضافة
            print("\n4. إنشاء إذن الإضافة...")
            ap = AdditionPermit()
            addition_id = ap.create_addition_permit(permit_id)
            ap.complete_addition(addition_id)
            ap.close()

            # 5. إنشاء فاتورة مخزنية
            print("\n5. إنشاء الفاتورة المخزنية...")
            ii = InventoryInvoice()
            invoice_id = ii.create_inventory_invoice(addition_id, supplier_id)
            ii.complete_invoice(invoice_id)
            ii.close()

            print("\n" + "=" * 50)
            print("تم تنفيذ سير العمل بنجاح!")
            print("=" * 50)

            return {
                'request_id': request_id,
                'order_id': order_id,
                'permit_id': permit_id,
                'addition_id': addition_id,
                'invoice_id': invoice_id
            }

        except Exception as e:
            print(f"\nخطأ في سير العمل: {e}")
            import traceback
            traceback.print_exc()
            return None

# تشغيل سير العمل
if __name__ == "__main__":
    workflow = PurchaseWorkflow()

    # بيانات مثال (item_id, quantity, unit_price)
    items_to_purchase = [
        (1, 100, 10.5),  # صنف 1، كمية 100، سعر 10.5
        (2, 50, 25.0)    # صنف 2، كمية 50، سعر 25.0
    ]

    result = workflow.run_complete_workflow(
        requester_id=1,
        department_id=1,
        supplier_id=1,
        warehouse_id=1,
        items=items_to_purchase
    )

    if result:
        print("\nنتائج سير العمل:")
        print(f"رقم طلب الشراء: {result['request_id']}")
        print(f"رقم أمر التوريد: {result['order_id']}")
        print(f"رقم إذن الاستلام: {result['permit_id']}")
        print(f"رقم إذن الإضافة: {result['addition_id']}")
        print(f"رقم الفاتورة المخزنية: {result['invoice_id']}")
    else:
        print("فشل في تنفيذ سير العمل!")
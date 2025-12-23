# auto_year_close.py

from database.manager.financial.transactions.financial_year_manager import FinancialYearManager
from database.db_connection import get_financials_db_connection

def show_report(mgr):
    """طباعة تقرير مفصل للسنوات المالية"""
    years = mgr.get_detailed_years_report()
    print("\n📑 تقرير السنوات المالية:")
    for y in years:
        print(
            f"- {y['year_name']} ({y['start_date']} → {y['end_date']}) "
            f"[{'مقفلة' if y['is_closed'] else 'مفتوحة'}]"
        )
        print(f"   الإيرادات: {y['revenues']:,}")
        print(f"   المصروفات: {y['expenses']:,}")
        print(f"   صافي الربح: {y['net_income']:,}")
        print(f"   قيد الإقفال: {y['closing_entry']}")
        print("-" * 60)

def main():
    mgr = FinancialYearManager(get_financials_db_connection)

    # جلب كل السنوات
    years = mgr.get_all_financial_years()
    print("📊 السنوات الحالية:", years)

    if not years:
        print("⚠️ لا توجد سنوات مالية - سيتم إنشاء سنة جديدة...")
        if mgr.create_financial_year():
            print("✅ تم إنشاء أول سنة مالية")
            show_report(mgr)
        return

    # البحث عن سنة مفتوحة
    open_year = mgr.get_active_financial_year()

    if not open_year:
        print("⚠️ كل السنوات مقفولة - سيتم إنشاء سنة جديدة...")
        if mgr.create_financial_year():
            print("✅ تم إنشاء السنة التالية")
            show_report(mgr)
        return

    print(f"➡️ السنة المفتوحة: {open_year['year_name']} ({open_year['start_date']} → {open_year['end_date']})")

    # محاولة إقفال السنة
    can_close, msg = mgr.validate_year_for_closing(open_year['id'])
    if not can_close:
        print(f"❌ لا يمكن الإقفال: {msg}")
        return

    success, message = mgr.create_year_end_closing_entry(open_year['id'])
    if success:
        print("✅ تم الإقفال:", message)
        show_report(mgr)
    else:
        print("❌ فشل الإقفال:", message)

if __name__ == "__main__":
    main()

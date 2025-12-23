# api/services/closing_api.py

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List
from database.services.year_end_closing import YearEndClosingService
from database.services.closing_setup import ClosingSetupService
from ui.service.dependencies import get_db_path

router = APIRouter(prefix="/financial-closing", tags=["Financial Closing"])

@router.get("/year/{year_id}/summary")
async def get_closing_summary(year_id: int, db_path: str = Depends(get_db_path)):
    """الحصول على ملخص إقفال السنة المالية"""
    service = YearEndClosingService(db_path)
    summary = service.get_closing_summary(year_id)
    return summary

@router.post("/year/{year_id}/execute")
async def execute_year_closing(year_id: int, user_id: int, db_path: str = Depends(get_db_path)):
    """تنفيذ إقفال السنة المالية"""
    service = YearEndClosingService(db_path)
    result = service.execute_year_closing(year_id, user_id)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result

@router.post("/year/{year_id}/reopen")
async def reopen_year(year_id: int, user_id: int, db_path: str = Depends(get_db_path)):
    """إعادة فتح سنة مالية مغلقة"""
    service = YearEndClosingService(db_path)
    success = service.reopen_financial_year(year_id, user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="فشل في إعادة فتح السنة المالية")
    
    return {"message": "تم إعادة فتح السنة المالية بنجاح"}

@router.get("/year/{year_id}/validation")
async def validate_year_closing(year_id: int, db_path: str = Depends(get_db_path)):
    """التحقق من إمكانية إقفال السنة المالية"""
    service = YearEndClosingService(db_path)
    can_close, errors = service.validate_year_for_closing(year_id)
    
    return {
        "can_close": can_close,
        "errors": errors
    }

@router.post("/setup/new-year")
async def setup_new_financial_year(year_data: Dict, db_path: str = Depends(get_db_path)):
    """إعداد سنة مالية جديدة"""
    setup_service = ClosingSetupService(db_path)
    
    try:
        year_id = setup_service.initialize_financial_year(**year_data)
        return {"year_id": year_id, "message": "تم إنشاء السنة المالية بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"فشل في إنشاء السنة المالية: {str(e)}")
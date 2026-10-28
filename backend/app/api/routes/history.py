from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from app.schemas.responses import HistoryItemResponse
from app.services.history_service import HistoryService

router = APIRouter(prefix="/api/history", tags=["Query History"])

@router.get("", response_model=List[HistoryItemResponse])
def get_history(limit: int = 50):
    try:
        return HistoryService.get_recent_history(limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch query history: {str(e)}"
        )

@router.post("/clear")
def clear_history() -> Dict[str, Any]:
    try:
        count = HistoryService.clear_history()
        return {"status": "success", "cleared_count": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear history: {str(e)}"
        )

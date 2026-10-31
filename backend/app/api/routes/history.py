from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.responses import HistoryItemResponse
from app.services.history_service import HistoryService
from app.database.models import User
from app.api.deps import get_optional_current_user

router = APIRouter(prefix="/api/history", tags=["Query History"])

@router.get("", response_model=List[HistoryItemResponse])
def get_history(
    limit: int = 50,
    current_user: User = Depends(get_optional_current_user)
):
    try:
        user_id = current_user.id if current_user else None
        supabase_id = getattr(current_user, "supabase_id", None) if current_user else None
        return HistoryService.get_recent_history(limit=limit, user_id=user_id, supabase_user_id=supabase_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch query history: {str(e)}"
        )

@router.post("/clear")
def clear_history(
    current_user: User = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    try:
        user_id = current_user.id if current_user else None
        supabase_id = getattr(current_user, "supabase_id", None) if current_user else None
        count = HistoryService.clear_history(user_id=user_id, supabase_user_id=supabase_id)
        return {"status": "success", "cleared_count": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear history: {str(e)}"
        )

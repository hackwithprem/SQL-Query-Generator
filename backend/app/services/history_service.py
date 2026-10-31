from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database.connection import SessionLocal
from app.database.models import QueryHistory
from app.schemas.responses import HistoryItemResponse
from app.services.supabase_service import SupabaseService

class HistoryService:
    @classmethod
    def record_query(
        cls,
        natural_query: str,
        generated_sql: str,
        executed: bool = False,
        status: str = "generated",
        execution_time_ms: Optional[float] = None,
        row_count: Optional[int] = None,
        error_message: Optional[str] = None,
        user_id: Optional[int] = None,
        supabase_user_id: Optional[str] = None
    ) -> QueryHistory:
        # Also persist to Supabase if configured
        if supabase_user_id and SupabaseService.is_configured():
            try:
                SupabaseService.record_query(
                    user_id=supabase_user_id,
                    natural_query=natural_query,
                    generated_sql=generated_sql,
                    executed=executed,
                    status=status,
                    execution_time_ms=execution_time_ms,
                    row_count=row_count,
                    error_message=error_message
                )
            except Exception as e:
                print(f"Notice: Supabase history logging: {e}")

        db: Session = SessionLocal()
        try:
            item = QueryHistory(
                user_id=user_id,
                natural_query=natural_query,
                generated_sql=generated_sql,
                executed=1 if executed else 0,
                status=status,
                execution_time_ms=execution_time_ms,
                row_count=row_count,
                error_message=error_message
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            return item
        finally:
            db.close()

    @classmethod
    def get_recent_history(
        cls,
        limit: int = 50,
        user_id: Optional[int] = None,
        supabase_user_id: Optional[str] = None
    ) -> List[HistoryItemResponse]:
        # If Supabase is configured and supabase_user_id is available, fetch from Supabase
        if supabase_user_id and SupabaseService.is_configured():
            sb_records = SupabaseService.get_user_history(user_id=supabase_user_id, limit=limit)
            if sb_records:
                return [
                    HistoryItemResponse(
                        id=r.get("id"),
                        natural_query=r.get("natural_query", ""),
                        generated_sql=r.get("generated_sql", ""),
                        executed=bool(r.get("executed", False)),
                        status=r.get("status", "generated"),
                        execution_time_ms=r.get("execution_time_ms"),
                        row_count=r.get("row_count"),
                        error_message=r.get("error_message"),
                        created_at=str(r.get("created_at", ""))
                    )
                    for r in sb_records
                ]

        db: Session = SessionLocal()
        try:
            query = db.query(QueryHistory)
            if user_id is not None:
                query = query.filter((QueryHistory.user_id == user_id) | (QueryHistory.user_id.is_(None)))
            records = query.order_by(desc(QueryHistory.id)).limit(limit).all()
            return [
                HistoryItemResponse(
                    id=r.id,
                    natural_query=r.natural_query,
                    generated_sql=r.generated_sql,
                    executed=bool(r.executed),
                    status=r.status,
                    execution_time_ms=r.execution_time_ms,
                    row_count=r.row_count,
                    error_message=r.error_message,
                    created_at=r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None
                )
                for r in records
            ]
        finally:
            db.close()

    @classmethod
    def clear_history(
        cls,
        user_id: Optional[int] = None,
        supabase_user_id: Optional[str] = None
    ) -> int:
        if supabase_user_id and SupabaseService.is_configured():
            SupabaseService.clear_user_history(user_id=supabase_user_id)

        db: Session = SessionLocal()
        try:
            query = db.query(QueryHistory)
            if user_id is not None:
                query = query.filter(QueryHistory.user_id == user_id)
            count = query.delete(synchronize_session=False)
            db.commit()
            return count
        finally:
            db.close()

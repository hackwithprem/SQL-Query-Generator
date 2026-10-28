from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database.connection import SessionLocal
from app.database.models import QueryHistory
from app.schemas.responses import HistoryItemResponse

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
        error_message: Optional[str] = None
    ) -> QueryHistory:
        db: Session = SessionLocal()
        try:
            item = QueryHistory(
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
    def get_recent_history(cls, limit: int = 50) -> List[HistoryItemResponse]:
        db: Session = SessionLocal()
        try:
            records = db.query(QueryHistory).order_by(desc(QueryHistory.id)).limit(limit).all()
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
    def clear_history(cls) -> int:
        db: Session = SessionLocal()
        try:
            count = db.query(QueryHistory).delete()
            db.commit()
            return count
        finally:
            db.close()

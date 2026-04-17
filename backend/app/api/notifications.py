from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database import get_db
from app.models.models import Worker, WorkerNotification
from app.services.auth_service import get_current_worker

router = APIRouter()


@router.get("/")
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    result = await db.execute(
        select(WorkerNotification)
        .where(WorkerNotification.worker_id == current_worker.id)
        .order_by(WorkerNotification.created_at.desc())
        .limit(50)
    )
    notifs = result.scalars().all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "body": n.body,
            "type": n.notif_type,
            "ref_id": n.ref_id,
            "is_read": n.is_read,
            "created_at": n.created_at,
        }
        for n in notifs
    ]


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    await db.execute(
        update(WorkerNotification)
        .where(
            WorkerNotification.id == notification_id,
            WorkerNotification.worker_id == current_worker.id,
        )
        .values(is_read=True)
    )
    await db.commit()
    return {"ok": True}


@router.post("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_worker: Worker = Depends(get_current_worker),
):
    await db.execute(
        update(WorkerNotification)
        .where(
            WorkerNotification.worker_id == current_worker.id,
            WorkerNotification.is_read == False,
        )
        .values(is_read=True)
    )
    await db.commit()
    return {"ok": True}

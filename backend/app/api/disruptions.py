from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.database import get_db
from app.models.models import DisruptionEvent, Worker
from app.schemas.schemas import DisruptionEventResponse
from app.services.auth_service import get_current_worker, get_current_auth_context, AuthContext
from app.services.disruption_service import check_disruptions
from app.services.notification_service import notify_disruption_detected
from app.config import settings

router = APIRouter()


@router.get("/active", response_model=list[DisruptionEventResponse])
async def get_active_disruptions(
    city: str = Query(..., description="City name"),
    db: AsyncSession = Depends(get_db),
):
    """Get all active disruption events for a city"""
    result = await db.execute(
        select(DisruptionEvent).where(
            DisruptionEvent.city == city,
            DisruptionEvent.is_active == True,
        )
    )
    return result.scalars().all()


@router.post("/simulate", response_model=list[DisruptionEventResponse])
async def simulate_disruption(
    city: str = Query(...),
    pincode: str = Query(...),
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth_context),
):
    """Simulate disruptions — always creates at least one event for demo."""
    from app.models.models import DisruptionType, DisruptionSeverity
    from app.services.disruption_service import get_dss
    from datetime import timedelta, timezone

    if not settings.DEMO_MODE_ENABLED or not auth.is_dev_mode or settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Simulation is available only in dev mode")

    current_worker = auth.worker
    city = current_worker.city or city
    pincode = current_worker.pincode or pincode

    events_data = await check_disruptions(city=city, pincode=pincode)

    if not events_data:
        events_data = [{
            "disruption_type": DisruptionType.HEAVY_RAIN,
            "severity": DisruptionSeverity.SEVERE,
            "city": city,
            "pincode": pincode,
            "dss_multiplier": get_dss(DisruptionType.HEAVY_RAIN, DisruptionSeverity.SEVERE, city, pincode),
            "raw_value": 70.0,
            "description": "64.5mm/hr rainfall (Heavy) - Simulated",
            "source": "OpenWeather API (Simulated)",
        }]

    events = []
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(minutes=5)

    for e in events_data:
        # Deduplicate: reuse existing active event of same type in last 5 min
        dup = await db.execute(
            select(DisruptionEvent).where(
                DisruptionEvent.city == city,
                DisruptionEvent.disruption_type == e["disruption_type"],
                DisruptionEvent.is_active == True,
                DisruptionEvent.started_at >= cutoff,
            )
        )
        existing = dup.scalar_one_or_none()
        if existing:
            events.append(existing)
            continue

        event = DisruptionEvent(
            disruption_type=e["disruption_type"],
            severity=e["severity"],
            city=city,
            pincode=pincode,
            dss_multiplier=e["dss_multiplier"],
            raw_value=e.get("raw_value"),
            description=e.get("description"),
            source=e.get("source"),
            started_at=now_utc,
            is_active=True,
        )
        db.add(event)
        events.append(event)

    await db.commit()
    for e in events:
        await db.refresh(e)
        await notify_disruption_detected(
            db=db,
            worker_ids=[current_worker.id],
            city=e.city,
            severity=e.severity.value,
            disruption_type=e.disruption_type.value,
            event_id=e.id,
        )
    await db.commit()

    return events


@router.get("/", response_model=list[DisruptionEventResponse])
async def list_disruptions(
    city: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(DisruptionEvent).order_by(DisruptionEvent.created_at.desc()).limit(50)
    if city:
        query = query.where(DisruptionEvent.city == city)
    result = await db.execute(query)
    return result.scalars().all()

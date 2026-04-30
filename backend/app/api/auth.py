from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from pydantic import BaseModel
from app.database import get_db
from app.models.models import Worker
from app.schemas.schemas import OTPRequest, OTPVerify, TokenResponse
from app.services.auth_service import generate_otp, send_otp_sms, verify_otp, create_access_token, create_refresh_token
from app.config import settings

router = APIRouter()


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/send-otp")
async def send_otp(payload: OTPRequest):
    # Basic abuse throttle. Production should also rate limit by IP/device at the edge.
    from app.services.auth_service import _redis, _use_redis
    if _use_redis:
        key = f"otp-send:{payload.phone}"
        attempts = _redis.incr(key)
        if attempts == 1:
            _redis.expire(key, 60)
        if attempts > 3:
            raise HTTPException(status_code=429, detail="Too many OTP requests. Try again later.")
    otp = generate_otp(payload.phone)
    await send_otp_sms(payload.phone, otp)
    return {"message": "OTP sent successfully", "phone": payload.phone}


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp_endpoint(payload: OTPVerify, db: AsyncSession = Depends(get_db)):
    is_dev_mode = (
        settings.DEV_OTP_ENABLED
        and settings.ENVIRONMENT != "production"
        and payload.otp == "123456"
    )
    if not verify_otp(payload.phone, payload.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )

    result = await db.execute(select(Worker).where(Worker.phone == payload.phone))
    worker = result.scalar_one_or_none()
    is_new = worker is None

    if is_new:
        worker = Worker(phone=payload.phone, name="", platform="zomato", city="", pincode="")
        db.add(worker)
        await db.commit()
        await db.refresh(worker)

    access_token = create_access_token({"sub": str(worker.id), "phone": worker.phone, "dev_mode": is_dev_mode})
    refresh_token = create_refresh_token({"sub": str(worker.id), "dev_mode": is_dev_mode})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        worker_id=worker.id,
        is_new_user=is_new,
        is_dev_mode=is_dev_mode,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )
    try:
        decoded = jwt.decode(payload.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        worker_id: str = decoded.get("sub")
        token_type: str = decoded.get("type")
        is_dev_mode = bool(decoded.get("dev_mode", False)) and settings.DEMO_MODE_ENABLED and settings.ENVIRONMENT != "production"
        if worker_id is None or token_type != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(Worker).where(Worker.id == str(worker_id)))
    worker = result.scalar_one_or_none()
    if worker is None:
        raise credentials_exception

    new_access = create_access_token({"sub": str(worker.id), "phone": worker.phone, "dev_mode": is_dev_mode})
    return TokenResponse(
        access_token=new_access,
        refresh_token=payload.refresh_token,
        worker_id=worker.id,
        is_new_user=False,
        is_dev_mode=is_dev_mode,
    )

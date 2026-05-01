import random
import httpx
import redis as redis_client
import hmac
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.database import get_db
from app.models.models import Worker

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


@dataclass
class AuthContext:
    worker: Worker
    is_dev_mode: bool

# Redis-backed OTP store — shared across all gunicorn workers
try:
    _redis = redis_client.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
    _redis.ping()
    _use_redis = True
except redis_client.RedisError:
    _use_redis = False
    otp_store: dict = {}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def send_otp_sms(phone: str, otp: str) -> bool:
    """Send OTP via 2Factor.in (free tier: 10k OTPs/month)."""
    api_key = settings.FAST2SMS_API_KEY.strip() if settings.FAST2SMS_API_KEY else ""
    if not api_key:
        print("[OTP] SMS not configured for " + phone[-4:].rjust(len(phone), "*"))
        return True
    number = phone.strip().lstrip("+")
    if number.startswith("91") and len(number) == 12:
        number = number[2:]
    number = number[-10:]
    try:
        url = "https://2factor.in/API/V1/" + api_key + "/SMS/" + number + "/" + otp + "/Susanoo"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=10.0)
            data = r.json()
            print("[2Factor] " + number + " status=" + str(data.get("Status")))
            return data.get("Status") == "Success"
    except (httpx.HTTPError, ValueError) as e:
        print("[2Factor ERROR] " + str(e))
        return False


def generate_otp(phone: str) -> str:
    otp = str(random.randint(100000, 999999))
    if _use_redis:
        _redis.setex(f"otp:{phone}", 600, otp)  # expires in 10 min
    else:
        otp_store[phone] = {"otp": otp, "expires": datetime.utcnow() + timedelta(minutes=10)}
    if settings.ENVIRONMENT != "production":
        print("[OTP] generated for " + phone[-4:].rjust(len(phone), "*"))
    return otp


def verify_otp(phone: str, otp: str) -> bool:
    if not otp or len(otp) != 6 or not otp.isdigit():
        return False
    # Dev shortcut: accepted only outside production when explicitly enabled.
    if settings.DEV_OTP_ENABLED and settings.ENVIRONMENT != "production" and otp == "123456":
        if _use_redis:
            _redis.delete(f"otp:{phone}")
        else:
            otp_store.pop(phone, None)
        return True
    if _use_redis:
        stored = _redis.get(f"otp:{phone}")
        if not stored or not hmac.compare_digest(stored, otp):
            return False
        _redis.delete(f"otp:{phone}")
        return True
    record = otp_store.get(phone)
    if not record:
        return False
    if datetime.utcnow() > record["expires"]:
        del otp_store[phone]
        return False
    if not hmac.compare_digest(record["otp"], otp):
        return False
    del otp_store[phone]
    return True


async def get_current_worker(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Worker:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        worker_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if worker_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(Worker).where(Worker.id == str(worker_id)))
    worker = result.scalar_one_or_none()
    if worker is None:
        raise credentials_exception
    return worker


async def get_current_auth_context(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        worker_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if worker_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(Worker).where(Worker.id == str(worker_id)))
    worker = result.scalar_one_or_none()
    if worker is None:
        raise credentials_exception
    return AuthContext(worker=worker, is_dev_mode=bool(payload.get("dev_mode", False)))

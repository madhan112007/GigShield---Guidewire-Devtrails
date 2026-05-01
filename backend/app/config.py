from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/gigshield"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "gigshield-dev-secret-key-change-in-production"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    FAST2SMS_API_KEY: str = "mock_key"  # Used for 2Factor.in API key
    NEWSAPI_KEY: str = "mock_key"
    OPENWEATHER_API_KEY: str = "mock_key"
    AQI_API_KEY: str = "mock_key"
    GOOGLE_MAPS_API_KEY: str = "mock_key"
    RAZORPAY_KEY_ID: str = "rzp_test_mock"
    RAZORPAY_KEY_SECRET: str = "mock_secret"
    RAZORPAY_ACCOUNT_NUMBER: str = "mock_account"
    FCM_SERVICE_ACCOUNT_PATH: str = "mock_key"  # Path to Firebase service account JSON
    FCM_PROJECT_ID: str = "mock_key"             # Firebase project ID (e.g. susanoo-d13b0)
    ENVIRONMENT: str = "development"



settings = Settings()


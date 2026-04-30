from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/gigshield"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "gigshield-dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    FAST2SMS_API_KEY: str = "mock_key"  # Used for 2Factor.in API key
    NEWSAPI_KEY: str = "mock_key"
    TWITTER_BEARER_TOKEN: str = "mock_key"
    TWITTER_CONSUMER_KEY: str = "mock_key"
    TWITTER_CONSUMER_SECRET: str = "mock_key"
    TWITTER_ACCESS_TOKEN: str = "mock_key"
    TWITTER_ACCESS_TOKEN_SECRET: str = "mock_key"
    OPENWEATHER_API_KEY: str = "mock_key"
    AQI_API_KEY: str = "mock_key"
    GOOGLE_MAPS_API_KEY: str = "mock_key"
    RAZORPAY_KEY_ID: str = "rzp_test_mock"
    RAZORPAY_KEY_SECRET: str = "mock_secret"
    RAZORPAY_ACCOUNT_NUMBER: str = "mock_account"
    FCM_SERVICE_ACCOUNT_PATH: str = "mock_key"  # Path to Firebase service account JSON
    FCM_PROJECT_ID: str = "mock_key"             # Firebase project ID (e.g. susanoo-d13b0)
    ENVIRONMENT: str = "development"
    DEV_OTP_ENABLED: bool = True
    DEMO_MODE_ENABLED: bool = True
    ADMIN_API_KEY: str = ""
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    def validate_runtime(self) -> None:
        if self.ENVIRONMENT == "production":
            unsafe_values = {
                "SECRET_KEY": "gigshield-dev-secret-key-change-in-production",
                "RAZORPAY_KEY_ID": "rzp_test_mock",
                "RAZORPAY_KEY_SECRET": "mock_secret",
                "DATABASE_URL": "postgresql+asyncpg://postgres:password@localhost:5432/gigshield",
            }
            for field, unsafe in unsafe_values.items():
                if getattr(self, field) == unsafe:
                    raise RuntimeError(f"{field} must be configured for production")
            if self.DEV_OTP_ENABLED or self.DEMO_MODE_ENABLED:
                raise RuntimeError("Demo and dev OTP modes must be disabled in production")
            if not self.ADMIN_API_KEY:
                raise RuntimeError("ADMIN_API_KEY must be configured in production")

    class Config:
        env_file = ".env"


settings = Settings()
settings.validate_runtime()

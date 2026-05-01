from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    FAST2SMS_API_KEY: str = ""  # Used for 2Factor.in API key
    NEWSAPI_KEY: str = ""
    TWITTER_BEARER_TOKEN: str = ""
    TWITTER_CONSUMER_KEY: str = ""
    TWITTER_CONSUMER_SECRET: str = ""
    TWITTER_ACCESS_TOKEN: str = ""
    TWITTER_ACCESS_TOKEN_SECRET: str = ""
    OPENWEATHER_API_KEY: str = ""
    AQI_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_ACCOUNT_NUMBER: str = ""
    FCM_SERVICE_ACCOUNT_PATH: str = ""  # Path to Firebase service account JSON
    FCM_PROJECT_ID: str = ""             # Firebase project ID (e.g. susanoo-d13b0)
    ENVIRONMENT: str = "development"
    DEV_OTP_ENABLED: bool = True
    DEMO_MODE_ENABLED: bool = True
    OPENAI_API_KEY: str = ""
    ADMIN_API_KEY: str = ""
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    def validate_runtime(self) -> None:
        if self.ENVIRONMENT == "production":
            required = ["SECRET_KEY", "RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "ADMIN_API_KEY"]
            for field in required:
                if not getattr(self, field):
                    raise RuntimeError(f"{field} must be configured for production")
            if self.DEV_OTP_ENABLED or self.DEMO_MODE_ENABLED:
                raise RuntimeError("Demo and dev OTP modes must be disabled in production")

    class Config:
        env_file = ".env"


settings = Settings()
settings.validate_runtime()

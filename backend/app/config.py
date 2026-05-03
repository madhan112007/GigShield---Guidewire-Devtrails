from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/gigshield"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "gigshield-dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    FAST2SMS_API_KEY: str = "mock_key"
    NEWSAPI_KEY: str = "mock_key"
    OPENWEATHER_API_KEY: str = "mock_key"
    AQI_API_KEY: str = "mock_key"
    GOOGLE_MAPS_API_KEY: str = "mock_key"
    RAZORPAY_KEY_ID: str = "rzp_test_mock"
    RAZORPAY_KEY_SECRET: str = "mock_secret"
    RAZORPAY_ACCOUNT_NUMBER: str = "mock_account"
    FCM_SERVICE_ACCOUNT_PATH: str = "mock_key"
    FCM_PROJECT_ID: str = "mock_key"
    ENVIRONMENT: str = "development"
    DEV_OTP_ENABLED: bool = True
    DEMO_MODE_ENABLED: bool = True
    ADMIN_API_KEY: str = ""
    ALLOWED_ORIGINS: str = "http://16.112.121.102:3000,http://16.112.121.102:8000,https://susanoo-theultimatedefense.netlify.app"
    GEMINI_API_KEY: str = "your_gemini_api_key_here"
    POSITIONSTACK_API_KEY: str = "your_positionstack_api_key"
    TWITTER_BEARER_TOKEN: str = "mock_key"
    TWITTER_CONSUMER_KEY: str = "mock_key"
    TWITTER_CONSUMER_SECRET: str = "mock_key"
    TWITTER_ACCESS_TOKEN: str = "mock_key"
    TWITTER_ACCESS_TOKEN_SECRET: str = "mock_key"
    # AI / Bedrock
    AWS_REGION: str = "ap-south-1"
    BEDROCK_MODEL_ID: str = "meta.llama3-1-70b-instruct-v1:0"
    BEDROCK_MODEL_FALLBACK: str = "meta.llama3-1-8b-instruct-v1:0"
    CHAT_MAX_TOKENS: int = 400
    CHAT_MAX_HISTORY_MESSAGES: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

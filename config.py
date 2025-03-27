from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Crawler settings
    MAX_WORKERS: int = 5
    TIMEOUT: int = 10
    MAX_RETRIES: int = 3
    USER_AGENT: str = "TothetopBot/1.0 (+https://tothetop.ai)"
    
    # Content quality thresholds
    MIN_WORD_COUNT: int = 100
    
    # Rate limiting
    REQUEST_DELAY: float = 1.0  # seconds between requests
    
    # Browser settings for Playwright
    PLAYWRIGHT_TIMEOUT: int = 30000  # 30 seconds
    
    class Config:
        env_file = ".env"

settings = Settings() 
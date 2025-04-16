from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    db_user: str
    db_password: str
    db_host: str
    db_port: str
    db_name: str
    
    # RabbitMQ settings
    project_name: str
    rabbitmq_host: str
    rabbitmq_port: str
    rabbitmq_user: str
    rabbitmq_password: str
    
    # Crawler settings
    MAX_WORKERS: int = 5
    TIMEOUT: int = 10
    MAX_RETRIES: int = 3
    USER_AGENT: str = "TothetopBot/1.0 (+https://tothetop.cloud)"
    
    # Content quality thresholds
    MIN_WORD_COUNT: int = 100
    
    # Rate limiting
    REQUEST_DELAY: float = 1.0  # seconds between requests
    
    # Browser settings for Playwright
    PLAYWRIGHT_TIMEOUT: int = 30000  # 30 seconds
    
    class Config:
        env_file = ".env"

settings = Settings() 
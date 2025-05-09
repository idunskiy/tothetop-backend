from pydantic_settings import BaseSettings
from typing import Optional
import logging
# Add debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    db_user: str
    db_password: str
    db_host: str
    db_port: str
    db_name: str
    
    # Google settings
    google_client_id: str
    google_client_secret: str
    
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
    
    # Trial optimization limit
    TRIAL_OPTIMIZATION_LIMIT: int = 2
    
    HOST_SANDBOX: str = 'https://sandbox-api.paddle.com/'
    HOST_PROD: str = 'https://api.paddle.com/'
    
    HOST_FRONTEND_PROD: str = 'https://tothetop.cloud'
    HOST_FRONTEND_DEV: str = 'http://localhost:3000'

    API_KEY_SANDBOX: str = 'pdl_sdbx_apikey_01jtsdk6kv7vqzskx1k9tbcwf6_Crt0tpQr4k9jv12x0tJ5XR_AP2'
    API_KEY_PROD: str = '4f0d4f75a55b2bc54354911db310c33a945a36bc74ba239475'
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add debug logging
        logger.debug(f"RabbitMQ settings: host={self.rabbitmq_host}, port={self.rabbitmq_port}")
        logger.debug(f"Project name: {self.project_name}")

settings = Settings() 
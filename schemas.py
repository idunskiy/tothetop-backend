from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    google_id: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Website schemas
class WebsiteBase(BaseModel):
    domain: str
    is_verified: bool = False
    verification_method: Optional[str] = None

class WebsiteCreate(WebsiteBase):
    user_id: int

class Website(WebsiteBase):
    id: int
    user_id: int
    added_at: datetime
    last_synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# GSC Data schemas
class GSCPageDataBase(BaseModel):
    page_url: str
    clicks: int = 0
    impressions: int = 0
    ctr: Optional[float] = None
    average_position: Optional[float] = None
    date: date
    batch_id: str  

class GSCPageDataCreate(GSCPageDataBase):
    user_id: int
    website_id: int

class GSCPageData(GSCPageDataBase):
    id: int
    user_id: int
    website_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class GSCKeywordDataBase(BaseModel):
    page_url: str
    keyword: str
    clicks: int = 0
    impressions: int = 0
    ctr: Optional[float] = None
    average_position: Optional[float] = None
    date: date
    batch_id: str  

class GSCKeywordDataCreate(GSCKeywordDataBase):
    user_id: int
    website_id: int

class GSCKeywordData(GSCKeywordDataBase):
    id: int
    user_id: int
    website_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Crawler Result schemas
class CrawlerResultBase(BaseModel):
    page_url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1: Optional[str] = None
    h2: Optional[List[str]] = None
    h3: Optional[List[str]] = None
    body_text: Optional[str] = None
    word_count: Optional[int] = None
    status: Optional[str] = None
    full_text: Optional[str] = None

class CrawlerResultCreate(CrawlerResultBase):
    user_id: int
    website_id: int

class CrawlerResult(CrawlerResultBase):
    id: int
    user_id: int
    website_id: int
    crawled_at: datetime

    class Config:
        from_attributes = True


class IntentRequest(BaseModel):
    full_text: str
    url: Optional[str] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    target_keywords: Optional[List[str]] = None

# Add these Pydantic models at the top with your other models
class OptimizationCreate(BaseModel):
    email: str
    url: str
    optimization_type: str
    summary: str
    reasoning: str
    original_content: str
    modified_content: str

class OptimizationResponse(BaseModel):
    id: int
    message: str

class LatestOptimization(BaseModel):
    timestamp: str
    summary: str
    type: str

class OptimizedPage(BaseModel):
    url: str
    latest_optimization: LatestOptimization
    optimization_count: int

class OptimizationsResponse(BaseModel):
    pages: List[OptimizedPage]
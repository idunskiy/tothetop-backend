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

# Analysis Result schemas
class AnalysisResultBase(BaseModel):
    overall_score: int
    metrics: Dict[str, Any]

class AnalysisResultCreate(AnalysisResultBase):
    user_id: int
    website_id: int

class AnalysisResult(AnalysisResultBase):
    id: int
    user_id: int
    website_id: int
    analyzed_at: datetime

    class Config:
        from_attributes = True

# Page Improvement schemas
class PageImprovementBase(BaseModel):
    page_url: str
    improvement_type: str
    priority: str
    description: str
    status: str = 'pending'

class PageImprovementCreate(PageImprovementBase):
    user_id: int
    website_id: int

class PageImprovement(PageImprovementBase):
    id: int
    user_id: int
    website_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 
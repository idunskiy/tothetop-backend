from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, date
import uuid

from database import SessionLocal
from models import User, Website, GSCPageData, GSCKeywordData, CrawlerResult, AnalysisResult, PageImprovement
from schemas import (
    UserCreate, User as UserSchema,
    WebsiteCreate, Website as WebsiteSchema,
    GSCPageDataCreate, GSCPageData as GSCPageDataSchema,
    GSCKeywordDataCreate, GSCKeywordData as GSCKeywordDataSchema,
    CrawlerResultCreate, CrawlerResult as CrawlerResultSchema,
    AnalysisResultCreate, AnalysisResult as AnalysisResultSchema,
    PageImprovementCreate, PageImprovement as PageImprovementSchema
)
from crawler import Crawler
from fastapi import HTTPException
from pydantic import HttpUrl
from typing import List, Optional, Dict
from pydantic import BaseModel
router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

class CrawlRequest(BaseModel):
    base_url: HttpUrl

class PageData(BaseModel):
    url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1: Optional[str] = None
    h2: Optional[List[str]] = None
    h3: Optional[List[str]] = None
    body_text: Optional[str] = None
    word_count: Optional[int] = None
    parse_method: Optional[str] = None
    status: str
    error_message: Optional[str] = None

class CrawlResponse(BaseModel):
    session_id: str
    pages: List[PageData]
    statistics: Dict
    
class CrawlStatus(BaseModel):
    session_id: str
    status: str
    pages_found: int = 0
    pages_crawled: int = 0
    
crawl_sessions = {}

# Crawl a website and extract SEO-relevant content from each page.
@router.post("/crawl", response_model=CrawlResponse)
async def crawl_website(request: CrawlRequest, db: Session = Depends(get_db)):
    try:
        session_id = str(uuid.uuid4())
        
        # Initialize the session first
        crawl_sessions[session_id] = {
            "status": "starting",
            "pages_found": 0,
            "pages_crawled": 0
        }
        
        crawler = Crawler(str(request.base_url))
        
        def update_progress(total_pages, crawled_pages):
            crawl_sessions[session_id].update({
                "status": crawler.status,
                "pages_found": total_pages,
                "pages_crawled": crawled_pages
            })
        
        crawler.set_progress_callback(update_progress)
        
        results = await crawler.crawl()
        
        # Save results to database, checking for duplicates
        saved_pages = []
        for page in results['pages']:
            # Check if page already exists with same content
            existing_page = db.query(CrawlerResult).filter(
                CrawlerResult.page_url == page['url'],
                CrawlerResult.word_count == page['word_count'],
                func.date(CrawlerResult.crawled_at) == func.current_date()
            ).first()
            
            if not existing_page:
                # Create new page record
                new_page = CrawlerResult(
                    page_url=page['url'],
                    title=page['title'],
                    meta_description=page['meta_description'],
                    h1=page['h1'],
                    h2=page['h2'],
                    h3=page['h3'],
                    body_text=page['body_text'],
                    word_count=page['word_count'],
                    status=page['status']
                )
                db.add(new_page)
                saved_pages.append(page)
        
        db.commit()
        
        crawl_sessions[session_id].update({
            "status": "completed"
        })
        
        return {
            "session_id": session_id,
            **results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/crawl/status/{session_id}", response_model=CrawlStatus)
async def get_crawl_status(session_id: str):
    """Get the status of a crawl session."""
    if session_id not in crawl_sessions:
        raise HTTPException(status_code=404, detail="Crawl session not found")
    
    return {
        "session_id": session_id,
        **crawl_sessions[session_id]
    }

# User endpoints
@router.post("/users/", response_model=UserSchema)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users/{user_id}", response_model=UserSchema)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Website endpoints
@router.post("/websites/", response_model=WebsiteSchema)
def create_website(website: WebsiteCreate, db: Session = Depends(get_db)):
    # Check if website already exists for this user
    existing_website = db.query(Website).filter(
        Website.user_id == website.user_id,
        Website.domain == website.domain
    ).first()
    
    if existing_website:
        return existing_website  # Return existing website instead of creating new one
        
    db_website = Website(**website.dict())
    db.add(db_website)
    db.commit()
    db.refresh(db_website)
    return db_website

@router.get("/websites/lookup", response_model=WebsiteSchema)
def get_website_by_url(
    domain: str = Query(..., min_length=1, description="Website domain without protocol"),
    user_id: int = Query(..., gt=0, description="User ID"),
    db: Session = Depends(get_db)
):
    print(f"Received lookup request - Domain: {domain}, User ID: {user_id}")  # Debug log
    
    # Add debug logging
    existing_domains = db.query(Website.domain).filter(Website.user_id == user_id).all()
    print(f"Existing domains for user {user_id}: {existing_domains}")
    
    website = db.query(Website).filter(
        Website.domain == domain,
        Website.user_id == user_id
    ).first()
    if not website:
        raise HTTPException(status_code=404, detail=f"Website not found for domain: {domain}")
    return website


@router.get("/websites/{website_id}", response_model=WebsiteSchema)
def get_website(website_id: int, db: Session = Depends(get_db)):
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    return website


@router.get("/websites/user/{user_id}", response_model=List[WebsiteSchema])
def get_user_websites(user_id: int, db: Session = Depends(get_db)):
    websites = db.query(Website).filter(Website.user_id == user_id).all()
    return websites


# GSC Page Data endpoints
@router.post("/gsc/page-data/", response_model=GSCPageDataSchema)
def create_gsc_page_data(data: GSCPageDataCreate, db: Session = Depends(get_db)):
    
    # Debug prints
    print("Incoming data:", data.dict())
    print("Page URL:", data.page_url)
    print("Date:", data.date)
    print("Website ID:", data.website_id)
    
    existing = db.query(GSCPageData).filter(
        GSCPageData.page_url == data.page_url,
        GSCPageData.date == data.date,
        GSCPageData.website_id == data.website_id
    ).first()
    
    if existing:
        # Update existing record
        for key, value in data.dict().items():
            setattr(existing, key, value)
    else:
        # Create new record
        existing = GSCPageData(**data.dict())
        db.add(existing)
    
    db.commit()
    db.refresh(existing)
    return existing

@router.get("/gsc/page-data/{website_id}", response_model=List[GSCPageDataSchema])
def get_website_page_data(website_id: int, db: Session = Depends(get_db)):
    data = db.query(GSCPageData).filter(GSCPageData.website_id == website_id).all()
    return data

# GSC Keyword Data endpoints
@router.post("/gsc/keyword-data/", response_model=GSCKeywordDataSchema)
def create_gsc_keyword_data(data: GSCKeywordDataCreate, db: Session = Depends(get_db)):
    existing = db.query(GSCKeywordData).filter(
        GSCKeywordData.keyword == data.keyword,
        GSCKeywordData.page_url == data.page_url,
        GSCKeywordData.date == data.date,
        GSCKeywordData.website_id == data.website_id
    ).first()
    
    if existing:
        # Update existing record
        for key, value in data.dict().items():
            setattr(existing, key, value)
    else:
        # Create new record
        existing = GSCKeywordData(**data.dict())
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing

@router.get("/gsc/keyword-data/{website_id}", response_model=List[GSCKeywordDataSchema])
def get_website_keyword_data(website_id: int, db: Session = Depends(get_db)):
    data = db.query(GSCKeywordData).filter(GSCKeywordData.website_id == website_id).all()
    return data

# Crawler Result endpoints
@router.post("/crawler/results/", response_model=CrawlerResultSchema)
def create_crawler_result(result: CrawlerResultCreate, db: Session = Depends(get_db)):
    db_result = CrawlerResult(**result.dict())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

@router.get("/crawler/results/{website_id}", response_model=List[CrawlerResultSchema])
def get_website_crawler_results(website_id: int, db: Session = Depends(get_db)):
    results = db.query(CrawlerResult).filter(CrawlerResult.website_id == website_id).all()
    return results

# Analysis Result endpoints
@router.post("/analysis/results/", response_model=AnalysisResultSchema)
def create_analysis_result(result: AnalysisResultCreate, db: Session = Depends(get_db)):
    db_result = AnalysisResult(**result.dict())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

@router.get("/analysis/results/{website_id}", response_model=List[AnalysisResultSchema])
def get_website_analysis_results(website_id: int, db: Session = Depends(get_db)):
    results = db.query(AnalysisResult).filter(AnalysisResult.website_id == website_id).all()
    return results

# Page Improvement endpoints
@router.post("/improvements/", response_model=PageImprovementSchema)
def create_page_improvement(improvement: PageImprovementCreate, db: Session = Depends(get_db)):
    db_improvement = PageImprovement(**improvement.dict())
    db.add(db_improvement)
    db.commit()
    db.refresh(db_improvement)
    return db_improvement

@router.get("/improvements/{website_id}", response_model=List[PageImprovementSchema])
def get_website_improvements(website_id: int, db: Session = Depends(get_db)):
    improvements = db.query(PageImprovement).filter(PageImprovement.website_id == website_id).all()
    return improvements 
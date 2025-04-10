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
import asyncio
from fastapi.responses import JSONResponse
from services.ai_service import AIService
import logging
from schemas import IntentRequest

router = APIRouter()


# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

class CrawlRequest(BaseModel):
    base_url: HttpUrl
    batch_id: str

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
    
class CrawlStatus(BaseModel):
    session_id: str
    status: str
    pages_found: int = 0
    pages_crawled: int = 0
    current_url: Optional[str] = None
    pages: Optional[List[PageData]] = None
    
crawl_sessions = {}

# Crawl a website and extract SEO-relevant content from each page.
# @router.post("/crawl", response_model=CrawlResponse)
# async def crawl_website(request: CrawlRequest, db: Session = Depends(get_db)):
#     try:
#         session_id = str(uuid.uuid4())
        
#         # Initialize the session first
#         crawl_sessions[session_id] = {
#             "status": "starting",
#             "pages_found": 0,
#             "pages_crawled": 0,
#             "batch_id": request.batch_id
#         }
        
#         crawler = Crawler(str(request.base_url), request.batch_id)
        
#         def update_progress(total_pages, crawled_pages, current_url):
#             crawl_sessions[session_id].update({
#                 "status": crawler.status,
#                 "pages_found": total_pages,
#                 "pages_crawled": crawled_pages,
#                 "current_url": current_url
#             })
        
#         crawler.set_progress_callback(update_progress)
        
#         results = await crawler.crawl()
        
#         # Save results to database, checking for duplicates
#         saved_pages = []
#         for page in results['pages']:
#             # Check if page already exists with same content
#             existing_page = db.query(CrawlerResult).filter(
#                 CrawlerResult.page_url == page['url'],
#                 CrawlerResult.word_count == page['word_count'],
#                 CrawlerResult.batch_id == request.batch_id  # Add batch_id to filter
#             ).first()
            
#             if not existing_page:
#                 # Create new page record
#                 new_page = CrawlerResult(
#                     page_url=page['url'],
#                     title=page['title'],
#                     meta_description=page['meta_description'],
#                     h1=page['h1'],
#                     h2=page['h2'],
#                     h3=page['h3'],
#                     body_text=page['body_text'],
#                     word_count=page['word_count'],
#                     status=page['status'],
#                     batch_id=request.batch_id
#                 )
#                 db.add(new_page)
#                 saved_pages.append(page)
        
#         db.commit()
        
#         crawl_sessions[session_id].update({
#             "status": "completed"
#         })
        
#         return {
#             "session_id": session_id,
#             **results
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/crawl", response_model=CrawlResponse)
async def crawl_website(request: CrawlRequest, db: Session = Depends(get_db)):
    try:
        session_id = str(uuid.uuid4())
        
        # Initialize the session first
        crawl_sessions[session_id] = {
            "status": "starting",
            "pages_found": 0,
            "pages_crawled": 0,
            "batch_id": request.batch_id,
            "current_url": None
        }
        
        # Create and start the crawler
        crawler = Crawler(str(request.base_url), request.batch_id)
        
        def update_progress(total_pages, crawled_pages, current_url):
            crawl_sessions[session_id].update({
                "status": "in_progress",
                "pages_found": total_pages,
                "pages_crawled": crawled_pages,
                "current_url": current_url
            })
        
        crawler.set_progress_callback(update_progress)

        # Start immediate response with session_id
        initial_response = {
            "session_id": session_id,
            "pages": [],
            "statistics": {}
        }

        # Start crawling in a separate task
        asyncio.create_task(
            run_crawl_task(
                crawler=crawler,
                session_id=session_id,
                db=db,
                batch_id=request.batch_id
            )
        )
        
        return initial_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
async def run_crawl_task(crawler: Crawler, session_id: str, db: Session, batch_id: str):
    try:
        logger.info(f"Starting crawl task for session {session_id}")
        results = await crawler.crawl()
        logger.info(f"Crawl completed, saving {len(results['pages'])} pages to database")

        
        # Save results to database
        saved_pages = []
        try:
            for page in results['pages']:
                existing_page = db.query(CrawlerResult).filter(
                    CrawlerResult.page_url == page['url'],
                    CrawlerResult.word_count == page['word_count'],
                    CrawlerResult.batch_id == batch_id
                ).first()
                
                if not existing_page:
                    new_page = CrawlerResult(
                        page_url=page['url'],
                        title=page['title'],
                        meta_description=page['meta_description'],
                        h1=page['h1'],
                        h2=page['h2'],
                        h3=page['h3'],
                        body_text=page['body_text'],
                        word_count=page['word_count'],
                        status=page['status'],
                        batch_id=batch_id,
                        full_text=page['full_text']
                    )
                    db.add(new_page)
                    saved_pages.append(page)
            
            db.commit()
            logger.info(f"Crawl task completed, updated session {session_id}")
        except Exception as e:
            logger.error(f"Error saving pages to database: {str(e)}")
            raise
        
        # print("Completed results in run_crawl_task:", results['pages'])
        # Update final status
        crawl_sessions[session_id].update({
            "status": "completed",
            "pages": saved_pages,
            "statistics": results['statistics']
        })
        
    except Exception as e:
        logger.error(f"Error in run_crawl_task: {str(e)}")
        crawl_sessions[session_id].update({
            "status": "failed",
            "error": str(e)
        })
    

@router.get("/crawl/status/{session_id}", response_model=CrawlStatus)
async def get_crawl_status(session_id: str):
    """Get the status of a crawl session."""
    try:
        if session_id not in crawl_sessions:
            return JSONResponse(
                status_code=404,
                content={"detail": "Crawl session not found"}
            )
        
        session_data = crawl_sessions[session_id]
        logger.info(f"Session data: {session_data}")
        
        # Create response with all fields including pages
        response_data = CrawlStatus(
            session_id=session_id,
            status=session_data["status"],
            pages_found=session_data["pages_found"],
            pages_crawled=session_data["pages_crawled"],
            current_url=session_data["current_url"],
            pages=session_data.get("pages", None)  # Include pages if they exist
        )
        
        return response_data

    except Exception as e:
        logger.error(f"Error in get_crawl_status: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )


@router.post("/crawl/stop/{session_id}")
async def stop_crawl(session_id: str):
    try:
        if session_id not in crawl_sessions:
            return JSONResponse(
                status_code=404,
                content={"detail": "Crawl session not found"}
            )
        
        # Update session status to stopped
        crawl_sessions[session_id].update({
            "status": "stopped",
            "pages": crawl_sessions[session_id].get("pages", [])
        })
        
        return {"status": "stopped"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )
        
# User endpoints
@router.post("/users/", response_model=UserSchema)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # First check if user exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        # Either return the existing user
        return existing_user
        # Or update the existing user's information
        # existing_user.name = user.name
        # existing_user.google_id = user.google_id
        # db.commit()
        # return existing_user
    
    # If user doesn't exist, create new user
    new_user = User(
        email=user.email,
        name=user.name,
        google_id=user.google_id
    )
    db.add(new_user)
    db.commit()
    return new_user

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
    print("Page Incoming data:", data.dict())
    print("Page URL:", data.page_url)
    print("Page Date:", data.date)
    print("Page Website ID:", data.website_id)
    print("Page Batch ID:", data.batch_id)
    existing = db.query(GSCPageData).filter(
        GSCPageData.page_url == data.page_url,
        GSCPageData.date == data.date,
        GSCPageData.website_id == data.website_id,
        GSCPageData.batch_id == data.batch_id
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
    print("Keyword Incoming data:", data.dict())
    print("Keyword:", data.keyword)
    print("Keyword Page URL:", data.page_url)
    print("Keyword Date:", data.date)
    print("Keyword Website ID:", data.website_id)
    print("Keyword Batch ID:", data.batch_id)
    
    existing = db.query(GSCKeywordData).filter(
        GSCKeywordData.keyword == data.keyword,
        GSCKeywordData.page_url == data.page_url,
        GSCKeywordData.date == data.date,
        GSCKeywordData.website_id == data.website_id,
        GSCKeywordData.batch_id == data.batch_id,
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
def get_website_keyword_data(
    website_id: int, 
    batch_id: Optional[str] = None,  # Add this parameter
    db: Session = Depends(get_db)
    ):
    query = db.query(GSCKeywordData).filter(GSCKeywordData.website_id == website_id)
    if batch_id:
        query = query.filter(GSCKeywordData.batch_id == batch_id)
    data = query.all()
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

@router.get("/analysis/last-batch")
def get_last_batch(
    website_id: int = Query(..., description="Website ID"),
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get the most recent batch_id for a given website and user."""
    try:
        # Query the most recent batch_id from GSCKeywordData
        last_batch = db.query(GSCKeywordData.batch_id)\
            .filter(GSCKeywordData.website_id == website_id)\
            .order_by(GSCKeywordData.created_at.desc())\
            .first()
        
        logger.info(f"Last batch from gsc-results: {last_batch}")

        if not last_batch:
            # If no batch found in GSCKeywordData, try CrawlerResult
            last_batch = db.query(CrawlerResult.batch_id)\
                .filter(CrawlerResult.batch_id.isnot(None))\
                .order_by(CrawlerResult.created_at.desc())\
                .first()

            logger.info(f"No last batch found in gsc-results, trying crawler-results")
            
        if last_batch:
            return {"batch_id": last_batch[0]}
        else:
            return {"batch_id": None}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{batch_id}")
async def get_batch_analysis(batch_id: str, db: Session = Depends(get_db)):
    # Get GSC data for this batch
    keyword_data = db.query(GSCKeywordData).filter(
        GSCKeywordData.batch_id == batch_id
    ).order_by(GSCKeywordData.impressions.desc()).all()
    
    # Get crawler results for this batch
    crawler_results = db.query(CrawlerResult).filter(
        CrawlerResult.batch_id == batch_id
    ).all()
    
    # Create a mapping of page_url to content
    page_content = {
        result.page_url: {
            'title': result.title,
            'meta_description': result.meta_description,
            'body_text': result.body_text,
            'word_count': result.word_count,
            'full_text': result.full_text
        }
        for result in crawler_results
    }
    
    # Analyze each page's keywords
    page_analysis = {}
    for keyword in keyword_data:
        if keyword.page_url not in page_analysis:
            page_analysis[keyword.page_url] = {
                'total_impressions': 0,
                'missing_keywords': [],
                'present_keywords': [],
                'total_keywords': 0
            }
            
        page_analysis[keyword.page_url]['total_impressions'] += keyword.impressions
        page_analysis[keyword.page_url]['total_keywords'] += 1
        
        # Check if keyword exists in content
        if keyword.page_url in page_content:
            content = page_content[keyword.page_url]
            combined_content = f"{content['title']} {content['meta_description']} {content['body_text']}".lower()
            
            if keyword.keyword.lower() in combined_content:
                page_analysis[keyword.page_url]['present_keywords'].append({
                    'keyword': keyword.keyword,
                    'impressions': keyword.impressions,
                    'clicks': keyword.clicks,
                    'position': keyword.average_position
                })
            else:
                page_analysis[keyword.page_url]['missing_keywords'].append({
                    'keyword': keyword.keyword,
                    'impressions': keyword.impressions,
                    'clicks': keyword.clicks,
                    'position': keyword.average_position
                })
    
    # Sort pages by impressions
    sorted_pages = sorted(
        page_analysis.items(),
        key=lambda x: x[1]['total_impressions'],
        reverse=True
    )
    
    return {
        'pages': [
            {
                'url': url,
                'total_impressions': stats['total_impressions'],
                'total_keywords': stats['total_keywords'],
                'missing_keywords_count': len(stats['missing_keywords']),
                'present_keywords_count': len(stats['present_keywords']),
                'word_count': page_content.get(url, {}).get('word_count', 0),
                'missing_keywords': stats['missing_keywords'],
                'present_keywords': stats['present_keywords'],
                'full_text': page_content.get(url, {}).get('full_text', ''),
                'title': page_content.get(url, {}).get('title', ''),
                'meta_description': page_content.get(url, {}).get('meta_description', '')
            }
            for url, stats in sorted_pages
        ]
    }
    
class TextRequest(BaseModel):
    text: str
    
ai_service = AIService()
    
@router.post("/process-text")
async def process_text(request: TextRequest):
    try:
        logger.debug(f"Processing text in backend: {request.text}")
        response = ai_service.process_invoice(request.text)
        if response is None:
            raise HTTPException(
                status_code=408, 
                detail="AI service timeout"
            )
        logger.debug(f"Got response from AI service: {response}")
        if response is None:
            raise HTTPException(status_code=408, detail="AI service timeout")
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-intent")
async def process_intent(request: IntentRequest):
    try:
        logger.debug(f"Processing intent in backend: {request}")
        request_dict = request.model_dump() 
        logger.debug(f"Request dictionary: {request_dict}")
        response = ai_service.process_intent(request_dict)
        logger.debug(f"AI service response: {response}")  # Add this log
        
        if response is None:  # Add this check
            logger.error("AI service returned None")
            raise HTTPException(status_code=500, detail="AI service returned no response")
            
        return response
    except Exception as e:
        logger.error(f"Error processing intent: {str(e)}")  # Log the specific error
        logger.exception("Full traceback:")  # This will log the full traceback
        raise HTTPException(status_code=500, detail=str(e))

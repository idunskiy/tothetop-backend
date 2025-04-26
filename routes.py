from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, date
import uuid

from database import SessionLocal
from models import User, Website, GSCPageData, GSCKeywordData, CrawlerResult,  PageOptimization
from schemas import (
    UserCreate, User as UserSchema,
    WebsiteCreate, Website as WebsiteSchema,
    GSCPageDataCreate, GSCPageData as GSCPageDataSchema,
    GSCKeywordDataCreate, GSCKeywordData as GSCKeywordDataSchema,
    CrawlerResultCreate, CrawlerResult as CrawlerResultSchema,
    OptimizationCreate, OptimizationResponse, LatestOptimization, OptimizedPage, OptimizationsList, OptimizationDetail
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
import os
import time
import sys
from fastapi import BackgroundTasks
router = APIRouter()


# Remove all existing logging configuration
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Configure logging with a more verbose format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

# Force the logger to use INFO level
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add a stream handler directly to this logger
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Test log to verify logging is working
logger.info("=== Logger initialized ===")

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
    user_id: int  
    website_id: int

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
ai_service = AIService()

@router.get("/user/email/{db_user_id}")
def get_user_email(db_user_id: int, db: Session = Depends(get_db)):
    """Get user's email by their database ID."""
    try:
        user = db.query(User).filter(User.id == db_user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        print(f"User email using db_user_id: {user.email}")
        return {"email": user.email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.post("/crawl", response_model=CrawlResponse)
async def crawl_website(request: CrawlRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        session_id = str(uuid.uuid4())
        logger.info(f"Starting crawl for session {session_id}")
        
        # Initialize the session first
        crawl_sessions[session_id] = {
            "status": "starting",
            "pages_found": 0,
            "pages_crawled": 0,
            "batch_id": request.batch_id,
            "website_id": request.website_id,
            "user_id": request.user_id,
            "current_url": None
        }
        
        # Create and start the crawler
        logger.info(f"Creating crawler for {request.base_url} with batch_id {request.batch_id}")
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
        
        logger.info(f"Initial response in crawl route: {initial_response}")

        # Start crawling in a separate task
        # asyncio.create_task(
        #     run_crawl_task(
        #         crawler=crawler,
        #         session_id=session_id,
        #         db=db,
        #         batch_id=request.batch_id,
        #         website_id=request.website_id,
        #         user_id=request.user_id
        #     )
        # )
        
        background_tasks.add_task(
            run_crawl_task,
                crawler=crawler,
                session_id=session_id,
                db=db,
            batch_id=request.batch_id,
            website_id=request.website_id,
            user_id=request.user_id
        )
        
        logger.info(f"Inital response: {initial_response}")
        
        return initial_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Old implemneta tion of crawl task - save to database after everything is crawled
# async def run_crawl_task(crawler: Crawler, session_id: str, db: Session, batch_id: str, website_id: int, user_id: int):
#     try:
#         logger.info(f"Starting crawl task for session {session_id}")
        
#         if session_id not in crawl_sessions:
#             logger.error(f"Session {session_id} not found in crawl_sessions")
#             return
        
#         # Update status to starting
#         crawl_sessions[session_id].update({
#             "status": "starting",
#             "pages_found": 0,
#             "pages_crawled": 0,
#             "current_url": None,
#             "pages": None
#         })
        
#         logger.info("Initializing crawler...")
#         try:
#             results = await crawler.crawl()
#             logger.info(f"Crawl completed, saving {len(results['pages'])} pages to database")
#         except Exception as e:
#             logger.error(f"Error during crawl: {str(e)}", exc_info=True)
#             crawl_sessions[session_id].update({
#                 "status": "failed",
#                 "error": f"Crawl error: {str(e)}",
#                 "pages": []
#             })
#             return
        
#         if not results or not results.get('pages'):
#             logger.error("Crawler returned no results or empty pages")
#             crawl_sessions[session_id].update({
#                 "status": "failed",
#                 "error": "Crawler returned no pages",
#                 "pages": []
#             })
#             return
        
#         logger.info(f"Crawl completed, found {len(results['pages'])} pages")

#         # Save results to database
#         saved_pages = []
#         try:
#             for page in results['pages']:
                
#                 logger.info(f"Saving page: {page['url']}")
                
#                 existing_page = db.query(CrawlerResult).filter(
#                     CrawlerResult.page_url == page['url'],
#                     CrawlerResult.word_count == page['word_count'],
#                     CrawlerResult.batch_id == batch_id,
#                     CrawlerResult.website_id == website_id,
#                     CrawlerResult.user_id == user_id
#                 ).first()
                
#                 if not existing_page:
#                     new_page = CrawlerResult(
#                         page_url=page['url'],
#                         title=page['title'],
#                         meta_description=page['meta_description'],
#                         h1=page['h1'],
#                         h2=page['h2'],
#                         h3=page['h3'],
#                         body_text=page['body_text'],
#                         word_count=page['word_count'],
#                         status=page['status'],
#                         batch_id=batch_id,
#                         website_id=website_id,
#                         user_id=user_id,
#                         full_text=page['full_text']
#                     )
#                     db.add(new_page)
#                     saved_pages.append(page)
            
#             db.commit()
#             logger.info(f"Crawl task completed, updated session {session_id}")
#         except Exception as e:
#             logger.error(f"Error saving pages to database: {str(e)}")
#             raise
        
#         # print("Completed results in run_crawl_task:", results['pages'])
#         # Update final status
#         crawl_sessions[session_id].update({
#             "status": "completed",
#             "pages": saved_pages,
#             "statistics": results['statistics'],
#             "pages_found": len(results['pages']),
#             "pages_crawled": len(saved_pages)
#         })
#         await asyncio.sleep(1)
#         logger.info(f"Crawl task completed, updated session {session_id}")
#     except Exception as e:
#         logger.error(f"Error in run_crawl_task: {str(e)}")
#         crawl_sessions[session_id].update({
#             "status": "failed",
#             "error": str(e)
#         })

async def run_crawl_task(crawler: Crawler, session_id: str, db: Session, batch_id: str, website_id: int, user_id: int):
    try:
        logger.info(f"Starting crawl task for session {session_id}")

        if session_id not in crawl_sessions:
            logger.error(f"Session {session_id} not found in crawl_sessions")
            return

        crawl_sessions[session_id].update({
            "status": "starting",
            "pages_found": 0,
            "pages_crawled": 0,
            "current_url": None,
            "pages": []
        })

        logger.info("Initializing crawler...")

        saved_pages = []
        pages_crawled = 0

        async for page in crawler.crawl():
            
            if crawl_sessions[session_id].get("status") == "stopped":
                logger.info(f"Crawl for session {session_id} was stopped by user.")
                break
            
            logger.info(f"Saving page: {page['url']}")
            existing_page = db.query(CrawlerResult).filter(
                CrawlerResult.page_url == page['url'],
                CrawlerResult.word_count == page['word_count'],
                CrawlerResult.batch_id == batch_id,
                CrawlerResult.website_id == website_id,
                CrawlerResult.user_id == user_id
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
                    website_id=website_id,
                    user_id=user_id,
                    full_text=page['full_text']
                )
                logger.info(f"About to save page: {new_page.page_url}")
                db.add(new_page)
                saved_pages.append(page)
                db.commit()
                pages_crawled += 1

            # Update session status after each page
            crawl_sessions[session_id].update({
                "status": "in_progress",
                "pages_found": pages_crawled,  # or use a better estimate if available
                "pages_crawled": pages_crawled,
                "current_url": page['url'],
                "pages": saved_pages
            })

        # Finalize
        crawl_sessions[session_id].update({
            "status": "completed",
            "pages": saved_pages,
            "statistics": crawler.stats,
            "pages_found": pages_crawled,
            "pages_crawled": pages_crawled
        })
        await asyncio.sleep(1)
        logger.info(f"Crawl task completed, updated session {session_id}")
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
        logger.info(f"Stopping crawl for session {session_id}")
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
    
    logger.info(f"=== Creating Website ===")
    logger.info(f"Received data: {website.dict()}")
    existing_website = db.query(Website).filter(
        Website.user_id == website.user_id,
        Website.domain == website.domain
    ).first()
    
    if existing_website:
        logger.info(f"Returning existing website: {existing_website.__dict__}")
        return existing_website  # Return existing website instead of creating new one
        
    db_website = Website(**website.dict())
    db.add(db_website)
    db.commit()
    db.refresh(db_website)
    logger.info(f"Created website: {db_website}")
    return db_website

@router.get("/websites/lookup", response_model=WebsiteSchema)
def get_website_by_url(
    domain: str = Query(..., min_length=1, description="Website domain without protocol"),
    user_id: int = Query(..., gt=0, description="User ID"),
    db: Session = Depends(get_db)
):
    logger.info(f"Received lookup request - Domain: {domain}, User ID: {user_id}")  # Debug log
    
    # Add debug logging
    existing_domains = db.query(Website.domain).filter(Website.user_id == user_id).all()
    logger.info(f"Existing domains for user {user_id}: {existing_domains}")
    
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
            .filter(GSCKeywordData.website_id == website_id,
                    GSCKeywordData.user_id == user_id)\
            .order_by(GSCKeywordData.created_at.desc())\
            .first()
        
        logger.info(f"Last batch from gsc-results: {last_batch}")

        if not last_batch:
            # If no batch found in GSCKeywordData, try CrawlerResult
            last_batch = db.query(CrawlerResult.batch_id)\
                .filter(CrawlerResult.batch_id.isnot(None),
                        CrawlerResult.user_id == user_id)\
                .order_by(CrawlerResult.created_at.desc())\
                .first()

            logger.info(f"No last batch found in gsc-results, trying crawler-results")
            
        if last_batch:
            return {"batch_id": last_batch[0]}
        else:
            return {"batch_id": None}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/user/last-batch")
def get_user_last_batch(
    email: str = Query(..., description="User email"),
    db: Session = Depends(get_db)
):
    """Get the most recent batch_id for a given user email."""
    try:
        # First get the user_id from the email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Query the most recent batch_id from GSCKeywordData
        last_batch = db.query(GSCKeywordData.batch_id)\
            .join(Website, GSCKeywordData.website_id == Website.id)\
            .filter(Website.user_id == user.id)\
            .order_by(GSCKeywordData.created_at.desc())\
            .first()
        
        logger.info(f"Last batch from gsc-results: {last_batch}")

        if not last_batch:
            # If no batch found in GSCKeywordData, try CrawlerResult
            last_batch = db.query(CrawlerResult.batch_id)\
                .join(Website, CrawlerResult.website_id == Website.id)\
                .filter(Website.user_id == user.id)\
                .filter(CrawlerResult.batch_id.isnot(None))\
                .order_by(CrawlerResult.created_at.desc())\
                .first()

            logger.info(f"No last batch found in gsc-results, trying crawler-results")
            
        if last_batch:
            return {"batch_id": last_batch[0]}
        else:
            return {"batch_id": None}

    except Exception as e:
        logger.error(f"Error in get_last_batch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{batch_id}")
async def get_batch_analysis(batch_id: str, db: Session = Depends(get_db)):
    def normalize_url(url: str) -> str:
        """Normalize URL to ensure consistent matching"""
        url = url.lower()
        url = url.rstrip('/')
        if url.startswith('http://'):
            url = 'https://' + url[7:]
        return url
    
    # Get crawler results for this batch
    crawler_results = db.query(CrawlerResult).filter(
        CrawlerResult.batch_id == batch_id
    ).all()
    
    logger.info(f"Crawler results: {len(crawler_results)}")
    unique_crawler_urls = set(cr.page_url for cr in crawler_results)
    logger.info(f"Unique crawler urls: {len(unique_crawler_urls)}")
    
    # Get GSC data but only for crawled URLs
    keyword_data = db.query(GSCKeywordData).filter(
        GSCKeywordData.batch_id == batch_id,
        func.lower(GSCKeywordData.page_url).in_([url for url in unique_crawler_urls])
    ).order_by(GSCKeywordData.impressions.desc()).all()

    urls_with_keywords = set(kw.page_url for kw in keyword_data)
    logger.info(f"URLs with GSC keyword data: {len(urls_with_keywords)}")
    logger.info(f"URLs without GSC data: {len(unique_crawler_urls - urls_with_keywords)}")

    
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
    
    logger.info(f"Page conten in get_batch_analysis: {len(page_content)}")
    
    # Initialize page_analysis for ALL crawled URLs
    page_analysis = {
        url: {
                'total_impressions': 0,
                'missing_keywords': [],
                'present_keywords': [],
                'total_keywords': 0
            }
        for url in unique_crawler_urls
    }
    for keyword in keyword_data:
        if keyword.page_url in page_analysis:
            page_analysis[keyword.page_url]['total_impressions'] += keyword.impressions
            page_analysis[keyword.page_url]['total_keywords'] += 1
        
        # Check if keyword exists in content
        if keyword.page_url in page_content:
            content = page_content[keyword.page_url]
            
            if keyword.keyword.lower() in content['full_text'].lower():
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
    
    # Sort pages by impressions but include ALL pages
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

@router.post("/add-keywords")
async def add_keywords(
    request_data: dict = Body(
        ...,  # ... means required
        example={
            "url": "https://example.com/blog-post",
            "batch_id": "batch_123"
        }
    ),
    db: Session = Depends(get_db)
):
    try:
        
        url = request_data.get("url")
        batch_id = request_data.get("batch_id")
        keywords = request_data.get("keywords")
        
        if not url or not batch_id:
            raise HTTPException(status_code=400, detail="URL and batch_id are required")

        # Get the crawler result with the content
        content = db.query(CrawlerResult).filter(
            CrawlerResult.page_url == url,
            CrawlerResult.batch_id == batch_id
        ).first()
        
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        optimization_data = {
            "original_content": content.full_text,
            "keywords": keywords
        }
        
        # Send to AI service
        response = ai_service.add_keywords(optimization_data)
        print(f"Received from AI service: {response}")  # Add this line
        return response

    except Exception as e:
        logger.error(f"Error in optimize_content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/optimize-section")
async def optimize_section(
    request_data: dict = Body(
        ...,
        example={
            "full_text": "Complete article content with block markers",
            "selected_text": "Text portion to optimize",
            "prompt": "User's optimization instructions"
        }
    ),
    db: Session = Depends(get_db)
):
    try:
        timestr = time.strftime("%Y%m%d-%H%M%S")
        logger.info(f"Received request to optimize section at {timestr}")
        print(f"Received request to optimize section at {timestr}")

        # Validate input
        full_text = request_data.get("full_text")
        selected_text = request_data.get("selected_text")
        prompt = request_data.get("prompt")

        if not all([full_text, selected_text, prompt]):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: full_text, selected_text, or prompt"
            )

        # Prepare the prompt data
        prompt_data = {
            "full_text": full_text,
            "selected_text": selected_text,
            "prompt": prompt
        }

        # Get optimization from AI service
        try:
            response = ai_service.optimize_section(prompt_data)
            print(f"Received from AI on optimize section: {response}")  # Add this line
            # Validate AI response structure
            if not isinstance(response, dict) or 'message' not in response:
                raise ValueError("Invalid AI response structure")

            return response

        except Exception as e:
            logger.error(f"AI service error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Failed to optimize content"
            )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in optimize_section: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
        
# Page Optimizations

# Add these routes with your other routes
@router.post("/add-optimization", response_model=OptimizationResponse)
async def save_optimization(
    optimization: OptimizationCreate,
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Received request to add optimization with data: {optimization}")
        print(f"Received request to add optimization with data: {optimization}")
        user = db.query(User).filter(User.email == optimization.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        keywords_json = None
        if optimization.keywords_used:
            keywords_json = [
                {
                    "keyword": kw.keyword,
                    "impressions": kw.impressions,
                    "position": kw.position
                }
                for kw in optimization.keywords_used
            ]
            
        sources_json = None
        if optimization.sources:
            sources_json = [
                {
                    "title": source.title,
                    "url": source.url   
                }
                for source in optimization.sources
            ]

        new_optimization = PageOptimization(
            user_id=user.id,
            url=optimization.url,
            optimization_type=optimization.optimization_type,
            summary=optimization.summary,
            reasoning=optimization.reasoning,
            original_content=optimization.original_content,
            modified_content=optimization.modified_content,
            keywords_used=keywords_json if optimization.optimization_type == 'add_keywords' else None,
            sources=sources_json if optimization.optimization_type == 'optimize_section' else None
        )
        
        db.add(new_optimization)
        db.commit()
        
        return {
            "id": new_optimization.id,
            "message": "Optimization saved successfully"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in save_optimization: {str(e)}")
        print(f"Error in save_optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/optimized-pages", response_model=OptimizationsList)
async def get_optimizations(
    email: str = Query(..., description="User email"),
    db: Session = Depends(get_db)
):
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get all optimizations ordered by created_at
        optimizations = db.query(
            PageOptimization.id,
            PageOptimization.url,
            PageOptimization.summary,
            PageOptimization.reasoning,
            PageOptimization.created_at,
            PageOptimization.optimization_type,
            PageOptimization.modified_content,
            PageOptimization.keywords_used,
            PageOptimization.sources
        ).filter(
            PageOptimization.user_id == user.id
        ).order_by(
            PageOptimization.created_at.desc()
        ).all()

        pages = [{
            'id': opt.id,
            'url': opt.url,
            'summary': opt.summary,
            'created_at': opt.created_at.isoformat(),
            'reasoning': opt.reasoning,
            'optimization_type': opt.optimization_type,
            'modified_content': opt.modified_content,
            'keywords_used': opt.keywords_used,
            'sources': opt.sources
        } for opt in optimizations]
        
        return {"pages": pages}

    except Exception as e:
        logger.error(f"Error in get_optimizations: {str(e)}")
        print(f"Error in get_optimizations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/optimized-pages/{optimization_id}", response_model=OptimizationDetail)
async def get_optimization_detail(
    optimization_id: int,
    db: Session = Depends(get_db)
):
    try:
        optimization = db.query(PageOptimization).filter(
            PageOptimization.id == optimization_id
        ).first()

        if not optimization:
            raise HTTPException(status_code=404, detail="Optimization not found")

        return {
            "id": optimization.id,
            "url": optimization.url,
            "optimization_type": optimization.optimization_type,
            "summary": optimization.summary,
            "reasoning": optimization.reasoning,
            "original_content": optimization.original_content,
            "modified_content": optimization.modified_content,
            "created_at": optimization.created_at.isoformat(),
            "keywords_used": optimization.keywords_used,
            "sources": optimization.sources
        }

    except Exception as e:
        logger.error(f"Error in get_optimization_detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
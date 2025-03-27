from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date

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

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
    db_website = Website(**website.dict())
    db.add(db_website)
    db.commit()
    db.refresh(db_website)
    return db_website

@router.get("/websites/{website_id}", response_model=WebsiteSchema)
def get_website(website_id: int, db: Session = Depends(get_db)):
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    return website

# GSC Page Data endpoints
@router.post("/gsc/page-data/", response_model=GSCPageDataSchema)
def create_gsc_page_data(data: GSCPageDataCreate, db: Session = Depends(get_db)):
    db_data = GSCPageData(**data.dict())
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data

@router.get("/gsc/page-data/{website_id}", response_model=List[GSCPageDataSchema])
def get_website_page_data(website_id: int, db: Session = Depends(get_db)):
    data = db.query(GSCPageData).filter(GSCPageData.website_id == website_id).all()
    return data

# GSC Keyword Data endpoints
@router.post("/gsc/keyword-data/", response_model=GSCKeywordDataSchema)
def create_gsc_keyword_data(data: GSCKeywordDataCreate, db: Session = Depends(get_db)):
    db_data = GSCKeywordData(**data.dict())
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data

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
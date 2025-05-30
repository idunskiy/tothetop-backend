from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Date, ForeignKey, Text, ARRAY, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from sqlalchemy.orm import relationship


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    google_id = Column(String(255), unique=True)
    google_refresh_token = Column(String(512))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    subscription_type = Column(String(255), default='trial')
    optimized_pages_count = Column(Integer, default=0)
    pages_limit = Column(Integer, default=2)
    purchase_date = Column(DateTime)
    
    # Add relationships with cascade
    websites = relationship('Website', backref='user', cascade='all, delete-orphan')
    gsc_page_data = relationship('GSCPageData', backref='user', cascade='all, delete-orphan')
    gsc_keyword_data = relationship('GSCKeywordData', backref='user', cascade='all, delete-orphan')
    crawler_results = relationship('CrawlerResult', backref='user', cascade='all, delete-orphan')
    page_optimizations = relationship('PageOptimization', backref='user', cascade='all, delete-orphan')

class Website(Base):
    __tablename__ = 'websites'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    domain = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    verification_method = Column(String(50))
    added_at = Column(DateTime, default=func.now())
    last_synced_at = Column(DateTime)

class GSCPageData(Base):
    __tablename__ = 'gsc_page_data'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    website_id = Column(Integer, ForeignKey('websites.id', ondelete='CASCADE'), nullable=False)
    page_url = Column(Text, nullable=False)
    clicks = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    ctr = Column(Float)
    average_position = Column(Float)
    batch_id = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=func.now())
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('page_url', 'date', 'website_id', 'batch_id', name='unique_page_data'),
    )

class GSCKeywordData(Base):
    __tablename__ = 'gsc_keyword_data'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    website_id = Column(Integer, ForeignKey('websites.id', ondelete='CASCADE'), nullable=False)
    page_url = Column(Text, nullable=False)
    keyword = Column(Text, nullable=False)
    clicks = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    ctr = Column(Float)
    average_position = Column(Float)
    date = Column(Date, nullable=False)
    batch_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('keyword', 'page_url', 'date', 'website_id', 'batch_id', name='unique_keyword_data'),
    )

class CrawlerResult(Base):
    __tablename__ = 'crawler_results'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    website_id = Column(Integer, ForeignKey('websites.id', ondelete='CASCADE'), nullable=False)
    page_url = Column(Text, nullable=False)
    title = Column(Text)
    meta_description = Column(Text)
    h1 = Column(Text)
    h2 = Column(JSONB)
    h3 = Column(JSONB)
    body_text = Column(Text)
    full_text = Column(Text)
    word_count = Column(Integer)
    crawled_at = Column(DateTime, default=func.now())
    status = Column(String(50))
    batch_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    
class PageOptimization(Base):
    __tablename__ = 'page_optimizations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    url = Column(Text, nullable=False)
    optimization_type = Column(Text, nullable=False)  # 'add_keywords' or 'optimize_section'
    summary = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=False)
    original_content = Column(Text, nullable=False)
    modified_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    keywords_used = Column(JSONB, nullable=True)  # Add this for keywords
    sources = Column(JSONB, nullable=True)        # Add this for sources

    # Add indexes for better query performance
    __table_args__ = (
        Index('idx_page_optimizations_user_url', 'user_id', 'url'),
        Index('idx_page_optimizations_created_at', 'created_at'),
    )
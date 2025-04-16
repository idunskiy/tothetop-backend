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
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Website(Base):
    __tablename__ = 'websites'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    domain = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    verification_method = Column(String(50))
    added_at = Column(DateTime, default=func.now())
    last_synced_at = Column(DateTime)

class GSCPageData(Base):
    __tablename__ = 'gsc_page_data'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    website_id = Column(Integer, ForeignKey('websites.id'))
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
    user_id = Column(Integer, ForeignKey('users.id'))
    website_id = Column(Integer, ForeignKey('websites.id'))
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
    user_id = Column(Integer, ForeignKey('users.id'))
    website_id = Column(Integer, ForeignKey('websites.id'))
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
    user_id = Column(Integer, ForeignKey('users.id'))
    url = Column(Text, nullable=False)
    optimization_type = Column(Text, nullable=False)  # 'keyword' or 'section'
    summary = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=False)
    original_content = Column(Text, nullable=False)
    modified_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Add indexes for better query performance
    __table_args__ = (
        Index('idx_page_optimizations_user_url', 'user_id', 'url'),
        Index('idx_page_optimizations_created_at', 'created_at'),
    )

    # Relationship to User model
    user = relationship('User', backref='page_optimizations')
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
import asyncio
from crawler import Crawler
from config import Settings

app = FastAPI(
    title="Tothetop.ai SEO Crawler",
    description="A powerful SEO crawler that extracts structured data from websites",
    version="1.0.0"
)

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
    pages: List[PageData]
    statistics: Dict

@app.post("/crawl", response_model=CrawlResponse)
async def crawl_website(request: CrawlRequest):
    """
    Crawl a website and extract SEO-relevant content from each page.
    Returns both the crawled pages and statistics about the crawl.
    """
    try:
        crawler = Crawler(str(request.base_url))
        results = await crawler.crawl()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
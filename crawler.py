import asyncio
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import trafilatura
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional, Set
from urllib.robotparser import RobotFileParser
from config import settings
import logging
from collections import deque
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Crawler:
    def __init__(self, base_url: str, batch_id: str):
        self.base_url = base_url
        self.batch_id = batch_id
        self.domain = urlparse(base_url).netloc
        self.url_queue = deque([base_url])
        self.visited_urls: Set[str] = set()
        self.processed_urls: Set[str] = set()
        self.results: List[Dict] = []
        self.browser = None
        self.semaphore = asyncio.Semaphore(settings.MAX_WORKERS)
        self.last_request_time = 0
        self.request_delay = settings.REQUEST_DELAY
        self.progress_callback = None
        self.status = "starting"
        self.pages_found = 0
        self.pages_crawled = 0
        self.current_url = None
        
        # Statistics tracking
        self.stats = {
            "start_time": None,
            "end_time": None,
            "total_pages_found": 0,
            "pages_parsed": 0,
            "successful_pages": 0,
            "failed_pages": 0,
            "failed_urls": [],
            "parse_time_seconds": 0
        }
        
        self.session_data = {
        'status': 'starting',
        'pages_found': 0,
        'pages_crawled': 0,
        'batch_id': batch_id,
        'current_url': None
         }
        
        # Initialize robots.txt parser
        self.robots_parser = RobotFileParser()
        self.robots_parser.set_url(f"{base_url}/robots.txt")
        try:
            self.robots_parser.read()
        except Exception as e:
            logger.warning(f"Could not read robots.txt: {str(e)}")
            self.robots_parser = None

    def normalize_url(self, url: str) -> str:
        """Remove fragments and normalize the URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    def set_progress_callback(self, callback):
        """Set callback function for progress updates."""
        print("Setting progress callback")
        self.progress_callback = callback

    async def run_crawl(self) -> Dict:
        """Run the crawl and report progress."""
        try:
            self.status = "in_progress"
            results = await self.crawl()
            self.status = "completed"
            return results
        except Exception as e:
            self.status = "failed"
            logger.error(f"Crawl failed: {str(e)}")
            raise
        
    async def crawl(self) -> Dict:
        """Main crawling method that orchestrates the crawling process."""
        self.stats["start_time"] = datetime.now()
        
        # Initialize single browser instance
        async with async_playwright() as p:
            self.browser = await p.chromium.launch()
            
            async with httpx.AsyncClient(
                timeout=settings.TIMEOUT,
                headers={"User-Agent": settings.USER_AGENT},
                limits=httpx.Limits(max_connections=settings.MAX_WORKERS)
            ) as client:
                while self.url_queue:
                    batch = []
                    for _ in range(settings.MAX_WORKERS):
                        if not self.url_queue:
                            break
                        batch.append(self.url_queue.popleft())
                    
                    tasks = [
                        self.process_url_with_semaphore(url, client)
                        for url in batch
                    ]
                    await asyncio.gather(*tasks)
                    
            await self.browser.close()
        
        # Calculate final statistics
        self.stats["end_time"] = datetime.now()
        self.stats["parse_time_seconds"] = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        self.stats["total_pages_found"] = len(self.processed_urls) + len(self.url_queue)
        
        return {
            "pages": self.results,
            "statistics": self.stats
        }

    async def process_url_with_semaphore(self, url: str, client: httpx.AsyncClient):
        """Process URL with semaphore for concurrency control"""
        async with self.semaphore:
            # Rate limiting
            now = time.time()
            time_since_last_request = now - self.last_request_time
            if time_since_last_request < self.request_delay:
                await asyncio.sleep(self.request_delay - time_since_last_request)
            
            self.last_request_time = time.time()
            await self.process_url(url, client)

    async def process_url(self, url: str, client: httpx.AsyncClient) -> None:
        """Process a single URL and extract its content."""
        current_url = self.normalize_url(url)
        if current_url in self.processed_urls:
            return
            
        if not self.is_allowed(current_url):
            return
            
        try:
            self.processed_urls.add(current_url)
            self.stats["pages_parsed"] += 1
            
            # Update these values with more stable counts
            self.pages_crawled = len(self.processed_urls)
            self.pages_found = len(self.processed_urls | self.visited_urls | set(self.url_queue))
            self.current_url = current_url
            
            self.session_data['pages_crawled'] = self.pages_crawled
            self.session_data['pages_found'] = self.pages_found
            self.session_data['current_url'] = current_url
            
            # Log the stable progress
            logger.info(f"Progress: {self.pages_crawled} out of {self.pages_found} pages crawled. Current: {current_url}")
            
            if self.progress_callback:
                self.progress_callback(self.pages_found, self.pages_crawled, current_url)
            
            # Try basic parsing first
            response = await client.get(current_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract content using basic parsing
            page_data = await self.extract_content_basic(soup, current_url)
            
            # Check if we need to try Playwright
            if self.needs_playwright(page_data):
                page_data = await self.extract_content_playwright(current_url)
            
            self.results.append(page_data)
            self.stats["successful_pages"] += 1
            
            # Extract and queue new URLs
            await self.extract_and_queue_urls(soup, current_url)
            
        except Exception as e:
            logger.error(f"Error processing {current_url}: {str(e)}")
            self.results.append({
                "url": current_url,
                "status": "fail",
                "error_message": str(e)
            })
            self.stats["failed_pages"] += 1
            self.stats["failed_urls"].append({
                "url": current_url,
                "error": str(e)
            })

    async def extract_content_basic(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract content using basic HTML parsing."""
        # Get individual elements
        title = soup.title.string if soup.title else None
        meta_desc = soup.find("meta", {"name": "description"})
        meta_description = meta_desc.get("content") if meta_desc else None
        
        h1 = soup.find("h1")
        h1_text = h1.get_text().strip() if h1 else None
        
        h2_tags = [h2.get_text().strip() for h2 in soup.find_all("h2")]
        h3_tags = [h3.get_text().strip() for h3 in soup.find_all("h3")]
        
        # Extract clean body content using trafilatura
        body_text = trafilatura.extract(str(soup))
        
        # Create full_text with markup
        full_text_parts = []
        
        if title:
            full_text_parts.append(f"[TITLE] {title}")
        
        if meta_description:
            full_text_parts.append(f"[META_DESCRIPTION] {meta_description}")
        
        if h1_text:
            full_text_parts.append(f"[H1] {h1_text}")
        
        # Add H2s and their associated content
        for h2 in soup.find_all("h2"):
            h2_text = h2.get_text().strip()
            full_text_parts.append(f"[H2] {h2_text}")
            
            # Get content until next h2 or h1
            current = h2.next_sibling
            section_content = []
            while current and not (current.name == 'h2' or current.name == 'h1'):
                if current.name == 'h3':
                    section_content.append(f"[H3] {current.get_text().strip()}")
                elif current.string and current.string.strip():
                    section_content.append(current.string.strip())
                current = current.next_sibling
            if section_content:
                full_text_parts.append(" ".join(section_content))
        
        # Add the main body text with markup
        if body_text:
            full_text_parts.append(f"[BODY] {body_text}")
        
        # Combine everything into full_text
        full_text = "\n\n".join(full_text_parts)
        
        # Calculate word count from body_text
        word_count = len(full_text.split()) if full_text else 0
        
        return {
            "url": url,
            "title": title,
            "meta_description": meta_description,
            "h1": h1_text,
            "h2": h2_tags,
            "h3": h3_tags,
            "body_text": body_text,
            "full_text": full_text,  # Now includes body text
            "word_count": word_count,
            "parse_method": "basic",
            "status": "partial" if word_count < settings.MIN_WORD_COUNT else "success"
        }
    
    async def extract_content_playwright(self, url: str) -> Dict:
        """Extract content using Playwright for JavaScript-rendered pages."""
        page = await self.browser.new_page()
        try:
            await page.goto(url, timeout=settings.PLAYWRIGHT_TIMEOUT)
            content = await page.content()
            
            soup = BeautifulSoup(content, 'html.parser')
            page_data = await self.extract_content_basic(soup, url)
            page_data["parse_method"] = "playwright"
            
            return page_data
        finally:
            await page.close()

    def needs_playwright(self, page_data: Dict) -> bool:
        """Check if we need to try Playwright for better extraction."""
        return (
            not page_data.get("title") or
            not page_data.get("h1") or
            (page_data.get("word_count", 0) < settings.MIN_WORD_COUNT)
        )

    async def extract_and_queue_urls(self, soup: BeautifulSoup, base_url: str) -> None:
        """Extract and queue new URLs from the page."""
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(base_url, href)
            current_url = self.normalize_url(full_url)
            
            if (
                self.is_same_domain(current_url) and
                current_url not in self.processed_urls and
                current_url not in self.visited_urls and
                self.is_allowed(current_url)
            ):
                self.url_queue.append(current_url)

    def is_same_domain(self, url: str) -> bool:
        """Check if URL is from the same domain."""
        return urlparse(url).netloc == self.domain

    def is_allowed(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        if self.robots_parser is None:
            return True
        return self.robots_parser.can_fetch(settings.USER_AGENT, url) 
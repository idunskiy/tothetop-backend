import asyncio
import httpx
from bs4 import BeautifulSoup, NavigableString, Comment
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
import sys

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
logger.info("=== Crawler Logger initialized ===")

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
        
        # Initialize robots.txt parser with more logging
        self.robots_parser = RobotFileParser()
        robots_url = f"{base_url}/robots.txt"
        logger.info(f"Attempting to fetch robots.txt from: {robots_url}")
        self.robots_parser.set_url(robots_url)
        try:
            self.robots_parser.read()
            logger.info("Successfully read robots.txt")
        except Exception as e:
            logger.warning(f"Could not read robots.txt: {str(e)}")
            logger.info("Proceeding without robots.txt restrictions")
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
        
    # Old implementation - parse all and then save to db
    
    # async def crawl(self) -> Dict:
    #     """Main crawling method that orchestrates the crawling process."""
    #     self.stats["start_time"] = datetime.now()
        
    #     logger.info(f"Starting crawl in crawler.py for {self.base_url}")
    #     logger.info(f"Initializing crawler with settings: MAX_WORKERS={settings.MAX_WORKERS}")
    #     # Initialize single browser instance
    #     async with async_playwright() as p:
    #         logger.info("Playwright initialized successfully")
    #         self.browser = await p.chromium.launch()
    #         logger.info("Browser launched successfully")
            
    #         async with httpx.AsyncClient(
    #             timeout=settings.TIMEOUT,
    #             headers={"User-Agent": settings.USER_AGENT},
    #             limits=httpx.Limits(max_connections=settings.MAX_WORKERS)
    #         ) as client:
    #             logger.info("HTTP client initialized successfully")
    #             while self.url_queue:
    #                 batch = []
    #                 for _ in range(settings.MAX_WORKERS):
    #                     if not self.url_queue:
    #                         break
    #                     batch.append(self.url_queue.popleft())
                    
    #                 logger.info(f"Processing {len(batch)} URLs")
    #                 tasks = [
    #                     self.process_url_with_semaphore(url, client)
    #                     for url in batch
    #                 ]
    #                 await asyncio.gather(*tasks)
    #                 logger.info("All tasks completed")
    #         await self.browser.close()
    #         logger.info("Browser closed successfully")
        
    #     # Calculate final statistics
    #     self.stats["end_time"] = datetime.now()
    #     self.stats["parse_time_seconds"] = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
    #     self.stats["total_pages_found"] = len(self.processed_urls) + len(self.url_queue)
    #     logger.info(f"Final statistics: {self.stats}")
    #     return {
    #         "pages": self.results,
    #         "statistics": self.stats
    #     }


    async def crawl(self):
        self.stats["start_time"] = datetime.now()
        logger.info(f"Starting crawl in crawler.py for {self.base_url}")
        logger.info(f"Initializing crawler with settings: MAX_WORKERS={settings.MAX_WORKERS}")
        async with async_playwright() as p:
            logger.info("Playwright initialized successfully")
            self.browser = await p.chromium.launch()
            logger.info("Browser launched successfully")
            async with httpx.AsyncClient(
                timeout=settings.TIMEOUT,
                headers={"User-Agent": settings.USER_AGENT},
                limits=httpx.Limits(max_connections=settings.MAX_WORKERS)
            ) as client:
                logger.info("HTTP client initialized successfully")
                while self.url_queue:
                    batch = []
                    for _ in range(settings.MAX_WORKERS):
                        if not self.url_queue:
                            break
                        batch.append(self.url_queue.popleft())
                    logger.info(f"Processing {len(batch)} URLs")
                    tasks = [
                        self.process_url_with_semaphore(url, client)
                        for url in batch
                    ]
                    results = await asyncio.gather(*tasks)
                    logger.info("All tasks completed")
                    for page in results:
                        if page:  # Only yield valid pages
                            yield page
        await self.browser.close()
        logger.info("Browser closed successfully")
        self.stats["end_time"] = datetime.now()
        self.stats["parse_time_seconds"] = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        self.stats["total_pages_found"] = len(self.processed_urls) + len(self.url_queue)
        logger.info(f"Final statistics after crawl in crawler.py: {self.stats}")
        
    # Old method - save once everything is parsed 
    # async def process_url_with_semaphore(self, url: str, client: httpx.AsyncClient):
    #     """Process URL with semaphore for concurrency control"""
    #     async with self.semaphore:
    #         # Rate limiting
    #         now = time.time()
    #         time_since_last_request = now - self.last_request_time
    #         if time_since_last_request < self.request_delay:
    #             await asyncio.sleep(self.request_delay - time_since_last_request)
            
    #         self.last_request_time = time.time()
    #         await self.process_url(url, client)
    
    async def process_url_with_semaphore(self, url: str, client: httpx.AsyncClient):
        """Process URL with semaphore for concurrency control"""
        async with self.semaphore:
            # Rate limiting
            now = time.time()
            time_since_last_request = now - self.last_request_time
            if time_since_last_request < self.request_delay:
                await asyncio.sleep(self.request_delay - time_since_last_request)
            
            self.last_request_time = time.time()
            return await self.process_url(url, client)

    # Old method - save results once the crawling is done
    # async def process_url(self, url: str, client: httpx.AsyncClient) -> None:
    #     """Process a single URL and extract its content."""
    #     current_url = self.normalize_url(url)
    #     logger.info(f"🔄 Processing URL in process_url in crawler.py: {current_url}")
    #     # Skip PDFs
    #     if current_url.lower().endswith('.pdf'):
    #         logger.info(f"Skipping PDF file: {current_url}")
    #         return
        
    #     if current_url in self.processed_urls:
    #         return
        
    #     if not self.is_allowed(current_url):
    #         logger.info(f"Skip: URL not allowed in process_url in crawler.py: {current_url}")
    #         return
        
    #     try:
    #         self.processed_urls.add(current_url)
    #         self.stats["pages_parsed"] += 1
            
    #         # Update these values with more stable counts
    #         self.pages_crawled = len(self.processed_urls)
    #         self.pages_found = len(self.processed_urls | self.visited_urls | set(self.url_queue))
    #         self.current_url = current_url
            
    #         self.session_data.update({
    #             'pages_crawled': self.pages_crawled,
    #             'pages_found': self.pages_found,
    #             'current_url': current_url,
    #             'status': 'in_progress'
    #         })
            
    #         # Log the stable progress
    #         logger.info(f"Progress in process_url in crawler.py: {self.pages_crawled} out of {self.pages_found} pages crawled. Current: {current_url}")
            
    #         if self.progress_callback:
    #             self.progress_callback(self.pages_found, self.pages_crawled, current_url)
            
    #         # Try basic parsing first
    #         response = await client.get(current_url)
    #         soup = BeautifulSoup(response.text, 'html.parser')
            
    #         # Extract content using basic parsing
    #         page_data = await self.extract_content_basic(soup, current_url)
            
    #         logger.info(f"Page data in process_url in crawler.py: {page_data}")
            
    #         # Check if we need to try Playwright
    #         if self.needs_playwright(page_data):
    #             logger.info(f"Trying Playwright for {current_url}")
    #             page_data = await self.extract_content_playwright(current_url)
            
    #         self.results.append(page_data)
    #         self.stats["successful_pages"] += 1
            
    #         # Extract and queue new URLs
    #         await self.extract_and_queue_urls(soup, current_url)
    #         logger.info(f"Extracted and queued URLs in process_url in crawler.py")
            
    #     except Exception as e:
    #         logger.error(f"Error processing {current_url}: {str(e)}")
    #         self.results.append({
    #             "url": current_url,
    #             "status": "fail",
    #             "error_message": str(e)
    #         })
    #         self.stats["failed_pages"] += 1
    #         self.stats["failed_urls"].append({
    #             "url": current_url,
    #             "error": str(e)
    #         })
    #     finally:
    #         # Ensure semaphore is released
    #         if hasattr(self, 'semaphore'):
    #             try:
    #                 self.semaphore.release()
    #             except ValueError:
    #                 pass  # Semaphore was already released
    
    
    async def process_url(self, url: str, client: httpx.AsyncClient) -> None:
        """Process a single URL and extract its content."""
        current_url = self.normalize_url(url)
        logger.info(f"🔄 Processing URL in process_url in crawler.py: {current_url}")
        # Skip PDFs
        if current_url.lower().endswith('.pdf'):
            logger.info(f"Skipping PDF file: {current_url}")
            return
        
        if current_url in self.processed_urls:
            return
        
        if not self.is_allowed(current_url):
            logger.info(f"Skip: URL not allowed in process_url in crawler.py: {current_url}")
            return
        
        try:
            self.processed_urls.add(current_url)
            self.stats["pages_parsed"] += 1
            
            # Update these values with more stable counts
            self.pages_crawled = len(self.processed_urls)
            self.pages_found = len(self.processed_urls | self.visited_urls | set(self.url_queue))
            self.current_url = current_url
            
            self.session_data.update({
                'pages_crawled': self.pages_crawled,
                'pages_found': self.pages_found,
                'current_url': current_url,
                'status': 'in_progress'
            })
            
            # Log the stable progress
            logger.info(f"Progress in process_url in crawler.py: {self.pages_crawled} out of {self.pages_found} pages crawled. Current: {current_url}")
            
            if self.progress_callback:
                self.progress_callback(self.pages_found, self.pages_crawled, current_url)
            
            # Try basic parsing first
            response = await client.get(current_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            page_data = await self.extract_content_basic(soup, current_url)
            
            # Extract content using basic parsing
            page_data = await self.extract_content_basic(soup, current_url)
            
            logger.info(f"Page data in process_url in crawler.py: {page_data}")
            
            # Check if we need to try Playwright
            if self.needs_playwright(page_data):
                logger.info(f"Trying Playwright for {current_url}")
                page_data = await self.extract_content_playwright(current_url)
            
            self.results.append(page_data)
            self.stats["successful_pages"] += 1
            
            # Extract and queue new URLs
            await self.extract_and_queue_urls(soup, current_url)
            logger.info(f"Extracted and queued URLs in process_url in crawler.py")
            return page_data
            
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
            return None
        finally:
            # Ensure semaphore is released
            if hasattr(self, 'semaphore'):
                try:
                    self.semaphore.release()
                except ValueError:
                    pass  # Semaphore was already released

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Replace multiple spaces, tabs, and newlines with a single space
        text = ' '.join(text.split())
        
        # Fix common spacing issues
        text = text.replace(' ,', ',')
        text = text.replace(' .', '.')
        text = text.replace(' :', ':')
        text = text.replace(' ;', ';')
        text = text.replace('( ', '(')
        text = text.replace(' )', ')')
        
        # Ensure proper spacing after punctuation
        text = text.replace(',', ', ')
        text = text.replace('.', '. ')
        text = text.replace(':', ': ')
        text = text.replace(';', '; ')
        
        # Clean up any double spaces that might have been created
        text = ' '.join(text.split())
        
        return text.strip()

    async def extract_content_basic(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract content using basic HTML parsing."""
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'footer', 'iframe', 'form']):
            element.decompose()
        
        # Get basic metadata
        title = soup.title.string if soup.title else None
        meta_desc = soup.find("meta", {"name": "description"})
        meta_description = meta_desc.get("content") if meta_desc else None
        
        structured_content = []
        seen_content = set()  # Track unique content to avoid duplicates
        
        if title:
            structured_content.append({
                'type': 'title',
                'content': title,
                'tag': 'title'
            })
            seen_content.add(title)
        
        if meta_description:
            structured_content.append({
                'type': 'meta',
                'content': meta_description,
                'tag': 'meta'
            })
            seen_content.add(meta_description)

        def process_element(element):
            # Handle NavigableString objects
            if isinstance(element, (str, NavigableString)):
                return

            # Skip comments
            if isinstance(element, Comment):
                return

            # Skip unwanted elements
            if element.name in ['script', 'style', 'nav', 'footer', 'iframe', 'form', 'button', 'input']:
                return

            # Skip elements with unwanted classes
            skip_classes = {'hidden', 'nav', 'menu', 'footer', 'header', 'sidebar', 'modal', 'dialog', 'popup'}
            if element.get('class'):
                if any(cls.lower() in skip_classes for cls in element.get('class')):
                    return

            # Skip elements with unwanted text
            skip_texts = {'====== Navbar Section', '====== Hero Section'}
            text = self.clean_text(element.get_text())
            if any(skip_text in text for skip_text in skip_texts):
                return

            # Process content based on tag type
            if text and text not in seen_content:  # Only process if text is unique
                if element.name == 'h1':
                    structured_content.append({
                        'type': 'heading',
                        'level': 1,
                        'content': text,
                        'tag': 'h1'
                    })
                    seen_content.add(text)
                
                elif element.name == 'h2':
                    structured_content.append({
                        'type': 'heading',
                        'level': 2,
                        'content': text,
                        'tag': 'h2'
                    })
                    seen_content.add(text)
                
                elif element.name in ['h3', 'h4']:
                    structured_content.append({
                        'type': 'heading',
                        'level': 3,
                        'content': text,
                        'tag': 'h3'
                    })
                    seen_content.add(text)
                
                elif element.name == 'p':
                    structured_content.append({
                        'type': 'paragraph',
                        'content': text,
                        'tag': 'p'
                    })
                    seen_content.add(text)
                
                elif element.name in ['ul', 'ol']:
                    list_items = []
                    # Find all li elements, including those nested in spans
                    for li in element.find_all('li', class_='mshfa-features__item-li'):  # Add class filter
                        li_text = self.clean_text(li.get_text())
                        if li_text and li_text not in seen_content:
                            list_items.append(li_text)
                            seen_content.add(li_text)
                    
                    # If no items found with class, try without class filter
                    if not list_items:
                        for li in element.find_all('li'):
                            li_text = self.clean_text(li.get_text())
                            if li_text and li_text not in seen_content:
                                list_items.append(li_text)
                                seen_content.add(li_text)
                    
                    if list_items:
                        # Also capture the list title if present
                        list_title = None
                        title_elem = element.find_previous_sibling('p', class_='mshfa-features__item-title')
                        if title_elem:
                            list_title = self.clean_text(title_elem.get_text())
                        
                        structured_content.append({
                            'type': 'list',
                            'title': list_title,  # Add title to the list structure
                            'items': list_items,
                            'tag': element.name
                        })

            # Process children only for container elements
            if element.name in ['div', 'section', 'article', 'main', 'body', 'span']:  # Added 'span'
                for child in element.children:
                    process_element(child)

        # Start processing from body
        if soup.body:
            process_element(soup.body)

        # Create full_text while preserving structure
        full_text_parts = []
        h1_text = None
        h2_tags = []
        h3_tags = []
        
        for item in structured_content:
            if item['type'] == 'title':
                full_text_parts.append(f"[TITLE_START]\n{item['content']}\n[TITLE_END]")
            elif item['type'] == 'meta':
                full_text_parts.append(f"[META_START]\n{item['content']}\n[META_END]")
            elif item['type'] == 'heading':
                if item['level'] == 1:
                    h1_text = item['content']
                    full_text_parts.append(f"[H1_START]\n{item['content']}\n[H1_END]")
                elif item['level'] == 2:
                    h2_tags.append(item['content'])
                    full_text_parts.append(f"[H2_START]\n{item['content']}\n[H2_END]")
                elif item['level'] == 3:
                    h3_tags.append(item['content'])
                    full_text_parts.append(f"[H3_START]\n{item['content']}\n[H3_END]")
            elif item['type'] == 'paragraph':
                full_text_parts.append(f"[P_START]\n{item['content']}\n[P_END]")
            elif item['type'] == 'list':
                if item.get('title'):
                    full_text_parts.append(f"[P_START]\n{item['title']}\n[P_END]")
                list_text = "\n".join(f"• {list_item}" for list_item in item['items'])
                full_text_parts.append(f"[LIST_START]\n{list_text}\n[LIST_END]")
        
        # Join parts and calculate word count safely
        try:
            full_text = "\n\n".join(full_text_parts)
            # Calculate word count from all text content
            word_count = sum(len(item.get('content', '').split()) for item in structured_content)
            word_count += sum(len(item.get('items', [])) for item in structured_content if item['type'] == 'list')
        except Exception as e:
            print(f"Error processing text: {e}")
            full_text = ""
            word_count = 0

        # Get body text using trafilatura
        try:
            body_text = trafilatura.extract(str(soup)) or ""
        except Exception as e:
            print(f"Error extracting body text: {e}")
            body_text = ""

        return {
            "url": url,
            "title": title,
            "meta_description": meta_description,
            "h1": h1_text,
            "h2": h2_tags,
            "h3": h3_tags,
            "body_text": body_text,
            # "structured_content": structured_content,  # New field
            "full_text": full_text,
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
            
            # Skip PDFs
            if current_url.lower().endswith('.pdf'):
                continue
            
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
            logger.info(f"No robots.txt restrictions, allowing URL: {url}")
            return True
        
        is_allowed = self.robots_parser.can_fetch(settings.USER_AGENT, url)
        logger.info(f"Robots.txt check for {url}: {'allowed' if is_allowed else 'not allowed'}")
        
        # If robots.txt exists but blocks everything, we'll proceed anyway
        if not is_allowed:
            logger.warning(f"URL {url} is blocked by robots.txt, but proceeding anyway")
            return True
            
        return True
    
    # def is_allowed(self, url: str) -> bool:
    #     """Check if URL is allowed by robots.txt."""
    #     if self.robots_parser is None:
    #         return True
    #     return self.robots_parser.can_fetch(settings.USER_AGENT, url) 
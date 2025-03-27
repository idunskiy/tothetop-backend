# Tothetop.ai SEO Crawler

A powerful SEO crawler built with FastAPI that extracts structured data from websites, handling both static HTML and JavaScript-heavy pages.

## Features

- Crawls entire websites while respecting robots.txt
- Extracts SEO-relevant content (title, meta description, headings, body text)
- Handles JavaScript-rendered content using Playwright
- Concurrent crawling with rate limiting
- Smart content extraction using trafilatura
- Configurable settings and thresholds

## Prerequisites

- Python 3.8+
- Node.js (for Playwright)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tothetop-backend.git
cd tothetop-backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install
```

## Usage

1. Start the server:
```bash
uvicorn main:app --reload
```

2. The API will be available at `http://localhost:8000`

3. Access the API documentation at `http://localhost:8000/docs`

4. Make a POST request to `/crawl` with a JSON body:
```json
{
    "base_url": "https://example.com"
}
```

## Configuration

You can customize the crawler's behavior by creating a `.env` file with the following variables:

```env
MAX_WORKERS=5
TIMEOUT=10
MAX_RETRIES=3
MIN_WORD_COUNT=100
REQUEST_DELAY=1.0
PLAYWRIGHT_TIMEOUT=30000
```

## API Response Format

The crawler returns an array of page data in the following format:

```json
[
    {
        "url": "https://example.com/about",
        "title": "About Us",
        "meta_description": "Learn more about our team and mission.",
        "h1": "Who We Are",
        "h2": ["Our Story", "Our Team"],
        "h3": ["Leadership", "Values"],
        "body_text": "We started this company...",
        "word_count": 437,
        "parse_method": "basic",
        "status": "success"
    }
]
```

## Status Codes

- `success`: Page was successfully crawled and contains sufficient content
- `partial`: Page was crawled but has less than 100 words
- `fail`: Page failed to load or was blocked

## License

MIT License 
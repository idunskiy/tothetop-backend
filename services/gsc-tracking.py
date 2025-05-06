# services/gsc_tracking.py

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import requests
import logging

# Configure logging
logging.basicConfig(
    filename='services/gsc_analysis.log',      # Log file name
    filemode='a',                    # Append mode
    level=logging.INFO,              # Log INFO and above
    format='%(asctime)s %(levelname)s: %(message)s'
)

load_dotenv()

def fetch_gsc_data(
    refresh_token: str,
    client_id: str,
    client_secret: str,
    site_url: str,
    start_date: str,
    end_date: str,
    country: str = None
):
    # Authenticate
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
    )
    service = build('searchconsole', 'v1', credentials=creds)
    
    print("Access token used:", creds.token)
    
    list_gsc_sites(creds)

    # Build filters
    dimension_filters = []
    if country:
        dimension_filters.append({
            "dimension": "country",
            "expression": country
        })

    # Query for page data
    page_request = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["page"],
        "rowLimit": 25000,
        "dimensionFilterGroups": [{"filters": dimension_filters}] if dimension_filters else []
    }
    page_response = service.searchanalytics().query(siteUrl=site_url, body=page_request).execute()
    pages = page_response.get("rows", [])

    # Query for keyword data
    query_request = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["query", "page"],
        "rowLimit": 25000,
        "dimensionFilterGroups": [{"filters": dimension_filters}] if dimension_filters else []
    }
    query_response = service.searchanalytics().query(siteUrl=site_url, body=query_request).execute()
    queries = query_response.get("rows", [])

    return pages, queries

def analyze_gsc_changes(old_queries, new_queries):
    # Map: (query, page) -> stats
    old_set = set((row['keys'][0], row['keys'][1]) for row in old_queries)
    new_set = set((row['keys'][0], row['keys'][1]) for row in new_queries)

    new_keywords = new_set - old_set
    gone_keywords = old_set - new_set

    logging.info(f"New keywords: {new_keywords}")
    logging.info(f"Keywords that disappeared: {gone_keywords}")

    # Example: print position changes for common keywords
    for key in new_set & old_set:
        old_row = next(row for row in old_queries if (row['keys'][0], row['keys'][1]) == key)
        new_row = next(row for row in new_queries if (row['keys'][0], row['keys'][1]) == key)
        logging.info(f"Keyword '{key[0]}' on page '{key[1]}': position {old_row['position']} -> {new_row['position']}")


def get_refresh_token_from_api(user_id: int, api_url="http://localhost:8000"):
    url = f"{api_url}/users/{user_id}/refresh-token"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("refresh_token")
    else:
        print("Error:", response.status_code, response.text)
        return None

def analyze_page_gsc_changes(old_queries, new_queries, page_url):
    # Filter to only this page
    old_page_queries = [row for row in old_queries if row['keys'][1] == page_url]
    new_page_queries = [row for row in new_queries if row['keys'][1] == page_url]

    old_set = set(row['keys'][0] for row in old_page_queries)  # keyword only
    new_set = set(row['keys'][0] for row in new_page_queries)

    new_keywords = new_set - old_set
    gone_keywords = old_set - new_set

    logging.info(f"=== Analysis for page: {page_url} ===")
    logging.info(f"New keywords: {new_keywords}")
    logging.info(f"Keywords that disappeared: {gone_keywords}")

    # Impressions/clicks for the page overall
    old_impr = sum(row.get('impressions', 0) for row in old_page_queries)
    new_impr = sum(row.get('impressions', 0) for row in new_page_queries)
    old_clicks = sum(row.get('clicks', 0) for row in old_page_queries)
    new_clicks = sum(row.get('clicks', 0) for row in new_page_queries)
    logging.info(f"Impressions: {old_impr} -> {new_impr}")
    logging.info(f"Clicks: {old_clicks} -> {new_clicks}")

    # Position changes for all keywords
    for keyword in new_set | old_set:
        old_row = next((row for row in old_page_queries if row['keys'][0] == keyword), None)
        new_row = next((row for row in new_page_queries if row['keys'][0] == keyword), None)
        old_pos = old_row['position'] if old_row else None
        new_pos = new_row['position'] if new_row else None
        logging.info(f"Keyword '{keyword}': position {old_pos} -> {new_pos}")
    
def list_gsc_sites(creds):
    service = build('searchconsole', 'v1', credentials=creds)
    site_list = service.sites().list().execute()
    print("Sites accessible by this user:")
    for site in site_list.get('siteEntry', []):
        print(f"- {site.get('siteUrl')} (type: {site.get('siteType')}, permission: {site.get('permissionLevel')})")
    return site_list.get('siteEntry', [])
    
# Example usage
if __name__ == "__main__":
    # These would come from your user/session storage
    
    user_id = 15
    refresh_token = get_refresh_token_from_api(user_id)
    if not refresh_token:
        print("Failed to get refresh token")
        exit(1)
    
    print(f"Refresh token: {refresh_token}")
    
    CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    SITE_URL = "sc-domain:demigos.com"
    PAGE_URL = "https://demigos.com/blog-post/predictive-modeling-in-healthcare/"

    # Baseline: 2 weeks ago
    start_date_old = (datetime.today() - timedelta(days=21)).strftime("%Y-%m-%d")
    end_date_old = (datetime.today() - timedelta(days=14)).strftime("%Y-%m-%d")
    # After implementation: last week
    start_date_new = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date_new = datetime.today().strftime("%Y-%m-%d")

    # Fetch old and new data
    old_pages, old_queries = fetch_gsc_data(
        refresh_token, CLIENT_ID, CLIENT_SECRET, SITE_URL, start_date_old, end_date_old
    )
    new_pages, new_queries = fetch_gsc_data(
        refresh_token, CLIENT_ID, CLIENT_SECRET, SITE_URL, start_date_new, end_date_new
    )

    # Analyze changes
    # analyze_gsc_changes(old_queries, new_queries)
    analyze_page_gsc_changes(old_queries, new_queries, PAGE_URL)
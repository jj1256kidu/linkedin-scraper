import os
import json
import logging
import re
import time
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class KeywordCategory(Enum):
    AI = "AI"
    COMPLIANCE = "Compliance"
    OTHER = "Other"

@dataclass
class JobListing:
    timestamp: str
    company: str
    title: str
    location: str
    link: str
    source: str
    website: str
    about: str
    news: str
    people: str
    category: KeywordCategory

@dataclass
class DecisionMaker:
    name: str
    title: str
    company: str
    linkedin_url: str
    news_mentions: List[Dict[str, str]]
    people_mentioned: List[str]
    timestamp: str

class Scraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.blacklist_keywords = [
            'senior', 'sr.', 'lead', 'principal', 'architect', 'manager',
            'director', 'vp', 'vice president', 'head', 'chief', 'cto'
        ]
        self.setup_google_sheets()

    def setup_google_sheets(self):
        """Initialize Google Sheets connection"""
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            
            # Get credentials from environment variable
            credentials_json = os.getenv('CREDENTIALS')
            if not credentials_json:
                raise ValueError("GOOGLE_CREDENTIALS environment variable not set")
                
            # Parse credentials
            credentials_dict = json.loads(credentials_json)
            
            # Create credentials object
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(
                credentials_dict, scope)
            
            # Authorize and open sheet
            gc = gspread.authorize(credentials)
            self.sheet = gc.open_by_key(os.getenv('SPREADSHEET_ID'))
            
        except Exception as e:
            logging.error(f"Error setting up Google Sheets: {e}")
            raise

    async def scrape_jobs(self) -> List[JobListing]:
        """Scrape LinkedIn jobs"""
        jobs = []
        base_keywords = [
            "Explainable AI Specialist Healthcare Compliance",
            "Healthcare AI Compliance Engineer",
            "Medical Device AI Compliance",
            "Healthcare Regulatory AI",
            "Medical AI Compliance Specialist",
            "Healthcare AI Governance",
            "Medical Device Regulatory AI",
            "Healthcare AI Quality Assurance",
            "Medical AI Regulatory Compliance",
            "Healthcare AI Standards"
        ]
        
        async with aiohttp.ClientSession() as session:
            for keyword in base_keywords[:10]:  # Process first 10 keywords
                try:
                    url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location=United%20States"
                    async with session.get(url, headers=self.headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            # Parse and extract job listings
                            # Add your parsing logic here
                            pass
                    await asyncio.sleep(1)  # Delay between requests
                except Exception as e:
                    logging.error(f"Error scraping keyword {keyword}: {e}")
                    continue
                    
        return jobs

    def get_top_companies(self, jobs: List[JobListing]) -> List[str]:
        """Get top companies from job listings"""
        company_counts = {}
        for job in jobs:
            company_counts[job.company] = company_counts.get(job.company, 0) + 1
        return sorted(company_counts.keys(), key=lambda x: company_counts[x], reverse=True)

    def find_decision_makers(self, company: str) -> List[DecisionMaker]:
        """Find decision makers in a company"""
        decision_makers = []
        titles = ["CTO", "VP Engineering", "Head of R&D"]
        
        for title in titles:
            try:
                time.sleep(0.3)
                search_url = f"https://www.linkedin.com/search/results/people/?keywords={title} {company}&origin=GLOBAL_SEARCH_HEADER"
                page_content = self.fetch_page(search_url)
                
                if not page_content:
                    continue
                    
                profile_urls = re.findall(r'https://www\.linkedin\.com/in/[^/]+/', page_content)
                
                for url in profile_urls[:2]:
                    try:
                        time.sleep(0.2)
                        profile_content = self.fetch_page(url)
                        
                        if not profile_content:
                            continue
                            
                        name_match = re.search(r'<title>(.*?) \|', profile_content)
                        title_match = re.search(r'<meta property="og:title" content="(.*?)"', profile_content)
                        
                        if name_match and title_match:
                            name = name_match.group(1).strip()
                            full_title = title_match.group(1).strip()
                            
                            news, people = self.get_company_news_and_mentions(company, name)
                            
                            decision_makers.append(DecisionMaker(
                                name=name,
                                title=full_title,
                                company=company,
                                linkedin_url=url,
                                news_mentions=news,
                                people_mentioned=people,
                                timestamp=datetime.now().isoformat()
                            ))
                            
                    except Exception as e:
                        logging.error(f"Error processing profile {url}: {e}")
                        continue
                        
            except Exception as e:
                logging.error(f"Error searching for {title} at {company}: {e}")
                continue
                
        return decision_makers

    def fetch_page(self, url: str, retries: int = 3) -> str:
        """Fetch page content with retry logic"""
        import requests
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 429:  # Rate limit
                    time.sleep(2 * (attempt + 1))
                else:
                    logging.warning(f"Unexpected status code: {response.status_code}")
            except Exception as e:
                logging.error(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 * (attempt + 1))
        return ""

    def get_company_news_and_mentions(self, company: str, person: str) -> Tuple[List[Dict[str, str]], List[str]]:
        """Get recent news and mentions for a company and person"""
        news_articles = []
        people_mentioned = set()
        
        try:
            time.sleep(0.2)
            search_query = f"{company} {person} news"
            news_url = f"https://news.google.com/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
            page_content = self.fetch_page(news_url)
            
            if not page_content:
                return [], []
                
            article_pattern = r'<article[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?</article>'
            articles = re.findall(article_pattern, page_content, re.DOTALL)
            
            for link, title in articles[:2]:
                if not link.startswith('http'):
                    link = f"https://news.google.com{link}"
                    
                news_articles.append({
                    'title': title.strip(),
                    'link': link
                })
                
                people_pattern = r'([A-Z][a-z]+ [A-Z][a-z]+)'
                mentioned = re.findall(people_pattern, title)
                people_mentioned.update(mentioned)
                
        except Exception as e:
            logging.error(f"Error fetching news for {company} {person}: {e}")
            
        return news_articles, list(people_mentioned)

    def save_to_google_sheets(self, jobs: List[JobListing]):
        """Save jobs to Google Sheets"""
        try:
            # Get existing records
            existing_records = self.sheet.get_all_records()
            existing_links = {record['Job Link'] for record in existing_records if 'Job Link' in record}
            
            # Filter out duplicates
            new_jobs = [job for job in jobs if job.link not in existing_links]
            
            if not new_jobs:
                logging.info("No new jobs to add")
                return
                
            # Prepare data
            rows_to_append = [
                [
                    job.timestamp, job.company, job.title, job.location,
                    job.link, job.source, job.website, job.about,
                    job.news, job.people, job.category.value
                ]
                for job in new_jobs
            ]
            
            # Append to sheet
            self.sheet.append_rows(rows_to_append)
            logging.info(f"Added {len(new_jobs)} new jobs to Google Sheets")
            
        except Exception as e:
            logging.error(f"Error saving to Google Sheets: {e}")

    def save_decision_makers_to_sheets(self, decision_makers: List[DecisionMaker]):
        """Save decision makers to Google Sheets"""
        try:
            # Get or create Decision Makers sheet
            try:
                dm_sheet = self.sheet.worksheet("Decision Makers")
            except:
                dm_sheet = self.sheet.add_worksheet("Decision Makers", rows=1000, cols=20)
                
            # Get existing records
            existing_records = dm_sheet.get_all_records()
            existing_urls = {record['LinkedIn URL'] for record in existing_records if 'LinkedIn URL' in record}
            
            # Filter out duplicates
            new_dms = [dm for dm in decision_makers if dm.linkedin_url not in existing_urls]
            
            if not new_dms:
                logging.info("No new decision makers to add")
                return
                
            # Prepare data
            rows_to_append = []
            for dm in new_dms:
                rows_to_append.append([
                    dm.timestamp,
                    dm.name,
                    dm.title,
                    dm.company,
                    dm.linkedin_url,
                    '\n'.join([f"{article['title']}: {article['link']}" for article in dm.news_mentions]),
                    '\n'.join(dm.people_mentioned)
                ])
            
            # Append to sheet
            dm_sheet.append_rows(rows_to_append)
            logging.info(f"Added {len(new_dms)} new decision makers to Google Sheets")
            
        except Exception as e:
            logging.error(f"Error saving decision makers to sheets: {e}")

def main():
    try:
        # Load environment variables
        load_dotenv()
        
        # Get credentials from GitHub Secrets
        credentials_json = os.getenv('CREDENTIALS')
        if credentials_json:
            credentials = json.loads(credentials_json)
            with open('credentials.json', 'w') as f:
                json.dump(credentials, f)
        
        # Initialize scraper
        scraper = Scraper()
        
        # Run the scraping process
        logging.info("Starting scraping process")
        jobs = asyncio.run(scraper.scrape_jobs())
        top_companies = scraper.get_top_companies(jobs)[:5]
        
        # Find decision makers
        all_decision_makers = []
        for company in top_companies:
            logging.info(f"Processing company: {company}")
            decision_makers = scraper.find_decision_makers(company)
            all_decision_makers.extend(decision_makers)
        
        # Save results
        logging.info("Saving results to Google Sheets")
        scraper.save_to_google_sheets(jobs)
        scraper.save_decision_makers_to_sheets(all_decision_makers)
        
        logging.info("Scraping completed successfully")
        
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main() 

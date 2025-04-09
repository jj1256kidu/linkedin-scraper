import os
import json
import logging
from dotenv import load_dotenv
import asyncio

# Set up logging
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

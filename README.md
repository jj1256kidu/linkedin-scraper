# LinkedIn Job Scraper

Automated scraper for LinkedIn jobs and decision makers, running on GitHub Actions.

## Features
- Scrapes LinkedIn jobs every 6 hours
- Finds decision makers in companies
- Saves results to Google Sheets
- Runs automatically using GitHub Actions

## Setup
1. Fork this repository
2. Set up GitHub Secrets:
   - `SPREADSHEET_ID`: Your Google Sheets ID
   - `GOOGLE_CREDENTIALS`: Your Google API credentials JSON
3. The scraper will run automatically every 6 hours

## Manual Run
You can also trigger a manual run:
1. Go to Actions tab
2. Select "LinkedIn Scraper"
3. Click "Run workflow"

## Logs
Logs are available in the Actions tab after each run.

## Requirements
See `requirements.txt` for Python dependencies. 

import requests
import json
from datetime import datetime
from scraper_utils import save_jobs

# Oracle Cloud HCM API endpoint
API_URL = "https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
BASE_UI_URL = "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job"

def parse_date(date_str):
    """
    Parse Oracle Cloud date format (ISO 8601).
    """
    if not date_str:
        return datetime.now()
    
    try:
        # Oracle typically returns ISO format like "2025-12-30T00:00:00+00:00"
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        return datetime.now()

def fetch_jpmc_jobs():
    print("Scraping JPMorgan Chase Jobs...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    params = {
        "onlyData": "true",
        "expand": "requisitionList",
        "finder": "findReqs;siteNumber=CX_1001,keyword=data engineer",
        "limit": 50,
        "offset": 0
    }
    
    all_jobs = []
    
    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # The response might have jobs in a nested field
        items = data.get("items", [])
        
        # Check if there's a requisitionList
        if items and len(items) > 0:
            first_item = items[0]
            if "requisitionList" in first_item:
                items = first_item.get("requisitionList", [])
        
        print(f"Fetched {len(items)} raw JPMC jobs.")
        
        for job in items:
            # Title - try multiple possible field names
            title = (job.get("Title") or 
                    job.get("JobTitle") or 
                    job.get("JobName") or
                    job.get("RequisitionTitle") or
                    "Unknown Title")
            print(f"Found Job: {title}")
            
            # ID
            job_id = job.get("Id") or job.get("RequisitionId") or "JPMC-Unknown"
            
            # Location
            primary_location = job.get("PrimaryLocation", "USA")
            
            # Posted Date
            posted_on = job.get("PostedDate") or job.get("DatePosted") or ""
            pdate = parse_date(posted_on)
            
            # URL
            full_url = f"{BASE_UI_URL}/{job_id}"
            
            job_entry = {
                "id": str(job_id),
                "title": title,
                "company": "JPMorgan Chase",
                "location": primary_location,
                "posted_date": pdate.isoformat(),
                "url_next_step": full_url,
                "description_short": title,
                "source": "JPMorgan Chase"
            }
            
            all_jobs.append(job_entry)
            
    except Exception as e:
        print(f"Error scraping JPMC: {e}")
        
    # Save using shared utility (filters will apply!)
    save_jobs(all_jobs)

if __name__ == "__main__":
    fetch_jpmc_jobs()

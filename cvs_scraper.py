import requests
import json
import re
from datetime import datetime, timedelta
from scraper_utils import save_jobs

# Endpoint from user screenshot
API_URL = "https://cvshealth.wd1.myworkdayjobs.com/wday/cxs/cvshealth/CVS_Health_Careers/jobs"
BASE_UI_URL = "https://cvshealth.wd1.myworkdayjobs.com/en-US/CVS_Health_Careers"

def parse_posted_date(posted_text):
    """
    Parses Workday relative dates like:
    - "Posted Yesterday"
    - "Posted 2 Days Ago"
    - "Posted 30+ Days Ago"
    - "Posted Today"
    """
    if not posted_text:
        return datetime.now()
    
    text = posted_text.lower()
    today = datetime.now()
    
    if "today" in text:
        return today
    if "yesterday" in text:
        return today - timedelta(days=1)
    
    # "Posted 5 Days Ago"
    match = re.search(r"(\d+)", text)
    if match:
        days = int(match.group(1))
        return today - timedelta(days=days)
        
    return today # Fallback

def fetch_cvs_jobs():
    print("Scraping CVS Health Jobs...")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    payload = {
        "appliedFacets": {},
        "limit": 20,
        "offset": 0,
        "searchText": "data engineer"
    }
    
    all_jobs = []
    offset = 0
    max_pages = 5
    
    for i in range(max_pages):
        print(f"Scraping page {i+1} (offset {offset})...")
        payload["offset"] = offset
        
        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            job_postings = data.get("jobPostings", [])
            if not job_postings:
                print("No more jobs found.")
                break
                
            print(f"Fetched {len(job_postings)} raw CVS jobs.")
            
            for j in job_postings:
                # Title
                title = j.get("title", "Unknown Title")
                print(f"Found Job: {title}")
                
                # Date
                posted_text = j.get("postedOn", "")
                pdate = parse_posted_date(posted_text)
                
                # URL
                # externalPath usually looks like "/job/..."
                ext_path = j.get("externalPath", "")
                full_url = f"{BASE_UI_URL}{ext_path}"
                
                # Location
                location = j.get("locationsText", "USA")
                
                # ID
                bullet_fields = j.get("bulletFields", [])
                # Workday often puts ID in bullet fields or just use the end of external path
                # externalPath: "/job/Senior-Data-Engineer_R012345" -> ID is R012345
                job_id = "CVS-Unknown"
                if ext_path:
                    parts = ext_path.split("_")
                    if len(parts) > 1:
                        job_id = parts[-1]
                
                job_entry = {
                    "id": job_id,
                    "title": title,
                    "company": "CVS Health",
                    "location": location,
                    "posted_date": pdate.isoformat(),
                    "url_next_step": full_url,
                    "description_short": title, # Workday search result doesn't give full desc
                    "source": "CVS Health"
                }
                
                all_jobs.append(job_entry)
            
        
            offset += 20
            
        except Exception as e:
            print(f"Error scraping CVS page {i+1}: {e}")
            break
        
    # Save using shared utility (filters will apply!)
    save_jobs(all_jobs)

if __name__ == "__main__":
    fetch_cvs_jobs()

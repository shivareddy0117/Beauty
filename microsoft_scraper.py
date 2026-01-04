import requests
import json
import time
from datetime import datetime
from scraper_utils import save_jobs, is_recent

BASE_URL = "https://apply.careers.microsoft.com/api/pcsx/search"
SLEEP = 0.5 

def fetch_microsoft_jobs():
    print("Scraping Microsoft Jobs...")
    all_jobs = []
    start = 0
    limit = 20 # API seems to return pages
    
    params = {
        "domain": "microsoft.com",
        "query": "Data Engineer",
        "location": "United States",
        "sort_by": "timestamp", # Get latest first
        "start": str(start)
    }
    
    while True:
        params["start"] = str(start)
        try:
            r = requests.get(BASE_URL, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"Error fetching Microsoft jobs: {e}")
            break
            
        # Structure is data -> positions
        payload_data = data.get("data", {})
        jobs = payload_data.get("positions", [])
            
        if not jobs:
            print("No jobs found in batch.")
            break
            
        print(f"Fetched {len(jobs)} jobs (offset {start})")
        found_recent = False
        
        for j in jobs:
            # Check date
            ts = j.get("postedTs")
            if not ts:
                continue
                
            try:
                # Assuming seconds
                pdate = datetime.fromtimestamp(int(ts))
            except:
                continue
                
            if is_recent(pdate, 7):
                found_recent = True
                
                # Construct URL
                # API returns /careers/job/ID but that seems broken. 
                # Use standard global URL: https://jobs.careers.microsoft.com/global/en/job/ID
                url = f"https://jobs.careers.microsoft.com/global/en/job/{j.get('id')}"

                locs = j.get("locations", [])
                location = locs[0] if locs else "United States"
                
                job_entry = {
                    "id": str(j.get("id")),
                    "title": j.get("name"),
                    "company": "Microsoft",
                    "location": location,
                    "posted_date": pdate.isoformat(),
                    "url_next_step": url,
                    "description_short": j.get("description", "")[:200] + "...", # description might be missing?
                    "source": "Microsoft"
                }
                all_jobs.append(job_entry)
        
        # Check last job date to decide if we stop
        last_ts = jobs[-1].get("postedTs")
        if last_ts:
             last_date = datetime.fromtimestamp(int(last_ts))
             if not is_recent(last_date, 7):
                 print("Reached older jobs, stopping.")
                 break
        else:
            # If no ts, can't determine, maybe just continue or break safely
            pass
            
        start += len(jobs)
        time.sleep(SLEEP)
        
        if start > 500: # safety limit
            break
            
    print(f"Found {len(all_jobs)} recent Microsoft jobs.")
    save_jobs(all_jobs)

if __name__ == "__main__":
    fetch_microsoft_jobs()

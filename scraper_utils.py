import json
import os
from datetime import datetime
import dateutil.parser

import re

# Regex Filters
INCLUDE_TITLE = re.compile(
    r"\b(data\s*engineer|data\s*engineering|analytics\s*engineer|etl|data\s*platform|data\s*pipeline|data\s*warehouse|big\s*data)\b",
    re.I
)

EXCLUDE_TITLE = re.compile(
    r"\b(site reliability|sre|security|network|frontend|front-end|full\s*stack|mobile|ios|android|devops|qa|test|product manager|program manager|scrum)\b",
    re.I
)

EXCLUDE_SENIORITY = re.compile(
    r"\b(director|manager|vp|head)\b",
    re.I
)

# Experience Filter (>= 6 years excluded)
MAX_EXPERIENCE_YEARS = 6
EXPERIENCE_PATTERN = re.compile(r"(\d+)\+?\s*years", re.I)

def is_data_engineer_title(title: str) -> bool:
    t = (title or "").strip()
    if not t:
        return False
    if not INCLUDE_TITLE.search(t):
        return False
    if EXCLUDE_TITLE.search(t):
        return False
    if EXCLUDE_SENIORITY.search(t):
        return False
    return True

def has_too_much_experience(description: str) -> bool:
    """
    Returns True if the description mentions experience >= 6 years.
    """
    if not description:
        return False
        
    # Scan for "X years", "X+ years"
    matches = EXPERIENCE_PATTERN.findall(description)
    for m in matches:
        try:
            years = int(m)
            # If we see "10+ years", clearly excluded.
            # If we see "3-5 years", regex finds 3 and 5. 5 is ok.
            if years >= MAX_EXPERIENCE_YEARS:
                # Context check could be better (e.g. "10 years ago"), but for now basic check
                return True
        except:
            pass
            
    return False

def save_jobs(new_jobs, filename="ui/jobs.json"):
    """
    Saves a list of job dictionaries to the specified JSON file.
    If the file exists, it merges the new jobs with existing ones (deduplicating by ID if possible).
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    existing_jobs = []
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                existing_jobs = json.load(f)
        except:
            print(f"Warning: Could not read {filename}, starting fresh.")
            existing_jobs = []
    
    # Simple deduplication by ID or URL if available
    # We'll use a set of IDs seen
    seen_ids = set()
    merged_jobs = []
    
    # Priority to new jobs? Or keep old? 
    # Let's keep existing, update with new if same ID.
    # Actually, simplistic approach: append all, then dedup by ID.
    
    # Apply filtering to NEW jobs only (or all? Safer to filter new ones first)
    # The user request implies they want this logic applied.
    # Apply filtering to NEW jobs only (or all? Safer to filter new ones first)
    # The user request implies they want this logic applied.
    filtered_new_jobs = []
    for j in new_jobs:
        title = j.get('title', '')
        if not is_data_engineer_title(title):
            continue
            
        # Check experience if description available
        desc = j.get('description') or j.get('basic_qualifications') or j.get('description_short') or ""
        if has_too_much_experience(desc):
             # Skip if too experienced
             continue
             
        # Check date (Past 7 days)
        if not is_recent(j.get('posted_date'), days=7):
            continue
             
        filtered_new_jobs.append(j)

    print(f"Filtered {len(new_jobs)} raw jobs down to {len(filtered_new_jobs)} relevant Data Engineer roles (<6 YOE, <7 Days).")

    all_candidates = existing_jobs + filtered_new_jobs
    
    # mapping to keep latest version of a job by ID
    job_map = {} 
    
    for job in all_candidates:
        # Try to find a unique ID
        uid = job.get("jobId") or job.get("id") or job.get("url")
        if uid:
             # This will overwrite older ones with newer ones if they come later in the list
             # Assuming new_jobs are fresher, they are added last
            job_map[uid] = job
        else:
            # If no ID, just add it (risks duplicates)
            # generate a synthetic ID from title+company+location
            slug = f"{job.get('title')}-{job.get('company')}-{job.get('location')}"
            job_map[slug] = job

    
    # Filter final list by date to ensure old jobs are removed
    final_list = []
    for job in job_map.values():
        if is_recent(job.get("posted_date"), days=7):
            final_list.append(job)

    
    # Write back to JSON for persistence between script runs
    with open(filename, "w") as f:
        json.dump(final_list, f, indent=2)
    
    # Write as JS file to avoid CORS issues when opening file:// directly
    # 'window.JOBS_DATA = [...]'
    js_filename = filename.replace(".json", ".js")
    
    with open(js_filename, "w") as f:
        f.write("window.JOBS_DATA = ")
        json.dump(final_list, f, indent=2)
        f.write(";")
    
    print(f"Saved {len(final_list)} unique jobs to {filename} and {js_filename}")

def is_recent(date_str, days=7):
    """
    Checks if a date string is within the last N days.
    """
    if not date_str: return False
    try:
        if isinstance(date_str, str):
            d = dateutil.parser.parse(date_str)
            # If timezone aware, convert to naive or handle explicitly
            if d.tzinfo:
                d = d.replace(tzinfo=None)
        else:
            d = date_str
            
        return (datetime.now() - d).days <= days
    except Exception as e:
        # print(f"Date parse error: {e}")
        return False

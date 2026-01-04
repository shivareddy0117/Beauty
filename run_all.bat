@echo off
echo Running Job Scrapers...

echo [1/2] Running Amazon Scraper...
"C:\Users\dell1\AppData\Local\Programs\Python\Python311\python.exe" amazon_scraper.py

echo [2/2] Running Microsoft Scraper...
"C:\Users\dell1\AppData\Local\Programs\Python\Python311\python.exe" microsoft_scraper.py

echo [3/4] Running CVS Health Scraper...
"C:\Users\dell1\AppData\Local\Programs\Python\Python311\python.exe" cvs_scraper.py

echo [4/4] Running JPMorgan Chase Scraper...
"C:\Users\dell1\AppData\Local\Programs\Python\Python311\python.exe" jpmc_scraper.py

echo.
echo ========================================
echo Scraping Complete!
echo Jobs saved to ui/jobs.js
echo Open ui/index.html to view the dashboard.
echo ========================================
pause

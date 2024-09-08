# fbref-scrape

Scripts to scrape data from Fbref. 

Current project status:
1) Scrape-Team-Fixtures script: retrieve and store in Excel file 2024 fixture data for user selected K-League 1 team, create urls Excel file containing the links to each team main page on fbref (to be used to scrape Match Report data)
2) Scrape-Match-Reports: use -> retrieve player stats from user selected K League 1 team from each match report. Save the scraped data in folder \Match-Reports\{selected-team}
3) Match Reports are now complete with both team players and goalkeepers data

Next features: 
1) Allow scraping of the selected league whole at once
2) Web app
3) Make Real DB 

Note: the project follows fbref scraping policy, which allows a maximum of 10 requests per minute.

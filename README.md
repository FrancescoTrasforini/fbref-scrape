# fbref-scrape

Scripts to scrape data from Fbref. 

Current project status:
1) Scrape-Team-Fixtures script: retrieve and store in Excel file 2024 fixture data for user selected K-League 1 team, create urls Excel file containing the links to each team main page on fbref (to be used to scrape Match Report data)
2) Scrape-Match-Reports: use -> retrieve player stats from user selected K League 1 team from each match report. Save the scraped data in folder \Match-Reports\{selected-team}
3) Match Reports are now complete with both team players and goalkeepers data
4) Allow user to select league and filter by gender
5) Scraping teams statistics in the competition, both for and against
6) Automatic scraping of fixtures

Next features: 
1) [In progress] Add links to match reports in the 'Match Report' field in Fixture files
2) Automatic scraping of reports from the selected league+season
3) Scrape the whole league at once
4) User Interface

File structure will be:
1) Main_Directory\{competition_name}-{gender}\{season}\{competition_name}_{season}.xlsx
2) Main_Directory\{competition_name}-{gender}\{season}\{Team}\{Team_data}_{season}.xlsx
3) Main_Directory\{competition_name}-{gender}\{season}\{Team}\Match Report-{match_number}-{Team}_{Opponent}_.xlsx

Note: the project follows fbref scraping policy, which allows a maximum of 10 requests per minute.

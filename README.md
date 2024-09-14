# fbref-scrape

Script to scrape data from Fbref. 

How to use it:
1) Download the files and execute the Scrape-Selected-League.ipynb
2) Insert league, gender (M/F) and season -> you need to know if the league is played across 2 years (e.g. 2023-2024) or in a single year (e.g. 2023)  

Current features:

1) User selects league, gender and season.
2) Scraping teams statistics in the competition, both for and against. Stored in different Excel files, "Season-Stats" and "Season-Stats-against".
3) Automatic scraping of fixtures.
4) Links to match reports added in the 'Match Report' field in Fixture files
5) Automatic scraping of reports from the selected league+season.

-> TL;DR: you can scrape the selected league statistics and each of its match reports automatically.
-> Note: the project follows fbref scraping policy, which allows a maximum of 10 requests per minute -> full season scraping procedure takes around 1h 
-> Note: the script has been designed to work for the leagues in which FBref offers full data coverage. For some leagues in which the data is structured in different ways, the script may not work as intended

Next features: 
1) User Interface
2) Fix known bugs (matching of desired league names doesn't always work as intended)

File structure:
1) Main_Directory\{competition_name}-{gender}\{season}\{competition_name}_{season}.xlsx
2) Main_Directory\{competition_name}-{gender}\{season}\{Team}\{Team_data}_{season}.xlsx
3) Main_Directory\{competition_name}-{gender}\{season}\{Team}\Match Report-{match_number}-{Team}_{Opponent}_.xlsx
 

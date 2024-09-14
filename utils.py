import time
import pandas as pd
import os
import json
import re
import requests
import openpyxl
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from rapidfuzz import process
from functools import lru_cache
from fuzzywuzzy import fuzz

# competitions dictionary

league_mapping = {
    "Liga Profesional de Fútbol Argentina": "Liga Argentina",
    "A-League Men": "A-League",
    "A-League Women": "A-League",
    "Austrian Football Bundesliga": "Bundesliga",
    "ÖFB Frauen-Bundesliga": "ÖFB Frauenliga",
    "Belgian Pro League": "Pro League A",
    "Belgian Women's Super League": "Belgian WSL",
    "División de Fútbol Profesional": "Primera División",
    "Campeonato Brasileiro Série A": "Série A",
    "Brasileirão Feminino Série A1": "Série A1",
    "First Professional Football League": "First League",
    "Canadian Premier League": "CanPL",
    "Chilean Primera División": "Primera División",
    "Chinese Football Association Super League": "Super League",
    "Categoría Primera A": "Primera A",
    "Croatian Football League": "HNL",
    "Czech First League": "Czech First League",
    "Danish Superliga": "Danish Superliga",
    "Danish Women's League": "Kvindeligaen",
    "Liga Profesional Ecuador": "Serie A",
    "Premier League": "Premier League",
    "FA Women's Super League": "WSL",
    "La Liga": "La Liga",
    "Liga F": "Liga F",
    "Veikkausliiga": "Veikkausliiga",
    "Ligue 1": "Ligue 1",
    "Première Ligue": "D1 Fém",
    "Fußball-Bundesliga": "Bundesliga",
    "Frauen-Bundesliga": "Bundesliga",
    "Super League Greece": "Super League",
    "Nemzeti Bajnokság I": "NB I",
    "Indian Super League": "Super League",
    "Persian Gulf Pro League": "Pro League",
    "Serie A": "Serie A",
    "J1 League": "J1 League",
    "Women Empowerment League": "WE League",
    "K League 1": "K League",
    "Saudi Professional League": "Saudi Professional League",
    "Liga MX": "Liga MX",
    "Eredivisie": "Eredivisie",
    "Eredivisie Vrouwen": "Eredivisie",
    "Eliteserien": "Eliteserien",
    "Toppserien": "Toppserien",
    "Paraguayan Primera División": "Primera Div",
    "Liga 1 de Fútbol Profesional": "Liga 1",
    "Ekstraklasa": "Ekstraklasa",
    "Primeira Liga": "Primeira Liga",
    "Liga I": "Liga I",
    "South African Premier Division": "Premier Division",
    "Russian Premier League": "Premier League",
    "Scottish Premiership": "Premiership",
    "Serbian SuperLiga": "SuperLiga",
    "Swiss Super League": "Super Lg",
    "Swiss Women's Super League": "Swiss WSL",
    "Allsvenskan": "Allsvenskan",
    "Damallsvenskan": "Damallsvenskan",
    "Süper Lig": "Süper Lig",
    "Ukrainian Premier League": "Premier League",
    "Uruguayan Primera División": "Uruguayan Primera División",
    "Major League Soccer": "MLS",
    "National Women's Soccer League": "NWSL",
    "Venezuelan Primera División": "Liga FUTVE",
    "Challenger Pro League": "Pro League B",
    "Campeonato Brasileiro Série B": "Série B",
    "EFL Championship": "Championship",
    "Spanish Segunda División": "La Liga 2",
    "Ligue 2": "Ligue 2",
    "2. Fußball-Bundesliga": "2. Bundesliga",
    "I-League": "I-League",
    "Serie B": "Serie B",
    "J2 League": "J2 League",
    "Eerste Divisie": "Eerste Divisie",
    "Scottish Championship": "Championship",
    "Superettan": "Superettan",
    "North American Soccer League": "NASL",
    "USL Championship": "USL Champ",
    "USL First Division": "USL D-1",
    "USSF Division 2 Professional League": "D2 Pro League"
}

# Initialize Selenium WebDriver
def init_webdriver():
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    service = Service(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=options)
    return driver

# Load the page and extract HTML content
def get_page_content(driver, url):
    driver.get(url)
    time.sleep(10)  # Wait for the page to load
    html = driver.page_source
    return html

# Parse the table using BeautifulSoup
def extract_table_data(html,table_name):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": table_name})
    
    # Extract table headers
    headers = [th.getText() for th in table.find("thead").findAll("th")]
    
    # Extract table rows
    rows = table.find("tbody").findAll("tr")
    data = []
    
    for row in rows:
        # "Date" appears to be in a <th> element rather than in a <td> one
        date = row.find("th").getText().strip()
        
        # Extract the rest of the columns (data) from <td> elements
        cells = row.findAll("td")
        # Replace empty values with 0
        cells = [cell if cell else '0' for cell in cells]  # <--- Replacement of empty data with '0'
        
        if len(cells) > 0:
            match_data = [cell.getText().strip() for cell in cells]  # Clean up the text
            match_data.insert(0, date)  # Insert the date at the beginning of the row data
            
            # This was for debugging purposes 
            # print(f"Row data ({len(match_data)}): {match_data}")  # Print row data for inspection
            
            # Check if the number of columns matches the headers
            if len(match_data) != len(headers):
                print(f"Skipping row with mismatched columns: {len(match_data)} columns")
                continue  # Skip this row if the column count doesn't match
            
            data.append(match_data)
    
    return headers, data

# Convert data to a DataFrame
def create_dataframe(headers, data):
    df = pd.DataFrame(data, columns=headers)
    # Clean up column names by removing any unnamed columns
    df.columns = df.columns.str.replace("Unnamed: ", "")
    # Add a new column "Match Number" starting from 1
    df.index = pd.RangeIndex(start=1, stop=len(df) + 1, step=1)
    df.index.name = "Match Number"
    return df

# Save data to Excel in a subfolder
def save_data(df, team):
    # Define the folder path and ensure the folder exists
    folder_path = os.path.join(os.getcwd(), "Fixtures")
    os.makedirs(folder_path, exist_ok=True)  # Create the folder if it doesn't exist
    
    # Define the full file path
    filename = os.path.join(folder_path, f"{team}_matches_2024.xlsx")
    
    # Save the DataFrame to the Excel file
    df.to_excel(filename, index=True)
    
    return filename

# Check if the table exists
def check_table(driver,table_name):
    try:
        table_exists = driver.find_element(By.ID, table_name)
        print(f"Table {table_exists} found using Selenium!")
    except:
        print(f"Table {table_exists} not found using Selenium")

def respect_fbref_scrape_policy():
    """
    Enforces FBref scrape policy of no more than 10 requests per minute
    by pausing for 6 seconds after each request.
    """
    print("Respecting FBref scrape policy... Sleeping for 6 seconds.")
    time.sleep(6)  # Sleep for 6 seconds to ensure we don't exceed 10 requests/minute

# Function to normalize team name input
def normalize_team_name(team_input):
    # Split the input into words
    words = team_input.split()
    
    # Capitalize the first letter of each word and remove "FC"
    normalized_words = [word.capitalize() for word in words if word.lower() != 'fc']
    
    # Join the words with a hyphen
    normalized_team = "-".join(normalized_words)
    
    return normalized_team

def extract_team_urls(url):
    base_url = "https://fbref.com"  # Root URL to prepend to relative links
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve FBref page. Status code: {response.status_code}")
        return {}, {}  # Return two empty dictionaries

    soup = BeautifulSoup(response.text, 'html.parser')

    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve FBref league page. Status code: {response.status_code}")
        return {}, {}  # Return two empty dictionaries

    table = soup.find("table", {"id": "stats_squads_standard_for"})
    print(f"Table: {table}")
    
    if not table:
        print("Table not found.")
        return []

    # Extract rows
    rows = table.find("tbody").findAll("tr")
    team_urls = []
    
    for row in rows:
        cells = row.findAll("th")
        if len(cells) > 0:
            team_links_cell = cells[0]
            # Print cell HTML for debugging
            #print(f"Cell HTML: {team_links_cell.prettify()}")
            
            link = team_links_cell.find("a")
            team = team_links_cell.text.strip()
            relative_url = link["href"] if link else None
            team_url = base_url + relative_url
            team_urls.append({'team':team, 'url':team_url})
            #print(f"Extracted URL: {team_url}")  # Debugging line

    return team_urls

def get_normalized_league(league):
    """Returns the normalized version of the league using the mapping."""
    best_match = None
    highest_score = 0
    
    # Loop through the league mapping to find the best match
    for official_name, alias in league_mapping.items():
        score = fuzz.ratio(league.lower(), official_name.lower())
        if score > highest_score:
            highest_score = score
            best_match = alias

    # Ensure that only a close enough match is selected
    if highest_score > 85:  # Consider only matches with a score above 85
        return best_match
    return league  # If no close match is found, return the original league

def extract_match_report_urls(team,url,league):
    base_url = "https://fbref.com"  # Root URL to prepend to relative links

    # Normalize the league name using the predefined mapping
    normalized_league = get_normalized_league(league)
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve FBref page. Status code: {response.status_code}")
        return {}, {}  # Return two empty dictionaries

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find("table", {"id": "matchlogs_for"})
    
    if not table:
        print("Table not found.")
        return []

    # Extract rows
    rows = table.find("tbody").findAll("tr")
    match_report_urls = []
    

    # Iterate over each row and find the specific td elements
    for row in rows:
        cells = row.find_all(lambda tag: tag.name == 'td' and tag.get('data-stat') in ['comp','opponent', 'match_report'])
        comp = None
        opponent = None
        link = None
        idx = 0
        while idx < len(cells):
            cell = cells[idx]
            if cell.get('data-stat') == 'comp':
                comp = cell.text.strip()
                print(f"Competition found: {comp}, Normalized League: {normalized_league}")
                # First, check if the competition matches the normalized league name
                if fuzz.ratio(comp.lower(), normalized_league.lower()) < 70:
                    # Skip if it doesn't match closely enough
                    print(f"Skipping competition: {comp}, not matching {normalized_league}")
                    idx += 3
                    continue
            if cell.get('data-stat') == 'opponent':
                opponent = cell.text.strip() 
            elif cell.get('data-stat') == 'match_report':
                link = cell.find('a')['href']
                match_report_url = base_url + link
                match_report_urls.append({'team': team, 'opponent': opponent, 'url': match_report_url})
                print(f"Team: {team}, Opponent: {opponent}, Link: {match_report_url}")  
            # Move to the next cell
            idx += 1
    
    return match_report_urls

# Update the main Excel file with Match Report URLs
def update_fixtures_with_match_report_urls(df,team,urls,file):
    # Ensure the number of URLs matches the number of rows in the DataFrame
    matching_rows = df[(df['Home'] == team) | (df['Away'] == team)]
    num_rows = len(matching_rows)
    num_urls = len(urls)
    
    # Avoid index mismatches by limiting the number of URLs or rows
    if num_rows != num_urls:
        raise ValueError(f"Warning: Mismatch between {team} DataFrame rows ({num_rows}) and URLs ({num_urls}).")
    else:
        #matching_rows["Match Report"] = urls
        matching_rows.loc[:, "Match Report"] = urls

    # Update the original DataFrame with the new 'Match Report' URLs
    df.update(matching_rows)
    
    #folder_path = os.path.join(os.getcwd())
    #filename = os.path.join(folder_path, f"Fixtures.xlsx")
    df.to_excel(file, index=False)
    print(f"Updated {file} with Match Report URLs.")

# Helper function to extract data from a player stats table
def extract_player_data(table):
    header_rows = table.find('thead').find_all('tr')
    if len(header_rows) > 1:
        # Use the second row for actual column names
        actual_headers_row = header_rows[1]
        headers = [header.text.strip() for header in actual_headers_row.find_all('th')]
    else:
        # Fallback to the first row if only one row of headers exists
        headers = [header.text.strip() for header in header_rows[0].find_all('th')]

    rows = table.find('tbody').find_all('tr')
    data = []
    for row in rows:
        cells = [cell.text.strip() for cell in row.find_all(['td', 'th'])]
        # Replace empty cells with 0
        cells = [cell if cell else '0' for cell in cells]
        if cells:
            data.append(cells)

    # Handle header/data column mismatch
    num_columns = len(data[0]) if data else 0
    if num_columns != len(headers):
        print(f"Warning: Mismatch between headers ({len(headers)}) and data columns ({num_columns}). Adjusting headers.")
        headers = headers[:num_columns]
    
    return pd.DataFrame(data, columns=headers)

def extract_player_stats(html, team, opponent):
    respect_fbref_scrape_policy()  # Enforce FBref scrape policy
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table')
    # Prepare team and opponent names
    teams = [team, opponent]
    dfs = []

    for team_name in teams:
        team_with_space = team_name.replace("-", " ")
        pattern = re.compile(
            rf"(?:FC\s+|SC\s+|Football\s+Club\s+)?{re.escape(team_with_space)}(?:\s+FC|\s+SC|\s+Football\s+Club)?",
            re.IGNORECASE
        )

        # Find the tables corresponding to the team or opponent
        tables_dict = {'Player Stats': [], 'Goalkeeper Stats': [], 'Shots': []}
        for table in tables:
            caption = table.find('caption')
            caption_text = caption.text.strip() if caption else 'No Caption'
            for key in tables_dict:
                if pattern.search(caption_text) and key in caption_text:
                    tables_dict[key].append(table)
        
        # Extract data from the found tables
        for key, table_list in tables_dict.items():
            for table in table_list:
                df = extract_player_data(table)
                dfs.append(df)

    return dfs

# Save the scraped match report tables to a new Excel file with multiple sheets
def save_report(dfs, team, opponent,report_file):
    
    # Save each dataframe in a separate sheet
    with pd.ExcelWriter(report_file, engine='xlsxwriter') as writer:
        # Define sheet names for each DataFrame
        sheet_names = [
            f"{team} Summary",
            f"{team} Pass",
            f"{team} PassType",
            f"{team} Def Act",
            f"{team} Poss",
            f"{team} Other",
            f"{team} GK",
            f"{opponent} Summary",
            f"{opponent} Pass",
            f"{opponent} PassType",
            f"{opponent} Def Act",
            f"{opponent} Poss",
            f"{opponent} Other",
            f"{opponent} GK",
            "Both Squads",
            f"{team} Shots",
            f"{opponent} Shots",
        ]
        
        # Iterate over the list of dataframes and save each one to a different sheet
        for i, df in enumerate(dfs):
            # Ensure sheet names match the order and number of DataFrames
            if i < len(sheet_names):  # Avoid index error if the list of dfs is shorter than sheet names
                sheet_name = sheet_names[i]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"Saved match report to {report_file}")
    return 

def scrape_and_save_reports(report_url,report_file,match_number,team,opponent):
    
    # Skip if there's no valid match report URL
    if not pd.isna(report_url):
        
        # Check if the URL contains "stathead" and break if true
        if "stathead" in report_url:
            print(f"Skipping Match {match_number} (not yet played): {report_url}")
            return  # Stop processing further rows

        print(f"Processing Match {match_number}: {team} vs {opponent}")
        

        response = requests.get(report_url)

        # Extract list of DataFrames (team and opponent)
        dfs = extract_player_stats(response.text, team, opponent)
        
        
        team_with_space = team.replace("-", " ")
        opponent_with_space = opponent.replace("-", " ")
        # Save all DataFrames into the same Excel file, in different sheets
        save_report(dfs, team_with_space, opponent_with_space,report_file)
        
    else:
        print(f"No match report found for Match {match_number}")

# Check if the urls.xlsx file exists
def check_url_file_exists():
    folder_path = os.path.join(os.getcwd(), "Team-Page-urls")
    filename = os.path.join(folder_path, "urls.xlsx")
    
    # Check if the file exists
    return os.path.exists(filename)

# Save urls to team pages in a subfolder
def save_team_urls(df):
    folder_path = os.path.join(os.getcwd(), "Team-Page-urls")
    os.makedirs(folder_path, exist_ok=True)  # Create the folder if it doesn't exist
    
    filename = os.path.join(folder_path, "urls.xlsx")
    
    if not os.path.exists(filename):
        df.to_excel(filename, index=True)
        print(f"File saved as {filename}")
    else:
        print(f"File {filename} already exists.")
    
    return filename

def load_team_urls():
    folder_path = os.path.join(os.getcwd(), "Team-Page-urls")
    filename = os.path.join(folder_path, "urls.xlsx")
    
    if os.path.exists(filename):
        # Load the Excel file into a DataFrame
        df = pd.read_excel(filename, index_col=0)  # index_col=0 to avoid the index column from Excel
        print(f"Loaded URLs from {filename}")
        return df
    else:
        print(f"File {filename} does not exist.")
        return None
    
def load_cache(cache_file):
    """Load cached URLs from a JSON file."""
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as file:
            return json.load(file)
    return {}

def save_cache(_dict, cache_file):
    """Save URLs to a JSON file for caching."""
    with open(cache_file, 'w') as file:
        json.dump(_dict, file)

def scrape_league_links_from_fbref():
    url = "https://fbref.com/en/comps/"  # FBref competitions page
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve FBref page. Status code: {response.status_code}")
        return {}, {}  # Return two empty dictionaries

    soup = BeautifulSoup(response.text, 'html.parser')
    
    men_league_dict = {}
    women_league_dict = {}
    
    # Find the table containing the top tier information
    top_leagues_table = soup.find('table', {'id': 'comps_1_fa_club_league_senior'})
    if not top_leagues_table:
        print("Could not find the top tier leagues table on the page.")
    
    # Loop through all rows in the table to extract league names, URLs, and genders
    for row in top_leagues_table.find('tbody').find_all('tr'):
        columns = row.find_all('td')
        headers = row.find_all('th')
        if len(headers) > 0 and len(columns) > 0:
            league_gender = columns[0].text.strip()  # Extract gender from the first td
            league_link_tag = headers[0].find('a')  # Find the link for the league in th
            if league_link_tag:
                league_name = league_link_tag.text.strip()
                league_url = 'https://fbref.com' + league_link_tag['href']
                if league_gender == 'M':
                    men_league_dict[league_name] = {'url': league_url, 'gender': league_gender}
                elif league_gender == 'F':
                    women_league_dict[league_name] = {'url': league_url, 'gender': league_gender}
    
    # Find the table containing the second tier information
    second_leagues_table = soup.find('table', {'id': 'comps_2_fa_club_league_senior'})
    if not second_leagues_table:
        print("Could not find the second tier leagues table on the page.")
    
    # Loop through all rows in the table to extract league names, URLs, and genders
    for row in second_leagues_table.find('tbody').find_all('tr'):
        columns = row.find_all('td')
        headers = row.find_all('th')
        if len(headers) > 0 and len(columns) > 0:
            league_gender = columns[0].text.strip()  # Extract gender from the first td
            league_link_tag = headers[0].find('a')  # Find the link for the league in th
            if league_link_tag:
                league_name = league_link_tag.text.strip()
                league_url = 'https://fbref.com' + league_link_tag['href']
                if league_gender == 'M':
                    men_league_dict[league_name] = {'url': league_url, 'gender': league_gender}
                elif league_gender == 'F':
                    women_league_dict[league_name] = {'url': league_url, 'gender': league_gender}
    
    return men_league_dict, women_league_dict

# Function to get league links, using caching to avoid redundant scraping
@lru_cache(maxsize=32)  # Caches the result in memory for 32 different league scrapes
def get_league_links(cache_file):
    #"""Scrapes the league URLs or loads them from cache."""
    league_dict = load_cache(cache_file)  # First try to load from cache
    if not league_dict:  # If cache is empty, scrape the league URLs
        # Placeholder for scraping logic
        # Example: league_dict = {'K League 1': 'https://fbref.com/en/comps/55/K-League-1'}
        league_dict = scrape_league_links_from_fbref()  # Your scraping function here
        save_cache(league_dict,cache_file)  # Save the newly scraped league URLs to cache
    return league_dict

# Fuzzy matching to get the closest league name with the specified gender
def get_closest_league(input_league, cache_file, gender):
    men_dict, women_dict = get_league_links(cache_file)  # Fetch the league dictionaries
    
    # Select the appropriate dictionary based on gender
    if gender.upper() == 'M':
        league_dict = men_dict
    elif gender.upper() == 'F':
        league_dict = women_dict
    else:
        print("Invalid gender specified. Use 'M' for men or 'F' for women.")
        return None, None
    
    league_names = list(league_dict.keys())  # List of league names after filtering
    closest_match = process.extractOne(input_league, league_names)  # Fuzzy match

    if closest_match and closest_match[1] > 80:  # Set a threshold for accuracy (80% in this case)
        league_name = closest_match[0]
        league_info = league_dict[league_name]  # Get the league's URL and gender
        return league_name, league_info  # Return the match and its URL and gender

    return None, None

# Function to scrape league links from FBref's main competitions page
def scrape_season_links_from_fbref(league_url):
    print(f"League URL: {league_url}") #debugging
    response = requests.get(league_url)
    if response.status_code != 200:
        print(f"Failed to retrieve FBref page. Status code: {response.status_code}")
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    
    seasons_dict = {}
    
    # Find the table containing the seasons
    seasons_table = soup.find('table', {'id': 'seasons'})
    if not seasons_table:
        print("Could not find the season table on the page.")
        return {}
    
    # Loop through all rows in the table to extract seasons and URLs
    for row in seasons_table.find('tbody').find_all('th'):
        season_link_tag = row.find('a')  # Find the link for the season
        if season_link_tag:
            season_name = season_link_tag.text.strip()
            season_url = 'https://fbref.com' + season_link_tag['href']
            seasons_dict[season_name] = season_url  
             
    return seasons_dict

# Function to get season links, using caching to avoid redundant scraping
@lru_cache(maxsize=64)  # Caches the result in memory for 64 different season scrapes
def get_season_links(cache_file,league_url):
    #"""Scrapes the season URLs or loads them from cache."""
    season_dict = load_cache(cache_file)  # First try to load from cache
    if not season_dict:  # If cache is empty, scrape the season URLs
        season_dict = scrape_season_links_from_fbref(league_url)  
        save_cache(season_dict,cache_file)  # Save the newly scraped league URLs to cache
    return season_dict

def get_season_url(season,cache_file,league_url):
    season_dict = get_season_links(cache_file,league_url)  # Fetch the league dictionary, either from cache or by scraping
    seasons_list = list(season_dict.keys())  # List of league names
    closest_match = process.extractOne(season, seasons_list)  # Fuzzy match

    if closest_match and closest_match[1] > 80:  # Set a threshold for accuracy (80% in this case)
        return closest_match[0], season_dict[closest_match[0]]  # Return the match and its URL
    return None, None

def get_scores_and_fixtures_url(competition_url):
    # Send a request to the competition page
    response = requests.get(competition_url)
    if response.status_code != 200:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the div with id "inner_nav" and look for the "Scores & Fixtures" link
    inner_nav = soup.find('div', {'id': 'inner_nav'})
    if not inner_nav:
        print("Could not find the 'inner_nav' section.")
        return None

    scores_link_tag = inner_nav.find('a', string="Scores & Fixtures")
    if not scores_link_tag:
        print("Could not find the 'Scores & Fixtures' link.")
        return None
    
    # Extract the relative URL and create the full URL
    scores_fixtures_url = 'https://fbref.com' + scores_link_tag['href']
    
    return scores_fixtures_url

def scrape_page_tables(url, output_file, table_card_position):
    """
    Scrape tables from the given URL and save to an Excel file. 
    The table_card_position determines if the scraped tables are in the "left" or "right" container.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all divs that have class "table_container"
    tables_div = soup.find_all('div', class_='table_container')

    if not tables_div:
        print(f"No tables found.")
        return
    
    # Initialize the Excel writer
    writer = pd.ExcelWriter(output_file, engine='openpyxl')

    for div in tables_div:
        # Check if the div belongs to the "left" or "right" card based on the presence of "current"
        is_left_card = 'current' in div.get('class', [])

        # Continue only if the current div matches the specified table_card_position
        if (table_card_position == "left" and not is_left_card) or (table_card_position == "right" and is_left_card):
            continue

        # Ensure the div contains a table
        table = div.find('table')
        if not table:
            continue

        # Extract the caption
        caption_tag = table.find('caption')
        if not caption_tag:
            continue

        caption = caption_tag.text.strip()

        # Extract table headers and rows
        headers = []
        rows = []
        
        # Extract table headers and rows
        header_rows = table.find('thead').find_all('tr')
        if len(header_rows) > 1:
            # Use the second row for actual column names if there are two rows
            headers = [header.text.strip() for header in header_rows[1].find_all('th')]
        else:
            # Fallback to the first row if only one row of headers exists
            headers = [header.text.strip() for header in header_rows[0].find_all('th')]
        #if header_rows:
        #    if len(header_rows) > 1:
        #        # Use the second row for actual column names
        #        actual_headers_row = header_rows[1]
        #        headers = [header.text.strip() for header in actual_headers_row.find_all('th')]
        #    else:
        #        # Fallback to the first row if only one row of headers exists
        #        headers = [header.text.strip() for header in header_rows[0].find_all('th')]

        # Extract rows
        body = table.find('tbody')
        if body:
            for row in body.find_all('tr'):
                cells = [cell.text.strip() for cell in row.find_all(['td', 'th'])]
                rows.append(cells)
                # Replace empty cells with 0
                #cells = [cell if cell else '0' for cell in cells]
                #if cells:
                #    rows.append(cells)

        # Handle header/data column mismatch
        num_columns = len(rows[0]) if rows else 0
        if num_columns != len(headers):
            print(f"Warning: Mismatch between headers ({len(headers)}) and data columns ({num_columns}). Adjusting headers.")
            headers = headers[:num_columns]
        
        # Create DataFrame
        try:
            df = pd.DataFrame(rows, columns=headers)
        except ValueError as e:
            print(f"Error creating DataFrame: {e}")
            continue

        # Drop rows where all values are NaN
        df.dropna(how='all', inplace=True)
        
        # Fill any remaining NaN values with 0 (in case of unbalanced rows or missing data)
        df.fillna(0, inplace=True)
        
        # Write each table to a different sheet named after the caption
        sheet_name = caption[:31]  # Excel sheet names are limited to 31 characters
        df.to_excel(writer, sheet_name=sheet_name, index=False)

    writer.close()





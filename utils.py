import time
import pandas as pd
import os
import re
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

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

def extract_league_teams(html):
    base_url = "https://fbref.com"  # Root URL to prepend to relative links
    soup = BeautifulSoup(html, "html.parser")
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
            relative_url = link["href"] if link else None
            team_url = base_url + relative_url
            team_urls.append(team_url)
            #print(f"Extracted URL: {team_url}")  # Debugging line
    
    return team_urls

def extract_match_report_urls(html):
    base_url = "https://fbref.com"  # Root URL to prepend to relative links
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "matchlogs_for"})
    
    if not table:
        print("Table not found.")
        return []

    # Extract rows
    rows = table.find("tbody").findAll("tr")
    match_report_urls = []
    
    for row in rows:
        cells = row.findAll("td")
        if len(cells) > 0:
            match_report_cell = cells[-2]
            # Print cell HTML for debugging
            #print(f"Cell HTML: {match_report_cell.prettify()}")
            
            link = match_report_cell.find("a")
            relative_url = link["href"] if link else None
            match_report_url = base_url + relative_url
            match_report_urls.append(match_report_url)
            #print(f"Extracted URL: {match_report_url}")  # Debugging line
    
    return match_report_urls

# Update the main Excel file with Match Report URLs
def update_match_report_urls(df,urls,team):
    df["Match Report"] = urls
    folder_path = os.path.join(os.getcwd(), "Fixtures")
    filename = os.path.join(folder_path, f"{team}_matches_2024.xlsx")
    df.to_excel(filename, index=False)
    print(f"Updated {filename} with Match Report URLs.")

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
        tables = {'Player Stats': None, 'Goalkeeper Stats': None}
        for tbl in soup.find_all('table'):
            caption = tbl.find('caption')
            if caption:
                caption_text = caption.get_text(strip=True)
                for key in tables:
                    if pattern.search(caption_text) and key in caption_text:
                        tables[key] = tbl

        # Check for missing tables
        for key, table in tables.items():
            if not table:
                raise ValueError(f"Table with caption containing '{team_with_space}' and '{key} Table' not found.")
        
        # Extract data from the tables and append DataFrames
        for key in tables:
            df = extract_player_data(tables[key])
            dfs.append(df)
    
    return dfs

# Save the scraped match report tables to a new Excel file with multiple sheets
def save_report(dfs, team, opponent, match_number):
    # Create folder path if it doesn't exist
    folder_path = f"Match-Reports\{team}"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # Define filename and full file path
    filename = f"Report Matchday {match_number} - {team} - {opponent}.xlsx"
    file_path = os.path.join(folder_path, filename)
    
    # Save each dataframe in a separate sheet
    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        # Define sheet names for each DataFrame
        sheet_names = [
            f"{team} Players",
            f"{team} Goalkeeper",
            f"{opponent} Players",
            f"{opponent} Goalkeeper"
        ]
        
        # Iterate over the list of dataframes and save each one to a different sheet
        for i, df in enumerate(dfs):
            # Ensure sheet names match the order and number of DataFrames
            sheet_name = sheet_names[i]
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"Saved match report to {file_path}")
    return file_path

def scrape_and_save_reports(df, driver, team):
    
    for index, row in df.iterrows():
        match_report_url = row["Match Report"]
        opponent = row["Opponent"]
        opponent_normalized = normalize_team_name(opponent)
        match_number = index + 1  # Match number as a unique identifier

        # Skip if there's no valid match report URL
        if not pd.isna(match_report_url):
            
            # Check if the URL contains "stathead" and break if true
            if "stathead" in match_report_url:
                print(f"Skipping Match {match_number} (not yet played): {match_report_url}")
                break  # Stop processing further rows

            print(f"Processing Match {match_number}: {team} vs {opponent_normalized}")
            
            # Load match report page
            html = get_page_content(driver, match_report_url)
            
            # Extract list of DataFrames (team and opponent)
            dfs = extract_player_stats(html, team, opponent_normalized)
            
            # Check if both DataFrames are present
            if all(df is not None for df in dfs):
                # remove "-" from team name
                team_with_space = team.replace("-", " ")
                opponent_with_space = opponent_normalized.replace("-", " ")
                # Save all DataFrames into the same Excel file, in different sheets
                file_path = save_report(dfs, team_with_space, opponent_with_space, match_number)

                # Optionally update the main Excel file with file paths or other metadata
                df.at[index, "Match Report"] = file_path
            
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
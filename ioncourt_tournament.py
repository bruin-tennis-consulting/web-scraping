import requests
import pandas as pd
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
# be especiallly critical of lines 43 and 52
class IONCourtTournamentScraper:
    def __init__(self):
        self.driver = None
        self.all_singles_stats = []  # Separate collection for singles
        self.all_doubles_stats = []  # Separate collection for doubles
        self.headers = {"UserAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}
    
    def start_driver(self):
        """Initialize Chrome driver"""
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
    
    def close_driver(self):
        """Close Chrome driver"""
        if self.driver:
            self.driver.quit()
    
    def login_to_ioncourt(self):
        """Login to IONCourt using provided credentials"""
        try:
            print("Logging into IONCourt...")
            self.driver.get("https://ioncourt.com/login")
            time.sleep(3)
            
            # Look for phone number field using specific XPATH
            phone_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/app-root/ion-app/ion-split-pane/ion-router-outlet/app-auth/ion-content/div/app-login/form/ion-list/ion-row/ion-col[2]/ion-item/ion-input/label/div[2]/input"))
            )
            # Click to focus the field first
            phone_field.click()
            time.sleep(1)
            phone_field.clear()
            phone_field.send_keys() # enter ur phone number here 
            time.sleep(1)
            
            # Look for password field using specific XPATH
            password_field = self.driver.find_element(By.XPATH, "/html/body/app-root/ion-app/ion-split-pane/ion-router-outlet/app-auth/ion-content/div/app-login/form/ion-list/ion-item/ion-input/label/div[2]/input")
            # Click to focus the field first
            password_field.click()
            time.sleep(1)
            password_field.clear()
            password_field.send_keys() # enter ur password here 
            time.sleep(1)
            
            # Click login button - try different selectors
            try:
                login_button = self.driver.find_element(By.XPATH, "//ion-button[@type='submit']")
            except:
                try:
                    login_button = self.driver.find_element(By.XPATH, "//ion-button[contains(text(), 'Log')]")
                except:
                    login_button = self.driver.find_element(By.CSS_SELECTOR, "ion-button[type='submit']")
            
            login_button.click()
            
            # Wait for login to complete
            WebDriverWait(self.driver, 10).until(
                lambda d: "login" not in d.current_url
            )
            
            print("Successfully logged into IONCourt")
            return True
            
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    def process_all_teams(self, tournament_name):
        """Process all teams one by one without collecting links first"""
        try:
            # Get all team elements (but don't click them yet)
            team_elements = self.driver.find_elements(By.XPATH, "//app-team-item/ion-item/ion-label")
            print(f"Found {len(team_elements)} teams to process")
            
            for i in range(len(team_elements)):
                try:
                    # Re-find team elements (page state might have changed)
                    team_elements = self.driver.find_elements(By.XPATH, "//app-team-item/ion-item/ion-label")
                    
                    if i >= len(team_elements):
                        print(f"Team {i+1} no longer available, skipping")
                        continue
                        
                    team_element = team_elements[i]
                    print(f"\n--- Processing Team {i+1}/{len(team_elements)} ---")
                    
                    # Click on this team
                    team_element.click()
                    time.sleep(3)
                    
                    # Get team name and process matches
                    team_name = self.get_team_name()
                    print(f"Team: {team_name}")
                    
                    # Get all matches for this team
                    match_links = self.get_team_match_links()
                    print(f"Found {len(match_links)} matches for {team_name}")
                    
                    # Process each match for this team
                    for j, match_link in enumerate(match_links):
                        print(f"  Processing match {j+1}/{len(match_links)}")
                        try:
                            self.process_match_tie(match_link, tournament_name, team_name)
                        except Exception as e:
                            print(f"  Error processing match {match_link}: {e}")
                            continue
                    
                    # Go back to teams page for next team
                    self.driver.back()
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"Error processing team {i+1}: {e}")
                    # Try to get back to teams page
                    try:
                        self.driver.back()
                        time.sleep(2)
                    except:
                        pass
                    continue
                    
        except Exception as e:
            print(f"Error in process_all_teams: {e}")

    def scrape_tournament(self, tournament_url):
        """
        Main function to scrape entire tournament
        Example URL: https://ioncourt.com/leagues/intennse-pro-league
        """
        try:
            self.start_driver()
            
            # First login to IONCourt
            if not self.login_to_ioncourt():
                print("Login failed - cannot proceed")
                return
            
            print(f"Starting tournament scrape for: {tournament_url}")
            self.driver.get(tournament_url)
            time.sleep(3)
            
            # Extract tournament name from URL for file naming
            tournament_name = tournament_url.split('/')[-1].replace('-', ' ').title()
            print(f"Tournament: {tournament_name}")
            
            # Step 1: Click on "Teams" tab
            self.click_teams_tab()
            
            # Step 2: Process all teams one by one
            self.process_all_teams(tournament_name)
            
            # Step 3: Save all data
            self.save_tournament_data(tournament_name)
            
        except Exception as e:
            print(f"Error in tournament scraping: {e}")
        finally:
            self.close_driver()
    
    def get_tournament_name(self):
        """Extract tournament name from current page - REMOVED"""
        pass
    
    def click_teams_tab(self):
        """Click the Teams tab/button"""
        try:
            teams_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/ion-app/ion-split-pane/ion-router-outlet/app-league-details/ion-header/ion-toolbar[2]/ion-segment/ion-segment-button[2]"))
            )
            teams_button.click()
            time.sleep(2)
            print("Clicked Teams tab")
        except Exception as e:
            print(f"Error clicking Teams tab: {e}")
            raise
    
    def get_team_links(self):
        """Get all team links from teams page"""
        try:
            # Get all team elements - generalize the XPATH to get all teams
            team_elements = self.driver.find_elements(By.XPATH, "//app-team-item/ion-item/ion-label")
            team_links = []
            
            for elem in team_elements:
                try:
                    # Click on the team element to get the link
                    elem.click()
                    time.sleep(1)
                    current_url = self.driver.current_url
                    team_links.append(current_url)
                    print(f"Found team link: {current_url}")
                    # Go back to teams page
                    self.driver.back()
                    time.sleep(1)
                except Exception as e:
                    print(f"Error getting link for team element: {e}")
                    continue
            
            return team_links
        except Exception as e:
            print(f"Error getting team links: {e}")
            return []
    
    def process_team(self, team_url, tournament_name):
        """Process individual team schedule"""
        try:
            print(f"  Navigating to team: {team_url}")
            self.driver.get(team_url)
            time.sleep(3)
            
            # Get team name from URL or page
            team_name = self.get_team_name()
            print(f"  Team: {team_name}")
            
            # Get all match links for this team
            match_links = self.get_team_match_links()
            print(f"  Found {len(match_links)} matches for {team_name}")
            
            # Process each match
            for j, match_link in enumerate(match_links):
                print(f"    Processing match {j+1}/{len(match_links)}")
                try:
                    self.process_match_tie(match_link, tournament_name, team_name)
                except Exception as e:
                    print(f"    Error processing match {match_link}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error processing team {team_url}: {e}")
    
    def get_team_name(self):
        """Extract team name from current page"""
        try:
            # Try to get team name from URL or page title
            current_url = self.driver.current_url
            if "/teams/" in current_url:
                # Extract team ID from URL and use that as team name for now
                team_id = current_url.split("/teams/")[-1].split("/")[0]
                return f"Team_{team_id}"
            else:
                # Try to find team name on page
                try:
                    team_element = self.driver.find_element(By.XPATH, "//ion-title")
                    return team_element.text.strip()
                except:
                    return "Unknown Team"
        except Exception as e:
            print(f"Could not get team name: {e}")
            return "Unknown Team"
    
    def get_team_match_links(self):
        """Get all match links from team schedule"""
        try:
            # Get all match elements using generalized XPATH for app-tie-scorecard
            match_elements = self.driver.find_elements(By.XPATH, "//app-tie-scorecard/ion-card")
            match_links = []
            
            print(f"    Found {len(match_elements)} matches on team schedule")
            
            for i in range(len(match_elements)):
                try:
                    # Re-find match elements each time (page state might have changed)
                    match_elements = self.driver.find_elements(By.XPATH, "//app-tie-scorecard/ion-card")
                    
                    if i >= len(match_elements):
                        print(f"      Match {i+1} no longer available, skipping")
                        continue
                    
                    match_element = match_elements[i]
                    print(f"      Clicking match {i+1}/{len(match_elements)}")
                    
                    # Click on the match element to get the match URL
                    match_element.click()
                    time.sleep(2)  # Wait for navigation
                    current_url = self.driver.current_url
                    match_links.append(current_url)
                    print(f"      Found match link: {current_url}")
                    
                    # Use IONCourt's back button instead of browser back
                    if not self.click_ioncourt_back_button():
                        print("      Falling back to browser back")
                        self.driver.back()
                        time.sleep(2)
                    
                except Exception as e:
                    print(f"      Error getting link for match element {i+1}: {e}")
                    # Try to get back to schedule page if something went wrong
                    if not self.click_ioncourt_back_button():
                        try:
                            self.driver.back()
                            time.sleep(2)
                        except:
                            pass
                    continue
            
            return match_links
        except Exception as e:
            print(f"Error getting match links: {e}")
            return []
    
    def process_match_tie(self, tie_url, tournament_name, team_name):
        """Process a tie (contains multiple individual matches - both singles and doubles)"""
        try:
            print(f"      Navigating to tie: {tie_url}")
            self.driver.get(tie_url)
            time.sleep(3)
            
            # Process doubles matches first (ion-item-group[1])
            print(f"        Processing doubles matches...")
            try:
                self.process_match_group(tie_url, tournament_name, team_name, group_index=1, match_type="Doubles")
                print(f"        ✅ Completed doubles processing")
            except Exception as e:
                print(f"        ❌ Error in doubles processing: {e}")
            
            # Make sure we're back on the tie page before processing singles
            self.driver.get(tie_url)
            time.sleep(2)
            
            # Process singles matches second (ion-item-group[2])
            print(f"        Processing singles matches...")
            try:
                self.process_match_group(tie_url, tournament_name, team_name, group_index=2, match_type="Singles")
                print(f"        ✅ Completed singles processing")
            except Exception as e:
                print(f"        ❌ Error in singles processing: {e}")
            
            print(f"      ✅ Completed entire tie: {tie_url}")
            
        except Exception as e:
            print(f"Error processing tie {tie_url}: {e}")
    
    def process_match_group(self, tie_url, tournament_name, team_name, group_index, match_type):
        """Process all matches in a specific ion-item-group (either doubles or singles)"""
        try:
            print(f"        Starting {match_type.lower()} processing for group {group_index}")
            
            match_index = 0
            max_attempts = 10  # Prevent infinite loops
            
            while match_index < max_attempts:
                # ALWAYS re-find matches to avoid stale elements
                group_matches = self.find_matches_in_group(group_index)
                
                if not group_matches:
                    print(f"          No {match_type.lower()} matches found in group {group_index}")
                    break
                
                if match_index >= len(group_matches):
                    print(f"          Processed all {match_index} {match_type.lower()} matches")
                    break
                
                print(f"          Processing {match_type.lower()} match {match_index + 1}/{len(group_matches)}")
                
                try:
                    # Always get fresh element reference
                    if match_index < len(group_matches):
                        match_element = group_matches[match_index]
                    else:
                        print(f"            Match index {match_index} out of range ({len(group_matches)} matches)")
                        break
                    
                    # Scroll element into view before clicking
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", match_element)
                    time.sleep(1)
                    
                    # Add wait for element to be clickable
                    WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(match_element)
                    )
                    
                    # Click the app-sb-body element directly
                    match_element.click()
                    time.sleep(3)
                    
                    # Wait for page to load and check URL changed
                    current_url = self.driver.current_url
                    print(f"            Navigated to: {current_url}")
                    
                    # Scrape match data based on type
                    if match_type == 'Singles':
                        match_data = self.scrape_singles_match_data(tie_url, tournament_name, team_name, {})
                    else:  # Doubles
                        match_data = self.scrape_doubles_match_data(tie_url, tournament_name, team_name, {})
                    
                    if match_data:
                        if match_type == 'Singles':
                            self.all_singles_stats.append(match_data)
                        else:
                            self.all_doubles_stats.append(match_data)
                        print(f"            ✅ Successfully scraped {match_type} match")
                    else:
                        print(f"            ❌ Failed to scrape {match_type} match data")
                    
                    # Go back to tie page for next match
                    print(f"            Going back to tie page...")
                    self.driver.back()
                    time.sleep(3)  # Increased wait time after back navigation
                    
                    # Verify we're back on the tie page and wait for it to load
                    if tie_url not in self.driver.current_url:
                        print(f"            Back button didn't work, forcing refresh to tie page")
                        self.driver.get(tie_url)
                        time.sleep(3)
                    
                    # Wait for page to stabilize before finding next elements
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, f"//ion-item-group[{group_index}]"))
                    )
                    time.sleep(1)  # Extra stability wait
                    
                    # Increment to process next match
                    match_index += 1
                    
                except Exception as e:
                    print(f"            ❌ Error processing {match_type.lower()} match {match_index + 1}: {e}")
                    # Try to get back to tie page
                    try:
                        print(f"            Attempting recovery - going back to tie page")
                        self.driver.get(tie_url)
                        time.sleep(3)
                        
                        # Wait for page to load after recovery
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, f"//ion-item-group[{group_index}]"))
                        )
                        time.sleep(1)
                        
                    except Exception as recovery_error:
                        print(f"            Recovery failed: {recovery_error}")
                        break
                    
                    # Skip this match and try the next one
                    match_index += 1
                    continue
            
            if match_index >= max_attempts:
                print(f"        ⚠️ Reached max attempts ({max_attempts}) for {match_type.lower()} matches")
            else:
                print(f"        ✅ Finished processing {match_type.lower()} matches")
                    
        except Exception as e:
            print(f"        ❌ Error processing {match_type.lower()} matches: {e}")
    
    def find_matches_in_group(self, group_index):
        """Find all match div elements within a specific ion-item-group"""
        try:
            # Use the exact XPATH structure to find the clickable app-sb-body elements
            xpath = f"/html/body/app-root/ion-app/ion-split-pane/ion-router-outlet/app-tie-details/ion-content/app-tie-match-list/div[1]/ion-list/ion-item-group[{group_index}]/div/app-tie-match-scoreboard/div/app-scoreboard/ion-card/div/div/app-sb-body"
            match_elements = self.driver.find_elements(By.XPATH, xpath)
            print(f"          Found {len(match_elements)} matches in group {group_index}")
            return match_elements
        except Exception as e:
            print(f"          Error finding matches in group {group_index}: {e}")
            return []
    
    def extract_match_info_and_type(self, match_element):
        """Extract match info and determine if it's singles or doubles based on participant count"""
        try:
            # Find participants within this match div (which contains app-tie-match-scoreboard)
            participants = match_element.find_elements(By.XPATH, ".//app-sb-participant")
            
            match_info = {
                'match_type': 'Unknown',
                'participants': []
            }
            
            total_names = 0
            for participant in participants:
                # Count the number of names in this participant element
                participant_text = participant.text.strip()
                # Split by lines to count individual names
                names_in_participant = [line.strip() for line in participant_text.split('\n') if line.strip() and '(' in line]
                total_names += len(names_in_participant)
                match_info['participants'].append(names_in_participant)
            
            # Determine match type based on total names
            if total_names == 2:  # 1 name per side = Singles
                match_info['match_type'] = 'Singles'
            elif total_names == 4:  # 2 names per side = Doubles
                match_info['match_type'] = 'Doubles'
            
            print(f"          Detected {match_info['match_type']} match (total names: {total_names})")
            return match_info
            
        except Exception as e:
            print(f"          Error extracting match info: {e}")
            return {'match_type': 'Unknown', 'participants': []}
    
    def scrape_singles_match_data(self, tie_url, tournament_name, team_name, match_info):
        """Scrape singles match data using script_singles.py logic"""
        try:
            # Get current match URL for API call
            current_url = self.driver.current_url
            
            # 1. Get basic match data via API (like script_singles.py)
            api_data = self.get_match_api_data(current_url)
            
            # 2. Click stats tab and get detailed stats via Selenium
            stats_data = self.get_detailed_match_stats_singles()
            
            # 3. Combine all data using script_singles.py format
            combined_data = {
                **(api_data if api_data else {}),
                **stats_data,
                "match_type": "Singles",
                "tournament": tournament_name,
                "team": team_name,
                "tie_url": tie_url,
                "match_url": current_url
            }
            
            return combined_data
            
        except Exception as e:
            print(f"        Error scraping singles match data: {e}")
            return None
    
    def scrape_doubles_match_data(self, tie_url, tournament_name, team_name, match_info):
        """Scrape doubles match data using script_doubles.py logic"""
        try:
            # Get current match URL for API call
            current_url = self.driver.current_url
            
            # 1. Get basic match data via API (like script_doubles.py)
            api_data = self.get_doubles_match_api_data(current_url)
            
            # 2. Click stats tab and get detailed stats via Selenium
            stats_data = self.get_detailed_match_stats_doubles()
            
            # 3. Combine all data using script_doubles.py format
            combined_data = {
                **(api_data if api_data else {}),
                **stats_data,
                "match_type": "Doubles",
                "tournament": tournament_name,
                "team": team_name,
                "tie_url": tie_url,
                "match_url": current_url
            }
            
            return combined_data
            
        except Exception as e:
            print(f"        Error scraping doubles match data: {e}")
            return None
    
    def get_detailed_match_stats_singles(self):
        """Get detailed match stats for singles using script_singles.py logic"""
        try:
            # Click on Stats tab using correct IONCourt XPATH (with ion-toolbar)
            print(f"          Clicking Stats tab...")
            stats_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/ion-app/ion-split-pane/ion-router-outlet/app-match-details/ion-split-pane/ion-router-outlet/app-match-tracker/ion-content/div[1]/ion-toolbar/ion-segment/ion-segment-button[3]"))
            )
            stats_button.click()
            time.sleep(2)
            
            # Get the stats grid using correct IONCourt XPATH
            print(f"          Scraping stats section...")
            stats_section = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/app-root/ion-app/ion-split-pane/ion-router-outlet/app-match-details/ion-split-pane/ion-router-outlet/app-match-tracker/ion-content/div[3]/app-stats"))
            )
            
            raw_data = stats_section.text
            print(f"          Raw stats data preview: {raw_data[:200]}...")
            
            # Parse stats using script_singles.py logic
            return self.parse_singles_stats_data(raw_data)
            
        except Exception as e:
            print(f"          Error getting detailed singles stats: {e}")
            return {}
    
    def get_detailed_match_stats_doubles(self):
        """Get detailed match stats for doubles using script_doubles.py logic"""
        try:
            # Click on Stats tab using correct IONCourt XPATH (with ion-toolbar)
            print(f"          Clicking Stats tab...")
            stats_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/ion-app/ion-split-pane/ion-router-outlet/app-match-details/ion-split-pane/ion-router-outlet/app-match-tracker/ion-content/div[1]/ion-toolbar/ion-segment/ion-segment-button[3]"))
            )
            stats_button.click()
            time.sleep(2)
            
            # Get the stats grid using correct IONCourt XPATH
            print(f"          Scraping stats section...")
            stats_section = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/app-root/ion-app/ion-split-pane/ion-router-outlet/app-match-details/ion-split-pane/ion-router-outlet/app-match-tracker/ion-content/div[3]/app-stats"))
            )
            
            raw_data = stats_section.text
            print(f"          Raw stats data preview: {raw_data[:200]}...")
            
            # Parse stats using script_doubles.py logic
            return self.parse_doubles_stats_data(raw_data)
            
        except Exception as e:
            print(f"          Error getting detailed doubles stats: {e}")
            return {}
    
    def parse_singles_stats_data(self, raw_data):
        """Parse raw stats data using script_singles.py logic"""
        try:
            lines = raw_data.strip().splitlines()
            start_index = 33  # Same as script_singles.py
            relevant_lines = lines[start_index:]
            
            stats = {
                "aces_player1": "", "aces_player2": "",
                "double_faults_player1": "", "double_faults_player2": "",
                "1st_serve_percentage_player1": "", "1st_serve_percentage_player2": "",
                "1st_serve_points_won_player1": "", "1st_serve_points_won_player2": "",
                "2nd_serve_points_won_player1": "", "2nd_serve_points_won_player2": "",
                "total_serve_points_won_player1": "", "total_serve_points_won_player2": "",
                "returns_made_player1": "", "returns_made_player2": "",
                "1st_serve_return_points_won_player1": "", "1st_serve_return_points_won_player2": "",
                "2nd_serve_return_points_won_player1": "", "2nd_serve_return_points_won_player2": "",
                "total_return_points_won_player1": "", "total_return_points_won_player2": "",
                "break_points_won_player1": "", "break_points_won_player2": "",
            }
            
            stat_keys = list(stats.keys())
            j = 0
            
            # Same parsing logic as script_singles.py (every 3 lines)
            for i in range(0, len(relevant_lines), 3):
                if j < len(stat_keys):
                    stats[stat_keys[j]] = relevant_lines[i].strip()
                    j += 1
                if j < len(stat_keys):
                    stats[stat_keys[j]] = relevant_lines[i + 2].strip()
                    j += 1
            
            return stats
            
        except Exception as e:
            print(f"          Error parsing singles stats data: {e}")
            return {}
    
    def parse_doubles_stats_data(self, raw_data):
        """Parse raw stats data using script_doubles.py logic"""
        try:
            lines = raw_data.strip().splitlines()
            start_index = 33  # Same as script_doubles.py
            relevant_lines = lines[start_index:]
            
            stats = {
                "aces_team1": "", "aces_team2": "",
                "double_faults_team1": "", "double_faults_team2": "",
                "1st_serve_percentage_team1": "", "1st_serve_percentage_team2": "",
                "1st_serve_points_won_team1": "", "1st_serve_points_won_team2": "",
                "2nd_serve_points_won_team1": "", "2nd_serve_points_won_team2": "",
                "total_serve_points_won_team1": "", "total_serve_points_won_team2": "",
                "returns_team1": "", "returns_team2": "",
                "returns_made_team1": "", "returns_made_team2": "",
                "1st_serve_return_points_won_team1": "", "1st_serve_return_points_won_team2": "",
                "2nd_serve_return_points_won_team1": "", "2nd_serve_return_points_won_team2": "",
                "total_return_points_won_team1": "", "total_return_points_won_team2": "",
                "break_points_won_team1": "", "break_points_won_team2": ""
            }
            
            stat_keys = list(stats.keys())
            j = 0
            
            # Same parsing logic as script_doubles.py (every 3 lines)
            for i in range(0, len(relevant_lines), 3):
                if j < len(stat_keys):
                    stats[stat_keys[j]] = relevant_lines[i].strip()
                    j += 1
                if j < len(stat_keys):
                    stats[stat_keys[j]] = relevant_lines[i + 2].strip()
                    j += 1
            
            return stats
            
        except Exception as e:
            print(f"          Error parsing doubles stats data: {e}")
            return {}
    
    def save_tournament_data(self, tournament_name):
        """Save all collected data as separate JSON files"""
        try:
            singles_filename = f"{tournament_name.replace(' ', '_')}_singles_stats.json"
            doubles_filename = f"{tournament_name.replace(' ', '_')}_doubles_stats.json"
            
            # Save singles data
            if self.all_singles_stats:
                singles_output = {
                    "tournament": tournament_name,
                    "total_matches": len(self.all_singles_stats),
                    "match_type": "Singles",
                    "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "matches": self.all_singles_stats
                }
                
                with open(singles_filename, 'w') as f:
                    json.dump(singles_output, f, indent=2)
                print(f"✅ Saved {len(self.all_singles_stats)} singles matches to {singles_filename}")
            
            # Save doubles data
            if self.all_doubles_stats:
                doubles_output = {
                    "tournament": tournament_name,
                    "total_matches": len(self.all_doubles_stats),
                    "match_type": "Doubles",
                    "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "matches": self.all_doubles_stats
                }
                
                with open(doubles_filename, 'w') as f:
                    json.dump(doubles_output, f, indent=2)
                print(f"✅ Saved {len(self.all_doubles_stats)} doubles matches to {doubles_filename}")
            
            total_matches = len(self.all_singles_stats) + len(self.all_doubles_stats)
            print(f"\n🎾 Tournament scraping complete! Total: {total_matches} matches ({len(self.all_singles_stats)} singles, {len(self.all_doubles_stats)} doubles)")
            
        except Exception as e:
            print(f"Error saving data: {e}")

    def test_navigation_only(self, tournament_url):
        """Test version - just test navigation up to teams"""
        try:
            self.start_driver()
            
            # First login to IONCourt
            if not self.login_to_ioncourt():
                print("Login failed - cannot proceed")
                return
            
            print(f"Testing navigation for: {tournament_url}")
            self.driver.get(tournament_url)
            time.sleep(3)
            
            # Extract tournament name from URL for file naming
            tournament_name = tournament_url.split('/')[-1].replace('-', ' ').title()
            print(f"Tournament: {tournament_name}")
            
            # Step 1: Click on "Teams" tab
            print("\n--- Testing Teams Tab Click ---")
            self.click_teams_tab()
            
            # Step 2: Get all team links
            print("\n--- Testing Team Links Extraction ---")
            team_links = self.get_team_links()
            print(f"\nFound {len(team_links)} teams:")
            for i, link in enumerate(team_links, 1):
                print(f"{i}. {link}")
            
            print(f"\n✅ Navigation test completed! Found {len(team_links)} teams")
            
        except Exception as e:
            print(f"Error in navigation test: {e}")
        finally:
            self.close_driver()

    def click_ioncourt_back_button(self):
        """Click IONCourt's built-in back button instead of browser back"""
        print("      Attempting to find IONCourt back button...")
        
        # First, let's see what's on the page
        current_url = self.driver.current_url
        print(f"      Current URL: {current_url}")
        
        try:
            # Try the simpler league page back button first
            print("      Trying simplified league page back button...")
            back_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/ion-app/ion-split-pane/ion-router-outlet/app-league-details/ion-header/ion-toolbar[1]/ion-buttons[1]/ion-back-button"))
            )
            back_button.click()
            time.sleep(2)
            print("      Used simplified league page back button")
            return True
        except Exception as e:
            print(f"      Simplified league page back button failed: {e}")
            
        try:
            # Try the tie page back button
            print("      Trying tie page back button...")
            back_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/ion-app/ion-split-pane/ion-router-outlet/app-tie-details/ion-header/ion-toolbar/div/div[1]/ion-buttons/ion-back-button"))
            )
            back_button.click()
            time.sleep(2)
            print("      Used tie page back button")
            return True
        except Exception as e:
            print(f"      Tie page back button failed: {e}")
            
        try:
            # Try the team page back button
            print("      Trying team page back button...")
            back_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/ion-app/ion-split-pane/ion-router-outlet/app-team-details/ion-header/ion-toolbar/ion-buttons[1]/ion-back-button"))
            )
            back_button.click()
            time.sleep(2)
            print("      Used team page back button")
            return True
        except Exception as e:
            print(f"      Team page back button failed: {e}")
            
        try:
            # Try just clicking any ion-back-button we can find
            print("      Trying generic ion-back-button...")
            back_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//ion-back-button"))
            )
            back_button.click()
            time.sleep(2)
            print("      Used generic ion-back-button")
            return True
        except Exception as e:
            print(f"      Generic ion-back-button failed: {e}")
            
        print(f"      All IONCourt back button attempts failed")
        return False

    def test_extended_navigation(self, tournament_url):
        """Extended test - test navigation through all teams and their matches"""
        try:
            self.start_driver()
            
            # First login to IONCourt
            if not self.login_to_ioncourt():
                print("Login failed - cannot proceed")
                return
            
            print(f"Testing extended navigation for: {tournament_url}")
            self.driver.get(tournament_url)
            time.sleep(3)
            
            # Extract tournament name from URL for file naming
            tournament_name = tournament_url.split('/')[-1].replace('-', ' ').title()
            print(f"Tournament: {tournament_name}")
            
            # Step 1: Click on "Teams" tab
            print("\n--- Testing Teams Tab Click ---")
            self.click_teams_tab()
            
            # Step 2: Get initial team count
            team_elements = self.driver.find_elements(By.XPATH, "//app-team-item/ion-item/ion-label")
            total_teams = len(team_elements)
            print(f"Found {total_teams} teams to test")
            
            all_match_data = {}  # Store all match data for summary
            
            for i in range(total_teams):
                try:
                    print(f"\n--- Testing Team {i+1}/{total_teams} ---")
                    
                    # Make sure we're on the teams page - go back to tournament and re-click teams
                    print(f"Going to tournament page to ensure fresh state...")
                    self.driver.get(tournament_url)
                    time.sleep(3)
                    self.click_teams_tab()
                    time.sleep(2)
                    
                    # Re-find team elements with fresh DOM
                    team_elements = self.driver.find_elements(By.XPATH, "//app-team-item/ion-item/ion-label")
                    
                    if i >= len(team_elements):
                        print(f"Team {i+1} no longer available, skipping")
                        continue
                        
                    team_element = team_elements[i]
                    
                    # Click on this team
                    team_element.click()
                    time.sleep(3)
                    
                    # Get team name
                    team_name = self.get_team_name()
                    print(f"Team: {team_name}")
                    
                    # Get all matches for this team
                    match_links = self.get_team_match_links()
                    print(f"Found {len(match_links)} matches for {team_name}")
                    
                    # Store match data
                    all_match_data[team_name] = match_links
                    
                    # Display match links for this team
                    for j, match_link in enumerate(match_links, 1):
                        print(f"  {j}. {match_link}")
                    
                    print(f"Completed processing {team_name}")
                    
                except Exception as e:
                    print(f"Error processing team {i+1}: {e}")
                    # Recovery: go back to tournament page
                    try:
                        print("Attempting to recover by going to tournament page...")
                        self.driver.get(tournament_url)
                        time.sleep(3)
                        self.click_teams_tab()
                        time.sleep(2)
                    except Exception as recovery_error:
                        print(f"Recovery failed: {recovery_error}")
                        break
                    continue
            
            # Summary
            print(f"\n{'='*50}")
            print(f"EXTENDED NAVIGATION TEST SUMMARY")
            print(f"{'='*50}")
            total_matches = 0
            for team_name, matches in all_match_data.items():
                print(f"{team_name}: {len(matches)} matches")
                total_matches += len(matches)
            print(f"\nTotal: {len(all_match_data)} teams, {total_matches} matches")
            print(f"✅ Extended navigation test completed!")
            
        except Exception as e:
            print(f"Error in extended navigation test: {e}")
        finally:
            self.close_driver()

    def get_match_api_data(self, match_url):
        """Extract basic match data using API (from script_singles.py logic)"""
        try:
            # Convert URL format - handle both URL formats: ties/match and live-scoring
            if "/ties/" in match_url and "/match/" in match_url:
                # Extract match ID from ties URL: /ties/xxx/match/MATCH_ID
                match_id = match_url.split("/match/")[-1]
                modified_url = f"https://api.ioncourt.com/api/match/{match_id}"
            else:
                # Fallback to original conversion method
                modified_url = match_url.replace("ioncourt.com/live-scoring", "api.ioncourt.com/api/match")
            
            page = requests.get(modified_url, headers=self.headers)
            match_data = page.json()
            
            if 'data' not in match_data:
                return None
                
            data = match_data['data']
            
            # Extract player info (from script_singles.py logic)
            sides = pd.json_normalize(data['sides'])
            p1_info = sides['players'][0][0]['participant']
            p2_info = sides['players'][1][0]['participant']
            
            # Extract scores (from script_singles.py logic)
            df_scores = pd.json_normalize(data['sets'])
            df_scores['score'] = df_scores.apply(lambda row: f"{row['side1Score']}-{row['side2Score']}", axis=1)
            scores_array = df_scores['score'].tolist()
            
            return {
                "date": data['startDate'][:10],
                "round": data.get('roundName', 'Unknown'),
                "player1_name": f"{p1_info['first_name']} {p1_info['last_name']}",
                "player2_name": f"{p2_info['first_name']} {p2_info['last_name']}",
                "scores": scores_array
            }
            
        except Exception as e:
            print(f"        Error getting API data: {e}")
            return None

    def get_individual_match_links(self):
        """Get individual match links from tie page - SIMPLIFIED since usually one match"""
        try:
            # Since it's usually one match per tie, just return the current tie URL
            # The actual match processing will happen in process_match_tie
            return [self.driver.current_url]
        except Exception as e:
            print(f"Error getting individual match links: {e}")
            return []

    def get_doubles_match_api_data(self, match_url):
        """Extract basic doubles match data using API (from script_doubles.py logic)"""
        try:
            # Convert URL format - handle both URL formats: ties/match and live-scoring
            if "/ties/" in match_url and "/match/" in match_url:
                # Extract match ID from ties URL: /ties/xxx/match/MATCH_ID
                match_id = match_url.split("/match/")[-1]
                modified_url = f"https://api.ioncourt.com/api/match/{match_id}"
            else:
                # Fallback to original conversion method
                modified_url = match_url.replace("ioncourt.com/live-scoring", "api.ioncourt.com/api/match")
            
            page = requests.get(modified_url, headers=self.headers)
            match_data = page.json()
            
            if 'data' not in match_data:
                return None
                
            data = match_data['data']
            
            # Extract player info for doubles (from script_doubles.py logic)
            sides = pd.json_normalize(data['sides'])
            
            # Team 1 players
            p1_info = sides['players'][0][0]['participant']
            p2_info = sides['players'][0][1]['participant']
            
            # Team 2 players
            p3_info = sides['players'][1][0]['participant']
            p4_info = sides['players'][1][1]['participant']
            
            # Extract scores (from script_doubles.py logic)
            df_scores = pd.json_normalize(data['sets'])
            df_scores['score'] = df_scores.apply(lambda row: f"{row['side1Score']}-{row['side2Score']}", axis=1)
            scores_array = df_scores['score'].tolist()
            
            return {
                "date": data['startDate'][:10],
                "round": data.get('roundName', 'Unknown'),
                "team1_player1": f"{p1_info['first_name']} {p1_info['last_name']}",
                "team1_player2": f"{p2_info['first_name']} {p2_info['last_name']}",
                "team2_player1": f"{p3_info['first_name']} {p3_info['last_name']}",
                "team2_player2": f"{p4_info['first_name']} {p4_info['last_name']}",
                "scores": scores_array
            }
            
        except Exception as e:
            print(f"        Error getting doubles API data: {e}")
            return None

# Usage
if __name__ == "__main__":
    tournament_url = input("Enter tournament URL (e.g., https://ioncourt.com/leagues/intennse-pro-league): ").strip()
    
    if not tournament_url:
        print("No URL provided")
        exit()
    
    scraper = IONCourtTournamentScraper()
    
    # Ask if user wants to test navigation only or run full scrape
    print("Choose test mode:")
    print("1. Basic navigation test (teams only)")
    print("2. Extended navigation test (teams + matches)")
    print("3. Full scrape")
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice == '1':
        scraper.test_navigation_only(tournament_url)
    elif choice == '2':
        scraper.test_extended_navigation(tournament_url)
    else:
        scraper.scrape_tournament(tournament_url) 
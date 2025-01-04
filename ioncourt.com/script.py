import requests
import pandas as pd
from curl_cffi import requests

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

# the link I personally used during testing 
# note, script probably won't work with doubles (slight modifications necessary)
#url_original = 'https://ioncourt.com/live-scoring/66f56802035c490337d02632'

# for now, user inputs link in format above..
url_original = input("Enter link: ")
modified_url = url_original.replace("ioncourt.com/live-scoring", "api.ioncourt.com/api/match")

headers = {"UserAgent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}
page = requests.get(modified_url, headers=headers)
match_data = page.json()

# normalize data 
match_data['data'].keys()
match_data = match_data['data']

# player 1 info 
p1_first_name = pd.json_normalize(match_data['sides'])['players'][0][0]['participant']['first_name']
p1_last_name = pd.json_normalize(match_data['sides'])['players'][0][0]['participant']['last_name']
p1_full_name = p1_first_name + " " + p1_last_name

# player 2 info 
p2_first_name = pd.json_normalize(match_data['sides'])['players'][1][0]['participant']['first_name']
p2_last_name = pd.json_normalize(match_data['sides'])['players'][1][0]['participant']['last_name']
p2_full_name = p2_first_name + " " + p2_last_name

# puts scores in #-# format 
df_scores = pd.json_normalize(match_data['sets'])
df_scores['score'] = df_scores.apply(lambda row: f"{row['side1Score']}-{row['side2Score']}", axis=1)

# converts the dataframe to a singular list 
scores_array = df_scores['score'].tolist()

# round info 
round_ofmatch = match_data['roundName']
round_num = match_data['roundNumber']

#reformat start date:
unformatted_date = match_data['startDate']
start_date = unformatted_date[:10]


# tournament id conversion to tournmanent name using Selenium script 
tournament_id = match_data['tournament']
tournament_url = f'https://ioncourt.com/tournaments/{tournament_id}/live-score'

# selenium script to get tournament name 

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

url = tournament_url
driver = webdriver.Chrome()

try:
    driver.get(tournament_url)

    time.sleep(3) # it doesn't work for some reason if i don't put have a sleep here 

    # locate tournament title name via XPATH
    tournament_label = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="content"]/app-tournament-details/ion-tabs/div/ion-router-outlet/app-live-score/app-tournament-header/ion-header/ion-toolbar[1]/ion-item/ion-label')
        )
    )
    # takes the text of the element's XPATH 
    tournament_name = tournament_label.text.strip()

finally:
    driver.quit()

match_info = {
    "Date": [start_date],
    "Round": [round_ofmatch], 
    "Player 1": [p1_full_name],  
    "Player 2": [p2_full_name],  
    "Score": [scores_array],  
    "Tournament": [tournament_name],  
}

# convert match_info dict to a dataframe 
df_match = pd.DataFrame(match_info)






# Selenium script for stats info 

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    driver = webdriver.Chrome()

    url = url_original
    driver.get(url)

    # click site's "STATS" button by locating via element's XPATH 
    stats_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@value='stats']"))
    )

    stats_button.click()

    # get the text info associated with the stats section 
    stats_grid = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="content"]/app-match-tracker/ion-content/div[3]/app-stats/ion-grid'))
    )

    raw_data = stats_grid.text 

except Exception as e:
    print("Error occurred:", e)

finally:
    driver.quit()

# Format the stats info

player1_stats = {}
player2_stats = {}

lines = raw_data.strip().splitlines()

start_index = 33
relevant_lines = lines[start_index:]

stats = {
    "aces_player1": "",
    "aces_player2": "",
    "double_faults_player1": "",
    "double_faults_player2": "",
    "1st_serve_percentage_player1": "",
    "1st_serve_percentage_player2": "",
    "1st_serve_points_won_player1": "",
    "1st_serve_points_won_player2": "",
    "2nd_serve_points_won_player1": "",
    "2nd_serve_points_won_player2": "",
    "total_serve_points_won_player1": "",
    "total_serve_points_won_player2": "",
    "returns_player1": "",
    "returns_player2": "",
    "returns_made_player1": "",
    "returns_made_player2": "",
    "1st_serve_return_points_won_player1": "",
    "1st_serve_return_points_won_player2": "",
    "2nd_serve_return_points_won_player1": "",
    "2nd_serve_return_points_won_player2": "",
    "total_return_points_won_player1": "",
    "total_return_points_won_player2": "",
    "break_points_won_player1": "",
    "break_points_won_player2": "",
    
    
}

stat_keys = [
    "aces_player1",
    "aces_player2",
    "double_faults_player1",
    "double_faults_player2",
    "1st_serve_percentage_player1",
    "1st_serve_percentage_player2",
    "1st_serve_points_won_player1",
    "1st_serve_points_won_player2",
    "2nd_serve_points_won_player1",
    "2nd_serve_points_won_player2",
    "total_serve_points_won_player1",
    "total_serve_points_won_player2",
    "returns_player1",
    "returns_player2",
    "returns_made_player1",
    "returns_made_player2",
    "1st_serve_return_points_won_player1",
    "1st_serve_return_points_won_player2",
    "2nd_serve_return_points_won_player1",
    "2nd_serve_return_points_won_player2",
    "total_return_points_won_player1",
    "total_return_points_won_player2",
    "break_points_won_player1",
    "break_points_won_player2",
]

j = 0

for i in range(0, len(relevant_lines), 3): 
    if j < len(stat_keys):  
        stats[stat_keys[j]] = relevant_lines[i].strip()  
        j += 1
    if j < len(stat_keys): 
        stats[stat_keys[j]] = relevant_lines[i + 2].strip()
        j += 1

# convert dict to dataframe, drop irrelevant column 
df_stats = pd.DataFrame([stats])
df_stats = df_stats.drop(columns=["returns_player1", "returns_player2"])

# combine the two dataframes
df_final = pd.concat([df_match, df_stats], ignore_index=False, axis = 1)

# convert match completed info into a csv
# this works for one match
df_final.to_csv('~/Downloads/final_test7.csv', index=False)







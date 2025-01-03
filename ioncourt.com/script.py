import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from curl_cffi import requests as cureq 

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)


# pass in a url, then modify it for the scraper
# compile a list of urls, then just do the change, or do it according to user input?

# idea should be maybe to have user input be url_original..
url_original = 'https://ioncourt.com/live-scoring/66f56802035c490337d02632'
modified_url = url_original.replace("ioncourt.com/live-scoring", "api.ioncourt.com/api/match")

headers = {"UserAgent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}
page = requests.get(modified_url, headers=headers)

### everything below is this copied from notebook, will require changes

match_data = page.json()
df = pd.json_normalize(match_data)

match_data['data'].keys()
match_data = match_data['data']

pd.json_normalize(match_data)
pd.json_normalize(match_data['sides'])['players']
pd.json_normalize(match_data['sides'])['players'][0]

p1_first_name = pd.json_normalize(match_data['sides'])['players'][0][0]['participant']['first_name']
p1_last_name = pd.json_normalize(match_data['sides'])['players'][0][0]['participant']['last_name']
p1_full_name = p1_first_name + " " + p1_last_name

p2_first_name = pd.json_normalize(match_data['sides'])['players'][1][0]['participant']['first_name']
p2_last_name = pd.json_normalize(match_data['sides'])['players'][1][0]['participant']['last_name']
p2_full_name = p2_first_name + " " + p2_last_name

pd.json_normalize(match_data['sets'])
pd.json_normalize(pd.json_normalize(match_data['sets'])['games'][0])
pd.json_normalize(pd.json_normalize(pd.json_normalize(match_data['sets'])['games'][0])['points'][0])


# my code:

# puts scores in #-# format 
df_scores = pd.json_normalize(match_data['sets'])
df_scores['score'] = df_scores.apply(lambda row: f"{row['side1Score']}-{row['side2Score']}", axis=1)

# makes scores an array 
scores_array = df_scores['score'].tolist()

round_ofmatch = match_data['roundName']

round_num = match_data['roundNumber']

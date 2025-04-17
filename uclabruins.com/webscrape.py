import requests
import json
import pandas as pd
from collections import defaultdict

api_url = "https://uclabruins.com/api/v2/EventsResults/results?sportId=21&$pageIndex=0&$pageSize=50"
response = requests.get(api_url)

bsurllist = []
box_score_api_urls = []

if response.status_code == 200:
    data = response.json()

    for game in data["items"]:
        date = game.get("date", "No date available")
        location = game.get("location", "No location available")
        opponent = game.get("opponent", {}).get("title", "No opponent title available")

        result = game.get("result", {})
        boxScore = result.get("boxScore", None) if isinstance(result, dict) else None

        if boxScore:
            if boxScore.startswith("/"):
                boxScore = "https://uclabruins.com/api/v2/Stats/boxscore/" + boxScore.split("=")[-1]
            bsurllist.append(boxScore)  
else:
    print(f"Error: Unable to fetch data (Status Code: {response.status_code})")

box_score_api_urls = [url for url in bsurllist if url]

player_stats = []
all_match_data = [] 

for url in box_score_api_urls:
    try:
        response = requests.get(url, timeout=10) 
        response.raise_for_status() 
        data1 = response.json() 

    except requests.exceptions.RequestException as e:
        continue 

    games1 = data1.get("singles", [])
    if not games1:
        continue 

    matches = {
        "1": [],
        "2": [],
        "3": [],
        "4": [],
        "5": [],
        "6": []
    }

    for game1 in games1:
        match_num = game1.get("matchNum", "").strip()
        if match_num not in matches:
            continue

        player_info = {
            "date": game1.get("date"),
            "name1": game1.get("name1", "Unknown"),
            "team": game1.get("team", ""),
            "gamestatus": game1.get("isWinner", ""),
            "setlist": [
                game1.get("set1"),
                game1.get("set2"),
                game1.get("set3"),
                game1.get("set4"),
                game1.get("set5"),
            ]
        }

        matches[match_num].append(player_info)

    for match_num, players in matches.items():
        for player in players:
            all_match_data.append({
                "Date": date,
                "Match": match_num,
                "Player": player["name1"],
                "Team": player["team"],
                "Set 1": player["setlist"][0] if player["setlist"][0] else "",
                "Set 2": player["setlist"][1] if player["setlist"][1] else "",
                "Set 3": player["setlist"][2] if player["setlist"][2] else "",
                "Set 4": player["setlist"][3] if player["setlist"][3] else "",
                "Set 5": player["setlist"][4] if player["setlist"][4] else "",
                "Game Status": player["gamestatus"]
            })

df = pd.DataFrame(all_match_data)
df.to_csv('tennis_matches.csv', index=False)
print("Data exported to 'tennis_matches.csv'")
df = pd.json_normalize(all_match_data)
print(df)
# import streamlit as st
from nba_api.stats.endpoints import playercareerstats, leaguegamefinder
from nba_api.live.nba.endpoints import scoreboard
from requests.exceptions import ReadTimeout, TooManyRedirects, ConnectionError
import time
from functools import partial
import pandas as pd
import numpy as np

def get_live_games():
    board = scoreboard.ScoreBoard()
    games = board.games.get_dict()
    df = pd.DataFrame(games)

    # Select and rename the desired columns
    df_filtered = df[['gameId', 'gameStatusText', 'gameEt']].copy()
    df_filtered['homeTeamId'] = df['homeTeam'].apply(lambda x: x['teamId'])
    df_filtered['homeTeamName'] = df['homeTeam'].apply(lambda x: x['teamName'])
    df_filtered['homeTeamScore'] = df['homeTeam'].apply(lambda x: x['score'])
    df_filtered['awayTeamId'] = df['awayTeam'].apply(lambda x: x['teamId'])
    df_filtered['awayTeamName'] = df['awayTeam'].apply(lambda x: x['teamName'])
    df_filtered['awayTeamScore'] = df['awayTeam'].apply(lambda x: x['score'])

    # Add winning team column
    df_filtered['winningTeam'] = df_filtered.apply(
        lambda row: row['homeTeamName'] if row['homeTeamScore'] > row['awayTeamScore']
        else (row['awayTeamName'] if row['awayTeamScore'] > row['homeTeamScore']
            else 'Tie' if row['gameStatusText'] == 'Final' else 'Undefined'),
        axis=1
    )
    
    # Extract the date from gameEt and rename it gameDate
    df_filtered['gameEt'] = pd.to_datetime(df_filtered['gameEt'])
    df_filtered.rename(columns={'gameEt': 'gameDate'}, inplace=True)

    return df_filtered

def get_past_games():
    # Fetch the data
    league_game_finder = leaguegamefinder.LeagueGameFinder(league_id_nullable='00', season_nullable='2024-25')
    games = league_game_finder.get_data_frames()[0]

    # Function to get the last word (nickname) of the team name
    def get_team_nickname(full_name):
        return full_name.split()[-1]

    # Create separate dataframes for home and away teams
    home_games = games[games['MATCHUP'].str.contains('vs.')].copy()
    away_games = games[games['MATCHUP'].str.contains('@')].copy()

    # Rename columns and extract team nicknames
    home_games = home_games.rename(columns={
        'TEAM_ID': 'homeTeamId',
        'TEAM_NAME': 'homeTeamName',
        'PTS': 'homeTeamScore'
    })
    home_games['homeTeamName'] = home_games['homeTeamName'].apply(get_team_nickname)

    away_games = away_games.rename(columns={
        'TEAM_ID': 'awayTeamId',
        'TEAM_NAME': 'awayTeamName',
        'PTS': 'awayTeamScore'
    })
    away_games['awayTeamName'] = away_games['awayTeamName'].apply(get_team_nickname)

    # Merge home and away games on GAME_ID
    merged_games = pd.merge(
        home_games[['GAME_ID', 'GAME_DATE', 'homeTeamId', 'homeTeamName', 'homeTeamScore']],
        away_games[['GAME_ID', 'awayTeamId', 'awayTeamName', 'awayTeamScore']],
        on='GAME_ID'
    )

    # Determine the winning team
    merged_games['winningTeam'] = np.where(
        merged_games['homeTeamScore'] > merged_games['awayTeamScore'],
        merged_games['homeTeamName'],
        merged_games['awayTeamName']
    )

    # Rename remaining columns and reorder
    final_df = merged_games.rename(columns={
        'GAME_ID': 'gameId',
        'GAME_DATE': 'gameDate'
    })

    # Add a placeholder for gameStatusText
    final_df['gameStatusText'] = 'Final'  # Placeholder

    # Reorder columns
    final_df = final_df[[
        'gameId', 'gameStatusText', 'gameDate',
        'homeTeamId', 'homeTeamName', 'homeTeamScore',
        'awayTeamId', 'awayTeamName', 'awayTeamScore',
        'winningTeam'
    ]]

    # Display the result
    return final_df

def get_game_by_date(selected_date):
    df = get_past_games()
    # Filter for the selected date
    final_df = df[df['gameDate'].str.startswith(selected_date.strftime('%Y-%m-%d'))]
    return final_df

def get_game_by_id(game_id):
    df = get_past_games()
    final_df = df[df['gameId'] == game_id]
    return final_df


def calculate_win_probability(elo_a, elo_b):
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

def probability_to_odds(probability):
    return 1 / probability

# @st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_data(endpoint, **kwargs):
    max_retries = 5
    base_delay = 3  # seconds
    
    for i in range(max_retries):
        try:
            # Increase timeout to 60 seconds
            endpoint_with_timeout = partial(endpoint, timeout=60)
            return endpoint_with_timeout(**kwargs).get_data_frames()[0]
        except (ReadTimeout, ConnectionError, TooManyRedirects) as e:
            if i < max_retries - 1:
                delay = base_delay * (2 ** i)  # Exponential backoff
                print(f"Request failed, retrying in {delay} seconds... (Attempt {i+1}/{max_retries})")
                time.sleep(delay)
            else:
                print(f"Failed to fetch data after {max_retries} attempts. Please try again later.")
                return None

# @st.cache_data(ttl=86400)  # Cache player stats for 24 hours
def fetch_player_stats(player_id):
    return fetch_data(playercareerstats.PlayerCareerStats, player_id=player_id)

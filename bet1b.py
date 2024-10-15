# app.py

import streamlit as st
import pandas as pd
from datetime import datetime

# Sample NBA games data
def get_mock_games():
    data = {
        'Game ID': [1, 2, 3, 4, 5],
        'Date': [
            '2023-11-01',
            '2023-11-02',
            '2023-11-03',
            '2023-11-04',
            '2023-11-05'
        ],
        'Home Team': ['Lakers', 'Warriors', 'Nets', 'Bucks', 'Celtics'],
        'Away Team': ['Heat', 'Nuggets', 'Knicks', 'Thunder', 'Pacers'],
        'Home Odds': [1.8, 2.0, 1.5, 1.9, 1.7],
        'Away Odds': [2.0, 1.9, 2.2, 2.0, 2.1]
    }
    return pd.DataFrame(data)

# Initialize session state for bets
if 'bets' not in st.session_state:
    st.session_state['bets'] = []

# App Title
st.title("🏀 NBA Betting App")

# Display Upcoming Games
st.header("Upcoming NBA Matches")

games = get_mock_games()
st.write(games[['Date', 'Home Team', 'Away Team', 'Home Odds', 'Away Odds']].rename(columns={
    'Home Team': 'Home Team',
    'Away Team': 'Away Team',
    'Home Odds': 'Home Team Odds',
    'Away Odds': 'Away Team Odds'
}))

# Select a Game to Bet On
st.subheader("Place a Bet")

game_id = st.selectbox("Select Game", games['Game ID'])

selected_game = games[games['Game ID'] == game_id].iloc[0]
home_team = selected_game['Home Team']
away_team = selected_game['Away Team']
home_odds = selected_game['Home Odds']
away_odds = selected_game['Away Odds']

stake = st.number_input("Enter your stake ($)", min_value=1.0, step=1.0)

team_choice = st.radio(
    "Choose a team to bet on:",
    (f"{home_team} (Odds: {home_odds})", f"{away_team} (Odds: {away_odds})")
)

if st.button("Place Bet"):
    bet = {
        'Date': selected_game['Date'],
        'Home Team': home_team,
        'Away Team': away_team,
        'Chosen Team': team_choice.split(" (")[0],
        'Odds': home_odds if 'Home' in team_choice else away_odds,
        'Stake': stake,
        'Potential Payout': stake * (home_odds if 'Home' in team_choice else away_odds)
    }
    st.session_state['bets'].append(bet)
    st.success("Bet placed successfully!")

# Display Betting History
st.header("Your Bets")

if st.session_state['bets']:
    bets_df = pd.DataFrame(st.session_state['bets'])
    st.table(bets_df)
else:
    st.info("You haven't placed any bets yet.")

# Optional: Reset Bets
if st.button("Reset Betting History"):
    st.session_state['bets'] = []
    st.success("Betting history has been reset.")


# app.py

import streamlit as st
import pandas as pd
from nba_api.live.nba.endpoints import scoreboard
from datetime import datetime

# Fetch today's NBA games
def get_today_games():
    today = datetime.now().date()
    date_str = today.strftime("%Y-%m-%d")
    
    board = scoreboard.ScoreBoard()
    games_today = board.games.get_dict()
    
    games = []
    for game in games_today:
        game_info = {
            'Game ID': game['gameId'],
            'Date': date_str,
            'Home Team': game['homeTeam']['teamName'],
            'Away Team': game['awayTeam']['teamName'],
            'Home Odds': 2.0,  # Placeholder odds
            'Away Odds': 2.0,  # Placeholder odds
        }
        games.append(game_info)
    
    return pd.DataFrame(games)

# Initialize session state for bets
if 'bets' not in st.session_state:
    st.session_state['bets'] = []

# App Title
st.title("🏀 NBA Betting App")

# Display Today's Games
st.header("Today's NBA Matches")

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def load_games():
    return get_today_games()

games = load_games()

if games.empty:
    st.info("There are no NBA games scheduled for today.")
else:
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

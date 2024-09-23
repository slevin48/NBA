import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder, playergamelog
from nba_api.stats.static import teams, players

# Fetch real NBA data
def get_recent_games(team_id, num_games=10):
    gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
    games = gamefinder.get_data_frames()[0]
    return games.head(num_games)

def get_player_stats(player_id, player_name, season='2022-23'):
    player_stats = playergamelog.PlayerGameLog(player_id=player_id, season=season)
    df = player_stats.get_data_frames()[0]
    df['Player'] = player_name
    return df

# Get team IDs
nba_teams = teams.get_teams()
team_dict = {team['full_name']: team['id'] for team in nba_teams}

# Fetch recent games for Lakers and Warriors
lakers_games = get_recent_games(team_dict['Los Angeles Lakers'])
warriors_games = get_recent_games(team_dict['Golden State Warriors'])

# Combine and process game data
df_games = pd.concat([lakers_games, warriors_games])
df_games = df_games[['TEAM_NAME', 'MATCHUP', 'PTS', 'GAME_DATE', 'WL']]
df_games.columns = ['Team', 'Matchup', 'Team Score', 'Date', 'Result']
df_games['Opponent'] = df_games['Matchup'].apply(lambda x: x.split()[-1])

def get_opponent_score(row, df):
    if row['Result'] == 'L':
        return row['Team Score']
    else:
        opponent_game = df[(df['Date'] == row['Date']) & (df['Team'] != row['Team'])]
        return opponent_game['Team Score'].values[0] if not opponent_game.empty else None

df_games['Opponent Score'] = df_games.apply(lambda row: get_opponent_score(row, df_games), axis=1)

# Remove rows with missing opponent scores
df_games = df_games.dropna(subset=['Opponent Score'])

# Fetch player stats for LeBron James, Anthony Davis, Stephen Curry, and Klay Thompson
player_ids = {
    'LeBron James': '2544',
    'Anthony Davis': '203076',
    'Stephen Curry': '201939',
    'Klay Thompson': '202691'
}

df_players = pd.concat([get_player_stats(player_id, player_name) for player_name, player_id in player_ids.items()])
df_players = df_players[['Player', 'GAME_DATE', 'PTS']]
df_players.columns = ['Player', 'Date', 'Player Score']

# Sort the DataFrame by date and reset the index
df_players['Date'] = pd.to_datetime(df_players['Date'])
df_players = df_players.sort_values('Date', ascending=False).reset_index(drop=True)

# Streamlit app
st.title('Basketball Betting App 🏀')
st.write('Bet on your favorite basketball games and view past game stats and player scores.')
# Create a sidebar for navigation
page = st.sidebar.radio('Navigate', ['Past Game Stats 📊', 'Player Scores 🏅', 'Place Your Bet 💰'])

if page == 'Past Game Stats 📊':
    st.header('Past Game Stats 📊')
    st.dataframe(df_games)

elif page == 'Player Scores 🏅':
    st.header('Player Scores 🏅')
    st.dataframe(df_players)

elif page == 'Place Your Bet 💰':
    st.header('Place Your Bet 💰')
    team = st.selectbox('Select Team', df_games['Team'].unique())
    opponent = st.selectbox('Select Opponent', df_games['Opponent'].unique())
    bet_amount = st.number_input('Bet Amount ($)', min_value=0, step=1)

    if st.button('Place Bet'):
        st.write(f'You placed a bet of ${bet_amount} on {team} against {opponent}.')
        st.balloons()


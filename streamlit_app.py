import streamlit as st
from nba_api.stats.endpoints import scoreboard, teamdetails, commonplayerinfo, teamyearbyyearstats, commonteamroster, playercareerstats
from nba_api.stats.static import teams, players
import requests
from requests.exceptions import TooManyRedirects
import time
import pandas as pd

st.set_page_config(page_title="NBA Data App", page_icon="🏀")

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_data(endpoint, **kwargs):
    max_retries = 3
    for i in range(max_retries):
        try:
            return endpoint(**kwargs).get_data_frames()[0]
        except TooManyRedirects:
            if i < max_retries - 1:
                st.warning(f"Too many redirects, retrying in 5 seconds... (Attempt {i+1}/{max_retries})")
                time.sleep(5)
            else:
                st.error("Failed to fetch data after multiple attempts. Please try again later.")
                return None

def main():
    st.title("NBA Data App")

    menu = ["Teams", "Players"]
    choice = st.sidebar.selectbox("Menu", menu)
    display_stat_legend()

    if choice == "Teams":
        show_teams()
    elif choice == "Players":
        show_players()

def show_todays_games():
    st.header("Today's Games")
    games = fetch_data(scoreboard.Scoreboard)
    if games is not None:
        for game in games.itertuples():
            st.write(f"{game.GAME_STATUS_TEXT}: {game.HOME_TEAM_CITY} {game.HOME_TEAM_NICKNAME} vs {game.VISITOR_TEAM_CITY} {game.VISITOR_TEAM_NICKNAME}")

def show_teams():
    st.header("NBA Teams")
    all_teams = teams.get_teams()
    team_names = [team['full_name'] for team in all_teams]
    selected_team = st.selectbox("Select a team", team_names)

    if selected_team:
        team = next(team for team in all_teams if team['full_name'] == selected_team)
        team_id = team['id']
        team_info = fetch_data(teamdetails.TeamDetails, team_id=team_id)
        team_stats = fetch_data(teamyearbyyearstats.TeamYearByYearStats, team_id=team_id)
        
        if team_info is not None and team_stats is not None:
            st.subheader(f"{team['full_name']} ({team['abbreviation']})")
            
            # Create two columns for layout
            col1, col2 = st.columns(2)
            
            with col1:
                st.image(f"https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg", width=200)
                st.metric("Year Founded", team_info.YEARFOUNDED.iloc[0])
                # st.metric("Arena Capacity", f"{team_info.ARENACAPACITY.iloc[0]:,}")

            with col2:
                st.subheader("Team Information")
                st.write(f"**City:** {team_info.CITY.iloc[0]}")
                st.write(f"**Arena:** {team_info.ARENA.iloc[0]}")
                st.write(f"**Owner:** {team_info.OWNER.iloc[0]}")
                st.write(f"**General Manager:** {team_info.GENERALMANAGER.iloc[0]}")
                st.write(f"**Head Coach:** {team_info.HEADCOACH.iloc[0]}")
                st.write(f"**D-League Affiliation:** {team_info.DLEAGUEAFFILIATION.iloc[0]}")

            # Team stats
            st.subheader("Current Season Stats")
            current_season_stats = team_stats.iloc[-1]  # Get the most recent season's stats
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if 'WINS' in current_season_stats:
                    st.metric("Wins", current_season_stats.WINS)
                if 'LOSSES' in current_season_stats:
                    st.metric("Losses", current_season_stats.LOSSES)
            with col2:
                if 'WIN_PCT' in current_season_stats:
                    st.metric("Win Percentage", f"{current_season_stats.WIN_PCT:.3f}")
                if 'CONF_RANK' in current_season_stats:
                    st.metric("Conference Rank", current_season_stats.CONF_RANK)
            with col3:
                if 'PTS' in current_season_stats:
                    st.metric("PTS/G", f"{current_season_stats.PTS:.1f}")
                if 'AST' in current_season_stats:
                    st.metric("AST/G", f"{current_season_stats.AST:.1f}")
            with col4:
                if 'REB' in current_season_stats:
                    st.metric("REB/G", f"{current_season_stats.REB:.1f}")
                # Check for different possible column names for point differential
                if 'PLUS_MINUS' in current_season_stats:
                    st.metric("DIFF", f"{current_season_stats.PLUS_MINUS:.1f}")
                elif 'POINT_DIFF' in current_season_stats:
                    st.metric("DIFF", f"{current_season_stats.POINT_DIFF:.1f}")
                elif 'DIFF' in current_season_stats:
                    st.metric("DIFF", f"{current_season_stats.DIFF:.1f}")

            # # Display all available columns for debugging
            # st.subheader("All Available Stats")
            # for col in current_season_stats.index:
            #     st.write(f"{col}: {current_season_stats[col]}")

            # Historical performance chart
            st.subheader("Historical Performance")
            if 'YEAR' in team_stats.columns and 'WIN_PCT' in team_stats.columns:
                chart_data = team_stats[['YEAR', 'WIN_PCT']]
                st.line_chart(chart_data.set_index('YEAR'))
            else:
                st.write("Historical data not available")

            # Current Season Roster
            st.subheader("Current Season Roster")
            roster = fetch_data(commonteamroster.CommonTeamRoster, team_id=team_id)
            if roster is not None and not roster.empty:
                # Initialize an empty list to store player data
                player_data_list = []

                # Iterate through each player in the roster
                for _, player in roster.iterrows():
                    player_id = player['PLAYER_ID']
                    player_stats = fetch_data(playercareerstats.PlayerCareerStats, player_id=player_id)
                    
                    if player_stats is not None and not player_stats.empty:
                        # Get the most recent season's stats
                        current_season_stats = player_stats.iloc[-1]
                        
                        player_data_list.append({
                            'Name': player['PLAYER'],
                            'Number': player['NUM'],
                            'Position': player['POSITION'],
                            'PPG': round(current_season_stats['PTS'] / current_season_stats['GP'], 1) if current_season_stats['GP'] > 0 else 0,
                            'APG': round(current_season_stats['AST'] / current_season_stats['GP'], 1) if current_season_stats['GP'] > 0 else 0,
                            'RPG': round(current_season_stats['REB'] / current_season_stats['GP'], 1) if current_season_stats['GP'] > 0 else 0,
                            'SPG': round(current_season_stats['STL'] / current_season_stats['GP'], 1) if current_season_stats['GP'] > 0 else 0,
                            'BPG': round(current_season_stats['BLK'] / current_season_stats['GP'], 1) if current_season_stats['GP'] > 0 else 0,
                        })

                # Create a DataFrame from the player data list
                player_data = pd.DataFrame(player_data_list)

                # Display the roster as a table
                st.dataframe(player_data, hide_index=True)
            else:
                st.write("Roster data not available")

def display_stat_legend():
    st.sidebar.subheader("Stat Legend")
    legend = {
        "PPG": "Points Per Game",
        "APG": "Assists Per Game",
        "RPG": "Rebounds Per Game",
        "SPG": "Steals Per Game",
        "BPG": "Blocks Per Game"
    }
    for acronym, explanation in legend.items():
        st.sidebar.text(f"{acronym}: {explanation}")

def show_players():
    st.header("NBA Players")
    all_players = players.get_active_players()
    player_names = [f"{player['first_name']} {player['last_name']}" for player in all_players]
    selected_player = st.selectbox("Select a player", player_names)

    if selected_player:
        player = next(player for player in all_players if f"{player['first_name']} {player['last_name']}" == selected_player)
        player_id = player['id']
        player_info = fetch_data(commonplayerinfo.CommonPlayerInfo, player_id=player_id)
        
        if player_info is not None:
            st.subheader(f"{player['first_name']} {player['last_name']}")
            st.write(f"Team: {player_info.TEAM_NAME.iloc[0]}")
            st.write(f"Position: {player_info.POSITION.iloc[0]}")
            st.write(f"Height: {player_info.HEIGHT.iloc[0]}")
            st.write(f"Weight: {player_info.WEIGHT.iloc[0]}")
            st.write(f"Country: {player_info.COUNTRY.iloc[0]}")

if __name__ == "__main__":
    main()

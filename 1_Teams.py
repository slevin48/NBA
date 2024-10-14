import streamlit as st
from nba_api.stats.static import teams
from nba_api.stats.endpoints import teamdetails, teamyearbyyearstats, commonteamroster, teamgamelog
from utils import fetch_data, fetch_player_stats
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="NBA Teams", 
    layout="wide",
    page_icon="🏀"
)

def show_teams():
    st.title("NBA Teams")
    
    all_teams = teams.get_teams()
    team_names = [team['full_name'] for team in all_teams]
    
    # Get the current query parameters
    params = st.query_params
    
    # Check if there's a team_id in the query parameters
    default_team = None
    if "team_id" in params:
        team_id = params["team_id"]
        default_team = next((team['full_name'] for team in all_teams if str(team['id']) == team_id), None)
    
    # Use session state to store the selected team
    if 'selected_team' not in st.session_state:
        st.session_state.selected_team = default_team or team_names[0]
    
    # Create the selectbox with the default value
    selected_team = st.selectbox(
        "Select a team", 
        team_names, 
        index=team_names.index(st.session_state.selected_team)
    )
    
    # Update session state and query params if a new team is selected
    if selected_team != st.session_state.selected_team:
        st.session_state.selected_team = selected_team
        team = next((team for team in all_teams if team['full_name'] == selected_team), None)
        st.query_params["team_id"] = str(team['id'])
        st.rerun()
    
    if selected_team:
        team = next(team for team in all_teams if team['full_name'] == selected_team)
        team_id = team['id']
        
        team_info = fetch_data(teamdetails.TeamDetails, team_id=team_id)
        team_stats = fetch_data(teamyearbyyearstats.TeamYearByYearStats, team_id=team_id)
        
        if team_info is None or team_stats is None:
            st.error("Unable to fetch team data. Please try again later.")
            return

        with st.sidebar:
            nba_stats_url = f"https://www.nba.com/stats/team/{team_id}"
            st.markdown(f"## [{team['full_name']} ({team['abbreviation']})]({nba_stats_url})")
            st.image(f"https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg", width=200)
        
            st.subheader("Current Season Stats")
            current_season_stats = team_stats.iloc[-1]
            
            if {'WINS', 'LOSSES', 'CONF_RANK'}.issubset(current_season_stats):
                st.text(f"Wins: {current_season_stats.WINS}, Losses: {current_season_stats.LOSSES}, Rank: {current_season_stats.CONF_RANK}")
            
            with st.expander("More Stats"):
                for stat in ['WIN_PCT', 'PTS', 'AST', 'REB', 'PLUS_MINUS']:
                    if stat in current_season_stats:
                        st.metric(stat, f"{current_season_stats[stat]:.1f}")

            with st.expander("Team Information"):
                st.metric("Year Founded", team_info.YEARFOUNDED.iloc[0])
                for info in ['CITY', 'ARENA', 'OWNER', 'GENERALMANAGER', 'HEADCOACH', 'DLEAGUEAFFILIATION']:
                    st.write(f"**{info.title()}:** {team_info[info].iloc[0]}")

        st.subheader("Current Season Roster")
        st.write("Player statistics are averaged per game for the current season.")
        roster = fetch_data(commonteamroster.CommonTeamRoster, team_id=team_id)
        if roster is not None and not roster.empty:
            player_data_list = []
            for _, player in roster.iterrows():
                player_id = player['PLAYER_ID']
                player_stats = fetch_player_stats(player_id)
                
                if player_stats is not None and not player_stats.empty:
                    current_season_stats = player_stats.iloc[-1]
                    
                    player_data_list.append({
                        'Name': player['PLAYER'],
                        'Number': player['NUM'],
                        'Position': player['POSITION'],
                        'Points': round(current_season_stats['PTS'] / current_season_stats['GP'], 1) if current_season_stats['GP'] > 0 else 0,
                        'Assists': round(current_season_stats['AST'] / current_season_stats['GP'], 1) if current_season_stats['GP'] > 0 else 0,
                        'Rebounds': round(current_season_stats['REB'] / current_season_stats['GP'], 1) if current_season_stats['GP'] > 0 else 0,
                    })

            player_data = pd.DataFrame(player_data_list)
            st.dataframe(player_data, hide_index=True)
        else:
            st.write("Roster data not available")
        # Toggle for Historical Performance
        show_historical = st.sidebar.toggle("Show Historical Performance", value=False)

        if show_historical:
            # Historical performance chart
            st.subheader("Historical Performance")
            if 'YEAR' in team_stats.columns and 'WIN_PCT' in team_stats.columns:
                fig = px.line(team_stats, x='YEAR', y='WIN_PCT', title='Win Percentage Over Years')
                fig.update_layout(xaxis_title='Year', yaxis_title='Win Percentage')
                st.plotly_chart(fig)
            else:
                st.write("Historical data not available")

        def display_season_games(season):
            game_log = fetch_data(teamgamelog.TeamGameLog, team_id=team_id, season=season)
            
            if game_log is not None and not game_log.empty:
                st.subheader(f"Games for the {season}-{season+1} Season")
                # Convert GAME_DATE to datetime
                game_log['GAME_DATE'] = pd.to_datetime(game_log['GAME_DATE'])
                
                # Sort games by date (most recent first)
                game_log = game_log.sort_values('GAME_DATE', ascending=False)
                
                # Prepare data for display
                games_display = game_log[['GAME_DATE', 'MATCHUP', 'WL', 'PTS', 'Game_ID']].copy()
                games_display['GAME_DATE'] = games_display['GAME_DATE'].dt.strftime('%Y-%m-%d')
                
                # Extract opponent name and score from MATCHUP
                def extract_opponent_and_score(matchup):
                    parts = matchup.split()
                    opponent = parts[2] if parts[1] in ['vs.', '@'] else parts[1]
                    score = parts[-1]
                    return pd.Series([opponent, score])

                games_display[['OPPONENT', 'OPP_SCORE']] = games_display['MATCHUP'].apply(extract_opponent_and_score)
                
                # Create a score column
                games_display['SCORE'] = games_display.apply(lambda row: f"{row['PTS']} - {row['OPP_SCORE']}", axis=1)
                
                # Create NBA game link
                def create_game_link(row):
                    matchup = row['MATCHUP'].replace(' vs. ', '-vs-').replace(' @ ', '-vs-').lower()
                    game_id = row['Game_ID']
                    return f"https://www.nba.com/game/{matchup}-{game_id}"

                games_display['GAME_LINK'] = games_display.apply(create_game_link, axis=1)
                
                # Highlight wins and losses
                def highlight_result(row):
                    if 'WL' not in row:
                        return [''] * len(row)
                    if row['WL'] == 'W':
                        return ['background-color: lightgreen'] * len(row)
                    elif row['WL'] == 'L':
                        return ['background-color: lightcoral'] * len(row)
                    else:
                        return [''] * len(row)
                
                # Rename and select columns for display
                games_display = games_display.rename(columns={
                    'GAME_DATE': 'Date',
                    'OPPONENT': 'Opponent',
                })[['Date', 'Opponent', 'SCORE', 'WL', 'GAME_LINK']]  # Include 'WL' column for highlighting
                
                # Display the games with highlighting
                st.dataframe(games_display.style.apply(highlight_result, axis=1), hide_index=True)
                
                # # Debug information
                # st.write("Debug: Columns in games_display", games_display.columns)
                # st.write("Debug: First few rows of games_display", games_display.head())
            else:
                st.write(f"Unable to fetch game schedule for the {str(season)}-{str(season+1)} season.")

        current_year = datetime.now().year
        seasons = list(range(1990, current_year+1))
        season = st.sidebar.number_input("Select a season", min_value=min(seasons), max_value=max(seasons), value=max(seasons), key='season_numeric_input')
        display_season_games(season)
    else:
        st.write("Please select a team to view details.")

show_teams()

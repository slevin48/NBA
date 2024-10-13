import streamlit as st
from nba_api.stats.static import teams
from nba_api.live.nba.endpoints import scoreboard
from utils import fetch_data, fetch_player_stats
from nba_api.stats.endpoints import teamdetails, teamyearbyyearstats, commonteamroster, teamgamelog
import pandas as pd
# import plotly.express as px
from datetime import datetime
import re

st.set_page_config(page_title="NBA Teams", page_icon="🏀")

st.sidebar.header("Teams")

def show_teams():
    st.title("NBA Teams")
    
    all_teams = teams.get_teams()
    team_names = [team['full_name'] for team in all_teams]
    selected_team = st.selectbox("Select a team", team_names)

    if selected_team:
        team = next(team for team in all_teams if team['full_name'] == selected_team)
        team_id = team['id']
        team_info = fetch_data(teamdetails.TeamDetails, team_id=team_id)
        team_stats = fetch_data(teamyearbyyearstats.TeamYearByYearStats, team_id=team_id)
        
        if team_info is None or team_stats is None:
            st.error("Unable to fetch team data. Please try again later.")
            return

        with st.sidebar:
            # Add link to NBA stats page
            nba_stats_url = f"https://www.nba.com/stats/team/{team_id}"
            st.markdown(f"## [{team['full_name']} ({team['abbreviation']})]({nba_stats_url})")
            
            st.image(f"https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg", width=200)
        
        # Current Season Stats (in sidebar)
        st.sidebar.subheader("Current Season Stats")
        current_season_stats = team_stats.iloc[-1]  # Get the most recent season's stats
        
        # Display win, loss, and rank on one single line
        if 'WINS' in current_season_stats and 'LOSSES' in current_season_stats and 'CONF_RANK' in current_season_stats:
            st.sidebar.text(f"Wins: {current_season_stats.WINS}, Losses: {current_season_stats.LOSSES}, Rank: {current_season_stats.CONF_RANK}")
        
        # Display other stats in an expander
        with st.sidebar.expander("More Stats"):
            if 'WIN_PCT' in current_season_stats:
                st.metric("Win Percentage", f"{current_season_stats.WIN_PCT:.3f}")
            if 'PTS' in current_season_stats:
                st.metric("PTS/G", f"{current_season_stats.PTS:.1f}")
            if 'AST' in current_season_stats:
                st.metric("AST/G", f"{current_season_stats.AST:.1f}")
            if 'REB' in current_season_stats:
                st.metric("REB/G", f"{current_season_stats.REB:.1f}")
            if 'PLUS_MINUS' in current_season_stats:
                st.metric("DIFF", f"{current_season_stats.PLUS_MINUS:.1f}")

        with st.sidebar.expander("Team Information"):
            st.metric("Year Founded", team_info.YEARFOUNDED.iloc[0])
            st.write(f"**City:** {team_info.CITY.iloc[0]}")
            st.write(f"**Arena:** {team_info.ARENA.iloc[0]}")
            st.write(f"**Owner:** {team_info.OWNER.iloc[0]}")
            st.write(f"**General Manager:** {team_info.GENERALMANAGER.iloc[0]}")
            st.write(f"**Head Coach:** {team_info.HEADCOACH.iloc[0]}")
            st.write(f"**D-League Affiliation:** {team_info.DLEAGUEAFFILIATION.iloc[0]}")

        # # Toggle for Historical Performance
        # show_historical = st.sidebar.toggle("Show Historical Performance", value=False)

        # if show_historical:
        #     # Historical performance chart
        #     st.subheader("Historical Performance")
        #     if 'YEAR' in team_stats.columns and 'WIN_PCT' in team_stats.columns:
        #         fig = px.line(team_stats, x='YEAR', y='WIN_PCT', title='Win Percentage Over Years')
        #         fig.update_layout(xaxis_title='Year', yaxis_title='Win Percentage')
        #         st.plotly_chart(fig)
        #     else:
        #         st.write("Historical data not available")

        # Current Season Roster
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

        # # Current Season's Games
        # st.subheader("Current Season's Games")
        # current_season = datetime.now().year
        # game_log = fetch_data(teamgamelog.TeamGameLog, team_id=team_id, season=current_season)
        
        # if game_log is not None and not game_log.empty:
        #     # Convert GAME_DATE to datetime
        #     game_log['GAME_DATE'] = pd.to_datetime(game_log['GAME_DATE'])
            
        #     # Sort games by date (most recent first)
        #     game_log = game_log.sort_values('GAME_DATE', ascending=False)
            
        #     # Prepare data for display
        #     games_display = game_log[['GAME_DATE', 'MATCHUP', 'WL', 'PTS']].copy()
        #     games_display['GAME_DATE'] = games_display['GAME_DATE'].dt.strftime('%Y-%m-%d')
            
        #     # Extract opponent name and score from MATCHUP
        #     def extract_opponent_and_score(matchup):
        #         parts = matchup.split()
        #         opponent = parts[2] if parts[1] == 'vs.' else parts[1]
        #         score = parts[-1]
        #         return pd.Series([opponent, score])

        #     games_display[['OPPONENT', 'OPP_SCORE']] = games_display['MATCHUP'].apply(extract_opponent_and_score)
            
        #     # Create a score column
        #     games_display['SCORE'] = games_display.apply(lambda row: f"{row['PTS']} - {row['OPP_SCORE']}", axis=1)
            
        #     # Highlight wins and losses
        #     def highlight_result(row):
        #         if row['WL'] == 'W':
        #             return ['background-color: lightgreen'] * len(row)
        #         elif row['WL'] == 'L':
        #             return ['background-color: lightcoral'] * len(row)
        #         else:
        #             return [''] * len(row)
            
        #     # Rename and select columns for display
        #     games_display = games_display.rename(columns={
        #         'GAME_DATE': 'Date',
        #         'OPPONENT': 'Opponent',
        #     })[['Date', 'Opponent', 'SCORE']]
            
        #     # Display the games with highlighting
        #     st.dataframe(games_display.style.apply(highlight_result, axis=1), hide_index=True)
        # else:
        #     st.write("Unable to fetch game schedule for the current season.")

if __name__ == "__main__":
    show_teams()

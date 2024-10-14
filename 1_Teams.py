import streamlit as st
from nba_api.stats.static import teams
from nba_api.stats.endpoints import teamdetails, teamyearbyyearstats, commonteamroster
from utils import fetch_data, fetch_player_stats
import pandas as pd
import plotly.express as px

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
    else:
        st.write("Please select a team to view details.")

show_teams()

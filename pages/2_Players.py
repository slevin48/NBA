import streamlit as st
from nba_api.stats.static import players
from utils import fetch_data
from nba_api.stats.endpoints import commonplayerinfo

st.set_page_config(page_title="NBA Players", page_icon="🏀")

def show_players():
    st.title("NBA Players")
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
    show_players()

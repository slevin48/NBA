import streamlit as st

st.logo("basketball_logo.png", size="large")

# Define your pages
home_page = st.Page("0_Home.py", title="Home", icon="🏠")
teams_page = st.Page("1_Teams.py", title="Teams", icon="👥")
players_page = st.Page("2_Players.py", title="Players", icon="🏃")
games_page = st.Page("3_Games.py", title="Games", icon="🏀")

# Create the navigation
pg = st.navigation(
    {
        "Main": [home_page],
        "Explore": [teams_page, players_page, games_page]
    },
    position="sidebar",
    expanded=True
)

pg.run()
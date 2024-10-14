import streamlit as st

st.logo("basketball_logo.png", size="large")

# Define your pages
home_page = st.Page("pages/0_Home.py", title="Home", icon="🏠")
teams_page = st.Page("pages/1_Teams.py", title="Teams", icon="👥")
players_page = st.Page("pages/2_Players.py", title="Players", icon="🏃")

# Create the navigation
pg = st.navigation(
    {
        "Main": [home_page],
        "Explore": [teams_page, players_page]
    },
    position="sidebar",
    expanded=True
)

pg.run()
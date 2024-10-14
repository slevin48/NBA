import streamlit as st
import pandas as pd
import random

# Set page configuration
st.set_page_config(page_title="NBA Betting App", page_icon="🏀")

# Sample data for upcoming matches
matches = pd.DataFrame({
    'Match ID': [1, 2, 3],
    'Home Team': ['Los Angeles Lakers', 'Golden State Warriors', 'Brooklyn Nets'],
    'Away Team': ['Boston Celtics', 'Miami Heat', 'Milwaukee Bucks'],
    'Date': ['2023-10-20', '2023-10-21', '2023-10-22']
})

# Function to simulate odds
def simulate_odds():
    return round(random.uniform(1.5, 3.0), 2)

# Title and description
st.title("🏀 NBA Betting App")
st.write("Welcome to the NBA Betting App! Select a match and place your bet.")

# Display the list of upcoming matches
st.subheader("Upcoming Matches")
st.table(matches[['Match ID', 'Home Team', 'Away Team', 'Date']])

# User selects a match
match_id = st.number_input("Enter the Match ID you want to bet on:", min_value=1, max_value=3, step=1)

# Validate match selection
if match_id in matches['Match ID'].values:
    selected_match = matches[matches['Match ID'] == match_id].iloc[0]
    st.write(f"You have selected: **{selected_match['Home Team']}** vs **{selected_match['Away Team']}** on {selected_match['Date']}")

    # Simulate odds for both teams
    home_odds = simulate_odds()
    away_odds = simulate_odds()

    # Display odds
    st.write(f"**Odds:**")
    st.write(f"- {selected_match['Home Team']}: **{home_odds}**")
    st.write(f"- {selected_match['Away Team']}: **{away_odds}**")

    # User selects a team to bet on
    team = st.radio("Select the team you want to bet on:", (selected_match['Home Team'], selected_match['Away Team']))

    # User enters bet amount
    bet_amount = st.number_input("Enter your bet amount ($):", min_value=1.0, step=1.0)

    # Calculate potential winnings
    if team == selected_match['Home Team']:
        potential_winnings = bet_amount * home_odds
        selected_odds = home_odds
    else:
        potential_winnings = bet_amount * away_odds
        selected_odds = away_odds

    st.write(f"Potential winnings if **{team}** wins: **${potential_winnings:.2f}**")

    # Place bet button
    if st.button("Place Bet"):
        st.success(f"Your bet of **${bet_amount:.2f}** on **{team}** at odds **{selected_odds}** has been placed!")
else:
    st.error("Please enter a valid Match ID from the list above.")

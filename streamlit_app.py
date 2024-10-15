import streamlit as st

st.logo("basketball_logo.png", size="large")

# Create the navigation
pg = st.navigation(
    [
        st.Page("bet1.py"),
        st.Page("bet1b.py"),
        st.Page("bet2.py"),
    ],
    position="sidebar",
    expanded=True
)

pg.run()
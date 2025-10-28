import streamlit as st
import pandas as pd

st.title("💰 Team Budget Scenario Simulator")

# --- Input Section ---
st.sidebar.header("Adjust Inputs")

# Workload assumptions
total_hours = st.sidebar.number_input("Total Workload Hours", 0, 10000, 5000)

# Team split sliders
team1_share = st.sidebar.slider("External Team 1 (%)", 0, 100, 40)
team2_share = st.sidebar.slider("External Team 2 (AI) (%)", 0, 100 - team1_share, 40)
inhouse_share = 100 - team1_share - team2_share

# Cost rates
st.sidebar.header("Cost Rates ($)")
team1_rate = st.sidebar.number_input("Team 1 avg hourly rate", 0, 200, 35)
team2_cost = st.sidebar.number_input("Team 2 yearly flat fee", 0, 200000, 80000)
inhouse_monthly = st.sidebar.number_input("In-house monthly salary total", 0, 50000, 15000)

# --- Computation ---
team1_cost = total_hours * (team1_share / 100) * team1_rate
team2_cost = team2_cost * (team2_share / 100)  # share of AI cost
inhouse_cost = inhouse_monthly * 12 * (inhouse_share / 100)

total_cost = team1_cost + team2_cost + inhouse_cost

# --- Results ---
st.subheader("Scenario Results")
st.metric("Total Annual Cost", f"${total_cost:,.0f}")
st.write(f"In-house share: {inhouse_share}%")
st.write(f"Team 1 (manual) cost: ${team1_cost:,.0f}")
st.write(f"Team 2 (AI) cost: ${team2_cost:,.0f}")
st.write(f"In-house cost: ${inhouse_cost:,.0f}")

# --- Chart ---
data = {
    'Team': ['In-house', 'External Team 1', 'External Team 2'],
    'Cost': [inhouse_cost, team1_cost, team2_cost]
}
df = pd.DataFrame(data)
st.bar_chart(df.set_index('Team'))


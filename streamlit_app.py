import streamlit as st
import pandas as pd

st.title("💰 Annual Budget Scenario Simulator")

# --- Sidebar Inputs ---
st.sidebar.header("Adjust Workload and Team Shares")

# Workload assumptions
total_hours = st.sidebar.number_input("Total Workload Hours", 0, 20000, 5000)

# Team split sliders
st.sidebar.markdown("### Workload Distribution (%)")
gresb_share = st.sidebar.slider("GRESB (%)", 0, 100, 20)
sas_share = st.sidebar.slider("SAS (%)", 0, 100 - gresb_share, 50)
esgds_share = st.sidebar.slider("ESGDS (%)", 0, 100 - gresb_share - sas_share, 30)

# Normalize (optional safety check)
total_share = gresb_share + sas_share + esgds_share
if total_share != 100:
    st.sidebar.warning(f"⚠️ Total = {total_share}%. Adjust to make it 100%.")
    
# --- Cost Inputs ---
st.sidebar.header("GRESB Cost Details")
gresb_monthly_cost = st.sidebar.number_input("GRESB monthly salary total ($)", 0, 100000, 15000)

st.sidebar.header("SAS Cost Details (External Manual Team)")
st.sidebar.caption("Adjust rates for seasonal or role-based changes")
sas_rate_new = st.sidebar.number_input("SAS New Reviewer Rate ($/hr)", 0, 200, 25)
sas_rate_exp = st.sidebar.number_input("SAS Experienced Reviewer Rate ($/hr)", 0, 200, 40)
sas_rate_consult = st.sidebar.number_input("SAS Consulting Rate ($/hr)", 0, 200, 50)

# Combine SAS blended rate (approximation)
st.sidebar.markdown("**SAS Rate Mix**")
new_weight = st.sidebar.slider("New Reviewer %", 0, 100, 40)
exp_weight = st.sidebar.slider("Experienced Reviewer %", 0, 100 - new_weight, 40)
consult_weight = 100 - new_weight - exp_weight

sas_blended_rate = (
    (new_weight / 100) * sas_rate_new +
    (exp_weight / 100) * sas_rate_exp +
    (consult_weight / 100) * sas_rate_consult
)

st.sidebar.write(f"**Blended SAS Rate:** ${sas_blended_rate:.2f}/hr")

st.sidebar.header("ESGDS (AI-Powered Team)")
esgds_annual_cost = st.sidebar.number_input("ESGDS yearly flat fee ($)", 0, 500000, 80000)

# --- Computations ---
# SAS cost (hourly)
sas_cost = total_hours * (sas_share / 100) * sas_blended_rate

# ESGDS cost (annual, proportional to workload share)
esgds_cost = esgds_annual_cost * (esgds_share / 100)

# GRESB cost (monthly salary × 12 months)
gresb_cost = gresb_monthly_cost * 12 * (gresb_share / 100)

# Total cost
total_cost = sas_cost + esgds_cost + gresb_cost

# --- Display Results ---
st.subheader("💡 Scenario Results")
st.metric("Total Annual Cost", f"${total_cost:,.0f}")
st.write(f"GRESB share: {gresb_share}%")
st.write(f"SAS share: {sas_share}%")
st.write(f"ESGDS share: {esgds_share}%")

st.write("---")
st.write(f"**GRESB cost:** ${gresb_cost:,.0f}")
st.write(f"**SAS cost:** ${sas_cost:,.0f}  (Blended rate ${sas_blended_rate:.2f}/hr)")
st.write(f"**ESGDS cost:** ${esgds_cost:,.0f}")

# --- Chart ---
data = {
    'Team': ['GRESB', 'SAS', 'ESGDS'],
    'Cost': [gresb_cost, sas_cost, esgds_cost]
}
df = pd.DataFrame(data)
st.bar_chart(df.set_index('Team'))



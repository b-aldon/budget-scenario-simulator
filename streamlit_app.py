import streamlit as st
import pandas as pd

st.set_page_config(page_title="Budget Scenario Simulator", layout="wide")

st.title("💰 GRESB Annual Budget Scenario Simulator")

# --- Sidebar Sections ---
st.sidebar.header("⚙️ Configure Model Inputs")

# ====================================================
# 1️⃣ Workstreams Section
# ====================================================
st.sidebar.subheader("1. Define Workstreams and Hours")

# Example workstreams (you can later expand or rename)
workstreams = ["Data Review", "QA Audit", "Consultation", "AI Integration"]

workstream_hours = {}
for ws in workstreams:
    workstream_hours[ws] = st.sidebar.number_input(
        f"Hours for {ws}", min_value=0, max_value=5000, value=500, step=50
    )

# ====================================================
# 2️⃣ Workload Distribution (per workstream)
# ====================================================
st.sidebar.subheader("2. Team Allocation per Workstream")

workload_split = {}
for ws in workstreams:
    st.sidebar.markdown(f"**{ws}**")
    gresb = st.sidebar.slider(f"GRESB share for {ws} (%)", 0, 100, 20, key=f"gresb_{ws}")
    sas = st.sidebar.slider(f"SAS share for {ws} (%)", 0, 100 - gresb, 50, key=f"sas_{ws}")
    esgds = st.sidebar.slider(
        f"ESGDS share for {ws} (%)", 0, 100 - gresb - sas, 30, key=f"esgds_{ws}"
    )

    total = gresb + sas + esgds
    if total != 100:
        st.sidebar.warning(f"⚠️ Total = {total}% for {ws}. Adjust to make 100%.")
    workload_split[ws] = {"GRESB": gresb, "SAS": sas, "ESGDS": esgds}

# ====================================================
# 3️⃣ Cost Details (Tidy expanders)
# ====================================================
st.sidebar.subheader("3. Cost Details")

with st.sidebar.expander("💼 GRESB"):
    gresb_monthly_cost = st.number_input("GRESB monthly salary total ($)", 0, 100000, 15000)

with st.sidebar.expander("🧑‍🏭 SAS (Manual Team)"):
    st.caption("Define SAS rate structure and role mix")
    sas_rate_new = st.number_input("SAS New Reviewer Rate ($/hr)", 0, 200, 25)
    sas_rate_exp = st.number_input("SAS Experienced Reviewer Rate ($/hr)", 0, 200, 40)
    sas_rate_consult = st.number_input("SAS Consulting Rate ($/hr)", 0, 200, 50)

    st.markdown("**Mix of SAS roles (%)**")
    new_weight = st.slider("New Reviewer %", 0, 100, 40)
    exp_weight = st.slider("Experienced Reviewer %", 0, 100 - new_weight, 40)
    consult_weight = 100 - new_weight - exp_weight
    sas_blended_rate = (
        (new_weight / 100) * sas_rate_new +
        (exp_weight / 100) * sas_rate_exp +
        (consult_weight / 100) * sas_rate_consult
    )
    st.write(f"Blended SAS Rate: **${sas_blended_rate:.2f}/hr**")

with st.sidebar.expander("🤖 ESGDS (AI Team)"):
    esgds_annual_cost = st.number_input("ESGDS yearly flat fee ($)", 0, 500000, 80000)

# ====================================================
# 🔢 COMPUTATION
# ====================================================
results = []
for ws in workstreams:
    hours = workstream_hours[ws]
    split = workload_split[ws]

    gresb_cost = gresb_monthly_cost * 12 * (split["GRESB"] / 100) * (hours / sum(workstream_hours.values()))
    sas_cost = hours * (split["SAS"] / 100) * sas_blended_rate
    esgds_cost = esgds_annual_cost * (split["ESGDS"] / 100) * (hours / sum(workstream_hours.values()))

    total_cost = gresb_cost + sas_cost + esgds_cost

    results.append({
        "Workstream": ws,
        "Hours": hours,
        "GRESB %": split["GRESB"],
        "SAS %": split["SAS"],
        "ESGDS %": split["ESGDS"],
        "GRESB Cost": gresb_cost,
        "SAS Cost": sas_cost,
        "ESGDS Cost": esgds_cost,
        "Total Cost": total_cost
    })

df = pd.DataFrame(results)

# ====================================================
# 📊 DISPLAY RESULTS
# ====================================================
st.header("📊 Results Overview")
st.dataframe(df.style.format("{:,.0f}", subset=["GRESB Cost", "SAS Cost", "ESGDS Cost", "Total Cost"]))

# Total summary
st.markdown("---")
total_summary = df[["GRESB Cost", "SAS Cost", "ESGDS Cost", "Total Cost"]].sum()
st.metric("Total Annual Cost", f"${total_summary['Total Cost']:,.0f}")

# Chart
chart_df = total_summary[:-1].reset_index()
chart_df.columns = ["Team", "Cost"]
st.bar_chart(chart_df.set_index("Team"))



import streamlit as st
import pandas as pd

st.set_page_config(page_title="GRESB Budget Simulator", layout="wide")

st.title("💰 GRESB Annual Budget Scenario Simulator")

# ====================================================
# WORKSTREAM STRUCTURE
# ====================================================

workstream_structure = {
    "Jan - March": [
        "Validation Guidance Docs",
        "OAD",
        "Edge cases files",
        "LLM output Refinement"
    ],
    "Apr - June": [
        "PSC admin",
        "PSC validation (Primary and QC)",
        "PSC notes prep for GRESB",
        "PSC call leads",
        "Report generation",
        "Queries on Front"
    ],
    "July - August": [
        "Validation Admin",
        "Primary Decisions",
        "Secondary decisions",
        "QC 10% of accepted Primaries",
        "Same Doc ID - CC",
        "YoY - CC",
        "Sensitive managers - CC",
        "Extra QC on LLM decisions",
        "Escalations Set-up"
    ],
    "September": [
        "All validation queries on Front",
        "Re-Validate from AC - Primary",
        "Re-Validate from AC - Secondary",
        "Deem YoY mistake",
        "Deem validation error",
        "Update and maintain trackers",
        "Revert Validation error decisions",
        "Same Doc ID - CC",
        "YoY - CC",
        "Sensitive managers - CC"
    ],
    "October - December": [
        "LLM Output refinement",
        "Compile cases for Outreach",
        "Post Vali tasks"
    ]
}

# ====================================================
# SIDEBAR: WORKSTREAMS (expandable)
# ====================================================

st.sidebar.header("⚙️ Configure Model Inputs")

with st.sidebar.expander("🧩 1. Workstreams & Hours", expanded=False):
    st.caption("Define the time allocation (in hours) for each task.")
    workstream_hours = {}

    for period, tasks in workstream_structure.items():
        with st.expander(period, expanded=False):
            for task in tasks:
                workstream_hours[task] = st.number_input(
                    f"{task} (hrs)", min_value=0, max_value=2000, value=100, step=10, key=f"hrs_{task}"
                )

# ====================================================
# SIDEBAR: TEAM ALLOCATION (expandable)
# ====================================================

with st.sidebar.expander("👥 2. Team Allocation per Workstream", expanded=False):
    st.caption("Assign workload shares (in %) to GRESB, SAS, and ESGDS for each sub-task. Total must equal 100%.")
    workload_split = {}

    for period, tasks in workstream_structure.items():
        with st.expander(period, expanded=False):
            for task in tasks:
                gresb = st.slider(f"GRESB share for {task}", 0, 100, 20, key=f"gresb_{task}")
                sas = st.slider(f"SAS share for {task}", 0, 100 - gresb, 50, key=f"sas_{task}")
                esgds = st.slider(f"ESGDS share for {task}", 0, 100 - gresb - sas, 30, key=f"esgds_{task}")

                total = gresb + sas + esgds
                if total != 100:
                    st.warning(f"⚠️ Total = {total}% for {task}. Adjust to make 100%.")
                workload_split[task] = {"GRESB": gresb, "SAS": sas, "ESGDS": esgds}

# ====================================================
# SIDEBAR: COST DETAILS (Grouped)
# ====================================================

st.sidebar.subheader("💵 3. Cost Details")

with st.sidebar.expander("GRESB (Internal Team)", expanded=False):
    gresb_monthly_cost = st.number_input("Monthly salary total ($)", 0, 100000, 15000)

with st.sidebar.expander("SAS (Manual Team)", expanded=False):
    sas_rate_new = st.number_input("New Reviewer Rate ($/hr)", 0, 200, 25)
    sas_rate_exp = st.number_input("Experienced Reviewer Rate ($/hr)", 0, 200, 40)
    sas_rate_consult = st.number_input("Consulting Rate ($/hr)", 0, 200, 50)

    st.markdown("**Role Mix for SAS (%)**")
    new_weight = st.slider("New Reviewer %", 0, 100, 40)
    exp_weight = st.slider("Experienced Reviewer %", 0, 100 - new_weight, 40)
    consult_weight = 100 - new_weight - exp_weight
    sas_blended_rate = (
        (new_weight / 100) * sas_rate_new +
        (exp_weight / 100) * sas_rate_exp +
        (consult_weight / 100) * sas_rate_consult
    )
    st.info(f"Blended SAS Rate: **${sas_blended_rate:.2f}/hr**")

with st.sidebar.expander("ESGDS (AI Team)", expanded=False):
    esgds_annual_cost = st.number_input("Yearly flat fee ($)", 0, 500000, 80000)

# ====================================================
# COMPUTATION
# ====================================================

results = []
total_hours = sum(workstream_hours.values()) if workstream_hours else 1

for period, tasks in workstream_structure.items():
    for task i


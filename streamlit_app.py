import streamlit as st
import pandas as pd

st.set_page_config(page_title="GRESB Budget Simulator", layout="wide")

st.title("💰 GRESB Annual Budget Scenario Simulator")

# ====================================================
# UPDATED WORKSTREAM STRUCTURE (unique names)
# ====================================================

workstream_structure = {
    "Jan - March": [
        "1. Validation Guidance Docs",
        "2. OAD",
        "3. Edge cases files",
        "4. LLM output Refinement"
    ],
    "Apr - June": [
        "5. PSC admin",
        "6. PSC validation (Primary and QC)",
        "7. PSC notes prep for GRESB calls",
        "8. PSC call leads",
        "9. Report generation",
        "10. Queries on Front"
    ],
    "July - August": [
        "11. Validation Admin",
        "12. Primary Decisions",
        "13. Secondary decisions",
        "14. QC 10% of accepted",
        "15. Same Doc ID - CC",
        "16. YoY - CC",
        "17. Sensitive managers - CC",
        "18. Extra QC on LLM decisions",
        "19. Escalations Set-up"
    ],
    "September": [
        "20. All validation queries on Front",
        "21. Re-Validate from AC - Primary",
        "22. Re-Validate from AC - Secondary",
        "23. Deem YoY mistake",
        "24. Deem validation error",
        "25. Update and maintain trackers",
        "26. Revert Validation error decisions",
        "27. Same Docs - CC",
        "28. Manager level - CC"
    ],
    "October - December": [
        "29. LLM Output refinement",
        "30. Compile Outreach cases",
        "31. Post-Validation tasks"
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
                    f"{task} (hrs)",
                    min_value=0,
                    max_value=2000,
                    value=100,
                    step=10,
                    key=f"hrs_{task.replace(' ', '_')}"
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
                gresb = st.slider(f"GRESB share for {task}", 0, 100, 20, key=f"gresb_{task.replace(' ', '_')}")
                sas = st.slider(f"SAS share for {task}", 0, 100 - gresb, 50, key=f"sas_{task.replace(' ', '_')}")
                esgds = st.slider(f"ESGDS share for {task}", 0, 100 - gresb - sas, 30, key=f"esgds_{task.replace(' ', '_')}")

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
    for task in tasks:
        hours = workstream_hours[task]
        split = workload_split[task]

        gresb_cost = gresb_monthly_cost * 12 * (split["GRESB"] / 100) * (hours / total_hours)
        sas_cost = hours * (split["SAS"] / 100) * sas_blended_rate
        esgds_cost = esgds_annual_cost * (split["ESGDS"] / 100) * (hours / total_hours)

        total_cost = gresb_cost + sas_cost + esgds_cost

        results.append({
            "Category": period,
            "Task": task,
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
# DISPLAY RESULTS
# ====================================================

st.header("📊 Results Overview")
st.dataframe(df.style.format("{:,.0f}", subset=["GRESB Cost", "SAS Cost", "ESGDS Cost", "Total Cost"]))

st.markdown("---")
summary = df.groupby("Category")[["GRESB Cost", "SAS Cost", "ESGDS Cost", "Total Cost"]].sum()
summary_total = summary.sum()

st.metric("Total Annual Cost", f"${summary_total['Total Cost']:,.0f}")

st.bar_chart(summary[["GRESB Cost", "SAS Cost", "ESGDS Cost"]])


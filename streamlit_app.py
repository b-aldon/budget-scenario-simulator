import streamlit as st
import pandas as pd

st.set_page_config(page_title="GRESB Budget Scenario Simulator", layout="wide")

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
# SIDEBAR: COMBINED INPUTS
# ====================================================

st.sidebar.header("⚙️ Configure Model Inputs")

with st.sidebar.expander("🧩 Workstreams, Hours & Team Allocation", expanded=False):
    st.caption("Define hours and team workload distribution per workstream.")
    workstream_inputs = {}

    for period, tasks in workstream_structure.items():
        with st.expander(period, expanded=False):
            for task in tasks:
                st.markdown(f"**{task}**")
                cols = st.columns([2, 1, 1, 1, 0.5])
                
                with cols[0]:
                    hours = st.number_input(
                        f"Hours for {task}",
                        min_value=0,
                        max_value=2000,
                        value=100,
                        step=10,
                        key=f"hrs_{task.replace(' ', '_')}"
                    )
                with cols[1]:
                    gresb = st.number_input(
                        "GRESB %",
                        min_value=0,
                        max_value=100,
                        value=20,
                        step=5,
                        key=f"gresb_{task.replace(' ', '_')}"
                    )
                with cols[2]:
                    sas = st.number_input(
                        "SAS %",
                        min_value=0,
                        max_value=100,
                        value=50,
                        step=5,
                        key=f"sas_{task.replace(' ', '_')}"
                    )
                with cols[3]:
                    esgds = st.number_input(
                        "ESGDS %",
                        min_value=0,
                        max_value=100,
                        value=30,
                        step=5,
                        key=f"esgds_{task.replace(' ', '_')}"
                    )

                total = gresb + sas + esgds
                if total > 100:
                    st.error(f"⚠️ Total {total}% exceeds 100% for {task}. Reduce one of the shares.")

                workstream_inputs[task] = {
                    "Category": period,
                    "Hours": hours,
                    "GRESB": gresb,
                    "SAS": sas,
                    "ESGDS": esgds
                }

# ====================================================
# SIDEBAR: COST DETAILS (Grouped)
# ====================================================

st.sidebar.subheader("💵 Cost Details")

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
total_hours = sum([v["Hours"] for v in workstream_inputs.values()]) or 1

for task, details in workstream_inputs.items():
    hours = details["Hours"]
    gresb_share = details["GRESB"]
    sas_share = details["SAS"]
    esgds_share = details["ESGDS"]

    # Cost calculations
    gresb_cost = gresb_monthly_cost * 12 * (gresb_share / 100) * (hours / total_hours)
    sas_cost = hours * (sas_share / 100) * sas_blended_rate
    esgds_cost = esgds_annual_cost * (esgds_share / 100) * (hours / total_hours)

    total_cost = gresb_cost + sas_cost + esgds_cost

    results.append({
        "Category": details["Category"],
        "Task": task,
        "Hours": hours,
        "GRESB %": gresb_share,
        "SAS %": sas_share,
        "ESGDS %": esgds_share,
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


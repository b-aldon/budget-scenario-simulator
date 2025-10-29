import streamlit as st
import pandas as pd

st.set_page_config(page_title="Validation Budget Simulator", layout="wide")

# --- Header Section ---
from PIL import Image
import requests
from io import BytesIO

# Load GRESB logo directly from the web
logo_url = "https://www.gresb.com/wp-content/uploads/page-press-media-5.png"
response = requests.get(logo_url)
logo = Image.open(BytesIO(response.content))

# Display logo and title neatly side by side
col1, col2 = st.columns([1, 4])
with col1:
    st.image(logo, width=180)
with col2:
    st.title("Validation Budget Simulator")

# --- Sidebar ---
st.sidebar.title("Workstreams, Hours & Team Allocation")
st.sidebar.markdown("Adjust the total hours and team allocation for each workstream below:")

# --- Define actors ---
actors = ["GRESB", "SAS New", "SAS Exp", "SAS Consl", "ESGDS"]

# --- Workstream structure ---
workstreams = {
    "Jan - March": [
        "1. Validation Guidance Docs", "2. OAD", "3. Edge cases files", "4. LLM output Refinement"
    ],
    "Apr - June": [
        "5. PSC admin", "6. PSC validation (Primary and QC)", "7. PSC notes prep for GRESB calls",
        "8. PSC call leads", "9. Report generation", "10. Queries on Front"
    ],
    "July - August": [
        "11. Validation Admin", "12. Primary Decisions", "13. Secondary decisions",
        "14. QC 10% of accepted", "15. Same Doc ID - CC", "16. YoY - CC",
        "17. Sensitive managers - CC", "18. Extra QC on LLM decisions", "19. Escalations Set-up"
    ],
    "September": [
        "20. All validation queries on Front", "21. Re-Validate from AC - Primary",
        "22. Re-Validate from AC - Secondary", "23. Deem YoY mistake",
        "24. Deem validation error", "25. Update and maintain trackers",
        "26. Revert Validation error decisions", "27. Same Docs - CC", "28. Manager level - CC"
    ],
    "October - December": [
        "29. LLM Output refinement", "30. Compile Outreach cases", "31. Post-Validation tasks"
    ]
}

# --- Collect user inputs ---
st.sidebar.markdown("### Workstream Allocation")

allocation_data = []

for period, tasks in workstreams.items():
    with st.sidebar.expander(period, expanded=False):
        for task in tasks:
            st.markdown(f"**{task}**")
            hours = st.number_input(f"Hours", min_value=0, value=0, step=1, key=f"hours_{task}")

            cols = st.columns(len(actors))
            percentages = []
            for i, actor in enumerate(actors):
                with cols[i]:
                    pct = st.number_input(f"{actor} %", min_value=0, max_value=100, value=0, step=1, key=f"{actor}_{task}")
                    percentages.append(pct)

            # Validation: Total % must not exceed 100
            total_pct = sum(percentages)
            if total_pct > 100:
                st.warning(f"⚠️ Total allocation exceeds 100% for {task}. Please adjust.")
            
            allocation_data.append({
                "Period": period,
                "Workstream": task,
                "Hours": hours,
                **{actor: pct for actor, pct in zip(actors, percentages)}
            })

# --- Cost Details Section ---
st.sidebar.markdown("---")
st.sidebar.title("Cost Details")

with st.sidebar.expander("GRESB"):
    gresb_cost = st.number_input("GRESB Monthly Cost ($)", min_value=0.0, value=1000.0, step=100.0)

with st.sidebar.expander("SAS"):
    sas_new = st.number_input("SAS New Reviewer Rate ($/hr)", min_value=0.0, value=25.0, step=1.0)
    sas_exp = st.number_input("SAS Experienced Reviewer Rate ($/hr)", min_value=0.0, value=40.0, step=1.0)
    sas_consl = st.number_input("SAS Consulting Rate ($/hr)", min_value=0.0, value=60.0, step=1.0)

with st.sidebar.expander("ESGDS"):
    esgds_cost = st.number_input("ESGDS Annual Cost ($)", min_value=0.0, value=15000.0, step=500.0)

# --- Convert inputs to DataFrame ---
df = pd.DataFrame(allocation_data)

# --- Calculate estimated cost for each row ---
def calc_cost(row):
    total_cost = 0
    total_cost += (row["Hours"] * row["GRESB"] / 100) * (gresb_cost / 160)  # Approx. hourly rate
    total_cost += (row["Hours"] * row["SAS New"] / 100) * sas_new
    total_cost += (row["Hours"] * row["SAS Exp"] / 100) * sas_exp
    total_cost += (row["Hours"] * row["SAS Consl"] / 100) * sas_consl
    total_cost += (row["Hours"] * row["ESGDS"] / 100) * (esgds_cost / 2000)  # Approx. hourly equivalent
    return total_cost

if not df.empty:
    df["Estimated Cost ($)"] = df.apply(calc_cost, axis=1)

# --- Main Output Section ---
import pandas as pd
st.markdown("## 💰 Cost per Workstream")

results = []
for period, tasks in workstreams.items():
    for task in tasks:
        hours = st.session_state.get(f"hours_{task}", 0)
        workload = {
            "GRESB": st.session_state.get(f"GRESB_{task}", 0),
            "SAS New": st.session_state.get(f"SAS New_{task}", 0),
            "SAS Exp": st.session_state.get(f"SAS Exp_{task}", 0),
            "SAS Consl": st.session_state.get(f"SAS Consl_{task}", 0),
            "ESGDS": st.session_state.get(f"ESGDS_{task}", 0),
        }

        # ✅ Use consistent variable names defined earlier
        gresb_share = workload["GRESB"]
        gresb_cost_calc = (hours * gresb_share / 100) * (gresb_cost / 160)  # Approx hourly

        sas_new_share = workload["SAS New"]
        sas_new_cost_calc = (hours * sas_new_share / 100) * sas_new

        sas_exp_share = workload["SAS Exp"]
        sas_exp_cost_calc = (hours * sas_exp_share / 100) * sas_exp

        sas_consl_share = workload["SAS Consl"]
        sas_consl_cost_calc = (hours * sas_consl_share / 100) * sas_consl

        esgds_share = workload["ESGDS"]
        esgds_cost_calc = (hours * esgds_share / 100) * (esgds_cost / 2000)

        total_cost = gresb_cost_calc + sas_new_cost_calc + sas_exp_cost_calc + sas_consl_cost_calc + esgds_cost_calc

        results.append({
            "Period": period,
            "Workstream": task,
            "Hours": hours,
            "GRESB": gresb_cost_calc,
            "SAS New": sas_new_cost_calc,
            "SAS Exp": sas_exp_cost_calc,
            "SAS Consl": sas_consl_cost_calc,
            "ESGDS": esgds_cost_calc,
            "Total": total_cost
        })

# --- Convert to DataFrame ---
df = pd.DataFrame(results)
df.index = df.index + 1  # start numbering at 1

# Group data by period
for period in output_df["Period"].unique():
    with st.expander(f"📅 {period}", expanded=True):
        period_df = output_df[output_df["Period"] == period].copy()

        # Optional: round off numeric columns for display
        numeric_cols = period_df.select_dtypes(include=["float", "int"]).columns
        period_df[numeric_cols] = period_df[numeric_cols].round(2)

        # Display the dataframe without the index
        st.dataframe(
            period_df[
                [
                    "Workstream",
                    "Hours",
                    "GRESB",
                    "SAS New",
                    "SAS Exp",
                    "SAS Consl",
                    "ESGDS",
                    "Total"
                ]
            ],
            use_container_width=True
        )

        # Add a mini summary below each expander
        total_cost = period_df["Total"].sum()
        total_hours = period_df["Hours"].sum()
        st.markdown(
            f"**Subtotal:** 💰 ${total_cost:,.0f} 🕒 {total_hours:,.0f} hours"
        )

st.divider()

# --- Bar Chart Visualization ---
st.markdown("### 📊 Cost Distribution by Actor")

actor_totals = {
    "GRESB": df["GRESB"].sum(),
    "SAS New": df["SAS New"].sum(),
    "SAS Exp": df["SAS Exp"].sum(),
    "SAS Consl": df["SAS Consl"].sum(),
    "ESGDS": df["ESGDS"].sum()
}

chart_df = pd.DataFrame({
    "Actor": list(actor_totals.keys()),
    "Total Cost": list(actor_totals.values())
})

chart_df.set_index("Actor", inplace=True)
st.bar_chart(chart_df)

# --- Summary Section ---
st.markdown("## 🧾 Aggregated Cost Summary")

total_gresb = actor_totals["GRESB"]
total_sas = actor_totals["SAS New"] + actor_totals["SAS Exp"] + actor_totals["SAS Consl"]
total_esgds = actor_totals["ESGDS"]

st.write(f"**GRESB Total:** ${total_gresb:,.2f}")
st.write(f"**SAS Total:** ${total_sas:,.2f}")
st.write(f"  • SAS New: ${actor_totals['SAS New']:,.2f}")
st.write(f"  • SAS Exp: ${actor_totals['SAS Exp']:,.2f}")
st.write(f"  • SAS Consl: ${actor_totals['SAS Consl']:,.2f}")
st.write(f"**ESGDS Total:** ${total_esgds:,.2f}")
st.write(f"### 💵 **Grand Total:** ${df['Total'].sum():,.2f}")


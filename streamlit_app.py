import streamlit as st
import pandas as pd

st.set_page_config(page_title="Validation Budget Simulator", layout="wide")

# --- Header Section ---
from PIL import Image
import requests
from io import BytesIO

# Load GRESB logo directly from the web

# Display logo and title neatly side by side


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

# --- SCENARIO SAVE/LOAD FUNCTIONALITY (Phase 1) ---
import copy

# Initialize storage for saved scenarios
if "saved_scenarios" not in st.session_state:
    st.session_state.saved_scenarios = {}

# --- Helper function to capture all sidebar inputs ---
def capture_current_state():
    state_snapshot = {}
    for key, value in st.session_state.items():
        if any(prefix in key for prefix in ["hours_", "GRESB_", "SAS New_", "SAS Exp_", "SAS Consl_", "ESGDS_", "cost_", "rate_", "share_"]):
            state_snapshot[key] = copy.deepcopy(value)
    return state_snapshot

# --- Save Scenario Section ---
# --- SCENARIO SAVE/LOAD FUNCTIONALITY (Phase 1.5 – Interactive Manager) ---
import copy

# Initialize storage for saved scenarios
if "saved_scenarios" not in st.session_state:
    st.session_state.saved_scenarios = {}

# --- Helper to capture all sidebar inputs ---
def capture_current_state():
    state_snapshot = {}
    for key, value in st.session_state.items():
        if any(prefix in key for prefix in [
            "hours_", "GRESB_", "SAS New_", "SAS Exp_", "SAS Consl_", "ESGDS_",
            "cost_", "rate_", "share_"
        ]):
            state_snapshot[key] = copy.deepcopy(value)
    return state_snapshot


st.markdown("## 💾 Scenario Manager")

# --- SAVE SCENARIO ---
with st.expander("💾 Save Current Scenario"):
    scenario_name = st.text_input("Enter a scenario name:")
    if st.button("Save Scenario"):
        if scenario_name.strip() == "":
            st.warning("Please enter a valid scenario name before saving.")
        else:
            if "df" in locals() and "Total" in df.columns and "Hours" in df.columns:
                saved_data = {
                    "inputs": capture_current_state(),
                    "results": df.to_dict(),
                    "summary": {
                        "total_cost": float(df["Total"].sum()),
                        "total_hours": float(df["Hours"].sum()),
                        "total_workstreams": len(df),
                    },
                }

                # Overwrite if scenario exists
                st.session_state.saved_scenarios[scenario_name] = saved_data
                st.success(f"✅ Scenario '{scenario_name}' saved/updated successfully!")
            else:
                st.warning("⚠️ Please run the model first before saving a scenario.")


# --- VIEW & LOAD SCENARIOS ---
if st.session_state.saved_scenarios:
    st.markdown("### 📁 Saved Scenarios")

    for name, data in list(st.session_state.saved_scenarios.items()):
        with st.expander(f"📊 {name}", expanded=False):
            st.write(f"**Total Workstreams:** {data['summary']['total_workstreams']}")
            st.write(f"**Total Hours:** {data['summary']['total_hours']}")
            st.write(f"**Total Cost:** ${data['summary']['total_cost']:,.2f}")

            df_preview = pd.DataFrame(data["results"])
            st.dataframe(df_preview, use_container_width=True)

            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button(f"🔄 Load", key=f"load_{name}"):
                    for k, v in data["inputs"].items():
                        st.session_state[k] = v
                    st.success(f"✅ Scenario '{name}' loaded! Sidebar will reflect saved inputs.")
                    st.rerun()

            with col2:
                if st.button(f"🗑️ Delete", key=f"delete_{name}"):
                    del st.session_state.saved_scenarios[name]
                    st.warning(f"Scenario '{name}' deleted.")
                    st.rerun()


# --- Main Output Section ---
# --- Main Output Section ---
st.markdown("## 🧮 Validation Budget Simulator")

# ==========================
#  I. COST OVERVIEW TABLE (Nested View)
# ==========================
st.markdown("### 📋 Cost Overview")

# --- Compute Costs ---
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

        gresb_cost_calc = (hours * workload["GRESB"] / 100) * (gresb_cost / 160)
        sas_new_cost_calc = (hours * workload["SAS New"] / 100) * sas_new
        sas_exp_cost_calc = (hours * workload["SAS Exp"] / 100) * sas_exp
        sas_consl_cost_calc = (hours * workload["SAS Consl"] / 100) * sas_consl
        esgds_cost_calc = (hours * workload["ESGDS"] / 100) * (esgds_cost / 2000)

        total_cost = (
            gresb_cost_calc + sas_new_cost_calc + sas_exp_cost_calc + sas_consl_cost_calc + esgds_cost_calc
        )

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

df = pd.DataFrame(results)
df.index = df.index + 1

# --- Create header row manually ---

# --- Render each Period as a collapsible row ---
for period in workstreams.keys():
    period_df = df[df["Period"] == period][
        ["Workstream", "Hours", "GRESB", "SAS New", "SAS Exp", "SAS Consl", "ESGDS", "Total"]
    ]
    total_period_cost = period_df["Total"].sum()
    with st.expander(f"📁 {period}  —  Total Cost: ${total_period_cost:,.0f}", expanded=False):
        st.dataframe(
            period_df.style.format({
                "Hours": "{:.0f}",
                "GRESB": "${:,.0f}",
                "SAS New": "${:,.0f}",
                "SAS Exp": "${:,.0f}",
                "SAS Consl": "${:,.0f}",
                "ESGDS": "${:,.0f}",
                "Total": "${:,.0f}",
            }),
            use_container_width=True,
        )


# ==========================
#  II. COST DISTRIBUTION CHARTS
# ==========================
st.markdown("### 📊 Cost Distribution Charts")

# --- Pie Chart: Cost by Actor ---
st.markdown("#### 🥧 Cost Distribution by Actor")

actor_totals = {
    "GRESB": df["GRESB"].sum(),
    "ESGDS": df["ESGDS"].sum(),
    "SAS New": df["SAS New"].sum(),
    "SAS Exp": df["SAS Exp"].sum(),
    "SAS Consl": df["SAS Consl"].sum()
}

pie_df = pd.DataFrame({
    "Actor": list(actor_totals.keys()),
    "Total Cost": list(actor_totals.values())
})

import altair as alt

# Updated color order and palette
color_scale = alt.Scale(
    domain=["GRESB", "ESGDS", "SAS New", "SAS Exp", "SAS Consl"],
    range=["#00A36C", "#800000", "#00BFFF", "#1E90FF", "#003366"]  # Green, Maroon, Blue shades
)

pie_chart = (
    alt.Chart(pie_df)
    .mark_arc(outerRadius=110)
    .encode(
        theta="Total Cost",
        color=alt.Color("Actor", scale=color_scale, legend=alt.Legend(title="Actor")),
        tooltip=["Actor", alt.Tooltip("Total Cost", format="$,.0f")]
    )
    .properties(height=400)
)
st.altair_chart(pie_chart, use_container_width=True)

# --- Stacked Bar Chart: Cost by Workstream Category ---
st.markdown("#### 📅 Cost Distribution by Workstream Category")

stack_df = (
    df.groupby("Period")[["GRESB", "ESGDS", "SAS New", "SAS Exp", "SAS Consl"]]
    .sum()
    .reset_index()
    .melt(id_vars="Period", var_name="Actor", value_name="Cost")
)

# Chronological order for periods
period_order = ["Jan - March", "Apr - June", "July - August", "September", "October - December"]

stack_chart = (
    alt.Chart(stack_df)
    .mark_bar()
    .encode(
        x=alt.X("Period:N", title="Workstream Category", sort=period_order),
        y=alt.Y("Cost:Q", title="Total Cost ($)", stack="normalize"),
        color=alt.Color("Actor", scale=color_scale, legend=alt.Legend(title="Actor")),
        tooltip=["Period", "Actor", alt.Tooltip("Cost", format="$,.0f")]
    )
    .properties(height=400)
)
st.altair_chart(stack_chart, use_container_width=True)

# ==========================
#  III. SUMMARY SECTION
# ==========================
st.markdown("### 🧾 Summary")

if df.empty:
    st.info("No data available yet — please input hours and allocations in the sidebar.")
else:
    num_workstreams = df["Workstream"].nunique()
    total_hours = df["Hours"].sum()
    total_cost = df["Total"].sum()

    total_gresb = df["GRESB"].sum()
    total_sas = df["SAS New"].sum() + df["SAS Exp"].sum() + df["SAS Consl"].sum()
    total_esgds = df["ESGDS"].sum()

    # --- Key Metrics ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🧩 Workstreams", f"{num_workstreams}")
    with col2:
        st.metric("⏱️ Total Hours", f"{total_hours:,.0f}")
    with col3:
        st.metric("💵 Total Cost", f"${total_cost:,.2f}")

    # --- Cost Split by Team ---
    st.markdown("---")
    st.markdown("#### 💼 Cost Split by Team")

    st.markdown(
        f"""
        <style>
        .team-header {{
            font-size: 17px;
            font-weight: 600;
            color: #222;
            line-height: 1.6;
        }}
        </style>

        <div class="team-header">GRESB: ${total_gresb:,.2f}</div>
        <div class="team-header">SAS: ${total_sas:,.2f}</div>
        <div class="team-header">ESGDS: ${total_esgds:,.2f}</div>
        """,
        unsafe_allow_html=True,
    )

    # --- Additional Key Facts ---
    st.markdown("---")
    avg_cost_per_hour = total_cost / total_hours if total_hours > 0 else 0
    cost_per_workstream = total_cost / num_workstreams if num_workstreams > 0 else 0
    gresb_ratio = (total_gresb / total_cost * 100) if total_cost > 0 else 0

    st.info(f"💡 **Average Cost per Hour:** ${avg_cost_per_hour:,.2f}")
    st.info(f"💡 **Average Cost per Workstream:** ${cost_per_workstream:,.2f}")
    st.info(f"💡 **GRESB Share of Total Cost:** {gresb_ratio:.1f}%")



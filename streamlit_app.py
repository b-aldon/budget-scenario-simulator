import streamlit as st
import pandas as pd

# --- Safe scenario reloader ---
if "pending_load_scenario" in st.session_state:
    try:
        pending_inputs = st.session_state.pop("pending_load_scenario", {})
        scenario_name = st.session_state.pop("pending_scenario_name", "Unknown")
        for key, val in pending_inputs.items():
            if key in st.session_state:
                st.session_state[key] = val
        st.toast(f"✅ Scenario '{scenario_name}' loaded successfully!")
    except Exception as e:
        st.warning(f"⚠️ Could not restore some scenario values: {e}")

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

# --- SCENARIO SAVE/LOAD FUNCTIONALITY (Phase 2) ---
# --- SCENARIO SAVE/LOAD FUNCTIONALITY (Robust, fixed for KeyError 'Total') ---
import json
import io

st.markdown("## 💾 Saved Scenarios")

# ensure storage exists
if "saved_scenarios" not in st.session_state:
    st.session_state.saved_scenarios = {}

# helper to capture sidebar-related inputs (conservative)
def capture_current_state():
    state_snapshot = {}
    for key, value in st.session_state.items():
        # keep primitive types and small containers only
        if isinstance(value, (int, float, str, bool, list, dict)):
            state_snapshot[key] = value
    return state_snapshot

# --- Save new scenario UI ---
with st.expander("💾 Save Current Scenario", expanded=False):
    scenario_name = st.text_input("Scenario Name", key="save_name_input")

    if st.button("Save Scenario"):
        model_df = st.session_state.get("model_df", None)

        # Validate model presence and structure
        if model_df is None or not isinstance(model_df, (pd.DataFrame,)) or model_df.empty:
            st.warning("⚠️ Please run the model first before saving a scenario.")
        elif "Total" not in model_df.columns or "Hours" not in model_df.columns:
            st.warning("⚠️ Model output incomplete - missing required columns. Re-run the model.")
        elif not scenario_name or not scenario_name.strip():
            st.warning("⚠️ Please provide a valid scenario name.")
        else:
            # capture safe snapshot of st.session_state inputs
            saved_inputs = capture_current_state()

            # actor_totals: compute safely from model_df
            actor_totals = {}
            for col in ["GRESB", "SAS New", "SAS Exp", "SAS Consl", "ESGDS"]:
                actor_totals[col] = float(model_df[col].sum()) if col in model_df.columns else 0.0

            # prepare dataframe dict for export (use orient='split' to be robust)
            df_dict = model_df.to_dict(orient="split")  # columns, index, data

            scenario_payload = {
                "inputs": saved_inputs,
                "dataframe": df_dict,
                "actor_totals": actor_totals,
                "summary": {
                    "total_workstreams": int(model_df.shape[0]),
                    "total_hours": float(model_df["Hours"].sum()),
                    "total_cost": float(model_df["Total"].sum()),
                },
            }

            # save/overwrite
            st.session_state.saved_scenarios[scenario_name] = scenario_payload
            st.success(f"✅ Scenario '{scenario_name}' saved successfully!")

# --- Export all scenarios as JSON ---
if st.session_state.saved_scenarios:
    try:
        export_payload = json.dumps(st.session_state.saved_scenarios, indent=2)
        st.download_button(
            label="⬇️ Download All Scenarios (.json)",
            data=export_payload,
            file_name="saved_scenarios.json",
            mime="application/json"
        )
    except Exception:
        st.error("Unable to prepare download of scenarios.")

# --- Import scenarios (merge into memory) ---
uploaded_file = st.file_uploader("📂 Upload Scenarios (.json)", type=["json"])
if uploaded_file:
    try:
        loaded = json.load(uploaded_file)
        if isinstance(loaded, dict):
            st.session_state.saved_scenarios.update(loaded)
            st.success("✅ Scenarios imported successfully.")
        else:
            st.error("Uploaded JSON must contain a dict of scenarios.")
    except Exception as e:
        st.error(f"Failed to import JSON: {e}")

# --- List saved scenarios with preview, load and delete ---
if st.session_state.saved_scenarios:
    st.markdown("### 📁 Saved Scenarios")
    for sname, sdata in list(st.session_state.saved_scenarios.items()):
        with st.expander(f"📊 {sname}", expanded=False):
            summary = sdata.get("summary", {})
            st.write(f"**Total Workstreams:** {summary.get('total_workstreams','N/A')}")
            st.write(f"**Total Hours:** {summary.get('total_hours','N/A')}")
            total_cost_display = summary.get("total_cost", "N/A")
            if isinstance(total_cost_display, (int, float)):
                st.write(f"**Total Cost:** ${total_cost_display:,.2f}")
            else:
                st.write("**Total Cost:** N/A")

            # Rebuild dataframe safely from 'split' orient if present
            df_saved = None
            df_dict = sdata.get("dataframe", None)
            if isinstance(df_dict, dict) and "data" in df_dict and "columns" in df_dict:
                try:
                    df_saved = pd.DataFrame(data=df_dict["data"], columns=df_dict["columns"])
                except Exception:
                    df_saved = None

            if df_saved is not None and not df_saved.empty:
                st.dataframe(df_saved, use_container_width=True)
            else:
                st.write("_No preview available_")

            # Controls: Load and Delete
            col_load, col_delete = st.columns([1,1])
            with col_load:
                if st.button("🔁 Load", key=f"load__{sname}"):
                   try:
                       saved_inputs = sdata.get("inputs", {})
                       # Store which scenario to load, and inputs separately.
                       st.session_state["pending_load_scenario"] = saved_inputs
                       st.session_state["pending_scenario_name"] = sname
                       st.experimental_rerun()  # trigger rerun safely
                   except Exception as e:
                       st.error(f"Failed to load scenario: {e}")
 
            with col_delete:
                if st.button("🗑️ Delete", key=f"del__{sname}"):
                    del st.session_state.saved_scenarios[sname]
                    st.warning(f"Scenario '{sname}' deleted.")
                    st.experimental_rerun()
else:
    st.info("ℹ️ No scenarios saved yet.")


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
st.session_state["model_df"] = df
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



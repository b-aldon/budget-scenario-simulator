import streamlit as st
import pandas as pd
import json
import altair as alt

# ------------------------------------------------------------
# --- INITIAL SETUP & SAFE SCENARIO RESTORE ---
# ------------------------------------------------------------
if "pending_load_scenario" in st.session_state:
    try:
        pending_inputs = st.session_state.pop("pending_load_scenario", {})
        scenario_name = st.session_state.pop("pending_scenario_name", "Unknown")

        # restore session_state safely (only simple types)
        for key, val in pending_inputs.items():
            if key in st.session_state:
                st.session_state[key] = val

        st.toast(f"✅ Scenario '{scenario_name}' loaded successfully!")
    except Exception as e:
        st.warning(f"⚠️ Could not restore some scenario values: {e}")

st.set_page_config(page_title="Validation Budget Simulator", layout="wide")

# ------------------------------------------------------------
# --- HEADER ---
# ------------------------------------------------------------
st.title("📊 Validation Budget Simulator (Phase 2 – Option B)")

# ------------------------------------------------------------
# --- ACTORS & WORKSTREAMS ---
# ------------------------------------------------------------
actors = ["GRESB", "SAS New", "SAS Exp", "SAS Consl", "ESGDS"]

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

# ------------------------------------------------------------
# --- SIDEBAR: INPUTS ---
# ------------------------------------------------------------
st.sidebar.title("Workstreams, Hours & Team Allocation")
st.sidebar.markdown("Adjust the total hours and team allocation for each workstream below:")

allocation_data = []

for period, tasks in workstreams.items():
    with st.sidebar.expander(period, expanded=False):
        for task in tasks:
            st.markdown(f"**{task}**")
            hours = st.number_input(
                f"Hours", min_value=0, value=0, step=1, key=f"hours_{task}"
            )

            cols = st.columns(len(actors))
            percentages = []
            for i, actor in enumerate(actors):
                with cols[i]:
                    pct = st.number_input(
                        f"{actor} %",
                        min_value=0,
                        max_value=100,
                        value=0,
                        step=1,
                        key=f"{actor}_{task}",
                    )
                    percentages.append(pct)

            total_pct = sum(percentages)
            if total_pct > 100:
                st.warning(f"⚠️ Total allocation exceeds 100% for {task}.")

            allocation_data.append({
                "Period": period,
                "Workstream": task,
                "Hours": hours,
                **{actor: pct for actor, pct in zip(actors, percentages)},
            })

# --- COST INPUTS ---
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

# ------------------------------------------------------------
# --- MAIN CALCULATION ---
# ------------------------------------------------------------
def calc_cost(row):
    return (
        (row["Hours"] * row["GRESB"] / 100) * (gresb_cost / 160) +
        (row["Hours"] * row["SAS New"] / 100) * sas_new +
        (row["Hours"] * row["SAS Exp"] / 100) * sas_exp +
        (row["Hours"] * row["SAS Consl"] / 100) * sas_consl +
        (row["Hours"] * row["ESGDS"] / 100) * (esgds_cost / 2000)
    )

results = []
for period, tasks in workstreams.items():
    for task in tasks:
        hours = st.session_state.get(f"hours_{task}", 0)
        workload = {actor: st.session_state.get(f"{actor}_{task}", 0) for actor in actors}

        gresb_cost_calc = (hours * workload["GRESB"] / 100) * (gresb_cost / 160)
        sas_new_cost_calc = (hours * workload["SAS New"] / 100) * sas_new
        sas_exp_cost_calc = (hours * workload["SAS Exp"] / 100) * sas_exp
        sas_consl_cost_calc = (hours * workload["SAS Consl"] / 100) * sas_consl
        esgds_cost_calc = (hours * workload["ESGDS"] / 100) * (esgds_cost / 2000)

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
            "Total": total_cost,
        })

df = pd.DataFrame(results)
st.session_state["model_df"] = df

# ------------------------------------------------------------
# --- SCENARIO SAVE / LOAD (Fixed Version) ---
# ------------------------------------------------------------
st.markdown("## 💾 Scenario Management")

if "saved_scenarios" not in st.session_state:
    st.session_state.saved_scenarios = {}

def capture_current_state():
    state_snapshot = {}
    for k, v in st.session_state.items():
        if isinstance(v, (int, float, str, bool)):
            state_snapshot[k] = v
    return state_snapshot

with st.expander("💾 Save Current Scenario", expanded=False):
    scenario_name = st.text_input("Scenario Name", key="save_name_input")
    if st.button("Save Scenario", key="btn_save_scenario"):
        if df.empty:
            st.warning("⚠️ Please input values before saving a scenario.")
        elif not scenario_name.strip():
            st.warning("⚠️ Provide a valid scenario name.")
        else:
            actor_totals = {actor: float(df[actor].sum()) for actor in actors}
            scenario_payload = {
                "inputs": capture_current_state(),
                "dataframe": df.to_dict(orient="split"),
                "actor_totals": actor_totals,
                "summary": {
                    "total_workstreams": int(df.shape[0]),
                    "total_hours": float(df["Hours"].sum()),
                    "total_cost": float(df["Total"].sum()),
                },
            }
            st.session_state.saved_scenarios[scenario_name] = scenario_payload
            st.success(f"✅ Scenario '{scenario_name}' saved successfully!")

# --- Download all scenarios ---
if st.session_state.saved_scenarios:
    st.download_button(
        "⬇️ Download All Scenarios (.json)",
        data=json.dumps(st.session_state.saved_scenarios, indent=2),
        file_name="saved_scenarios.json",
        mime="application/json",
    )

# --- Upload scenarios ---
uploaded = st.file_uploader("📂 Upload Scenarios (.json)", type=["json"])
if uploaded:
    try:
        data = json.load(uploaded)
        if isinstance(data, dict):
            st.session_state.saved_scenarios.update(data)
            st.success("✅ Scenarios imported successfully.")
        else:
            st.error("Uploaded file must be a valid JSON dictionary.")
    except Exception as e:
        st.error(f"Failed to import: {e}")

# --- Scenario listing ---
if st.session_state.saved_scenarios:
    st.markdown("### 📁 Saved Scenarios")
    for sname, sdata in list(st.session_state.saved_scenarios.items()):
        with st.expander(f"📊 {sname}", expanded=False):
            summary = sdata.get("summary", {})
            st.write(f"**Workstreams:** {summary.get('total_workstreams','N/A')}")
            st.write(f"**Hours:** {summary.get('total_hours','N/A')}")
            total_cost_display = summary.get("total_cost", "N/A")
            st.write(f"**Total Cost:** ${total_cost_display:,.2f}" if isinstance(total_cost_display, (int,float)) else "N/A")

            # preview DataFrame
            df_dict = sdata.get("dataframe", {})
            try:
                df_saved = pd.DataFrame(data=df_dict["data"], columns=df_dict["columns"])
                st.dataframe(df_saved, use_container_width=True)
            except Exception:
                st.write("_No preview available_")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔁 Load", key=f"load_btn_{sname}"):
                    st.session_state["pending_load_scenario"] = sdata.get("inputs", {})
                    st.session_state["pending_scenario_name"] = sname
                    st.rerun()
            with c2:
                if st.button("🗑️ Delete", key=f"del_btn_{sname}"):
                    del st.session_state.saved_scenarios[sname]
                    st.warning(f"Deleted '{sname}'.")
                    st.rerun()
else:
    st.info("No scenarios saved yet.")

# ------------------------------------------------------------
# --- MAIN OUTPUTS ---
# ------------------------------------------------------------
st.markdown("## 🧮 Simulation Results")

# Cost Overview
st.markdown("### 📋 Cost Overview")
for period in workstreams.keys():
    period_df = df[df["Period"] == period]
    if period_df.empty:
        continue
    total_period_cost = period_df["Total"].sum()
    with st.expander(f"📁 {period} — Total: ${total_period_cost:,.0f}", expanded=False):
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

# ------------------------------------------------------------
# --- VISUALS ---
# ------------------------------------------------------------
st.markdown("#### 🥧 Cost Distribution by Actor")

actor_totals = {actor: df[actor].sum() for actor in actors}
pie_df = pd.DataFrame({"Actor": actor_totals.keys(), "Total Cost": actor_totals.values()})

color_scale = alt.Scale(
    domain=actors,
    range=["#00A36C", "#00BFFF", "#1E90FF", "#003366", "#800000"],
)

pie_chart = (
    alt.Chart(pie_df)
    .mark_arc(outerRadius=110)
    .encode(
        theta="Total Cost",
        color=alt.Color("Actor", scale=color_scale, legend=alt.Legend(title="Actor")),
        tooltip=["Actor", alt.Tooltip("Total Cost", format="$,.0f")],
    )
)
st.altair_chart(pie_chart, use_container_width=True)

st.markdown("#### 📅 Cost Distribution by Workstream Category")

stack_df = (
    df.groupby("Period")[actors]
    .sum()
    .reset_index()
    .melt(id_vars="Period", var_name="Actor", value_name="Cost")
)

period_order = ["Jan - March", "Apr - June", "July - August", "September", "October - December"]

stack_chart = (
    alt.Chart(stack_df)
    .mark_bar()
    .encode(
        x=alt.X("Period:N", sort=period_order),
        y=alt.Y("Cost:Q", title="Total Cost ($)", stack="normalize"),
        color=alt.Color("Actor", scale=color_scale),
        tooltip=["Period", "Actor", alt.Tooltip("Cost", format="$,.0f")],
    )
)
st.altair_chart(stack_chart, use_container_width=True)

# ------------------------------------------------------------
# --- SUMMARY METRICS ---
# ------------------------------------------------------------
st.markdown("### 🧾 Summary")
if not df.empty:
    num_ws = df["Workstream"].nunique()
    total_hours = df["Hours"].sum()
    total_cost = df["Total"].sum()
    total_gresb = df["GRESB"].sum()
    total_sas = df["SAS New"].sum() + df["SAS Exp"].sum() + df["SAS Consl"].sum()
    total_esgds = df["ESGDS"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("🧩 Workstreams", f"{num_ws}")
    c2.metric("⏱️ Total Hours", f"{total_hours:,.0f}")
    c3.metric("💵 Total Cost", f"${total_cost:,.2f}")

    st.markdown("---")
    st.markdown(f"**GRESB:** ${total_gresb:,.2f}")
    st.markdown(f"**SAS (Total):** ${total_sas:,.2f}")
    st.markdown(f"**ESGDS:** ${total_esgds:,.2f}")

    avg_cost_per_hour = total_cost / total_hours if total_hours else 0
    cost_per_ws = total_cost / num_ws if num_ws else 0
    gresb_share = (total_gresb / total_cost * 100) if total_cost else 0

    st.info(f"💡 Average Cost per Hour: ${avg_cost_per_hour:,.2f}")
    st.info(f"💡 Average Cost per Workstream: ${cost_per_ws:,.2f}")
    st.info(f"💡 GRESB Share of Total Cost: {gresb_share:.1f}%")
else:
    st.info("No data available yet.")
    


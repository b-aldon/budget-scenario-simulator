import streamlit as st
import pandas as pd
import json
import altair as alt

# ------------------------------------------------------------
# --- RESTORE SCENARIO IF NEEDED (auto-recalc on load) -------
# ------------------------------------------------------------
if "pending_load_scenario" in st.session_state:
    try:
        pending_inputs = st.session_state.pop("pending_load_scenario", {})
        scenario_name = st.session_state.pop("pending_scenario_name", "Unknown")

        # restore only simple session values
        for key, val in pending_inputs.items():
            if key in st.session_state:
                st.session_state[key] = val

        st.toast(f"✅ Scenario '{scenario_name}' loaded successfully!")
    except Exception as e:
        st.warning(f"⚠️ Error restoring scenario: {e}")

st.set_page_config(page_title="Validation Budget Simulator", layout="wide")

# ------------------------------------------------------------
# --- HEADER -------------------------------------------------
# ------------------------------------------------------------
st.title("📊 Validation Budget Simulator")

# ------------------------------------------------------------
# --- WORKSTREAMS & ACTORS ----------------------------------
# ------------------------------------------------------------
actors = ["GRESB", "SAS New", "SAS Exp", "SAS Consl", "ESGDS"]

workstreams = {
    "Jan - March": [
        "1. Validation Guidance Docs",
        "2. OAD",
        "3. Edge cases files",
        "4. LLM Prompting"
    ],
    "Apr - June": [
        "5. PSC & Vali admin",
        "6. PSC stock texts updates",
        "7. PSC validation (Primary)",
        "8. PSC validation (Secondary and QC)",
        "9. PSC notes prep for GRESB calls",
        "10. PSC call",
        "11. PSC Report generation",
        "12. Queries on Front",
        "13. LLM prompting",
        "14. SAS recruiting & training"
    ],
    "July - August": [
        "15. Validation Admin",
        "16. Primary Decisions",
        "17. Secondary decisions",
        "18. Same Doc ID - Consistency check",
        "19. YoY - Consistency check",
        "20. Validation Escalations"
    ],
    "September": [
        "21. All validation queries on Front",
        "22. Re-Validate from AC - Primary",
        "23. Re-Validate from AC - Secondary",
        "24. Free-Desubmissions",
        "25. Revert Validation error decisions",
        "26. Post AC Consistency check"
    ],
    "Oct - Dec": [
        "27. LLM Output refinement",
        "28. Compile cases for Outreach",
        "29. Post-Validation tasks"
    ]
}
# ------------------------------------------------------------
# --- SIDEBAR INPUTS ----------------------------------------
# ------------------------------------------------------------
st.sidebar.title("Workstreams, Hours & Team Allocation")
st.sidebar.markdown("Adjust hours and % allocation per workstream:")

allocation_data = []

for period, tasks in workstreams.items():
    with st.sidebar.expander(period):
        for task in tasks:
            row1 = st.columns([2,1])
            with row1[0]: st.markdown(f"**{task}**")
            with row1[1]:
                hours = st.number_input(
                    "Hours", min_value=0, step=1,
                    value=st.session_state.get(f"hours_{task}", 0),
                    key=f"hours_{task}", label_visibility="collapsed"
                )

            cols = st.columns(len(actors))
            pcts = []
            for idx, actor in enumerate(actors):
                with cols[idx]:
                    pct = st.number_input(
                        f"{actor} %", min_value=0, max_value=100, step=1,
                        value=st.session_state.get(f"{actor}_{task}", 0),
                        key=f"{actor}_{task}"
                    )
                    pcts.append(pct)

            if sum(pcts) > 100:
                st.warning(f"⚠️ Allocation >100% for {task}")

            allocation_data.append({
                "Period": period,
                "Workstream": task,
                "Hours": hours,
                **{actor: pct for actor, pct in zip(actors,pcts)}
            })

# Cost Inputs
st.sidebar.markdown("---")
st.sidebar.title("Cost Inputs")

with st.sidebar.expander("GRESB"):
    gresb_cost = st.number_input("Monthly Cost ($)", value=1000.0, min_value=0.0, step=100.0)

with st.sidebar.expander("SAS"):
    sas_new = st.number_input("New Reviewer ($/hr)", value=25.0)
    sas_exp = st.number_input("Experienced ($/hr)", value=40.0)
    sas_consl = st.number_input("Consultant ($/hr)", value=60.0)

with st.sidebar.expander("ESGDS"):
    esgds_cost = st.number_input("Annual Cost ($)", value=15000.0, min_value=0.0, step=500.0)

# ------------------------------------------------------------
# --- CALCULATIONS ------------------------------------------
# ------------------------------------------------------------
results = []
for period, tasks in workstreams.items():
    for task in tasks:
        h = st.session_state.get(f"hours_{task}", 0)
        w = {actor: st.session_state.get(f"{actor}_{task}", 0) for actor in actors}

        gresb_val = (h * w["GRESB"]/100) * (gresb_cost/160)
        sas_new_val = (h * w["SAS New"]/100) * sas_new
        sas_exp_val = (h * w["SAS Exp"]/100) * sas_exp
        sas_consl_val = (h * w["SAS Consl"]/100) * sas_consl
        esgds_val = (h * w["ESGDS"]/100) * (esgds_cost/2000)

        total = gresb_val + sas_new_val + sas_exp_val + sas_consl_val + esgds_val

        results.append({
            "Period": period, "Workstream": task, "Hours": h,
            "GRESB": gresb_val, "SAS New": sas_new_val,
            "SAS Exp": sas_exp_val, "SAS Consl": sas_consl_val,
            "ESGDS": esgds_val, "Total": total
        })

df = pd.DataFrame(results)
st.session_state["model_df"] = df

# ------------------------------------------------------------
# --- SCENARIO MANAGEMENT ------------------------------------
# ------------------------------------------------------------
st.markdown("## 💾 Scenario Management")

if "saved_scenarios" not in st.session_state:
    st.session_state.saved_scenarios = {}

def capture_current_state():
    snap = {}
    for k,v in st.session_state.items():
        if isinstance(v,(int,float,str,bool)):
            snap[k] = v
    return snap

with st.expander("💾 Save Scenario"):
    name = st.text_input("Scenario Name")
    if st.button("Save"):
        if not name.strip():
            st.warning("Enter name")
        else:
            payload = {
                "inputs": capture_current_state(),
                "dataframe": df.to_dict("split"),
                "summary": {
                    "hours": float(df["Hours"].sum()),
                    "cost": float(df["Total"].sum())
                }
            }
            st.session_state.saved_scenarios[name] = payload
            st.success(f"Saved '{name}'")

# Download all
if st.session_state.saved_scenarios:
    st.download_button(
        "⬇️ Download All Scenarios",
        data=json.dumps(st.session_state.saved_scenarios,indent=2),
        file_name="scenarios.json"
    )

# Upload
upload = st.file_uploader("📂 Upload Scenarios", type="json")
if upload:
    try:
        data = json.load(upload)
        st.session_state.saved_scenarios.update(data)
        st.success("Imported!")
    except:
        st.error("Bad file")

# List + Load/Delete
if st.session_state.saved_scenarios:
    st.markdown("### 📁 Saved Scenarios")
    for s, payload in st.session_state.saved_scenarios.items():
        with st.expander(s):
            st.write(f"Hours: {payload['summary']['hours']:.0f}")
            st.write(f"Cost: ${payload['summary']['cost']:,.0f}")
            if st.button(f"Load {s}"):
                st.session_state["pending_load_scenario"] = payload["inputs"]
                st.session_state["pending_scenario_name"] = s
                st.rerun()
            if st.button(f"Delete {s}"):
                del st.session_state.saved_scenarios[s]
                st.rerun()

# ------------------------------------------------------------
# --- RESULTS TABLES -----------------------------------------
# ------------------------------------------------------------
st.markdown("## 🧮 Simulation Results")

for period in workstreams.keys():
    # select rows for this period
    block = df[df["Period"] == period].copy()
    if block.empty:
        continue

    # --- Recompute per-row GRESB hours from the sidebar allocation keys ---
    # Expect sidebar keys like "GRESB_1. Validation Guidance Docs"
    def compute_gresb_hours(row):
        task = row["Workstream"]
        pct = st.session_state.get(f"GRESB_{task}", 0)  # percent allocated to GRESB
        try:
            hrs = float(row.get("Hours", 0))
        except Exception:
            hrs = 0.0
        return hrs * (pct / 100.0)

    block["GRESB_Hours"] = block.apply(compute_gresb_hours, axis=1)

    # --- SAS cost per row is already present in the df (SAS New/Exp/Consl) ---
    # total cost and sas cost for the period:
    total_cost = block["Total"].sum()
    sas_cost = block[["SAS New", "SAS Exp", "SAS Consl"]].sum().sum()

    # total GRESB hours for the period:
    total_gresb_hours = block["GRESB_Hours"].sum()

    # --- Prepare display table: replace 'GRESB' cost column with hours column ---
    display_block = block.copy()
    # remove Period column and index
    display_block = display_block.drop(columns=["Period"], errors="ignore").reset_index(drop=True)

    # Remove the old GRESB cost column if present and insert the hours column in its place
    if "GRESB" in display_block.columns:
        display_block = display_block.drop(columns=["GRESB"], errors="ignore")
    # place GRESB_Hours next to Hours column
    cols = ["Workstream", "Hours", "GRESB_Hours", "SAS New", "SAS Exp", "SAS Consl", "ESGDS", "Total"]
    # keep only existing columns in that order
    display_cols = [c for c in cols if c in display_block.columns]
    display_block = display_block[display_cols]

    # rename column for clarity
    display_block = display_block.rename(columns={"GRESB_Hours": "GRESB (hrs)"})

    # --- Expander header with totals ---
    header = (
        f"{period} — Total Cost: ${total_cost:,.0f} | "
        f"SAS Cost: ${sas_cost:,.0f} | "
        f"GRESB Hours: {total_gresb_hours:,.0f}"
    )

    with st.expander(header, expanded=False):
        st.dataframe(
            display_block.style.format({
                "Hours": "{:.0f}",
                "GRESB (hrs)": "{:.0f}",            # hours formatting
                "SAS New": "${:,.0f}",
                "SAS Exp": "${:,.0f}",
                "SAS Consl": "${:,.0f}",
                "ESGDS": "${:,.0f}",
                "Total": "${:,.0f}"
            }),
            use_container_width=True
        )

# ------------------------------------------------------------
# --- CHARTS -------------------------------------------------
# ------------------------------------------------------------
st.markdown("#### 🥧 Cost by Actor")
actor_totals = {a: df[a].sum() for a in actors}
pie_df = pd.DataFrame({"Actor": list(actor_totals.keys()), "Cost": list(actor_totals.values())})

pie = alt.Chart(pie_df).mark_arc().encode(
    theta="Cost:Q",
    color=alt.Color("Actor:N", legend=alt.Legend(title="Actor")),
    tooltip=["Actor", alt.Tooltip("Cost", format="$,.0f")]
)
st.altair_chart(pie, use_container_width=True)

st.markdown("#### 📅 Cost by Period (stacked)")

# Group by period and sum actor columns
period_sum = df.groupby("Period")[actors].sum().reset_index()

# Melt into long format safely
stack = period_sum.melt(
    id_vars=["Period"],
    value_vars=actors,
    var_name="Actor",
    value_name="Cost"
)

# Optional: ensure periods are in your desired chronological order
period_order = ["Jan - March", "Apr - June", "July - August", "September", "October - December"]
stack["Period"] = pd.Categorical(stack["Period"], categories=period_order, ordered=True)

stack_chart = alt.Chart(stack).mark_bar().encode(
    x=alt.X("Period:N", sort=period_order, title="Period"),
    y=alt.Y("Cost:Q", title="Total Cost ($)"),
    color=alt.Color("Actor:N", legend=alt.Legend(title="Actor")),
    tooltip=["Period", "Actor", alt.Tooltip("Cost", format="$,.0f")]
).properties(height=400)

st.altair_chart(stack_chart, use_container_width=True)


# ------------------------------------------------------------
# --- SUMMARY METRICS ---------------------------------------
# ------------------------------------------------------------
st.markdown("### 🧾 Summary")
if not df.empty:
    total_hours = df["Hours"].sum()
    total_cost = df["Total"].sum()

    total_gresb = df["GRESB"].sum()
    total_sas = df["SAS New"].sum() + df["SAS Exp"].sum() + df["SAS Consl"].sum()
    total_esgds = df["ESGDS"].sum()

    # ---- Display Total Hours & Total Cost side-by-side ----
    colA, colB = st.columns(2)
    with colA:
        st.metric("⏱️ Total Hours", f"{total_hours:,.0f}")
    with colB:
        st.metric("💵 Total Cost", f"${total_cost:,.2f}")

    st.markdown("---")

    # ---- Stat 1: Total SAS Cost ----
    st.info(f"💡 **Total SAS Cost:** ${total_sas:,.2f}")

    # ---- Stat 2: Most expensive workstream ----
    max_row = df.loc[df["Total"].idxmax()]
    most_expensive_ws = max_row["Workstream"]
    most_expensive_ws_cost = max_row["Total"]
    st.info(f"💡 **Most Expensive Workstream:** {most_expensive_ws} (${most_expensive_ws_cost:,.2f})")

else:
    st.info("No data available yet.")


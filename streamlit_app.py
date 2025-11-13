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
# Simplified/renamed actors for better alignment
actors = ["GRESB", "GRESB N", "SAS New", "SAS Exp", "SAS Con", "ESGDS"]

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
            row1 = st.columns([2, 1])
            with row1[0]:
                st.markdown(f"**{task}**")
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
                **{actor: pct for actor, pct in zip(actors, pcts)}
            })

# ------------------------------------------------------------
# --- COST INPUTS --------------------------------------------
# ------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.title("Cost Inputs")

# GRESB N (New) — Monthly rate
with st.sidebar.expander("GRESB N (monthly)"):
    gresb_new_cost = st.number_input(
        "GRESB N Monthly Cost ($)", value=1000.0, min_value=0.0, step=100.0
    )

# SAS team — hourly rates
with st.sidebar.expander("SAS (hourly rates)"):
    sas_new = st.number_input("SAS New ($/hr)", value=25.0)
    sas_exp = st.number_input("SAS Exp ($/hr)", value=40.0)
    sas_con = st.number_input("SAS Con ($/hr)", value=60.0)

# ESGDS — annual rate
with st.sidebar.expander("ESGDS (annual)"):
    esgds_cost = st.number_input(
        "ESGDS Annual Cost ($)", value=15000.0, min_value=0.0, step=500.0
    )

# ------------------------------------------------------------
# --- CALCULATIONS ------------------------------------------
# ------------------------------------------------------------
results = []
for period, tasks in workstreams.items():
    for task in tasks:
        h = st.session_state.get(f"hours_{task}", 0)
        w = {actor: st.session_state.get(f"{actor}_{task}", 0) for actor in actors}

        # Costs
        gresb_n_val = (h * w.get("GRESB N", 0) / 100) * (gresb_new_cost / 160)  # Monthly → hourly
        gresb_val = 0.0  # GRESB (experienced) → no cost, hours only

        sas_new_val = (h * w.get("SAS New", 0) / 100) * sas_new
        sas_exp_val = (h * w.get("SAS Exp", 0) / 100) * sas_exp
        sas_con_val = (h * w.get("SAS Con", 0) / 100) * sas_con
        esgds_val = (h * w.get("ESGDS", 0) / 100) * (esgds_cost / 2000)

        total = gresb_val + gresb_n_val + sas_new_val + sas_exp_val + sas_con_val + esgds_val

        results.append({
            "Period": period,
            "Workstream": task,
            "Hours": h,
            "GRESB": gresb_val,
            "GRESB N": gresb_n_val,
            "SAS New": sas_new_val,
            "SAS Exp": sas_exp_val,
            "SAS Con": sas_con_val,
            "ESGDS": esgds_val,
            "Total": total
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
    for k, v in st.session_state.items():
        if isinstance(v, (int, float, str, bool)):
            snap[k] = v
    return snap

with st.expander("💾 Save Scenario"):
    name = st.text_input("Scenario Name")
    if st.button("Save"):
        if not name.strip():
            st.warning("Enter a scenario name")
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
            st.success(f"Saved '{name}' successfully!")

# Download all
if st.session_state.saved_scenarios:
    st.download_button(
        "⬇️ Download All Scenarios",
        data=json.dumps(st.session_state.saved_scenarios, indent=2),
        file_name="scenarios.json"
    )

# Upload scenarios
upload = st.file_uploader("📂 Upload Scenarios", type="json")
if upload:
    try:
        data = json.load(upload)
        st.session_state.saved_scenarios.update(data)
        st.success("Imported successfully!")
    except:
        st.error("Invalid file format")

# List saved scenarios
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

    # --- Recompute per-row GRESB & GRESB N hours from the sidebar allocation keys ---
    def compute_gresb_hours(row, actor_name):
        task = row["Workstream"]
        pct = st.session_state.get(f"{actor_name}_{task}", 0)
        try:
            hrs = float(row.get("Hours", 0))
        except Exception:
            hrs = 0.0
        return hrs * (pct / 100.0)

    block["GRESB_Hours"] = block.apply(lambda r: compute_gresb_hours(r, "GRESB"), axis=1)
    block["GRESB_N_Hours"] = block.apply(lambda r: compute_gresb_hours(r, "GRESB N"), axis=1)

    # --- SAS cost per row already present in df ---
    total_cost = block["Total"].sum()
    sas_cost = block[["SAS New", "SAS Exp", "SAS Con"]].sum().sum()

    # total GRESB hours for the period:
    total_gresb_hours = block["GRESB_Hours"].sum() + block["GRESB_N_Hours"].sum()

    # --- Prepare display table: include both GRESB hour columns and SAS/ESGDS costs ---
    display_block = block.copy()
    display_block = display_block.drop(columns=["Period"], errors="ignore").reset_index(drop=True)

    # remove GRESB cost columns if they exist
    display_block = display_block.drop(columns=["GRESB", "GRESB N"], errors="ignore")

    # define column order for display
    cols = [
        "Workstream", "Hours",
        "GRESB_Hours", "GRESB_N_Hours",
        "SAS New", "SAS Exp", "SAS Con",
        "ESGDS", "Total"
    ]
    display_cols = [c for c in cols if c in display_block.columns]
    display_block = display_block[display_cols]

    display_block = display_block.rename(columns={
        "GRESB_Hours": "GRESB (hrs)",
        "GRESB_N_Hours": "GRESB N (hrs)"
    })

    # --- Expander header with totals ---
    header = (
        f"{period} — Total Cost: ${total_cost:,.0f} | "
        f" SAS_ Total Cost: ${sas_cost:,.0f} | "
        f"GRESB Total Hours: {total_gresb_hours:,.0f}"
    )

    with st.expander(header, expanded=False):
        st.dataframe(
            display_block.style.format({
                "Hours": "{:.0f}",
                "GRESB (hrs)": "{:.0f}",
                "GRESB N (hrs)": "{:.0f}",
                "SAS New": "${:,.0f}",
                "SAS Exp": "${:,.0f}",
                "SAS Con": "${:,.0f}",
                "ESGDS": "${:,.0f}",
                "Total": "${:,.0f}"
            }),
            use_container_width=True
        )

# ------------------------------------------------------------
# --- CHARTS -------------------------------------------------
# ------------------------------------------------------------
st.markdown("#### 🥧 Cost by Actor")

actor_totals = {a: df[a].sum() for a in ["GRESB", "GRESB N", "SAS New", "SAS Exp", "SAS Con", "ESGDS"]}
pie_df = pd.DataFrame({"Actor": list(actor_totals.keys()), "Cost": list(actor_totals.values())})

pie = alt.Chart(pie_df).mark_arc().encode(
    theta="Cost:Q",
    color=alt.Color("Actor:N", legend=alt.Legend(title="Actor")),
    tooltip=["Actor", alt.Tooltip("Cost", format="$,.0f")]
)
st.altair_chart(pie, use_container_width=True)

st.markdown("#### 📅 Cost by Period (stacked)")

# Group by period and sum actor columns
actors_for_charts = ["GRESB", "GRESB N", "SAS New", "SAS Exp", "SAS Con", "ESGDS"]
period_sum = df.groupby("Period")[actors_for_charts].sum().reset_index()

# Melt into long format safely
stack = period_sum.melt(
    id_vars=["Period"],
    value_vars=actors_for_charts,
    var_name="Actor",
    value_name="Cost"
)

# Optional: ensure periods are in your desired chronological order
period_order = ["Jan - March", "Apr - June", "July - August", "September", "Oct - Dec"]
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
    # --- Basic totals ---
    total_hours = df["Hours"].sum()

    # --- Corrected Total Cost Calculation (keeps ESGDS fixed) ---
    total_cost = (
        df.get("GRESB", 0).sum() +
        df.get("GRESB N", 0).sum() +
        df.get("SAS New", 0).sum() +
        df.get("SAS Exp", 0).sum() +
        df.get("SAS Con", 0).sum()
    )
    total_cost += esgds_cost  # add fixed ESGDS cost manually

    # --- GRESB Exp total hours (experienced staff hours only) ---
    total_gresb_exp_hours = 0.0
    for task in df["Workstream"]:
        hrs = st.session_state.get(f"hours_{task}", 0)
        pct_exp = st.session_state.get(f"GRESB_{task}", 0)
        total_gresb_exp_hours += hrs * (pct_exp / 100.0)

    # --- GRESB N total hours & FTEs (new hires / interns) ---
    total_gresbN_hours = 0.0
    for task in df["Workstream"]:
        hrs = st.session_state.get(f"hours_{task}", 0)
        pct_new = st.session_state.get(f"GRESB N_{task}", 0)
        total_gresbN_hours += hrs * (pct_new / 100.0)

    # FTE formula: 40 hrs/week * 15 weeks
    gresbN_fte = total_gresbN_hours / (40 * 15) if (40 * 15) != 0 else 0.0

    # --- SAS costs breakdown ---
    total_sas = df.get("SAS New", 0).sum() + df.get("SAS Exp", 0).sum() + df.get("SAS Con", 0).sum()
    sas_new_cost = df.get("SAS New", 0).sum()
    sas_exp_cost = df.get("SAS Exp", 0).sum()
    sas_con_cost = df.get("SAS Con", 0).sum()

    # ---- Layout: two columns ----
    left_col, right_col = st.columns(2)

    # LEFT: Hours metrics
    with left_col:
        st.metric("⏱️ Total Hours", f"{total_hours:,.0f}")
        st.markdown(
            f"""
            <div style="font-size:14px; line-height:1.5;">
              <strong>GRESB Exp Hours:</strong> {total_gresb_exp_hours:,.0f}<br>
              <strong>GRESB N Hours:</strong> {total_gresbN_hours:,.0f} &nbsp;&nbsp;|&nbsp;&nbsp;
              <strong>FTEs:</strong> {gresbN_fte:.2f}
            </div>
            """,
            unsafe_allow_html=True
        )

    # RIGHT: Cost metrics
    with right_col:
        st.metric("💵 Total Cost", f"${total_cost:,.2f}")
        st.markdown(
            f"""
            <div style="font-size:14px; line-height:1.5;">
              <strong>Total SAS Cost:</strong> ${total_sas:,.2f}<br>
              <strong>SAS New:</strong> ${sas_new_cost:,.2f} &nbsp;&nbsp;|&nbsp;&nbsp;
              <strong>SAS Exp:</strong> ${sas_exp_cost:,.2f} &nbsp;&nbsp;|&nbsp;&nbsp;
              <strong>SAS Con:</strong> ${sas_con_cost:,.2f}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ---- Stat 1: Most expensive workstream ----
    # ---- Stat 1: Most expensive workstream (excluding ESGDS) ----
try:
    # Compute effective total per workstream excluding ESGDS
    df["Effective_Total"] = (
        df.get("GRESB", 0) +
        df.get("GRESB N", 0) +
        df.get("SAS New", 0) +
        df.get("SAS Exp", 0) +
        df.get("SAS Con", 0)
    )

    max_idx = df["Effective_Total"].idxmax()
    max_row = df.loc[max_idx]
    most_expensive_ws = max_row["Workstream"]
    most_expensive_ws_cost = max_row["Effective_Total"]

    st.info(f"💡 **Most Expensive Workstream:** {most_expensive_ws} — ${most_expensive_ws_cost:,.2f}")

except Exception:
    st.info("💡 **Most Expensive Workstream:** N/A")

    # ---- Stat 2: Total PSC cost (excluding ESGDS portion) ----
    psc_tasks = [
        "5. PSC & Vali admin",
        "6. PSC stock texts updates",
        "7. PSC validation (Primary)",
        "8. PSC validation (Secondary and QC)",
        "9. PSC notes prep for GRESB calls",
        "10. PSC call",
        "11. PSC Report generation"
    ]

    # Exclude ESGDS contribution for these tasks
    total_psc_cost = (
        df[df["Workstream"].isin(psc_tasks)][["GRESB", "GRESB N", "SAS New", "SAS Exp", "SAS Con"]]
        .sum(axis=1)
        .sum()
    )
    st.info(f"💡 **Total PSC Cost (excluding ESGDS):** ${total_psc_cost:,.2f}")

else:
    st.info("No data available yet.")

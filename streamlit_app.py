import streamlit as st
import pandas as pd

st.set_page_config(page_title="Validation Budget Simulator", layout="wide")

# --- Header Section ---
from PIL import Image
import requests
from io import BytesIO

# Load GRESB logo directly from the web

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
st.markdown("## 💰 Validation Budget Simulator")

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
df.index = df.index + 1  # Start numbering at 1

# --- Collapsible Workstream Cards by Period ---
for period in df["Period"].unique():
    with st.expander(f"📅 {period}", expanded=True):
        period_df = df[df["Period"] == period].copy()

        # Round numeric columns for readability
        numeric_cols = period_df.select_dtypes(include=["float", "int"]).columns
        period_df[numeric_cols] = period_df[numeric_cols].round(2)

        # Display tidy dataframe
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

        # Subtotal summary per period
        total_cost = period_df["Total"].sum()
        total_hours = period_df["Hours"].sum()
        st.markdown(
            f"**Subtotal for {period}:** 💰 ${total_cost:,.0f} 🕒 {total_hours:,.0f} hours"
        )

st.divider()

# --- Charts: Pie + Stacked Bar (Altair) ---
import altair as alt

# Guard: if df is empty, show a message
if df.empty:
    st.info("Enter workstream hours and allocations in the sidebar to generate charts.")
else:
    # ---------- Pie chart data ----------
    actor_totals = {
        "GRESB": df["GRESB"].sum(),
        "SAS New": df["SAS New"].sum(),
        "SAS Exp": df["SAS Exp"].sum(),
        "SAS Consl": df["SAS Consl"].sum(),
        "ESGDS": df["ESGDS"].sum()
    }

    pie_df = pd.DataFrame({
        "Actor": list(actor_totals.keys()),
        "Total Cost": list(actor_totals.values())
    })

    # color scheme (GRESB green, SAS shades of blue, ESGDS pink)
    color_scale = alt.Scale(
        domain=["GRESB", "SAS New", "SAS Exp", "SAS Consl", "ESGDS"],
        range=["#2E8B57", "#A7C7E7", "#4682B4", "#1E3A8A", "#FF69B4"]
    )

    st.markdown("### 🥧 Cost Distribution by Actor")
    pie_chart = (
        alt.Chart(pie_df)
        .mark_arc(outerRadius=120)
        .encode(
            theta=alt.Theta(field="Total Cost", type="quantitative"),
            color=alt.Color(field="Actor", type="nominal", scale=color_scale, legend=alt.Legend(title="Actor")),
            tooltip=[
                alt.Tooltip("Actor", title="Team"),
                alt.Tooltip("Total Cost", title="Total Cost", format=",.2f")
            ]
        )
        .properties(width=400, height=350)
    )
    st.altair_chart(pie_chart, use_container_width=True)

    st.markdown("---")

    # ---------- Stacked bar: cost per period ----------
    st.markdown("### 📅 Cost Distribution by Workstream Category (stacked)")

    # Aggregate by Period
    # Ensure the actor columns exist and are numeric
    period_df = df.groupby("Period")[["GRESB", "SAS New", "SAS Exp", "SAS Consl", "ESGDS"]].sum().reset_index()

    # Melt for Altair stacked bars
    period_melted = period_df.melt(id_vars="Period", var_name="Actor", value_name="Total Cost")

    # Define ordering for Periods to ensure chronological bars
    period_order = ["Jan - March", "Apr - June", "July - August", "September", "October - December"]

    stacked_bar = (
        alt.Chart(period_melted)
        .mark_bar()
        .encode(
            x=alt.X("Period:N", sort=period_order, title="Workstream Category"),
            y=alt.Y("Total Cost:Q", title="Total Cost ($)"),
            color=alt.Color("Actor:N", scale=color_scale, legend=alt.Legend(title="Actor")),
            tooltip=[
                alt.Tooltip("Period", title="Category"),
                alt.Tooltip("Actor", title="Team"),
                alt.Tooltip("Total Cost", title="Cost ($)", format=",.2f")
            ]
        )
        .properties(width=700, height=420)
    )

    st.altair_chart(stacked_bar, use_container_width=True)

# --- Validation Summary Section ---
st.markdown("## 🧾 Validation Summary")

if df.empty:
    st.info("No data available yet — please input hours and allocations in the sidebar.")
else:
    # --- Core summary metrics ---
    num_workstreams = df["Workstream"].nunique()
    total_hours = df["Hours"].sum()
    total_cost = df["Total"].sum()

    total_gresb = df["GRESB"].sum()
    total_sas_new = df["SAS New"].sum()
    total_sas_exp = df["SAS Exp"].sum()
    total_sas_consl = df["SAS Consl"].sum()
    total_esgds = df["ESGDS"].sum()

    total_sas = total_sas_new + total_sas_exp + total_sas_consl

    # --- Summary Cards Layout ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🧩 Number of Workstreams", f"{num_workstreams}")
    with col2:
        st.metric("⏱️ Total Hours", f"{total_hours:,.0f}")
    with col3:
        st.metric("💵 Total Cost", f"${total_cost:,.2f}")

    st.markdown("---")
    st.markdown("### 💼 Cost Split by Team")

    colA, colB, colC = st.columns(3)
    with colA:
        st.markdown(f"**GRESB:** ${total_gresb:,.2f}")
    with colB:
        st.markdown(
            f"**SAS:** ${total_sas:,.2f}  \n"
            f" • SAS New: ${total_sas_new:,.2f}  \n"
            f" • SAS Exp: ${total_sas_exp:,.2f}  \n"
            f" • SAS Consl: ${total_sas_consl:,.2f}"
        )
    with colC:
        st.markdown(f"**ESGDS:** ${total_esgds:,.2f}")

    st.markdown("---")

    # --- Enhancement: highlight ratios and insights ---
    avg_cost_per_hour = total_cost / total_hours if total_hours > 0 else 0
    highest_cost_actor = max(
        {
            "GRESB": total_gresb,
            "SAS": total_sas,
            "ESGDS": total_esgds,
        },
        key=lambda x: {
            "GRESB": total_gresb,
            "SAS": total_sas,
            "ESGDS": total_esgds,
        }[x],
    )

    st.markdown("### 📊 Key Insights")
    st.info(
        f"💡 **Average Cost per Hour:** ${avg_cost_per_hour:,.2f}  \n"
        f"🏆 **Highest Contributor:** {highest_cost_actor}"
    )

    st.success("✅ Validation cost simulation completed successfully!")


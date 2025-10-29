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
st.subheader("📊 Validation Budget Simulator")

if not df.empty:
    # Clean up table grouping
    df_display = df.copy()
    df_display.loc[df_display["Period"].duplicated(), "Period"] = ""
    st.dataframe(df_display.style.format({"Estimated Cost ($)": "${:,.2f}"}), use_container_width=True)

    total_budget = df["Estimated Cost ($)"].sum()
    st.markdown(f"### 💵 Total Estimated Budget: **${total_budget:,.2f}**")

else:
    st.info("Please enter workstream hours and allocation details on the sidebar to view results.")



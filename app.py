import streamlit as st
import pyodbc
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Live MySQL Dashboard", layout="wide")

st.markdown(
    """
    <style>
    /* Subtle professional pattern background */
    .stApp {
        background-image: url("image.png");
        background-size: auto;
        background-repeat: repeat;
        background-attachment: fixed;
        background-color: #f8f8f8;
        background-blend-mode: lighten;
    }

    .stApp > .main > div {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 1rem;
        border-radius: 1rem;
    }

    .stMetric > div {
        background-color: rgba(255, 255, 255, 0.85) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    /* Dashboard title color */
    h1 {
        color: #C32148 !important;
        font-weight: 800;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("SERVICE CALL DASHBOARD")

# ODBC connection
def get_connection():
    return pyodbc.connect(
        "DSN=CRM - ODBC Connector;"
        "UID=hive_user;"
        "PWD=Cargen@2026;"
    )

# Live data fetch
@st.cache_data(ttl=30)  # refresh every 30 seconds
def load_data():
    conn = get_connection()
    query = """
    SELECT T0.id ,
    T0.`inquiry_id`,
    T0.serviceCallNumber,
    T0.serviceCallID AS serviceCallId,
    T0.Branch AS  ServiceBranch,
    T0.`servicedetail_id`,
    T0.technicianStatus,
    T0.createdOn,
    T0.createdBy,
    T0.isClosed,
    T0.closedOn,
    T0.closedBy,
    T0.serviceDescription,
    T0.remarks,
    T0.`technician_remarks`,
    T0.`final_remarks`,
    T0.`technician_completed_at`,
    T0.`completed_at`,
    T0.`created_at`,
    T0.`updated_at`,
    T1.`user_id` as technician_id,
    T2.`first_name`,
    T2.`last_name`,
    CONCAT(T2.`first_name`, ' ', T2.`last_name`) AS technicianName,
    T2.branch as technicianBranch,
    T3.`customer_id`,
    T4.`customer_name`
    
    
FROM cargenhive.services T0
LEFT JOIN cargenhive.`service_assignments` T1 ON T0.id = T1.`service_id`
LEFT JOIN cargenhive.`service_technicians` T2 ON  T1.`user_id` = T2.id
LEFT JOIN cargenhive.`product_inquiries` T3 ON T0.`inquiry_id` = T3.id
LEFT JOIN cargenhive.customers T4 ON T3.`customer_id` = T4.id
"""
    df = pd.read_sql(query, conn)
    conn.close()
    return df

df = load_data()
# st.dataframe(df, use_container_width=True)

# Ensure datetime
df["created_at"] = pd.to_datetime(df["created_at"])

# Today filter
today = pd.Timestamp.now().normalize()
df_today = df[df["created_at"].dt.normalize() == today]


# st.sidebar.header("Filters")

# branch_filter = st.sidebar.multiselect(
#     "Service Branch",
#     options=df["ServiceBranch"].dropna().unique()
# )

# if branch_filter:
#     df = df[df["ServiceBranch"].isin(branch_filter)]
#     df_today = df_today[df_today["ServiceBranch"].isin(branch_filter)]


# ---- Overall KPIs ----
total_service_calls = df["serviceCallId"].dropna().nunique()
total_closed = df[df["isClosed"] == 1]["serviceCallId"].dropna().nunique()
total_open = df[df["isClosed"] == 0]["serviceCallId"].dropna().nunique()
total_completed_but_open = df[df["technicianStatus"] == 1][df["isClosed"] == 0]["serviceCallId"].dropna().nunique()

# ---- Today KPIs ----
today_service_calls = df_today["serviceCallId"].dropna().nunique()
today_closed = df_today[df_today["isClosed"] == 1]["serviceCallId"].dropna().nunique()
today_open = df_today[df_today["isClosed"] == 0]["serviceCallId"].dropna().nunique()
today_completed_but_open = df_today[df_today["technicianStatus"] == 1][df_today["isClosed"] == 0]["serviceCallId"].dropna().nunique()

# ---- Customer KPIs ----
total_customers = (df[df["serviceCallId"].notna()]["customer_id"].dropna().nunique())
today_customers = df_today[df_today["serviceCallId"].notna()]["customer_id"].dropna().nunique()

st.markdown(
    """
    <style>
    /* Metric container */
    .stMetric > div {
        border-radius: 1rem !important;
        padding: 1rem !important;
        background-color: #ffffff !important;
        box-shadow: 0px 0px 4px rgba(255,0,0,0.2) !important;
    }

    /* Metric label */
    .stMetric label {
        color: #555555 !important;
        font-weight: 600 !important;
    }

    /* Metric value */
    .stMetric [data-testid="stMetricValue"] {
        
        font-weight: 800 !important;
    }

    /* Metric delta (optional, keeps it clean) */
    .stMetric [data-testid="stMetricDelta"] {
        font-weight: 600 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

    
# st.subheader(" Service Call KPIs")

col1, col2, col3, col4, col5= st.columns(5)
col1.metric("Total Jobs Done", total_service_calls)
col2.metric("Closed Jobs (Overall)", total_closed)
col3.metric("Completed but Open(Overall)", total_completed_but_open)
col4.metric("Open Jobs(Overall)", total_open)
col5.metric("Total Customers", total_customers)

col6, col7, col8, col9, col10 = st.columns(5)
col6.metric("Services Today", today_service_calls)
col7.metric("Services Pending", today_open)
col8.metric("Services Completed Today but Open", today_completed_but_open)
col9.metric("Services Closed", today_closed)
col10.metric("Customers Today", today_customers)



st.markdown(
    """
    <style>
    /* Dashboard title color */
    h3 {
        color: #C32148 !important;
        font-weight: 800;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.subheader("👨‍🔧 Service Calls per Technician (Today)")

# ===============================
# ONE BLOCK – TODAY (DISTINCT)
# ===============================

today = df_today[df_today["serviceCallId"].notna()].copy()

if not today.empty:

    # --- Base: DISTINCT service calls today ---
    base = (
        today.groupby("technicianName")
        .agg(Total_Service_Calls=("serviceCallId", "nunique"))
    )

    # --- Closed today (from isClosed ONLY) ---
    closed = (
        today[today["isClosed"] == 1]
        .groupby("technicianName")
        .agg(Closed=("serviceCallId", "nunique"))
    )

    # --- Technician status breakdown today ---
    status = (
        today.groupby(["technicianName", "technicianStatus"])
        .agg(serviceCalls=("serviceCallId", "nunique"))
        .unstack(fill_value=0)
    )

    # 🔑 Flatten MultiIndex columns
    status.columns = status.columns.droplevel(0)

    # Rename technicianStatus codes
    status = status.rename(columns={
        0: "Open",
        1: "Completed",
        2: "On Hold",
        3: "Escalated"
    })

    # --- Merge everything ---
    final_today = (
        base
        .join(status, how="left")
        .join(closed, how="left")
        .fillna(0)
        .astype(int)
    )
    final_today.index.name = "Technician"

    # Ensure all columns always exist
    for col in ["Open", "Completed", "On Hold", "Escalated", "Closed"]:
        if col not in final_today.columns:
            final_today[col] = 0

    # Order columns
    final_today = final_today[
        ["Total_Service_Calls", "Open", "Completed", "On Hold", "Escalated", "Closed"]
    ]
    
 
    # Display
    st.dataframe(
        final_today.sort_values("Total_Service_Calls", ascending=False),
        use_container_width=True
    )

else:
    st.info("No service calls created today.")


st.subheader("👨‍🔧 Service Calls per Technician (Overall)")

# ===============================
# ONE BLOCK – DISTINCT & SAFE
# ===============================

data = df[df["serviceCallId"].notna()].copy()

# --- Base: DISTINCT service calls ---
base = (
    data.groupby("technicianName")
    .agg(Total_Service_Calls=("serviceCallId", "nunique"))
)

# --- Closed (from isClosed ONLY) ---
closed = (
    data[data["isClosed"] == 1]
    .groupby("technicianName")
    .agg(Closed=("serviceCallId", "nunique"))
)

# --- Technician status breakdown ---
status = (
    data.groupby(["technicianName", "technicianStatus"])
    .agg(serviceCalls=("serviceCallId", "nunique"))
    .unstack(fill_value=0)
)

# 🔑 FLATTEN MultiIndex columns
status.columns = status.columns.droplevel(0)

# Rename technicianStatus codes
status = status.rename(columns={
    0: "Open",
    1: "Completed",
    2: "On Hold",
    3: "Escalated"
})

# --- Merge everything ---
final = (
    base
    .join(status, how="left")
    .join(closed, how="left")
    .fillna(0)
    .astype(int)
)
final.index.name = "Technician"


# Ensure all columns always exist
for col in ["Open", "Completed", "On Hold", "Escalated", "Closed"]:
    if col not in final.columns:
        final[col] = 0

# Order columns
final = final[
    ["Total_Service_Calls", "Open", "Completed", "On Hold", "Escalated", "Closed"]
]


# --- Display ---
st.dataframe(
    final.sort_values("Total_Service_Calls", ascending=False),
    use_container_width=True
)

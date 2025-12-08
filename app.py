import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import altair as alt
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Netcreators Automation",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Festive Diwali Marquee Banner
st.markdown(
    """
    <style>
    .fixed-marquee {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        overflow: hidden;
        background: linear-gradient(90deg, #ff8800, #ff4b2b, #ff8800);
        color: #fff;
        font-weight: 600;
        font-size: 17px;
        padding: 10px 0;
        z-index: 9999;
        text-shadow: 0 0 6px rgba(0, 0, 0, 0.4);
        letter-spacing: 0.5px;
    }
    .marquee-content {
        display: inline-block;
        white-space: nowrap;
        padding-left: 100%;
        animation: scroll-left 25s linear infinite;
    }
    @keyframes scroll-left {
        0% { transform: translateX(0); }
        100% { transform: translateX(-100%); }
    }
    </style>

    <div class="fixed-marquee">
      <div class="marquee-content">
        For all queries in regards to Hotel Automation, pls contact us on +91-9167584555, or mail us on info@netcreatorsautomation.in
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Authenticate with Google Sheets
service_account_info = st.secrets["gcp_service_account"]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
client = gspread.authorize(creds)

# Load data from Google Sheets
SHEET_ID = "1polqqd0z2BJKZc_P9m6IQ-IOpCCRi-m0HHANCLweRrM"
spreadsheet = client.open_by_key(SHEET_ID)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_transactions():
    transactions_sheet = spreadsheet.worksheet("Transactions")
    data = transactions_sheet.get_all_records()
    return pd.DataFrame(data)

@st.cache_data(ttl=300)
def load_balances():
    balance_sheet = spreadsheet.worksheet("CurrentBalances")
    data = balance_sheet.get_all_records()
    return pd.DataFrame(data)

# Header
st.header("Netcreators Automation Dashboard", divider="gray")

# Refresh Button
col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
with col2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Load Data
df_transactions = load_transactions()
df_balances = load_balances()

# Convert date columns
if "Timestamp" in df_transactions.columns:
    df_transactions["Timestamp"] = pd.to_datetime(df_transactions["Timestamp"])

if "Last Updated" in df_balances.columns:
   df_balances["Last Updated"] = pd.to_datetime(
    df_balances["Last Updated"],
    format="%d/%m/%Y %H:%M:%S",
    errors="coerce"
)


# Sidebar Filters
st.sidebar.header("Filters")

# User selection
users = df_transactions["userName"].unique()
selected_users = st.sidebar.multiselect("Select Users", users, default=users)

# Transaction type selection
types = df_transactions["type"].unique()
selected_type = st.sidebar.multiselect("Select Transaction Type", types, default=types)

# Date range
date_range = st.sidebar.date_input("Select Date Range", [])

# Apply Filters
if selected_users:
    df_transactions = df_transactions[df_transactions["userName"].isin(selected_users)]
    df_balances = df_balances[df_balances["Username"].isin(selected_users)]

df_transactions = df_transactions[df_transactions["type"].isin(selected_type)]

if len(date_range) == 2:
    start_date, end_date = date_range
    df_transactions = df_transactions[
        (df_transactions["Timestamp"] >= pd.to_datetime(start_date)) & 
        (df_transactions["Timestamp"] <= pd.to_datetime(end_date))
    ]

# Fix data types
df_transactions["phoneNumber"] = df_transactions["phoneNumber"].astype(str)
df_balances["Phone"] = df_balances["Phone"].astype(str)

# Dashboard Metrics
st.subheader("📈 Key Metrics")

# Calculate metrics
total_users = len(df_balances)
total_balance = df_balances["Current Balance"].sum()
total_transactions = len(df_transactions)
avg_balance = df_balances["Current Balance"].mean()

# Display metrics in columns
metric1, metric2, metric3, metric4 = st.columns(4)

with metric1:
    st.metric(
        label="Total Users", 
        value=total_users,
        delta=f"{len(df_balances[df_balances['Current Balance'] > 0])} active"
    )

with metric2:
    st.metric(
        label="Total Balance", 
        value=f"₹{total_balance:,.0f}",
        delta=f"Avg: ₹{avg_balance:.0f}"
    )

with metric3:
    st.metric(
        label="Total Transactions", 
        value=total_transactions
    )

with metric4:
    positive_transactions = len(df_transactions[df_transactions["amount"] > 0])
    st.metric(
        label="Positive Transactions", 
        value=positive_transactions,
        delta=f"{positive_transactions/total_transactions*100:.1f}%"
    )

# Current Balance Section
st.subheader("💰 Current Balances")

# Display balances in a nice table
balance_col1, balance_col2 = st.columns([2, 1])

with balance_col1:
    # Sort by balance
    df_balances_sorted = df_balances.sort_values("Current Balance", ascending=False)
    
    # Style the balances table
    st.dataframe(
        df_balances_sorted.style.format({
            "Current Balance": "₹{:.0f}",
            "Phone": lambda x: str(x)
        }).background_gradient(subset=["Current Balance"], cmap="Greens"),
        use_container_width=True
    )

with balance_col2:
    # Balance distribution pie chart
    balance_pie = alt.Chart(df_balances).mark_arc(innerRadius=50).encode(
        theta=alt.Theta(field="Current Balance", type="quantitative"),
        color=alt.Color(field="Username", type="nominal", legend=None),
        tooltip=["Username", "Current Balance"]
    ).properties(
        title="Balance Distribution",
        height=300
    )
    
    st.altair_chart(balance_pie, use_container_width=True)

# Transactions Section
st.subheader("📋 Transaction History")

# Transaction summary
transaction_col1, transaction_col2 = st.columns([3, 1])

with transaction_col1:
    st.dataframe(
        df_transactions.style.format({
            "amount": "₹{:.0f}",
            "phoneNumber": lambda x: str(x)
        }),
        use_container_width=True
    )

with transaction_col2:
    # Transaction type distribution
    type_counts = df_transactions["type"].value_counts().reset_index()
    type_counts.columns = ["type", "count"]
    
    type_pie = alt.Chart(type_counts).mark_arc().encode(
        theta=alt.Theta(field="count", type="quantitative"),
        color=alt.Color(field="type", type="nominal"),
        tooltip=["type", "count"]
    ).properties(
        title="Transaction Types",
        height=300
    )
    
    st.altair_chart(type_pie, use_container_width=True)

# Charts Section
st.subheader("📊 Analytics & Insights")

# Create tabs for different charts
tab1, tab2, tab3, tab4 = st.tabs(["Transaction Analysis", "User Activity", "Balance Trends", "Performance Metrics"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # Bar Chart for Transaction Types
        type_summary = df_transactions.groupby("type")["amount"].sum().reset_index()
        bar_chart = alt.Chart(type_summary).mark_bar().encode(
            x=alt.X("type", title="Transaction Type", sort="-y"),
            y=alt.Y("amount", title="Total Amount (₹)"),
            color=alt.Color("type", legend=None),
            tooltip=["type", "amount"]
        ).properties(
            title="Total Amount per Transaction Type",
            height=300
        )
        st.altair_chart(bar_chart, use_container_width=True)
    
    with col2:
        # Transaction timeline
        if "Timestamp" in df_transactions.columns:
            daily_transactions = df_transactions.groupby(
                df_transactions["Timestamp"].dt.date
            )["amount"].sum().reset_index()
            daily_transactions.columns = ["Date", "Total Amount"]
            
            timeline_chart = alt.Chart(daily_transactions).mark_line(point=True).encode(
                x=alt.X("Date:T", title="Date"),
                y=alt.Y("Total Amount:Q", title="Daily Total (₹)"),
                tooltip=["Date", "Total Amount"]
            ).properties(
                title="Daily Transaction Trends",
                height=300
            )
            st.altair_chart(timeline_chart, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        # User transaction count
        user_activity = df_transactions["userName"].value_counts().reset_index()
        user_activity.columns = ["userName", "transaction_count"]
        
        activity_chart = alt.Chart(user_activity).mark_bar().encode(
            x=alt.X("userName", title="User", sort="-y"),
            y=alt.Y("transaction_count", title="Number of Transactions"),
            color=alt.Color("userName", legend=None),
            tooltip=["userName", "transaction_count"]
        ).properties(
            title="User Transaction Activity",
            height=300
        )
        st.altair_chart(activity_chart, use_container_width=True)
    
    with col2:
        # User balance comparison
        balance_chart = alt.Chart(df_balances).mark_bar().encode(
            x=alt.X("Username", title="User", sort="-y"),
            y=alt.Y("Current Balance", title="Current Balance (₹)"),
            color=alt.Color("Current Balance", scale=alt.Scale(scheme="greens")),
            tooltip=["Username", "Current Balance"]
        ).properties(
            title="Current Balances by User",
            height=300
        )
        st.altair_chart(balance_chart, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        # Balance distribution histogram
        hist_chart = alt.Chart(df_balances).mark_bar().encode(
            x=alt.X("Current Balance:Q", bin=alt.Bin(maxbins=20), title="Balance Range"),
            y=alt.Y("count()", title="Number of Users"),
            color=alt.Color("Current Balance:Q", scale=alt.Scale(scheme="blues")),
            tooltip=["count()"]
        ).properties(
            title="Balance Distribution",
            height=300
        )
        st.altair_chart(hist_chart, use_container_width=True)
    
    with col2:
        # Top users by balance
        top_users = df_balances.nlargest(5, "Current Balance")
        top_chart = alt.Chart(top_users).mark_bar().encode(
            x=alt.X("Current Balance:Q", title="Balance (₹)"),
            y=alt.Y("Username:N", title="User", sort="-x"),
            color=alt.Color("Current Balance:Q", scale=alt.Scale(scheme="viridis")),
            tooltip=["Username", "Current Balance"]
        ).properties(
            title="Top 5 Users by Balance",
            height=300
        )
        st.altair_chart(top_chart, use_container_width=True)

with tab4:
    col1, col2 = st.columns(2)
    
    with col1:
        # Transaction amount distribution
        amount_hist = alt.Chart(df_transactions).mark_bar().encode(
            x=alt.X("amount:Q", bin=alt.Bin(maxbins=20), title="Transaction Amount"),
            y=alt.Y("count()", title="Frequency"),
            color=alt.Color("type:N", title="Transaction Type"),
            tooltip=["count()", "type"]
        ).properties(
            title="Transaction Amount Distribution",
            height=300
        )
        st.altair_chart(amount_hist, use_container_width=True)
    
    with col2:
        # User performance scatter plot
        user_summary = df_transactions.groupby("userName").agg({
            "amount": ["sum", "count"],
            "type": "first"
        }).reset_index()
        user_summary.columns = ["userName", "total_amount", "transaction_count", "first_type"]
        
        # Merge with balances
        user_performance = pd.merge(user_summary, df_balances, left_on="userName", right_on="Username", how="left")
        
        scatter_chart = alt.Chart(user_performance).mark_circle(size=100).encode(
            x=alt.X("transaction_count:Q", title="Number of Transactions"),
            y=alt.Y("total_amount:Q", title="Total Transaction Amount (₹)"),
            size=alt.Size("Current Balance:Q", title="Current Balance"),
            color=alt.Color("userName:N", title="User"),
            tooltip=["userName", "transaction_count", "total_amount", "Current Balance"]
        ).properties(
            title="User Performance: Transactions vs Total Amount",
            height=300
        )
        st.altair_chart(scatter_chart, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: gray;'>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>",
    unsafe_allow_html=True
)

st.success("Dashboard Updated Successfully! ✅")





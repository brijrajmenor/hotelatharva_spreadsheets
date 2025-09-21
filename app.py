import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import altair as alt
import time

# Authenticate with Google Sheets
service_account_info = st.secrets["gcp_service_account"]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
client = gspread.authorize(creds)

# Load data from Google Sheets
SHEET_ID = "1polqqd0z2BJKZc_P9m6IQ-IOpCCRi-m0HHANCLweRrM"
transactions_sheet = client.open_by_key(SHEET_ID).worksheet("Transactions")

def load_transactions():
    data = transactions_sheet.get_all_records()
    return pd.DataFrame(data)

st.header("Netcreators Automation", divider="gray")
st.subheader("📊 Transaction Dashboard")


# Refresh Button
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

# Load Data
df = load_transactions()

# Convert date column
if "Timestamp" in df.columns:
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

# Filters
users = df["userName"].unique()
selected_users = st.sidebar.multiselect("Select Users", users, default=users)

types = df["type"].unique()
selected_type = st.sidebar.multiselect("Select Transaction Type", types, default=types)

date_range = st.sidebar.date_input("Select Date Range", [])

# Apply Filters
if selected_users:
    df = df[df["userName"].isin(selected_users)]

df = df[df["type"].isin(selected_type)]

if len(date_range) == 2:
    start_date, end_date = date_range
    df = df[(df["Timestamp"] >= pd.to_datetime(start_date)) & (df["Timestamp"] <= pd.to_datetime(end_date))]

# Fix: Convert phoneNumber to string
df["phoneNumber"] = df["phoneNumber"].astype(str)

st.dataframe(df)

# Charts
st.subheader("Transaction Summary")

# Bar Chart for Transaction Types
bar_chart = alt.Chart(df).mark_bar().encode(
    x=alt.X("type", title="Transaction Type"),
    y=alt.Y("sum(amount)", title="Total Amount"),
    color="type"
).properties(title="Total Amount per Transaction Type")
st.altair_chart(bar_chart, use_container_width=True)

# Pie Chart for User Transactions
user_pie = alt.Chart(df).mark_arc().encode(
    theta="sum(amount)",
    color="userName",
    tooltip=["userName", "sum(amount)"]
).properties(title="User-wise Transactions")
st.altair_chart(user_pie, use_container_width=True)

st.success("Dashboard Updated ✅")
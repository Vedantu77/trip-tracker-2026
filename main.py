import streamlit as st
from supabase import create_client
import pandas as pd
import time

# --- 1. SETUP ---
# Replace with your actual credentials
URL = "YOUR_SUPABASE_URL"
KEY = "YOUR_SUPABASE_ANON_KEY"
YOUR_UPI_ID = "vedantgaikwad538@okaxis" 
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Trip Ledger 2026", layout="wide")

# --- 2. THE FIX FOR BLANK TABS ---
# This function creates a button that works on mobile without opening a new tab
def upi_button(label, upi_url, color="#673ab7"):
    # Using target="_self" and a custom style to prevent blank pages
    html_code = f'''
    <a href="{upi_url}" target="_self" style="text-decoration: none;">
        <div style="
            background-color: {color};
            color: white;
            padding: 12px;
            border-radius: 10px;
            text-align: center;
            font-weight: bold;
            font-family: sans-serif;
            margin-bottom: 10px;
            cursor: pointer;">
            {label}
        </div>
    </a>
    '''
    return st.markdown(html_code, unsafe_allow_html=True)

# --- 3. DATA & AUTO-REFRESH ---
# This makes the app "Live" for your friends
def load_data():
    f = supabase.table("trip_funds").select("*").execute()
    e = supabase.table("trip_expenses").select("*").execute()
    return pd.DataFrame(f.data), pd.DataFrame(e.data)

df_f, df_e = load_data()
t_in = df_f['amount'].sum() if not df_f.empty else 0
t_out = df_e['amount'].sum() if not df_e.empty else 0
bal = t_in - t_out

# --- 4. DASHBOARD ---
st.title("🚩 Vrindavan-Ujjain Live Ledger")
c1, c2, c3 = st.columns(3)
c1.metric("Total Collected", f"₹{t_in}")
c2.metric("Total Spent", f"₹{t_out}", delta=f"-{t_out}", delta_color="inverse")
c3.metric("Live Bank Balance", f"₹{bal}")

st.divider()

# --- 5. TABS ---
t1, t2, t3 = st.tabs(["📥 Friends: Add Fund", "💸 Admin: Pay & Record", "📜 History"])

with t1:
    st.subheader("Send Money to Vedant")
    f_name = st.text_input("Your Name")
    f_amt = st.number_input("Amount", min_value=0, step=100, key="f_amt")
    
    if f_amt > 0:
        link = f"upi://pay?pa={YOUR_UPI_ID}&pn=Vedant&am={f_amt}&cu=INR&tn=TripFund"
        upi_button(f"📲 Pay ₹{f_amt} via GPay/PhonePe", link, "#4CAF50")
        
    if st.button("✅ I have paid (Update Ledger)"):
        if f_name and f_amt > 0:
            supabase.table("trip_funds").insert({"member_name": f_name, "amount": f_amt}).execute()
            st.success("Sent! Ledger will update.")
            time.sleep(1)
            st.rerun()

with t2:
    st.subheader("Admin Spending")
    pwd = st.text_input("Admin Key", type="password")
    
    if pwd == "vedant2026":
        e_purp = st.text_input("Spending Purpose (e.g. Dormitory)")
        e_amt = st.number_input("Amount", min_value=0, step=10, key="e_amt")
        
        if e_amt > 0:
            e_link = f"upi://pay?pa={YOUR_UPI_ID}&pn=Merchant&am={e_amt}&cu=INR&tn={e_purp}"
            upi_button(f"🚀 Open App & Pay ₹{e_amt}", e_link, "#E91E63")
            
            if st.button("💾 Transaction Done (Record Now)"):
                supabase.table("trip_expenses").insert({"purpose": e_purp, "amount": e_amt, "category": "Trip"}).execute()
                st.balloons()
                time.sleep(1)
                st.rerun()
    else:
        st.warning("Admin access required to record expenses.")

with t3:
    st.subheader("Recent Activity")
    if not df_e.empty:
        st.dataframe(df_e[['purpose', 'amount', 'created_at']].sort_values('created_at', ascending=False), use_container_width=True)
    else:
        st.info("No expenses yet.")

# --- 6. AUTO REFRESH LOGIC ---
# Every 15 seconds, the page will check for new data automatically
# st.write("_(Auto-refreshing every 15s to keep balance live)_")
# time.sleep(15)
# st.rerun()
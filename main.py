import streamlit as st
from supabase import create_client
import pandas as pd
import time

# --- 1. CONFIG & SECRETS ---
# Ensure these match the keys in your Streamlit Cloud "Secrets" tab
# --- 1. CONFIG & SECRETS ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
YOUR_UPI_ID = "vedantgaikwad538@ibl" 
ADMIN_PASS = "vedant2026"
# Connect to Supabase
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Trip Ledger 2026", layout="wide", page_icon="🚩")

# --- 2. DATA LOADING ---
def load_data():
    try:
        f = supabase.table("trip_funds").select("*").execute()
        e = supabase.table("trip_expenses").select("*").execute()
        return pd.DataFrame(f.data), pd.DataFrame(e.data)
    except Exception as err:
        st.error(f"Database Error: {err}")
        return pd.DataFrame(), pd.DataFrame()

df_f, df_e = load_data()

# Calculate Metrics
total_collected = df_f['amount'].sum() if not df_f.empty else 0
total_spent = df_e['amount'].sum() if not df_e.empty else 0
wallet_balance = total_collected - total_spent

# --- 3. UI: DASHBOARD ---
st.title("🚩 Vrindavan-Ujjain Trip Manager")
st.write(f"Logged in as: **Vedant (Admin)**")

c1, c2, c3 = st.columns(3)
c1.metric("Total Pool 📥", f"₹{total_collected}")
c2.metric("Total Spent 📤", f"₹{total_spent}", delta=f"-{total_spent}", delta_color="inverse")
c3.metric("Wallet Balance 💰", f"₹{wallet_balance}")

# Progress Bar (Goal: Stay within Budget)
if total_collected > 0:
    progress = min(total_spent / total_collected, 1.0)
    st.progress(progress, text=f"Spending: {int(progress*100)}% of the collected pool used")

st.divider()

# --- 4. TABS ---
t1, t2, t3, t4 = st.tabs(["📥 Friend Pay", "💸 Admin: Pay Anyone", "📜 History", "👥 Members"])

with t1:
    st.subheader("📥 One-Click Pay to Vedant")
    f_name = st.text_input("Friend's Name")
    f_amt = st.number_input("Amount", min_value=0, step=100)
    
    if f_amt > 0:
        # This is the "Magic Link"
        pay_url = f"upi://pay?pa={YOUR_UPI_ID}&pn=Vedant&am={f_amt}&cu=INR&tn=Trip"
        
        # We use a Custom HTML Button to force the phone to open the app
        pay_btn = f'''
            <a href="{pay_url}">
                <button style="width:100%; padding:15px; background-color:#28a745; color:white; border:none; border-radius:10px; font-size:18px; font-weight:bold;">
                    💸 Pay ₹{f_amt} Now
                </button>
            </a>
        '''
        st.markdown(pay_btn, unsafe_allow_html=True)

    if st.button("✅ Record Payment in Ledger"):
        if f_name and f_amt > 0:
            supabase.table("trip_funds").insert({"member_name": f_name, "amount": f_amt}).execute()
            st.success("Logged!")
            st.rerun()

with t2:
    st.subheader("💸 Admin: Direct Merchant Pay")
    pwd = st.text_input("Key", type="password")
    if pwd == ADMIN_PASS:
        e_purp = st.text_input("Spending on?")
        e_amt = st.number_input("Expense Amount", min_value=0)
        target_upi = st.text_input("Merchant UPI ID (e.g. shop@okaxis)")
        
        if e_amt > 0 and target_upi:
            m_url = f"upi://pay?pa={target_upi}&pn=Merchant&am={e_amt}&cu=INR&tn={e_purp}"
            
            # The Admin Magic Button
            admin_pay_btn = f'''
                <a href="{m_url}">
                    <button style="width:100%; padding:15px; background-color:#e91e63; color:white; border:none; border-radius:10px; font-size:18px; font-weight:bold;">
                        🚀 Pay Merchant ₹{e_amt}
                    </button>
                </a>
            '''
            st.markdown(admin_pay_btn, unsafe_allow_html=True)

        if st.button("💾 Transaction Done (Record)"):
            supabase.table("trip_expenses").insert({"purpose": e_purp, "amount": e_amt, "category": "Trip"}).execute()
            st.rerun()

with t3:
    st.subheader("Recent Spending Activity")
    if not df_e.empty:
        st.dataframe(df_e[['purpose', 'amount', 'category', 'created_at']].sort_values('created_at', ascending=False), use_container_width=True)
    else:
        st.info("No logs yet.")

with t4:
    st.subheader("Member Contribution Board")
    if not df_f.empty:
        summary = df_f.groupby('member_name')['amount'].sum().reset_index()
        st.table(summary)
    else:
        st.write("Waiting for first contribution.")
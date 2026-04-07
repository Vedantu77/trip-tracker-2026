import streamlit as st
from supabase import create_client
import pandas as pd
import time

# --- 1. CONFIG ---
# Replace with your actual credentials
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
YOUR_UPI_ID = "vedantgaikwad538@ibl"  # All contributions come here
ADMIN_PASS = "vedant2026"

supabase = create_client(URL, KEY)

st.set_page_config(page_title="Trip Ledger 2026", layout="wide", page_icon="🚩")

# --- 2. DATA LOAD & CALCULATIONS ---
def load_data():
    f = supabase.table("trip_funds").select("*").execute()
    e = supabase.table("trip_expenses").select("*").execute()
    return pd.DataFrame(f.data), pd.DataFrame(e.data)

df_f, df_e = load_data()

# Math for the Dashboard
total_collected = df_f['amount'].sum() if not df_f.empty else 0
total_spent = df_e['amount'].sum() if not df_e.empty else 0
remaining_fund = total_collected - total_spent

# --- 3. UI: DASHBOARD ---
st.title("🚩 Vrindavan-Ujjain Trip Manager")
st.write(f"Logged in as: **Vedant (Admin)**")

col1, col2, col3 = st.columns(3)
col1.metric("Total Pool 📥", f"₹{total_collected}")
col2.metric("Total Spent 📤", f"₹{total_spent}", delta=f"-{total_spent}", delta_color="inverse")
col3.metric("Wallet Balance 💰", f"₹{remaining_fund}")

st.divider()

# --- 4. TABS ---
t1, t2, t3, t4 = st.tabs(["📥 Friend Pay", "💸 Admin: Pay Merchant", "📜 History", "👥 Members"])

with t1:
    st.subheader("Add Funds to the Trip")
    f_name = st.text_input("Friend's Name")
    f_amt = st.number_input("Amount to Contribute", min_value=0, step=500)
    
    # Pre-filled UPI link for YOUR account only
    friend_link = f"upi://pay?pa={YOUR_UPI_ID}&pn=Vedant&am={f_amt}&cu=INR&tn=TripContribution"
    
    st.markdown(f'''
        <a href="{friend_link}" target="_self" style="text-decoration:none;">
            <div style="background-color:#4CAF50;color:white;padding:15px;border-radius:10px;text-align:center;font-weight:bold;">
                📲 Pay ₹{f_amt} to Vedant
            </div>
        </a>''', unsafe_allow_html=True)
    
    if st.button("✅ I have Paid (Add to Ledger)"):
        if f_name and f_amt > 0:
            supabase.table("trip_funds").insert({"member_name": f_name, "amount": f_amt}).execute()
            st.success(f"Log Updated! ₹{f_amt} added from {f_name}.")
            time.sleep(1)
            st.rerun()

with t2:
    st.subheader("Admin: Pay Anyone (Merchant/Taxi/Hotel)")
    pwd = st.text_input("Enter Admin Key", type="password")
    
    if pwd == ADMIN_PASS:
        exp_name = st.text_input("What are you paying for? (e.g. Rickshaw)")
        exp_amt = st.number_input("Expense Amount", min_value=0)
        
        st.info("💡 Tip: Look at the Merchant's QR code for their UPI ID (e.g. name@paytm)")
        merchant_upi = st.text_input("Merchant UPI ID", placeholder="Enter merchant UPI ID here...")
        exp_cat = st.selectbox("Category", ["Food", "Transport", "Stay", "Pooja", "Misc"])
        
        if exp_amt > 0 and merchant_upi:
            # This link opens GPay/PhonePe to pay the MERCHANT
            merchant_link = f"upi://pay?pa={merchant_upi}&pn=Merchant&am={exp_amt}&cu=INR&tn={exp_name}"
            st.markdown(f'''
                <a href="{merchant_link}" target="_self" style="text-decoration:none;">
                    <div style="background-color:#E91E63;color:white;padding:15px;border-radius:10px;text-align:center;font-weight:bold;">
                        🚀 Open App & Pay ₹{exp_amt} to Merchant
                    </div>
                </a>''', unsafe_allow_html=True)
            
            if st.button("💾 Transaction Done (Save Expense)"):
                supabase.table("trip_expenses").insert({"purpose": exp_name, "amount": exp_amt, "category": exp_cat}).execute()
                st.balloons()
                time.sleep(1)
                st.rerun()
    else:
        st.warning("Please enter the correct Admin Key to access payments.")

with t3:
    st.subheader("Recent Activity")
    if not df_e.empty:
        # Show spending history
        st.dataframe(df_e[['purpose', 'amount', 'category', 'created_at']].sort_values('created_at', ascending=False), use_container_width=True)
    else:
        st.info("No expenses recorded yet.")

with t4:
    st.subheader("Member Contribution Board")
    if not df_f.empty:
        summary = df_f.groupby('member_name')['amount'].sum().reset_index()
        st.table(summary)
    else:
        st.write("No contributions recorded.")
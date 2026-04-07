import streamlit as st
from supabase import create_client
import pandas as pd
import time

# --- 1. SECRETS & CONFIG ---
URL = st.secrets["https://ulliatblhllbxvjhlvlx.supabase.co"]
KEY = st.secrets["sb_publishable_X9DBJwrA3im5ARK_jfTomw_Tk1eRBQ4"]
YOUR_UPI_ID = "vedantgaikwad538@ibl" 
ADMIN_PASS = "vedant2026"

supabase = create_client(URL, KEY)

st.set_page_config(page_title="Trip Ledger: Auto-Sync", layout="wide", page_icon="📡")

# --- 2. DATA LOADING ---
def load_data():
    f = supabase.table("trip_funds").select("*").execute()
    e = supabase.table("trip_expenses").select("*").execute()
    return pd.DataFrame(f.data), pd.DataFrame(e.data)

df_f, df_e = load_data()

# Calculations
total_verified = df_f[df_f['status'] == 'Verified']['amount'].sum() if not df_f.empty else 0
total_spent = df_e['amount'].sum() if not df_e.empty else 0
balance = total_verified - total_spent

# --- 3. DASHBOARD ---
st.title("🚩 Vrindavan-Ujjain Smart Ledger")
st.caption("📡 Auto-syncing with Bank Notifications")

m1, m2, m3 = st.columns(3)
m1.metric("Verified Fund 📥", f"₹{total_verified}")
m2.metric("Total Spent 📤", f"₹{total_spent}", delta=f"-{total_spent}", delta_color="inverse")
m3.metric("Live Balance 💰", f"₹{balance}")

st.divider()

# --- 4. TABS ---
t1, t2, t3, t4 = st.tabs(["📥 Add Fund", "💸 Admin Pay", "📜 History", "🛡️ Manual Verify"])

with t1:
    st.subheader("Send Money")
    name = st.text_input("Your Name (As seen on GPay)")
    amt = st.number_input("Amount", min_value=0, step=100)
    if amt > 0:
        link = f"upi://pay?pa={YOUR_UPI_ID}&pn=Vedant&am={amt}&cu=INR&tn=TripFund"
        st.markdown(f'<a href="{link}" target="_self" style="text-decoration:none;"><div style="background-color:#4CAF50;color:white;padding:12px;border-radius:10px;text-align:center;font-weight:bold;">📲 Pay ₹{amt} via UPI</div></a>', unsafe_allow_html=True)
        if st.button("I Have Paid"):
            supabase.table("trip_funds").insert({"member_name": name, "amount": amt, "status": "Pending"}).execute()
            st.info("Waiting for Bank Confirmation... (Auto-updates in 30s)")

with t2:
    st.subheader("Admin Payments")
    if st.text_input("Admin Key", type="password") == ADMIN_PASS:
        p_purp = st.text_input("Purpose")
        p_amt = st.number_input("Expense Amount", min_value=0)
        p_cat = st.selectbox("Category", ["Food", "Transport", "Stay", "Pooja", "Misc"])
        if p_amt > 0:
            if st.button("Save Expense"):
                supabase.table("trip_expenses").insert({"purpose": p_purp, "amount": p_amt, "category": p_cat}).execute()
                st.rerun()

with t3:
    st.subheader("Spending History")
    if not df_e.empty:
        st.table(df_e[['purpose', 'amount', 'category', 'created_at']].sort_values('created_at', ascending=False))

with t4:
    st.subheader("🛡️ Backup Verification")
    if st.text_input("Verify Key", type="password", key="v_key") == ADMIN_PASS:
        pending = df_f[df_f['status'] == 'Pending']
        if not pending.empty:
            for _, row in pending.iterrows():
                col_a, col_b = st.columns([3,1])
                col_a.write(f"**{row['member_name']}** → ₹{row['amount']}")
                if col_b.button("Verify ✅", key=f"v_{row['id']}"):
                    supabase.table("trip_funds").update({"status": "Verified"}).eq("id", row['id']).execute()
                    st.rerun()
        else:
            st.success("No pending items.")

# --- 5. AUTO-REFRESH LOGIC ---
time.sleep(30)
st.rerun()
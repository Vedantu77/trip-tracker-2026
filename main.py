import streamlit as st
from supabase import create_client
import pandas as pd
import time

# --- 1. SETUP ---
# Ensure these match your Supabase Dashboard
URL = "https://ulliatblhllbxvjhlvlx.supabase.co"
KEY = "sb_publishable_X9DBJwrA3im5ARK_jfTomw_Tk1eRBQ4"
YOUR_UPI_ID = "vedantgaikwad538@ibl" 
ADMIN_PASS = "vedant2026"

supabase = create_client(URL, KEY)

st.set_page_config(page_title="Trip Ledger 2026", layout="wide", page_icon="🚩")

# --- 2. THE FIX FOR MOBILE TABS ---
def upi_button(label, upi_url, color="#673ab7"):
    html_code = f'''
    <a href="{upi_url}" target="_self" style="text-decoration: none;">
        <div style="background-color:{color}; color:white; padding:12px; border-radius:10px; text-align:center; font-weight:bold; cursor:pointer;">
            {label}
        </div>
    </a>
    '''
    return st.markdown(html_code, unsafe_allow_html=True)

# --- 3. DATA LOADING ---
def load_data():
    f = supabase.table("trip_funds").select("*").execute()
    e = supabase.table("trip_expenses").select("*").execute()
    return pd.DataFrame(f.data), pd.DataFrame(e.data)

df_f, df_e = load_data()
t_in = df_f['amount'].sum() if not df_f.empty else 0
t_out = df_e['amount'].sum() if not df_e.empty else 0
bal = t_in - t_out

# --- 4. DASHBOARD ---
st.title("🚩 Vrindavan-Ujjain Live Tracker")
c1, c2, c3 = st.columns(3)
c1.metric("Total Collected 📥", f"₹{t_in}")
c2.metric("Total Spent 📤", f"₹{t_out}", delta=f"-{t_out}", delta_color="inverse")
c3.metric("Available Balance 💰", f"₹{bal}")

st.divider()

# --- 5. TABS ---
t1, t2, t3, t4 = st.tabs(["📥 Add Fund", "💸 Pay & Record", "📜 History", "👥 Members"])

with t1:
    st.subheader("Contribute to Trip")
    f_name = st.text_input("Friend Name")
    f_amt = st.number_input("Amount", min_value=0, step=100)
    if f_amt > 0:
        link = f"upi://pay?pa={YOUR_UPI_ID}&pn=Vedant&am={f_amt}&cu=INR&tn=TripFund"
        upi_button(f"📲 Pay ₹{f_amt} via UPI", link, "#4CAF50")
    if st.button("✅ Log My Payment"):
        if f_name and f_amt > 0:
            supabase.table("trip_funds").insert({"member_name": f_name, "amount": f_amt}).execute()
            st.success("Entry Saved!")
            time.sleep(1)
            st.rerun()

with t2:
    st.subheader("Admin: New Expense")
    pwd = st.text_input("Admin Key", type="password")
    if pwd == ADMIN_PASS:
        e_purp = st.text_input("Purpose (e.g. Hotel/Rickshaw)")
        e_amt = st.number_input("Expense Amount", min_value=0, step=10)
        e_cat = st.selectbox("Category", ["Food", "Transport", "Stay", "Pooja", "Misc"])
        if e_amt > 0:
            e_link = f"upi://pay?pa={YOUR_UPI_ID}&pn=Merchant&am={e_amt}&cu=INR&tn={e_purp}"
            upi_button(f"🚀 Open App & Pay ₹{e_amt}", e_link, "#E91E63")
            if st.button("💾 Save to Ledger"):
                supabase.table("trip_expenses").insert({"purpose": e_purp, "amount": e_amt, "category": e_cat}).execute()
                st.success("Balance Updated!")
                time.sleep(1)
                st.rerun()

with t3:
    st.subheader("Spending History")
    if not df_e.empty:
        # Added a Delete feature for Admin
        for index, row in df_e.iterrows():
            col_a, col_b, col_c = st.columns([3, 1, 1])
            col_a.write(f"**{row['purpose']}** ({row['category']})")
            col_b.write(f"₹{row['amount']}")
            if pwd == ADMIN_PASS:
                if col_c.button("🗑️ Delete", key=f"del_{row['id']}"):
                    supabase.table("trip_expenses").delete().eq("id", row['id']).execute()
                    st.rerun()
    else:
        st.info("No expenses yet.")

with t4:
    st.subheader("Who has paid how much?")
    if not df_f.empty:
        summary = df_f.groupby('member_name')['amount'].sum().reset_index()
        st.table(summary)
    else:
        st.write("No contributions recorded.")
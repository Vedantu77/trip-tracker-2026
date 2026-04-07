import streamlit as st
from supabase import create_client
import pandas as pd
import time

# --- 1. CONFIG & SECRETS ---
# Ensure these match the keys in your Streamlit Cloud "Secrets" tab
URL = st.secrets["https://ulliatblhllbxvjhlvlx.supabase.co"]
KEY = st.secrets["sb_publishable_X9DBJwrA3im5ARK_jfTomw_Tk1eRBQ4"]
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
    st.subheader("Add Funds to the Trip")
    f_name = st.text_input("Friend's Name")
    f_amt = st.number_input("Amount to Contribute", min_value=0, step=500)
    
    # Links ONLY to your account
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
            st.success(f"Pool Updated! Added ₹{f_amt} from {f_name}.")
            time.sleep(1)
            st.rerun()

with t2:
    st.subheader("Admin: Universal Pay (Any Merchant)")
    pwd = st.text_input("Admin Key", type="password")
    
    if pwd == ADMIN_PASS:
        e_purp = st.text_input("Purpose (e.g. Taxi, Dinner)")
        e_amt = st.number_input("Expense Amount", min_value=0)
        
        st.info("💡 Enter any Merchant UPI ID or Number below to pay them directly.")
        target = st.text_input("Merchant UPI ID / Phone Number")
        e_cat = st.selectbox("Category", ["Food", "Transport", "Stay", "Pooja", "Misc"])
        
        if e_amt > 0 and target:
            # Flexible Link Generation
            merchant_link = f"upi://pay?pa={target}&pn=Merchant&am={e_amt}&cu=INR&tn={e_purp}"
            
            st.markdown(f'''
                <a href="{merchant_link}" target="_self" style="text-decoration:none;">
                    <div style="background-color:#E91E63;color:white;padding:15px;border-radius:10px;text-align:center;font-weight:bold;">
                        🚀 Open App & Pay ₹{e_amt} to Merchant
                    </div>
                </a>''', unsafe_allow_html=True)
            
            st.caption("Note: If the link fails for security, pay manually and click the Record button below.")
            
            if st.button("💾 Record Expense to History"):
                supabase.table("trip_expenses").insert({"purpose": e_purp, "amount": e_amt, "category": e_cat}).execute()
                st.balloons()
                time.sleep(1)
                st.rerun()
    else:
        st.warning("Admin Access Required.")

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
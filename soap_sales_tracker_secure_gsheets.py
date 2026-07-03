import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# 1. Page Configuration
st.set_page_config(page_title="መላ ሳሙና እና ዲተርጀንት ሽያጭ መቆጣጠሪያ", layout="wide")

# 2. Define Default Passwords (In production, these come from st.secrets)
PASSWORDS = {
    "📊 የኤግዚኪቲቭ ዳሽቦርድ (Executive Dashboard)": st.secrets.get("PASSWORD_EXEC", "exec123"),
    "🏭 የኢንቬንተሪ ክፍል (Inventory Dispatch)": st.secrets.get("PASSWORD_INV", "inv123"),
    "💰 የሽያጭ ክፍል - ሮቤል (Sales Department)": st.secrets.get("PASSWORD_ROBEL", "robel123"),
    "⚙️ የሲስተም ማስተካከያ (System Settings)": st.secrets.get("PASSWORD_SETTINGS", "settings123")
}

# 3. Google Sheets Connection Setup
# Connects using Streamlit Secrets for the Service Account
@st.cache_resource
def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # In Streamlit Cloud, you put the JSON content inside st.secrets["gcp_service_account"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ ከGoogle Sheets ጋር መገናኘት አልተቻለም። እባክዎ የSecrets ቅንብሩን ያረጋግጡ። ስህተት: {e}")
        return None

def get_sheet_data(sheet_name):
    client = get_gspread_client()
    if client:
        try:
            # Open spreadsheet by URL or ID from secrets
            spreadsheet_url = st.secrets["google_sheet_url"]
            spreadsheet = client.open_by_url(spreadsheet_url)
            worksheet = spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_records()
            return pd.DataFrame(data), worksheet
        except Exception as e:
            st.error(f"❌ ማህደሩን ማንበብ አልተቻለም ({sheet_name}): {e}")
    return pd.DataFrame(), None

# --- Main Interface ---
st.title("🧼 መላ (Mella) ሳሙና እና ዲተርጀንት ማከፋፈያና ሽያጭ መቆጣጠሪያ")
st.markdown("---")

# Role Selection Sidebar
st.sidebar.header("🔐 የሥራ ክፍል መግቢያ (User Login)")
role = st.sidebar.radio(
    "የሚገቡበትን የስራ ክፍል ይምረጡ:",
    ["📊 የኤግዚኪቲቭ ዳሽቦርድ (Executive Dashboard)", 
     "🏭 የኢንቬንተሪ ክፍል (Inventory Dispatch)", 
     "💰 የሽያጭ ክፍል - ሮቤል (Sales Department)", 
     "⚙️ የሲስተም ማስተካከያ (System Settings)"]
)

# Password Check
password_input = st.sidebar.text_input(f"የ {role} የይለፍ ቃል ያስገቡ", type="password")

if not password_input:
    st.info("👋 እባክዎ ለመቀጠል በግራ በኩል ባለው ሳጥን ውስጥ የሥራ ክፍልዎን የይለፍ ቃል (Password) ያስገቡ።")
elif password_input != PASSWORDS[role]:
    st.error("❌ የተሳሳተ የይለፍ ቃል ነው! እባክዎ እንደገና ይሞክሩ።")
else:
    st.sidebar.success(f"🔓 በተሳካ ሁኔታ ገብተዋል!")
    
    # --- Load Configuration from Google Sheets ---
    # We fall back to defaults if sheet fails to load
    df_settings, worksheet_settings = get_sheet_data("System_Settings")
    
    if not df_settings.empty:
        # Extract variables from Google Sheet dynamically
        price_200g = float(df_settings.loc[df_settings['Setting'] == 'price_200g', 'Value'].values[0])
        price_100g = float(df_settings.loc[df_settings['Setting'] == 'price_100g', 'Value'].values[0])
        truck_options = df_settings.loc[df_settings['Setting'] == 'trucks', 'Value'].values[0].split(',')
        bank_options = df_settings.loc[df_settings['Setting'] == 'banks', 'Value'].values[0].split(',')
    else:
        # Fallback Defaults
        price_200g = 1800.0
        price_100g = 1750.0
        truck_options = ["TRUCK-01 (አክሊሉ አሰፋ)", "TRUCK-02 (ዘመን)"]
        bank_options = ["የኢትዮጵያ ንግድ ባንክ (CBE)", "አዋሽ ባንክ (Awash)", "ዳሽን ባንክ (Dashen)", "ወጋገን ባንክ (Wegagen)", "ህብረት ባንክ(Hibret)", "አቢሲኒያ ባንክ(BOA)", "አባይ ባንክ (Abay Bank)"]

    # -------------------------------------------------------------------
    # 1. EXECUTIVE DASHBOARD
    # -------------------------------------------------------------------
    if role == "📊 የኤግዚኪቲቭ ዳሽቦርድ (Executive Dashboard)":
        st.header("📈 የኩባንያው አጠቃላይ የሽያጭና እንቅስቃሴ ሪፖርት (Executive Panel)")
        
        df_sales, _ = get_sheet_data("Sales_Tracker")
        df_inv, _ = get_sheet_data("Inventory_Dispatch")
        
        # Performance KPIs
        total_sales_val = df_sales['Total Sales Value'].astype(float).sum() if not df_sales.empty else 0
        total_dep_val = df_sales['Deposited Amount'].astype(float).sum() if not df_sales.empty else 0
        total_variance = df_sales['Variance'].astype(float).sum() if not df_sales.empty else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("ጠቅላላ የሽያጭ ዋጋ (Total Sales)", f"{total_sales_val:,.2f} ETB")
        col2.metric("ባንክ የገባው ጠቅላላ ገንዘብ (Total Deposited)", f"{total_dep_val:,.2f} ETB")
        
        if total_variance < 0:
            col3.metric("አጠቃላይ ልዩነት / ጉድለት (Total Variance)", f"{total_variance:,.2f} ETB", delta=f"{total_variance:,.2f} ETB", delta_color="inverse")
        else:
            col3.metric("አጠቃላይ ልዩነት / ጉድለት (Total Variance)", f"{total_variance:,.2f} ETB", delta=f"{total_variance:,.2f} ETB")
            
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["📋 የሽያጭና የሂሳብ ማመሳከሪያ መዝገብ (Sales Tracker)", "🚛 የኢንቬንተሪ ጭነት መዝገብ (Inventory Dispatches)"])
        
        with tab1:
            if not df_sales.empty:
                st.dataframe(df_sales, use_container_width=True)
            else:
                st.info("በጉግል ሺት ላይ እስካሁን የተመዘገበ የሽያጭ መረጃ የለም።")
                
        with tab2:
            if not df_inv.empty:
                st.dataframe(df_inv, use_container_width=True)
            else:
                st.info("በጉግል ሺት ላይ እስካሁን የተመዘገበ የጭነት መረጃ የለም።")

    # -------------------------------------------------------------------
    # 2. INVENTORY DISPATCH
    # -------------------------------------------------------------------
    elif role == "🏭 የኢንቬንተሪ ክፍል (Inventory Dispatch)":
        st.header("🏭 የኢንቬንተሪ ጭነት መመዝገቢያ (የተመረተ ምርት መላኪያ)")
        st.info("ወደ መኪናዎች የተጫነውንና የተላከውን የሳሙና ካርቶን ብዛት እዚህ ጋር ይመዝግቡ። መረጃው ቀጥታ ጉግል ሺት ላይ ይገባል።")
        
        _, worksheet_inv = get_sheet_data("Inventory_Dispatch")
        
        with st.form("inventory_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                dispatch_date = st.date_input("የተጫነበት ቀን (Date)", datetime.today())
                truck = st.selectbox("የመኪና / የሹፌር ኮድ (Select Truck)", truck_options)
            with col2:
                qty_200g = st.number_input("ባለ 200ግ የተላከ ካርቶን (200g Ctn Sent)", min_value=0, step=1)
                qty_100g = st.number_input("ባለ 100ግ የተላከ ካርቶን (100g Ctn Sent)", min_value=0, step=1)
                
            remarks = st.text_area("ማብራሪያ / ሪማርክ (Remarks)")
            submit_inv = st.form_submit_button("🚀 የጭነት መረጃውን ወደ Google Sheets ላክ")
            
            if submit_inv:
                if worksheet_inv:
                    new_row = [dispatch_date.strftime('%Y-%m-%d'), truck, int(qty_200g), int(qty_100g), remarks]
                    worksheet_inv.append_row(new_row)
                    st.success(f"✅ ለ {truck} የተላከው የኢንቬንተሪ ጭነት በተሳካ ሁኔታ ወደ Google Sheets ተቀምጧል!")
                else:
                    st.error("❌ ወደ Google Sheets መጻፍ አልተቻለም።")

    # -------------------------------------------------------------------
    # 3. SALES DEPARTMENT (ROBEL)
    # -------------------------------------------------------------------
    elif role == "💰 የሽያጭ ክፍል - ሮቤል (Sales Department)":
        st.header("💰 የሽያጭና ባንክ ሪኮንሲሊየሽን መመዝገቢያ (ሮቤል)")
        st.info("ሮቤል፡ የሸጡትን የሳሙና ብዛት እና ባንክ ያስገቡትን የገንዘብ መጠን ሲያስገቡ ሲስተሙ በራሱ አውቶማቲክ ስሌት ያሰላል።")
        
        df_inv_recent, worksheet_sales = get_sheet_data("Sales_Tracker")
        
        with st.form("sales_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                sales_date = st.date_input("የሽያጭ ቀን (Sales Date)", datetime.today())
                truck = st.selectbox("የመኪና / የሹፌር ኮድ (Select Truck)", truck_options)
                
                st.markdown("##### 📥 መኪናው ላይ የተቀበሉት ምርት (Received from Inventory)")
                recv_200g = st.number_input("የተረከቡት ባለ 200ግ ካርቶን", min_value=0, step=1)
                recv_100g = st.number_input("የተረከቡት ባለ 100ግ ካርቶን", min_value=0, step=1)
                
            with col2:
                st.markdown("##### 🛍️ በትክክል የተሸጠው ምርት ብዛት (Sold Quantity)")
                sold_200g = st.number_input("የተሸጠ ባለ 200ግ ካርቶን", min_value=0, step=1)
                sold_100g = st.number_input("የተሸጠ ባለ 100ግ ካርቶን", min_value=0, step=1)
                
                st.markdown("##### 🏦 የባንክና የሂሳብ መረጃ (Financial Details)")
                dep_amount = st.number_input("ባንክ የገባው ጠቅላላ ብር (Deposited Amount ETB)", min_value=0.0, step=100.0)
                bank_name = st.selectbox("የባንክ ስም (Select Bank)", bank_options)
                
            remarks = st.text_area("ማብራሪያ / የሽያጭ ማስታወሻ (Remarks)")
            
            # --- Auto-Calculations Base on Settings ---
            calc_sales_200 = sold_200g * price_200g
            calc_sales_100 = sold_100g * price_100g
            calculated_total_sales = calc_sales_200 + calc_sales_100
            calculated_variance = dep_amount - calculated_total_sales
            
            st.markdown("### 🧮 የሲስተም አውቶማቲክ ስሌት ቅድመ-እይታ (Calculations Preview)")
            c_val1, c_val2, c_val3 = st.columns(3)
            c_val1.write(f"**የባለ 200ግ ሽያጭ ዋጋ:** {calc_sales_200:,.2f} ETB")
            c_val1.write(f"**የባለ 100ግ ሽያጭ ዋጋ:** {calc_sales_100:,.2f} ETB")
            c_val2.info(f"**ሊመጣ የሚገባው ጠቅላላ የሽያጭ ዋጋ:** {calculated_total_sales:,.2f} ETB")
            
            if calculated_variance < 0:
                c_val3.error(f"**ጉድለት (Shortage):** {calculated_variance:,.2f} ETB")
                status = "ጉድለት አለበት (Shortage)"
            elif calculated_variance > 0:
                c_val3.warning(f"****ብልጫ (Overage):** {calculated_variance:,.2f} ETB")
                status = "ብልጫ አለው (Overage)"
            else:
                c_val3.success(f"**ልዩነት የለም (Balanced):** {calculated_variance:,.2f} ETB")
                status = "የተስተካከለ (Balanced)"
                
            submit_sales = st.form_submit_button("💾 የሽያጭ መረጃውን ወደ Google Sheets አስቀምጥ")
            
            if submit_sales:
                if worksheet_sales:
                    # Append row to Google Sheets
                    new_sales_row = [
                        sales_date.strftime('%Y-%m-%d'), truck, int(recv_200g), int(recv_100g),
                        int(sold_200g), int(sold_100g), float(calculated_total_sales),
                        float(dep_amount), bank_name, float(calculated_variance), status, remarks
                    ]
                    worksheet_sales.append_row(new_sales_row)
                    st.success("✅ ሮቤል፡ የሽያጭና የሂሳብ ማመሳከሪያ መረጃው በቀጥታ ወደ Google Sheets ተልኳል!")
                else:
                    st.error("❌ ወደ Google Sheets መፃፍ አልተቻለም።")

    # -------------------------------------------------------------------
    # 4. SYSTEM SETTINGS
    # -------------------------------------------------------------------
    elif role == "⚙️ የሲስተም ማስተካከያ (System Settings)":
        st.header("⚙️ የሲስተም ቅንብሮችና የዋጋ ማስተካከያ ማዕከል")
        st.warning("እዚህ ጋር የሚቀይሩት ዋጋ በቀጥታ ሮቤል ጋ ያለውን የሽያጭ አውቶማቲክ ማባዣ ፎርሙላ ይቀይረዋል።")
        
        if worksheet_settings:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("💰 የምርት መሸጫ ዋጋ ቅንብር")
                new_p200 = st.number_input("ባለ 200ግ ሳሙና ካርቶን መሸጫ ዋጋ (ETB)", value=price_200g, step=50.0)
                new_p100 = st.number_input("ባለ 100ግ ሳሙና ካርቶን መሸጫ ዋጋ (ETB)", value=price_100g, step=50.0)
                
            with col2:
                st.subheader("ዝርዝሮች (የመኪና እና ባንኮች)")
                trucks_str = st.text_input("የጭነት መኪናዎች (በኮማ `,` በመለየት ያስገቡ)", value=",".join(truck_options))
                banks_str = st.text_input("የባንክ ስሞች (በኮማ `,` በመለየት ያስገቡ)", value=",".join(bank_options))
                
            if st.button("💾 ሙሉ አዲስ ቅንብሮችን ወደ Google Sheets አዘምን"):
                # Clear and write fresh configurations
                worksheet_settings.clear()
                worksheet_settings.append_row(["Setting", "Value"])
                worksheet_settings.append_row(["price_200g", str(new_p200)])
                worksheet_settings.append_row(["price_100g", str(new_p100)])
                worksheet_settings.append_row(["trucks", trucks_str])
                worksheet_settings.append_row(["banks", banks_str])
                st.success("✅ አዳዲስ የዋጋና የማዋቀሪያ ቅንብሮች በGoogle Sheets ላይ በተሳካ ሁኔታ ተሻሽለዋል!")
        else:
            st.error("❌ ከGoogle Sheets Settings ማህደር ጋር መገናኘት አልተቻለም።")

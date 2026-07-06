import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# 1. Page Configuration
st.set_page_config(page_title="መላ ሳሙና እና ዲተርጀንት ሽያጭ መመዝገቢያ", layout="wide")

# 2. Define Default Passwords (With English-only keys for Executive and System Settings)
PASSWORDS = {
    "Executive Dashboard": st.secrets.get("PASSWORD_EXEC", "exec123"),
    "🏭 የኢንቬንተሪ ክፍል (Inventory Dispatch)": st.secrets.get("PASSWORD_INV", "inv123"),
    "💰 የሽያጭ ክፍል - ሮቤል (Sales Department)": st.secrets.get("PASSWORD_ROBEL", "robel123"),
    "System Settings": st.secrets.get("PASSWORD_SETTINGS", "settings123")
}

# 3. Google Sheets Connection Setup
@st.cache_resource
def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        gcp_creds = st.secrets["gcp_service_account"]
        
        creds_dict = {
            "type": gcp_creds["type"],
            "project_id": gcp_creds["project_id"],
            "private_key_id": gcp_creds["private_key_id"],
            "private_key": gcp_creds["private_key"].replace("\\n", "\n"),
            "client_email": gcp_creds["client_email"],
            "client_id": gcp_creds["client_id"],
            "auth_uri": gcp_creds["auth_uri"],
            "token_uri": gcp_creds["token_uri"],
            "auth_provider_x509_cert_url": gcp_creds["auth_provider_x509_cert_url"],
            "client_x509_cert_url": gcp_creds["client_x509_cert_url"]
        }
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ ከGoogle Sheets ጋር መገናኘት አልተቻለም። ስህተት: {e}")
        return None

def get_sheet_data(sheet_name):
    client = get_gspread_client()
    if client:
        try:
            spreadsheet_url = st.secrets["google_sheet_url"]
            spreadsheet = client.open_by_url(spreadsheet_url)
            worksheet = spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_records()
            return pd.DataFrame(data), worksheet
        except Exception as e:
            st.error(f"❌ ማህደሩን ማንበብ አልተቻለም ({sheet_name}): {e}")
    return pd.DataFrame(), None

# --- Main Interface ---
st.title("🧼 መላ ሳሙና እና ዲተርጀንት ማከፋፈያና ሽያጭ መመዝገቢያ")
st.markdown("---")

# Role Selection Sidebar
st.sidebar.header("🔐 የሥራ ክፍል መግቢያ (User Login)")
role = st.sidebar.radio(
    "የሚገቡበትን የስራ ክፍል ይምረጡ:",
    ["Executive Dashboard", 
     "🏭 የኢንቬንተሪ ክፍል (Inventory Dispatch)", 
     "💰 የሽያጭ ክፍል - ሮቤል (Sales Department)", 
     "System Settings"]
)

password_input = st.sidebar.text_input(f"የ {role} የይለፍ ቃል ያስገቡ", type="password")

if not password_input:
    st.info("👋 እባክዎ ለመቀጠል በግራ በኩል ባለው ሳጥን ውስጥ የሥራ ክፍልዎን የይለፍ ቃል (Password) ያስገቡ።")
elif password_input != PASSWORDS[role]:
    st.error("❌ የተሳሳተ የይለፍ ቃል ነው! እባክዎ እንደገና ይሞክሩ።")
else:
    st.sidebar.success(f"🔓 በተሳካ ሁኔታ ገብተዋል!")
    
    df_settings, worksheet_settings = get_sheet_data("System_Settings")
    
    # CRASH-PROOF SETTINGS EXTRACTION
    price_200g = 1800.0
    price_100g = 1750.0
    truck_options = ["TRUCK-01 (አክሊሉ አሰፋ)", "TRUCK-02 (ዘመን)"]
    bank_options = ["የኢትዮጵያ ንግድ ባንክ (CBE)", "አዋሽ ባንክ (Awash)", "ዳሽን ባንክ (Dashen)", "ወጋገን ባንክ (Wegagen)", "ህብረት ባንክ(Hibret)", "አቢሲኒያ ባንክ(BOA)", "አባይ ባንክ (Abay Bank)"]

    if not df_settings.empty:
        try:
            if 'Setting' in df_settings.columns and 'Value' in df_settings.columns:
                p200_rows = df_settings.loc[df_settings['Setting'] == 'price_200g', 'Value'].values
                if len(p200_rows) > 0: price_200g = float(p200_rows[0])
                
                p100_rows = df_settings.loc[df_settings['Setting'] == 'price_100g', 'Value'].values
                if len(p100_rows) > 0: price_100g = float(p100_rows[0])
                
                truck_rows = df_settings.loc[df_settings['Setting'] == 'trucks', 'Value'].values
                if len(truck_rows) > 0: truck_options = truck_rows[0].split(',')
                
                bank_rows = df_settings.loc[df_settings['Setting'] == 'banks', 'Value'].values
                if len(bank_rows) > 0: bank_options = bank_rows[0].split(',')
            else:
                price_200g = float(df_settings.iloc[0, 1])
                price_100g = float(df_settings.iloc[1, 1])
                truck_options = str(df_settings.iloc[2, 1]).split(',')
                bank_options = str(df_settings.iloc[3, 1]).split(',')
        except Exception:
            pass

    # 1. EXECUTIVE DASHBOARD
    if role == "Executive Dashboard":
        st.header("📈 የኩባንያው አጠቃላይ የሽያጭና እንቅስቃሴ ሪፖርት (Executive Panel)")
        
        df_sales, _ = get_sheet_data("Sales_Tracker")
        df_inv, _ = get_sheet_data("Inventory_Dispatch")
        
        total_sales_val = df_sales.iloc[:, 6].astype(float).sum() if not df_sales.empty and len(df_sales.columns) > 6 else 0
        total_dep_val = df_sales.iloc[:, 7].astype(float).sum() if not df_sales.empty and len(df_sales.columns) > 7 else 0
        total_variance = df_sales.iloc[:, 9].astype(float).sum() if not df_sales.empty and len(df_sales.columns) > 9 else 0
        
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

    # 2. INVENTORY DISPATCH
    elif role == "🏭 የኢንቬንተሪ ክፍል (Inventory Dispatch)":
        st.header("🏭 የኢንቬንተሪ ጭነት መመዝገቢያ")
        _, worksheet_inv = get_sheet_data("Inventory_Dispatch")
        
        with st.form("inventory_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                dispatch_date = st.date_input("የተጫነበት ቀን (Date)", datetime.today())
                truck = st.selectbox("የመኪና / የሹፌር ኮድ (Select Truck)", truck_options)
            with col2:
                qty_200g = st.number_input("ባለ 200ግ የተላከ ካርቶን", min_value=0, step=1)
                qty_100g = st.number_input("ባለ 100ግ የተላከ ካርቶን", min_value=0, step=1)
                
            remarks = st.text_area("ማብራሪያ / ሪማርክ (Remarks)")
            submit_inv = st.form_submit_button("🚀 የጭነት መረጃውን ወደ Google Sheets ላክ")
            
            if submit_inv:
                if worksheet_inv:
                    new_row = [dispatch_date.strftime('%Y-%m-%d'), truck, int(qty_200g), int(qty_100g), remarks]
                    worksheet_inv.append_row(new_row)
                    st.success(f"✅ የጭነት መረጃው በተሳካ ሁኔታ ተቀምጧል!")

    # 3. SALES DEPARTMENT (ROBEL)
    elif role == "💰 የሽያጭ ክፍል - ሮቤል (Sales Department)":
        st.header("💰 የሽያጭና ባንክ ሪኮንሲሊየሽን መመዝገቢያ (ሮቤል)")
        _, worksheet_sales = get_sheet_data("Sales_Tracker")
        
        with st.form("sales_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                sales_date = st.date_input("የሽያጭ ቀን (Sales Date)", datetime.today())
                truck = st.selectbox("የመኪና / የሹፌር ኮድ (Select Truck)", truck_options)
                recv_200g = st.number_input("የተረከቡት ባለ 200ግ ካርቶን", min_value=0, step=1)
                recv_100g = st.number_input("የተረከቡት ባለ 100ግ ካርቶን", min_value=0, step=1)
                
            with col2:
                sold_200g = st.number_input("የተሸጠ ባለ 200ግ ካርቶን", min_value=0, step=1)
                sold_100g = st.number_input("የተሸጠ ባለ 100ግ ካርቶን", min_value=0, step=1)
                dep_amount = st.number_input("ባንክ የገባው ጠቅላላ ብር (ETB)", min_value=0.0, step=100.0)
                bank_name = st.selectbox("የባንክ ስም (Select Bank)", bank_options)
                
            remarks = st.text_area("ማብራሪያ / የሽያጭ ማስታወሻ (Remarks)")
            
            calc_sales_200 = sold_200g * price_200g
            calc_sales_100 = sold_100g * price_100g
            calculated_total_sales = calc_sales_200 + calc_sales_100
            calculated_variance = dep_amount - calculated_total_sales
            
            if calculated_variance < 0: status = "ጉድለት አለበት (Shortage)"
            elif calculated_variance > 0: status = "ብልጫ አለው (Overage)"
            else: status = "የተስተካከለ (Balanced)"
                
            submit_sales = st.form_submit_button("💾 የሽያጭ መረጃውን ወደ Google Sheets አስቀምጥ")
            
            if submit_sales:
                if worksheet_sales:
                    new_sales_row = [
                        sales_date.strftime('%Y-%m-%d'), truck, int(recv_200g), int(recv_100g),
                        int(sold_200g), int(sold_100g), float(calculated_total_sales),
                        float(dep_amount), bank_name, float(calculated_variance), status, remarks
                    ]
                    worksheet_sales.append_row(new_sales_row)
                    st.success("✅ የሽያጭ መረጃው በቀጥታ ወደ Google Sheets ተልኳል!")

    # 4. SYSTEM SETTINGS & DATA CORRECTION (CRUD)
    elif role == "System Settings":
        st.header("⚙️ የሲስተም ቅንብሮችና የተሳሳቱ መረጃዎች ማስተካከያ ማዕከል")
        
        tab_config, tab_edit_sales, tab_edit_inv = st.tabs([
            "⚙️ የዋጋና መኪና ቅንብሮች", 
            "✏️ የሽያጭ መዝገብ ማስተካከያ (Edit Sales)", 
            "✏️ የኢንቬንተሪ መዝገብ ማስተካከያ (Edit Inventory)"
        ])
        
        with tab_config:
            if worksheet_settings:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("💰 የምርት መሸጫ ዋጋ ቅንብር")
                    new_p200 = st.number_input("ባለ 200ግ ሳሙና ካርቶን መሸጫ ዋጋ (ETB)", value=price_200g, step=50.0)
                    new_p100 = st.number_input("ባለ 100ግ ሳሙና ካርቶን መሸጫ ዋጋ (ETB)", value=price_100g, step=50.0)
                with col2:
                    st.subheader("ዝርዝሮች (የመኪና እና ባንኮች)")
                    truck_options_str = ",".join(truck_options)
                    bank_options_str = ",".join(bank_options)
                    trucks_str = st.text_input("የጭነት መኪናዎች (በኮማ `,` መለየት)", value=truck_options_str)
                    banks_str = st.text_input("የባንክ ስሞች (በኮማ `,` መለየት)", value=bank_options_str)
                    
                if st.button("💾 ሙሉ አዲስ ቅንብሮችን ወደ Google Sheets አዘምን"):
                    worksheet_settings.clear()
                    worksheet_settings.append_row(["Setting", "Value"])
                    worksheet_settings.append_row(["price_200g", str(new_p200)])
                    worksheet_settings.append_row(["price_100g", str(new_p100)])
                    worksheet_settings.append_row(["trucks", trucks_str])
                    worksheet_settings.append_row(["banks", banks_str])
                    st.success("✅ አዳዲስ ቅንብሮች በGoogle Sheets ላይ ተሻሽለዋል!")
                    st.rerun()

        # TAB 2: Edit/Delete Sales Tracker Data
        with tab_edit_sales:
            st.subheader("✏️ በሮቤል የተመዘገቡ የተሳሳቱ የሽያጭ መረጃዎችን ማስተካከያ")
            df_sales_raw, worksheet_sales = get_sheet_data("Sales_Tracker")
            
            if not df_sales_raw.empty:
                df_sales_raw['Sheet_Row_ID'] = range(2, len(df_sales_raw) + 2)
                sales_options = df_sales_raw.to_dict(orient='records')
                
                st.write("ማስተካከል ወይም መሰረዝ የሚፈልጉትን መስመር ይምረጡ፦")
                row_to_edit = st.selectbox(
                    "የሚስተካከለውን መዝገብ በቀን እና በመኪና ይምረጡ:",
                    options=sales_options,
                    format_func=lambda x: f"መስመር {x.get('Sheet_Row_ID', '')} | ቀን: {list(x.values())[0]} | መኪና: {list(x.values())[1]} | ባንክ ገቢ: {list(x.values())[7] if len(x.values()) > 7 else ''}"
                )
                
                if row_to_edit:
                    st.markdown("---")
                    st.warning(f"⚠️ አሁን እየቀየሩ ያሉት መስመር ቁጥር **{row_to_edit['Sheet_Row_ID']}** ላይ ያለውን መረጃ ነው!")
                    
                    vals = list(row_to_edit.values())
                    with st.form("edit_sales_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            e_date = st.text_input("ቀን (YYYY-MM-DD)", value=str(vals[0]))
                            e_truck = st.selectbox("የመኪና ኮድ", truck_options, index=truck_options.index(str(vals[1])) if str(vals[1]) in truck_options else 0)
                            e_recv_200 = st.number_input("የተረከቡት ባለ 200ግ", value=int(vals[2]) if str(vals[2]).isdigit() else 0, step=1)
                            e_recv_100 = st.number_input("የተረከቡት ባለ 100ግ", value=int(vals[3]) if str(vals[3]).isdigit() else 0, step=1)
                        with col2:
                            e_sold_200 = st.number_input("የተሸጠ ባለ 200ግ", value=int(vals[4]) if str(vals[4]).isdigit() else 0, step=1)
                            e_sold_100 = st.number_input("የተሸጠ ባለ 100ግ", value=int(vals[5]) if str(vals[5]).isdigit() else 0, step=1)
                            e_dep = st.number_input("ባንክ የገባው ብር", value=float(vals[7]) if str(vals[7]).replace('.','',1).isdigit() else 0.0, step=100.0)
                            e_bank = st.selectbox("የባንክ ስም", bank_options, index=bank_options.index(str(vals[8])) if str(vals[8]) in bank_options else 0)
                        
                        e_remarks = st.text_area("ማብራሪያ", value=str(vals[11]) if len(vals) > 11 else "")
                        
                        e_total_sales = (e_sold_200 * price_200g) + (e_sold_100 * price_100g)
                        e_variance = e_dep - e_total_sales
                        if e_variance < 0: e_status = "ጉድለት አለበት (Shortage)"
                        elif e_variance > 0: e_status = "ብልጫ አለው (Overage)"
                        else: e_status = "የተስተካከለ (Balanced)"
                        
                        btn_update, btn_delete = st.columns(2)
                        with btn_update:
                            submit_update = st.form_submit_button("🔄 መረጃውን አስተካክልና በጉግል ሺት ላይ ቀይር")
                        with btn_delete:
                            submit_delete = st.form_submit_button("🗑️ ይህንን ሙሉ መዝገብ ከሲስተሙ ሰርዝ")
                            
                        if submit_update:
                            updated_row = [
                                e_date, e_truck, int(e_recv_200), int(e_recv_100),
                                int(e_sold_200), int(e_sold_100), float(e_total_sales),
                                float(e_dep), e_bank, float(e_variance), e_status, e_remarks
                            ]
                            worksheet_sales.update(range_name=f"A{row_to_edit['Sheet_Row_ID']}:L{row_to_edit['Sheet_Row_ID']}", values=[updated_row])
                            st.success(f"✅ መስመር {row_to_edit['Sheet_Row_ID']} በተሳካ ሁኔታ ተሻሽሏል!")
                            st.rerun()
                            
                        if submit_delete:
                            worksheet_sales.delete_rows(row_to_edit['Sheet_Row_ID'])
                            st.success(f"🗑️ መዝገቡ ሙሉ በሙሉ ተሰርዟል!")
                            st.rerun()
            else:
                st.info("የሽያጭ ማህደሩ ባዶ ነው።")

        # TAB 3: Edit/Delete Inventory Dispatch Data
        with tab_edit_inv:
            st.subheader("✏️ በኢንቬንተሪ ክፍል የተመዘገቡ የጭነት መረጃዎችን ማስተካከያ")
            df_inv_raw, worksheet_inv = get_sheet_data("Inventory_Dispatch")
            
            if not df_inv_raw.empty:
                df_inv_raw['Sheet_Row_ID'] = range(2, len(df_inv_raw) + 2)
                inv_options = df_inv_raw.to_dict(orient='records')
                
                row_to_edit_inv = st.selectbox(
                    "የሚስተካከለውን የጭነት መዝገብ ይምረጡ:",
                    options=inv_options,
                    format_func=lambda x: f"መስመር {x.get('Sheet_Row_ID', '')} | ቀን: {list(x.values())[0]} | መኪና: {list(x.values())[1]} | ባለ 200ግ: {list(x.values())[2]}"
                )
                
                if row_to_edit_inv:
                    st.markdown("---")
                    st.warning(f"⚠️ አሁን እየቀየሩ ያሉት የኢንቬንተሪ መስመር ቁጥር **{row_to_edit_inv['Sheet_Row_ID']}** ነው!")
                    
                    vals_inv = list(row_to_edit_inv.values())
                    with st.form("edit_inv_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            ei_date = st.text_input("ቀን (YYYY-MM-DD)", value=str(vals_inv[0]))
                            ei_truck = st.selectbox("የመኪና ኮድ", truck_options, index=truck_options.index(str(vals_inv[1])) if str(vals_inv[1]) in truck_options else 0)
                        with col2:
                            ei_qty_200 = st.number_input("ባለ 200ግ የተላከ ካርቶን", value=int(vals_inv[2]) if str(vals_inv[2]).isdigit() else 0, step=1)
                            ei_qty_100 = st.number_input("ባለ 100ግ የተላከ ካርቶን", value=int(vals_inv[3]) if str(vals_inv[3]).isdigit() else 0, step=1)
                            
                        ei_remarks = st.text_area("ማብራሪያ/ሪማርክ", value=str(vals_inv[4]) if len(vals_inv) > 4 else "")
                        
                        btn_update_inv, btn_delete_inv = st.columns(2)
                        with btn_update_inv:
                            submit_update_inv = st.form_submit_button("🔄 የጭነት መረጃውን አስተካክል")
                        with btn_delete_inv:
                            submit_delete_inv = st.form_submit_button("🗑️ ይህንን የጭነት መዝገብ ሰርዝ")
                            
                        if submit_update_inv:
                            updated_inv_row = [ei_date, ei_truck, int(ei_qty_200), int(ei_qty_100), ei_remarks]
                            worksheet_inv.update(range_name=f"A{row_to_edit_inv['Sheet_Row_ID']}:E{row_to_edit_inv['Sheet_Row_ID']}", values=[updated_inv_row])
                            st.success(f"✅ የኢንቬንተሪ መስመር {row_to_edit_inv['Sheet_Row_ID']} ተስተካክሏል!")
                            st.rerun()
                            
                        if submit_delete_inv:
                            worksheet_inv.delete_rows(row_to_edit_inv['Sheet_Row_ID'])
                            st.success(f"🗑️ የጭነት መዝገቡ በተሳካ ሁኔታ ተሰርዟል!")
                            st.rerun()
            else:
                st.info("የኢንቬንተሪ ማህደሩ ባዶ ነው።")

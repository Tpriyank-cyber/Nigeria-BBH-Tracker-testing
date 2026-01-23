# -*- coding: utf-8 -*-
"""
Created on Fri Jan 23 16:58:50 2026

@author: tpriyank
"""

import base64
import streamlit as st
from io import BytesIO
import pandas as pd
from streamlit_option_menu import option_menu

# -------------------- Streamlit Settings --------------------
favicon = "favicon.png"
color_1 = "transparent"
st.set_page_config(page_title="Airtel Nigeria BBH Tracker", page_icon=favicon, layout="wide")

background_text_color = "#001135"
background_header_text_color = "#a235b6"
background_header_font_style = "18px"
background_font_style = "18px"

# Sidebar Menu
with st.sidebar:
    selected = option_menu(
        menu_title="Airtel Nigeria",
        options=["About", "Tool Name", "Contact Us"],
        icons=["person", "slack", "telephone"],
        menu_icon='None',
        styles={
            "container": {"background-color": color_1},
            "icon": {"font-size": "23px"},
            "menu-icon": {"color": "red"},
            "menu-title": {"color": "#660a93", "text-align": "center", "font-weight": "bold"},
            "nav-link": {
                "color": "#61206d",
                "font-size": "17px",
                "text-align": "left",
                "font-weight": "bold",
                "font-family": "Nokia Pure Headline",
                "margin-top": "0px",
            },
            "nav-link-selected": {"background-image": "linear-gradient(to left, #a235b6, #a235b6)", "color": "white"},
        },
    )

# -------------------- About Page --------------------
if selected == "About":
    st.markdown("## ℹ Tool Introduction")
    st.write(
        "This Multi-Tech Data BBH Processing tool automates **BBH level KPI aggregation** "
        "for **Cell views**, enabling faster and accurate OSS-based performance analysis."
    )
    st.markdown("## 🚀 Key Capabilities")
    st.markdown("""
    - BBH/Day KPI aggregation  
    - Cell level analysis  
    """)

if selected == "Contact Us":
    st.markdown("## 📞 Contact Us")
    st.write(
        "**Developer:** Priyank Tomar  \n"
        "**Domain:** 2G / 3G / LTE - OSS / KPI Automation   \n"
        "**Email:** tomar.priyank@nokia.com"
    )

# -------------------- Tool Page --------------------
elif selected == "Tool Name":
    st.write(f"<span style='color: {background_text_color}; font-weight: bold; font-size:{background_font_style}; font-family: Nokia Pure Headline Light;'>Select Technology & Upload File:</span>", unsafe_allow_html=True)

    # Tech selection
    tech_option = st.selectbox("Airtel Nigeria BBH Tracker:", ["2G", "3G", "4G", "All"])
    st.write("**Developed by Priyank Tomar**")
    # Multiple uploads for OSS
    uploaded_file_oss1 = st.file_uploader("Upload Excel File OSS 1", type=["xlsx"], key="oss1")
    uploaded_file_oss2 = st.file_uploader("Upload Excel File OSS 2", type=["xlsx"], key="oss2")

    if uploaded_file_oss1 and uploaded_file_oss2:
        # Read input files separately
        xls1 = pd.ExcelFile(uploaded_file_oss1)
        xls2 = pd.ExcelFile(uploaded_file_oss2)
    
        final_outputs = []


        
        # -------------------- 2G Processing --------------------
        if tech_option in ["2G", "All"]:
            # BBH sheets
            df_bbh_oss1 = pd.read_excel(xls1, sheet_name="BH_2G_N1")
            df_bbh_oss2 = pd.read_excel(xls2, sheet_name="BH_2G_N2")
            df_bbh = pd.concat([df_bbh_oss1, df_bbh_oss2], ignore_index=True).drop(index=1, errors='ignore').reset_index(drop=True)
            
            # Day sheets
            df_day_oss1 = pd.read_excel(xls1, sheet_name="2G_N1_Daily")
            df_day_oss2 = pd.read_excel(xls2, sheet_name="2G_N2_Daily")
            df_day = pd.concat([df_day_oss1, df_day_oss2], ignore_index=True).drop(index=1, errors='ignore').reset_index(drop=True)
            
            # Dates
            df_bbh["Period start time"] = pd.to_datetime(df_bbh["Period start time"])
            df_day["Period start time"] = pd.to_datetime(df_day["Period start time"])
            df_bbh["DATE"] = df_bbh["Period start time"].dt.strftime("%d-%b")
            df_day["DATE"] = df_day["Period start time"].dt.strftime("%d-%b")
            
            # KPIs
            bbh_kpis = ["TCH_Availability", "AccessibilityCSSR", "SDCCH Blocking",
                        "TCH Blocking (User Perceived)", "SDCCH Drop", "CDR_2G",
                        "HOSR_HW_2G", "TotalTrafficErlangs", "Total_Data_Traffic_HW"]
            bbh_rename = {"TotalTrafficErlangs":"TotalTrafficErlangs_BBH", "Total_Data_Traffic_HW":"Total_Data_Traffic_BBH"}
            day_kpis = ["TotalTrafficErlangs", "Total_Data_Traffic_HW", "Cell avail accuracy 1s cellL"]
            day_rename = {"TotalTrafficErlangs":"TotalTrafficErlangs_DAY", "Total_Data_Traffic_HW":"Total_Data_Traffic_DAY"}
            
            df_bbh = df_bbh.rename(columns=bbh_rename)
            df_day = df_day.rename(columns=day_rename)
            
            # Melt long format
            df_bbh_long = df_bbh.melt(id_vars=["BSC name", "Segment Name", "DATE"],
                                       value_vars=[bbh_rename.get(k,k) for k in bbh_kpis],
                                       var_name="KPI", value_name="VALUE")
            df_day_long = df_day.melt(id_vars=["BSC name", "Segment Name", "DATE"],
                                       value_vars=[day_rename.get(k,k) for k in day_kpis],
                                       var_name="KPI", value_name="VALUE")
            df_all_2G = pd.concat([df_bbh_long, df_day_long], ignore_index=True)
            
            # Pivot
            final_2G = df_all_2G.pivot_table(index=["BSC name", "Segment Name", "KPI"],
                                             columns="DATE", values="VALUE", aggfunc="first").reset_index()
            
            # Thresholds
            thresholds_2G = {
                "TCH_Availability": (">=", 99.5),
                "AccessibilityCSSR": (">=", 98),
                "SDCCH Blocking": ("<=", 1.25),
                "TCH Blocking (User Perceived)": ("<=", 1.25),
                "SDCCH Drop": ("<=", 1.25),
                "CDR_2G": ("<=", 1.25),
                "HOSR_HW_2G": (">=", 90),
                "Cell avail accuracy 1s cellL": (">=", 99.5)
            }
            date_cols = sorted([c for c in final_2G.columns if c not in ["BSC name", "Segment Name", "KPI"]],
                               key=lambda x: pd.to_datetime(x, format="%d-%b"))
            last_date = date_cols[-1]
            rna_kpi = "TCH_Availability"
            
            # Dynamic remark function
            traffic_kpis = ["TotalTrafficErlangs_BBH", "TotalTrafficErlangs_DAY", "Total_Data_Traffic_BBH", "Total_Data_Traffic_DAY"]
            
            def enhanced_remark_2G(row):
                kpi = row["KPI"]
                v = row[last_date]
                if pd.isna(v):
                    return "NO DATA"
                if kpi in ["TCH_Availability", "Cell avail accuracy 1s cellL"] and v==0:
                    return "SITE/CELL DOWN"
                remark=""
                threshold_broken=False
                if kpi in thresholds_2G:
                    op,val=thresholds_2G[kpi]
                    if (op==">=" and v>=val) or (op=="<=" and v<=val):
                        remark="KPI Stable/Meeting Threshold"
                    else:
                        remark="KPI not ok"
                        threshold_broken=True
                if kpi not in traffic_kpis and threshold_broken:
                    mask=(final_2G["BSC name"]==row["BSC name"]) & (final_2G["Segment Name"]==row["Segment Name"]) & (final_2G["KPI"]==rna_kpi)
                    if not final_2G.loc[mask].empty:
                        rna_val=final_2G.loc[mask,last_date].values[0]
                        rna_val=round(float(rna_val),2)
                        rna_op,rna_thr=thresholds_2G[rna_kpi]
                        if (rna_op==">=" and rna_val<rna_thr) or (rna_op=="<=" and rna_val>rna_thr):
                            remark += f", RNA UNSTABLE {rna_val}%"
                return remark
            
            final_2G["REMARKS"] = final_2G.apply(enhanced_remark_2G, axis=1)
            kpi_cols=[c for c in final_2G.columns if c not in ["BSC name","Segment Name","KPI","REMARKS"]]
            final_2G[kpi_cols]=final_2G[kpi_cols].apply(pd.to_numeric, errors='coerce').round(2)
            final_outputs.append(final_2G)
        
        # -------------------- 3G Processing --------------------
        if tech_option in ["3G", "All"]:
            df_3g_day_oss1 = pd.read_excel(xls1, sheet_name="3G_N1")
            df_3g_day_oss2 = pd.read_excel(xls2, sheet_name="3G_N2")
            
            # Merge the two OSS sheets
            df_3g_day = pd.concat([df_3g_day_oss1, df_3g_day_oss2], ignore_index=True).drop(index=1, errors='ignore').reset_index(drop=True)
            
            # Convert datetime and create DATE column
            df_3g_day["Period start time"] = pd.to_datetime(df_3g_day["Period start time"])
            df_3g_day["DATE"] = df_3g_day["Period start time"].dt.strftime("%d-%b")
            
            # Select relevant KPIs and rename for clarity
            day_3g_kpis = [
                "Cell Availability, excluding blocked by user state (BLU)",
                "CS_RRC_SR",
                "CS_RAB_SR",
                "PS_RRC_SR_New2",
                "PS_RAB_SR_NEW2",
                "Voice_DCR",
                "PS_DCR",
                "HSPA Drop Rate",
                "CS_traffic",
                "Total PS Traffic (MB)",
                "SHO_SR",
                "HS_THR",
                "RTWP"
            ]
            
            day_3g_rename = {
                "Cell Availability, excluding blocked by user state (BLU)": "RNA %",
                "CS_RRC_SR": "CS RRC Stp SR %",
                "CS_RAB_SR": "CS RAB Stp SR %",
                "PS_RRC_SR_New2": "PS RRC Stp SR %",
                "PS_RAB_SR_NEW2": "PS RAB Stp SR %",
                "Voice_DCR": "VOICE DROP RATE %",
                "PS_DCR": "PS DROP RATE %",
                "HSPA Drop Rate": "HS DROP RATE %",
                "CS_traffic": "Total CS traffic - Erl",
                "Total PS Traffic (MB)": "DATA TRAFFIC_MB",
                "SHO_SR": "SHO SR %",
                "HS_THR": "Act HS-DSCH end usr thp_Kbps",
                "RTWP": "Avg RTWP"
            }
            
            df_3g_day = df_3g_day.rename(columns=day_3g_rename)
            
            # Unpivot to long format
            df_3g_long = df_3g_day.melt(
                id_vars=["WBTS name", "WCEL name", "DATE"],
                value_vars=[day_3g_rename.get(k, k) for k in day_3g_kpis],
                var_name="KPI",
                value_name="VALUE"
            )
            
            # Pivot → DATE as columns
            final_3G = df_3g_long.pivot_table(
                index=["WBTS name", "WCEL name", "KPI"],
                columns="DATE",
                values="VALUE",
                aggfunc="first"
            ).reset_index()
            
            # 3G thresholds
            thresholds_3G = {
                "RNA %": (">=", 98),
                "CS RRC Stp SR %": (">=", 98),
                "CS RAB Stp SR %": (">=", 98),
                "PS RRC Stp SR %": (">=", 98),
                "PS RAB Stp SR %": (">=", 98),
                "VOICE DROP RATE %": ("<=", 0.7),
                "PS DROP RATE %": ("<=", 0.7),
                "HS DROP RATE %": ("<=", 0.7),
                "Total CS traffic - Erl": (">", 0),
                "DATA TRAFFIC_MB": (">", 0),
                "SHO SR %": (">=", 99),
                "Act HS-DSCH end usr thp_Kbps": (">=", 1000),
                "Avg RTWP": ("<=", -97)
            }
            
            # Last date detection
            date_cols_3G = sorted([c for c in final_3G.columns if c not in ["WBTS name", "WCEL name", "KPI"]],
                                  key=lambda x: pd.to_datetime(x, format="%d-%b"))
            last_date = date_cols_3G[-1]
            
            # Apply remarks
            def enhanced_remark_3G(row):
                kpi = row["KPI"]
                v = row[last_date]
                if pd.isna(v):
                    return "NO DATA"
                remark = ""
                if kpi in thresholds_3G:
                    op, val = thresholds_3G[kpi]
                    if (op == ">=" and v >= val) or (op == "<=" and v <= val) or (op == ">" and v > val) or (op == "<" and v < val):
                        remark = "KPI Stable/Meeting Threshold"
                    else:
                        remark = "KPI not ok"
                return remark
            
            final_3G["REMARKS"] = final_3G.apply(enhanced_remark_3G, axis=1)
            
            # Round KPI values
            kpi_cols_3G = [c for c in final_3G.columns if c not in ["WBTS name", "WCEL name", "KPI", "REMARKS"]]
            final_3G[kpi_cols_3G] = final_3G[kpi_cols_3G].apply(pd.to_numeric, errors='coerce').round(2)
            final_outputs.append(final_3G)

        
        # -------------------- 4G Processing --------------------
        if tech_option in ["4G", "All"]:
            df_4g_bbh_oss1 = pd.read_excel(xls1, sheet_name="BH_4G_N1")
            df_4g_bbh_oss2 = pd.read_excel(xls2, sheet_name="BH_4G_N2")
            df_4g_bbh = pd.concat([df_4g_bbh_oss1, df_4g_bbh_oss2], ignore_index=True).drop(index=1, errors='ignore').reset_index(drop=True)
            
            # Read Daily 7-day sheets from two OSS
            df_4g_day_oss1 = pd.read_excel(xls1, sheet_name="4G_N1")
            df_4g_day_oss2 = pd.read_excel(xls2, sheet_name="4G_N2")
            df_4g_day = pd.concat([df_4g_day_oss1, df_4g_day_oss2], ignore_index=True).drop(index=1, errors='ignore').reset_index(drop=True)
            
            # Convert datetime and create DATE column
            df_4g_bbh["Period start time"] = pd.to_datetime(df_4g_bbh["Period start time"])
            df_4g_day["Period start time"] = pd.to_datetime(df_4g_day["Period start time"])
            df_4g_bbh["DATE"] = df_4g_bbh["Period start time"].dt.strftime("%d-%b")
            df_4g_day["DATE"] = df_4g_day["Period start time"].dt.strftime("%d-%b")
            
            # KPI selection + rename
            bbh_4g_kpis = [
                "Cell Avail", "Total E-UTRAN RRC conn stp SR", "E-UTRAN E-RAB stp SR",
                "Setup Session Success Rate", "TOTALHOSRNEW", "CSFB Prep SR New",
                "RRC_CONNECTED_UE_MAX (M8051C56)", "Perc DL PRB Util", "Perc UL PRB Util",
                "Avg RSSI for PUCCH", "Avg RRC conn UE", "E-UTRAN E-RAB DR, RAN View",
                "DLUserThroughputMbps", "ULUserThroughoutMbps",
                "Total_Data_Volume_Gb New(1024)", "DL_Data_Volume_Gb New(1024)", "UL_Data_Volume_Gb New(1024)"
            ]
            bbh_4g_rename = {
                "Total_Data_Volume_Gb New(1024)": "Total_Data_Volume_BBH",
                "DL_Data_Volume_Gb New(1024)": "DL_Data_Volume_BBH",
                "UL_Data_Volume_Gb New(1024)": "UL_Data_Volume_BBH"
            }
            
            day_4g_kpis = [
                "Cell Avail excl BLU", "Total_Data_Volume_Gb New(1024)",
                "DL_Data_Volume_Gb New(1024)", "UL_Data_Volume_Gb New(1024)"
            ]
            day_4g_rename = {
                "Total_Data_Volume_Gb New(1024)": "Total_Data_Volume_DAY",
                "DL_Data_Volume_Gb New(1024)": "DL_Data_Volume_DAY",
                "UL_Data_Volume_Gb New(1024)": "UL_Data_Volume_DAY"
            }
            
            df_4g_bbh = df_4g_bbh.rename(columns=bbh_4g_rename)
            df_4g_day = df_4g_day.rename(columns=day_4g_rename)
            
            # Force numeric for KPIs used in formulas
            for col in ["Total E-UTRAN RRC conn stp SR", "E-UTRAN E-RAB stp SR"]:
                df_4g_bbh[col] = pd.to_numeric(df_4g_bbh[col].astype(str).str.replace(",", ".", regex=False).replace(["-", "N/A", "nan"], pd.NA), errors='coerce')
            
            # Derived KPI – Setup Session Success Rate
            df_4g_bbh["Setup Session Success Rate"] = (df_4g_bbh["Total E-UTRAN RRC conn stp SR"] *
                                                      df_4g_bbh["E-UTRAN E-RAB stp SR"]) / 100
            
            # Unpivot to long format
            df_4g_bbh_long = df_4g_bbh.melt(
                id_vars=["LNBTS name", "LNCEL name", "DATE"],
                value_vars=[bbh_4g_rename.get(k, k) for k in bbh_4g_kpis],
                var_name="KPI",
                value_name="VALUE"
            )
            df_4g_day_long = df_4g_day.melt(
                id_vars=["LNBTS name", "LNCEL name", "DATE"],
                value_vars=[day_4g_rename.get(k, k) for k in day_4g_kpis],
                var_name="KPI",
                value_name="VALUE"
            )
            
            # Merge BBH + Day
            final_4G = pd.concat([df_4g_bbh_long, df_4g_day_long], ignore_index=True)
            
            # Pivot → DATE as columns
            final_4G = final_4G.pivot_table(
                index=["LNBTS name", "LNCEL name", "KPI"],
                columns="DATE",
                values="VALUE",
                aggfunc="first"
            ).reset_index()
            
            # 4G thresholds
            thresholds_4G = {
                "Cell Avail": (">=", 99.5),
                "Cell Avail excl BLU": (">=", 99.5),
                "Total E-UTRAN RRC conn stp SR": (">=", 98),
                "E-UTRAN E-RAB stp SR": (">=", 98),
                "Setup Session Success Rate": (">=", 98),
                "TOTALHOSRNEW": (">=", 98),
                "CSFB Prep SR New": (">=", 98),
                "E-UTRAN E-RAB DR, RAN View": ("<=", 2)
            }
            
            # Last date detection
            date_cols_4G = sorted([c for c in final_4G.columns if c not in ["LNBTS name", "LNCEL name", "KPI"]],
                                  key=lambda x: pd.to_datetime(x, format="%d-%b"))
            last_date = date_cols_4G[-1]
            
            # Apply remarks
            def enhanced_remark_4G(row):
                kpi = row["KPI"]
                v = row[last_date]
                if pd.isna(v):
                    return "NO DATA"
                remark = ""
                if kpi in thresholds_4G:
                    op, val = thresholds_4G[kpi]
                    if (op == ">=" and v >= val) or (op == "<=" and v <= val):
                        remark = "KPI Stable/Meeting Threshold"
                    else:
                        remark = "KPI not ok"
                return remark
            
            final_4G["REMARKS"] = final_4G.apply(enhanced_remark_4G, axis=1)
            
            # Round KPI values
            kpi_cols_4G = [c for c in final_4G.columns if c not in ["LNBTS name", "LNCEL name", "KPI", "REMARKS"]]
            final_4G[kpi_cols_4G] = final_4G[kpi_cols_4G].apply(pd.to_numeric, errors='coerce').round(2)
            final_outputs.append(final_4G)


        
        # -------------------- MERGE ALL OUTPUTS --------------------
        merged_output=pd.concat(final_outputs,ignore_index=True)
        
        # -------------------- DOWNLOAD --------------------
        towrite = BytesIO()
        merged_output.to_excel(towrite, index=False, engine='openpyxl')
        towrite.seek(0)
        st.download_button(label="Download Processed KPI Excel", data=towrite, file_name="Processed_KPIs.xlsx", mime="application/vnd.ms-excel")













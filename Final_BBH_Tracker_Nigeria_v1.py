# -*- coding: utf-8 -*-
"""
Created on Fri Jan 23 16:31:45 2026

@author: tpriyank
"""

import streamlit as st
import pandas as pd
from io import BytesIO
import zipfile

# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(
    page_title="Nokia MAPA KPI Audit Tool",
    layout="wide"
)

st.title("📡 Nokia MAPA KPI Audit Tool")

# ----------------------------------------------------
# HELPERS
# ----------------------------------------------------
def normalize_columns(df, tech):
    if tech == "2G":
        return df.rename(columns={
            "BSC name": "NODE_NAME",
            "Segment Name": "CELL_NAME"
        })
    if tech == "3G":
        return df.rename(columns={
            "WBTS name": "NODE_NAME",
            "WCEL name": "CELL_NAME"
        })
    if tech == "4G":
        return df.rename(columns={
            "LNBTS name": "NODE_NAME",
            "LNCEL name": "CELL_NAME"
        })
    return df


def to_numeric_safe(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = (
                df[c].astype(str)
                .str.replace(",", ".", regex=False)
                .replace(["-", "N/A", "nan"], pd.NA)
            )
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

# ----------------------------------------------------
# FILE UPLOAD
# ----------------------------------------------------
uploaded_files = st.file_uploader(
    "Upload NetAct Excel file(s)",
    type=["xlsx"],
    accept_multiple_files=True
)

tech_option = st.radio(
    "Select Technology",
    ["2G", "3G", "4G", "ALL"],
    horizontal=True
)

# ====================================================
# ===================== 2G ===========================
# ====================================================
def process_2g(files):
    f1, f2 = files[0], files[1]

    df_bbh = pd.concat([
        pd.read_excel(f1, "BH_2G_N1"),
        pd.read_excel(f2, "BH_2G_N2")
    ], ignore_index=True)

    df_day = pd.concat([
        pd.read_excel(f1, "2G_N1_Daily"),
        pd.read_excel(f2, "2G_N2_Daily")
    ], ignore_index=True)

    df_bbh.drop(index=1, errors="ignore", inplace=True)
    df_day.drop(index=1, errors="ignore", inplace=True)

    df_bbh = normalize_columns(df_bbh, "2G")
    df_day = normalize_columns(df_day, "2G")

    df_bbh["Period start time"] = pd.to_datetime(df_bbh["Period start time"])
    df_day["Period start time"] = pd.to_datetime(df_day["Period start time"])

    df_bbh["DATE"] = df_bbh["Period start time"].dt.strftime("%d-%b")
    df_day["DATE"] = df_day["Period start time"].dt.strftime("%d-%b")

    bbh_kpis = [
        "TCH_Availability", "AccessibilityCSSR", "SDCCH Blocking",
        "TCH Blocking (User Perceived)", "SDCCH Drop", "CDR_2G",
        "HOSR_HW_2G", "TotalTrafficErlangs", "Total_Data_Traffic_HW"
    ]

    day_kpis = [
        "TotalTrafficErlangs",
        "Total_Data_Traffic_HW",
        "Cell avail accuracy 1s cellL"
    ]

    df_bbh_long = df_bbh.melt(
        id_vars=["NODE_NAME", "CELL_NAME", "DATE"],
        value_vars=bbh_kpis,
        var_name="KPI",
        value_name="VALUE"
    )

    df_day_long = df_day.melt(
        id_vars=["NODE_NAME", "CELL_NAME", "DATE"],
        value_vars=day_kpis,
        var_name="KPI",
        value_name="VALUE"
    )

    df_all = pd.concat([df_bbh_long, df_day_long], ignore_index=True)

    final_df = df_all.pivot_table(
        index=["NODE_NAME", "CELL_NAME", "KPI"],
        columns="DATE",
        values="VALUE",
        aggfunc="first"
    ).reset_index()

    return final_df

# ====================================================
# ===================== 3G ===========================
# ====================================================
def process_3g(files):
    df = pd.read_excel(files[0])
    df = normalize_columns(df, "3G")

    kpis = [
        "RNA %",
        "CS RRC Stp SR %",
        "CS RAB Stp SR %",
        "PS RRC Stp SR %",
        "PS RAB Stp SR %",
        "VOICE DROP RATE %",
        "PS DROP RATE %",
        "HS DROP RATE %",
        "SHO SR %",
        "Act HS-DSCH  end usr thp_Kbps",
        "Avg RTWP"
    ]

    df = to_numeric_safe(df, kpis)

    records = []
    for kpi in kpis:
        if kpi in df.columns:
            tmp = df[["NODE_NAME", "CELL_NAME"]].copy()
            tmp["KPI"] = kpi
            tmp["VALUE"] = df[kpi]
            records.append(tmp)

    df_long = pd.concat(records, ignore_index=True)

    return df_long

# ====================================================
# ===================== 4G ===========================
# ====================================================
def process_4g(files):
    df = pd.read_excel(files[0])
    df = normalize_columns(df, "4G")

    df = to_numeric_safe(
        df,
        ["Total E-UTRAN RRC conn stp SR", "E-UTRAN E-RAB stp SR"]
    )

    df["Setup Session Success Rate"] = (
        df["Total E-UTRAN RRC conn stp SR"] *
        df["E-UTRAN E-RAB stp SR"]
    ) / 100

    kpis = [
        "Cell Avail",
        "Cell Avail excl BLU",
        "Total E-UTRAN RRC conn stp SR",
        "E-UTRAN E-RAB stp SR",
        "Setup Session Success Rate",
        "TOTALHOSRNEW",
        "CSFB Prep SR New",
        "E-UTRAN E-RAB DR, RAN View",
        "DLUserThroughputMbps",
        "ULUserThroughoutMbps",
        "Total_Data_Volume_Gb New(1024)"
    ]

    df = to_numeric_safe(df, kpis)

    records = []
    for kpi in kpis:
        if kpi in df.columns:
            tmp = df[["NODE_NAME", "CELL_NAME"]].copy()
            tmp["KPI"] = kpi
            tmp["VALUE"] = df[kpi]
            records.append(tmp)

    return pd.concat(records, ignore_index=True)

# ----------------------------------------------------
# RUN
# ----------------------------------------------------
if st.button("🚀 Process KPIs") and uploaded_files:

    outputs = {}

    if tech_option in ["2G", "ALL"]:
        outputs["2G"] = process_2g(uploaded_files)

    if tech_option in ["3G", "ALL"]:
        outputs["3G"] = process_3g(uploaded_files)

    if tech_option in ["4G", "ALL"]:
        outputs["4G"] = process_4g(uploaded_files)

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for tech, df_out in outputs.items():
            buf = BytesIO()
            df_out.to_excel(buf, index=False)
            zf.writestr(f"{tech}_FINAL_OUTPUT.xlsx", buf.getvalue())

    st.success("✅ KPI Processing Completed")

    st.download_button(
        "⬇ Download Results (ZIP)",
        data=zip_buffer.getvalue(),
        file_name="MAPA_KPI_OUTPUT.zip",
        mime="application/zip"
    )

    for tech, df_out in outputs.items():
        st.subheader(f"{tech} Output Preview")
        st.dataframe(df_out.head(20))

import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Page setup
st.set_page_config(layout="wide")
st.title("📊 GEAdrive - Cross_Data Fault Analysis")

# File uploader
uploaded_file = st.file_uploader("📁 Upload the GEADrive Excel File (.xlsx or .xltx)", type=["xlsx", "xltx"])
if not uploaded_file:
    st.warning("Please upload an Excel file to proceed.")
    st.stop()

# Load sheet names
excel_file = pd.ExcelFile(uploaded_file)
sheet_names = excel_file.sheet_names
selected_sheet = st.selectbox("📄 Select a sheet", sheet_names)

# Read selected sheet (skip first row as header)
df = pd.read_excel(uploaded_file, sheet_name=selected_sheet, header=1)

# Fix leading/trailing whitespaces in column names
df.columns = df.columns.str.strip()

# Normalize the 'Year' column
df['Year'] = pd.to_datetime(df['Year'], errors='coerce').dt.year

# Year and Revenue Hour filters side by side
col_year, col_rev = st.columns(2)
with col_year:
    year_option = st.selectbox("📆 Select Year", ["Total", 2023, 2024, 2025])
with col_rev:
    revenue_option = st.selectbox("💰 Select Revenue Hours", ["Total", "Yes", "No"])

# Apply Year filter
if year_option != "Total":
    df = df[df['Year'] == int(year_option)]

# Apply Revenue Hours filter
if revenue_option != "Total":
    df = df[df['Revenue hours'] == revenue_option]

# Filter only Cross_Data fault codes (case-sensitive)
df = df[df['Fault Code'].str.contains("Cross_Data", case=True, na=False)]

# Count total reports
total_reports = len(df)

# Split into false alarms (empty comment) and actual faults
df_false = df[df['Comment'].isna()]
df_actual = df[df['Comment'].notna()]

false_count = len(df_false)
actual_count = len(df_actual)

# Summary Table
st.markdown(f"## 📌 Summary of Cross_Data Faults ({year_option}, Revenue: {revenue_option})")
summary_data = {
    "Total Cross_Data Reports": [total_reports],
    "False Alarms (No Comment)": [false_count],
    "False Alarm %": [f"{(false_count / total_reports) * 100:.2f}%" if total_reports else "0.00%"],
    "Actual Faults (With Comment)": [actual_count],
    "Actual Fault %": [f"{(actual_count / total_reports) * 100:.2f}%" if total_reports else "0.00%"]
}
st.table(pd.DataFrame(summary_data))

# Charts
# Row 1: Pie chart + Heatmap
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown(f"###Faults by GEALOC ({year_option})")
    gealoc_counts = df_actual['GEALOC'].value_counts().reset_index()
    gealoc_counts.columns = ['GEALOC', 'Count']
    fig1, ax1 = plt.subplots(figsize=(4, 4))
    wedges, texts, autotexts = ax1.pie(
        gealoc_counts['Count'],
        labels=gealoc_counts['GEALOC'],
        startangle=90,
        autopct=lambda p: f'{int(p * sum(gealoc_counts["Count"]) / 100)}',
        textprops=dict(color="black", fontsize=8)
    )
    ax1.axis('equal')
    st.pyplot(fig1)

with col2:
    st.markdown(f"###GEALOC vs Cause Correlation ({year_option})")
    heatmap_df = df_actual[['GEALOC', 'Comment']].copy()
    pivot = heatmap_df.groupby(['GEALOC', 'Comment']).size().reset_index(name='Count')
    pivot = pivot[pivot['Count'] >= 5]
    heatmap_data = pivot.pivot(index='GEALOC', columns='Comment', values='Count').fillna(0)
    fig_heatmap, ax_heatmap = plt.subplots(figsize=(max(6, heatmap_data.shape[1] * 0.8), max(4, heatmap_data.shape[0] * 0.6)))
    sns.heatmap(heatmap_data, annot=True, fmt=".0f", cmap="YlGnBu", cbar=True, ax=ax_heatmap, annot_kws={"size": 8})
    ax_heatmap.set_xlabel("Cause", fontsize=9)
    ax_heatmap.set_ylabel("GEALOC", fontsize=9)
    plt.xticks(rotation=45, ha='right', fontsize=7)
    plt.yticks(fontsize=8)
    st.pyplot(fig_heatmap)

# Row 2: Compact Horizontal Bar Chart (Top 5 Causes)
st.markdown(f"### 📊 Top 5 Causes ({year_option})")
cause_counts = df_actual['Comment'].value_counts().reset_index()
cause_counts.columns = ['Cause', 'Count']
top5_causes = cause_counts.head(5)
fig_top5, ax_top5 = plt.subplots(figsize=(6, 3))
barplot_top5 = sns.barplot(data=top5_causes, y='Cause', x='Count', ax=ax_top5, palette='Set2')
ax_top5.set_ylabel("Cause", fontsize=10)
ax_top5.set_xlabel("Count", fontsize=10)
for p in barplot_top5.patches:
    width = p.get_width()
    ax_top5.annotate(f'{int(width)}', (width + 0.1, p.get_y() + p.get_height() / 2),
                     ha='left', va='center', fontsize=8, color='black')
st.pyplot(fig_top5)

# Expandable Full Chart (All Causes)
with st.expander(f"🔎 See All Causes (Expanded View) ({year_option})"):
    fig_full, ax_full = plt.subplots(figsize=(12, max(5, len(cause_counts) * 0.3)))
    full_barplot = sns.barplot(data=cause_counts, y='Cause', x='Count', ax=ax_full, palette='Set3')
    ax_full.set_ylabel("Cause", fontsize=10)
    ax_full.set_xlabel("Count", fontsize=10)
    for p in full_barplot.patches:
        width = p.get_width()
        ax_full.annotate(f'{int(width)}', (width + 0.1, p.get_y() + p.get_height() / 2),
                         ha='left', va='center', fontsize=7, color='black')
    st.pyplot(fig_full)


import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Dashboard ยอดขายหมูกมล", layout="wide")

# ส่วน Upload File
uploaded_file = st.file_uploader("📤 อัปโหลดไฟล์ยอดขาย (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    sales_data = pd.read_excel(uploaded_file)
    st.success("✅ อัปโหลดไฟล์ใหม่เรียบร้อยแล้ว!")
else:
    sales_data = pd.read_excel('ยอดขาย Online.xlsx')
    st.info("ℹ️ กำลังใช้งานไฟล์ยอดขายเริ่มต้น")

# ตรวจสอบและค้นหาคอลัมน์วันที่
st.write("🗂️ คอลัมน์ทั้งหมดในไฟล์:", sales_data.columns.tolist())

date_column = None
for col in sales_data.columns:
    if 'วัน' in col or 'date' in col.lower():
        date_column = col
        break

if date_column:
    sales_data[date_column] = pd.to_datetime(sales_data[date_column], errors='coerce', dayfirst=True)
    sales_data = sales_data.dropna(subset=[date_column])
    sales_data = sales_data.rename(columns={date_column: 'วันที่'})
else:
    st.error("❌ ไม่พบคอลัมน์วันที่ในไฟล์ กรุณาตรวจสอบไฟล์ยอดขายอีกครั้ง")
    st.stop()

# ตัดเฉพาะสินค้าจริง ไม่เอาค่าขนส่ง
sales_data = sales_data[~sales_data['หมวดสินค้า'].isin(['ขนส่ง'])]

# รวมยอดขายแต่ละวันของลูกค้า
sales_summary = (sales_data.groupby(['รหัสลูกค้า/ผู้ขาย', 'วันที่'])
                  .agg({'ยอดรวม': 'sum'})
                  .reset_index())

# คำนวณความถี่การซื้อซ้ำ
sales_summary = sales_summary.sort_values(['รหัสลูกค้า/ผู้ขาย', 'วันที่'])
sales_summary['diff_days'] = sales_summary.groupby('รหัสลูกค้า/ผู้ขาย')['วันที่'].diff().dt.days

# ลูกค้าซื้อซ้ำ
repeat_customers = sales_summary.dropna(subset=['diff_days'])
repeat_frequency_avg = repeat_customers['diff_days'].mean()

# ยอดขายรายภาค
sales_by_region = (sales_data.groupby('ชื่อกลุ่มลูกค้า/ผู้ขาย 2')['ยอดรวม']
                   .sum()
                   .sort_values(ascending=False))

# ดึง Top 10 สินค้าขายดีที่สุด
top_products = (sales_data.groupby('ชื่อสินค้า/บริการ [ข้อมูลจำเพาะ]')['ยอดรวม']
                .sum()
                .sort_values(ascending=False)
                .head(10))

# ยอดขายรายเดือน
sales_data['เดือน'] = sales_data['วันที่'].dt.to_period('M')
sales_by_month = sales_data.groupby('เดือน')['ยอดรวม'].sum().reset_index()
sales_by_month['เดือน'] = sales_by_month['เดือน'].astype(str)

# Dashboard
st.title("📊 Dashboard ยอดขาย Online : หมูกมล")

col1, col2, col3 = st.columns(3)
col1.metric("จำนวนลูกค้าทั้งหมด", f"{sales_data['รหัสลูกค้า/ผู้ขาย'].nunique()} คน")
col2.metric("ลูกค้าซื้อซ้ำ", f"{repeat_customers['รหัสลูกค้า/ผู้ขาย'].nunique()} คน")
col3.metric("ความถี่เฉลี่ยการซื้อซ้ำ", f"{repeat_frequency_avg:.2f} วัน" if not pd.isna(repeat_frequency_avg) else "ไม่มีข้อมูล")

st.header("ยอดขายรายภาค")
fig_region = px.bar(sales_by_region.reset_index(), x='ชื่อกลุ่มลูกค้า/ผู้ขาย 2', y='ยอดรวม', text='ยอดรวม')
st.plotly_chart(fig_region, use_container_width=True)

st.header("สินค้า Top 10 ขายดีที่สุด")
st.dataframe(top_products.reset_index())
fig_top10 = px.bar(top_products.reset_index(), x='ยอดรวม', y='ชื่อสินค้า/บริการ [ข้อมูลจำเพาะ]', orientation='h', text='ยอดรวม')
st.plotly_chart(fig_top10, use_container_width=True)

st.header("ยอดขายรายเดือน (Line Chart)")
if not sales_by_month.empty:
    fig_monthly = px.line(sales_by_month, x='เดือน', y='ยอดรวม', markers=True)
    st.plotly_chart(fig_monthly, use_container_width=True)
else:
    st.info("📉 ขณะนี้ยังไม่มีข้อมูลยอดขายรายเดือน")

st.header("Distribution ความถี่ซื้อซ้ำ (วัน)")
if not repeat_customers.empty:
    fig_repeat = px.histogram(repeat_customers, x='diff_days', nbins=30, title='จำนวนวันระหว่างการซื้อซ้ำ')
    st.plotly_chart(fig_repeat, use_container_width=True)
else:
    st.info("ℹ️ ขณะนี้ยังไม่มีข้อมูลการซื้อซ้ำ")

with st.expander("ดูข้อมูลดิบเพิ่มเติม"):
    st.dataframe(sales_data)

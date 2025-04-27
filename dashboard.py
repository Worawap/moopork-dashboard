
import pandas as pd
import plotly.express as px
import streamlit as st

# โหลดข้อมูล
sales_data = pd.read_excel('ยอดขาย Online (1).xlsx')

# แก้ไขวันที่
sales_data['วันที่'] = pd.to_datetime(sales_data['วันที่'], errors='coerce')

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

# สินค้าขายดีสุด
top_product = (sales_data.groupby('ชื่อสินค้า/บริการ [ข้อมูลจำเพาะ]')['ยอดรวม']
               .sum()
               .sort_values(ascending=False)
               .head(10))

# Dashboard
st.set_page_config(page_title="Dashboard ยอดขายหมูกมล", layout="wide")

st.title("📊 Dashboard ยอดขาย Online : หมูกมล")

col1, col2, col3 = st.columns(3)
col1.metric("จำนวนลูกค้าทั้งหมด", f"{sales_data['รหัสลูกค้า/ผู้ขาย'].nunique()} คน")
col2.metric("ลูกค้าซื้อซ้ำ", f"{repeat_customers['รหัสลูกค้า/ผู้ขาย'].nunique()} คน")
col3.metric("ความถี่เฉลี่ยการซื้อซ้ำ", f"{repeat_frequency_avg:.2f} วัน")

st.header("ยอดขายรายภาค")
fig_region = px.bar(sales_by_region.reset_index(), x='ชื่อกลุ่มลูกค้า/ผู้ขาย 2', y='ยอดรวม', text='ยอดรวม')
st.plotly_chart(fig_region, use_container_width=True)

st.header("สินค้าขายดีที่สุด")
st.success(f"\U0001F947 {top_product.index[0]} : {top_product.values[0]:,.2f} บาท")

st.header("Distribution ความถี่ซื้อซ้ำ (วัน)")
fig_repeat = px.histogram(repeat_customers, x='diff_days', nbins=30, title='จำนวนวันระหว่างการซื้อซ้ำ')
st.plotly_chart(fig_repeat, use_container_width=True)

with st.expander("ดูข้อมูลดิบเพิ่มเติม"):
    st.dataframe(sales_data)

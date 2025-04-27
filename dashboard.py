import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Dashboard ยอดขายหมูกมล", layout="wide")

st.markdown("""
    <h1 style='text-align: center; color: #FF4B4B;'>📈 Dashboard ยอดขาย Online : หมูกมล</h1>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("\U0001F4C2 อัปโหลดไฟล์ยอดขาย (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        all_sheets = pd.ExcelFile(uploaded_file).sheet_names
        selected_sheet = st.selectbox("เลือกชีต:", all_sheets)
        preview_data = pd.read_excel(uploaded_file, sheet_name=selected_sheet, header=None)
        st.subheader("\U0001F50D ตัวอย่างข้อมูล (ยังไม่ตั้งหัวตาราง)")
        st.dataframe(preview_data.head(20))

        header_row = st.number_input('เลือกหมายเลขแถวที่เป็นหัวตารางจริง (เริ่มจาก 0)', min_value=0, max_value=100, value=2, step=1)
        skiprows = st.number_input('เลือกจำนวนแถวที่ต้องข้ามก่อนเริ่มข้อมูล (รวม header)', min_value=0, max_value=100, value=2, step=1)
        load_data = st.button("\U0001F680 โหลดข้อมูลจริง")

        if load_data:
            sales_data = pd.read_excel(uploaded_file, sheet_name=selected_sheet, header=0, skiprows=skiprows)
            st.success("✅ อัปโหลดไฟล์ใหม่เรียบร้อยแล้ว!")

            date_column = None
            for col in sales_data.columns:
                if isinstance(col, str) and ('วัน' in col or 'date' in col.lower()):
                    date_column = col
                    break

            if date_column:
                sales_data[date_column] = pd.to_datetime(sales_data[date_column], errors='coerce', dayfirst=True)
                sales_data = sales_data.dropna(subset=[date_column])
                sales_data = sales_data.rename(columns={date_column: 'วันที่'})
            else:
                st.error("❌ ไม่พบคอลัมน์วันที่ในไฟล์ กรุณาตรวจสอบไฟล์ยอดขายอีกครั้ง")
                st.stop()

            # ลบข้อมูลสรุปประจำเดือนหรือบรรทัดที่ไม่ใช่ข้อมูลจริง
            sales_data = sales_data[sales_data['วันที่'].notna()]
            sales_data = sales_data[sales_data['วันที่'].dt.year >= 2000]

            if 'ยอดรวม' in sales_data.columns:
                sales_data = sales_data[sales_data['ยอดรวม'].apply(lambda x: isinstance(x, (int, float)))]

            if 'หมวดสินค้า' in sales_data.columns:
                sales_data = sales_data[~sales_data['หมวดสินค้า'].isin(['ขนส่ง'])]

            sales_data['เดือน'] = sales_data['วันที่'].dt.to_period('M')
            sales_by_month = sales_data.groupby('เดือน')['ยอดรวม'].sum().reset_index()
            sales_by_month['เดือน'] = sales_by_month['เดือน'].astype(str)

            if 'รหัสลูกค้า/ผู้ขาย' in sales_data.columns and 'ยอดรวม' in sales_data.columns:
                sales_summary = (sales_data.groupby(['รหัสลูกค้า/ผู้ขาย', 'วันที่'])
                                  .agg({'ยอดรวม': 'sum'})
                                  .reset_index())
                sales_summary = sales_summary.sort_values(['รหัสลูกค้า/ผู้ขาย', 'วันที่'])
                sales_summary['diff_days'] = sales_summary.groupby('รหัสลูกค้า/ผู้ขาย')['วันที่'].diff().dt.days
                repeat_customers = sales_summary.dropna(subset=['diff_days'])
                repeat_frequency_avg = repeat_customers['diff_days'].mean()
            else:
                repeat_customers = pd.DataFrame()
                repeat_frequency_avg = None

            if 'ชื่อกลุ่มลูกค้า/ผู้ขาย 2' in sales_data.columns:
                sales_by_region = (sales_data.groupby('ชื่อกลุ่มลูกค้า/ผู้ขาย 2')['ยอดรวม']
                                   .sum()
                                   .sort_values(ascending=False))
            else:
                sales_by_region = pd.DataFrame()

            if 'ชื่อสินค้า/บริการ [ข้อมูลจำเพาะ]' in sales_data.columns:
                top_products = (sales_data.groupby('ชื่อสินค้า/บริการ [ข้อมูลจำเพาะ]')['ยอดรวม']
                                .sum()
                                .sort_values(ascending=False)
                                .head(10))
            else:
                top_products = pd.DataFrame()

            st.header("\U0001F4C8 ยอดขายรายเดือน (Line Chart)")
            if not sales_by_month.empty:
                fig_monthly = px.line(sales_by_month, x='เดือน', y='ยอดรวม', markers=True, title='ยอดขายรายเดือน')
                st.plotly_chart(fig_monthly, use_container_width=True)
            else:
                st.info("ขณะนี้ยังไม่มีข้อมูลยอดขายรายเดือน")

            col1, col2, col3 = st.columns(3)
            col1.metric("\U0001F465 จำนวนลูกค้าทั้งหมด", f"{sales_data['รหัสลูกค้า/ผู้ขาย'].nunique()} คน")
            col2.metric("♻️ ลูกค้าซื้อซ้ำ", f"{repeat_customers['รหัสลูกค้า/ผู้ขาย'].nunique()} คน" if not repeat_customers.empty else "0 คน")
            col3.metric("⏳ ความถี่เฉลี่ยการซื้อซ้ำ", f"{repeat_frequency_avg:.2f} วัน" if repeat_frequency_avg else "ไม่มีข้อมูล")

            st.header("\U0001F30D ยอดขายรายภาค")
            if not sales_by_region.empty:
                fig_region = px.bar(sales_by_region.reset_index(), x='ชื่อกลุ่มลูกค้า/ผู้ขาย 2', y='ยอดรวม', text='ยอดรวม', title='ยอดขายตามภาค')
                st.plotly_chart(fig_region, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลยอดขายรายภาคให้แสดงผล")

            st.header("\U0001F947 สินค้า Top 10 ขายดีที่สุด")
            if not top_products.empty:
                fig_top10 = px.bar(top_products.reset_index(), x='ยอดรวม', y='ชื่อสินค้า/บริการ [ข้อมูลจำเพาะ]', orientation='h', text='ยอดรวม', title='Top 10 สินค้าขายดี')
                st.plotly_chart(fig_top10, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลสินค้าขายดีให้แสดงผล")

            st.header("\U0001F5E3 Distribution ความถี่ซื้อซ้ำ (วัน)")
            if not repeat_customers.empty:
                fig_repeat = px.histogram(repeat_customers, x='diff_days', nbins=30, title='จำนวนวันระหว่างการซื้อซ้ำ')
                st.plotly_chart(fig_repeat, use_container_width=True)
            else:
                st.info("ขณะนี้ยังไม่มีข้อมูลการซื้อซ้ำ")

            with st.expander("\U0001F4C4 ดูข้อมูลดิบเพิ่มเติม"):
                st.dataframe(sales_data)
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
        st.stop()
else:
    st.info("\U0001F4C2 กรุณาอัปโหลดไฟล์ยอดขาย (.xlsx)")

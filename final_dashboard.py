import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📊 ระบบวิเคราะห์หุ้น Institutional Grade")

ticker = st.sidebar.text_input("สัญลักษณ์หุ้น:", value="AAPL").strip().upper()

@st.cache_data(ttl=1800)
def get_data(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty: return None
        # แก้ไขปัญหา MultiIndex
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # ใส่ตัวแปรพื้นฐานไว้ก่อน
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        return df
    except: return None

df = get_data(ticker)
if df is None:
    st.error("❌ เกิดข้อผิดพลาดในการโหลดข้อมูล หรือไม่พบสัญลักษณ์หุ้นนี้")
else:
    # ถ้ากราฟขึ้น แสดงว่ามาแล้ว!
    st.line_chart(df['Close'])
    st.success("✅ ระบบกลับมาทำงานปกติแล้วครับ")

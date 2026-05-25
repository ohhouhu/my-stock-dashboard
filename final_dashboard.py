import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Stock Dashboard", layout="wide")
st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว")

# เลือกหุ้น
ticker = st.sidebar.text_input("ใส่ชื่อหุ้น:", value="AAPL")

# ดึงข้อมูล
@st.cache_data
def get_data(ticker):
    df = yf.download(ticker, period="1y", interval="1d", progress=False)
    # ถ้าข้อมูลเป็น MultiIndex ให้ปรับให้เป็น Column เดียว
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

df = get_data(ticker)

if not df.empty and 'Close' in df.columns:
    # คำนวณ RSI
    close_price = df['Close'].squeeze() # ทำให้แน่ใจว่าเป็น Series
    delta = close_price.diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # แสดงกราฟ
    st.subheader(f"ราคาหุ้นของ {ticker}")
    st.line_chart(close_price)

    st.subheader("ดัชนี RSI (14 วัน)")
    st.line_chart(rsi)
else:
    st.error("ไม่พบข้อมูลหุ้นตัวนี้ โปรดตรวจสอบชื่อ Ticker อีกครั้ง")

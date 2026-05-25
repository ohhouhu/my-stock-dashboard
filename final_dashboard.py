import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Stock Dashboard", layout="wide")
st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว")

ticker = st.sidebar.text_input("ใส่ชื่อหุ้น:", value="AAPL")

@st.cache_data
def get_data(ticker):
    # ปรับปรุงให้ดึงข้อมูลได้แม่นยำขึ้น
    df = yf.download(ticker, period="1y", interval="1d", auto_adjust=True)
    return df

if ticker:
    df = get_data(ticker)
    
    # ตรวจสอบว่า df ไม่ว่างและมีข้อมูลราคา
    if not df.empty and 'Close' in df.columns:
        # ใช้ .iloc[:, 0] กรณีที่มีหลาย column ซ้อนกัน
        close_price = df['Close']
        if isinstance(close_price, pd.DataFrame):
            close_price = close_price.iloc[:, 0]
            
        st.subheader(f"ราคาหุ้นของ {ticker}")
        st.line_chart(close_price)

        # คำนวณ RSI
        delta = close_price.diff()
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        st.subheader("ดัชนี RSI (14 วัน)")
        st.line_chart(rsi)
    else:
        st.error(f"ไม่พบข้อมูลหุ้น {ticker} กรุณาตรวจสอบชื่อ Ticker อีกครั้ง")

# 1. เขียนไฟล์ final_dashboard.py ลงไปใหม่ (อันนี้เป็นเวอร์ชันสมบูรณ์ครับ)
with open('final_dashboard.py', 'w') as f:
    f.write('''
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Dashboard", layout="wide")
st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว")

# เลือกหุ้น
ticker = st.sidebar.selectbox("เลือกหุ้น:", ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"])

# ดึงข้อมูล
df = yf.download(ticker, period="1y", interval="1d", progress=False)

# คำนวณ RSI (ตัวที่พี่อยากได้)
delta = df['Close'].diff()
gain = (delta.where(delta > 0, 0))
loss = (-delta.where(delta < 0, 0))
avg_gain = gain.rolling(window=14).mean()
avg_loss = loss.rolling(window=14).mean()
rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))

# แสดงกราฟ
st.subheader(f"ราคาหุ้นของ {ticker}")
st.line_chart(df['Close'])

st.subheader("ดัชนี RSI (14 วัน)")
st.line_chart(rsi)
''')

print("✅ สร้างไฟล์ final_dashboard.py เรียบร้อยแล้วครับ!")
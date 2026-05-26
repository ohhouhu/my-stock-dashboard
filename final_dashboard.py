import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Stock Dashboard", layout="wide", page_icon="📈")
st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว (ฉบับสมบูรณ์ 100%)")

# Sidebar
ticker = st.sidebar.text_input("กรอกสัญลักษณ์หุ้น:", value="AAPL").strip().upper()
if ticker and not ticker.endswith('.BK') and len(ticker) < 5:
    st.sidebar.info(f"💡 ทริค: หุ้นไทยต้องเติม .BK (เช่น {ticker}.BK)")

period_options = ["1 เดือน", "3 เดือน", "6 เดือน", "1 ปี", "2 ปี", "5 ปี"]
selected_period = st.sidebar.selectbox("เลือกช่วงเวลา", period_options, index=3)
period_map = {"1 เดือน": "1mo", "3 เดือน": "3mo", "6 เดือน": "6mo", "1 ปี": "1y", "2 ปี": "2y", "5 ปี": "5y"}

@st.cache_data(ttl=1800)
def get_stock_data(ticker, period):
    try:
        df = yf.download(ticker, period=period, interval="1d", progress=False)
        if df.empty or len(df) < 20: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df = df.round(4)
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        df['BB_std'] = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
        df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)
        
        delta = df['Close'].diff()
        gain = delta.clip(lower=0); loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, min_periods=14).mean()
        avg_loss = loss.ewm(com=13, min_periods=14).mean()
        df['RSI'] = 100 - (100 / (1 + avg_gain / avg_loss))
        
        exp12 = df['Close'].ewm(span=12, adjust=False).mean()
        exp26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp12 - exp26
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal']
        return df
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {str(e)}")
        return None

if ticker:
    df = get_stock_data(ticker, period_map[selected_period])
    if df is None: st.error("ไม่พบข้อมูลหุ้น"); st.stop()
    
    st.success(f"✅ กำลังวิเคราะห์: **{ticker}**")

    # 1. กราฟ Candlestick + EMA/BB
    fig_price = go.Figure()
    fig_price.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name='EMA50', line=dict(color='purple', width=1.5)))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA200', line=dict(color='orange', width=2, dash='dot')))
    fig_price.update_layout(height=600, template="plotly_white", hovermode="x unified", legend=dict(orientation="h", x=0, y=1.05))
    st.plotly_chart(fig_price, use_container_width=True)

    # 2. Volume & Indicators
    c_v, c_r, c_m = st.columns(3)
    with c_v:
        fig_vol = go.Figure(go.Bar(x=df.index, y=df['Volume'], marker_color='#1E90FF'))
        fig_vol.update_layout(height=300, title="Volume", template="plotly_white")
        st.plotly_chart(fig_vol, use_container_width=True)
    with c_r:
        fig_rsi = go.Figure(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#FF4500')))
        fig_rsi.update_layout(height=300, title="RSI", template="plotly_white")
        st.plotly_chart(fig_rsi, use_container_width=True)
    with c_m:
        fig_macd = go.Figure(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue')))
        fig_macd.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='Hist', marker_color=['green' if x >= 0 else 'red' for x in df['MACD_Hist']]))
        fig_macd.update_layout(height=300, title="MACD", template="plotly_white")
        st.plotly_chart(fig_macd, use_container_width=True)

    # 3. AI วิเคราะห์
    st.divider()
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    body = abs(latest['Close'] - latest['Open'])
    wick_upper = latest['High'] - max(latest['Close'], latest['Open'])
    wick_lower = min(latest['Close'], latest['Open']) - latest['Low']
    pattern = "Hammer (กลับตัวขาขึ้น)" if wick_lower > body * 2 else "Shooting Star (กลับตัวขาลง)" if wick_upper > body * 2 else "ปกติ"
    
    st.subheader(f"🧠 AI วิเคราะห์เชิงลึก: {ticker}")
    c_a, c_b = st.columns(2)
    c_a.write(f"• **แนวโน้มหลัก:** {'ขาขึ้น' if latest['Close'] > latest['EMA200'] else 'ขาลง'}")
    c_a.write(f"• **รูปแบบแท่งเทียน:** {pattern}")
    c_b.write(f"• **ราคาปิด:** {latest['Close']:.2f}")
    c_b.write(f"• **RSI:** {latest['RSI']:.1f}")

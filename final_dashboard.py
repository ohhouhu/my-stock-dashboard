import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Institutional Dashboard", layout="wide", page_icon="🏦")
st.title("📊 ระบบวิเคราะห์หุ้นระดับสถาบัน (Full Professional)")

# Sidebar
ticker = st.sidebar.text_input("กรอกสัญลักษณ์หุ้น:", value="AAPL").strip().upper()
if ticker and not ticker.endswith('.BK') and len(ticker) < 5:
    st.sidebar.info(f"💡 ทริค: หุ้นไทยต้องเติม .BK")

period_map = {"1 เดือน": "1mo", "3 เดือน": "3mo", "6 เดือน": "6mo", "1 ปี": "1y", "2 ปี": "2y", "5 ปี": "5y"}
selected_period = st.sidebar.selectbox("เลือกช่วงเวลา", list(period_map.keys()), index=3)

@st.cache_data(ttl=1800)
def get_data(ticker, period):
    df = yf.download(ticker, period=period_map[period], interval="1d", progress=False)
    if df.empty or len(df) < 20: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # คำนวณตรรกะระดับสถาบัน
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    money_flow = typical_price * df['Volume']
    pos_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
    neg_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
    mfi_ratio = pos_flow.rolling(14).sum() / neg_flow.rolling(14).sum()
    df['MFI'] = 100 - (100 / (1 + mfi_ratio))
    
    # ตัวบ่งชี้มาตรฐาน
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['RSI'] = 100 - (100 / (1 + (df['Close'].diff().clip(lower=0).ewm(14).mean() / -df['Close'].diff().clip(upper=0).ewm(14).mean())))
    return df

if ticker:
    df = get_data(ticker, selected_period)
    if df is None: st.error("ไม่พบข้อมูล"); st.stop()

    # 1. กราฟหลัก (Candlestick + VWAP)
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name='VWAP (ต้นทุนรายใหญ่)', line=dict(color='orange', width=2)))
    fig.update_layout(height=500, template="plotly_white", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # 2. Indicators (Volume, RSI, MFI)
    c1, c2, c3 = st.columns(3)
    c1.bar_chart(df['Volume'])
    c2.line_chart(df['RSI'])
    c3.line_chart(df['MFI'])

    # 3. AI วิเคราะห์เชิงลึกระดับขาใหญ่
    st.divider()
    latest = df.iloc[-1]
    st.subheader(f"🧠 AI วิเคราะห์มุมมองขาใหญ่: {ticker}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"• **สถานะราคาเทียบ VWAP:** {'แข็งแกร่ง (ราคา > ต้นทุนรายใหญ่)' if latest['Close'] > latest['VWAP'] else 'อ่อนแอ (ราคา < ต้นทุนรายใหญ่)'}")
        st.write(f"• **กระแสเงิน (MFI):** {latest['MFI']:.1f} ({'เข้าสะสม' if latest['MFI'] < 20 else 'รินขาย' if latest['MFI'] > 80 else 'ปกติ'})")
    with col2:
        st.write(f"• **แนวโน้มระยะยาว:** {'ขาขึ้น (เหนือ EMA200)' if latest['Close'] > latest['EMA200'] else 'ขาลง (ใต้ EMA200)'}")
        st.write(f"• **แรงซื้อปัจจุบัน:** {'Overbought' if latest['RSI'] > 70 else 'Oversold' if latest['RSI'] < 30 else 'ปกติ'}")

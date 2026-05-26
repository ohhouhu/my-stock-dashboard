import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Institutional Dashboard", layout="wide", page_icon="🏦")
st.title("📊 ระบบวิเคราะห์หุ้นระดับสถาบัน (Professional Layout)")

# Sidebar
ticker = st.sidebar.text_input("กรอกสัญลักษณ์หุ้น:", value="AAPL").strip().upper()
if ticker and not ticker.endswith('.BK') and len(ticker) < 5:
    st.sidebar.info("💡 ทริค: หุ้นไทยต้องเติม .BK")

period_map = {"1 เดือน": "1mo", "3 เดือน": "3mo", "6 เดือน": "6mo", "1 ปี": "1y", "2 ปี": "2y", "5 ปี": "5y"}
selected_period = st.sidebar.selectbox("เลือกช่วงเวลา", list(period_map.keys()), index=3)

@st.cache_data(ttl=1800)
def get_data(ticker, period):
    df = yf.download(ticker, period=period_map[period], interval="1d", progress=False)
    if df.empty or len(df) < 20: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # VWAP
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()

    # MFI
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    money_flow = typical_price * df['Volume']
    pos_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
    neg_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
    mfi_ratio = pos_flow.rolling(14).sum() / neg_flow.replace(0, np.nan).rolling(14).sum()
    df['MFI'] = 100 - (100 / (1 + mfi_ratio))

    # EMA
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # RSI (มาตรฐาน)
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df['RSI'] = 100 - (100 / (1 + rs))

    return df

if ticker:
    df = get_data(ticker, selected_period)
    if df is None: st.error("ไม่พบข้อมูล"); st.stop()

    # รวมทุกกราฟใน Subplots
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        row_heights=[0.6, 0.2, 0.2],
                        vertical_spacing=0.05)

    # Candlestick + VWAP
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                 low=df['Low'], close=df['Close'],
                                 name="Price"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name='VWAP', line=dict(color='orange')), row=1, col=1)

    # Volume
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='gray'), row=2, col=1)

    # RSI + MFI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='blue')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MFI'], name='MFI', line=dict(color='green')), row=3, col=1)

    fig.update_layout(height=800, template="plotly_white", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # AI วิเคราะห์เชิงลึก
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

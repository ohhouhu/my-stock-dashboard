import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Dashboard", layout="wide", page_icon="📈")
st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว (ฉบับสมบูรณ์ 100%)")

# Sidebar
ticker = st.sidebar.text_input("กรอกสัญลักษณ์หุ้น:", value="AAPL").strip().upper()
period_map = {"1 เดือน": "1mo", "3 เดือน": "3mo", "6 เดือน": "6mo", "1 ปี": "1y", "2 ปี": "2y", "5 ปี": "5y"}
selected_period = st.sidebar.selectbox("เลือกช่วงเวลา", list(period_map.keys()), index=3)

@st.cache_data(ttl=1800)
def get_data(ticker, period):
    # ดึงข้อมูลแบบปกติเพื่อให้ได้ Open, High, Low, Close ครบ
    df = yf.download(ticker, period=period, interval="1d", progress=False)
    if df.empty or len(df) < 20: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
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
    
    return df

if ticker:
    df = get_data(ticker, period_map[selected_period])
    if df is None: st.error("ไม่พบข้อมูลหุ้น"); st.stop()

    # กราฟ Candlestick
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Market')])
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name='EMA50', line=dict(color='purple', width=1)))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA200', line=dict(color='orange', width=1)))
    fig.update_layout(height=600, template="plotly_white", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # สรุป AI ท้ายสุด
    st.divider()
    latest = df.iloc[-1]
    body = abs(latest['Close'] - latest['Open'])
    wick_lower = min(latest['Close'], latest['Open']) - latest['Low']
    pattern = "Hammer (กลับตัวขาขึ้น)" if wick_lower > body * 2 else "ปกติ"
    
    st.subheader(f"🧠 AI วิเคราะห์: {pattern}")
    st.write(f"ราคาปิดล่าสุด: **{latest['Close']:.2f}** | RSI: **{latest['RSI']:.1f}**")

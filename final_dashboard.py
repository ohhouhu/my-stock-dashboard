import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ====================== CUSTOM CSS ======================
st.set_page_config(page_title="Stock Dashboard", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e2937 100%);
    }
    h1, h2, h3 {
        color: #e2e8f0 !important;
        font-weight: 700;
    }
    .stMetric {
        background-color: #1e2937;
        border-radius: 10px;
        padding: 10px;
    }
    .signal-box {
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin: 10px 0;
        font-size: 28px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 SMART STOCK DASHBOARD")
st.markdown("**ระบบวิเคราะห์หุ้นอัจฉริยะ** | วิเคราะห์ด้วย AI Indicators")

# Sidebar
with st.sidebar:
    st.header("⚙️ ตั้งค่า")
    ticker = st.text_input("สัญลักษณ์หุ้น", value="AAPL").strip().upper()
    period_options = ["1 เดือน", "3 เดือน", "6 เดือน", "1 ปี", "2 ปี", "5 ปี"]
    selected_period = st.selectbox("ช่วงเวลา", period_options, index=3)

period_map = {"1 เดือน": "1mo", "3 เดือน": "3mo", "6 เดือน": "6mo",
              "1 ปี": "1y", "2 ปี": "2y", "5 ปี": "5y"}

@st.cache_data(ttl=3600)
def get_stock_data(ticker, period):
    try:
        df = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        df['BB_std'] = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
        df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)
        
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, min_periods=14, adjust=False).mean()
        avg_loss = loss.ewm(com=13, min_periods=14, adjust=False).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        exp12 = df['Close'].ewm(span=12, adjust=False).mean()
        exp26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp12 - exp26
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal']
        
        return df
    except:
        return None

if ticker:
    df = get_stock_data(ticker, period_map[selected_period])
    
    if df is None or df.empty:
        st.error(f"❌ ไม่พบข้อมูลหุ้น `{ticker}`")
        st.stop()

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # ====================== SIGNAL GENERATOR ======================
    st.subheader("🚨 สัญญาณซื้อ-ขายอัตโนมัติ")
    
    is_uptrend = latest['Close'] > latest['EMA200']
    rsi = latest['RSI']
    macd_cross_up = latest['MACD'] > latest['Signal'] and prev['MACD'] <= prev['Signal']
    
    score = 0
    if is_uptrend: score += 2
    if rsi < 35: score += 3
    elif rsi > 65: score -= 3
    if macd_cross_up: score += 2

    if score >= 6:
        signal_text = "🟢 STRONG BUY"
        signal_color = "#22c55e"
    elif score >= 3:
        signal_text = "🟢 BUY"
        signal_color = "#86efac"
    elif score <= -5:
        signal_text = "🔴 STRONG SELL"
        signal_color = "#ef4444"
    else:
        signal_text = "⚪ NEUTRAL"
        signal_color = "#94a3b8"

    st.markdown(f"""
    <div class="signal-box" style="background-color: {signal_color}20; color: {signal_color}; border: 2px solid {signal_color};">
        {signal_text} &nbsp;&nbsp; Score: {score}/10
    </div>
    """, unsafe_allow_html=True)

    # Take Profit & Stop Loss
    st.subheader("🎯 Take Profit & Stop Loss")
    current = latest['Close']
    stop_loss = max(latest['BB_lower'] * 0.975, current * 0.93)
    tp1 = current + (current - stop_loss) * 2
    tp2 = current + (current - stop_loss) * 3

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("ราคาปัจจุบัน", f"${current:.2f}")
    with c2:
        st.metric("Stop Loss", f"${stop_loss:.2f}", f"-{((current-stop_loss)/current*100):.1f}%")
    with c3:
        st.metric("Take Profit 1", f"${tp1:.2f}", f"+{((tp1-current)/current*100):.1f}%")

    st.divider()

    # กราฟหลัก
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='ราคาปิด', line=dict(color='#60a5fa', width=2.5)))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA 200', line=dict(color='#fbbf24', dash='dot', width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_upper'], name='Upper Band', line=dict(color='rgba(248,113,113,0.4)', dash='dash')))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_lower'], name='Lower Band', line=dict(color='rgba(147,197,253,0.4)', dash='dash'), fill='tonexty', fillcolor='rgba(147,197,253,0.08)'))
    
    fig.update_layout(
        title=f"{ticker} - Price Analysis",
        template="plotly_dark",
        height=520,
        hovermode="x unified",
        legend=dict(x=0, y=1.1, orientation="h")
    )
    st.plotly_chart(fig, use_container_width=True)

    # ส่วนล่าง
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("RSI (14)")
        fig_rsi = go.Figure()
        fig_rsi.add_hrect(y0=70, y1=100, fillcolor="#f87171", opacity=0.2)
        fig_rsi.add_hrect(y0=0, y1=30, fillcolor="#4ade80", opacity=0.2)
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#f97316', width=3)))
        fig_rsi.update_layout(template="plotly_dark", height=340, yaxis=dict(range=[0,100]))
        st.plotly_chart(fig_rsi, use_container_width=True)

    with col2:
        st.subheader("MACD")
        fig_macd = make_subplots(rows=1, cols=1)
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='#3b82f6')))
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal', line=dict(color='#f59e0b')))
        fig_macd.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='Histogram',
                                marker_color=['#22c55e' if x >= 0 else '#ef4444' for x in df['MACD_Hist']]))
        fig_macd.update_layout(template="plotly_dark", height=340)
        st.plotly_chart(fig_macd, use_container_width=True)

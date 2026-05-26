import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Stock Dashboard", layout="wide", page_icon="📈")
st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว")

# Sidebar
st.sidebar.header("⚙️ การตั้งค่า")
ticker = st.sidebar.text_input("กรอกสัญลักษณ์หุ้น:", value="AAPL").strip().upper()

period_options = ["1 เดือน", "3 เดือน", "6 เดือน", "1 ปี", "2 ปี", "5 ปี"]
selected_period = st.sidebar.selectbox("เลือกช่วงเวลา", period_options, index=3)

period_map = {
    "1 เดือน": "1mo", "3 เดือน": "3mo", "6 เดือน": "6mo",
    "1 ปี": "1y", "2 ปี": "2y", "5 ปี": "5y"
}

@st.cache_data(ttl=3600)
def get_stock_data(ticker, period):
    try:
        df = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False)
        if df.empty:
            return None
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Indicators
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        # Bollinger Bands
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        df['BB_std'] = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
        df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)
        
        # RSI
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, min_periods=14, adjust=False).mean()
        avg_loss = loss.ewm(com=13, min_periods=14, adjust=False).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp12 = df['Close'].ewm(span=12, adjust=False).mean()
        exp26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp12 - exp26
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal']
        
        return df
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {str(e)}")
        return None

# ==================== MAIN ====================
if ticker:
    df = get_stock_data(ticker, period_map[selected_period])
    
    if df is None or df.empty:
        st.error(f"❌ ไม่พบข้อมูลหุ้น `{ticker}`")
        st.info("ตัวอย่าง: AAPL, TSLA, NVDA, PTT.BK, 0700.HK")
        st.stop()

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    st.success(f"✅ แสดงข้อมูล: **{ticker}** | {selected_period}")

    # ====================== SIGNAL GENERATOR ======================
    st.subheader("🚨 Signal Generator (สัญญาณซื้อ-ขายอัตโนมัติ)")

    # คำนวณสัญญาณ
    is_uptrend = latest['Close'] > latest['EMA200']
    rsi = latest['RSI']
    macd_cross_up = latest['MACD'] > latest['Signal'] and prev['MACD'] <= prev['Signal']
    macd_cross_down = latest['MACD'] < latest['Signal'] and prev['MACD'] >= prev['Signal']
    near_lower_bb = latest['Close'] <= latest['BB_lower'] * 1.01
    near_upper_bb = latest['Close'] >= latest['BB_upper'] * 0.99

    score = 0
    reasons = []

    if is_uptrend:
        score += 2
        reasons.append("✅ ราคาอยู่เหนือ EMA200 (แนวโน้มขาขึ้น)")
    else:
        reasons.append("❌ ราคาอยู่ใต้ EMA200 (แนวโน้มขาลง)")

    if rsi < 35:
        score += 3
        reasons.append("✅ RSI ต่ำกว่า 35 (Oversold)")
    elif rsi > 65:
        score -= 3
        reasons.append("❌ RSI สูงกว่า 65 (Overbought)")
    elif 45 <= rsi <= 55:
        reasons.append("➖ RSI อยู่ในระดับสมดุล")

    if macd_cross_up:
        score += 2
        reasons.append("✅ MACD ตัดขึ้น (Bullish)")
    elif macd_cross_down:
        score -= 2
        reasons.append("❌ MACD ตัดลง (Bearish)")

    if near_lower_bb and is_uptrend:
        score += 2
        reasons.append("✅ ราคาใกล้ Bollinger Lower Band + ขาขึ้น")
    elif near_upper_bb:
        score -= 2
        reasons.append("❌ ราคาใกล้ Bollinger Upper Band")

    # กำหนดสัญญาณ
    if score >= 6:
        signal = "🟢 **STRONG BUY**"
        color = "green"
    elif score >= 3:
        signal = "🟢 **BUY**"
        color = "green"
    elif score <= -6:
        signal = "🔴 **STRONG SELL**"
        color = "red"
    elif score <= -3:
        signal = "🔴 **SELL**"
        color = "red"
    else:
        signal = "⚪ **NEUTRAL**"
        color = "gray"

    # แสดงสัญญาณหลัก
    st.markdown(f"""
    <h2 style="color:{color}; text-align:center; font-size:28px;">
        {signal} (Score: {score}/10)
    </h2>
    """, unsafe_allow_html=True)

    # แสดงเหตุผล
    st.write("**เหตุผลหลัก:**")
    for reason in reasons:
        st.write(reason)

    st.divider()

    # กราฟราคาหลัก + Bollinger Bands
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=df.index, y=df['Close'], name='ราคาปิด', line=dict(color='#008080', width=2)))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_upper'], name='BB Upper', line=dict(color='rgba(255,0,0,0.3)', dash='dash')))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_lower'], name='BB Lower', line=dict(color='rgba(0,0,255,0.3)', dash='dash'), fill='tonexty', fillcolor='rgba(0,0,255,0.05)'))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_middle'], name='BB Middle', line=dict(color='gray', dash='dot')))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA 200', line=dict(color='orange', width=2, dash='dot')))
    
    fig_price.update_layout(title=f"กราฟราคา {ticker} + Bollinger Bands", template="plotly_white", height=500, hovermode="x unified")
    st.plotly_chart(fig_price, use_container_width=True)

    # RSI, Volume, MACD (เหมือนเดิม)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("RSI (14)")
        fig_rsi = go.Figure()
        fig_rsi.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.15)
        fig_rsi.add_hrect(y0=30, y1=70, fillcolor="lightblue", opacity=0.15)
        fig_rsi.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.15)
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='#FF4500', width=2.5)))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        fig_rsi.update_layout(template="plotly_white", height=350, yaxis=dict(range=[0,100]))
        st.plotly_chart(fig_rsi, use_container_width=True)

    with col2:
        st.subheader("Volume")
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color='#1E90FF'))
        fig_vol.update_layout(template="plotly_white", height=350)
        st.plotly_chart(fig_vol, use_container_width=True)

    st.subheader("MACD")
    fig_macd = make_subplots(rows=1, cols=1)
    fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue')))
    fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal', line=dict(color='orange')))
    fig_macd.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='Histogram',
                            marker_color=['green' if x >= 0 else 'red' for x in df['MACD_Hist']]))
    fig_macd.update_layout(template="plotly_white", height=350)
    fig_macd.add_hline(y=0, line_dash="dash", line_color="gray")
    st.plotly_chart(fig_macd, use_container_width=True)

    # สรุปสถานะ
    st.divider()
    st.subheader(f"📌 สรุปสถานะล่าสุดของ {ticker}")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("ราคาล่าสุด", f"{latest['Close']:.2f}")
    with c2:
        change = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
        st.metric("เปลี่ยนแปลง", f"{change:+.2f}%")
    with c3:
        st.metric("RSI", f"{latest['RSI']:.1f}")

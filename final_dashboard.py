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

    is_uptrend = latest['Close'] > latest['EMA200']
    rsi = latest['RSI']
    macd_cross_up = latest['MACD'] > latest['Signal'] and prev['MACD'] <= prev['Signal']
    macd_cross_down = latest['MACD'] < latest['Signal'] and prev['MACD'] >= prev['Signal']
    near_lower_bb = latest['Close'] <= latest['BB_lower'] * 1.02
    near_upper_bb = latest['Close'] >= latest['BB_upper'] * 0.98

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

    if macd_cross_up:
        score += 2
        reasons.append("✅ MACD ตัดขึ้น")
    elif macd_cross_down:
        score -= 2
        reasons.append("❌ MACD ตัดลง")

    if near_lower_bb and is_uptrend:
        score += 2
        reasons.append("✅ ราคาใกล้ Lower Band + ขาขึ้น")

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

    st.markdown(f"""
    <h2 style="color:{color}; text-align:center; font-size:28px;">
        {signal} (Score: {score}/10)
    </h2>
    """, unsafe_allow_html=True)

    for reason in reasons:
        st.write(reason)

    # ====================== TAKE PROFIT & STOP LOSS ======================
    st.subheader("🎯 Take Profit / Stop Loss แนะนำ")

    current_price = latest['Close']
    bb_upper = latest['BB_upper']
    bb_lower = latest['BB_lower']

    if signal in ["🟢 **STRONG BUY**", "🟢 **BUY**"]:
        # สำหรับ Buy
        stop_loss = max(bb_lower * 0.98, current_price * 0.93)   # ไม่ต่ำกว่า 7%
        take_profit1 = current_price + (current_price - stop_loss) * 2   # Risk:Reward 1:2
        take_profit2 = current_price + (current_price - stop_loss) * 3   # Risk:Reward 1:3
        
        risk = current_price - stop_loss
        reward1 = take_profit1 - current_price
        reward2 = take_profit2 - current_price

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Stop Loss", f"{stop_loss:.2f}", f"-{((current_price-stop_loss)/current_price*100):.1f}%")
        with col2:
            st.metric("Take Profit 1 (1:2)", f"{take_profit1:.2f}", f"+{((reward1/risk)):.1f}x")
        with col3:
            st.metric("Take Profit 2 (1:3)", f"{take_profit2:.2f}", f"+{((reward2/risk)):.1f}x")

        st.info(f"**คำแนะนำ**: ตั้ง Stop Loss ที่ {stop_loss:.2f} และ Target หลักที่ {take_profit1:.2f}")

    elif signal in ["🔴 **STRONG SELL**", "🔴 **SELL**"]:
        # สำหรับ Sell
        stop_loss = min(bb_upper * 1.02, current_price * 1.07)
        take_profit1 = current_price - (stop_loss - current_price) * 2
        take_profit2 = current_price - (stop_loss - current_price) * 3
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Stop Loss", f"{stop_loss:.2f}", f"+{((stop_loss-current_price)/current_price*100):.1f}%")
        with col2:
            st.metric("Take Profit 1 (1:2)", f"{take_profit1:.2f}")
        with col3:
            st.metric("Take Profit 2 (1:3)", f"{take_profit2:.2f}")
        
        st.info("**คำแนะนำ**: สำหรับ Short Sell")

    else:
        st.write("⚪ **สถานะ Neutral** ไม่แนะนำเปิดตำแหน่งใหม่ในขณะนี้")

    st.divider()

    # กราฟและส่วนอื่นๆ (เหมือนเดิม)
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=df.index, y=df['Close'], name='ราคาปิด', line=dict(color='#008080', width=2)))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_upper'], name='BB Upper', line=dict(color='rgba(255,0,0,0.3)', dash='dash')))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_lower'], name='BB Lower', line=dict(color='rgba(0,0,255,0.3)', dash='dash'), fill='tonexty', fillcolor='rgba(0,0,255,0.05)'))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA 200', line=dict(color='orange', width=2, dash='dot')))
    
    fig_price.update_layout(title=f"กราฟราคา {ticker}", template="plotly_white", height=500, hovermode="x unified")
    st.plotly_chart(fig_price, use_container_width=True)

    # RSI + MACD (ย่อ)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("RSI (14)")
        fig_rsi = go.Figure()
        fig_rsi.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.15)
        fig_rsi.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.15)
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#FF4500', width=2.5)))
        fig_rsi.update_layout(template="plotly_white", height=320, yaxis=dict(range=[0,100]))
        st.plotly_chart(fig_rsi, use_container_width=True)

    with col2:
        st.subheader("MACD")
        fig_macd = make_subplots(rows=1, cols=1)
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue')))
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal', line=dict(color='orange')))
        fig_macd.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='Histogram',
                                marker_color=['green' if x >= 0 else 'red' for x in df['MACD_Hist']]))
        fig_macd.update_layout(template="plotly_white", height=320)
        st.plotly_chart(fig_macd, use_container_width=True)

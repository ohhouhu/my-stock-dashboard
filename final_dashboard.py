import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Stock Dashboard", layout="wide", page_icon="📈")
st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว")

# Sidebar
st.sidebar.header("⚙️ การตั้งค่า")
ticker = st.sidebar.text_input("กรอกสัญลักษณ์หุ้น:", value="AAPL").strip().upper()

period_options = ["1 เดือน", "3 เดือน", "6 เดือน", "1 ปี", "2 ปี", "5 ปี"]
selected_period = st.sidebar.selectbox("เลือกช่วงเวลา", period_options, index=3)

# แปลงช่วงเวลา
period_map = {
    "1 เดือน": "1mo", "3 เดือน": "3mo", "6 เดือน": "6mo",
    "1 ปี": "1y", "2 ปี": "2y", "5 ปี": "5y"
}

@st.cache_data(ttl=3600)  # Cache 1 ชั่วโมง
def get_stock_data(ticker, period):
    try:
        df = yf.download(ticker, period=period, interval="1d", 
                        auto_adjust=True, progress=False)
        
        if df.empty:
            return None
            
        # จัดการคอลัมน์
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # คำนวณ Indicators
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        # RSI 14
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
        
        return df
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
        return None

# ==================== แสดงผล ====================
if ticker:
    df = get_stock_data(ticker, period_map[selected_period])
    
    if df is None or df.empty:
        st.error(f"❌ ไม่พบข้อมูลหุ้น `{ticker}` กรุณาตรวจสอบสัญลักษณ์อีกครั้ง")
        st.info("ตัวอย่าง: AAPL, TSLA, NVDA, 0700.HK, PTT.BK")
        st.stop()

    st.success(f"✅ กำลังแสดงข้อมูล: **{ticker}** | ช่วงเวลา: {selected_period}")

    # กราฟราคาหลัก
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=df.index, y=df['Close'], 
                                 name='ราคาปิด', line=dict(color='#008080', width=2)))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA200'], 
                                 name='EMA 200', line=dict(color='orange', dash='dot', width=2)))
    
    fig_price.update_layout(
        title=f"กราฟราคา {ticker} (EMA 200)",
        template="plotly_white",
        height=550,
        hovermode="x unified",
        legend=dict(position="top left")
    )
    st.plotly_chart(fig_price, use_container_width=True)

    # RSI และ MACD
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("RSI (14)")
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], 
                                   name='RSI', line=dict(color='#FF4500')))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
        fig_rsi.update_layout(template="plotly_white", height=320)
        st.plotly_chart(fig_rsi, use_container_width=True)

    with col2:
        st.subheader("MACD")
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], 
                                    name='MACD', line=dict(color='blue')))
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal'], 
                                    name='Signal Line', line=dict(color='orange')))
        fig_macd.update_layout(template="plotly_white", height=320)
        st.plotly_chart(fig_macd, use_container_width=True)

    # สรุปสถานะ
    st.divider()
    latest = df.iloc[-1]
    
    is_uptrend = latest['Close'] > latest['EMA200']
    trend = "🟢 ขาขึ้น (เหนือ EMA200)" if is_uptrend else "🔴 ขาลง (ใต้ EMA200)"
    
    st.subheader(f"📌 สรุปสถานะล่าสุดของ {ticker}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("ราคาล่าสุด", f"{latest['Close']:.2f}")
    with c2:
        change = ((latest['Close'] - df.iloc[-2]['Close']) / df.iloc[-2]['Close']) * 100
        st.metric("เปลี่ยนแปลงวันนี้", f"{change:+.2f}%")
    with c3:
        st.metric("RSI", f"{latest['RSI']:.1f}")

    st.write(f"**แนวโน้มหลัก**: {trend}")

    if latest['RSI'] > 70:
        st.warning("**Overbought** - ราคาอาจย่อตัวลงในระยะสั้น")
    elif latest['RSI'] < 30:
        if is_uptrend:
            st.success("**Oversold + ขาขึ้น** → โอกาสซื้อดี")
        else:
            st.error("**Oversold + ขาลง** → ระวัง")
    else:
        st.info("สถานะปกติ")

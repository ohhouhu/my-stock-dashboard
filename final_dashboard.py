import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Stock Dashboard", layout="wide", page_icon="📈")

st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว (ฉบับสมบูรณ์)")

# ===================== SIDEBAR =====================
st.sidebar.header("⚙️ การตั้งค่า")
ticker = st.sidebar.text_input("กรอกสัญลักษณ์หุ้น:", value="AAPL").strip().upper()

# เพิ่มคำแนะนำหุ้นไทย
if ticker and not ticker.endswith('.BK') and len(ticker) < 5:
    st.sidebar.info(f"💡 ทริค: หุ้นไทยต้องเติม .BK (เช่น {ticker}.BK)")

period_options = ["1 เดือน", "3 เดือน", "6 เดือน", "1 ปี", "2 ปี", "5 ปี"]
selected_period = st.sidebar.selectbox("เลือกช่วงเวลา", period_options, index=3)

period_map = {
    "1 เดือน": "1mo", "3 เดือน": "3mo", "6 เดือน": "6mo",
    "1 ปี": "1y", "2 ปี": "2y", "5 ปี": "5y"
}

@st.cache_data(ttl=1800)
def get_stock_data(ticker, period):
    try:
        df = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False)
        if df.empty or len(df) < 20: return None
        if isinstance(df.columns, pd.MultiIndex): df = df.droplevel(1, axis=1)
        
        df = df.round(4)
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        df['BB_std'] = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
        df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)
        
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
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

# ===================== MAIN =====================
if ticker:
    df = get_stock_data(ticker, period_map[selected_period])
    if df is None:
        st.error(f"❌ ไม่พบข้อมูลหุ้น `{ticker}`")
        st.stop()

    st.success(f"✅ กำลังวิเคราะห์: **{ticker}** | ช่วงเวลา: {selected_period}")

    # 1. กราฟราคาหลัก
    st.subheader(f"📈 กราฟราคา {ticker}")
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=df.index, y=df['Close'], name='ราคาปิด', line=dict(color='#008080', width=2.5)))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name='EMA50', line=dict(color='purple', width=1.5)))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA200', line=dict(color='orange', width=2, dash='dot')))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_upper'], name='BB Upper', line=dict(color='rgba(255,0,0,0.3)', dash='dash')))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_lower'], name='BB Lower', line=dict(color='rgba(0,0,255,0.3)', dash='dash'), fill='tonexty', fillcolor='rgba(0,100,255,0.05)'))
    
    fig_price.update_layout(height=600, template="plotly_white", hovermode="x unified", legend=dict(orientation="h", x=0, y=1.05))
    fig_price.update_xaxes(showspikes=True, spikecolor="gray", spikemode="across", spikesnap="cursor")
    fig_price.update_yaxes(showspikes=True, spikecolor="gray", spikemode="across")
    st.plotly_chart(fig_price, use_container_width=True)

    # 2. Volume
    st.subheader("📊 ปริมาณการซื้อขาย (Volume)")
    fig_vol = go.Figure(go.Bar(x=df.index, y=df['Volume'], marker_color='#1E90FF'))
    fig_vol.update_layout(height=300, template="plotly_white", hovermode="x unified")
    st.plotly_chart(fig_vol, use_container_width=True)

    # 3. RSI
    st.subheader("📈 RSI (14)")
    fig_rsi = go.Figure()
    fig_rsi.add_hrect(70, 100, fillcolor="red", opacity=0.1); fig_rsi.add_hrect(30, 70, fillcolor="lightblue", opacity=0.1); fig_rsi.add_hrect(0, 30, fillcolor="green", opacity=0.1)
    fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='#FF4500', width=2)))
    fig_rsi.update_layout(height=350, template="plotly_white", hovermode="x unified", yaxis=dict(range=[0, 100]))
    st.plotly_chart(fig_rsi, use_container_width=True)

    # 4. MACD
    st.subheader("📈 MACD")
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue')))
    fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal', line=dict(color='orange')))
    fig_macd.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='Histogram', marker_color=['green' if x >= 0 else 'red' for x in df['MACD_Hist']]))
    fig_macd.update_layout(height=350, template="plotly_white", hovermode="x unified")
    st.plotly_chart(fig_macd, use_container_width=True)

    # 5. สรุปสถานะ (ไว้ท้ายสุด)
    st.divider()
    latest = df.iloc[-1]
    change = ((latest['Close'] - df.iloc[-2]['Close']) / df.iloc[-2]['Close']) * 100
    is_bullish = latest['Close'] > latest['EMA200']

    st.subheader(f"📌 สรุปสาเหตุและสถานะล่าสุด: {ticker}")
    c1, c2, c3 = st.columns(3)
    c1.metric("ราคาล่าสุด", f"{latest['Close']:.2f}", f"{change:+.2f}%")
    c2.metric("RSI", f"{latest['RSI']:.1f}")
    c3.metric("แนวโน้มหลัก", "ขาขึ้น" if is_bullish else "ขาลง")

    if latest['RSI'] > 70:
        st.warning("**สถานะ: Overbought** - ราคาขึ้นมาสูงมากในระยะสั้น ระวังการปรับฐานหรือย่อตัว")
    elif latest['RSI'] < 30:
        if is_bullish: st.success("**สถานะ: Oversold ในแนวโน้มขาขึ้น** - เป็นจังหวะย่อตัวในขาขึ้นที่น่าสนใจ (Buy the dip)")
        else: st.error("**สถานะ: Oversold ในแนวโน้มขาลง** - ระวังการรับมีด หุ้นอาจลงต่อได้อีก")
    else:
        st.info("สถานะ: ปกติ - ราคายังแกว่งตัวในระดับสมดุล")

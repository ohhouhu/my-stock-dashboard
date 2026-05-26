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
        df = yfinance.download(ticker, period=period, interval="1d", 
                              auto_adjust=True, progress=False)
        
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
        
        # MACD + Histogram
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

    st.success(f"✅ แสดงข้อมูล: **{ticker}** | {selected_period}")

    # กราฟราคาหลัก + Bollinger Bands
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=df.index, y=df['Close'], name='ราคาปิด', line=dict(color='#008080', width=2)))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_upper'], name='BB Upper', line=dict(color='rgba(255,0,0,0.3)', dash='dash')))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_lower'], name='BB Lower', line=dict(color='rgba(0,0,255,0.3)', dash='dash'), fill='tonexty', fillcolor='rgba(0,0,255,0.05)'))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_middle'], name='BB Middle (SMA20)', line=dict(color='gray', dash='dot')))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA 200', line=dict(color='orange', width=2, dash='dot')))
    
    fig_price.update_layout(
        title=f"กราฟราคา {ticker} + Bollinger Bands",
        template="plotly_white",
        height=550,
        hovermode="x unified",
        legend=dict(x=0, y=1.02, xanchor="left", yanchor="bottom")
    )
    st.plotly_chart(fig_price, use_container_width=True)

    # Volume
    st.subheader("📊 ปริมาณการซื้อขาย (Volume)")
    fig_volume = go.Figure()
    fig_volume.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='#1E90FF'))
    fig_volume.update_layout(template="plotly_white", height=300, hovermode="x unified")
    st.plotly_chart(fig_volume, use_container_width=True)

    # ====================== RSI แต่งใหม่ (สวยขึ้น) ======================
    st.subheader("📈 RSI (14)")
    fig_rsi = go.Figure()
    
    # พื้นที่สีโซน
    fig_rsi.add_hrect(y0=70, y1=100, line_width=0, fillcolor="red", opacity=0.15, annotation_text="Overbought")
    fig_rsi.add_hrect(y0=30, y1=70, line_width=0, fillcolor="lightblue", opacity=0.15, annotation_text="ปกติ")
    fig_rsi.add_hrect(y0=0, y1=30, line_width=0, fillcolor="green", opacity=0.15, annotation_text="Oversold")
    
    # เส้น RSI
    fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], 
                               name='RSI (14)', 
                               line=dict(color='#FF4500', width=2.5)))
    
    # เส้นสำคัญ
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="70")
    fig_rsi.add_hline(y=50, line_dash="dot", line_color="gray", annotation_text="50")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="30")
    
    # ค่าล่าสุด
    latest_rsi = df['RSI'].iloc[-1]
    fig_rsi.add_annotation(
        x=df.index[-1], y=latest_rsi,
        text=f" {latest_rsi:.1f}",
        showarrow=True,
        arrowhead=1,
        bgcolor="white",
        bordercolor="#FF4500"
    )
    
    fig_rsi.update_layout(
        template="plotly_white",
        height=380,
        hovermode="x unified",
        yaxis=dict(range=[0, 100], title="RSI"),
        legend=dict(x=0, y=1.02, xanchor="left", yanchor="bottom")
    )
    st.plotly_chart(fig_rsi, use_container_width=True)

    # MACD
    st.subheader("📈 MACD (Moving Average Convergence Divergence)")
    fig_macd = make_subplots(rows=1, cols=1, shared_xaxes=True)
    fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD Line', line=dict(color='blue')))
    fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal Line', line=dict(color='orange')))
    fig_macd.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], 
                            name='Histogram', 
                            marker_color=['green' if x >= 0 else 'red' for x in df['MACD_Hist']]))
    
    fig_macd.update_layout(
        template="plotly_white",
        height=350,
        hovermode="x unified",
        legend=dict(x=0, y=1.02, xanchor="left", yanchor="bottom")
    )
    fig_macd.add_hline(y=0, line_dash="dash", line_color="gray")
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
        st.warning("**Overbought** - ราคาอาจย่อตัวลง")
    elif latest['RSI'] < 30:
        if is_uptrend:
            st.success("**Oversold + ขาขึ้น** → โอกาสซื้อ")
        else:
            st.error("**Oversold + ขาลง** → ระวัง")
    else:
        st.info("สถานะปกติ")

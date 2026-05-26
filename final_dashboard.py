import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Stock Dashboard", layout="wide", page_icon="📈")

st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว")

# ===================== SIDEBAR =====================
st.sidebar.header("⚙️ การตั้งค่า")
ticker = st.sidebar.text_input("กรอกสัญลักษณ์หุ้น:", value="AAPL").strip().upper()

period_options = ["1 เดือน", "3 เดือน", "6 เดือน", "1 ปี", "2 ปี", "5 ปี", "10 ปี"]
selected_period = st.sidebar.selectbox("เลือกช่วงเวลา", period_options, index=3)

interval = st.sidebar.selectbox("ช่วงข้อมูล", ["1d", "1h"], index=0)

period_map = {
    "1 เดือน": "1mo", "3 เดือน": "3mo", "6 เดือน": "6mo",
    "1 ปี": "1y", "2 ปี": "2y", "5 ปี": "5y", "10 ปี": "10y"
}

@st.cache_data(ttl=1800)  # 30 นาที
def get_stock_data(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval,
                        auto_adjust=True, progress=False)
        
        if df.empty:
            return None
            
        # จัดการ MultiIndex (บางตัวอย่างเช่น .BK)
        if isinstance(df.columns, pd.MultiIndex):
            df = df.droplevel(1, axis=1)
            
        df = df.round(4)
        
        # ==================== Indicators ====================
        # EMA
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # Bollinger Bands
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        df['BB_std'] = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
        df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)
        
        # RSI
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, min_periods=14).mean()
        avg_loss = loss.ewm(com=13, min_periods=14).mean()
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

# ===================== MAIN =====================
if ticker:
    df = get_stock_data(ticker, period_map[selected_period], interval)
    
    if df is None or len(df) < 20:
        st.error(f"❌ ไม่พบข้อมูลหุ้น `{ticker}` หรือข้อมูลน้อยเกินไป")
        st.info("ตัวอย่าง: AAPL, TSLA, NVDA, PTT.BK, DELTA.BK, 0700.HK")
        st.stop()

    st.success(f"✅ แสดงข้อมูล: **{ticker}** | {selected_period} | {interval}")

    # ===================== กราฟราคาหลัก =====================
    fig_price = go.Figure()
    
    fig_price.add_trace(go.Scatter(x=df.index, y=df['Close'], name='ราคาปิด', 
                                  line=dict(color='#008080', width=2.5)))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA 200', 
                                  line=dict(color='orange', width=2, dash='dot')))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name='EMA 50', 
                                  line=dict(color='purple', width=1.5, dash='dash')))
    
    # Bollinger Bands
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_upper'], name='BB Upper', 
                                  line=dict(color='rgba(255,0,0,0.4)', dash='dash')))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_lower'], name='BB Lower', 
                                  line=dict(color='rgba(0,0,255,0.4)', dash='dash'),
                                  fill='tonexty', fillcolor='rgba(0,100,255,0.08)'))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_middle'], name='BB Middle (SMA20)', 
                                  line=dict(color='gray', dash='dot')))

    fig_price.update_layout(
        title=f"กราฟราคา {ticker} + Bollinger Bands & EMA",
        template="plotly_white",
        height=600,
        hovermode="x unified",
        legend=dict(x=0, y=1.02, xanchor="left", yanchor="bottom", orientation="h")
    )
    
    st.plotly_chart(fig_price, use_container_width=True)

    # ===================== Volume + RSI + MACD (ใน 2 คอลัมน์) =====================
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📊 ปริมาณการซื้อขาย")
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='#1E90FF'))
        fig_vol.update_layout(template="plotly_white", height=320, hovermode="x unified")
        st.plotly_chart(fig_vol, use_container_width=True)

        st.subheader("📈 MACD")
        fig_macd = make_subplots(rows=1, cols=1, shared_xaxes=True)
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue')))
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal', line=dict(color='orange')))
        fig_macd.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], 
                                name='Histogram',
                                marker_color=['green' if x >= 0 else 'red' for x in df['MACD_Hist']]))
        fig_macd.update_layout(template="plotly_white", height=320, hovermode="x unified")
        st.plotly_chart(fig_macd, use_container_width=True)

    with col2:
        st.subheader("📈 RSI (14)")
        fig_rsi = go.Figure()
        
        fig_rsi.add_hrect(70, 100, fillcolor="red", opacity=0.12, layer="below", line_width=0)
        fig_rsi.add_hrect(30, 70, fillcolor="lightblue", opacity=0.12, layer="below", line_width=0)
        fig_rsi.add_hrect(0, 30, fillcolor="green", opacity=0.12, layer="below", line_width=0)
        
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', 
                                    line=dict(color='#FF4500', width=2.5)))
        
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        fig_rsi.add_hline(y=50, line_dash="dot", line_color="gray")
        
        latest_rsi = df['RSI'].iloc[-1]
        fig_rsi.add_annotation(x=df.index[-1], y=latest_rsi, 
                             text=f"{latest_rsi:.1f}", showarrow=True, arrowhead=1)
        
        fig_rsi.update_layout(template="plotly_white", height=640, hovermode="x unified", 
                            yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig_rsi, use_container_width=True)

    # ===================== สรุปสถานะ =====================
    st.divider()
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    change = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
    is_bullish = latest['Close'] > latest['EMA200']
    
    st.subheader(f"📌 สรุปสถานะล่าสุดของ {ticker}")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("ราคาล่าสุด", f"{latest['Close']:.2f}", f"{change:+.2f}%")
    with c2:
        st.metric("RSI", f"{latest['RSI']:.1f}")
    with c3:
        st.metric("MACD Hist", f"{latest['MACD_Hist']:.3f}")
    with c4:
        trend = "🟢 ขาขึ้น (เหนือ EMA200)" if is_bullish else "🔴 ขาลง (ใต้ EMA200)"
        st.write("**แนวโน้มหลัก**")
        st.write(trend)

    # คำแนะนำ
    if latest['RSI'] > 75:
        st.error("**Overbought แรง** - ระวังการปรับตัวลง")
    elif latest['RSI'] < 25:
        st.success("**Oversold แรง** - พิจารณาเปิดตำแหน่ง")
    elif 70 < latest['RSI'] < 75:
        st.warning("**Overbought**")
    elif 25 < latest['RSI'] < 30:
        st.info("**Oversold**")

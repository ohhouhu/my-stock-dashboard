import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Institutional Dashboard", layout="wide")
st.title("📊 ระบบวิเคราะห์หุ้นระดับสถาบัน (Full Professional)")

# Sidebar
ticker = st.sidebar.text_input("กรอกสัญลักษณ์หุ้น:", value="AAPL").strip().upper()
selected_period = st.sidebar.selectbox("เลือกช่วงเวลา", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
interval = st.sidebar.selectbox("ช่วงข้อมูล", ["1d", "1h"], index=0)

@st.cache_data(ttl=1800)
def get_full_data(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # 1. สมการขาใหญ่
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        money_flow = typical_price * df['Volume']
        pos_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
        neg_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
        mfi_ratio = pos_flow.rolling(14).sum() / neg_flow.rolling(14).sum()
        df['MFI'] = 100 - (100 / (1 + mfi_ratio))
        
        # 2. Indicators เดิม
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['RSI'] = 100 - (100 / (1 + (df['Close'].diff().clip(lower=0).ewm(14).mean() / -df['Close'].diff().clip(upper=0).ewm(14).mean())))
        return df
    except: return None

df = get_full_data(ticker, selected_period, interval)

if df is not None:
    # กราฟหลัก Candlestick
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name='VWAP (ต้นทุนขาใหญ่)', line=dict(color='orange', width=2)))
    fig.update_layout(height=500, template="plotly_white", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # สรุปข้อมูล
    latest = df.iloc[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("ราคาปิด", f"{latest['Close']:.2f}")
    c2.metric("MFI (กระแสเงิน)", f"{latest['MFI']:.1f}")
    c3.metric("สถานะราคา", "แข็งแกร่ง" if latest['Close'] > latest['VWAP'] else "อ่อนแอ")

    # AI วิเคราะห์
    st.divider()
    st.subheader("🧠 AI วิเคราะห์ระดับมืออาชีพ")
    if latest['Close'] > latest['VWAP'] and latest['MFI'] > 50:
        st.success("✅ สัญญาณขาใหญ่: ราคาอยู่เหนือต้นทุนสถาบันและเงินยังไหลเข้าต่อเนื่อง")
    elif latest['MFI'] < 20:
        st.info("⚠️ สัญญาณสะสม: เงินไหลออกจนเหือดแห้ง เป็นจังหวะเฝ้าระวังการกลับตัว")
    else:
        st.warning("⚠️ สัญญาณเตือน: แรงซื้อจากสถาบันไม่ชัดเจน ระวังความผันผวน")
else:
    st.error("กรุณาตรวจสอบสัญลักษณ์หุ้น")

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Institutional Dashboard", layout="wide", page_icon="🏦")
st.title("📊 ระบบวิเคราะห์หุ้นระดับสถาบัน (Institutional Grade)")

# Sidebar
ticker = st.sidebar.text_input("กรอกสัญลักษณ์หุ้น:", value="AAPL").strip().upper()
period_map = {"1 ปี": "1y", "2 ปี": "2y", "5 ปี": "5y"}
selected_period = st.sidebar.selectbox("ช่วงเวลา", list(period_map.keys()), index=0)

@st.cache_data(ttl=1800)
def get_institutional_data(ticker, period):
    df = yf.download(ticker, period=period, interval="1d", progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # VWAP Calculation
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    
    # MFI Calculation
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    money_flow = typical_price * df['Volume']
    pos_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
    neg_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
    mfi_ratio = pos_flow.rolling(14).sum() / neg_flow.rolling(14).sum()
    df['MFI'] = 100 - (100 / (1 + mfi_ratio))
    
    # Standard Indicators
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    return df

if ticker:
    df = get_institutional_data(ticker, period_map[selected_period])
    if df is None: st.stop()
    
    # 1. กราฟราคา + VWAP
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name='VWAP (ต้นทุนรายใหญ่)', line=dict(color='orange', width=2)))
    fig.update_layout(height=600, template="plotly_white", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # 2. วิเคราะห์เชิงสถาบัน
    st.divider()
    latest = df.iloc[-1]
    st.subheader("🏦 AI วิเคราะห์มุมมองขาใหญ่ (Institutional Logic)")
    
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"### MFI: {latest['MFI']:.1f}")
        if latest['MFI'] > 80: st.warning("⚠️ ขาใหญ่เริ่มรินขายทำกำไร (Overbought)")
        elif latest['MFI'] < 20: st.success("✅ ขาใหญ่เริ่มเข้าสะสมของ (Oversold)")
        else: st.info("การไหลของเงินยังอยู่ในระดับปกติ")
            
    with c2:
        status = "แข็งแกร่ง" if latest['Close'] > latest['VWAP'] else "อ่อนแอ"
        st.write(f"### สถานะราคาเทียบ VWAP: {status}")
        st.write(f"• ราคาปัจจุบัน: {latest['Close']:.2f}")
        st.write(f"• ต้นทุนเฉลี่ยรายใหญ่ (VWAP): {latest['VWAP']:.2f}")
        if status == "แข็งแกร่ง": st.success("ราคาอยู่เหนือต้นทุนเฉลี่ยรายใหญ่")
        else: st.error("ราคาหลุดเส้นต้นทุนเฉลี่ยรายใหญ่ ระวังแรงขาย")

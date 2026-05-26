import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Dashboard", layout="wide")

# พื้นหลังสีขาวสะอาดตา
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3, div, p { color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว (Standard & Clean)")

# Sidebar
ticker = st.sidebar.text_input("วิเคราะห์รายตัว:", value="AAPL")

@st.cache_data
def get_data(ticker):
    df = yf.download(ticker, period="1y", interval="1d", auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    # เพิ่มเส้น EMA 200 วัน
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    return df

if ticker:
    df = get_data(ticker)
    if not df.empty:
        # กราฟราคา + เส้น EMA 200
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='ราคาปิด', line=dict(color='#008080')))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA 200', line=dict(color='orange', dash='dot')))
        fig.update_layout(title=f"กราฟราคา {ticker} & EMA 200", template="plotly_white", height=400)
        st.plotly_chart(fig, use_container_width=True)

        # สูตร RSI แบบ Wilder's (แม่นยำขึ้น)
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        exp1, exp2 = df['Close'].ewm(span=12, adjust=False).mean(), df['Close'].ewm(span=26, adjust=False).mean()
        macd, signal = exp1 - exp2, (exp1 - exp2).ewm(span=9, adjust=False).mean()

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("RSI (Wilder's Smoothing)")
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df.index, y=rsi, line=dict(color='#FF4500')))
            fig_rsi.update_layout(template="plotly_white", height=250)
            st.plotly_chart(fig_rsi, use_container_width=True)
        with c2:
            st.subheader("MACD")
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(x=df.index, y=macd, name='MACD', line=dict(color='blue')))
            fig_macd.add_trace(go.Scatter(x=df.index, y=signal, name='Signal', line=dict(color='red')))
            fig_macd.update_layout(template="plotly_white", height=250)
            st.plotly_chart(fig_macd, use_container_width=True)

        # สรุปผล
        latest_rsi = rsi.iloc[-1]
        st.subheader(f"สถานะล่าสุด: {ticker}")
        if latest_rsi > 70: st.info("สถานะ: Overbought (ระวัง!)")
        elif latest_rsi < 30: st.success("สถานะ: Oversold (น่าสนใจ)")
        else: st.write("สถานะ: ปกติ")

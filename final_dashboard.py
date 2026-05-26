import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Dashboard", layout="wide")

st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว")

# Sidebar
st.sidebar.header("การตั้งค่า")
ticker = st.sidebar.text_input("วิเคราะห์รายตัว:", value="AAPL")
tickers = st.sidebar.multiselect("เปรียบเทียบหุ้น:", ["AAPL", "NVDA", "TSLA", "MSFT", "PTT.BK"], default=["AAPL", "NVDA"])

@st.cache_data
def get_data(ticker):
    df = yf.download(ticker, period="1y", interval="1d", auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    return df

# 1. ส่วนเปรียบเทียบ
if tickers:
    st.subheader("กราฟเปรียบเทียบผลตอบแทน (%)")
    df_multi = yf.download(tickers, period="1y", interval="1d", auto_adjust=True)['Close']
    norm_df = (df_multi / df_multi.iloc[0] - 1) * 100
    st.line_chart(norm_df)

st.divider()

# 2. วิเคราะห์เจาะลึก
if ticker:
    df = get_data(ticker)
    if not df.empty and 'Close' in df.columns:
        st.subheader(f"วิเคราะห์เชิงลึก: {ticker}")
        
        # กราฟราคา
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='ราคาปิด', line=dict(color='#008080')))
        fig.update_layout(title=f"กราฟราคา {ticker}", template="plotly_white", height=400)
        st.plotly_chart(fig, use_container_width=True)

        # คำนวณ RSI & MACD
        delta = df['Close'].diff()
        rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / (-delta.where(delta < 0, 0).rolling(14).mean()))))
        exp1, exp2 = df['Close'].ewm(span=12, adjust=False).mean(), df['Close'].ewm(span=26, adjust=False).mean()
        macd, signal = exp1 - exp2, (exp1 - exp2).ewm(span=9, adjust=False).mean()

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("RSI")
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df.index, y=rsi, line=dict(color='#FF4500')))
            fig_rsi.update_layout(template="plotly_white", height=250)
            st.plotly_chart(fig_rsi, use_container_width=True)
        with c2:
            st.subheader("MACD")
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(x=df.index, y=macd, name='MACD', line=dict(color='blue')))
            fig_macd.add_trace(go.Scatter(x=df.index, y=signal, name='Signal', line=dict(color='orange')))
            fig_macd.update_layout(template="plotly_white", height=250)
            st.plotly_chart(fig_macd, use_container_width=True)

        # ตาราง Quick Stats พร้อมสถานะ Overbought/Oversold
        st.subheader(f"สรุปสถานะล่าสุดของ {ticker}")
        
        latest_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change_pct = ((latest_price - prev_price) / prev_price) * 100
        latest_rsi = rsi.iloc[-1]
        
        # แบ่งเป็น 3 ช่อง (ราคา, RSI, สถานะ)
        col1, col2, col3 = st.columns(3)
        
        col1.metric("ราคาล่าสุด", f"${latest_price:.2f}", f"{change_pct:.2f}%")
        col2.metric("ค่า RSI", f"{latest_rsi:.2f}")
        
        # ตัวที่หายไป: Logic เช็คสถานะ RSI
        if latest_rsi > 70:
            col3.info("สถานะ: Overbought (ระวัง!)")
        elif latest_rsi < 30:
            col3.success("สถานะ: Oversold (น่าสนใจ)")
        else:
            col3.write("สถานะ: ปกติ")
            
   

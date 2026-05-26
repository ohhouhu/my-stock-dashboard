import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. ตั้งค่าหน้าเว็บให้เป็น Dark Theme ตั้งแต่เริ่มต้น
st.set_page_config(page_title="Stock Dashboard", layout="wide", initial_sidebar_state="expanded")

# 2. ใส่ CSS ให้พื้นหลังมืดสนิท
st.markdown("""
    <style>
    .stApp { background-color: #121212; }
    h1, h2, h3, div, p { color: #e0e0e0 !important; }
    section[data-testid="stSidebar"] { background-color: #1e1e1e; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว (Dark Mode Premium)")

# 3. Sidebar
ticker = st.sidebar.text_input("วิเคราะห์รายตัว:", value="AAPL")
tickers = st.sidebar.multiselect("เปรียบเทียบหุ้น:", ["AAPL", "NVDA", "TSLA", "MSFT", "PTT.BK"], default=["AAPL", "NVDA"])

# --- ฟังก์ชันดึงข้อมูล ---
@st.cache_data
def get_data(ticker):
    df = yf.download(ticker, period="1y", interval="1d", auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    return df

# --- กราฟเปรียบเทียบ ---
if tickers:
    st.subheader("กราฟเปรียบเทียบผลตอบแทน (%)")
    df_multi = yf.download(tickers, period="1y", interval="1d", auto_adjust=True)['Close']
    norm_df = (df_multi / df_multi.iloc[0] - 1) * 100
    st.line_chart(norm_df)

st.divider()

# --- วิเคราะห์เจาะลึก ---
if ticker:
    df = get_data(ticker)
    if not df.empty and 'Close' in df.columns:
        # กราฟราคา
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='ราคาปิด', line=dict(color='#008080')))
        fig.update_layout(title=f"กราฟราคา {ticker}", template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)

        # คำนวณ RSI & MACD
        delta = df['Close'].diff()
        rsi = 100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / (-delta.where(delta < 0, 0).rolling(14).mean()))))
        exp1, exp2 = df['Close'].ewm(span=12, adjust=False).mean(), df['Close'].ewm(span=26, adjust=False).mean()
        macd, signal = exp1 - exp2, (exp1 - exp2).ewm(span=9, adjust=False).mean()

        # แสดง RSI & MACD (ใช้ plotly_dark ทุกตัว)
        c1, c2 = st.columns(2)
        with c1:
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df.index, y=rsi, name='RSI', line=dict(color='#FF4500')))
            fig_rsi.update_layout(title="RSI", template="plotly_dark", height=250)
            st.plotly_chart(fig_rsi, use_container_width=True)
        with c2:
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(x=df.index, y=macd, name='MACD', line=dict(color='cyan')))
            fig_macd.add_trace(go.Scatter(x=df.index, y=signal, name='Signal', line=dict(color='orange')))
            fig_macd.update_layout(title="MACD", template="plotly_dark", height=250)
            st.plotly_chart(fig_macd, use_container_width=True)
            
        # Quick Stats
        latest = df['Close'].iloc[-1]
        col1, col2 = st.columns(2)
        col1.metric("ราคาล่าสุด", f"${latest:.2f}")
        col2.metric("สถานะ RSI", f"{rsi.iloc[-1]:.2f}")
    else:
        st.warning("ไม่พบข้อมูลหุ้น")

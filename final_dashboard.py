import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Dashboard", layout="wide")

# ปรับ CSS ให้ดูสะอาดขึ้นนิดหน่อย
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว (Premium Look)")

ticker = st.sidebar.text_input("ใส่ชื่อหุ้น (เช่น AAPL, PTT.BK):", value="AAPL")

@st.cache_data
def get_data(ticker):
    df = yf.download(ticker, period="1y", interval="1d", auto_adjust=True)
    return df

if ticker:
    df = get_data(ticker)
    
    if not df.empty and 'Close' in df.columns:
        close_price = df['Close']
        if isinstance(close_price, pd.DataFrame): close_price = close_price.iloc[:, 0]
        
        # ใช้ Plotly แทน line_chart ธรรมดา
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=close_price, mode='lines', name='ราคาปิด', line=dict(color='#008080', width=2)))
        fig.update_layout(title=f"กราฟราคา {ticker}", template="plotly_white", height=400)
        st.plotly_chart(fig, use_container_width=True)

        # คำนวณ RSI
        delta = close_price.diff()
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # แสดงกราฟ RSI แบบสวยๆ ด้วย Plotly
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df.index, y=rsi, mode='lines', name='RSI', line=dict(color='#FF4500')))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        fig_rsi.update_layout(title="ดัชนี RSI (14 วัน)", template="plotly_white", height=300)
        st.plotly_chart(fig_rsi, use_container_width=True)
       
        # เพิ่มการคำนวณ MACD
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        exp1 = df['Close'].ewm(span=12, adjust=False).mean() # EMA 12 วัน
        exp2 = df['Close'].ewm(span=26, adjust=False).mean() # EMA 26 วัน
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean() # เส้นสัญญาณ
        st.line_chart(df[['MACD', 'Signal_Line']])
    else:
        st.warning("ไม่พบข้อมูลหุ้นตัวนี้ครับ")

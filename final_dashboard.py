import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Dashboard", layout="wide")

# ปรับ CSS ให้ดูสะอาดขึ้น
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว (Premium Look)")
ticker = st.sidebar.text_input("ใส่ชื่อหุ้น (เช่น AAPL, PTT.BK):", value="AAPL")
# เปลี่ยนจาก text_input เป็น multiselect ให้เลือกได้หลายตัว
tickers = st.sidebar.multiselect("เลือกหุ้นที่ต้องการเปรียบเทียบ:", 
                                 ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "PTT.BK"], 
                                 default=["AAPL", "NVDA"])

@st.cache_data
def get_data(ticker):
    df = yf.download(ticker, period="1y", interval="1d", auto_adjust=True)
    # แก้ปัญหา Multi-Index ตั้งแต่ดึงข้อมูล
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

if ticker:
    df = get_data(ticker)
    
    if not df.empty and 'Close' in df.columns:
        
        # กราฟราคา
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='ราคาปิด', line=dict(color='#008080', width=2)))
        fig.update_layout(title=f"กราฟราคา {ticker}", template="plotly_white", height=400)
        st.plotly_chart(fig, use_container_width=True)

        # คำนวณ RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        st.subheader("ดัชนี RSI (14 วัน)")
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df.index, y=rsi, mode='lines', name='RSI', line=dict(color='#FF4500')))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        fig_rsi.update_layout(template="plotly_white", height=300)
        st.plotly_chart(fig_rsi, use_container_width=True)
        
        # คำนวณ MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        st.subheader(f"กราฟ MACD ของ {ticker}")
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue')))
        fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], name='Signal', line=dict(color='orange')))
        fig_macd.update_layout(template="plotly_white", height=300)
        st.plotly_chart(fig_macd, use_container_width=True)
        # --- เพิ่มส่วนตาราง Quick Stats ---
        st.subheader(f"สรุปสถานะล่าสุดของ {ticker}")
        
        # ดึงข้อมูลล่าสุด
        latest_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change_pct = ((latest_price - prev_price) / prev_price) * 100
        latest_rsi = rsi.iloc[-1]
        
        # สร้าง Columns สำหรับวางตัวเลข 3 ตัว
        col1, col2, col3 = st.columns(3)
        
        col1.metric(label="ราคาล่าสุด", value=f"${latest_price:.2f}", delta=f"{change_pct:.2f}%")
        col2.metric(label="ค่า RSI", value=f"{latest_rsi:.2f}")
        
        # บอกสถานะ RSI
        if latest_rsi > 70:
            col3.info("สถานะ: Overbought (ระวัง!)")
        elif latest_rsi < 30:
            col3.success("สถานะ: Oversold (น่าสนใจ)")
        else:
            col3.write("สถานะ: ปกติ")

    else:
        st.warning("ไม่พบข้อมูลหุ้นตัวนี้ครับ")

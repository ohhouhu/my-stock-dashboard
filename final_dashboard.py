import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Dashboard", layout="wide")
# --- 1. สร้างปุ่มสลับธีม ---
dark_mode = st.sidebar.toggle("Dark Mode", value=False)

# --- 2. เปลี่ยนสีตามสถานะปุ่ม ---
if dark_mode:
    bg_color = "#1e1e1e"  # เทาเข้ม
    text_color = "#ffffff" # ขาว
    st.markdown(f"""
        <style>
        .main {{ background-color: {bg_color}; color: {text_color}; }}
        h1, h2, h3, div {{ color: {text_color}; }}
        </style>
        """, unsafe_allow_html=True)
else:
    bg_color = "#f5f5f5" # เทาอ่อน (ค่าเริ่มต้นเดิม)
    text_color = "#000000"
    st.markdown(f"""
        <style>
        .main {{ background-color: {bg_color}; color: {text_color}; }}
        </style>
        """, unsafe_allow_html=True)

# ปรับ CSS ให้ดูสะอาดขึ้น
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว (Premium Look)")

# --- ส่วนรับค่าจาก Sidebar ---
st.sidebar.header("การตั้งค่า")
ticker = st.sidebar.text_input("วิเคราะห์รายตัว (เช่น AAPL):", value="AAPL")
tickers = st.sidebar.multiselect("เปรียบเทียบหุ้น:", 
                                 ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "PTT.BK"], 
                                 default=["AAPL", "NVDA"])

# --- ฟังก์ชันดึงข้อมูล ---
@st.cache_data
def get_data(ticker):
    df = yf.download(ticker, period="1y", interval="1d", auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

@st.cache_data
def get_multi_data(tickers):
    df = yf.download(tickers, period="1y", interval="1d", auto_adjust=True)['Close']
    # คำนวณ % การเปลี่ยนแปลงเทียบกับวันแรก
    norm_df = (df / df.iloc[0] - 1) * 100
    return norm_df

# --- 1. ส่วนเปรียบเทียบหุ้น (Multi-Ticker) ---
if tickers:
    st.subheader("กราฟเปรียบเทียบผลตอบแทน (%)")
    df_multi = get_multi_data(tickers)
    st.line_chart(df_multi)

# --- 2. ส่วนวิเคราะห์เจาะลึก (Single Ticker) ---
st.divider()
if ticker:
    df = get_data(ticker)
    
    if not df.empty and 'Close' in df.columns:
        st.subheader(f"วิเคราะห์เชิงลึก: {ticker}")
        
        # กราฟราคา
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='ราคาปิด', line=dict(color='#008080', width=2)))
        # เปลี่ยน template จาก "plotly_white" เป็น "plotly_dark" ถ้าพี่ชอบ Dark Mode
        # แก้ไขโค้ดส่วนที่ Error ของพี่
        fig.update_layout(title=f"กราฟราคา {ticker}", template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)

        # คำนวณ RSI & MACD
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()

        # แสดง RSI & MACD
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("RSI (14 วัน)")
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df.index, y=rsi, line=dict(color='#FF4500')))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
            ffig_rsi.update_layout(template="plotly_dark", height=250) 
            st.plotly_chart(fig_rsi, use_container_width=True)
        
        with c2:
            st.subheader("MACD")
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(x=df.index, y=macd, name='MACD', line=dict(color='blue')))
            fig_macd.add_trace(go.Scatter(x=df.index, y=signal, name='Signal', line=dict(color='orange')))
            fig_macd.update_layout(template="plotly_dark", height=250) 
            st.plotly_chart(fig_macd, use_container_width=True)
        
        # ตาราง Quick Stats
        st.subheader(f"สรุปสถานะล่าสุดของ {ticker}")
        latest_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change_pct = ((latest_price - prev_price) / prev_price) * 100
        latest_rsi = rsi.iloc[-1]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("ราคาล่าสุด", f"${latest_price:.2f}", f"{change_pct:.2f}%")
        col2.metric("ค่า RSI", f"{latest_rsi:.2f}")
        if latest_rsi > 70: col3.info("สถานะ: Overbought")
        elif latest_rsi < 30: col3.success("สถานะ: Oversold")
        else: col3.write("สถานะ: ปกติ")

    else:
        st.warning("ไม่พบข้อมูลหุ้นตัวนี้ครับ")

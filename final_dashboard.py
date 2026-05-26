import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Dashboard", layout="wide")

st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว (สวยงามแบบเดิม)")

# Sidebar
st.sidebar.header("การตั้งค่า")
ticker = st.sidebar.text_input("วิเคราะห์รายตัว:", value="AAPL")

# ใช้ Multiselect ที่สวยงาม (แบบที่พี่ชอบ)
default_tickers = ["AAPL", "NVDA", "TSLA", "MSFT", "PTT.BK"]
tickers = st.sidebar.multiselect("เปรียบเทียบหุ้น:", default_tickers, default=["AAPL", "NVDA"])

@st.cache_data
def get_data(ticker):
    df = yf.download(ticker, period="1y", interval="1d", auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    return df

# 1. ส่วนเปรียบเทียบ (แบบ Multiselect สวยๆ)
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
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA 200', line=dict(color='orange', dash='dot')))
        fig.update_layout(title=f"กราฟราคา {ticker}", template="plotly_white", height=400)
        st.plotly_chart(fig, use_container_width=True)

        # คำนวณ RSI & MACD
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rsi = 100 - (100 / (1 + (avg_gain / avg_loss)))
        
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

        # 3. สรุปผลสถานะ (ไว้ท้ายสุด)
        st.divider()
        st.subheader(f"สรุปสาเหตุและสถานะล่าสุด: {ticker}")
        latest_rsi = rsi.iloc[-1]
        is_uptrend = df['Close'].iloc[-1] > df['EMA200'].iloc[-1]
        trend_text = "ขาขึ้น" if is_uptrend else "ขาลง"
        
        st.write(f"แนวโน้มหลัก (EMA 200): **{trend_text}**")
        
        if latest_rsi > 70:
            st.warning("**สถานะ: Overbought (ระวัง!)**")
            st.write("สาเหตุ: RSI สูงกว่า 70 บ่งบอกว่ามีการไล่ซื้อมากเกินไป ราคาอาจเกิดการย่อตัวได้")
        elif latest_rsi < 30:
            st.success("**สถานะ: Oversold (น่าสนใจ)**")
            if is_uptrend:
                st.write("สาเหตุ: RSI ต่ำกว่า 30 ในแนวโน้มขาขึ้น นี่คือจังหวะ Buy the dip")
            else:
                st.write("สาเหตุ: RSI ต่ำกว่า 30 แต่อยู่ในแนวโน้มขาลง ระวังการรับมีด")
        else:
            st.write(f"สถานะ: ปกติ (RSI อยู่ที่ {latest_rsi:.2f})")
            st.write("สาเหตุ: ราคายังแกว่งตัวอยู่ในระดับสมดุล ไม่ร้อนแรงจนเกินไป")

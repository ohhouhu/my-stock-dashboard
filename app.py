import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="AI Scalping Dashboard", layout="wide")

# 1. การดึงข้อมูล
@st.cache_data(ttl=60)
def get_data(ticker):
    df = yf.download(ticker, period="5d", interval="1m", auto_adjust=True, progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df = df.droplevel(1, axis=1)
    
    # คำนวณ Indicators
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    delta = df['Close'].diff()
    gain = delta.clip(lower=0); loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, min_periods=14).mean()
    avg_loss = loss.ewm(com=13, min_periods=14).mean()
    df['RSI'] = 100 - (100 / (1 + avg_gain / avg_loss))
    return df

# 2. AI วิเคราะห์
def ai_analyze(df):
    latest = df.iloc[-1]
    score = 0
    insights = []
    if latest['Close'] > latest['EMA200']: score += 2
    if latest['RSI'] < 30: score += 3; insights.append("🟢 RSI ต่ำ: สัญญาณเตรียมกลับตัว")
    if latest['RSI'] > 70: score -= 3; insights.append("🔴 RSI สูง: ระวังแรงขาย")
    return score, insights

# 3. แสดงผล
ticker = st.sidebar.text_input("สัญลักษณ์หุ้น", "AAPL").strip().upper()
if ticker:
    df = get_data(ticker)
    if df is not None:
        score, insights = ai_analyze(df)
        st.title(f"Dashboard: {ticker}")
        
        # กราฟ
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        st.plotly_chart(fig, use_container_width=True)
        
        # ผลสรุป AI
        st.subheader("🤖 AI Scalping Insight")
        st.write(f"คะแนนความน่าสนใจ: {score}")
        for i in insights: st.info(i)
    else:
        st.error("ไม่พบข้อมูล")

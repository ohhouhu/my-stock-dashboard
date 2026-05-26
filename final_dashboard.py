import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# เพิ่มฟังก์ชันคำนวณขั้นสูง
def calculate_quant_indicators(df):
    # ADX (วัดความแข็งแกร่งของเทรนด์)
    plus_di = 100 * (df['High'] - df['High'].shift(1)).clip(lower=0).ewm(alpha=1/14).mean() / (df['High']-df['Low']).rolling(14).mean()
    minus_di = 100 * (df['Low'].shift(1) - df['Low']).clip(lower=0).ewm(alpha=1/14).mean() / (df['High']-df['Low']).rolling(14).mean()
    df['ADX'] = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
    # ATR (ตั้งจุด Stop Loss)
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    return df

# ... (ส่วนการเรียกใช้ข้อมูลเดิม) ...

# ในส่วน AI วิเคราะห์ ให้เพิ่ม "การตัดสินใจเชิงปริมาณ" เข้าไป:
    st.subheader(f"🧠 AI Quant Analysis: {ticker}")
    c1, c2 = st.columns(2)
    
    # เงื่อนไขขั้นเทพ
    trend_strength = "แข็งแกร่งมาก" if latest['ADX'] > 25 else "ไร้ทิศทาง (พักตัว)"
    stop_loss = latest['Close'] - (latest['ATR'] * 2) # สูตรคำนวณ Stop Loss ของสถาบัน
    
    with c1:
        st.write(f"• **ความแข็งแกร่งของเทรนด์ (ADX):** {latest['ADX']:.1f} → {trend_strength}")
        st.write(f"• **Volatility-based Stop Loss:** {stop_loss:.2f}")
    with c2:
        if latest['ADX'] > 25 and latest['Close'] > latest['VWAP']:
            st.success("✅ ระบบ Quant แนะนำ: เทรนด์แข็งแกร่งและอยู่เหนือต้นทุนสถาบัน → BUY/HOLD")
        else:
            st.info("ℹ️ ระบบ Quant แนะนำ: ตลาดไร้ทิศทางหรือความเสี่ยงสูง → WAIT/REDUCE RISK")

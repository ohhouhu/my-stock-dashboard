import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Stock Dashboard", layout="wide", page_icon="📈")

# ===================== SIDEBAR NAVIGATION =====================
st.sidebar.header("📍 เมนูหลัก")
page = st.sidebar.radio("เลือกหน้าที่ต้องการ", 
                       ["📊 วิเคราะห์หุ้นเดี่ยว", "🔄 เปรียบเทียบหลายหุ้น"])

# ===================== PAGE 1: วิเคราะห์หุ้นเดี่ยว =====================
if page == "📊 วิเคราะห์หุ้นเดี่ยว":
    st.title("📊 ระบบวิเคราะห์หุ้นส่วนตัว")

    # Setting
    col_set1, col_set2 = st.columns([3,1])
    with col_set1:
        ticker = st.text_input("กรอกสัญลักษณ์หุ้น:", value="AAPL").strip().upper()
    with col_set2:
        period_options = ["1 เดือน", "3 เดือน", "6 เดือน", "1 ปี", "2 ปี", "5 ปี"]
        selected_period = st.selectbox("ช่วงเวลา", period_options, index=3)

    period_map = {"1 เดือน": "1mo", "3 เดือน": "3mo", "6 เดือน": "6mo",
                  "1 ปี": "1y", "2 ปี": "2y", "5 ปี": "5y"}

    @st.cache_data(ttl=1800)
    def get_stock_data(ticker, period):
        try:
            df = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False)
            if df.empty or len(df) < 20:
                return None
            if isinstance(df.columns, pd.MultiIndex):
                df = df.droplevel(1, axis=1)
            df = df.round(4)
            
            # Technical Indicators
            df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
            df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
            df['BB_middle'] = df['Close'].rolling(20).mean()
            df['BB_std'] = df['Close'].rolling(20).std()
            df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
            df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)
            
            delta = df['Close'].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            df['RSI'] = 100 - (100 / (1 + gain.ewm(com=13, min_periods=14).mean() / loss.ewm(com=13, min_periods=14).mean()))
            
            exp12 = df['Close'].ewm(span=12, adjust=False).mean()
            exp26 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp12 - exp26
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Hist'] = df['MACD'] - df['Signal']
            
            return df
        except:
            return None

    if ticker:
        df = get_stock_data(ticker, period_map[selected_period])
        
        if df is None:
            st.error(f"❌ ไม่พบข้อมูลหุ้น `{ticker}`")
            st.stop()

        st.success(f"✅ แสดงข้อมูล: **{ticker}** | {selected_period}")

        # กราฟราคา
        st.subheader(f"📈 กราฟราคา {ticker}")
        fig_price = go.Figure()
        fig_price.add_trace(go.Scatter(x=df.index, y=df['Close'], name='ราคาปิด', line=dict(color='#008080', width=2.8)))
        fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name='EMA50', line=dict(color='purple')))
        fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA200', line=dict(color='orange', dash='dot')))
        fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_upper'], name='BB Upper', line=dict(color='red', dash='dash')))
        fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_lower'], name='BB Lower', line=dict(color='blue', dash='dash'),
                                      fill='tonexty', fillcolor='rgba(0,100,255,0.08)'))
        
        fig_price.update_layout(height=600, template="plotly_white", hovermode="x unified", legend_orientation="h")
        st.plotly_chart(fig_price, use_container_width=True)

        # Volume, RSI, MACD เรียงลงมา
        st.subheader("📊 ปริมาณการซื้อขาย")
        st.plotly_chart(go.Figure(go.Bar(x=df.index, y=df['Volume'], marker_color='#1E90FF')).update_layout(height=350, template="plotly_white"), use_container_width=True)

        # RSI + MACD (เหมือนเดิม)
        col_rsi, col_macd = st.columns(2)
        with col_rsi:
            st.subheader("📈 RSI (14)")
            # ... (ใส่โค้ด RSI เหมือนเดิม)
        with col_macd:
            st.subheader("📈 MACD")
            # ... (ใส่โค้ด MACD เหมือนเดิม)

        # ===================== ตารางข้อมูลพื้นฐาน =====================
        st.divider()
        st.subheader("📋 ข้อมูลพื้นฐาน (Fundamental Data)")
        
        stock = yf.Ticker(ticker)
        info = stock.info
        
        fundamentals = {
            "ราคาปัจจุบัน": f"{info.get('currentPrice', info.get('regularMarketPrice', 'N/A')):.2f}",
            "มูลค่าตลาด (Market Cap)": f"{info.get('marketCap', 0)/1e9:.2f} พันล้าน",
            "P/E Ratio": f"{info.get('trailingPE', 'N/A'):.2f}" if info.get('trailingPE') else "N/A",
            "EPS": f"{info.get('trailingEps', 'N/A'):.2f}",
            "Dividend Yield": f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "N/A",
            "Volume": f"{info.get('volume', 0):,}",
            "52 สัปดาห์สูงสุด": f"{info.get('fiftyTwoWeekHigh', 'N/A'):.2f}",
            "52 สัปดาห์ต่ำสุด": f"{info.get('fiftyTwoWeekLow', 'N/A'):.2f}",
            "Beta": f"{info.get('beta', 'N/A'):.2f}",
            "Sector": info.get('sector', 'N/A'),
            "Industry": info.get('industry', 'N/A')
        }
        
        df_fund = pd.DataFrame.from_dict(fundamentals, orient='index', columns=['ค่า'])
        st.dataframe(df_fund, use_container_width=True, height=400)

# ===================== PAGE 2: เปรียบเทียบหลายหุ้น =====================
# ===================== PAGE 2: เปรียบเทียบหลายหุ้น =====================
elif page == "🔄 เปรียบเทียบหลายหุ้น":
    st.title("🔄 เปรียบเทียบหลายหุ้น")
    
    tickers_input = st.text_input("กรอกสัญลักษณ์หุ้น (คั่นด้วย comma)", 
                                 value="AAPL, TSLA, NVDA, PTT.BK").strip().upper()
    tickers = [t.strip() for t in tickers_input.split(",") if t.strip()]
    
    period_options = ["1 เดือน", "3 เดือน", "6 เดือน", "1 ปี", "2 ปี"]
    selected_period = st.selectbox("เลือกช่วงเวลา", period_options, index=3)
    period_map = {"1 เดือน": "1mo", "3 เดือน": "3mo", "6 เดือน": "6mo", "1 ปี": "1y", "2 ปี": "2y"}

    if st.button("🔍 เปรียบเทียบ", type="primary"):
        if len(tickers) < 2:
            st.warning("กรุณากรอกหุ้นอย่างน้อย 2 ตัว")
            st.stop()
            
        with st.spinner("กำลังดึงข้อมูลหุ้น..."):
            closes = {}
            for t in tickers:
                try:
                    df = yf.download(t, period=period_map[selected_period], 
                                   interval="1d", progress=False, auto_adjust=True)
                    if not df.empty:
                        closes[t] = df['Close']
                except Exception as e:
                    st.warning(f"ไม่สามารถดึงข้อมูล {t} ได้")

            if len(closes) == 0:
                st.error("ไม่พบข้อมูลหุ้นใดเลย กรุณาลองใหม่อีกครั้ง")
                st.stop()

            # ===================== สร้าง DataFrame อย่างปลอดภัย =====================
            df_compare = pd.concat(closes, axis=1)  # วิธีที่ดีที่สุด
            df_compare = df_compare.dropna(how='all')  # ลบแถวที่ว่างทั้งหมด

            st.success(f"เปรียบเทียบสำเร็จ: {len(closes)} หุ้น")

            # กราฟ Normalized (เริ่มต้นที่ 100)
            st.subheader("📈 กราฟเปรียบเทียบราคา (Normalized)")
            df_norm = df_compare / df_compare.iloc[0] * 100
            
            fig = go.Figure()
            for col in df_norm.columns:
                fig.add_trace(go.Scatter(x=df_norm.index, y=df_norm[col], name=col, mode='lines'))
            
            fig.update_layout(
                height=600, 
                template="plotly_white", 
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig, use_container_width=True)

            # ตารางราคาปิดล่าสุด
            st.subheader("📊 ราคาปิดล่าสุดและการเปลี่ยนแปลง")
            latest = df_compare.iloc[-1]
            change = df_compare.pct_change().iloc[-1] * 100
            
            summary = pd.DataFrame({
                "ราคาล่าสุด": latest,
                "เปลี่ยนแปลง (%)": change.round(2)
            })
            st.dataframe(summary.style.format({"ราคาล่าสุด": "{:.2f}", "เปลี่ยนแปลง (%)": "{:+.2f}"}), 
                        use_container_width=True)

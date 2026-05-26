import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Stock Dashboard", layout="wide", page_icon="ðŸ“ˆ")

st.title("ðŸ“Š à¸£à¸°à¸šà¸šà¸§à¸´à¹€à¸„à¸£à¸²à¸°à¸«à¹Œà¸«à¸¸à¹‰à¸™à¸ªà¹ˆà¸§à¸™à¸•à¸±à¸§ (à¸‰à¸šà¸±à¸šà¸ªà¸¡à¸šà¸¹à¸£à¸“à¹Œ)")

# ===================== SIDEBAR =====================
st.sidebar.header("âš™ï¸ à¸à¸²à¸£à¸•à¸±à¹‰à¸‡à¸„à¹ˆà¸²")
ticker = st.sidebar.text_input("à¸à¸£à¸­à¸à¸ªà¸±à¸à¸¥à¸±à¸à¸©à¸“à¹Œà¸«à¸¸à¹‰à¸™:", value="AAPL").strip().upper()

# à¹€à¸žà¸´à¹ˆà¸¡à¸„à¸³à¹à¸™à¸°à¸™à¸³à¸«à¸¸à¹‰à¸™à¹„à¸—à¸¢
if ticker and not ticker.endswith('.BK') and len(ticker) < 5:
    st.sidebar.info(f"ðŸ’¡ à¸—à¸£à¸´à¸„: à¸«à¸¸à¹‰à¸™à¹„à¸—à¸¢à¸•à¹‰à¸­à¸‡à¹€à¸•à¸´à¸¡ .BK (à¹€à¸Šà¹ˆà¸™ {ticker}.BK)")

period_options = ["1 à¹€à¸”à¸·à¸­à¸™", "3 à¹€à¸”à¸·à¸­à¸™", "6 à¹€à¸”à¸·à¸­à¸™", "1 à¸›à¸µ", "2 à¸›à¸µ", "5 à¸›à¸µ"]
selected_period = st.sidebar.selectbox("à¹€à¸¥à¸·à¸­à¸à¸Šà¹ˆà¸§à¸‡à¹€à¸§à¸¥à¸²", period_options, index=3)

period_map = {
    "1 à¹€à¸”à¸·à¸­à¸™": "1mo", "3 à¹€à¸”à¸·à¸­à¸™": "3mo", "6 à¹€à¸”à¸·à¸­à¸™": "6mo",
    "1 à¸›à¸µ": "1y", "2 à¸›à¸µ": "2y", "5 à¸›à¸µ": "5y"
}

@st.cache_data(ttl=1800)
def get_stock_data(ticker, period):
    try:
        df = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False)
        if df.empty or len(df) < 20: return None
        if isinstance(df.columns, pd.MultiIndex): df = df.droplevel(1, axis=1)
        
        df = df.round(4)
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        df['BB_std'] = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
        df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)
        
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, min_periods=14).mean()
        avg_loss = loss.ewm(com=13, min_periods=14).mean()
        df['RSI'] = 100 - (100 / (1 + avg_gain / avg_loss))
        
        exp12 = df['Close'].ewm(span=12, adjust=False).mean()
        exp26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp12 - exp26
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal']
        
        return df
    except Exception as e:
        st.error(f"à¹€à¸à¸´à¸”à¸‚à¹‰à¸­à¸œà¸´à¸”à¸žà¸¥à¸²à¸”: {str(e)}")
        return None

# ===================== MAIN =====================
if ticker:
    df = get_stock_data(ticker, period_map[selected_period])
    if df is None:
        st.error(f"âŒ à¹„à¸¡à¹ˆà¸žà¸šà¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¸«à¸¸à¹‰à¸™ `{ticker}`")
        st.stop()

    st.success(f"âœ… à¸à¸³à¸¥à¸±à¸‡à¸§à¸´à¹€à¸„à¸£à¸²à¸°à¸«à¹Œ: **{ticker}** | à¸Šà¹ˆà¸§à¸‡à¹€à¸§à¸¥à¸²: {selected_period}")

    # 1. à¸à¸£à¸²à¸Ÿà¸£à¸²à¸„à¸²à¸«à¸¥à¸±à¸
    st.subheader(f"ðŸ“ˆ à¸à¸£à¸²à¸Ÿà¸£à¸²à¸„à¸² {ticker}")
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=df.index, y=df['Close'], name='à¸£à¸²à¸„à¸²à¸›à¸´à¸”', line=dict(color='#008080', width=2.5)))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name='EMA50', line=dict(color='purple', width=1.5)))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['EMA200'], name='EMA200', line=dict(color='orange', width=2, dash='dot')))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_upper'], name='BB Upper', line=dict(color='rgba(255,0,0,0.3)', dash='dash')))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['BB_lower'], name='BB Lower', line=dict(color='rgba(0,0,255,0.3)', dash='dash'), fill='tonexty', fillcolor='rgba(0,100,255,0.05)'))
    
    fig_price.update_layout(height=600, template="plotly_white", hovermode="x unified", legend=dict(orientation="h", x=0, y=1.05))
    fig_price.update_xaxes(showspikes=True, spikecolor="gray", spikemode="across", spikesnap="cursor")
    fig_price.update_yaxes(showspikes=True, spikecolor="gray", spikemode="across")
    st.plotly_chart(fig_price, use_container_width=True)

    # 2. Volume
    st.subheader("ðŸ“Š à¸›à¸£à¸´à¸¡à¸²à¸“à¸à¸²à¸£à¸‹à¸·à¹‰à¸­à¸‚à¸²à¸¢ (Volume)")
    fig_vol = go.Figure(go.Bar(x=df.index, y=df['Volume'], marker_color='#1E90FF'))
    fig_vol.update_layout(height=300, template="plotly_white", hovermode="x unified")
    st.plotly_chart(fig_vol, use_container_width=True)

    # 3. RSI
    st.subheader("ðŸ“ˆ RSI (14)")
    fig_rsi = go.Figure()
    fig_rsi.add_hrect(70, 100, fillcolor="red", opacity=0.1); fig_rsi.add_hrect(30, 70, fillcolor="lightblue", opacity=0.1); fig_rsi.add_hrect(0, 30, fillcolor="green", opacity=0.1)
    fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='#FF4500', width=2)))
    fig_rsi.update_layout(height=350, template="plotly_white", hovermode="x unified", yaxis=dict(range=[0, 100]))
    st.plotly_chart(fig_rsi, use_container_width=True)

    # 4. MACD
    st.subheader("ðŸ“ˆ MACD")
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue')))
    fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal', line=dict(color='orange')))
    fig_macd.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='Histogram', marker_color=['green' if x >= 0 else 'red' for x in df['MACD_Hist']]))
    fig_macd.update_layout(height=350, template="plotly_white", hovermode="x unified")
    st.plotly_chart(fig_macd, use_container_width=True)

    # 5. à¸ªà¸£à¸¸à¸›à¸ªà¸–à¸²à¸™à¸° (à¹„à¸§à¹‰à¸—à¹‰à¸²à¸¢à¸ªà¸¸à¸”)
    st.divider()
    latest = df.iloc[-1]
    change = ((latest['Close'] - df.iloc[-2]['Close']) / df.iloc[-2]['Close']) * 100
    is_bullish = latest['Close'] > latest['EMA200']

    st.subheader(f"ðŸ“Œ à¸ªà¸£à¸¸à¸›à¸ªà¸²à¹€à¸«à¸•à¸¸à¹à¸¥à¸°à¸ªà¸–à¸²à¸™à¸°à¸¥à¹ˆà¸²à¸ªà¸¸à¸”: {ticker}")
    c1, c2, c3 = st.columns(3)
    c1.metric("à¸£à¸²à¸„à¸²à¸¥à¹ˆà¸²à¸ªà¸¸à¸”", f"{latest['Close']:.2f}", f"{change:+.2f}%")
    c2.metric("RSI", f"{latest['RSI']:.1f}")
    c3.metric("à¹à¸™à¸§à¹‚à¸™à¹‰à¸¡à¸«à¸¥à¸±à¸", "à¸‚à¸²à¸‚à¸¶à¹‰à¸™" if is_bullish else "à¸‚à¸²à¸¥à¸‡")

    if latest['RSI'] > 70:
        st.warning("**à¸ªà¸–à¸²à¸™à¸°: Overbought** - à¸£à¸²à¸„à¸²à¸‚à¸¶à¹‰à¸™à¸¡à¸²à¸ªà¸¹à¸‡à¸¡à¸²à¸à¹ƒà¸™à¸£à¸°à¸¢à¸°à¸ªà¸±à¹‰à¸™ à¸£à¸°à¸§à¸±à¸‡à¸à¸²à¸£à¸›à¸£à¸±à¸šà¸à¸²à¸™à¸«à¸£à¸·à¸­à¸¢à¹ˆà¸­à¸•à¸±à¸§")
    elif latest['RSI'] < 30:
        if is_bullish: st.success("**à¸ªà¸–à¸²à¸™à¸°: Oversold à¹ƒà¸™à¹à¸™à¸§à¹‚à¸™à¹‰à¸¡à¸‚à¸²à¸‚à¸¶à¹‰à¸™** - à¹€à¸›à¹‡à¸™à¸ˆà¸±à¸‡à¸«à¸§à¸°à¸¢à¹ˆà¸­à¸•à¸±à¸§à¹ƒà¸™à¸‚à¸²à¸‚à¸¶à¹‰à¸™à¸—à¸µà¹ˆà¸™à¹ˆà¸²à¸ªà¸™à¹ƒà¸ˆ (Buy the dip)")
        else: st.error("**à¸ªà¸–à¸²à¸™à¸°: Oversold à¹ƒà¸™à¹à¸™à¸§à¹‚à¸™à¹‰à¸¡à¸‚à¸²à¸¥à¸‡** - à¸£à¸°à¸§à¸±à¸‡à¸à¸²à¸£à¸£à¸±à¸šà¸¡à¸µà¸” à¸«à¸¸à¹‰à¸™à¸­à¸²à¸ˆà¸¥à¸‡à¸•à¹ˆà¸­à¹„à¸”à¹‰à¸­à¸µà¸")
    else:
        st.info("à¸ªà¸–à¸²à¸™à¸°: à¸›à¸à¸•à¸´ - à¸£à¸²à¸„à¸²à¸¢à¸±à¸‡à¹à¸à¸§à¹ˆà¸‡à¸•à¸±à¸§à¹ƒà¸™à¸£à¸°à¸”à¸±à¸šà¸ªà¸¡à¸”à¸¸à¸¥")

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="AI Stock Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📊 AI Stock Dashboard")
st.caption("Advanced Trend • Momentum • Volume • Market Structure Engine")

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.header("⚙️ ตั้งค่าระบบ")

symbol = st.sidebar.text_input(
    "Ticker",
    value="AAPL"
).upper().strip()

period_map = {
    "1 เดือน": "1mo",
    "3 เดือน": "3mo",
    "6 เดือน": "6mo",
    "1 ปี": "1y",
    "2 ปี": "2y",
    "5 ปี": "5y"
}

selected_period = st.sidebar.selectbox(
    "ช่วงเวลา",
    list(period_map.keys()),
    index=3
)

interval = st.sidebar.selectbox(
    "Timeframe",
    ["1d", "1h"],
    index=0
)

show_bb = st.sidebar.checkbox("แสดง Bollinger Bands", value=True)
show_ema = st.sidebar.checkbox("แสดง EMA", value=True)
show_volume = st.sidebar.checkbox("แสดง Volume Spike", value=True)

# =====================================================
# DATA LOADER
# =====================================================
@st.cache_data(ttl=1800)
def load_data(symbol, period, interval):
    try:
        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False
        )

        if df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        # =====================================================
        # INDICATORS
        # =====================================================

        # EMA
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

        # RSI
        delta = df['Close'].diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()

        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()

        df['MACD'] = ema12 - ema26
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal']

        # Bollinger Bands
        df['BB_MID'] = df['Close'].rolling(20).mean()
        bb_std = df['Close'].rolling(20).std()

        df['BB_UPPER'] = df['BB_MID'] + (bb_std * 2)
        df['BB_LOWER'] = df['BB_MID'] - (bb_std * 2)

        # Volume
        df['VOL_MA20'] = df['Volume'].rolling(20).mean()
        df['HIGH_VOLUME'] = df['Volume'] > (df['VOL_MA20'] * 2)

        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)

        df['ATR'] = true_range.rolling(14).mean()
        df['ATR_PERCENT'] = (df['ATR'] / df['Close']) * 100

        # Support / Resistance
        df['SUPPORT'] = df['Low'].rolling(20).min()
        df['RESISTANCE'] = df['High'].rolling(20).max()

        # Trend Score
        trend_score = []

        for i in range(len(df)):
            score = 0

            if df['Close'].iloc[i] > df['EMA200'].iloc[i]:
                score += 1

            if df['EMA50'].iloc[i] > df['EMA200'].iloc[i]:
                score += 1

            if df['MACD'].iloc[i] > df['Signal'].iloc[i]:
                score += 1

            if df['RSI'].iloc[i] > 50:
                score += 1

            trend_score.append(score)

        df['TREND_SCORE'] = trend_score

        return df.round(4)

    except Exception as e:
        st.error(f"โหลดข้อมูลล้มเหลว: {e}")
        return None

# =====================================================
# LOAD DATA
# =====================================================
if symbol:

    df = load_data(
        symbol,
        period_map[selected_period],
        interval
    )

    if df is None or len(df) < 30:
        st.error("❌ ไม่พบข้อมูล หรือข้อมูลน้อยเกินไป")
        st.stop()

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # =====================================================
    # MARKET REGIME
    # =====================================================
    if latest['ATR_PERCENT'] > 5:
        regime = "🔥 High Volatility"
    elif latest['ATR_PERCENT'] < 2:
        regime = "🧊 Low Volatility"
    else:
        regime = "⚖️ Normal Volatility"

    # =====================================================
    # AI BIAS ENGINE
    # =====================================================
    score = latest['TREND_SCORE']

    if score >= 4:
        bias = "🟢 STRONG BULLISH"
        conviction = "HIGH"

    elif score == 3:
        bias = "🟡 BULLISH"
        conviction = "MEDIUM"

    elif score == 2:
        bias = "⚪ NEUTRAL"
        conviction = "LOW"

    else:
        bias = "🔴 BEARISH"
        conviction = "MEDIUM"

    # =====================================================
    # SIGNALS
    # =====================================================
    golden_cross = (
        df['EMA50'].iloc[-2] < df['EMA200'].iloc[-2]
        and
        df['EMA50'].iloc[-1] > df['EMA200'].iloc[-1]
    )

    macd_cross_up = (
        df['MACD'].iloc[-2] < df['Signal'].iloc[-2]
        and
        df['MACD'].iloc[-1] > df['Signal'].iloc[-1]
    )

    breakout = latest['Close'] > latest['RESISTANCE'] * 0.995

    # =====================================================
    # TOP METRICS
    # =====================================================
    st.subheader(f"📌 {symbol} วิเคราะห์ล่าสุด")

    c1, c2, c3, c4, c5 = st.columns(5)

    price_change = ((latest['Close'] - prev['Close']) / prev['Close']) * 100

    with c1:
        st.metric(
            "Price",
            f"{latest['Close']:.2f}",
            f"{price_change:+.2f}%"
        )

    with c2:
        st.metric(
            "RSI",
            f"{latest['RSI']:.1f}"
        )

    with c3:
        st.metric(
            "Trend Score",
            f"{int(score)}/4"
        )

    with c4:
        st.metric(
            "Market Regime",
            regime
        )

    with c5:
        st.metric(
            "Conviction",
            conviction
        )

    # =====================================================
    # AI SUMMARY
    # =====================================================
    st.divider()

    st.subheader("🧠 AI วิเคราะห์")

    if score >= 3:
        st.success(
            "Momentum ยังอยู่ฝั่ง Bullish | ราคาอยู่เหนือ EMA หลัก | "
            "Trend Structure ยังแข็งแรง"
        )
    elif score == 2:
        st.warning(
            "ตลาดอยู่ในช่วง Neutral | Momentum ยังไม่ชัดเจน"
        )
    else:
        st.error(
            "โครงสร้างราคาอ่อนแรง | Bearish Pressure ยังเด่น"
        )

    # =====================================================
    # SIGNAL BOXES
    # =====================================================
    signal_col1, signal_col2, signal_col3 = st.columns(3)

    with signal_col1:
        if golden_cross:
            st.success("✅ Golden Cross Detected")
        else:
            st.info("ไม่มี Golden Cross")

    with signal_col2:
        if macd_cross_up:
            st.success("✅ MACD Bullish Cross")
        else:
            st.info("MACD ยังไม่ Cross")

    with signal_col3:
        if breakout:
            st.success("🚀 Resistance Breakout")
        else:
            st.info("ยังไม่ Breakout")

    # =====================================================
    # MAIN CHART
    # =====================================================
    st.divider()

    st.subheader("📈 Price Action")

    fig = go.Figure()

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Candles'
        )
    )

    # EMA
    if show_ema:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['EMA20'],
                name='EMA20',
                line=dict(width=1.5)
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['EMA50'],
                name='EMA50',
                line=dict(width=2)
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['EMA200'],
                name='EMA200',
                line=dict(width=2.5)
            )
        )

    # Bollinger Bands
    if show_bb:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['BB_UPPER'],
                name='BB Upper',
                line=dict(dash='dash')
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['BB_LOWER'],
                name='BB Lower',
                line=dict(dash='dash'),
                fill='tonexty'
            )
        )

    # Support / Resistance
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['SUPPORT'],
            name='Support',
            line=dict(dash='dot')
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['RESISTANCE'],
            name='Resistance',
            line=dict(dash='dot')
        )
    )

    fig.update_layout(
        template='plotly_white',
        height=700,
        hovermode='x unified',
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # =====================================================
    # LOWER PANELS
    # =====================================================
    left, right = st.columns(2)

    with left:

        # Volume
        st.subheader("📊 Volume")

        volume_colors = [
            'red' if close < open_ else 'green'
            for close, open_ in zip(df['Close'], df['Open'])
        ]

        fig_vol = go.Figure()

        fig_vol.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                marker_color=volume_colors,
                name='Volume'
            )
        )

        fig_vol.add_trace(
            go.Scatter(
                x=df.index,
                y=df['VOL_MA20'],
                name='Vol MA20'
            )
        )

        if show_volume:
            spike_df = df[df['HIGH_VOLUME'] == True]

            fig_vol.add_trace(
                go.Scatter(
                    x=spike_df.index,
                    y=spike_df['Volume'],
                    mode='markers',
                    marker=dict(size=10),
                    name='Volume Spike'
                )
            )

        fig_vol.update_layout(
            template='plotly_white',
            height=300
        )

        st.plotly_chart(fig_vol, use_container_width=True)

        # MACD
        st.subheader("📈 MACD")

        hist_colors = []

        for i in range(len(df)):

            if i == 0:
                hist_colors.append('gray')
                continue

            current = df['MACD_Hist'].iloc[i]
            prev_hist = df['MACD_Hist'].iloc[i - 1]

            if current >= 0:
                if current > prev_hist:
                    hist_colors.append('darkgreen')
                else:
                    hist_colors.append('lightgreen')
            else:
                if current < prev_hist:
                    hist_colors.append('darkred')
                else:
                    hist_colors.append('salmon')

        fig_macd = go.Figure()

        fig_macd.add_trace(
            go.Bar(
                x=df.index,
                y=df['MACD_Hist'],
                marker_color=hist_colors,
                name='Histogram'
            )
        )

        fig_macd.add_trace(
            go.Scatter(
                x=df.index,
                y=df['MACD'],
                name='MACD'
            )
        )

        fig_macd.add_trace(
            go.Scatter(
                x=df.index,
                y=df['Signal'],
                name='Signal'
            )
        )

        fig_macd.update_layout(
            template='plotly_white',
            height=300
        )

        st.plotly_chart(fig_macd, use_container_width=True)

    with right:

        # RSI
        st.subheader("📈 RSI")

        fig_rsi = go.Figure()

        fig_rsi.add_hrect(
            y0=70,
            y1=100,
            opacity=0.1
        )

        fig_rsi.add_hrect(
            y0=0,
            y1=30,
            opacity=0.1
        )

        fig_rsi.add_trace(
            go.Scatter(
                x=df.index,
                y=df['RSI'],
                name='RSI',
                line=dict(width=2)
            )
        )

        fig_rsi.add_hline(y=70, line_dash='dash')
        fig_rsi.add_hline(y=30, line_dash='dash')
        fig_rsi.add_hline(y=50, line_dash='dot')

        fig_rsi.update_layout(
            template='plotly_white',
            height=620,
            yaxis=dict(range=[0, 100])
        )

        st.plotly_chart(fig_rsi, use_container_width=True)

    # =====================================================
    # WATCHLIST SCANNER
    # =====================================================
    st.divider()

    st.subheader("🚀 Quick Watchlist Scanner")

    watchlist = [
        'AAPL',
        'TSLA',
        'NVDA',
        'META',
        'AMZN',
        'GOOGL',
        'MSFT'
    ]

    scan_results = []

    for stock in watchlist:

        try:
            scan_df = yf.download(
                stock,
                period='6mo',
                interval='1d',
                auto_adjust=True,
                progress=False
            )

            if len(scan_df) < 50:
                continue

            if isinstance(scan_df.columns, pd.MultiIndex):
                scan_df.columns = scan_df.columns.droplevel(1)

            close = scan_df['Close']

            ema50 = close.ewm(span=50, adjust=False).mean()
            ema200 = close.ewm(span=200, adjust=False).mean()

            bullish = close.iloc[-1] > ema50.iloc[-1] > ema200.iloc[-1]

            scan_results.append({
                'Ticker': stock,
                'Price': round(close.iloc[-1], 2),
                'Bullish Structure': bullish
            })

        except:
            pass

    scan_df = pd.DataFrame(scan_results)

    st.dataframe(scan_df, use_container_width=True)

    st.caption(
        'ระบบนี้เป็น Educational Dashboard ไม่ใช่คำแนะนำการลงทุน'
    )

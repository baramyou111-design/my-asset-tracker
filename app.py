import streamlit as st
import yfinance as yf
import pandas as pd

# 1. ตั้งค่าหน้าจอ Mobile-First Layout
st.set_page_config(
    page_title="Pro Trading Terminal Ultimate",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. Custom CSS แต่ง UI ให้เป็น Fintech App โมเดิร์นล้ำๆ
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #0f0c1b 0%, #1a153b 100%);
        color: #f3f4f6;
    }
    .fintech-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 16px;
        border-radius: 16px;
        margin-bottom: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    .stButton>button {
        width: 100%;
        border-radius: 14px;
        font-weight: 600;
        height: 48px;
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
        color: white;
        font-size: 15px;
        border: none;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4);
    }
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Session State สำหรับจัดการหน้าจอและ Watchlist
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = None
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["AAPL", "NVDA", "PTT.BK", "BTC-USD"]
if 'nav_tab' not in st.session_state:
    st.session_state.nav_tab = "หน้าแรก"

# แผงตั้งค่าพับได้ (Settings)
with st.expander("⚙️ ตั้งค่าเงินทุนและรายชื่อสินทรัพย์ทั้งหมด", expanded=False):
    default_input = "PTT.BK, AOT.BK, CPALL.BK, AAPL, TSLA, NVDA, BTC-USD, ETH-USD, GC=F"
    ticker_input = st.text_area("รายชื่อสินทรัพย์ (คั่นด้วย ,):", default_input, height=80)
    total_capital_thb = st.number_input("เงินทุนรวมทั้งพอร์ต (บาท):", value=100000.0, step=10000.0, format="%.2f")

scan_button = st.button("🚀 สแกนตลาด & คำนวณพอร์ต")
st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 📱 1. หน้าจอหลัก (Home / Market Scan)
# ==========================================
if st.session_state.selected_stock is None:
    
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 10px;">
            <h2 style="margin: 0; font-size: 20px; color: #ffffff;">🔥 ตลาดหุ้น & พอร์ตจัดสรร</h2>
            <span style="font-size: 12px; color: #c084fc; background: rgba(168,85,247,0.2); padding: 4px 10px; border-radius: 12px;">แตะหุ้นเพื่อดูรายละเอียด</span>
        </div>
    """, unsafe_allow_html=True)

    if scan_button or 'df_cache' not in st.session_state:
        with st.spinner("⏳ กำลังวิเคราะห์ข้อมูลตลาด..."):
            try:
                fx_ticker = yf.Ticker("USDTHB=X")
                fx_hist = fx_ticker.history(period="1d")
                usd_thb_rate = float(fx_hist['Close'].iloc[-1]) if not fx_hist.empty else 35.0
            except Exception:
                usd_thb_rate = 35.0
                
            raw_results = []
            tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
            
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period="3mo")
                    if hist.empty or len(hist) < 20:
                        continue
                        
                    current_price = float(hist['Close'].iloc[-1])
                    prev_price = float(hist['Close'].iloc[-2])
                    pct_change = ((current_price - prev_price) / prev_price) * 100
                    
                    is_thai = ".BK" in ticker
                    currency = "฿" if is_thai else "$"
                    
                    hist['SMA20'] = hist['Close'].rolling(window=20).mean()
                    curr_sma = float(hist['SMA20'].iloc[-1])
                    
                    delta = hist['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    current_rsi = float(100 - (100 / (1 + rs)).iloc[-1])
                    
                    support_1 = max(curr_sma, current_price * 0.98)
                    support_2 = float(hist['Low'].rolling(window=20).min().iloc[-1])
                    resistance = float(hist['High'].rolling(window=20).max().iloc[-1])
                    
                    score = 3.0 if current_price > curr_sma and 45 <= current_rsi <= 65 else (1.5 if current_price > curr_sma else 0.0)
                    
                    raw_results.append({
                        "สัญลักษณ์": ticker,
                        "ราคาปัจจุบัน": f"{current_price:,.2f} {currency}",
                        "raw_price": current_price,
                        "currency": currency,
                        "เปลี่ยนแปลง (%)": f"{pct_change:+.2f}%",
                        "RSI": f"{current_rsi:.1f}",
                        "score": score,
                        "แนวรับ 1": support_1,
                        "แนวรับ 2": support_2,
                        "แนวต้าน": resistance
                    })
                except Exception:
                    pass
            st.session_state.df_cache = raw_results

    if 'df_cache' in st.session_state and st.session_state.df_cache:
        # คำนวณน้ำหนักพอร์ต
        total_score = sum([r["score"] for r in st.session_state.df_cache])
        
        for item in st.session_state.df_cache:
            weight_pct = (item["score"] / total_score * 100) if total_score > 0 else 0
            alloc_thb = total_capital_thb * (weight_pct / 100)
            
            col_info, col_btn = [st.container(), st.container()]
            with st.container():
                is_fav = item['สัญลักษณ์'] in st.session_state.watchlist
                fav_icon = "⭐" if is_fav else "☆"
                
                st.markdown(f"""
                    <div class="fintech-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: bold; font-size: 16px; color: #fff;">{item['สัญลักษณ์']}</span>
                            <span style="color: {'#22c55e' if '+' in item['เปลี่ยนแปลง (%)'] else '#ef4444'}; font-weight: bold;">{item['เปลี่ยนแปลง (%)']}</span>
                        </div>
                        <div style="font-size: 13px; color: #9ca3af; margin-top: 4px;">ราคา: {item['ราคาปัจจุบัน']} | น้ำหนักพอร์ต: <b style="color:#c084fc;">{weight_pct:.1f}%</b> ({alloc_thb:,.0f} ฿)</div>
                    </div>
                """, unsafe_allow_html=True)
                
                c_action1, c_action2 = st.columns(2)
                with c_action1:
                    if st.button("📈 เจาะลึกรายละเอียด", key=f"detail_{item['สัญลักษณ์']}"):
                        st.session_state.selected_stock = item['สัญลักษณ์']
                        st.rerun()
                with c_action2:
                    if st.button(f"{fav_icon} Watchlist", key=f"fav_{item['สัญลักษณ์']}"):
                        if is_fav:
                            st.session_state.watchlist.remove(item['สัญลักษณ์'])
                        else:
                            st.session_state.watchlist.append(item['สัญลักษณ์'])
                        st.rerun()

# ==========================================
# 📊 2. หน้าจอรายละเอียดหุ้นรายตัว (Stock Detail View)
# ==========================================
else:
    selected_ticker = st.session_state.selected_stock
    
    if st.button("◀️ กลับหน้าหลัก"):
        st.session_state.selected_stock = None
        st.rerun()
        
    stock_obj = yf.Ticker(selected_ticker)
    
    # Timeframe Selector (1M, 3M, 6M, 1Y)
    timeframe = st.radio("เลือกช่วงเวลากราฟ:", ["1M", "3M", "6M", "1Y"], horizontal=True, index=1)
    period_map = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y"}
    
    hist_data = stock_obj.history(period=period_map[timeframe])
    curr_p = float(hist_data['Close'].iloc[-1]) if not hist_data.empty else 0
    prev_p = float(hist_data['Close'].iloc[-2]) if len(hist_data) > 1 else curr_p
    pct_c = ((curr_p - prev_p) / prev_p) * 100 if prev_p > 0 else 0
    
    curr_sma = float(hist_data['Close'].rolling(window=20).mean().iloc[-1]) if len(hist_data) >= 20 else curr_p
    s1 = max(curr_sma, curr_p * 0.98)
    s2 = float(hist_data['Low'].rolling(window=20).min().iloc[-1]) if len(hist_data) >= 20 else curr_p * 0.9
    res = float(hist_data['High'].rolling(window=20).max().iloc[-1]) if len(hist_data) >= 20 else curr_p * 1.1
    
    # Header หุ้น
    st.markdown(f"""
        <div class="fintech-card">
            <h2 style="margin:0; color:#fff;">{selected_ticker}</h2>
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 10px;">
                <span style="font-size: 24px; font-weight: bold; color: #fff;">{curr_p:,.2f}</span>
                <span style="font-size: 15px; font-weight: bold; color: {'#22c55e' if pct_c >= 0 else '#ef4444'};">{pct_c:+.2f}%</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Tabs ย่อยในหน้า Detail
    tab_graf, tab_stats, tab_news = st.tabs(["📉 กราฟ & แนวรับ", "📊 Quick Stats", "📰 ข่าวล่าสุด"])
    
    with tab_graf:
        st.markdown(f"""
            <div class="fintech-card">
                <p style="color: #a855f7; font-weight: bold; margin-bottom: 5px;">📍 ระดับราคาสำคัญ (Technical Levels)</p>
                <p style="margin: 2px 0; color: #ef4444;">🛡️ <b>แนวรับ 2 (S2):</b> {s2:,.2f}</p>
                <p style="margin: 2px 0; color: #facc15;">🛡️ <b>แนวรับ 1 (S1):</b> {s1:,.2f}</p>
                <p style="margin: 2px 0; color: #22c55e;">🎯 <b>แนวต้าน (Resistance):</b> {res:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        if not hist_data.empty:
            st.line_chart(hist_data['Close'])
            
    with tab_stats:
        st.markdown("<b>📊 ข้อมูลสรุปการเงินด่วน (Quick Stats):</b>", unsafe_allow_html=True)
        try:
            info = stock_obj.info
            mcap = info.get('marketCap', 'N/A')
            mcap_str = f"{mcap:,}" if isinstance(mcap, int) else "N/A"
            pe = info.get('trailingPE', 'N/A')
            div = info.get('dividendYield', 0)
            div_str = f"{div * 100:.2f}%" if div else "N/A"
            
            st.markdown(f"""
                <div class="fintech-card">
                    <p>📌 <b>Market Cap:</b> {mcap_str}</p>
                    <p>📌 <b>P/E Ratio:</b> {pe}</p>
                    <p>📌 <b>Dividend Yield:</b> {div_str}</p>
                </div>
            """, unsafe_allow_html=True)
        except:
            st.info("ข้อมูล Quick Stats ไม่พร้อมใช้งาน")
            
    with tab_news:
        st.markdown("<b>📰 หัวข้อข่าวสารล่าสุด:</b>", unsafe_allow_html=True)
        try:
            news_items = stock_obj.news
            if news_items:
                for n in news_items[:3]:
                    st.markdown(f"- [{n.get('title', '')}]({n.get('link', '#')})")
            else:
                st.info("ไม่มีข่าวสารในช่วงนี้")
        except:
            st.info("ไม่สามารถดึงข้อมูลข่าวได้")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ระบบจำลอง Paper Trading / บันทึกซื้อขายจริง
    with st.form("paper_trading_form"):
        st.markdown("<b>📝 จำลองการบันทึกซื้อขาย (Paper Trading)</b>", unsafe_allow_html=True)
        sim_price = st.number_input("ราคาที่ต้องการจำลองซื้อ:", value=curr_p, format="%.2f")
        sim_shares = st.number_input("จำนวนหน่วย:", value=10.0, step=1.0)
        submit_sim = st.form_submit_button("💾 บันทึกแผนเข้าซื้อเข้าพอร์ตจำลอง")
        if submit_sim:
            st.success(f"บันทึกแผนซื้อ {selected_ticker} จำนวน {sim_shares} หน่วย ที่ราคา {sim_price:,.2f} เรียบร้อย!")

# ==========================================
# 🧭 เมนูด้านล่าง (Bottom Navigation Bar)
# ==========================================
st.markdown("""
    <style>
    .bottom-nav {
        position: fixed; bottom: 15px; left: 50%; transform: translateX(-50%);
        width: 90%; max-width: 400px; background: rgba(31, 41, 55, 0.9);
        backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1);
        display: flex; justify-content: space-around; padding: 10px 0;
        border-radius: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); z-index: 999;
    }
    .nav-item { color: #9ca3af; text-align: center; font-size: 11px; text-decoration: none; }
    </style>
    <div class="bottom-nav">
        <div class="nav-item">🏠 หน้าแรก</div>
        <div class="nav-item">⭐ Watchlist ({len(st.session_state.watchlist)})</div>
        <div class="nav-item">📊 วิเคราะห์</div>
        <div class="nav-item">👤 พอร์ตจำลอง</div>
    </div>
""", unsafe_allow_html=True)

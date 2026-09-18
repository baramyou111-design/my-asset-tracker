import streamlit as st
import yfinance as yf
import pandas as pd

# 1. ตั้งค่าหน้าจอ Mobile-First Layout
st.set_page_config(
    page_title="Pro Trading Terminal",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. Custom CSS แต่ง UI ให้เป็น Fintech App โมเดิร์น
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
        height: 50px;
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
        color: white;
        font-size: 16px;
        border: none;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4);
    }
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# State สำหรับควบคุมการเปิดหน้า Detail หุ้นรายตัว
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = None

# แผงตั้งค่าพับได้
with st.expander("⚙️ ตั้งค่าพอร์ต เงินทุน และสินทรัพย์", expanded=False):
    default_input = "PTT.BK, AOT.BK, AAPL, TSLA, NVDA, BTC-USD, GC=F"
    ticker_input = st.text_area("รายชื่อสินทรัพย์ (คั่นด้วย ,):", default_input, height=80)
    total_capital_thb = st.number_input("เงินทุนรวมทั้งพอร์ต (บาท):", value=100000.0, step=10000.0, format="%.2f")
    my_entry_asset = st.text_input("หุ้นที่ถืออยู่จริง (Tracker):", "AAPL")
    my_buy_price = st.number_input("ทุนจริง:", value=180.0, step=1.0)
    my_shares_held = st.number_input("จำนวนหน่วย:", value=10.0, step=1.0)

scan_button = st.button("🚀 สแกนตลาด & จัดสรรพอร์ต")
st.markdown("<br>", unsafe_allow_html=True)

# ถ้ายังไม่ได้เลือกหุ้น ให้แสดงหน้าจอหลัก (Home / Watchlist)
if st.session_state.selected_stock is None:
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 0 15px 0;">
            <h2 style="margin: 0; font-size: 22px; color: #ffffff;">📊 รายชื่อสินทรัพย์ในพอร์ต</h2>
            <span style="font-size: 12px; color: #c084fc; background: rgba(168,85,247,0.2); padding: 4px 10px; border-radius: 12px;">แตะชื่อหุ้นเพื่อดูรายละเอียด</span>
        </div>
    """, unsafe_allow_html=True)

    if scan_button or 'df_cache' not in st.session_state:
        with st.spinner("⏳ กำลังโหลดข้อมูลตลาด..."):
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
                    
                    raw_results.append({
                        "สัญลักษณ์": ticker,
                        "ราคาปัจจุบัน": f"{current_price:,.2f} {currency}",
                        "raw_price": current_price,
                        "currency": currency,
                        "เปลี่ยนแปลง (%)": f"{pct_change:+.2f}%",
                        "RSI": f"{current_rsi:.1f}",
                        "แนวรับ 1": f"{support_1:,.2f} {currency}",
                        "แนวรับ 2": f"{support_2:,.2f} {currency}",
                        "แนวต้าน": f"{resistance:,.2f} {currency}",
                        "History": hist['Close']
                    })
                except Exception:
                    pass
            st.session_state.df_cache = raw_results

    if 'df_cache' in st.session_state and st.session_state.df_cache:
        for item in st.session_state.df_cache:
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"""
                    <div class="fintech-card" style="margin-bottom: 8px; padding: 12px;">
                        <div style="font-weight: bold; font-size: 16px; color: #fff;">{item['สัญลักษณ์']}</div>
                        <div style="font-size: 14px; color: #9ca3af;">ราคา: {item['ราคาปัจจุบัน']} | เปลี่ยนแปลง: <span style="color: {'#22c55e' if '+' in item['เปลี่ยนแปลง (%)'] else '#ef4444'};">{item['เปลี่ยนแปลง (%)']}</span></div>
                    </div>
                """, unsafe_allow_html=True)
            with col_b:
                if st.button("📈 เจาะลึก", key=f"btn_{item['สัญลักษณ์']}"):
                    st.session_state.selected_stock = item['สัญลักษณ์']
                    st.rerun()

# หากเลือกหุ้นตัวใดตัวหนึ่งแล้ว ให้แสดงหน้าจอ Detail View (สไตล์ Rocket Tool)
else:
    selected_ticker = st.session_state.selected_stock
    
    if st.button("◀️ กลับหน้าหลัก"):
        st.session_state.selected_stock = None
        st.rerun()
        
    stock_obj = yf.Ticker(selected_ticker)
    hist_data = stock_obj.history(period="3mo")
    curr_p = float(hist_data['Close'].iloc[-1])
    prev_p = float(hist_data['Close'].iloc[-2])
    pct_c = ((curr_p - prev_p) / prev_p) * 100
    
    curr_sma = float(hist_data['Close'].rolling(window=20).mean().iloc[-1])
    s1 = max(curr_sma, curr_p * 0.98)
    s2 = float(hist_data['Low'].rolling(window=20).min().iloc[-1])
    res = float(hist_data['High'].rolling(window=20).max().iloc[-1])
    
    # Header หุ้นรายตัว
    st.markdown(f"""
        <div class="fintech-card">
            <h2 style="margin:0; color:#fff;">{selected_ticker}</h2>
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 10px;">
                <span style="font-size: 26px; font-weight: bold; color: #fff;">{curr_p:,.2f}</span>
                <span style="font-size: 16px; font-weight: bold; color: {'#22c55e' if pct_c >= 0 else '#ef4444'};">{pct_c:+.2f}%</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # แท็บจำลองข้อมูลด้านใน (กราฟ, สรุป, ข่าวล่าสุด)
    tab_graf, tab_news, tab_fin = st.tabs(["📉 กราฟเทคนิค & แนวรับ", "📰 ข่าวล่าสุด", "💰 ข้อมูลการเงิน"])
    
    with tab_graf:
        st.markdown(f"""
            <div class="fintech-card">
                <p style="color: #a855f7; font-weight: bold; margin-bottom: 5px;">📍 ระดับราคาสำคัญ (Technical Levels)</p>
                <p style="margin: 2px 0; color: #ef4444;">🛡️ <b>แนวรับ 2:</b> ${s2:,.2f}</p>
                <p style="margin: 2px 0; color: #facc15;">🛡️ <b>แนวรับ 1:</b> ${s1:,.2f}</p>
                <p style="margin: 2px 0; color: #22c55e;">🎯 <b>แนวต้าน:</b> ${res:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        st.line_chart(hist_data['Close'])
        
    with tab_news:
        st.markdown("<b>📰 ข่าวสารล่าสุดจากตลาด:</b>", unsafe_allow_html=True)
        try:
            news_items = stock_obj.news
            if news_items:
                for n in news_items[:3]:
                    st.markdown(f"- [{n.get('title', '')}]({n.get('link', '#')})")
            else:
                st.info("ไม่มีข่าวสารในช่วงนี้")
        except:
            st.info("ไม่สามารถดึงข้อมูลข่าวได้ในขณะนี้")
            
    with tab_fin:
        st.markdown("<b>📊 ข้อมูลสรุปงบการเงินเบื้องต้น:</b>", unsafe_allow_html=True)
        try:
            info = stock_obj.info
            st.write(f"- **Market Cap:** {info.get('marketCap', 'N/A'):,}" if isinstance(info.get('marketCap'), int) else "- **Market Cap:** N/A")
            st.write(f"- **P/E Ratio:** {info.get('trailingPE', 'N/A')}")
            st.write(f"- **Dividend Yield:** {info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else "- **Dividend Yield:** N/A")
        except:
            st.info("ข้อมูลการเงินไม่พร้อมใช้งาน")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🛠️ เครื่องมือคำนวณแผนซื้อ-ขาย"):
        st.success(f"ระบบเปิดเครื่องมือคำนวณสำหรับ {selected_ticker} เรียบร้อย! สามารถนำเงินทุนไปจัดสรรตามแนวรับที่คำนวณไว้ได้เลยครับ")

# เมนูด้านล่าง (Bottom Navigation Bar)
st.markdown("""
    <style>
    .bottom-nav {
        position: fixed; bottom: 15px; left: 50%; transform: translateX(-50%);
        width: 90%; max-width: 400px; background: rgba(31, 41, 55, 0.85);
        backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1);
        display: flex; justify-content: space-around; padding: 10px 0;
        border-radius: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); z-index: 999;
    }
    .nav-item { color: #9ca3af; text-align: center; font-size: 11px; text-decoration: none; }
    .nav-item.active { color: #a855f7; font-weight: bold; }
    </style>
    <div class="bottom-nav">
        <div class="nav-item active">🏠 หน้าแรก</div>
        <div class="nav-item">⭐ วอทช์ลิสต์</div>
        <div class="nav-item">📊 วิเคราะห์</div>
        <div class="nav-item">👤 พอร์ตของฉัน</div>
    </div>
""", unsafe_allow_html=True)

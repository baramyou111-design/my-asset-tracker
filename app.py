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

# 2. Custom CSS แต่ง UI ให้ดู Modern โทนม่วงเข้ม/สว่าง สไตล์ Fintech App ล้ำๆ
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #0f0c1b 0%, #1a153b 100%);
        color: #f3f4f6;
    }
    
    /* การ์ดสไตล์มินิมอล โมเดิร์น */
    .fintech-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 16px;
        border-radius: 16px;
        margin-bottom: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* ปุ่มกดสไตล์แอปมือถือ */
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
        transition: 0.3s;
    }
    .stButton>button:hover {
        opacity: 0.9;
        transform: translateY(-2px);
    }

    /* ซ่อนเมนู Streamlit ด้านบน */
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. ส่วนหัวแอป (Header สไตล์ App)
st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0 20px 0;">
        <div>
            <span style="font-size: 13px; color: #a855f7; font-weight: 600;">⚡ SMART TERMINAL</span>
            <h2 style="margin: 0; font-size: 22px; color: #ffffff;">พอร์ต & ตลาดหุ้น</h2>
        </div>
        <div style="background: rgba(168, 85, 247, 0.2); padding: 6px 14px; border-radius: 20px; border: 1px solid rgba(168, 85, 247, 0.4);">
            <span style="font-size: 12px; color: #c084fc;">● Live Sync</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# 4. ฟีเจอร์จำลองโพลความเห็นตลาด (ตามภาพตัวอย่าง)
st.markdown("""
    <div class="fintech-card">
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <span style="background: #ef4444; color: white; font-size: 11px; padding: 2px 8px; border-radius: 6px; font-weight: bold; margin-right: 6px;">🔥 มาแรง</span>
            <span style="font-size: 15px; font-weight: bold; color: #fff;">ดอกเบี้ยจะขึ้นหรือไม่?</span>
        </div>
        <div style="font-size: 13px; color: #9ca3af; margin-bottom: 6px;">ขึ้น ↗ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>81%</b></div>
        <div style="background: #374151; border-radius: 10px; height: 8px; width: 100%; margin-bottom: 8px;">
            <div style="background: linear-gradient(90deg, #8b5cf6, #ec4899); width: 81%; height: 8px; border-radius: 10px;"></div>
        </div>
        <div style="font-size: 13px; color: #9ca3af; margin-bottom: 4px;">คงที่ ➔ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>19%</b></div>
    </div>
""", unsafe_allow_html=True)

# 5. แผงตั้งค่าพับได้ (Expander)
with st.expander("⚙️ ตั้งค่าพอร์ต เงินทุน และสินทรัพย์", expanded=False):
    default_input = "PTT.BK, AOT.BK, AAPL, TSLA, BTC-USD, GC=F"
    ticker_input = st.text_area("รายชื่อสินทรัพย์ (คั่นด้วย ,):", default_input, height=80)
    total_capital_thb = st.number_input("เงินทุนรวมทั้งพอร์ต (บาท):", value=100000.0, step=10000.0, format="%.2f")
    my_entry_asset = st.text_input("หุ้นที่ถืออยู่จริง (Tracker):", "AAPL")
    my_buy_price = st.number_input("ทุนจริง:", value=180.0, step=1.0)
    my_shares_held = st.number_input("จำนวนหน่วย:", value=10.0, step=1.0)

scan_button = st.button("🚀 สแกนตลาด & จัดสรรพอร์ต")

st.markdown("<br>", unsafe_allow_html=True)

# 6. ส่วนการประมวลผลและการแสดงผล
if scan_button:
    with st.spinner("⏳ กำลังประมวลผลระบบ AI..."):
        try:
            fx_ticker = yf.Ticker("USDTHB=X")
            fx_hist = fx_ticker.history(period="1d")
            usd_thb_rate = float(fx_hist['Close'].iloc[-1]) if not fx_hist.empty else 35.0
        except Exception:
            usd_thb_rate = 35.0
            
        raw_results = []
        normalized_history_dict = {}
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
                
                norm_series = (hist['Close'] / hist['Close'].iloc[0]) * 100
                normalized_history_dict[ticker] = norm_series
                
                news_list = []
                try:
                    raw_news = stock.news
                    if raw_news:
                        for n in raw_news[:2]:
                            title = n.get('title', '')
                            link = n.get('link', '#')
                            if title:
                                news_list.append(f"• [{title}]({link})")
                except Exception:
                    pass
                news_text = "<br>".join(news_list) if news_list else "ไม่มีข่าวล่าสุด"
                
                is_thai = ".BK" in ticker
                currency = "฿" if is_thai else "$"
                asset_type = "หุ้นไทย 🇹🇭" if is_thai else ("คริปโต 🪙" if "-USD" in ticker else ("ทอง/คอมโม 🥇" if "=F" in ticker else "หุ้นนอก 🌎"))
                
                hist['SMA20'] = hist['Close'].rolling(window=20).mean()
                curr_sma = float(hist['SMA20'].iloc[-1])
                prev_sma = float(hist['SMA20'].iloc[-2])
                
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                hist['RSI'] = 100 - (100 / (1 + rs))
                current_rsi = float(hist['RSI'].iloc[-1])
                
                exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
                exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
                hist['MACD'] = exp1 - exp2
                hist['MACD_Signal'] = hist['MACD'].ewm(span=9, adjust=False).mean()
                current_macd = float(hist['MACD'].iloc[-1])
                current_signal = float(hist['MACD_Signal'].iloc[-1])
                
                support_1 = max(curr_sma, current_price * 0.98)
                support_2 = float(hist['Low'].rolling(window=20).min().iloc[-1])
                resistance = float(hist['High'].rolling(window=20).max().iloc[-1])
                
                target_buy_price = min(current_price, support_1)
                stop_loss = support_2 * 0.98
                take_profit_1 = resistance
                
                score = 0.0
                if current_price > curr_sma and current_macd > current_signal:
                    if 45 <= current_rsi <= 65:
                        signal = "🟢 Strong Buy"
                        score = 3.0
                    else:
                        signal = "🟡 Uptrend"
                        score = 1.5
                elif current_price <= curr_sma and current_rsi < 40:
                    signal = "🟡 Oversold (รอรับ)"
                    score = 1.0
                else:
                    signal = "🔴 หลีกเลี่ยง"
                    score = 0.0
                
                if score > 0:
                    risk = target_buy_price - stop_loss
                    reward = take_profit_1 - target_buy_price
                    rr_ratio = (reward / risk) if risk > 0 else 0.0
                    rr_grade = f"1:{rr_ratio:.1f} (คุ้มค่า)"
                else:
                    rr_grade = "⚠️ รอยืนยัน"
                
                raw_results.append({
                    "สัญลักษณ์": ticker,
                    "ประเภท": asset_type,
                    "ราคาปัจจุบัน": f"{current_price:,.2f} {currency}",
                    "is_thai": is_thai,
                    "currency": currency,
                    "เปลี่ยนแปลง (%)": f"{pct_change:+.2f}%",
                    "แนวรับ 1": f"{support_1:,.2f} {currency}",
                    "แนวต้าน": f"{resistance:,.2f} {currency}",
                    "Risk/Reward": rr_grade,
                    "score": score,
                    "สถานะ": signal,
                    "News": news_text,
                    "History": hist[['Close', 'SMA20']]
                })
            except Exception:
                pass
        
        if raw_results:
            total_score = sum([r["score"] for r in raw_results])
            results = []
            total_allocated_thb = 0.0
            
            for r in raw_results:
                if total_score > 0 and r["score"] > 0:
                    weight_pct = (r["score"] / total_score) * 100
                    allocated_budget_thb = total_capital_thb * (weight_pct / 100)
                else:
                    weight_pct = 0.0
                    allocated_budget_thb = 0.0
                
                total_allocated_thb += allocated_budget_thb
                
                s1_val = float(r["แนวรับ 1"].replace('$', '').replace('฿', '').replace(',', '').strip())
                target_buy_thb = s1_val * (1 if r["is_thai"] else usd_thb_rate)
                
                if allocated_budget_thb > 0 and target_buy_thb > 0:
                    raw_shares = allocated_budget_thb / target_buy_thb
                    suggested_shares = int(raw_shares) if r["is_thai"] else round(raw_shares, 4)
                else:
                    suggested_shares = 0
                
                results.append({
                    "สัญลักษณ์": r["สัญลักษณ์"],
                    "ประเภท": r["ประเภท"],
                    "ราคา": r["ราคาปัจจุบัน"],
                    "เปลี่ยน (%)": r["เปลี่ยนแปลง (%)"],
                    "น้ำหนัก (%)": f"{weight_pct:.1f}%",
                    "งบลงทุน": f"{allocated_budget_thb:,.0f} ฿",
                    "จำนวน": f"{suggested_shares:,.4f}" if not r["is_thai"] else f"{suggested_shares:,}",
                    "สถานะ": r["สถานะ"],
                    "History": r["History"]
                })
            
            df_results = pd.DataFrame(results)
            
            # แท็บเมนูสไตล์แอปมือถือ
            tab1, tab2 = st.tabs(["🔥 หุ้นน่าซื้อ (Top Picks)", "📊 ภาพรวมพอร์ต"])
            
            with tab1:
                invest_df = df_results[df_results['งบลงทุน'] != "0 ฿"]
                if not invest_df.empty:
                    for _, row in invest_df.iterrows():
                        st.markdown(f"""
                            <div class="fintech-card">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-weight: bold; font-size: 16px; color: #fff;">{row['สัญลักษณ์']}</span>
                                    <span style="background: rgba(34, 197, 94, 0.2); color: #4ade80; font-size: 12px; padding: 2px 8px; border-radius: 6px;">{row['สถานะ']}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 14px; color: #9ca3af; margin-bottom: 4px;">
                                    <span>ราคา: <b style="color:#fff;">{row['ราคา']}</b></span>
                                    <span>เปลี่ยน: <b style="color:#22c55e;">{row['เปลี่ยน (%)']}</b></span>
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 14px; color: #9ca3af;">
                                    <span>งบจัดสรร: <b style="color:#c084fc;">{row['งบลงทุน']}</b></span>
                                    <span>สัดส่วน: <b style="color:#fff;">{row['น้ำหนัก (%)']}</b></span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("💡 วันนี้ไม่มีสินทรัพย์เข้าเกณฑ์ ถือเงินสดปลอดภัยที่สุด")
            
            with tab2:
                st.dataframe(df_results.drop(columns=['History']), use_container_width=True, hide_index=True)
        else:
            st.error("❌ ไม่พบข้อมูลสินทรัพย์")
else:
    st.info("👆 กดปุ่ม **'🚀 สแกนตลาด & จัดสรรพอร์ต'** ด้านบนเพื่อเริ่มต้นใช้งานแอปพลิเคชัน")

# 7. เมนูด้านล่างแบบลอยตัว (Bottom Navigation Bar สไตล์แอปมือถือ)
st.markdown("""
    <style>
    .bottom-nav {
        position: fixed;
        bottom: 15px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 400px;
        background: rgba(31, 41, 55, 0.85);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        justify-content: space-around;
        padding: 10px 0;
        border-radius: 30px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        z-index: 999;
    }
    .nav-item {
        color: #9ca3af;
        text-align: center;
        font-size: 11px;
        text-decoration: none;
    }
    .nav-item.active {
        color: #a855f7;
        font-weight: bold;
    }
    </style>
    <div class="bottom-nav">
        <div class="nav-item active">🏠 หน้าแรก</div>
        <div class="nav-item">⭐ วอทช์ลิสต์</div>
        <div class="nav-item">📊 วิเคราะห์</div>
        <div class="nav-item">👤 พอร์ตของฉัน</div>
    </div>
""", unsafe_allow_html=True)

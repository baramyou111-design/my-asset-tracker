import streamlit as st
import yfinance as yf
import pandas as pd

# 1. ตั้งค่าหน้าจอแบบ Mobile-Friendly
st.set_page_config(
    page_title="Pro Trading Terminal",
    page_icon="📱",
    layout="centered", # เปลี่ยนเป็น centered เพื่อให้ดูเหมือนกรอบแอปมือถือ/แท็บเล็ต
    initial_sidebar_state="collapsed" # พับ Sidebar ไว้โดยอัตโนมัติเพื่อให้เหมือนแอปจริง
)

# Custom CSS เพื่อปรับแต่ง UI ให้เป็นสไตล์ Mobile App (ปุ่มมนใหญ่, ฟอนต์สะอาด, ระยะห่างพอดีนิ้วสัมผัส)
st.markdown("""
    <style>
    .main { background-color: #0b0f19; color: #f3f4f6; }
    
    /* ปรับแต่งปุ่มให้ใหญ่และกดง่ายสไตล์แอปมือถือ */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        font-weight: 600;
        height: 48px;
        background-color: #2563eb;
        color: white;
        font-size: 16px;
        border: none;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
    }

    /* ปรับแต่งกล่อง Metric ให้โค้งมนสวยงามเหมือน Widget มือถือ */
    [data-testid="stMetric"] {
        background-color: #1f2937;
        padding: 14px;
        border-radius: 14px;
        border: 1px solid #374151;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }

    /* ซ่อน Streamlit Menu ด้านบนและ Footer เพื่อความเหมือนแอปแท้ */
#     #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ส่วนหัวแอปสไตล์ Mobile App Header
st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0;">
        <h2 style="margin: 0; font-size: 22px;">📱 Pro Trading App</h2>
        <span style="font-size: 14px; color: #22c55e; background: #064e3b; padding: 4px 10px; border-radius: 20px;">● Live Online</span>
    </div>
""", unsafe_allow_html=True)

# 2. แผงตั้งค่า (ซ่อนอยู่ใน Expandable Menu เพื่อความสะอาดตาแบบแอป)
with st.expander("⚙️ ตั้งค่าพอร์ต เงินทุน และสินทรัพย์", expanded=True):
    default_input = "PTT.BK, AOT.BK, AAPL, TSLA, BTC-USD, GC=F"
    ticker_input = st.text_area(
        "รายชื่อสินทรัพย์ (คั่นด้วย ,):",
        default_input,
        height=80
    )
    total_capital_thb = st.number_input("เงินทุนรวมทั้งพอร์ต (บาท):", value=100000.0, step=10000.0, format="%.2f")
    my_entry_asset = st.text_input("หุ้นที่ถืออยู่จริง (Tracker):", "AAPL")
    my_buy_price = st.number_input("ทุนจริง:", value=180.0, step=1.0)
    my_shares_held = st.number_input("จำนวนหน่วย:", value=10.0, step=1.0)

scan_button = st.button("🚀 สแกนตลาด & จัดพอร์ต")

st.markdown("---")

# 3. ส่วนการประมวลผล
if scan_button:
    with st.spinner("⏳ กำลังโหลดข้อมูล..."):
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
            
            # แสดงผลแบบ Tab ย่อยสไตล์แอปมือถือ
            tab1, tab2 = st.tabs(["🔥 หุ้นน่าซื้อ", "📊 พอร์ตทั้งหมด"])
            
            with tab1:
                invest_df = df_results[df_results['งบลงทุน'] != "0 ฿"]
                if not invest_df.empty:
                    for _, row in invest_df.iterrows():
                        with st.container():
                            st.markdown(f"### 📌 {row['สัญลักษณ์']} <span style='font-size:14px; color:#22c55e;'>{row['สถานะ']}</span>", unsafe_allow_html=True)
                            c1, c2 = st.columns(2)
                            c1.metric("ราคาปัจจุบัน", row['ราคา'], row['เปลี่ยน (%)'])
                            c2.metric("งบจัดสรร (บาท)", row['งบลงทุน'], f"สัดส่วน {row['น้ำหนัก (%)']}")
                            st.markdown("---")
                else:
                    st.info("💡 วันนี้ไม่มีสินทรัพย์เข้าเกณฑ์ ถือเงินสดปลอดภัยที่สุด")
            
            with tab2:
                st.dataframe(df_results.drop(columns=['History']), use_container_width=True, hide_index=True)
        else:
            st.error("❌ ไม่พบข้อมูลสินทรัพย์")
else:
    st.info("👆 กดปุ่ม **'🚀 สแกนตลาด & จัดพอร์ต'** เพื่อเริ่มใช้งานระบบได้ทันทีครับ")

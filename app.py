import streamlit as st
import yfinance as yf
import pandas as pd

# 1. ตั้งค่าหน้าจอ Dashboard (ให้สอดคล้องกับการเลือก Theme)
st.set_page_config(
    page_title="Ultimate Pro Trading Terminal",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. แผงควบคุมด้านข้าง (Sidebar) สำหรับตั้งค่าและเลือก Theme
with st.sidebar:
    st.header("⚙️ ตั้งค่าระบบ & ธีม")
    
    # ฟีเจอร์เลือก Theme สี
    theme_mode = st.radio("🎨 เลือกธีมการแสดงผล:", ["Dark Mode 🌙", "Light Mode ☀️"], index=0)
    
    default_input = "PTT.BK, AOT.BK, CPALL.BK, AAPL, TSLA, NVDA, BTC-USD, ETH-USD, GC=F, SI=F, CL=F"
    ticker_input = st.text_area(
        "รายชื่อสินทรัพย์ (คั่นด้วย ,):",
        default_input,
        height=110
    )
    
    st.markdown("---")
    st.subheader("💰 จัดการเงินทุนรวมพอร์ต")
    total_capital_thb = st.number_input("เงินทุนรวมทั้งพอร์ต (บาท):", value=100000.0, step=10000.0, format="%.2f")
    
    st.markdown("---")
    st.subheader("🪙 บันทึกพอร์ตที่ซื้อจริง (Virtual Tracker)")
    my_entry_asset = st.text_input("ชื่อหุ้นที่ถืออยู่ (เช่น AAPL หรือ PTT.BK):", "AAPL")
    my_buy_price = st.number_input("ราคาที่คุณซื้อมา (ทุนจริง):", value=180.0, step=1.0)
    my_shares_held = st.number_input("จำนวนหน่วยที่ถืออยู่:", value=10.0, step=1.0)

    st.markdown("<br>", unsafe_allow_html=True)
    scan_button = st.button("🔍 วิเคราะห์พอร์ตและสแกนตลาด", type="primary")

# กำหนด CSS ตามธีมที่ผู้ใช้เลือก
if "Dark" in theme_mode:
    bg_color = "#0e1117"
    text_color = "#ffffff"
    card_bg = "#1f2937"
    st.markdown(f"""
        <style>
        .main {{ background-color: {bg_color}; color: {text_color}; }}
        .stButton>button {{
            width: 100%; border-radius: 8px; font-weight: 600;
            background-color: #2563eb; color: white;
        }}
        .stButton>button:hover {{ background-color: #1d4ed8; }}
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .main { background-color: #f8fafc; }
        .stButton>button {
            width: 100%; border-radius: 8px; font-weight: 600;
            background-color: #2563eb; color: white;
        }
        .stButton>button:hover { background-color: #1d4ed8; }
        </style>
    """, unsafe_allow_html=True)

st.title("🚀 Ultimate Pro Trading Terminal")
st.markdown("ระบบวิเคราะห์ความเสี่ยง จัดพอร์ตตามความน่าจะเป็น ดึงข่าว Yahoo News เปรียบเทียบผลตอบแทน และคำนวณ Risk/Reward Ratio")

tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

# 3. ส่วนการประมวลผล
if scan_button:
    with st.spinner("⏳ กำลังดึงข้อมูลตลาดโลก คำนวณความเสี่ยง และเช็คพอร์ตจริง..."):
        try:
            fx_ticker = yf.Ticker("USDTHB=X")
            fx_hist = fx_ticker.history(period="1d")
            usd_thb_rate = float(fx_hist['Close'].iloc[-1]) if not fx_hist.empty else 35.0
        except Exception:
            usd_thb_rate = 35.0
            
        raw_results = []
        normalized_history_dict = {}
        
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
                
                # ดึงข่าวล่าสุดจาก Yahoo Finance
                news_list = []
                try:
                    raw_news = stock.news
                    if raw_news:
                        for n in raw_news[:3]:
                            title = n.get('title', '')
                            link = n.get('link', '#')
                            publisher = n.get('publisher', '')
                            if title:
                                news_list.append(f"• [{title}]({link}) ({publisher})")
                except Exception:
                    pass
                
                news_text = "<br>".join(news_list) if news_list else "ไม่มีรายงานข่าวล่าสุด"
                
                is_thai = ".BK" in ticker
                currency = "฿" if is_thai else "$"
                
                if is_thai:
                    asset_type = "หุ้นไทย 🇹🇭"
                elif "-USD" in ticker:
                    asset_type = "คริปโต 🪙"
                elif "=F" in ticker or "DX-" in ticker:
                    asset_type = "สินค้าโภคภัณฑ์ 🥇"
                else:
                    asset_type = "หุ้นต่างประเทศ 🌎"
                
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
                
                target_buy_price = min(current_price, max(curr_sma, current_price * 0.985))
                stop_loss = target_buy_price * 0.97
                take_profit_1 = target_buy_price + (target_buy_price - stop_loss) * 2.0 # ขยับ TP เป็น 1:2 เพื่อความคุ้มค่า
                
                # คำนวณ Risk / Reward Ratio (RR)
                risk = target_buy_price - stop_loss
                reward = take_profit_1 - target_buy_price
                rr_ratio = (reward / risk) if risk > 0 else 0.0
                rr_grade = "🔥 คุ้มค่าสูง (RR > 2.0)" if rr_ratio >= 2.0 else ("👍 พอใช้ได้ (RR > 1.5)" if rr_ratio >= 1.5 else "⚠️ ไม่ค่อยคุ้มเสี่ยง")
                
                score = 0.0
                if current_price > curr_sma and current_macd > current_signal:
                    if 45 <= current_rsi <= 65:
                        signal = "🟢 ความน่าจะเป็นทำกำไรสูง (Strong Buy)"
                        score = 3.0
                    else:
                        signal = "🟡 แนวโน้มขาขึ้นแต่ต้องระวัง (Uptrend)"
                        score = 1.5
                elif current_price <= curr_sma and current_rsi < 40:
                    signal = "🟡 อยู่ในโซน Oversold (รอสะสมรีบาวด์)"
                    score = 1.0
                else:
                    signal = "🔴 แนวโน้มขาลงความเสี่ยงสูง (ไม่ลงทุน)"
                    score = 0.0
                
                raw_results.append({
                    "สัญลักษณ์": ticker,
                    "ประเภท": asset_type,
                    "ราคาปัจจุบัน": f"{current_price:,.2f} {currency}",
                    "raw_price": current_price,
                    "currency": currency,
                    "is_thai": is_thai,
                    "เปลี่ยนแปลง (%)": f"{pct_change:+.2f}%",
                    "🎯 ราคาเข้าซื้อ": target_buy_price,
                    "RSI": f"{current_rsi:.1f}",
                    "Stop Loss": f"{stop_loss:,.2f} {currency}",
                    "Take Profit": f"{take_profit_1:,.2f} {currency}",
                    "Risk/Reward": f"1 : {rr_ratio:.2f} ({rr_grade})",
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
                
                target_buy_thb = r["🎯 ราคาเข้าซื้อ"] * (1 if r["is_thai"] else usd_thb_rate)
                if allocated_budget_thb > 0 and target_buy_thb > 0:
                    raw_shares = allocated_budget_thb / target_buy_thb
                    suggested_shares = int(raw_shares) if r["is_thai"] else round(raw_shares, 4)
                else:
                    suggested_shares = 0
                
                results.append({
                    "สัญลักษณ์": r["สัญลักษณ์"],
                    "ประเภท": r["ประเภท"],
                    "ราคาปัจจุบัน": r["ราคาปัจจุบัน"],
                    "เปลี่ยนแปลง (%)": r["เปลี่ยนแปลง (%)"],
                    "🎯 ราคาเข้าซื้อ": f"{r['🎯 ราคาเข้าซื้อ']:,.2f} {r['currency']}",
                    "น้ำหนักพอร์ต (%)": f"{weight_pct:.1f}%",
                    "Risk/Reward Ratio": r["Risk/Reward"],
                    "Stop Loss": r["Stop Loss"],
                    "Take Profit": r["Take Profit"],
                    "งบลงทุน (บาท)": f"{allocated_budget_thb:,.2f} ฿",
                    "จำนวนหน่วย": f"{suggested_shares:,} หน่วย" if r["is_thai"] else f"{suggested_shares:,.4f} หน่วย",
                    "สถานะ": r["สถานะ"],
                    "News": r["News"],
                    "History": r["History"]
                })
            
            df_results = pd.DataFrame(results)
            cash_remaining = total_capital_thb - total_allocated_thb
            
            st.success(f"✅ วิเคราะห์พอร์ตสำเร็จเรียบร้อย!")
            
            # ตรวจสอบคำนวณกำไร-ขาดทุนพอร์ตจริงที่คุณกรอกเข้ามา
            my_asset_clean = my_entry_asset.strip().upper()
            matched_asset = df_results[df_results['สัญลักษณ์'] == my_asset_clean]
            
            if not matched_asset.empty:
                # ดึงราคาปัจจุบันที่เป็นตัวเลขออกมาคำนวณ
                curr_p_str = matched_asset.iloc[0]['ราคาปัจจุบัน'].replace('$', '').replace('฿', '').replace(',', '').strip()
                curr_p_float = float(curr_p_str)
                pnl_thb = (curr_p_float - my_buy_price) * my_shares_held * (1 if ".BK" in my_asset_clean else usd_thb_rate)
                pnl_pct = ((curr_p_float - my_buy_price) / my_buy_price) * 100
                
                st.info(f"🪙 **สถานะพอร์ตจริงของคุณ ({my_asset_clean}):** ต้นทุน {my_buy_price:,.2f} | ราคาปัจจุบัน {curr_p_float:,.2f} | กำไร/ขาดทุน: **{pnl_thb:+,.2f} ฿ ({pnl_pct:+.2f}%)**")

            # สรุปภาพรวม Metrics พอร์ต
            m1, m2, m3 = st.columns(3)
            m1.metric("💰 เงินทุนรวมทั้งพอร์ต", f"{total_capital_thb:,.2f} ฿")
            m2.metric("📈 งบที่จัดสรรลงทุนจริง", f"{total_allocated_thb:,.2f} ฿")
            m3.metric("💵 เงินสดสำรองคงเหลือ", f"{cash_remaining:,.2f} ฿")
            
            st.markdown("---")
            
            tab1, tab2, tab3, tab4 = st.tabs(["🔥 โซนคัดเน้นๆ + ข่าว", "📈 กราฟเทียบผลตอบแทน", "📋 ตารางพอร์ตคัดกรอง", "⚙️ ดูทั้งหมด"])
            
            with tab1:
                invest_df = df_results[df_results['งบลงทุน (บาท)'] != "0.00 ฿"]
                if not invest_df.empty:
                    for _, row in invest_df.iterrows():
                        with st.container():
                            st.markdown(f"### 🎯 {row['สัญลักษณ์']} <span style='font-size:16px; color:#22c55e;'>({row['สถานะ']})</span>", unsafe_allow_html=True)
                            
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("น้ำหนักพอร์ต", row['น้ำหนักพอร์ต (%)'], row['เปลี่ยนแปลง (%)'])
                            c2.metric("🎯 ราคาควรเข้าซื้อ", row['🎯 ราคาเข้าซื้อ'])
                            c3.metric("ความคุ้มค่า (R/R)", row['Risk/Reward Ratio'])
                            c4.metric("งบลงทุนจัดสรร", row['งบลงทุน (บาท)'])
                            
                            st.markdown(f"**📰 ข่าวสารล่าสุดจาก Yahoo News:**<br>{row['News']}", unsafe_allow_html=True)
                            st.line_chart(row['History'], height=200)
                            st.markdown("---")
                else:
                    st.warning("⚠️ วันนี้ไม่มีสินทรัพย์ผ่านเกณฑ์ความเสี่ยง แนะนำให้ถือเงินสด")
            
            with tab2:
                st.subheader("📈 กราฟเปรียบเทียบผลตอบแทนย้อนหลัง (Normalized Performance)")
                if normalized_history_dict:
                    df_perf = pd.DataFrame(normalized_history_dict)
                    st.line_chart(df_perf, height=400)
                else:
                    st.info("ไม่พบข้อมูลกราฟเปรียบเทียบ")
            
            with tab3:
                st.subheader("📊 ตารางจัดสรรพอร์ต (เฉพาะตัวที่แนะนำให้ลงทุน)")
                active_df = df_results[df_results['งบลงทุน (บาท)'] != "0.00 ฿"].drop(columns=['History', 'News'])
                if not active_df.empty:
                    st.dataframe(active_df, use_container_width=True, height=400, hide_index=True)
                else:
                    st.info("ไม่มีสินทรัพย์ผ่านเกณฑ์ในรอบนี้")
                
            with tab4:
                st.subheader("📋 ตารางแสดงผลทั้งหมด")
                full_display_df = df_results.drop(columns=['History', 'News'])
                st.dataframe(full_display_df, use_container_width=True, height=500, hide_index=True)
                
                csv_data = full_display_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 ดาวน์โหลดรายงานพอร์ต (CSV)",
                    data=csv_data,
                    file_name="ultimate_portfolio_report.csv",
                    mime="text/csv"
                )
        else:
            st.error("❌ ไม่สามารถดึงข้อมูลได้ โปรดตรวจสอบรายชื่อสัญลักษณ์ใหม่อีกครั้งครับ")
else:
    st.info("👈 ตั้งค่าธีม กรอกเงินทุน และใส่รายชื่อสินทรัพย์ด้านซ้าย แล้วกดปุ่ม **'🔍 วิเคราะห์พอร์ตและสแกนตลาด'** ได้เลยครับ")

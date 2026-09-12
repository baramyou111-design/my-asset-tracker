import streamlit as st
import yfinance as yf
import pandas as pd

# 1. ตั้งค่าหน้าจอ Dashboard
st.set_page_config(
    page_title="AI Risk-Adjusted Fund Terminal with News",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        background-color: #2563eb;
        color: white;
    }
    .stButton>button:hover { background-color: #1d4ed8; }
    </style>
""", unsafe_allow_html=True)

st.title("📰 Risk-Adjusted Fund Terminal + Yahoo News")
st.markdown("ระบบวิเคราะห์ความเสี่ยง จัดพอร์ตตามความน่าจะเป็น และดึงข่าวสารล่าสุดจาก Yahoo News ประกอบการตัดสินใจ")

# 2. แผงควบคุมด้านข้าง (Sidebar)
with st.sidebar:
    st.header("⚙️ ตั้งค่าพอร์ตและสินทรัพย์")
    
    default_input = "PTT.BK, AOT.BK, CPALL.BK, AAPL, TSLA, NVDA, BTC-USD, ETH-USD, GC=F, SI=F, CL=F"
    ticker_input = st.text_area(
        "รายชื่อสินทรัพย์ (คั่นด้วย ,):",
        default_input,
        height=120
    )
    
    st.markdown("---")
    st.subheader("💰 จัดการเงินทุนรวมพอร์ต")
    total_capital_thb = st.number_input("เงินทุนรวมทั้งพอร์ต (บาท):", value=100000.0, step=10000.0, format="%.2f")
    
    st.markdown("<br>", unsafe_allow_html=True)
    scan_button = st.button("🔍 วิเคราะห์ความเสี่ยงและดึงข่าว", type="primary")

tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

# 3. ส่วนการประเมินความเสี่ยงและดึงข่าว
if scan_button:
    with st.spinner("⏳ กำลังวิเคราะห์ทางเทคนิค ประเมินความเสี่ยง และดึงข่าวล่าสุดจาก Yahoo News..."):
        try:
            fx_ticker = yf.Ticker("USDTHB=X")
            fx_hist = fx_ticker.history(period="1d")
            usd_thb_rate = float(fx_hist['Close'].iloc[-1]) if not fx_hist.empty else 35.0
        except Exception:
            usd_thb_rate = 35.0
            
        raw_results = []
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="6mo")
                if hist.empty or len(hist) < 30:
                    continue
                    
                current_price = float(hist['Close'].iloc[-1])
                prev_price = float(hist['Close'].iloc[-2])
                pct_change = ((current_price - prev_price) / prev_price) * 100
                
                # ดึงข่าวล่าสุดจาก Yahoo Finance
                news_list = []
                try:
                    raw_news = stock.news
                    if raw_news:
                        for n in raw_news[:3]: # ดึงมาแสดง 3 ข่าวล่าสุด
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
                take_profit_1 = target_buy_price + (target_buy_price - stop_loss) * 1.5
                
                score = 0.0
                if current_price > curr_sma and current_macd > current_signal:
                    if 45 <= current_rsi <= 65:
                        signal = "🟢 ความน่าจะเป็นทำกำไรสูง (Strong Buy)"
                        score = 3.0
                    else:
                        signal = "🟡 แนวโน้มขาขึ้นแต่ต้องระวัง (Uptrend)"
                        score = 1.5
                elif current_price <= curr_sma and current_rsi < 40:
                    signal = "🟡 อยู่ในโซน Oversold (รอสะสมเผื่อรีบาวด์)"
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
                    "Take Profit 1": f"{take_profit_1:,.2f} {currency}",
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
            
            for r in raw_results:
                if total_score > 0 and r["score"] > 0:
                    weight_pct = (r["score"] / total_score) * 100
                    allocated_budget_thb = total_capital_thb * (weight_pct / 100)
                else:
                    weight_pct = 0.0
                    allocated_budget_thb = 0.0
                
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
                    "RSI": r["RSI"],
                    "Stop Loss": r["Stop Loss"],
                    "งบลงทุน (บาท)": f"{allocated_budget_thb:,.2f} ฿",
                    "จำนวนหน่วย": f"{suggested_shares:,} หน่วย" if r["is_thai"] else f"{suggested_shares:,.4f} หน่วย",
                    "สถานะ": r["สถานะ"],
                    "News": r["News"],
                    "History": r["History"]
                })
            
            df_results = pd.DataFrame(results)
            st.success(f"✅ วิเคราะห์และดึงข่าวสำเร็จ! (งบรวมพอร์ต: {total_capital_thb:,.2f} ฿)")
            
            tab1, tab2, tab3 = st.tabs(["🔥 โซนคัดเน้นๆ + ข่าวล่าสุด", "📋 ตารางพอร์ตคัดกรองความเสี่ยง", "⚙️ ดูทั้งหมดรวมตัวถูกตัด"])
            
            with tab1:
                invest_df = df_results[df_results['งบลงทุน (บาท)'] != "0.00 ฿"]
                if not invest_df.empty:
                    for _, row in invest_df.iterrows():
                        with st.container():
                            st.markdown(f"### 🎯 {row['สัญลักษณ์']} <span style='font-size:16px; color:#22c55e;'>({row['สถานะ']})</span>", unsafe_allow_html=True)
                            
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("น้ำหนักพอร์ต", row['น้ำหนักพอร์ต (%)'], row['เปลี่ยนแปลง (%)'])
                            c2.metric("🎯 ราคาควรเข้าซื้อ", row['🎯 ราคาเข้าซื้อ'])
                            c3.metric("งบลงทุนจัดสรร", row['งบลงทุน (บาท)'])
                            c4.metric("จำนวนหน่วย", row['จำนวนหน่วย'])
                            
                            # แสดงข่าวสารล่าสุดจาก Yahoo News ภายใน Card
                            st.markdown(f"**📰 ข่าวสารล่าสุดจาก Yahoo News:**<br>{row['News']}", unsafe_allow_html=True)
                            
                            st.line_chart(row['History'], height=200)
                            st.markdown("---")
                else:
                    st.warning("⚠️ วันนี้ตลาดมีความเสี่ยงสูง ไม่มีสินทรัพย์ผ่านเกณฑ์ ระบบแนะนำให้ถือเงินสด")
            
            with tab2:
                st.subheader("📊 ตารางจัดสรรพอร์ต (เฉพาะตัวที่แนะนำให้ลงทุน)")
                active_df = df_results[df_results['งบลงทุน (บาท)'] != "0.00 ฿"].drop(columns=['History', 'News'])
                if not active_df.empty:
                    st.dataframe(active_df, use_container_width=True, height=400, hide_index=True)
                else:
                    st.info("ไม่มีสินทรัพย์ผ่านเกณฑ์ในรอบนี้")
                
            with tab3:
                st.subheader("📋 ตารางแสดงผลทั้งหมด (รวมตัวที่ถูกตัดสิทธิ์งบ 0 บาท)")
                full_display_df = df_results.drop(columns=['History', 'News'])
                st.dataframe(full_display_df, use_container_width=True, height=500, hide_index=True)
                
                csv_data = full_display_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 ดาวน์โหลดรายงาน (CSV)",
                    data=csv_data,
                    file_name="risk_adjusted_portfolio_news.csv",
                    mime="text/csv"
                )
        else:
            st.error("❌ ไม่สามารถดึงข้อมูลได้ โปรดตรวจสอบรายชื่อสัญลักษณ์ใหม่อีกครั้งครับ")
else:
    st.info("👈 กำหนดเงินทุนรวมและรายชื่อสินทรัพย์ด้านซ้าย แล้วกดปุ่ม **'🔍 วิเคราะห์ความเสี่ยงและดึงข่าว'** ได้เลยครับ")

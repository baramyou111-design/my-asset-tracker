import streamlit as st
import yfinance as yf
import pandas as pd

# 1. ตั้งค่าหน้าจอ Dashboard
st.set_page_config(
    page_title="Ultimate Pro Trading Terminal",
    page_icon="🚀",
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

st.title("🚀 Ultimate Pro Trading Terminal")
st.markdown("ระบบวิเคราะห์ จัดสรรพอร์ต และคำนวณจุดเข้าซื้อ/ขายทำกำไรอัตโนมัติ (รองรับหุ้นไทย, หุ้นนอก, คริปโต และสินค้าโภคภัณฑ์)")

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
    st.subheader("💰 จัดการเงินลงทุน")
    total_capital_thb = st.number_input("เงินทุนทั้งหมด (บาท):", value=100000.0, step=10000.0, format="%.2f")
    risk_pct = st.slider("สัดส่วนงบลงทุนต่อไม้ (% ของพอร์ต):", min_value=0.5, max_value=10.0, value=2.0, step=0.5)
    
    st.markdown("<br>", unsafe_allow_html=True)
    scan_button = st.button("🔍 เริ่มสแกนและวิเคราะห์ตลาด", type="primary")

tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

# 3. ส่วนการประมวลผล
if scan_button:
    with st.spinner("⏳ กำลังเชื่อมต่อตลาดโลก คำนวณอินดิเคเตอร์ และอัตราแลกเปลี่ยน..."):
        try:
            fx_ticker = yf.Ticker("USDTHB=X")
            fx_hist = fx_ticker.history(period="1d")
            usd_thb_rate = float(fx_hist['Close'].iloc[-1]) if not fx_hist.empty else 35.0
        except Exception:
            usd_thb_rate = 35.0
            
        results = []
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="6mo")
                if hist.empty or len(hist) < 30:
                    continue
                    
                current_price = float(hist['Close'].iloc[-1])
                prev_price = float(hist['Close'].iloc[-2])
                pct_change = ((current_price - prev_price) / prev_price) * 100
                
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
                
                # เส้นค่าเฉลี่ย SMA 20
                hist['SMA20'] = hist['Close'].rolling(window=20).mean()
                curr_sma = float(hist['SMA20'].iloc[-1])
                prev_sma = float(hist['SMA20'].iloc[-2])
                
                # RSI (14)
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                hist['RSI'] = 100 - (100 / (1 + rs))
                current_rsi = float(hist['RSI'].iloc[-1])
                
                # MACD
                exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
                exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
                hist['MACD'] = exp1 - exp2
                hist['MACD_Signal'] = hist['MACD'].ewm(span=9, adjust=False).mean()
                current_macd = float(hist['MACD'].iloc[-1])
                current_signal = float(hist['MACD_Signal'].iloc[-1])
                
                # ราคาเข้าซื้อที่สมเหตุสมผล (ไม่แพงกว่าปัจจุบัน)
                target_buy_price = min(current_price, max(curr_sma, current_price * 0.985))
                target_buy_thb = target_buy_price * (1 if is_thai else usd_thb_rate)
                
                # Stop Loss และ Take Profit (TP1, TP2)
                stop_loss = target_buy_price * 0.97
                resistance = float(hist['High'].rolling(window=20).max().iloc[-1])
                take_profit_1 = target_buy_price + (target_buy_price - stop_loss) * 1.5  # Risk/Reward Ratio 1:1.5
                take_profit_2 = resistance
                
                # งบลงทุน
                suggested_budget_thb = total_capital_thb * (risk_pct / 100)
                
                if target_buy_thb > 0:
                    raw_shares = suggested_budget_thb / target_buy_thb
                    suggested_shares = int(raw_shares) if is_thai else round(raw_shares, 4)
                else:
                    suggested_shares = 0
                
                # สถานะ
                signal = "⚪ รอดูสถานการณ์"
                if prev_price < prev_sma and current_price > curr_sma and current_macd > current_signal:
                    signal = "🟢 Strong Buy"
                elif current_price > curr_sma:
                    signal = "🟡 Uptrend"
                else:
                    signal = "🔴 Accumulate / Dip"
                
                results.append({
                    "สัญลักษณ์": ticker,
                    "ประเภท": asset_type,
                    "ราคาปัจจุบัน": f"{current_price:,.2f} {currency}",
                    "เปลี่ยนแปลง (%)": f"{pct_change:+.2f}%",
                    "🎯 ราคาเข้าซื้อ": f"{target_buy_price:,.2f} {currency}",
                    "RSI": f"{current_rsi:.1f}",
                    "Stop Loss": f"{stop_loss:,.2f} {currency}",
                    "Take Profit 1": f"{take_profit_1:,.2f} {currency}",
                    "งบลงทุน (บาท)": f"{suggested_budget_thb:,.2f} ฿",
                    "จำนวนหน่วย": f"{suggested_shares:,} หน่วย" if is_thai else f"{suggested_shares:,.4f} หน่วย",
                    "สถานะ": signal,
                    "History": hist[['Close', 'SMA20']]
                })
            except Exception:
                pass
        
        df_results = pd.DataFrame(results)
        
        if not df_results.empty:
            st.success(f"✅ สแกนสำเร็จ! (อัตราแลกเปลี่ยนอ้างอิง: 1 USD = {usd_thb_rate:.2f} THB)")
            
            # แบ่งเป็นแท็บการใช้งาน
            tab1, tab2, tab3 = st.tabs(["🔥 โซนหุ้นน่าซื้อ (Top Signals)", "📋 ตารางภาพรวมพอร์ต", "⚙️ ตัวกรองขั้นสูง"])
            
            with tab1:
                buy_df = df_results[df_results['สถานะ'].str.contains("🟢")]
                if not buy_df.empty:
                    for _, row in buy_df.iterrows():
                        with st.container():
                            st.markdown(f"### 🎯 {row['สัญลักษณ์']} <span style='font-size:16px; color:#9ca3af;'>({row['ประเภท']})</span>", unsafe_allow_html=True)
                            
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("ราคาปัจจุบัน", row['ราคาปัจจุบัน'], row['เปลี่ยนแปลง (%)'])
                            c2.metric("🎯 ราคาควรเข้าซื้อ", row['🎯 ราคาเข้าซื้อ'])
                            c3.metric("Stop Loss / TP1", f"{row['Stop Loss']} / {row['Take Profit 1']}")
                            c4.metric("งบลงทุน / จำนวน", row['งบลงทุน (บาท)'], row['จำนวนหน่วย'])
                            
                            st.line_chart(row['History'], height=200)
                            st.markdown("---")
                else:
                    st.info("💡 วันนี้ยังไม่มีสินทรัพย์ตัวไหนเกิดสัญญาณ Strong Buy ขั้นสุด แต่สามารถดูแผนสะสมจากแท็บภาพรวมพอร์ตได้เลยครับ")
            
            with tab2:
                st.subheader("📊 ตารางภาพรวมสินทรัพย์ทั้งหมด")
                display_df = df_results.drop(columns=['History'])
                st.dataframe(display_df, use_container_width=True, height=500, hide_index=True)
                
                csv_data = display_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 ดาวน์โหลดรายงานการวิเคราะห์พอร์ต (CSV)",
                    data=csv_data,
                    file_name="ultimate_trading_report.csv",
                    mime="text/csv"
                )
                
            with tab3:
                st.subheader("🔍 กรองข้อมูลตามสถานะที่คุณสนใจ")
                selected_status = st.selectbox("เลือกสถานะที่ต้องการแสดง:", ["ทั้งหมด", "🟢 Strong Buy", "🟡 Uptrend", "🔴 Accumulate / Dip"])
                
                if selected_status == "ทั้งหมด":
                    filtered_df = df_results.drop(columns=['History'])
                else:
                    filtered_df = df_results[df_results['สถานะ'] == selected_status].drop(columns=['History'])
                    
                st.dataframe(filtered_df, use_container_width=True, height=400, hide_index=True)
        else:
            st.error("❌ ไม่สามารถดึงข้อมูลได้ โปรดตรวจสอบรายชื่อสัญลักษณ์ใหม่อีกครั้งครับ")
else:
    st.info("👈 กรอกรายชื่อสินทรัพย์และตั้งค่าเงินทุนที่แถบด้านซ้าย แล้วกดปุ่ม **'🔍 เริ่มสแกนและวิเคราะห์ตลาด'** ได้เลยครับ")
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("🌐 ตลาดที่รองรับ", "ไทย / นอก / คริปโต")
    col_b.metric("🥇 สินค้าโภคภัณฑ์", "ทองคำ / เงิน / น้ำมัน")
    col_c.metric("🎯 ฟีเจอร์เด็ด", "TP / SL / Fractional Shares")

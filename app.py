import streamlit as st
import yfinance as yf
import pandas as pd

# 1. ตั้งค่าหน้าจอ Dashboard
st.set_page_config(page_title="Pro Trading Terminal", layout="wide", page_icon="📈")
st.title("🚀 Pro Trading Terminal & Fractional Shares")
st.markdown("ระบบวิเคราะห์และคำนวณงบลงทุนเป็นเงินบาทแบบ **รองรับเศษหุ้น/เศษทอง** ทุกสินทรัพย์ แม้ยังไม่เกิดสัญญาณซื้อก็คำนวณยอดให้ทันที")

# 2. แผงควบคุมด้านข้าง (Sidebar)
st.sidebar.header("⚙️ ตั้งค่าการติดตามสินทรัพย์")

default_input = "PTT.BK, AOT.BK, CPALL.BK, AAPL, TSLA, NVDA, BTC-USD, ETH-USD, GC=F, SI=F, CL=F"
ticker_input = st.sidebar.text_area(
    "พิมพ์รายชื่อหุ้น/คริปโต/สินค้าโภคภัณฑ์ (คั่นด้วย ,):",
    default_input,
    help="ทองคำ=GC=F, เงิน=SI=F, น้ำมัน=CL=F, หุ้นไทย=.BK, คริปโต=-USD"
)

tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

st.sidebar.markdown("---")
st.sidebar.header("💰 ระบบคำนวณขนาดพอร์ต (คิดเป็นเงินบาท)")
total_capital_thb = st.sidebar.number_input("เงินทุนทั้งหมด (บาท):", value=100000.0, step=10000.0)
risk_pct = st.sidebar.slider("สัดส่วนเงินลงทุนต่อไม้ (% ของพอร์ต):", min_value=0.5, max_value=10.0, value=2.0, step=0.5)

# 3. ปุ่มเริ่มสแกน
if st.sidebar.button("🔍 เริ่มสแกนและวิเคราะห์ตลาด", type="primary"):
    with st.spinner("กำลังดึงอัตราแลกเปลี่ยน (USD/THB) และคำนวณงบลงทุน..."):
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
                asset_type = "หุ้นไทย 🇹🇭" if is_thai else ("คริปโต 🪙" if "-USD" in ticker else "สินค้าโภคภัณฑ์ 🥇" if "=F" in ticker or "DX-" in ticker else "หุ้นต่างประเทศ 🌎")
                
                # เส้นค่าเฉลี่ย SMA 20 วัน
                hist['SMA20'] = hist['Close'].rolling(window=20).mean()
                curr_sma = float(hist['SMA20'].iloc[-1])
                prev_sma = float(hist['SMA20'].iloc[-2])
                
                # คำนวณ RSI (14 วัน)
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                hist['RSI'] = 100 - (100 / (1 + rs))
                current_rsi = float(hist['RSI'].iloc[-1])
                
                # คำนวณ MACD
                exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
                exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
                hist['MACD'] = exp1 - exp2
                hist['MACD_Signal'] = hist['MACD'].ewm(span=9, adjust=False).mean()
                current_macd = float(hist['MACD'].iloc[-1])
                current_signal = float(hist['MACD_Signal'].iloc[-1])
                
                # ราคาเป้าหมายเข้าซื้อ
                target_buy_price = max(curr_sma, current_price * 0.985) if current_price > curr_sma else curr_sma
                target_buy_thb = target_buy_price * (1 if is_thai else usd_thb_rate)
                
                # จุด Stop Loss
                stop_loss = target_buy_price * 0.97
                resistance = float(hist['High'].rolling(window=20).max().iloc[-1])
                
                # ปรับการคำนวณงบลงทุนใหม่: ให้ดึงจาก % เงินทุนที่ตั้งไว้มาจัดสรรเป็นงบซื้อทันที (ไม่อิงความเสี่ยงติดลบ)
                suggested_budget_thb = total_capital_thb * (risk_pct / 100)
                
                if target_buy_thb > 0:
                    raw_shares = suggested_budget_thb / target_buy_thb
                    suggested_shares = int(raw_shares) if is_thai else round(raw_shares, 4)
                else:
                    suggested_shares = 0
                
                # เงื่อนไขสัญญาณซื้อ
                signal = "⚪ รอดูสถานการณ์"
                if prev_price < prev_sma and current_price > curr_sma and current_macd > current_signal:
                    signal = "🟢 แนะนำซื้อแรง (Strong Buy)"
                elif current_price > curr_sma:
                    signal = "🟡 ถือรันเทรนด์ (Uptrend)"
                else:
                    signal = "🔴 แนวโน้มขาลง (สะสมได้)"
                
                results.append({
                    "สัญลักษณ์": ticker,
                    "ประเภท": asset_type,
                    "ราคาปัจจุบัน": f"{current_price:,.2f} {currency}",
                    "เปลี่ยนแปลง (%)": f"{pct_change:+.2f}%",
                    "🎯 ราคาควรเข้าซื้อ": f"{target_buy_price:,.2f} {currency}",
                    "RSI (14)": f"{current_rsi:.1f}",
                    "Stop Loss": f"{stop_loss:,.2f} {currency}",
                    "งบลงทุนแนะนำ (บาท)": f"{suggested_budget_thb:,.2f} ฿",
                    "จำนวนที่ควรซื้อ": f"{suggested_shares:,} หน่วย" if is_thai else f"{suggested_shares:,.4f} หน่วย",
                    "คำแนะนำ": signal,
                    "History": hist[['Close', 'SMA20']]
                })
            except Exception:
                pass
        
        df_results = pd.DataFrame(results)
        
        if not df_results.empty:
            st.markdown(f"ℹ️ **อัตราแลกเปลี่ยนอ้างอิงปัจจุบัน:** 1 USD $\approx$ {usd_thb_rate:.2f} THB | *คำนวณงบลงทุนและเศษหุ้นอัตโนมัติ*")
            st.markdown("---")
            buy_df = df_results[df_results['คำแนะนำ'].str.contains("🟢")]
            
            st.header("🔥 ตัวที่น่าเข้าซื้อประจำวัน (Top Buy Signals)")
            if not buy_df.empty:
                for _, row in buy_df.iterrows():
                    st.markdown(f"### 🎯 สัญญาณซื้อ: **{row['สัญลักษณ์']}** ({row['ประเภท']})")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("ราคาปัจจุบัน", row['ราคาปัจจุบัน'], row['เปลี่ยนแปลง (%)'])
                    c2.metric("🎯 ราคาควรเข้าซื้อ", row['🎯 ราคาควรเข้าซื้อ'])
                    c3.metric("Stop Loss แนะนำ", row['Stop Loss'])
                    c4.metric("งบลงทุนจากพอร์ตบาท", f"{row['งบลงทุนแนะนำ']} ({row['จำนวนที่ควรซื้อ']})")
                    
                    st.line_chart(row['History'])
                    st.markdown("---")
            else:
                st.info("วันนี้ยังไม่มีสินทรัพย์ตัวไหนเกิดสัญญาณ Breakout หลัก แต่คุณสามารถดูงบลงทุนสะสมจากตารางด้านล่างได้เลยครับ")
            
            st.subheader("📊 ตารางสรุปภาพรวมทั้งหมด & งบลงทุนเทียบเงินบาท")
            display_df = df_results.drop(columns=['History'])
            
            st.dataframe(display_df, use_container_width=True, height=500, hide_index=True)
            
            csv_data = display_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 ดาวน์โหลดรายงานการวิเคราะห์ (CSV)", data=csv_data, file_name="fractional_trading_report.csv", mime="text/csv")
        else:
            st.error("ไม่สามารถดึงข้อมูลได้ โปรดตรวจสอบสัญลักษณ์ใหม่อีกครั้งครับ")
else:
    st.info("👈 กำหนดเงินทุนเป็นบาทและรายชื่อสินทรัพย์ด้านซ้ายมือ แล้วกดปุ่ม **'🔍 เริ่มสแกนและวิเคราะห์ตลาด'** เพื่อเริ่มต้นใช้งานได้ทันทีครับ!")

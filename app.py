import streamlit as st
import yfinance as yf
import pandas as pd

# 1. ตั้งค่าหน้าจอ Dashboard
st.set_page_config(page_title="Pro Trading Terminal", layout="wide", page_icon="📈")
st.title("🚀 Pro Trading Terminal & Advanced Buy Signals")
st.markdown("ระบบวิเคราะห์หุ้น คริปโต และสินค้าโภคภัณฑ์ (ทองคำ/เงิน/น้ำมัน) แบบเรียลไทม์ พร้อม RSI, MACD และจุด Stop Loss")

# 2. แผงควบคุมด้านข้าง (Sidebar)
st.sidebar.header("⚙️ ตั้งค่าการติดตามสินทรัพย์")

# เพิ่มทองคำ เงิน และน้ำมันไว้ในค่าเริ่มต้นให้เลย
default_input = "PTT.BK, AOT.BK, CPALL.BK, AAPL, TSLA, NVDA, BTC-USD, ETH-USD, GC=F, SI=F, CL=F"
ticker_input = st.sidebar.text_area(
    "พิมพ์รายชื่อหุ้น/คริปโต/สินค้าโภคภัณฑ์ (คั่นด้วย ,):",
    default_input,
    help="ทองคำ=GC=F, เงิน=SI=F, น้ำมัน=CL=F, หุ้นไทย=.BK, คริปโต=-USD"
)

tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

st.sidebar.markdown("---")
st.sidebar.header("💰 ระบบคำนวณขนาดพอร์ต (Position Sizing)")
total_capital = st.sidebar.number_input("เงินทุนทั้งหมด (บาท/ดอลลาร์):", value=100000, step=10000)
risk_pct = st.sidebar.slider("ยอมรับความเสี่ยงได้สูงสุดต่อไม้ (%):", min_value=0.5, max_value=5.0, value=2.0, step=0.5)

# 3. ปุ่มเริ่มสแกน
if st.sidebar.button("🔍 เริ่มสแกนและวิเคราะห์ตลาด", type="primary"):
    with st.spinner("กำลังดึงข้อมูลตลาดโลก (หุ้น, คริปโต, ทองคำ, น้ำมัน) และคำนวณอินดิเคเตอร์..."):
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
                
                # จุด Stop Loss และแนวต้าน
                stop_loss = current_price * 0.97
                resistance = float(hist['High'].rolling(window=20).max().iloc[-1])
                
                # คำนวณ Position Sizing
                risk_amount = total_capital * (risk_pct / 100)
                risk_per_share = current_price - stop_loss
                suggested_shares = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
                suggested_budget = suggested_shares * current_price
                
                # จำแนกประเภทสินทรัพย์
                if "-USD" in ticker:
                    asset_type = "คริปโต 🪙"
                elif ".BK" in ticker:
                    asset_type = "หุ้นไทย 🇹🇭"
                elif "=F" in ticker or "DX-" in ticker:
                    asset_type = "สินค้าโภคภัณฑ์ 🥇"
                else:
                    asset_type = "หุ้นต่างประเทศ 🌎"
                
                # เงื่อนไขสัญญาณซื้อ
                signal = "⚪ รอดูสถานการณ์"
                if prev_price < prev_sma and current_price > curr_sma and current_macd > current_signal:
                    signal = "🟢 แนะนำซื้อแรง (Strong Buy)"
                elif current_price > curr_sma:
                    signal = "🟡 ถือรันเทรนด์ (Uptrend)"
                else:
                    signal = "🔴 แนวโน้มขาลง"
                
                results.append({
                    "สัญลักษณ์": ticker,
                    "ประเภท": asset_type,
                    "ราคาปัจจุบัน": current_price,
                    "เปลี่ยนแปลง (%)": pct_change,
                    "RSI (14)": current_rsi,
                    "แนวรับ SMA20": curr_sma,
                    "Stop Loss": stop_loss,
                    "แนวต้าน": resistance,
                    "งบลงทุนแนะนำ": suggested_budget,
                    "จำนวนที่ควรซื้อ": suggested_shares,
                    "คำแนะนำ": signal,
                    "History": hist[['Close', 'SMA20']]
                })
            except Exception:
                pass
        
        df_results = pd.DataFrame(results)
        
        if not df_results.empty:
            st.markdown("---")
            buy_df = df_results[df_results['คำแนะนำ'].str.contains("🟢")]
            
            st.header("🔥 ตัวที่น่าเข้าซื้อประจำวัน (Top Buy Signals)")
            if not buy_df.empty:
                for _, row in buy_df.iterrows():
                    st.markdown(f"### 🎯 สัญญาณซื้อ: **{row['สัญลักษณ์']}** ({row['ประเภท']})")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("ราคาปัจจุบัน", f"{row['ราคาปัจจุบัน']:.2f}", f"{row['เปลี่ยนแปลง (%)']:.2f}%")
                    c2.metric("RSI Momentum", f"{row['RSI (14)']:.1f}")
                    c3.metric("Stop Loss แนะนำ", f"{row['Stop Loss']:.2f}")
                    c4.metric("งบลงทุนตามความเสี่ยง", f"{row['งบลงทุนแนะนำ']:,.2f} ({row['จำนวนที่ควรซื้อ']:,} หน่วย)")
                    
                    st.line_chart(row['History'])
                    st.markdown("---")
            else:
                st.info("วันนี้ยังไม่มีสินทรัพย์ตัวไหนเกิดสัญญาณซื้อที่สมบูรณ์ แนะนำให้รอดูสถานการณ์ก่อนครับ")
            
            st.subheader("📊 ตารางสรุปภาพรวมทั้งหมด & อินดิเคเตอร์เทคนิค")
            display_df = df_results.drop(columns=['History'])
            
            st.dataframe(
                display_df.style.format({
                    "ราคาปัจจุบัน": "{:.2f}",
                    "เปลี่ยนแปลง (%)": "{:.2f}%",
                    "RSI (14)": "{:.1f}",
                    "แนวรับ SMA20": "{:.2f}",
                    "Stop Loss": "{:.2f}",
                    "แนวต้าน": "{:.2f}",
                    "งบลงทุนแนะนำ": "{:,.2f}",
                    "จำนวนที่ควรซื้อ": "{:,}"
                }),
                use_container_width=True, height=500, hide_index=True
            )
            
            csv_data = display_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 ดาวน์โหลดรายงานการวิเคราะห์ (CSV)", data=csv_data, file_name="pro_trading_report.csv", mime="text/csv")
        else:
            st.error("ไม่สามารถดึงข้อมูลได้ โปรดตรวจสอบสัญลักษณ์ใหม่อีกครั้งครับ")
else:
    st.info("👈 กำหนดรายชื่อสินทรัพย์ด้านซ้ายมือ แล้วกดปุ่ม **'🔍 เริ่มสแกนและวิเคราะห์ตลาด'** เพื่อเริ่มต้นใช้งานได้ทันทีครับ!")
